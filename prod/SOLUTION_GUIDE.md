# YOLO CCTV Detection Solution Guide

This document explains the issues encountered and the solutions implemented for the YOLO CCTV Detection application.

## Issue 1: RTSP Connection Problems

### Symptoms:
- Connection to RTSP stream was timing out
- Warning messages about stream timeouts
- Application attempting to reconnect repeatedly but not getting frames

### Solution:
1. **Implemented a dedicated RTSP connection function**:
   - Added `setup_rtsp_capture()` to configure OpenCV for RTSP streaming
   - Set RTSP transport to TCP which is more reliable than UDP
   - Reduced timeouts to 5 seconds to fail faster and retry

2. **Added robust reconnection logic**:
   - The system now attempts up to 5 reconnections with 2-second delay between attempts
   - Improved error handling and logging of connection status
   - Added proper cleanup of resources when reconnection fails

## Issue 2: Socket.IO Connection Issues

### Symptoms:
- 405 Method Not Allowed error when connecting to Socket.IO
- 404 Not Found errors for Socket.IO endpoints
- Missing detection logs in the frontend

### Solution:
1. **Fixed Socket.IO URL handling**:
   - Updated the frontend to dynamically determine the correct Socket.IO URL
   - Added transport fallback options (websocket → polling)
   - Implemented automatic reconnection with increasing backoff

2. **Improved Socket.IO event handling**:
   - Added explicit error handling for socket events
   - Enhanced debugging with ping/pong event logging
   - Added detailed logging of Socket.IO connection state

## Issue 3: Detection Logs Not Appearing

### Symptoms:
- Connection to RTSP stream succeeded, but no detection logs appeared
- No errors in the console, but silently failing to display detections

### Solution:
1. **Fixed detection formatting**:
   - Ensured logs have the same format as test.py
   - Added filtering for box size (minimum width of 100px) to match test.py
   - Improved raw text formatting for better readability

2. **Enhanced detection visibility**:
   - Added special styling for detection logs with bright colors
   - Created a detection counter to track total detections
   - Added explicit console logging of detection data for debugging

3. **Added debug mode**:
   - Implemented a debug mode toggle in the UI
   - Added verbose logging for debugging connection issues
   - Improved tracking of stream state and reconnection attempts

## Issue 4: Package Compatibility

### Symptoms:
- Error importing 'url_quote' from 'werkzeug.urls'
- Flask application crashing on startup

### Solution:
1. **Created a requirements.txt with specific versions**:
   - Flask 2.0.1
   - Werkzeug 2.0.1
   - Specified compatible versions of all dependencies
   - Added instructions for fixing package compatibility issues

## Issue 5: User Experience

### Symptoms:
- Difficulty troubleshooting and running the application
- No clear instructions for testing RTSP connections

### Solution:
1. **Created comprehensive documentation**:
   - README.md with detailed usage instructions
   - QUICKSTART.md for fast setup
   - SOLUTION_GUIDE.md explaining fixes
   - Added run.py script for easier application management

2. **Added diagnostic tools**:
   - Created test_rtsp.py for testing RTSP connections
   - Added detailed status reporting in the UI
   - Implemented clear error messages and connection status indicators

## Summary of Changes

1. **Backend Improvements**:
   - Refactored RTSP connection handling
   - Added robust error recovery
   - Enhanced detection processing and logging
   - Fixed package compatibility issues

2. **Frontend Enhancements**:
   - Improved Socket.IO connection reliability
   - Enhanced detection log display
   - Added detection counter
   - Improved connection status visualization

3. **Documentation and Tools**:
   - Created detailed guides
   - Added diagnostic tools
   - Implemented a convenient run script
   - Added comprehensive error handling and reporting

## Implementation Overview

The application consists of several key components:

1. **Flask Backend (app.py)**
   - Handles incoming requests
   - Processes RTSP/video streams
   - Performs object detection using YOLO
   - Emits detection logs via Socket.IO

2. **Web Frontend (index.html)**
   - Provides a user interface for entering stream URLs
   - Displays real-time detection logs
   - Manages Socket.IO connection
   - Offers stream control (start/stop)

3. **Utility Scripts**
   - `run.sh`: Main script to run the application
   - `test_rtsp.py`: Tool to test RTSP stream connectivity

## How Detection Works

1. The YOLO model is loaded from the specified path
2. Video frames are captured from the RTSP/video stream
3. Each frame is processed by the YOLO model to detect objects
4. Detection results are formatted and sent to the frontend
5. The frontend displays the results in a format similar to the command-line output

## Detection Log Format

The logs follow a format similar to the original test.py script:

