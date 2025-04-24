FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for OpenCV and other packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir numpy==1.24.3
RUN pip install --no-cache-dir opencv-python==4.7.0.72
RUN pip install --no-cache-dir redis==5.0.1 
RUN pip install --no-cache-dir pydantic==2.5.2 pydantic-settings==2.1.0 python-dotenv==1.0.0
RUN pip install --no-cache-dir --no-deps ultralytics==8.0.20
RUN pip install --no-cache-dir torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cpu

# Create directory structure
RUN mkdir -p /app/prod/face_detection/model

# Copy the application code
COPY prod/face_detection/__init__.py /app/prod/face_detection/
COPY prod/face_detection/face_detection.py /app/prod/face_detection/
COPY prod/config.py /app/prod/config.py
COPY prod/utils.py /app/prod/utils.py
COPY prod/__init__.py /app/prod/

# Copy the YOLO model file
COPY runs/detect/train3/weights/best.pt /app/prod/face_detection/model/best.pt

# Set Python path
ENV PYTHONPATH=/app

# Verify versions for debugging
RUN python -c "import numpy; print(f'Using NumPy version: {numpy.__version__}')"
RUN python -c "import cv2; print(f'Using OpenCV version: {cv2.__version__}')"
RUN python -c "import torch; print(f'Using PyTorch version: {torch.__version__}')"

# Set the entry point
CMD ["python", "-m", "prod.face_detection.face_detection", "--workers", "2", "--model", "/app/prod/face_detection/model/best.pt"] 