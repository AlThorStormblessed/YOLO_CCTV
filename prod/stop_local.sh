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

# Don't stop Redis and PostgreSQL by default, as they might be used by other applications
# Ask the user if they want to stop these services
read -p "Do you want to stop Redis and PostgreSQL? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Check if Redis is running and stop it
    if pgrep -x "redis-server" > /dev/null; then
        echo "Stopping Redis server..."
        redis-cli shutdown
        echo "Redis server stopped."
    else
        echo "Redis server was not running."
    fi
    
    # Stop PostgreSQL based on OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if brew services list | grep postgresql | grep started > /dev/null; then
            echo "Stopping PostgreSQL..."
            brew services stop postgresql
            echo "PostgreSQL stopped."
        else
            echo "PostgreSQL was not running."
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if systemctl is-active --quiet postgresql; then
            echo "Stopping PostgreSQL..."
            sudo systemctl stop postgresql
            echo "PostgreSQL stopped."
        else
            echo "PostgreSQL was not running."
        fi
    else
        echo "Unsupported OS. Please stop PostgreSQL manually if needed."
    fi
fi

echo "All services stopped." 