```
0: 384x640 1 Yash, 71.7ms
Speed: 1.3ms preprocess, 71.7ms inference, 0.6ms postprocess per image at shape (1, 3, 384, 640)
```

Where:
- `0`: Frame number
- `384x640`: Frame dimensions
- `1`: Number of detections
- `Yash`: Detected class name
- `71.7ms`: Inference time
- The second line shows detailed timing information

## Common Issues and Solutions

### 1. Socket.IO Connection Issues

**Problem**: Socket.IO fails to connect or frequently disconnects

**Solutions**:
- Ensure you're accessing the application via http://localhost:5001 and not directly opening the HTML file
- Check browser console for specific connection errors
- Try using a different web browser
- Verify no firewall or network policy is blocking WebSocket connections
- Use the "Reconnect Socket" button in the debug panel

### 2. No Detection Logs Appearing

**Problem**: Application starts but no detection logs are displayed

**Solutions**:
- Check terminal output for any errors in the model loading or processing
- Verify the YOLO model path is correct in app.py
- Confirm the RTSP stream is accessible (use test_rtsp.py to verify)
- Look for any JavaScript errors in the browser console
- Try a different RTSP stream or video URL

### 3. High CPU Usage

**Problem**: The application uses excessive CPU resources

**Solution**:
- Adjust the sleep time in the processing loop (currently 0.1 seconds)
- Lower the resolution of the input stream if possible
- Consider using a more powerful machine for production use

### 4. Model Not Found

**Problem**: "Error: YOLO model not found" message

**Solution**:
- Check the model path in app.py (`MODEL_PATH` variable)
- Ensure the model file exists at the specified location
- If using a custom path, update both app.py and run.sh

### 5. RTSP Stream Connection Issues

**Problem**: Cannot connect to RTSP stream

**Solutions**:
- Verify the RTSP URL format is correct (rtsp://username:password@ip:port/path)
- Check if the stream requires authentication
- Test the RTSP stream with a third-party player like VLC
- Use the test_rtsp.py script to diagnose connection issues
- Ensure no firewall is blocking the RTSP port (typically 554)

## Modifying the Code

### Changing the YOLO Model

To use a different YOLO model:

1. Update the `MODEL_PATH` variable in app.py:
   ```python
   MODEL_PATH = "/path/to/your/model.pt"
   ```

2. Update the model check in run.sh if you've modified the path

### Adding Video Display (If Needed)

The current implementation intentionally does not display video frames to focus on detection logs. If you need to add video display:

1. Modify the process_stream function in app.py to encode and emit frames:
   ```python
   # Add after detection processing
   _, buffer = cv2.imencode('.jpg', frame)
   frame_base64 = base64.b64encode(buffer).decode('utf-8')
   socketio.emit('video_frame', {
       'stream_id': stream_id,
       'frame': frame_base64
   })
   ```

2. Add video display to index.html:
   ```html
   <div>
       <img id="videoFrame" style="max-width: 100%;">
   </div>
   
   <script>
   // Add to Socket.IO event handlers
   socket.on('video_frame', (data) => {
       if (data.stream_id === currentStreamId) {
           document.getElementById('videoFrame').src = 'data:image/jpeg;base64,' + data.frame;
       }
   });
   </script>
   ```

## Performance Optimization

For improved performance:

1. Reduce frame processing rate (increase sleep time)
2. Lower the input resolution if possible
3. Process only every Nth frame (e.g., skip 2-3 frames between processing)
4. Run the application on a machine with GPU support
5. Adjust the confidence threshold (higher values = fewer detections)

## Advanced Usage

### Running as a Service

To run the application as a background service:

1. Create a systemd service file (Linux):
   ```ini
   [Unit]
   Description=YOLO CCTV Detection Service
   After=network.target

   [Service]
   User=your_username
   WorkingDirectory=/path/to/YOLO_CCTV/prod
   ExecStart=/bin/bash /path/to/YOLO_CCTV/prod/run.sh
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

2. Install and start the service:
   ```bash
   sudo cp your-service.service /etc/systemd/system/
   sudo systemctl enable your-service
   sudo systemctl start your-service
   ```

### Extending the Application

Possible extensions:

1. **Database Integration**: Store detection logs in a database
2. **Alerting System**: Send notifications when specific objects are detected
3. **Multiple Stream Support**: Process multiple RTSP streams simultaneously
4. **Authentication**: Add user login for security
5. **Recording**: Save detection events with timestamps and images

## Conclusion

The YOLO CCTV application provides a robust solution for monitoring RTSP streams and detecting objects using YOLO. The implementation focuses on displaying detection information rather than showing the video itself, making it suitable for logging and monitoring purposes.

For basic usage instructions, refer to the QUICKSTART.md file in this directory. 