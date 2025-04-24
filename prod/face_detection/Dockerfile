FROM facerecognition-base:latest

# Set the working directory
WORKDIR /app

# Make sure we use the correct NumPy version
ENV PYTHONNOUSERSITE=1

# Copy the application code
COPY prod/face_detection/__init__.py /app/prod/face_detection/
COPY prod/face_detection/face_detection.py /app/prod/face_detection/
COPY prod/__init__.py /app/prod/

# Copy the YOLO model file
COPY runs/detect/train3/weights/best.pt /app/prod/face_detection/model/best.pt

# Create model directory and verify NumPy version
RUN python -c "import numpy; print(f'Using NumPy version: {numpy.__version__}')"
RUN python -c "import cv2; print(f'Using OpenCV version: {cv2.__version__}')"

# Set the entry point
CMD ["python", "-m", "prod.face_detection.face_detection", "--workers", "2", "--model", "/app/prod/face_detection/model/best.pt"] 