import time
import logging
import signal
import threading
from ultralytics import YOLO
import numpy as np
import cv2
from typing import List, Tuple, Dict, Any

from prod.config import (
    MODEL_PATH,
    REDIS_HOST,
    REDIS_PORT,
    REDIS_DB,
    REDIS_PASSWORD,
    FRAMES_QUEUE,
    FACES_QUEUE,
    FACE_DETECTION_CONFIDENCE,
    FACE_DETECTION_IOU,
    MIN_FACE_WIDTH
)
from prod.utils import (
    get_redis_connection,
    decode_frame_data,
    encode_face_data
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('face_detection')

class FaceDetector:
    """Detects faces in frames retrieved from the Redis queue."""
    
    def __init__(self, model_path: str = MODEL_PATH, workers: int = 1):
        """
        Initialize the face detector.
        
        Args:
            model_path: Path to the YOLO model weights
            workers: Number of worker threads to process frames
        """
        self.model_path = model_path
        self.workers = workers
        self.redis_client = get_redis_connection()
        self.stop_event = threading.Event()
        self.model = None
        self.worker_threads = []
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"Face detector initialized with model: {model_path}, workers: {workers}")
    
    def _signal_handler(self, sig, frame):
        """Handle termination signals gracefully."""
        logger.info(f"Received signal {sig}, shutting down...")
        self.stop_event.set()
    
    def _load_model(self):
        """Load the YOLO model for face detection."""
        try:
            logger.info(f"Loading model from {self.model_path}")
            self.model = YOLO(self.model_path)
            logger.info(f"Model loaded successfully, class names: {self.model.model.names}")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            return False
    
    def start(self):
        """Start the face detection workers."""
        if not self._load_model():
            logger.error("Failed to load model, exiting")
            return
        
        # Start worker threads
        for i in range(self.workers):
            thread = threading.Thread(
                target=self._process_frames,
                args=(i,),
                daemon=True
            )
            self.worker_threads.append(thread)
            thread.start()
            logger.info(f"Started worker thread {i}")
        
        # Keep the main thread alive
        try:
            while not self.stop_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, shutting down...")
        finally:
            self._cleanup()
    
    def _process_frames(self, worker_id: int):
        """
        Process frames from the queue.
        
        Args:
            worker_id: Identifier for this worker thread
        """
        logger.info(f"Worker {worker_id} starting to process frames")
        
        while not self.stop_event.is_set():
            try:
                # BLPOP waits for items in the queue with a timeout
                queue_item = self.redis_client.blpop(FRAMES_QUEUE, timeout=1)
                
                if not queue_item:
                    continue
                
                # Extract the frame data (queue name and data)
                _, frame_data = queue_item
                
                # Decode the frame data
                frame, metadata = decode_frame_data(frame_data)
                
                # Detect faces in the frame
                faces = self._detect_faces(frame)
                
                # Process each detected face
                for face_img, bbox in faces:
                    # Encode and queue the face data
                    encoded_face = encode_face_data(face_img, bbox, metadata)
                    self.redis_client.rpush(FACES_QUEUE, encoded_face)
                    
                    logger.debug(f"Worker {worker_id} queued face from {metadata['stream_id']}")
                
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {str(e)}")
                time.sleep(1)
        
        logger.info(f"Worker {worker_id} stopping")
    
    def _detect_faces(self, frame: np.ndarray) -> List[Tuple[np.ndarray, List[int]]]:
        """
        Detect faces in a frame.
        
        Args:
            frame: Input image frame
            
        Returns:
            List of tuples containing (face_image, bounding_box)
        """
        faces = []
        
        try:
            # Run detection
            results = self.model.predict(
                frame, 
                conf=FACE_DETECTION_CONFIDENCE, 
                iou=FACE_DETECTION_IOU
            )
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # Get bounding box coordinates
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    # Filter out small detections
                    if (x2 - x1) < MIN_FACE_WIDTH:
                        continue
                    
                    # Extract the face image
                    face_img = frame[y1:y2, x1:x2]
                    
                    # Store face image and bbox
                    faces.append((face_img, [x1, y1, x2, y2]))
            
        except Exception as e:
            logger.error(f"Error detecting faces: {str(e)}")
        
        return faces
    
    def _cleanup(self):
        """Clean up resources before shutdown."""
        logger.info("Cleaning up resources...")
        self.stop_event.set()
        
        # Wait for all threads to finish
        for i, thread in enumerate(self.worker_threads):
            thread.join(timeout=2)
            logger.info(f"Worker thread {i} joined")
        
        logger.info("Face detector shutdown complete")


def main():
    """Main entry point for the face detection service."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Face Detection Service')
    parser.add_argument('--model', default=MODEL_PATH, help='Path to the YOLO model weights')
    parser.add_argument('--workers', type=int, default=1, help='Number of worker threads')
    
    args = parser.parse_args()
    
    detector = FaceDetector(model_path=args.model, workers=args.workers)
    detector.start()


if __name__ == "__main__":
    main() 