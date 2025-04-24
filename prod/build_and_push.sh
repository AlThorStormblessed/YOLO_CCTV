#!/bin/bash
set -e

# Colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Set your Docker Hub username
DOCKER_USERNAME=${1:-"yourusername"}

# Version tag
VERSION="0.1.0"

# Platform flag for compatibility
PLATFORM_FLAG="--platform linux/amd64"

# Determine if we're in the prod directory or project root
SCRIPT_DIR=$(dirname "$(realpath "$0")")
if [[ $SCRIPT_DIR == */prod ]]; then
    # We're in the prod directory
    PROD_DIR="$SCRIPT_DIR"
    PROJECT_ROOT=$(dirname "$SCRIPT_DIR")
else
    # We're in the project root
    PROD_DIR="$SCRIPT_DIR/prod"
    PROJECT_ROOT="$SCRIPT_DIR"
fi

# Navigate to the project root
cd "$PROJECT_ROOT" || exit 1

echo -e "${YELLOW}Building images from directory: ${PROJECT_ROOT}${NC}"
echo -e "${YELLOW}Using prod directory: ${PROD_DIR}${NC}"

# Build the base image first
echo -e "${YELLOW}Building base image...${NC}"
docker build $PLATFORM_FLAG -t facerecognition-base:latest -f "${PROD_DIR}/Dockerfile.base" .

# Build each service
echo -e "${YELLOW}Building Stream Processor image...${NC}"
docker build $PLATFORM_FLAG -t $DOCKER_USERNAME/facerecognition-stream-processor:$VERSION -f "${PROD_DIR}/stream_processor/Dockerfile" .
docker tag $DOCKER_USERNAME/facerecognition-stream-processor:$VERSION $DOCKER_USERNAME/facerecognition-stream-processor:latest

echo -e "${YELLOW}Building Face Detection image...${NC}"
docker build $PLATFORM_FLAG -t $DOCKER_USERNAME/facerecognition-face-detection:$VERSION -f "${PROD_DIR}/face_detection/Dockerfile" .
docker tag $DOCKER_USERNAME/facerecognition-face-detection:$VERSION $DOCKER_USERNAME/facerecognition-face-detection:latest

echo -e "${YELLOW}Building Face Recognition image...${NC}"
docker build $PLATFORM_FLAG -t $DOCKER_USERNAME/facerecognition-face-recognition:$VERSION -f "${PROD_DIR}/face_recognition/Dockerfile" .
docker tag $DOCKER_USERNAME/facerecognition-face-recognition:$VERSION $DOCKER_USERNAME/facerecognition-face-recognition:latest

echo -e "${YELLOW}Building Result Aggregator image...${NC}"
docker build $PLATFORM_FLAG -t $DOCKER_USERNAME/facerecognition-result-aggregator:$VERSION -f "${PROD_DIR}/result_aggregator/Dockerfile" .
docker tag $DOCKER_USERNAME/facerecognition-result-aggregator:$VERSION $DOCKER_USERNAME/facerecognition-result-aggregator:latest

# Push images to Docker Hub if requested
if [ "$2" == "--push" ]; then
    echo -e "${YELLOW}Logging into Docker Hub...${NC}"
    docker login -u $DOCKER_USERNAME
    
    echo -e "${YELLOW}Pushing images to Docker Hub...${NC}"
    docker push $DOCKER_USERNAME/facerecognition-stream-processor:$VERSION
    docker push $DOCKER_USERNAME/facerecognition-stream-processor:latest
    
    docker push $DOCKER_USERNAME/facerecognition-face-detection:$VERSION
    docker push $DOCKER_USERNAME/facerecognition-face-detection:latest
    
    docker push $DOCKER_USERNAME/facerecognition-face-recognition:$VERSION
    docker push $DOCKER_USERNAME/facerecognition-face-recognition:latest
    
    docker push $DOCKER_USERNAME/facerecognition-result-aggregator:$VERSION
    docker push $DOCKER_USERNAME/facerecognition-result-aggregator:latest
    
    echo -e "${GREEN}Successfully pushed all images to Docker Hub${NC}"
else
    echo -e "${GREEN}Images built successfully. Use '$0 $DOCKER_USERNAME --push' to push to Docker Hub.${NC}"
fi 