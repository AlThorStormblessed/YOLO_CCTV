import os
from pathlib import Path

# Base project directory
BASE_DIR = Path(__file__).parent.parent

# Model path
MODEL_PATH = os.environ.get("MODEL_PATH", str(BASE_DIR / "runs/detect/train3/weights/best.pt"))

# Redis configuration
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", None)
REDIS_DB = int(os.environ.get("REDIS_DB", 0))

# Queue names
FRAMES_QUEUE = "frames_queue"
FACES_QUEUE = "faces_queue"
RECOGNITION_QUEUE = "recognition_queue"
RESULTS_STORE = "results_store"
KNOWN_FACES_STORE = "known_faces"

# Queue size limits
MAX_FRAMES_QUEUE_SIZE = int(os.environ.get("MAX_FRAMES_QUEUE_SIZE", 100))
MAX_FACES_QUEUE_SIZE = int(os.environ.get("MAX_FACES_QUEUE_SIZE", 200))
MAX_RECOGNITION_QUEUE_SIZE = int(os.environ.get("MAX_RECOGNITION_QUEUE_SIZE", 200))
MAX_RESULTS_STORE_SIZE = int(os.environ.get("MAX_RESULTS_STORE_SIZE", 1000))
QUEUE_FLUSH_INTERVAL = int(os.environ.get("QUEUE_FLUSH_INTERVAL", 3600))  # In seconds, default 1 hour

# Frame processing
FRAME_SAMPLE_RATE = int(os.environ.get("FRAME_SAMPLE_RATE", 5))  # Frames per second to process

# Face detection settings
FACE_DETECTION_CONFIDENCE = float(os.environ.get("FACE_DETECTION_CONFIDENCE", 0.4))
FACE_DETECTION_IOU = float(os.environ.get("FACE_DETECTION_IOU", 0.5))
MIN_FACE_WIDTH = int(os.environ.get("MIN_FACE_WIDTH", 100))  # Minimum width for a detected face

# Database settings
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "postgres")
POSTGRES_PORT = int(os.environ.get("POSTGRES_PORT", 5432))
POSTGRES_USER = os.environ.get("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "face_recognition")
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}" 