FROM facerecognition-base:latest

# Set the working directory
WORKDIR /app

# Install additional required packages
RUN pip install --no-cache-dir deepface==0.0.79 flask==2.2.3 scikit-learn==1.2.2 dlib==19.24.1 opencv-python==4.7.0.72 numpy==1.24.2

# Create directory structure
RUN mkdir -p /app/prod/face_recognition
RUN mkdir -p /app/db

# Copy the application code
COPY prod/face_recognition/__init__.py /app/prod/face_recognition/
COPY prod/face_recognition/face_recognition.py /app/prod/face_recognition/
COPY prod/__init__.py /app/prod/
COPY prod/config.py /app/prod/
COPY prod/utils.py /app/prod/

# Set the entry point
CMD ["python", "-m", "prod.face_recognition.face_recognition", "--workers", "2"] 