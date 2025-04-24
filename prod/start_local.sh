#!/bin/bash

# Exit on error
set -e

# Script to start the face recognition system locally
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_DIR="$PROJECT_ROOT/venv"
PID_DIR="$SCRIPT_DIR/pids"
LOG_DIR="$SCRIPT_DIR/logs"

# Make sure the virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Activating virtual environment..."
    source "$ENV_DIR/bin/activate"
fi

# Create directories for logs and pids if they don't exist
mkdir -p "$LOG_DIR"
mkdir -p "$PID_DIR"

# Load environment variables from .env file
if [ -f "$SCRIPT_DIR/.env" ]; then
    echo "Loading environment variables from .env..."
    export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs)
else
    echo "Error: .env file not found. Please run setup_local_env.sh first."
    exit 1
fi

# Check if the model file exists
MODEL_PATH=${MODEL_PATH:-"$PROJECT_ROOT/runs/detect/train3/weights/best.pt"}
if [ ! -f "$MODEL_PATH" ]; then
    echo "Warning: Model file not found at $MODEL_PATH"
    echo "Please make sure the model file exists or update the MODEL_PATH in your .env file."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Start Redis if it's not already running
if ! pgrep -x "redis-server" > /dev/null; then
    echo "Starting Redis server..."
    redis-server --daemonize yes
    echo "Redis server started."
else
    echo "Redis server is already running."
fi

# Start PostgreSQL if it's not already running
if [[ "$OSTYPE" == "darwin"* ]]; then
    if ! brew services list | grep postgresql | grep started > /dev/null; then
        echo "Starting PostgreSQL..."
        brew services start postgresql
        echo "PostgreSQL started."
    else
        echo "PostgreSQL is already running."
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if ! systemctl is-active --quiet postgresql; then
        echo "Starting PostgreSQL..."
        sudo systemctl start postgresql
        echo "PostgreSQL started."
    else
        echo "PostgreSQL is already running."
    fi
else
    echo "Please ensure PostgreSQL is running."
fi

# Set up environment variables for local development
export REDIS_HOST=${REDIS_HOST:-"localhost"}
export REDIS_PORT=${REDIS_PORT:-6379}
export POSTGRES_HOST=${POSTGRES_HOST:-"localhost"}
export POSTGRES_PORT=${POSTGRES_PORT:-5432}
export POSTGRES_USER=${POSTGRES_USER:-"postgres"}
export POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-"postgres"}
export POSTGRES_DB=${POSTGRES_DB:-"face_recognition"}
export DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"

# Function to start a service
start_service() {
    local service=$1
    local module=$2
    local args=$3

    echo "Starting $service service..."
    python -m $module $args > "$LOG_DIR/${service}.log" 2>&1 &
    local pid=$!
    echo $pid > "$PID_DIR/${service}.pid"
    echo "$service started with PID $pid"
}

# Start stream processor service
RTSP_URLS=${RTSP_URLS:-"rtsp://example.com/stream1"}
start_service "stream_processor" "prod.stream_processor.stream_processor" "--urls $RTSP_URLS"

# Start face detection service
start_service "face_detection" "prod.face_detection.face_detection" "--model $MODEL_PATH --workers 2"

# Start face recognition service
start_service "face_recognition" "prod.face_recognition.face_recognition" "--workers 2 --threshold 0.7"

# Start result aggregator service
start_service "result_aggregator" "prod.result_aggregator.result_aggregator" "--workers 2 --ttl 3600"

# Start web service for remote access
start_service "web_interface" "prod.web_interface" ""

echo "All services started! Check logs in $LOG_DIR directory."
echo "To stop all services, run: ./stop_local.sh" 