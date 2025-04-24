FROM python:3.10-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir numpy opencv-python redis psycopg2-binary

# Copy the stream processor code
COPY prod/stream_processor /app/prod/stream_processor

# Default command
CMD ["python", "-m", "prod.stream_processor.stream_processor", "--urls", "rtsp://example.com/stream1"] 