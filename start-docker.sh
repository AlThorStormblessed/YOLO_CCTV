#!/bin/bash

# Production deployment script for YOLO CCTV Application
echo "Starting production deployment..."

# Check if we're in production mode with domains
if [ "$1" == "prod" ] || [ "$1" == "production" ]; then
  echo "Running in PRODUCTION mode"
  FRONTEND_DOMAIN="yolo.viewer.in"
  BACKEND_DOMAIN="model.viewer.in"
  
  # The actual server public IP address
  SERVER_IP="16.171.224.154"
  
  # Use HTTP for now since HTTPS is not fully configured
  FRONTEND_URL="http://$SERVER_IP:3000"
  BACKEND_URL="http://$SERVER_IP:5003"
  
  # Update docker-compose.yml for production with IP address for direct communication
  sed -i.bak "s/NEXT_PUBLIC_SOCKET_HOST: \".*\"/NEXT_PUBLIC_SOCKET_HOST: \"$SERVER_IP\"/" docker-compose.yml
  sed -i.bak "s/NEXT_PUBLIC_API_HOST: \".*\"/NEXT_PUBLIC_API_HOST: \"$SERVER_IP\"/" docker-compose.yml
  sed -i.bak "s/NEXT_PUBLIC_SOCKET_PROTOCOL: \".*\"/NEXT_PUBLIC_SOCKET_PROTOCOL: \"http:\"/" docker-compose.yml
  sed -i.bak "s/NEXT_PUBLIC_API_PROTOCOL: \".*\"/NEXT_PUBLIC_API_PROTOCOL: \"http:\"/" docker-compose.yml
  sed -i.bak "s/NEXT_PUBLIC_SOCKET_PORT: \".*\"/NEXT_PUBLIC_SOCKET_PORT: \"5003\"/" docker-compose.yml
  sed -i.bak "s/NEXT_PUBLIC_API_PORT: \".*\"/NEXT_PUBLIC_API_PORT: \"5003\"/" docker-compose.yml
  
  # Update CORS settings to include all possible access URLs
  CORS_ORIGINS="\"https://yolo.viewer.in,http://yolo.viewer.in,http://$SERVER_IP:3000,http://$SERVER_IP:3003,http://model.viewer.in:5003,https://model.viewer.in\""
  sed -i.bak "s/CORS_ORIGINS: \".*\"/CORS_ORIGINS: $CORS_ORIGINS/" docker-compose.yml
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
  sed -i.bak "s/NEXT_PUBLIC_SOCKET_PROTOCOL: \".*\"/NEXT_PUBLIC_SOCKET_PROTOCOL: \"http:\"/" docker-compose.yml
  sed -i.bak "s/NEXT_PUBLIC_API_PROTOCOL: \".*\"/NEXT_PUBLIC_API_PROTOCOL: \"http:\"/" docker-compose.yml
  sed -i.bak "s/NEXT_PUBLIC_SOCKET_PORT: \".*\"/NEXT_PUBLIC_SOCKET_PORT: \"5003\"/" docker-compose.yml
  sed -i.bak "s/NEXT_PUBLIC_API_PORT: \".*\"/NEXT_PUBLIC_API_PORT: \"5003\"/" docker-compose.yml
  
  # Update CORS settings for development
  CORS_ORIGINS="\"http://$HOST:3000\""
  sed -i.bak "s/CORS_ORIGINS: \".*\"/CORS_ORIGINS: $CORS_ORIGINS/" docker-compose.yml
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