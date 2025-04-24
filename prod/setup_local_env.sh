#!/bin/bash

# Exit on error
set -e

# Script to set up a local development environment for the face recognition system
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_NAME="face_recognition_env"
ENV_DIR="$PROJECT_ROOT/venv"

# Check if we're already in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "Error: You are already in a virtual environment. Please deactivate it first."
    exit 1
fi

# Create directories for logs and pids
mkdir -p "$SCRIPT_DIR/logs"
mkdir -p "$SCRIPT_DIR/pids"

echo "Setting up local environment in $ENV_DIR..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed. Please install Python 3 and try again."
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is required but not installed. Please install Docker and try again."
    echo "Visit https://docs.docker.com/get-docker/ for installation instructions."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is required but not installed."
    echo "For newer Docker installations, it should be included as 'docker compose'."
    echo "If using older Docker versions, please install Docker Compose separately."
    echo "Visit https://docs.docker.com/compose/install/ for installation instructions."
    
    # Check for new docker compose command format
    if ! docker compose version &> /dev/null; then
        exit 1
    else
        echo "Found Docker Compose as 'docker compose'."
    fi
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$ENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$ENV_DIR"
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
source "$ENV_DIR/bin/activate"

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r "$SCRIPT_DIR/local_requirements.txt"

# Generate Prisma client
echo "Generating Prisma client..."
cd "$SCRIPT_DIR"
if ! command -v prisma &> /dev/null; then
    npm install -g prisma
fi
prisma generate

echo "Checking Docker and Docker Compose..."
echo "Docker and Docker Compose will be used to run Redis and PostgreSQL with pgvector."

# Create a local .env file if it doesn't exist
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo "Creating default .env file..."
    cp "$SCRIPT_DIR/env.template" "$SCRIPT_DIR/.env"
    
    # Set Redis and PostgreSQL host to localhost in the .env file
    sed -i 's/REDIS_HOST=redis/REDIS_HOST=localhost/g' "$SCRIPT_DIR/.env" 2>/dev/null || \
    sed -i '' 's/REDIS_HOST=redis/REDIS_HOST=localhost/g' "$SCRIPT_DIR/.env"
    
    sed -i 's/POSTGRES_HOST=postgres/POSTGRES_HOST=localhost/g' "$SCRIPT_DIR/.env" 2>/dev/null || \
    sed -i '' 's/POSTGRES_HOST=postgres/POSTGRES_HOST=localhost/g' "$SCRIPT_DIR/.env"
    
    echo "Please edit $SCRIPT_DIR/.env with your configuration."
else
    echo ".env file already exists."
fi

echo "Environment setup complete! Activate it with:"
echo "  source $ENV_DIR/bin/activate"
echo ""
echo "Start the system with:"
echo "  ./start_local.sh"
echo ""
echo "Redis and PostgreSQL will be started in Docker containers." 