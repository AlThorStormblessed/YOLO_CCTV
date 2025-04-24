import time
import logging
import signal
import threading
import numpy as np
import cv2
import json
import os
import base64
from typing import Dict, Any, Optional, List, Tuple
import torch
from torch import nn
from torchvision import models, transforms
from PIL import Image

from prod.config import (
    REDIS_HOST,
    REDIS_PORT, 
    REDIS_DB,
    REDIS_PASSWORD,
    FACES_QUEUE,
    RECOGNITION_QUEUE,
    KNOWN_FACES_STORE,
    DATABASE_URL
)
from prod.utils import (
    get_redis_connection,
    decode_face_data,
    encode_recognition_result
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('face_recognition')

class FaceRecognizer:
    """Recognizes faces from detected face images."""
    
    def __init__(self, workers: int = 1, similarity_threshold: float = 0.7):
        """
        Initialize the face recognizer.
        
        Args:
            workers: Number of worker threads to process faces
            similarity_threshold: Threshold for face matching confidence
        """
        self.workers = workers
        self.similarity_threshold = similarity_threshold
        self.redis_client = get_redis_connection()
        self.stop_event = threading.Event()
        self.worker_threads = []
        self.feature_extractor = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"Face recognizer initialized with workers: {workers}, device: {self.device}")
    
    def _signal_handler(self, sig, frame):
        """Handle termination signals gracefully."""
        logger.info(f"Received signal {sig}, shutting down...")
        self.stop_event.set()
    
    def _load_model(self):
        """Load the face recognition model."""
        try:
            logger.info("Loading face recognition model")
            
            # Use ResNet50 as a feature extractor
            model = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
            # Remove the classification layer
            self.feature_extractor = nn.Sequential(*list(model.children())[:-1])
            self.feature_extractor.to(self.device)
            self.feature_extractor.eval()
            
            # Define preprocessing transform
            self.transform = transforms.Compose([
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                ),
            ])
            
            logger.info("Model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            return False
    
    def start(self):
        """Start the face recognition workers."""
        if not self._load_model():
            logger.error("Failed to load model, exiting")
            return
        
        # Start worker threads
        for i in range(self.workers):
            thread = threading.Thread(
                target=self._process_faces,
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
    
    def _process_faces(self, worker_id: int):
        """
        Process faces from the queue.
        
        Args:
            worker_id: Identifier for this worker thread
        """
        logger.info(f"Worker {worker_id} starting to process faces")
        
        while not self.stop_event.is_set():
            try:
                # BLPOP waits for items in the queue with a timeout
                queue_item = self.redis_client.blpop(FACES_QUEUE, timeout=1)
                
                if not queue_item:
                    continue
                
                # Extract the face data (queue name and data)
                _, face_data = queue_item
                
                # Decode the face data
                face_img, metadata = decode_face_data(face_data)
                
                # Extract features from the face
                face_features = self._extract_features(face_img)
                
                # Match against known faces
                face_id, confidence = self._match_face(face_features)
                
                # Encode and queue the recognition result
                result = encode_recognition_result(face_id, confidence, metadata)
                self.redis_client.rpush(RECOGNITION_QUEUE, result)
                
                logger.debug(f"Worker {worker_id} recognized face from {metadata['stream_id']}: {face_id} ({confidence:.2f})")
                
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {str(e)}")
                time.sleep(1)
        
        logger.info(f"Worker {worker_id} stopping")
    
    def _extract_features(self, face_img: np.ndarray) -> np.ndarray:
        """
        Extract features from a face image.
        
        Args:
            face_img: Face image array
            
        Returns:
            Face feature vector
        """
        try:
            # Convert OpenCV BGR image to RGB
            rgb_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
            
            # Convert to PIL image and apply transformations
            pil_img = Image.fromarray(rgb_img)
            img_tensor = self.transform(pil_img).unsqueeze(0).to(self.device)
            
            # Extract features
            with torch.no_grad():
                features = self.feature_extractor(img_tensor)
                features = features.squeeze().cpu().numpy()
            
            # Normalize features
            features = features / np.linalg.norm(features)
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features: {str(e)}")
            return np.zeros(512)  # Return zero vector on error
    
    def _match_face(self, face_features: np.ndarray) -> Tuple[str, float]:
        """
        Match face features against known faces.
        
        Args:
            face_features: Face feature vector
            
        Returns:
            Tuple of (face_id, confidence)
        """
        best_match_id = "unknown"
        best_match_score = 0.0
        
        try:
            # Get all known faces from Redis
            known_faces = self.redis_client.hgetall(KNOWN_FACES_STORE)
            
            if not known_faces:
                logger.debug("No known faces found in database")
                return best_match_id, best_match_score
            
            # Compare with each known face
            for face_id, face_data in known_faces.items():
                face_id = face_id.decode('utf-8')
                face_data = json.loads(face_data.decode('utf-8'))
                known_features = np.array(face_data['features'])
                
                # Compute similarity (cosine similarity)
                similarity = np.dot(face_features, known_features)
                
                if similarity > best_match_score:
                    best_match_score = similarity
                    best_match_id = face_id
            
            # Check if similarity is above threshold
            if best_match_score < self.similarity_threshold:
                best_match_id = "unknown"
            
        except Exception as e:
            logger.error(f"Error matching face: {str(e)}")
        
        return best_match_id, float(best_match_score)
    
    def _cleanup(self):
        """Clean up resources before shutdown."""
        logger.info("Cleaning up resources...")
        self.stop_event.set()
        
        # Wait for all threads to finish
        for i, thread in enumerate(self.worker_threads):
            thread.join(timeout=2)
            logger.info(f"Worker thread {i} joined")
        
        logger.info("Face recognizer shutdown complete")


def main():
    """Main entry point for the face recognition service."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Face Recognition Service')
    parser.add_argument('--workers', type=int, default=1, help='Number of worker threads')
    parser.add_argument('--threshold', type=float, default=0.7, help='Similarity threshold')
    
    args = parser.parse_args()
    
    recognizer = FaceRecognizer(workers=args.workers, similarity_threshold=args.threshold)
    recognizer.start()


if __name__ == "__main__":
    main() 