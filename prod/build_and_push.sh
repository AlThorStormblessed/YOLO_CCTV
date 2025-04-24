#!/bin/bash
set -e

# Set your Docker Hub username
DOCKER_USERNAME=${1:-"yashs3324"}

# Version tag
VERSION="0.1.0"

# Platform flag for compatibility
PLATFORM_FLAG="--platform linux/amd64"

# Build the base image first
echo "Building base image..."
docker build $PLATFORM_FLAG -t facerecognition-base:latest -f prod/Dockerfile.base .

# Build each service
echo "Building Stream Processor image..."
docker build $PLATFORM_FLAG -t $DOCKER_USERNAME/facerecognition-stream-processor:$VERSION -f prod/stream_processor/Dockerfile .
docker tag $DOCKER_USERNAME/facerecognition-stream-processor:$VERSION $DOCKER_USERNAME/facerecognition-stream-processor:latest

echo "Building Face Detection image..."
docker build $PLATFORM_FLAG -t $DOCKER_USERNAME/facerecognition-face-detection:$VERSION -f prod/face_detection/Dockerfile .
docker tag $DOCKER_USERNAME/facerecognition-face-detection:$VERSION $DOCKER_USERNAME/facerecognition-face-detection:latest

echo "Building Face Recognition image..."
docker build $PLATFORM_FLAG -t $DOCKER_USERNAME/facerecognition-face-recognition:$VERSION -f prod/face_recognition/Dockerfile .
docker tag $DOCKER_USERNAME/facerecognition-face-recognition:$VERSION $DOCKER_USERNAME/facerecognition-face-recognition:latest

echo "Building Result Aggregator image..."
docker build $PLATFORM_FLAG -t $DOCKER_USERNAME/facerecognition-result-aggregator:$VERSION -f prod/result_aggregator/Dockerfile .
docker tag $DOCKER_USERNAME/facerecognition-result-aggregator:$VERSION $DOCKER_USERNAME/facerecognition-result-aggregator:latest

# Push images to Docker Hub if requested
if [ "$2" == "--push" ]; then
    echo "Logging into Docker Hub..."
    docker login -u $DOCKER_USERNAME
    
    echo "Pushing images to Docker Hub..."
    docker push $DOCKER_USERNAME/facerecognition-stream-processor:$VERSION
    docker push $DOCKER_USERNAME/facerecognition-stream-processor:latest
    
    docker push $DOCKER_USERNAME/facerecognition-face-detection:$VERSION
    docker push $DOCKER_USERNAME/facerecognition-face-detection:latest
    
    docker push $DOCKER_USERNAME/facerecognition-face-recognition:$VERSION
    docker push $DOCKER_USERNAME/facerecognition-face-recognition:latest
    
    docker push $DOCKER_USERNAME/facerecognition-result-aggregator:$VERSION
    docker push $DOCKER_USERNAME/facerecognition-result-aggregator:latest
    
    echo "Successfully pushed all images to Docker Hub"
else
    echo "Images built successfully. Use '$0 $DOCKER_USERNAME --push' to push to Docker Hub."
fi 