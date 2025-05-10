#!/bin/bash

# Production deployment script for YOLO CCTV Application
echo "Starting deployment..."

# Check if we're in production mode with domains
if [ "$1" == "prod" ] || [ "$1" == "production" ]; then
  echo "Running in PRODUCTION mode with domain names"
  FRONTEND_DOMAIN="yolo.viewer.in"
  BACKEND_DOMAIN="model.viewer.in"
  
  # Use HTTPS for production
  FRONTEND_URL="https://$FRONTEND_DOMAIN"
  BACKEND_URL="https://$BACKEND_DOMAIN"
  
  # Update docker-compose.yml for production
  sed -i.bak "s/NEXT_PUBLIC_SOCKET_PROTOCOL: \".*\"/NEXT_PUBLIC_SOCKET_PROTOCOL: \"https:\"/" docker-compose.yml
  sed -i.bak "s/NEXT_PUBLIC_SOCKET_HOST: \".*\"/NEXT_PUBLIC_SOCKET_HOST: \"model.viewer.in\"/" docker-compose.yml
  sed -i.bak "s/NEXT_PUBLIC_SOCKET_PORT: \".*\"/NEXT_PUBLIC_SOCKET_PORT: \"\"/" docker-compose.yml
  sed -i.bak "s/NEXT_PUBLIC_API_PROTOCOL: \".*\"/NEXT_PUBLIC_API_PROTOCOL: \"https:\"/" docker-compose.yml
  sed -i.bak "s/NEXT_PUBLIC_API_HOST: \".*\"/NEXT_PUBLIC_API_HOST: \"model.viewer.in\"/" docker-compose.yml
  sed -i.bak "s/NEXT_PUBLIC_API_PORT: \".*\"/NEXT_PUBLIC_API_PORT: \"\"/" docker-compose.yml
  
  # Update CORS settings for production
  CORS_ORIGINS="\"https://yolo.viewer.in,http://yolo.viewer.in,http://localhost:5003,https://model.viewer.in,http://model.viewer.in\""
  sed -i.bak "s/CORS_ORIGINS: \".*\"/CORS_ORIGINS: $CORS_ORIGINS/" docker-compose.yml
else
  # For development/testing using localhost
  echo "Running in DEVELOPMENT mode using localhost"
  
  FRONTEND_DOMAIN="localhost"
  BACKEND_DOMAIN="localhost"
  
  # Use HTTP for development
  FRONTEND_URL="http://$FRONTEND_DOMAIN:3000"
  BACKEND_URL="http://$BACKEND_DOMAIN:5003"
  
  # Update docker-compose.yml with localhost settings
  sed -i.bak "s/NEXT_PUBLIC_SOCKET_PROTOCOL: \".*\"/NEXT_PUBLIC_SOCKET_PROTOCOL: \"http:\"/" docker-compose.yml
  sed -i.bak "s/NEXT_PUBLIC_SOCKET_HOST: \".*\"/NEXT_PUBLIC_SOCKET_HOST: \"localhost\"/" docker-compose.yml
  sed -i.bak "s/NEXT_PUBLIC_SOCKET_PORT: \".*\"/NEXT_PUBLIC_SOCKET_PORT: \"5003\"/" docker-compose.yml
  sed -i.bak "s/NEXT_PUBLIC_API_PROTOCOL: \".*\"/NEXT_PUBLIC_API_PROTOCOL: \"http:\"/" docker-compose.yml
  sed -i.bak "s/NEXT_PUBLIC_API_HOST: \".*\"/NEXT_PUBLIC_API_HOST: \"localhost\"/" docker-compose.yml
  sed -i.bak "s/NEXT_PUBLIC_API_PORT: \".*\"/NEXT_PUBLIC_API_PORT: \"5003\"/" docker-compose.yml
  
  # Update CORS settings for development
  CORS_ORIGINS="\"http://localhost:3000,http://localhost:5003\""
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