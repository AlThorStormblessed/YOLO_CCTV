#!/bin/bash

# Production deployment script for YOLO CCTV Application
echo "Starting production deployment with domain names..."

# Check if we're in production mode with domains
if [ "$1" == "prod" ] || [ "$1" == "production" ]; then
  echo "Running in PRODUCTION mode with domain names"
  FRONTEND_DOMAIN="yolo.viewer.in"
  BACKEND_DOMAIN="model.viewer.in"
  
  # Use HTTPS for production
  FRONTEND_URL="https://$FRONTEND_DOMAIN"
  BACKEND_URL="https://$BACKEND_DOMAIN"
  
  # Update docker-compose.yml for production (not needed if already configured in the file)
  # Left here for reference if manual adjustments are needed
  # sed -i.bak "s/NEXT_PUBLIC_SOCKET_HOST: \".*\"/NEXT_PUBLIC_SOCKET_HOST: \"$BACKEND_DOMAIN\"/" docker-compose.yml
  # sed -i.bak "s/NEXT_PUBLIC_API_HOST: \".*\"/NEXT_PUBLIC_API_HOST: \"$BACKEND_DOMAIN\"/" docker-compose.yml
else
  # For development/testing using IP address
  export HOST=$(hostname -I | cut -d' ' -f1)
  echo "Running in DEVELOPMENT mode using IP address: $HOST"
  
  FRONTEND_DOMAIN="$HOST"
  BACKEND_DOMAIN="$HOST"
  
  # Use HTTP for development
  FRONTEND_URL="http://$FRONTEND_DOMAIN:3000"
  BACKEND_URL="http://$BACKEND_DOMAIN:5003"
  
  # Update docker-compose.yml with the local IP
  sed -i.bak "s/NEXT_PUBLIC_SOCKET_HOST: \".*\"/NEXT_PUBLIC_SOCKET_HOST: \"$HOST\"/" docker-compose.yml
  sed -i.bak "s/NEXT_PUBLIC_API_HOST: \".*\"/NEXT_PUBLIC_API_HOST: \"$HOST\"/" docker-compose.yml
  sed -i.bak "s/NEXT_PUBLIC_SOCKET_PROTOCOL: \"https:\"/NEXT_PUBLIC_SOCKET_PROTOCOL: \"http:\"/" docker-compose.yml
  sed -i.bak "s/NEXT_PUBLIC_API_PROTOCOL: \"https:\"/NEXT_PUBLIC_API_PROTOCOL: \"http:\"/" docker-compose.yml
  sed -i.bak "s/NEXT_PUBLIC_SOCKET_PORT: \"443\"/NEXT_PUBLIC_SOCKET_PORT: \"5003\"/" docker-compose.yml
  sed -i.bak "s/NEXT_PUBLIC_API_PORT: \"443\"/NEXT_PUBLIC_API_PORT: \"5003\"/" docker-compose.yml
  sed -i.bak "s/CORS_ORIGINS: \"https:\/\/yolo.viewer.in,http:\/\/yolo.viewer.in\"/CORS_ORIGINS: \"http:\/\/$HOST:3000\"/" docker-compose.yml
fi

# Build and start the containers
echo "Starting Docker Compose services..."
docker-compose up --build -d

echo "Services started!"
echo "Frontend: $FRONTEND_URL"
echo "Backend: $BACKEND_URL"
echo ""
echo "To view logs, run: docker-compose logs -f"
echo "To stop services, run: docker-compose down" 