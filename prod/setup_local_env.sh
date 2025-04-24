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

echo "Checking Redis installation..."
if ! command -v redis-server &> /dev/null; then
    echo "Warning: Redis server not found. Please install Redis:"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  For macOS: brew install redis"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "  For Ubuntu/Debian: sudo apt-get install redis-server"
        echo "  For CentOS/RHEL: sudo yum install redis"
    else
        echo "  Please install Redis for your OS: https://redis.io/download"
    fi
fi

echo "Checking PostgreSQL installation..."
if ! command -v psql &> /dev/null; then
    echo "Warning: PostgreSQL not found. Please install PostgreSQL with pgvector extension:"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  For macOS: brew install postgresql"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "  For Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib"
        echo "  For CentOS/RHEL: sudo yum install postgresql-server postgresql-contrib"
    else
        echo "  Please install PostgreSQL for your OS: https://www.postgresql.org/download/"
    fi
    echo "  Then install pgvector extension: https://github.com/pgvector/pgvector"
fi

# Create a local .env file if it doesn't exist
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo "Creating default .env file..."
    cp "$SCRIPT_DIR/env.template" "$SCRIPT_DIR/.env"
    echo "Please edit $SCRIPT_DIR/.env with your configuration."
else
    echo ".env file already exists."
fi

echo "Environment setup complete! Activate it with:"
echo "  source $ENV_DIR/bin/activate"
echo ""
echo "Start the system with:"
echo "  ./start_local.sh" 