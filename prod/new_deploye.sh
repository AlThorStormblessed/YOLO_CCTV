#!/bin/bash
set -e

# Colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting cleanup and redeployment process...${NC}"

# Navigate to the project directory if not already there
cd "$(dirname "$0")/.." || exit 1

# Stop all running containers
echo -e "${YELLOW}Stopping all running containers...${NC}"
docker-compose -f prod/docker-compose.yml down

# Remove old face recognition containers
echo -e "${YELLOW}Removing old face recognition containers...${NC}"
docker ps -a | grep 'facerecognition' | awk '{print $1}' | xargs -r docker rm -f

# Remove dangling images
echo -e "${YELLOW}Removing dangling images...${NC}"
docker images | grep '<none>' | awk '{print $3}' | xargs -r docker rmi

# Remove old face recognition images
echo -e "${YELLOW}Removing old face recognition images...${NC}"
docker images | grep 'facerecognition' | awk '{print $3}' | xargs -r docker rmi

# Pull latest images if using Docker Hub
# Uncomment if pulling from registry rather than building locally
# echo -e "${YELLOW}Pulling latest images...${NC}"
# DOCKER_USERNAME=${1:-"yourusername"}
# docker pull $DOCKER_USERNAME/facerecognition-stream-processor:latest
# docker pull $DOCKER_USERNAME/facerecognition-face-detection:latest
# docker pull $DOCKER_USERNAME/facerecognition-face-recognition:latest
# docker pull $DOCKER_USERNAME/facerecognition-result-aggregator:latest

# Build new images
echo -e "${YELLOW}Building new images...${NC}"
./prod/build_and_push.sh ${1:-"yourusername"}

# Restart the services
echo -e "${YELLOW}Starting services...${NC}"
docker-compose -f prod/docker-compose.yml up -d

# Check if the services are running
echo -e "${YELLOW}Checking service status...${NC}"
docker-compose -f prod/docker-compose.yml ps

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${YELLOW}View logs with: docker-compose -f prod/docker-compose.yml logs -f${NC}" 