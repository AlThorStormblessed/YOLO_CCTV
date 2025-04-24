FROM python:3.10-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir numpy==1.24.3 opencv-python==4.8.0.74 redis psycopg2-binary
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Create model directory
RUN mkdir -p /app/model

# Copy the face detection code
COPY prod/face_detection /app/prod/face_detection

# Copy the model file into the container
COPY runs/detect/train3/weights/best.pt /app/model/best.pt

# Default command
CMD ["python", "-m", "prod.face_detection.face_detection", "--workers", "2", "--model_path", "/app/model/best.pt"] 