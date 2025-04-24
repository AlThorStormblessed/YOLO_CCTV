FROM facerecognition-base:latest

# Set the working directory
WORKDIR /app

# Install required packages
RUN pip install --no-cache-dir ultralytics==8.0.20

# Create directory structure
RUN mkdir -p /app/prod/face_detection
RUN mkdir -p /app/prod/face_detection/model

# Copy the application code
COPY prod/face_detection/__init__.py /app/prod/face_detection/
COPY prod/face_detection/face_detection.py /app/prod/face_detection/
COPY prod/__init__.py /app/prod/
COPY prod/config.py /app/prod/
COPY prod/utils.py /app/prod/

# Set the model path environment variable
ENV MODEL_PATH=/app/prod/face_detection/model/best.pt

# Set the entry point
CMD ["python", "-m", "prod.face_detection.face_detection", "--workers", "2", "--model", "/app/prod/face_detection/model/best.pt"] 