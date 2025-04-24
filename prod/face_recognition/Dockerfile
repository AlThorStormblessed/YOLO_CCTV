FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies without dlib/face_recognition
RUN pip install --no-cache-dir numpy==1.24.3
RUN pip install --no-cache-dir opencv-python==4.8.0.76
RUN pip install --no-cache-dir scikit-learn==1.2.2
RUN pip install --no-cache-dir redis==4.6.0
RUN pip install --no-cache-dir pydantic==2.5.0

# Install deepface which provides alternative face recognition methods
RUN pip install --no-cache-dir deepface==0.0.79

# Create directory structure
RUN mkdir -p /app/prod/face_recognition

# Copy application code
COPY prod/face_recognition/__init__.py /app/prod/face_recognition/
COPY prod/face_recognition/face_recognition.py /app/prod/face_recognition/
COPY prod/config.py /app/prod/config.py
COPY prod/utils.py /app/prod/utils.py
COPY prod/__init__.py /app/prod/

# Set Python path
ENV PYTHONPATH=/app

# Verify library versions (for debugging)
RUN python -c "import numpy; print(f'NumPy version: {numpy.__version__}')"
RUN python -c "import cv2; print(f'OpenCV version: {cv2.__version__}')"

# Run the face recognition service
CMD ["python", "-m", "prod.face_recognition.face_recognition", "--workers", "2", "--threshold", "0.7"] 