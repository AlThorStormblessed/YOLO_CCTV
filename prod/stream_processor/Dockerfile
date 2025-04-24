FROM facerecognition-base:latest

WORKDIR /app

# Copy the stream processor code
COPY prod/stream_processor /app/prod/stream_processor

# Default command
CMD ["python", "-m", "prod.stream_processor.stream_processor", "--urls", "rtsp://example.com/stream1"] 