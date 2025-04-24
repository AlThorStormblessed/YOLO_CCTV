# Face Recognition Microservices

This project implements a scalable, microservices-based face recognition system for CCTV/RTSP camera streams. The system leverages YOLO for face detection and a feature extraction model for face recognition, with Redis queues for inter-service communication.

## Architecture

The system follows a microservices architecture with the following components:

1. **Stream Processor**: Extracts frames from RTSP streams at configurable rates and pushes them to the processing pipeline.
2. **Face Detection**: Uses YOLO to detect faces in frames extracted from video streams.
3. **Face Recognition**: Extracts features from detected faces and compares them to known faces.
4. **Result Aggregator**: Collects and stores recognition results in Redis and PostgreSQL.

The services communicate through Redis queues, and the architecture supports auto-scaling based on queue lengths.

## Requirements

- Docker and Docker Compose
- RTSP video streams
- A trained YOLO face detection model

## Setup

### 1. Configure Environment Variables

Create a `.env` file in the same directory as the `docker-compose.yml` file with the following content:

```
# Docker Hub username
DOCKER_USERNAME=yourusername

# RTSP URLs (comma-separated)
RTSP_URLS=rtsp://example.com/stream1

# Model path
MODEL_PATH=./runs/detect/train3/weights/best.pt

# Redis configuration
REDIS_HOST=redis
REDIS_PORT=6379

# PostgreSQL configuration
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=face_recognition

# Face detection settings
FACE_DETECTION_CONFIDENCE=0.4
FACE_DETECTION_IOU=0.5
MIN_FACE_WIDTH=100

# Frame processing
FRAME_SAMPLE_RATE=5
```

Adjust the values as needed for your deployment.

### 2. Build Docker Images

Use the provided script to build all the Docker images:

```bash
./build_and_push.sh yourusername
```

To build and push to Docker Hub:

```bash
./build_and_push.sh yourusername --push
```

### 3. Deploy with Docker Compose

Start the entire stack:

```bash
docker-compose up -d
```

To scale specific services:

```bash
docker-compose up -d --scale face_detection=3 --scale face_recognition=2
```

## Configuration

You can adjust the system configuration by modifying the `config.py` file or by setting environment variables in the `.env` file or in the Docker Compose file.

## Database Schema

The system uses PostgreSQL with the pgvector extension for vector similarity search. The following tables are defined:

- **Person**: Stores person identities and their face vectors
- **Face**: Stores face images and vectors for each person
- **Detection**: Records face detection events
- **Stream**: Stores information about RTSP streams

## Deployment Scripts

Several utility scripts are provided to help with deployment and monitoring:

### 1. New Deployment (`new_deploye.sh`)

This script automates the process of cleaning up old containers/images and redeploying the services:

```bash
./prod/new_deploye.sh yourusername
```

The script:
- Stops all running containers
- Removes old face recognition containers and images
- Builds new images
- Starts the services with docker-compose

### 2. Test Deployment (`test_deployment.sh`)

This script tests the production deployment with a specified RTSP URL:

```bash
./prod/test_deployment.sh "rtsp://admin123:admin123@103.100.219.14:8555/11" yourusername
```

The script:
- Tests if the RTSP URL is accessible (requires ffmpeg to be installed)
- Creates a test .env file with the provided RTSP URL
- Tests the docker-compose configuration
- Optionally builds and deploys the services for testing

### 3. Queue Status Check (`check_queues.sh`)

This script monitors the Redis queue status to help identify potential bottlenecks:

```bash
./prod/check_queues.sh
```

The script:
- Checks the length of all Redis queues
- Displays a summary of the queue status
- Provides resource usage information for all containers

## Performance Considerations

- Adjust the `FRAME_SAMPLE_RATE` to control processing load
- Scale each microservice independently based on workload
- Consider using GPU-enabled containers for face detection and recognition

## Testing

To test with the model at `/Users/tanishqsingh/Desktop/projects/YOLO_CCTV/runs/detect/train3/weights/best.pt`, ensure the path is mounted correctly in the Docker Compose configuration.

## Development

For development and contributing, refer to the individual service directories for more detailed information. 