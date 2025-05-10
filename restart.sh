#!/bin/bash

echo "Stopping any running containers..."
docker-compose down

echo "Rebuilding containers with new configuration..."
docker-compose build

echo "Starting containers..."
docker-compose up -d

echo "Containers started in background. Check logs with:"
echo "docker-compose logs -f" 