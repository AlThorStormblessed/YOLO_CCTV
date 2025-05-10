#!/bin/bash

# Set the host IP or hostname for accessing the services
# This will be used for the frontend to connect to the backend
export HOST=$(hostname -I | cut -d' ' -f1)
echo "Using host: $HOST"

# Update docker-compose.yml with the correct host
sed -i.bak "s/NEXT_PUBLIC_SOCKET_HOST: \"localhost\"/NEXT_PUBLIC_SOCKET_HOST: \"$HOST\"/" docker-compose.yml
sed -i.bak "s/NEXT_PUBLIC_API_HOST: \"localhost\"/NEXT_PUBLIC_API_HOST: \"$HOST\"/" docker-compose.yml

# Build and start the containers
echo "Starting Docker Compose services..."
docker-compose up --build -d

echo "Services started!"
echo "Frontend: http://$HOST:3000"
echo "Backend: http://$HOST:5001"
echo ""
echo "To view logs, run: docker-compose logs -f"
echo "To stop services, run: docker-compose down" 