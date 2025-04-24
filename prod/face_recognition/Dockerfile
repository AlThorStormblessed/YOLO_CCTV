FROM facerecognition-base:latest

WORKDIR /app

# Copy the face recognition code
COPY prod/face_recognition /app/prod/face_recognition

# Default command
CMD ["python", "-m", "prod.face_recognition.face_recognition", "--workers", "2"] 