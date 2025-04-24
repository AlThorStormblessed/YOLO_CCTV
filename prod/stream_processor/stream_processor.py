import cv2
import time
import threading
import logging
import redis
import signal
import sys
from typing import Dict, List, Optional

from prod.config import (
    REDIS_HOST,
    REDIS_PORT, 
    REDIS_DB, 
    REDIS_PASSWORD,
    FRAMES_QUEUE,
    FRAME_SAMPLE_RATE
)
from prod.utils import get_redis_connection, encode_frame_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('stream_processor')

class RTSPStreamProcessor:
    """Processes RTSP streams and extracts frames for face detection."""
    
    def __init__(self, rtsp_urls: List[str]):
        """
        Initialize the RTSP stream processor.
        
        Args:
            rtsp_urls: List of RTSP stream URLs to process
        """
        self.rtsp_urls = rtsp_urls
        self.redis_client = get_redis_connection()
        self.capture_threads = {}
        self.stop_event = threading.Event()
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"Stream processor initialized with {len(rtsp_urls)} streams")
    
    def _signal_handler(self, sig, frame):
        """Handle termination signals gracefully."""
        logger.info(f"Received signal {sig}, shutting down...")
        self.stop_event.set()
    
    def start(self):
        """Start processing all streams in separate threads."""
        for i, url in enumerate(self.rtsp_urls):
            stream_id = f"stream_{i}"
            thread = threading.Thread(
                target=self._process_stream,
                args=(url, stream_id),
                daemon=True
            )
            self.capture_threads[stream_id] = thread
            thread.start()
            logger.info(f"Started thread for {stream_id} - {url}")
        
        # Keep the main thread alive
        try:
            while not self.stop_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, shutting down...")
        finally:
            self._cleanup()
    
    def _process_stream(self, rtsp_url: str, stream_id: str):
        """
        Process a single RTSP stream.
        
        Args:
            rtsp_url: RTSP URL to process
            stream_id: Unique identifier for this stream
        """
        logger.info(f"Starting to process stream: {stream_id}")
        
        # OpenCV capture for the RTSP stream
        cap = cv2.VideoCapture(rtsp_url)
        if not cap.isOpened():
            logger.error(f"Failed to open stream: {rtsp_url}")
            return
        
        # Get FPS of stream to calculate frame skipping
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            logger.warning(f"Could not determine FPS for {stream_id}, using default of 30")
            fps = 30
        
        # Calculate frames to skip based on desired sample rate
        frames_to_skip = max(1, int(fps / FRAME_SAMPLE_RATE))
        logger.info(f"Stream {stream_id} FPS: {fps}, sampling every {frames_to_skip} frames")
        
        frame_count = 0
        
        while not self.stop_event.is_set():
            try:
                ret, frame = cap.read()
                if not ret:
                    logger.warning(f"Failed to read frame from {stream_id}, reconnecting...")
                    time.sleep(1)
                    cap.release()
                    cap = cv2.VideoCapture(rtsp_url)
                    continue
                
                frame_count += 1
                
                # Only process every nth frame
                if frame_count % frames_to_skip != 0:
                    continue
                
                # Current timestamp
                timestamp = time.time()
                
                # Encode and queue the frame
                encoded_data = encode_frame_data(frame, timestamp, stream_id)
                self.redis_client.rpush(FRAMES_QUEUE, encoded_data)
                
                logger.debug(f"Queued frame from {stream_id} at {timestamp}")
                
            except Exception as e:
                logger.error(f"Error processing stream {stream_id}: {str(e)}")
                time.sleep(1)
        
        # Clean up resources
        cap.release()
        logger.info(f"Stopped processing stream: {stream_id}")
    
    def _cleanup(self):
        """Clean up resources before shutdown."""
        logger.info("Cleaning up resources...")
        self.stop_event.set()
        
        # Wait for all threads to finish
        for stream_id, thread in self.capture_threads.items():
            thread.join(timeout=2)
            logger.info(f"Thread for {stream_id} joined")
        
        logger.info("Stream processor shutdown complete")


def main():
    """Main entry point for the stream processor service."""
    import argparse
    
    parser = argparse.ArgumentParser(description='RTSP Stream Processor')
    parser.add_argument('--urls', nargs='+', required=True, help='RTSP stream URLs')
    
    args = parser.parse_args()
    
    processor = RTSPStreamProcessor(args.urls)
    processor.start()


if __name__ == "__main__":
    main() 