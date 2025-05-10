#!/bin/bash

# Check if we're in production mode with domains
if [ "$1" == "prod" ] || [ "$1" == "production" ]; then
  echo "Restarting in PRODUCTION mode..."
  ./start-docker.sh prod
else
  echo "Restarting in DEVELOPMENT mode..."
  ./start-docker.sh
fi 