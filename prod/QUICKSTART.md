# Quick Start Guide

Follow these steps to quickly get up and running with the YOLO Object Detection Logs application.

## Step 1: Install Dependencies

Run the following command to install all required packages:

```bash
./run.sh --install
```

## Step 2: Test the RTSP Connection

Before running the full application, test that your RTSP stream is accessible:

```bash
./run.sh --test-rtsp
```

You should see output showing successful frame retrieval. If this fails, check your network connection and RTSP URL.

## Step 3: Start the Application

Start the Flask server:

```bash
./run.sh
```

## Step 4: Open the Web Interface

Open your web browser and navigate to:

```
http://localhost:5001
```

## Step 5: Connect to a Stream

1. Verify that the Socket.IO connection indicator at the top of the page shows "Connected" (green dot)
2. Choose between "RTSP Stream" or "Video URL"
3. Enter your stream URL or click "Sample RTSP" to use the default test stream
4. Click "Start Processing"

## Step 6: Monitor Detection Logs

The logs will appear in real-time showing:
- Frame numbers
- Number of detections
- Object classes and counts
- Processing speed information

## Step 7: Stop Processing

When finished, click the "Stop Processing" button to end the stream processing.

## Troubleshooting

### Socket.IO Not Connecting

If the Socket.IO connection indicator shows "Disconnected" (red dot):

1. Click the "Reconnect Socket" button
2. Check that the server is running
3. Refresh the browser page

### Stream Processing Issues

If stream processing starts but no logs appear:

1. Check the terminal running the server for error messages
2. Verify that your RTSP URL is correct
3. Make sure the YOLO model path in app.py is correct

### Browser Console Errors

If you see errors in the browser console (F12):

1. Make sure you're accessing the application via http://localhost:5001
2. Check for any Socket.IO or network-related errors
3. Try using a different browser if issues persist

## Notes

- The application is designed to process RTSP streams and video URLs
- It focuses on displaying detection information without showing the video itself
- You can clear logs at any time using the "Clear Logs" button
- For detailed information, refer to the README.md file 