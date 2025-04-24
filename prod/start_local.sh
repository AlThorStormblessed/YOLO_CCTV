#!/bin/bash

# Exit on error
set -e

# Script to start the face recognition system locally
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_DIR="$PROJECT_ROOT/venv"
PID_DIR="$SCRIPT_DIR/pids"
LOG_DIR="$SCRIPT_DIR/logs"

# Create migrations directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/migrations"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

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

# Start Redis and PostgreSQL using Docker Compose
echo "Starting Redis and PostgreSQL using Docker..."
if command -v docker-compose &> /dev/null; then
    # Using docker-compose command
    docker-compose -f "$SCRIPT_DIR/docker-compose-local.yml" up -d
elif docker compose version &> /dev/null; then
    # Using docker compose subcommand
    docker compose -f "$SCRIPT_DIR/docker-compose-local.yml" up -d
else
    echo "Error: Cannot find Docker Compose. Please install Docker Compose and try again."
    exit 1
fi

# Wait for services to be ready
echo "Waiting for Redis to be ready..."
until docker exec face_recognition_redis redis-cli ping 2>/dev/null | grep -q PONG; do
    echo -n "."
    sleep 1
done
echo " Redis is ready!"

echo "Waiting for PostgreSQL to be ready..."
until docker exec face_recognition_postgres pg_isready -U postgres 2>/dev/null; do
    echo -n "."
    sleep 1
done
echo " PostgreSQL is ready!"

# Ensure we're using localhost for database connection
export REDIS_HOST="localhost"
export REDIS_PORT=6379
export POSTGRES_HOST="localhost"
export POSTGRES_PORT=5432
export POSTGRES_USER="postgres"
export POSTGRES_PASSWORD="postgres"
export POSTGRES_DB="face_recognition"
export DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"

# Initialize the database and create pgvector extension
echo "Initializing PostgreSQL database and pgvector extension..."
# First ensure the database exists
docker exec face_recognition_postgres psql -U postgres -c "CREATE DATABASE face_recognition WITH OWNER postgres" 2>/dev/null || echo "Database already exists"

# Then create the pgvector extension
docker exec face_recognition_postgres psql -U postgres -d face_recognition -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null || echo "Could not create vector extension"

# Create the SQL migration file if it doesn't exist
if [ ! -f "$SCRIPT_DIR/migrations/001_create_initial_schema.sql" ]; then
    echo "Creating SQL migration file..."
    cat > "$SCRIPT_DIR/migrations/001_create_initial_schema.sql" << 'EOL'
-- Initial schema for face recognition system
-- This file is used if Prisma migrations fail

-- Make sure the vector extension is enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Create Person table
CREATE TABLE IF NOT EXISTS "Person" (
    "id" TEXT PRIMARY KEY,
    "name" TEXT NOT NULL,
    "faceVector" vector(512),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create Face table
CREATE TABLE IF NOT EXISTS "Face" (
    "id" TEXT PRIMARY KEY,
    "imageData" BYTEA NOT NULL,
    "faceVector" vector(512),
    "personId" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "Face_personId_fkey" FOREIGN KEY ("personId") REFERENCES "Person"("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Create Detection table
CREATE TABLE IF NOT EXISTS "Detection" (
    "id" TEXT PRIMARY KEY,
    "streamId" TEXT NOT NULL,
    "timestamp" DOUBLE PRECISION NOT NULL,
    "bbox" JSONB NOT NULL,
    "confidence" DOUBLE PRECISION NOT NULL,
    "personId" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "processedAt" DOUBLE PRECISION NOT NULL,
    CONSTRAINT "Detection_personId_fkey" FOREIGN KEY ("personId") REFERENCES "Person"("id") ON DELETE SET NULL ON UPDATE CASCADE
);

-- Create Stream table
CREATE TABLE IF NOT EXISTS "Stream" (
    "id" TEXT PRIMARY KEY,
    "name" TEXT NOT NULL,
    "rtspUrl" TEXT NOT NULL UNIQUE,
    "description" TEXT,
    "active" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS "Person_faceVector_idx" ON "Person" USING gist("faceVector");
CREATE INDEX IF NOT EXISTS "Face_faceVector_idx" ON "Face" USING gist("faceVector");
CREATE INDEX IF NOT EXISTS "Detection_streamId_timestamp_idx" ON "Detection"("streamId", "timestamp");
EOL
fi

# Run Prisma migrations
echo "Running Prisma migrations..."
cd "$SCRIPT_DIR"
MIGRATION_SUCCESS=false
if command -v npx &> /dev/null; then
    # Use the correct DATABASE_URL for Prisma
    DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}" \
    npx prisma migrate deploy && MIGRATION_SUCCESS=true || echo "Failed to run Prisma migrations. Falling back to manual SQL script."
else
    echo "Warning: npx not found. Skipping Prisma migrations. Using manual SQL script instead."
fi

# If Prisma migrations failed, run the SQL script directly
if [ "$MIGRATION_SUCCESS" = false ]; then
    echo "Applying manual SQL migrations..."
    if [ -f "$SCRIPT_DIR/migrations/001_create_initial_schema.sql" ]; then
        docker exec -i face_recognition_postgres psql -U postgres -d face_recognition < "$SCRIPT_DIR/migrations/001_create_initial_schema.sql"
        echo "Manual SQL migrations applied."
    else
        echo "Error: Manual SQL migration file not found at $SCRIPT_DIR/migrations/001_create_initial_schema.sql"
        echo "Database schema may not be properly initialized."
    fi
fi

# Display connection information
echo "-----------------------------------------------------------"
echo "Connection Information:"
echo "Redis: $REDIS_HOST:$REDIS_PORT"
echo "PostgreSQL: $POSTGRES_HOST:$POSTGRES_PORT (user: $POSTGRES_USER, db: $POSTGRES_DB)"
echo "Database URL: $DATABASE_URL"
echo "-----------------------------------------------------------"

# Install the prod package if not already installed
if ! python -c "import prod" &>/dev/null; then
    echo "Installing the prod package in development mode..."
    cd "$PROJECT_ROOT"
    pip install -e .
fi

# Function to start a service with proper PYTHONPATH
start_service() {
    local service=$1
    local module=$2
    local args=$3

    echo "Starting $service service..."
    PYTHONPATH="$PROJECT_ROOT" python -m $module $args > "$LOG_DIR/${service}.log" 2>&1 &
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
echo "Web interface available at: http://localhost:5000"
echo "To stop all services, run: ./stop_local.sh" 