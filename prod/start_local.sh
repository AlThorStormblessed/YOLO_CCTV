#!/bin/bash

# Exit on any error
set -e

# Setup project paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_DIR="$PROJECT_ROOT/venv"
PID_DIR="$SCRIPT_DIR/pids"
LOG_DIR="$SCRIPT_DIR/logs"

mkdir -p "$LOG_DIR" "$PID_DIR" "$SCRIPT_DIR/migrations"

# Check Docker status
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Activate virtual environment if not active
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "📦 Activating virtual environment..."
    source "$ENV_DIR/bin/activate"
fi

# Load environment variables
if [ -f "$SCRIPT_DIR/.env" ]; then
    echo "📄 Loading environment variables..."
    export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs)
else
    echo "❌ .env file not found. Run setup_local_env.sh first."
    exit 1
fi

# Check model existence
MODEL_PATH=${MODEL_PATH:-"$PROJECT_ROOT/runs/detect/train3/weights/best.pt"}
if [ ! -f "$MODEL_PATH" ]; then
    echo "⚠️ Model not found at $MODEL_PATH"
    read -p "Continue without model? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then exit 1; fi
fi

# Start Docker containers
echo "🐳 Starting Redis and PostgreSQL..."
DOCKER_COMPOSE_FILE="$SCRIPT_DIR/docker-compose-local.yml"
if command -v docker-compose &> /dev/null; then
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
elif docker compose version &> /dev/null; then
    docker compose -f "$DOCKER_COMPOSE_FILE" up -d
else
    echo "❌ Docker Compose not found."
    exit 1
fi

# Wait for Redis
echo "⏳ Waiting for Redis..."
until docker exec face_recognition_redis redis-cli ping 2>/dev/null | grep -q PONG; do
    echo -n "."
    sleep 1
done
echo " ✅ Redis ready!"

# Wait for PostgreSQL
echo "⏳ Waiting for PostgreSQL..."
until docker exec face_recognition_postgres pg_isready -U postgres 2>/dev/null; do
    echo -n "."
    sleep 1
done
echo " ✅ PostgreSQL ready!"

# Set DB env vars
export REDIS_HOST="localhost"
export REDIS_PORT=6379
export POSTGRES_HOST="localhost"
export POSTGRES_PORT=5432
export POSTGRES_USER="postgres"
export POSTGRES_PASSWORD="postgres"
export POSTGRES_DB="face_recognition"
export DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"

# Ensure DB and extension
echo "📦 Initializing DB and pgvector extension..."
docker exec face_recognition_postgres psql -U postgres -c "CREATE DATABASE face_recognition" 2>/dev/null || true
docker exec face_recognition_postgres psql -U postgres -d face_recognition -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null || true

# Generate migration file if needed
if [ ! -f "$SCRIPT_DIR/migrations/001_create_initial_schema.sql" ]; then
    echo "📝 Creating fallback SQL migration..."
    cat > "$SCRIPT_DIR/migrations/001_create_initial_schema.sql" << 'EOF'
-- Initial schema here (unchanged)
-- ...
EOF
fi

# Run Prisma migrations
cd "$SCRIPT_DIR"
echo "⚙️ Running Prisma migrations..."
MIGRATION_SUCCESS=false
if command -v npx &> /dev/null; then
    DATABASE_URL="$DATABASE_URL" npx prisma migrate deploy && MIGRATION_SUCCESS=true || true
else
    echo "⚠️ npx not found, skipping Prisma."
fi

# Apply fallback if Prisma failed
if [ "$MIGRATION_SUCCESS" = false ]; then
    echo "🔁 Applying fallback SQL..."
    docker exec -i face_recognition_postgres psql -U postgres -d face_recognition < "$SCRIPT_DIR/migrations/001_create_initial_schema.sql"
    echo "✅ Fallback schema applied."
fi

# Display info
echo "-----------------------------------------------------------"
echo "Connection Info:"
echo "🔌 Redis: $REDIS_HOST:$REDIS_PORT"
echo "🛢️ PostgreSQL: $POSTGRES_HOST:$POSTGRES_PORT (DB: $POSTGRES_DB)"
echo "📍 DATABASE_URL: $DATABASE_URL"
echo "-----------------------------------------------------------"

# Install local dev package
if ! python -c "import prod" &>/dev/null; then
    echo "📦 Installing local 'prod' package..."
    cd "$PROJECT_ROOT"
    pip install -e .
fi

# Function to launch a service
start_service() {
    local service="$1"
    local module="$2"
    local args="$3"

    echo "🚀 Starting $service..."
    PYTHONPATH="$PROJECT_ROOT" python -m "$module" $args > "$LOG_DIR/${service}.log" 2>&1 &
    echo $! > "$PID_DIR/${service}.pid"
    echo "✅ $service running with PID $(cat "$PID_DIR/${service}.pid")"
}

# Launch services
RTSP_URLS=${RTSP_URLS:-"rtsp://example.com/stream1,https://studentimagess.s3.us-east-1.amazonaws.com/test_video_for_stream_process.mov"}
start_service "stream_processor" "prod.stream_processor.stream_processor" "--urls $RTSP_URLS"
start_service "face_detection" "prod.face_detection.face_detection" "--model $MODEL_PATH --workers 2"
start_service "face_recognition" "prod.face_recognition.face_recognition" "--workers 2 --threshold 0.7"
start_service "result_aggregator" "prod.result_aggregator.result_aggregator" "--workers 2 --ttl 3600"
start_service "web_interface" "prod.web_interface.app" ""

echo "✅ All services launched. Logs: $LOG_DIR"
echo "🌐 Web UI: http://localhost:5000"
echo "🛑 To stop: ./stop_local.sh"
