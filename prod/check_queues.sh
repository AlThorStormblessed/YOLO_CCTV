#!/bin/bash
set -e

# Colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Queue names
FRAMES_QUEUE="frames_queue"
FACES_QUEUE="faces_queue"
RECOGNITION_QUEUE="recognition_queue"
RESULTS_STORE="results_store"
KNOWN_FACES_STORE="known_faces"

# Check if Redis container is running
if ! docker ps | grep -q "face_recognition_redis"; then
    echo -e "${RED}Redis container is not running. Please start the services first.${NC}"
    exit 1
fi

# Function to check queue length
check_queue_length() {
    local queue=$1
    local length
    length=$(docker exec face_recognition_redis redis-cli LLEN "$queue")
    echo -e "${BLUE}$queue${NC}: ${length} items"
}

# Function to check hash size
check_hash_size() {
    local hash=$1
    local size
    size=$(docker exec face_recognition_redis redis-cli HLEN "$hash")
    echo -e "${BLUE}$hash${NC}: ${size} items"
}

echo -e "${YELLOW}Checking Redis queue lengths...${NC}"
check_queue_length $FRAMES_QUEUE
check_queue_length $FACES_QUEUE
check_queue_length $RECOGNITION_QUEUE
check_hash_size $RESULTS_STORE
check_hash_size $KNOWN_FACES_STORE

echo -e "\n${YELLOW}Queue status summary:${NC}"
total_items=$(($(docker exec face_recognition_redis redis-cli LLEN "$FRAMES_QUEUE") + \
               $(docker exec face_recognition_redis redis-cli LLEN "$FACES_QUEUE") + \
               $(docker exec face_recognition_redis redis-cli LLEN "$RECOGNITION_QUEUE")))

if [ "$total_items" -eq 0 ]; then
    echo -e "${GREEN}All queues are empty. System is processing in real-time.${NC}"
elif [ "$total_items" -lt 10 ]; then
    echo -e "${GREEN}Queue backlog is minimal ($total_items items). System is running well.${NC}"
elif [ "$total_items" -lt 50 ]; then
    echo -e "${YELLOW}Moderate queue backlog ($total_items items). System is keeping up.${NC}"
else
    echo -e "${RED}Large queue backlog ($total_items items). System may be overwhelmed.${NC}"
    echo -e "${YELLOW}Consider scaling up services with:${NC}"
    echo -e "${YELLOW}docker-compose -f prod/docker-compose.yml up -d --scale face_detection=3 --scale face_recognition=3${NC}"
fi

# Get container resource usage
echo -e "\n${YELLOW}Container resource usage:${NC}"
docker stats --no-stream $(docker-compose -f prod/docker-compose.yml ps -q) | grep -v "CONTAINER ID" 