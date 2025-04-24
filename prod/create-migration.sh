#!/bin/bash

# Exit on error
set -e

# Script to create Prisma migrations
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is required but not installed. Please install Node.js and try again."
    echo "Visit https://nodejs.org/ for installation instructions."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "Error: npm is required but not installed. Please install npm and try again."
    exit 1
fi

# Check if docker containers are running
if ! docker ps | grep -q face_recognition_postgres; then
    echo "Warning: PostgreSQL container is not running. Starting it now..."
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$SCRIPT_DIR/docker-compose-local.yml" up -d postgres
    elif docker compose version &> /dev/null; then
        docker compose -f "$SCRIPT_DIR/docker-compose-local.yml" up -d postgres
    else
        echo "Error: Cannot find Docker Compose. Please start the PostgreSQL container manually."
        exit 1
    fi
    
    # Wait for PostgreSQL to be ready
    echo "Waiting for PostgreSQL to be ready..."
    until docker exec face_recognition_postgres pg_isready -U postgres 2>/dev/null; do
        echo -n "."
        sleep 1
    done
    echo " PostgreSQL is ready!"
fi

# Ensure the database exists
echo "Ensuring database exists..."
docker exec face_recognition_postgres psql -U postgres -c "CREATE DATABASE face_recognition WITH OWNER postgres" || echo "Database already exists"

# Set up environment variables for migration
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5432"
export POSTGRES_USER="postgres"
export POSTGRES_PASSWORD="postgres"
export POSTGRES_DB="face_recognition"
export DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"

echo "DATABASE_URL=$DATABASE_URL"

# Change to the project directory
cd "$SCRIPT_DIR"

# Ensure package.json exists
if [ ! -f "$SCRIPT_DIR/package.json" ]; then
    echo "Creating package.json file..."
    cat > "$SCRIPT_DIR/package.json" << EOL
{
  "name": "face-recognition-system",
  "version": "1.0.0",
  "description": "Face Recognition System",
  "main": "index.js",
  "scripts": {
    "test": "echo \"Error: no test specified\" && exit 1"
  },
  "prisma": {
    "schema": "prisma/schema.prisma"
  },
  "keywords": [],
  "author": "",
  "license": "ISC",
  "dependencies": {
    "@prisma/client": "^5.4.2",
    "prisma": "^5.4.2"
  }
}
EOL
fi

# Install dependencies if needed
if [ ! -d "$SCRIPT_DIR/node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi

# Get migration name
if [ -z "$1" ]; then
    read -p "Enter migration name (e.g., 'init'): " MIGRATION_NAME
else
    MIGRATION_NAME="$1"
fi

# Create Prisma migration
echo "Creating Prisma migration '$MIGRATION_NAME'..."
npx prisma migrate dev --name "$MIGRATION_NAME"

echo "Migration created successfully!"
echo "To apply the migration during startup, run: ./start_local.sh" 