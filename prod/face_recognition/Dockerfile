FROM facerecognition-base:latest

# Set the working directory
WORKDIR /app

# Copy the application code
COPY prod/face_recognition/__init__.py /app/prod/face_recognition/
COPY prod/face_recognition/face_recognition.py /app/prod/face_recognition/
COPY prod/__init__.py /app/prod/

# Set the entry point
CMD ["python", "-m", "prod.face_recognition.face_recognition", "--workers", "2"] 