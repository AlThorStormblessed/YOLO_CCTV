import cv2
import time
import threading
import logging
import redis
import signal
import sys
import os
import tempfile
import requests
from typing import Dict, List, Optional
import random
import argparse

from prod.config import (
    REDIS_HOST,
    REDIS_PORT, 
    REDIS_DB, 
    REDIS_PASSWORD,
    FRAMES_QUEUE,
    FRAME_SAMPLE_RATE
)
from prod.utils import get_redis_connection, encode_frame_data, manage_queue_size

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('stream_processor')


class RTSPStreamProcessor:
    """Processes RTSP streams, HTTP(S) URLs, or video files and extracts frames for face detection."""

    def __init__(self, sources: List[str]):
        self.sources = sources
        self.redis_client = get_redis_connection()
        self.capture_threads = {}
        self.stop_event = threading.Event()
        self.local_file_map = {}

        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info(f"Stream processor initialized with {len(sources)} sources")

    def _signal_handler(self, sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        self.stop_event.set()

    def start(self):
        """Start processing all sources in separate threads."""
        queue_mgmt_thread = threading.Thread(
            target=self._manage_queues,
            daemon=True
        )
        queue_mgmt_thread.start()
        logger.info("Started queue management thread")

        for i, src in enumerate(self.sources):
            source_id = f"source_{i}"
            thread = threading.Thread(
                target=self._process_source,
                args=(src, source_id),
                daemon=True
            )
            self.capture_threads[source_id] = thread
            thread.start()
            logger.info(f"Started thread for {source_id} - {src}")
            time.sleep(1)

        try:
            while not self.stop_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, shutting down...")
        finally:
            self._cleanup()

    def _manage_queues(self):
        logger.info("Queue management thread started")
        last_check_time = time.time()

        while not self.stop_event.is_set():
            try:
                current_time = time.time()
                if current_time - last_check_time >= 60:
                    frames_trimmed = manage_queue_size(self.redis_client, FRAMES_QUEUE, 100)
                    if frames_trimmed > 0:
                        logger.info(f"Queue management: Trimmed {frames_trimmed} frames")
                    last_check_time = current_time
                time.sleep(10)
            except Exception as e:
                logger.error(f"Error in queue management: {str(e)}")
                time.sleep(30)

    def _download_file(self, url):
        """Download video from URL to a local temp file."""
        logger.info(f"Downloading file from {url} ...")
        response = requests.get(url, stream=True)
        if response.status_code != 200:
            raise Exception(f"Failed to download file: {url}")

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                temp_file.write(chunk)
        temp_file.close()
        logger.info(f"Downloaded to {temp_file.name}")
        return temp_file.name

    def _process_source(self, src: str, source_id: str):
        logger.info(f"Starting to process source: {source_id}")

        reconnect_attempt = 0
        last_successful_read = time.time()
        cap = None

        while not self.stop_event.is_set():
            try:
                if cap is None or not cap.isOpened():
                    if cap is not None:
                        cap.release()

                    actual_src = src

                    if src.startswith(('http://', 'https://')):
                        if source_id not in self.local_file_map:
                            local_path = self._download_file(src)
                            self.local_file_map[source_id] = local_path
                        actual_src = self.local_file_map[source_id]

                    cap = cv2.VideoCapture(actual_src)

                    if not cap.isOpened():
                        logger.warning(f"Failed to open {source_id}")
                        raise Exception("Failed to open source")

                    fps = cap.get(cv2.CAP_PROP_FPS)
                    if fps <= 0 or fps > 100000:
                        fps = 30

                    frames_to_skip = max(1, int(fps / FRAME_SAMPLE_RATE))
                    logger.info(f"{source_id} FPS: {fps}, sampling every {frames_to_skip} frames")

                    frame_count = 0
                    reconnect_attempt = 0

                ret, frame = cap.read()
                current_time = time.time()

                if not ret:
                    logger.warning(f"End of stream or failed frame read for {source_id}")
                    cap.release()
                    cap = None
                    reconnect_attempt += 1
                    sleep_time = min(30, reconnect_attempt * 2)
                    logger.info(f"Will attempt to reconnect to {source_id} in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                    continue

                reconnect_attempt = 0
                last_successful_read = current_time
                frame_count += 1

                if frame_count % frames_to_skip != 0:
                    continue

                timestamp = time.time()

                if frame is None or frame.size == 0:
                    logger.warning(f"Empty frame from {source_id}")
                    continue

                encoded_data = encode_frame_data(frame, timestamp, source_id)
                self.redis_client.rpush(FRAMES_QUEUE, encoded_data)

                if frame_count % 100 == 0:
                    logger.info(f"Processed {frame_count} frames from {source_id}")
                else:
                    logger.debug(f"Queued frame from {source_id} at {timestamp}")

            except Exception as e:
                logger.error(f"Error processing source {source_id}: {str(e)}")
                if cap is not None:
                    cap.release()
                    cap = None
                reconnect_attempt += 1
                sleep_time = min(30, reconnect_attempt * 2)
                logger.info(f"Will attempt to reconnect to {source_id} in {sleep_time} seconds...")
                time.sleep(sleep_time)

        if cap is not None:
            cap.release()

        logger.info(f"Stopped processing source: {source_id}")

    def _cleanup(self):
        logger.info("Cleaning up resources...")
        self.stop_event.set()

        for source_id, thread in self.capture_threads.items():
            thread.join(timeout=2)
            logger.info(f"Thread for {source_id} joined")

        # Delete downloaded temp files
        for source_id, path in self.local_file_map.items():
            try:
                os.remove(path)
                logger.info(f"Deleted temp file {path}")
            except Exception as e:
                logger.warning(f"Failed to delete temp file {path}: {str(e)}")

        logger.info("Processor shutdown complete")


def main():
    """Main entry point for the processor."""
    parser = argparse.ArgumentParser(description='Stream Processor')
    parser.add_argument('--urls', required=True, help='Sources (comma-separated RTSP/HTTP URLs or file paths)')
    args = parser.parse_args()

    try:
        sources = [s.strip() for s in args.urls.split(',')]
        processor = RTSPStreamProcessor(sources)
        processor.start()
    except Exception as e:
        logger.error(f"Failed to run stream processor: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    main()
