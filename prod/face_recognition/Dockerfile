FROM facerecognition-base:latest

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONNOUSERSITE=1

# Copy application code
COPY prod/face_recognition/__init__.py /app/prod/face_recognition/
COPY prod/face_recognition/face_recognition.py /app/prod/face_recognition/
COPY prod/__init__.py /app/prod/

# Verify library versions (for debugging)
RUN python -c "import numpy; print(f'NumPy version: {numpy.__version__}')"
RUN python -c "import cv2; print(f'OpenCV version: {cv2.__version__}')"

# Run the face recognition service
CMD ["python", "-m", "prod.face_recognition.face_recognition", "--workers", "2", "--threshold", "0.7"] 