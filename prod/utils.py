import json
import redis
import numpy as np
import base64
import cv2
import time
from typing import Dict, Any, Optional, List, Tuple

from prod.config import (
    REDIS_HOST, 
    REDIS_PORT, 
    REDIS_PASSWORD, 
    REDIS_DB
)

def get_redis_connection() -> redis.Redis:
    """Create and return a Redis connection using configuration settings."""
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        db=REDIS_DB,
        decode_responses=False  # Keep as bytes for binary data
    )

def encode_image(image: np.ndarray) -> bytes:
    """Encode an OpenCV image to a compressed bytes format."""
    success, encoded_img = cv2.imencode('.jpg', image)
    if not success:
        raise ValueError("Failed to encode image")
    return encoded_img.tobytes()

def decode_image(encoded_image: bytes) -> np.ndarray:
    """Decode a compressed bytes format back to an OpenCV image."""
    np_arr = np.frombuffer(encoded_image, np.uint8)
    return cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

def encode_frame_data(frame: np.ndarray, timestamp: float, stream_id: str) -> bytes:
    """Encode frame data for queue storage."""
    encoded_image = encode_image(frame)
    metadata = {
        "timestamp": timestamp,
        "stream_id": stream_id,
    }
    
    # Convert metadata to JSON string then to bytes
    metadata_bytes = json.dumps(metadata).encode('utf-8')
    
    # Combine length prefix, metadata and image data
    metadata_length = len(metadata_bytes).to_bytes(4, byteorder='big')
    return metadata_length + metadata_bytes + encoded_image

def decode_frame_data(frame_data: bytes) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Decode frame data from queue storage."""
    # First 4 bytes represent metadata length
    metadata_length = int.from_bytes(frame_data[:4], byteorder='big')
    
    # Extract and parse metadata
    metadata_bytes = frame_data[4:4+metadata_length]
    metadata = json.loads(metadata_bytes.decode('utf-8'))
    
    # Extract and decode image
    image_bytes = frame_data[4+metadata_length:]
    frame = decode_image(image_bytes)
    
    return frame, metadata

def encode_face_data(face_image: np.ndarray, bbox: List[int], 
                    metadata: Dict[str, Any]) -> bytes:
    """Encode detected face data for queue storage."""
    encoded_face = encode_image(face_image)
    
    # Add bbox to metadata
    metadata_with_bbox = metadata.copy()
    metadata_with_bbox["bbox"] = bbox
    
    # Convert metadata to JSON string then to bytes
    metadata_bytes = json.dumps(metadata_with_bbox).encode('utf-8')
    
    # Combine length prefix, metadata and image data
    metadata_length = len(metadata_bytes).to_bytes(4, byteorder='big')
    return metadata_length + metadata_bytes + encoded_face

def decode_face_data(face_data: bytes) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Decode face data from queue storage."""
    # First 4 bytes represent metadata length
    metadata_length = int.from_bytes(face_data[:4], byteorder='big')
    
    # Extract and parse metadata
    metadata_bytes = face_data[4:4+metadata_length]
    metadata = json.loads(metadata_bytes.decode('utf-8'))
    
    # Extract and decode image
    image_bytes = face_data[4+metadata_length:]
    face_image = decode_image(image_bytes)
    
    return face_image, metadata

def encode_recognition_result(face_id: str, confidence: float, 
                           metadata: Dict[str, Any]) -> bytes:
    """Encode face recognition result for queue storage."""
    result = metadata.copy()
    result["face_id"] = face_id
    result["confidence"] = confidence
    result["processed_at"] = time.time()
    
    return json.dumps(result).encode('utf-8')

def decode_recognition_result(result_data: bytes) -> Dict[str, Any]:
    """Decode recognition result from queue storage."""
    return json.loads(result_data.decode('utf-8')) 