FROM facerecognition-base:latest

WORKDIR /app

# Copy the result aggregator code
COPY prod/result_aggregator /app/prod/result_aggregator

# Default command
CMD ["python", "-m", "prod.result_aggregator.result_aggregator", "--workers", "2"] 