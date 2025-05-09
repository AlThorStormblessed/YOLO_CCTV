# Running the Face Recognition System Without Docker

This guide explains how to set up and run the face recognition system without using Docker on your local machine, as well as how to access it remotely.

## Prerequisites

- Python 3.10 or later
- Docker and Docker Compose
- Node.js and npm (for Prisma database migrations, optional but recommended)
- A YOLO face detection model (e.g., the pre-trained model in `runs/detect/train3/weights/best.pt`)
- RTSP camera streams to monitor

## Setting Up the Local Environment

1. **Run the setup script**:

   ```bash
   cd /Users/tanishqsingh/Desktop/projects/YOLO_CCTV/prod
   chmod +x setup_local_env.sh
   ./setup_local_env.sh
   ```

   This script will:
   - Create a Python virtual environment
   - Install all required dependencies
   - Set up the Prisma client for database access
   - Check for Docker and Docker Compose installations
   - Create a default `.env` file

2. **Configure the environment**:

   Edit the `.env` file in the `prod` directory:

   ```bash
   nano .env
   ```

   Modify the following settings:
   - `RTSP_URLS`: Your RTSP camera stream URLs (comma-separated)
   - `MODEL_PATH`: Path to your trained YOLO model
   - `REDIS_HOST`: Redis server hostname (default: localhost)
   - `POSTGRES_HOST`: PostgreSQL server hostname (default: localhost)
   - Other settings as needed

3. **Initialize the database**:

   The PostgreSQL database with pgvector extension will be automatically initialized in a Docker container when you start the system. The database schema will be created using one of two methods:
   
   - If Node.js and npm are installed, Prisma migrations will be used.
   - If Node.js is not available, a manual SQL script will be used as a fallback.

   You don't need to install PostgreSQL locally as it runs in Docker.

## Starting the System

1. **Run the start script**:

   ```bash
   cd /Users/tanishqsingh/Desktop/projects/YOLO_CCTV/prod
   chmod +x start_local.sh
   ./start_local.sh
   ```

   This script will:
   - Activate the virtual environment if needed
   - Start Redis and PostgreSQL in Docker containers
   - Configure environment variables
   - Start all system components:
     - Stream processor
     - Face detection
     - Face recognition
     - Result aggregator
     - Web interface

2. **Monitor the logs**:

   All service logs are stored in the `logs` directory:

   ```bash
   tail -f logs/stream_processor.log
   tail -f logs/face_detection.log
   tail -f logs/face_recognition.log
   tail -f logs/result_aggregator.log
   tail -f logs/web_interface.log
   ```

## Accessing the System Remotely

The system includes a web interface that can be accessed remotely.

1. **Default access**:

   By default, the web interface runs on port 5000 and listens on all network interfaces (0.0.0.0), so it's accessible from other machines on the network.

   - From the local machine: http://localhost:5000
   - From other machines: http://YOUR_IP_ADDRESS:5000

2. **Configure remote access**:

   You can modify the host and port by setting environment variables in the `.env` file:

   ```
   WEB_HOST=0.0.0.0  # Listen on all interfaces
   WEB_PORT=5000     # Use port 5000
   ```

3. **Firewall configuration**:

   Ensure that your firewall allows incoming connections on the web interface port:

   ```bash
   # On macOS
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add $(which python)
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblock $(which python)

   # On Linux
   sudo ufw allow 5000/tcp
   ```

4. **Using ngrok for remote access**:

   If you're behind a firewall or NAT, you can use ngrok to expose your local server to the internet:

   ```bash
   # Install ngrok
   brew install ngrok  # macOS
   sudo snap install ngrok  # Ubuntu

   # Expose your local web interface
   ngrok http 5000
   ```

   ngrok will provide a public URL that you can share with others.

## Stopping the System

To stop all services:

```bash
cd /Users/tanishqsingh/Desktop/projects/YOLO_CCTV/prod
chmod +x stop_local.sh
./stop_local.sh
```

This script will stop all running services. It will ask if you also want to stop Redis and PostgreSQL.

## Troubleshooting

1. **Service not starting**:
   - Check the service log file in the `logs` directory
   - Ensure all dependencies are installed
   - Verify that Docker is running and the Redis and PostgreSQL containers are active (`docker ps`)

2. **Cannot access web interface remotely**:
   - Check that the web interface is running (`ps aux | grep web_interface`)
   - Verify firewall settings
   - Ensure the correct IP address and port are being used

3. **Model not found**:
   - Update the `MODEL_PATH` in your `.env` file to point to your YOLO model

4. **Database connection errors**:
   - Verify PostgreSQL container is running (`docker ps | grep postgres`)
   - Check Docker logs (`docker logs face_recognition_postgres`)
   - Ensure database credentials in the `.env` file match the ones in the Docker container

5. **Docker-related issues**:
   - Ensure Docker daemon is running
   - Check for port conflicts (Redis uses port 6379, PostgreSQL uses port 5432)
   - View logs with `docker logs face_recognition_redis` or `docker logs face_recognition_postgres`

## System Architecture

The system consists of several components that communicate through Redis queues:

1. **Stream Processor**: Extracts frames from RTSP streams
2. **Face Detection**: Uses YOLO to detect faces in frames
3. **Face Recognition**: Recognizes faces using a neural network
4. **Result Aggregator**: Stores recognition results
5. **Web Interface**: Provides a dashboard for monitoring the system

Each component runs as a separate Python process, allowing for easier debugging and reduced resource usage compared to Docker containers.

## Database Migrations

If you need to make changes to the database schema:

1. **Create a new migration:**

   ```bash
   cd /Users/tanishqsingh/Desktop/projects/YOLO_CCTV/prod
   ./create-migration.sh
   ```

   This script will:
   - Start the PostgreSQL container if needed
   - Create the database if it doesn't exist
   - Run Prisma's migration tool
   - Generate a new migration based on changes to `prisma/schema.prisma`

2. **Manually apply migrations:**

   Migrations are automatically applied when you run `start_local.sh`, but you can also apply them manually:

   ```bash
   cd /Users/tanishqsingh/Desktop/projects/YOLO_CCTV/prod
   npx prisma migrate deploy
   ```

3. **Reset the database (caution - destructive):**

   If you need to reset the database completely:

   ```bash
   cd /Users/tanishqsingh/Desktop/projects/YOLO_CCTV/prod
   npx prisma migrate reset
   ```

   This will drop and recreate the database and apply all migrations. 