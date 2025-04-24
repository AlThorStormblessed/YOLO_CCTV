FROM facerecognition-base:latest

WORKDIR /app

# Copy the face detection code
COPY prod/face_detection /app/prod/face_detection

# Default command
CMD ["python", "-m", "prod.face_detection.face_detection", "--workers", "2"] 