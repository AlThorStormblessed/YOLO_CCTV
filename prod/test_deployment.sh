#!/bin/bash
set -e

# Colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default RTSP URL - can be overridden by command line argument
RTSP_URL=${1:-"rtsp://admin123:admin123@103.100.219.14:8555/11"}
DOCKER_USERNAME=${2:-"yourusername"}

echo -e "${YELLOW}Testing production deployment with RTSP URL: ${RTSP_URL}${NC}"

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

# Step 1: Test if the RTSP URL is accessible
echo -e "${YELLOW}Testing RTSP URL accessibility...${NC}"
if command -v ffprobe >/dev/null 2>&1; then
    if ffprobe -v quiet -i "$RTSP_URL" -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 -t 5 > /dev/null 2>&1; then
        echo -e "${GREEN}RTSP URL is accessible${NC}"
    else
        echo -e "${RED}RTSP URL is not accessible. Please check the URL and network connectivity${NC}"
        echo -e "${YELLOW}Continuing with testing Docker setup anyway...${NC}"
    fi
else
    echo -e "${YELLOW}ffprobe not found, skipping RTSP URL test${NC}"
    echo -e "${YELLOW}You can install ffmpeg to enable this test${NC}"
fi

# Step 2: Create a test .env file with the RTSP URL
echo -e "${YELLOW}Creating test .env file...${NC}"
cat > "$PROD_DIR/.env" << EOF
# Docker Hub username
DOCKER_USERNAME=${DOCKER_USERNAME}

# RTSP URLs (comma-separated)
RTSP_URLS=${RTSP_URL}

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
EOF

echo -e "${GREEN}Test .env file created${NC}"

# Step 3: Test docker-compose configuration
echo -e "${YELLOW}Testing docker-compose configuration...${NC}"
if docker-compose -f "$PROD_DIR/docker-compose.yml" config > /dev/null; then
    echo -e "${GREEN}Docker-compose configuration is valid${NC}"
else
    echo -e "${RED}Docker-compose configuration is invalid${NC}"
    exit 1
fi

# Step 4: Prompt for deployment
echo -e "${YELLOW}Do you want to deploy the services for testing? (y/n)${NC}"
read -r DEPLOY_CHOICE

if [[ "$DEPLOY_CHOICE" == "y" || "$DEPLOY_CHOICE" == "Y" ]]; then
    echo -e "${YELLOW}Building and deploying services...${NC}"
    
    # Build the base image first
    echo -e "${YELLOW}Building base image...${NC}"
    docker build --platform linux/amd64 -t facerecognition-base:latest -f "$PROD_DIR/Dockerfile.base" .
    
    # Start the services
    echo -e "${YELLOW}Starting services...${NC}"
    docker-compose -f "$PROD_DIR/docker-compose.yml" up -d
    
    # Check if services are running
    echo -e "${YELLOW}Checking if services are running...${NC}"
    running_services=$(docker-compose -f "$PROD_DIR/docker-compose.yml" ps --services --filter "status=running" | wc -l)
    total_services=$(docker-compose -f "$PROD_DIR/docker-compose.yml" ps --services | wc -l)
    
    echo -e "${YELLOW}Running services: ${running_services} out of ${total_services}${NC}"
    
    if [ "$running_services" -eq "$total_services" ]; then
        echo -e "${GREEN}All services are running!${NC}"
    else
        echo -e "${RED}Some services are not running. Please check the logs:${NC}"
        echo -e "${YELLOW}docker-compose -f $PROD_DIR/docker-compose.yml logs${NC}"
    fi
    
    # Show service status
    echo -e "${YELLOW}Service status:${NC}"
    docker-compose -f "$PROD_DIR/docker-compose.yml" ps
    
    echo -e "${YELLOW}Viewing logs for 20 seconds... Press Ctrl+C to stop${NC}"
    timeout 20 docker-compose -f "$PROD_DIR/docker-compose.yml" logs -f || true
    
    echo -e "${GREEN}Testing completed!${NC}"
    echo -e "${YELLOW}Use these commands for further investigation:${NC}"
    echo -e "${YELLOW}- View logs: docker-compose -f $PROD_DIR/docker-compose.yml logs -f${NC}"
    echo -e "${YELLOW}- Stop services: docker-compose -f $PROD_DIR/docker-compose.yml down${NC}"
else
    echo -e "${YELLOW}Deployment skipped. Configuration tests completed.${NC}"
fi 