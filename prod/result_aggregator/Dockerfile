FROM python:3.10-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir numpy opencv-python redis psycopg2-binary

# Copy the result aggregator code
COPY prod/result_aggregator /app/prod/result_aggregator

# Default command
CMD ["python", "-m", "prod.result_aggregator.result_aggregator"] 