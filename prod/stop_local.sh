#!/bin/bash

# Exit on error
set -e

# Script to stop the face recognition system
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PID_DIR="$SCRIPT_DIR/pids"

echo "Stopping all services..."

# Stop services by PIDs
if [ -d "$PID_DIR" ]; then
    for pid_file in "$PID_DIR"/*.pid; do
        if [ -f "$pid_file" ]; then
            service_name=$(basename "$pid_file" .pid)
            pid=$(cat "$pid_file")
            
            echo "Stopping $service_name (PID: $pid)..."
            
            if ps -p $pid > /dev/null; then
                kill $pid
                echo "$service_name stopped."
            else
                echo "$service_name was not running."
            fi
            
            # Remove PID file
            rm "$pid_file"
        fi
    done
else
    echo "No PID directory found at $PID_DIR."
fi

# Ask if Redis and PostgreSQL Docker containers should be stopped
read -p "Do you want to stop Redis and PostgreSQL Docker containers? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Stopping Docker containers..."
    
    if command -v docker-compose &> /dev/null; then
        # Using docker-compose command
        docker-compose -f "$SCRIPT_DIR/docker-compose-local.yml" down
    elif docker compose version &> /dev/null; then
        # Using docker compose subcommand
        docker compose -f "$SCRIPT_DIR/docker-compose-local.yml" down
    else
        echo "Warning: Docker Compose not found, trying to stop containers manually."
        
        # Stop Redis container if it exists
        if docker ps -q -f name=face_recognition_redis | grep -q .; then
            echo "Stopping Redis container..."
            docker stop face_recognition_redis
        fi
        
        # Stop PostgreSQL container if it exists
        if docker ps -q -f name=face_recognition_postgres | grep -q .; then
            echo "Stopping PostgreSQL container..."
            docker stop face_recognition_postgres
        fi
    fi
    
    echo "Docker containers stopped."
else
    echo "Redis and PostgreSQL Docker containers left running."
fi

echo "All services stopped." 