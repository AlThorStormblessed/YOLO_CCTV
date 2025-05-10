# YOLO CCTV Detection Application

This application processes RTSP streams and video URLs, performs YOLO object detection, and displays real-time detection logs without showing the video itself.

## Features

- Support for RTSP streams and video URLs
- Real-time object detection using YOLO
- Socket.IO-based live updates
- Stream status monitoring and reconnection
- Debug mode for troubleshooting
- No video display - designed for log display only

## Setup

1. Make sure you have Python 3.8+ installed
2. Install the required packages:

```bash
pip install -r requirements.txt
```

3. Ensure your YOLO model is available at the path specified in `app.py`

## Running the Application

The application includes a convenient run script with several commands:

### Start the web application:

```bash
python run.py start
```

Optional parameters:
- `--host`: Host to bind the server to (default: 0.0.0.0)
- `--port`: Port to run the server on (default: 5003)
- `--debug`: Run in debug mode

### Test RTSP Connection:

```bash
python run.py test-rtsp
```

Optional parameters:
- `--url`: RTSP URL to test
- `--attempts`: Number of connection attempts (default: 3)
- `--timeout`: Connection timeout in seconds (default: 10)

### Run the test.py script:

```bash
python run.py test
```

## Usage

1. Start the application using the run script
2. Open your browser to `http://localhost:5003`
3. Enter an RTSP URL or video URL
4. Click "Start Processing"
5. View the detection logs in real-time
6. Click "Stop Processing" when done

## Troubleshooting RTSP Connection Issues

If you're experiencing issues with RTSP streams:

1. Test the RTSP connection using the test script:
   ```bash
   python run.py test-rtsp --url your_rtsp_url
   ```

2. Check if the RTSP stream is accessible from your network

3. Try enabling debug mode in the web interface to get more detailed logs

4. Verify that your YOLO model is correctly loaded and can detect objects

## Recent Fixes

- **Fixed "image_shape" Error**: Added robust error handling around YOLO prediction results to prevent crashes when the model doesn't provide expected attributes
- **Improved RTSP Connection**: Added better error recovery and connection testing
- **Enhanced Error Handling**: Added comprehensive try/except blocks throughout the code
- **Fixed Package Compatibility**: Added specific versions in requirements.txt to ensure compatibility

## Known Issues

- If detection logs aren't appearing, check that:
  - Debug mode is enabled
  - The RTSP connection is working properly (use test-rtsp command)
  - Your YOLO model has the correct classes

- For issues with the Socket.IO connection:
  - Make sure you're accessing the application with the same hostname used in the URL
  - Try the "Reconnect Socket" button in the interface

## Files

- `app.py`: Main Flask application
- `run.py`: Helper script for running various functions
- `test_rtsp.py`: RTSP connection testing tool
- `templates/index.html`: Web interface 
- `requirements.txt`: Package dependencies with specific versions 