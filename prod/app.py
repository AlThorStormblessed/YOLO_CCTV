from flask import Flask, request, jsonify, render_template, Response
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import cv2
import base64
import os
import time
from datetime import datetime
import threading
import queue
import re
import logging
from ultralytics import YOLO
import sys
import urllib.parse
import numpy as np
import torch

# Fix for PyTorch 2.6+ model loading
# Add ultralytics model classes to safe globals for deserialization
try:
    from torch.serialization import add_safe_globals
    add_safe_globals(["ultralytics.nn.tasks.DetectionModel"])
    print("Added ultralytics.nn.tasks.DetectionModel to PyTorch safe globals")
except ImportError:
    print("PyTorch version doesn't have add_safe_globals, will use weights_only=False instead")

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Get CORS origins from environment or use default
cors_origins = os.environ.get("CORS_ORIGINS", "*")

# Log the CORS origins for debugging
logger.info(f"CORS origins from environment: {cors_origins}")

# If CORS_ORIGINS is a comma-separated list, split it into a list
if cors_origins != "*" and "," in cors_origins:
    cors_origins_list = [origin.strip() for origin in cors_origins.split(",")]
    logger.info(f"Parsed CORS origins list: {cors_origins_list}")
else:
    cors_origins_list = cors_origins
    logger.info(f"Using CORS origin: {cors_origins_list}")

# Enable CORS for all routes with more permissive settings
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Initialize SocketIO with CORS allowed origins
# More permissive for development - will accept any origin in production
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

# Paths
MODEL_PATH = os.environ.get("MODEL_PATH", "/Users/tanishqsingh/Desktop/projects/YOLO_CCTV/runs/detect/train3/weights/best.pt")

# Global variables
active_streams = {}
log_queue = queue.Queue(maxsize=1000)  # Queue for log messages
# RTSP stream connection parameters
RTSP_CONNECTION_TIMEOUT = 10  # Seconds to wait for RTSP connection 
MAX_RECONNECT_ATTEMPTS = 5   # Maximum number of reconnection attempts

def is_valid_url(url):
    """
    Validate if the URL is a valid video or RTSP URL
    """
    # Check for RTSP URL
    rtsp_pattern = r'^rtsp://'
    # Check for common video URL patterns
    video_pattern = r'^https?://.*\.(mp4|avi|mov|wmv|flv|mkv)$'
    
    return bool(re.match(rtsp_pattern, url) or re.match(video_pattern, url))

def setup_rtsp_capture(url):
    """
    Configure RTSP capture with OpenCV using optimized parameters
    """
    logger.info(f"Setting up RTSP capture for {url}")
    
    # Configure OpenCV's RTSP parameters to use TCP transport
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
    
    try:
        # Create VideoCapture with specific parameters
        cap = cv2.VideoCapture(url)
        
        # Set additional RTSP parameters
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)       # Small buffer size
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)  # 5 second connection timeout
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)  # 5 second read timeout
        
        # Verify the connection
        if not cap.isOpened():
            logger.error(f"Failed to initialize video capture for {url}")
            return None
        
        # Try to read a test frame to confirm the connection works
        ret, frame = cap.read()
        if not ret:
            logger.warning(f"Could open the connection but failed to read a test frame from {url}")
            # We'll still return the capture object and let the main process handle retries
        else:
            logger.info(f"Successfully read a test frame of shape {frame.shape} from {url}")
            
        logger.info(f"Successfully opened capture for {url}")
        return cap
    
    except Exception as e:
        logger.error(f"Exception during RTSP setup: {str(e)}")
        return None

def process_stream(stream_id, url):
    """
    Process video stream and emit detection logs via socketio
    """
    logger.info(f"Starting stream processing for stream_id: {stream_id}, URL: {url}")
    
    if stream_id not in active_streams:
        logger.error(f"Stream ID {stream_id} not found in active_streams")
        return
        
    # Load YOLO model
    try:
        logger.info(f"Loading YOLO model from {MODEL_PATH}")
        # Handle PyTorch 2.6+ model loading with specific params
        try:
            # First try with safe_globals context manager if available
            from torch.serialization import safe_globals
            with safe_globals(["ultralytics.nn.tasks.DetectionModel"]):
                model = YOLO(MODEL_PATH)
                logger.info("Model loaded using safe_globals context manager")
        except (ImportError, AttributeError):
            try:
                # Then try with weights_only=False
                model = YOLO(MODEL_PATH, weights_only=False)
                logger.info("Model loaded with weights_only=False")
            except TypeError:
                # Fallback to default YOLO loading
                logger.info("Falling back to default YOLO loading")
                model = YOLO(MODEL_PATH)
        
        # In ultralytics 8.x, the model handling is different
        # The model is already in inference mode, no need to call model.eval()
        logger.info("Setting model to inference mode (CPU)")
        # Set to CPU device if available
        try:
            model.to('cpu')  # Try to use CPU for inference
            logger.info("Successfully set model to CPU")
        except Exception as e:
            logger.warning(f"Could not set model to CPU, using default device: {str(e)}")
        
        logger.info("YOLO model loaded successfully")
        # Get class names from the model
        try:
            class_names = model.model.names
            logger.info(f"Model has {len(class_names)} classes: {class_names}")
        except AttributeError:
            # For newer ultralytics versions
            try:
                class_names = model.names
                logger.info(f"Model has {len(class_names)} classes (using model.names): {class_names}")
            except AttributeError:
                logger.warning("Could not get class names from model")
                class_names = {0: 'unknown'}
        
        # Print all available class names with their indices
        for i, name in class_names.items():
            logger.info(f"Class {i}: {name}")
        
        # Check for person name classes (not generic like "person" or "face")
        generic_classes = ["face", "person", "Face", "Person"]
        person_name_classes = []
        for i, name in class_names.items():
            if name not in generic_classes:
                person_name_classes.append(name)
                
        if person_name_classes:
            logger.info(f"Found specific person name classes: {', '.join(person_name_classes)}")
            logger.info("These specific names will be shown in detection logs like in test.py")
        else:
            logger.warning("No specific person name classes found in the model")
        
        # Check if the model has the necessary face detection classes
        has_face_detection = False
        face_class_names = ["face", "person", "Face", "Person"]
        for potential_face_class in face_class_names:
            if potential_face_class in class_names.values():
                has_face_detection = True
                logger.info(f"Found face detection class: {potential_face_class}")
                break
        
        if not has_face_detection:
            logger.warning("This model may not be configured for face detection. Available classes: " + 
                          ", ".join([f"{i}:{n}" for i, n in class_names.items()]))
            
            socketio.emit('log_message', {
                "stream_id": stream_id,
                "timestamp": datetime.now().isoformat(),
                "message": "Warning: This model may not be configured for face detection.",
                "type": "warning"
            })
        
        # Test the model with a blank frame to initialize
        logger.info("Testing model with a blank frame for initialization")
        try:
            # Create a small blank test image
            test_frame = np.zeros((640, 640, 3), dtype=np.uint8)
            # Run prediction with low confidence to just test the model
            test_results = model.predict(test_frame, conf=0.1, verbose=False)
            logger.info("Model initialization successful")
        except Exception as e:
            logger.warning(f"Model test initialization failed: {str(e)}")
            logger.info("Will attempt to initialize on first frame instead")
    except Exception as e:
        logger.error(f"Error loading YOLO model: {str(e)}")
        socketio.emit('log_message', {
            "stream_id": stream_id,
            "timestamp": datetime.now().isoformat(),
            "message": f"Error loading YOLO model: {str(e)}",
            "type": "error"
        })
        active_streams[stream_id]["status"] = "error"
        return
    
    # Initialize video capture with special handling for RTSP
    logger.info(f"Initializing video capture for {url}")
    is_rtsp = url.startswith('rtsp://')
    
    # Use custom RTSP configuration for RTSP streams
    if is_rtsp:
        cap = setup_rtsp_capture(url)
    else:
        cap = cv2.VideoCapture(url)
    
    reconnect_attempts = 0
    
    if not cap or not cap.isOpened():
        error_msg = f"Error: Could not open video source: {url}"
        logger.error(error_msg)
        log_queue.put({
            "stream_id": stream_id,
            "timestamp": datetime.now().isoformat(),
            "message": error_msg,
            "type": "error"
        })
        socketio.emit('log_message', {
            "stream_id": stream_id,
            "timestamp": datetime.now().isoformat(),
            "message": error_msg,
            "type": "error"
        })
        active_streams[stream_id]["status"] = "error"
        return
    
    active_streams[stream_id]["status"] = "running"
    frame_count = 0
    empty_frame_count = 0
    
    # Log successful connection
    log_message = {
        "stream_id": stream_id,
        "timestamp": datetime.now().isoformat(),
        "message": f"Connected to {url}",
        "type": "info"
    }
    logger.info(f"Successfully connected to stream: {url}")
    log_queue.put(log_message)
    socketio.emit('log_message', log_message)
    
    try:
        logger.info("Starting frame processing loop")
        while active_streams.get(stream_id, {}).get("status") == "running":
            # Read frame with explicit success/failure logging
            logger.debug(f"Attempting to read frame from {url}")
            try:
                ret, frame = cap.read()
                logger.debug(f"Frame read result: {'success' if ret else 'failed'}")
            except Exception as e:
                logger.error(f"Exception during frame reading: {str(e)}")
                ret = False
                
            if not ret:
                empty_frame_count += 1
                logger.warning(f"Failed to get frame from stream {stream_id} (attempt {empty_frame_count})")
                
                # If we've failed too many times in a row, try to reconnect
                if empty_frame_count >= 3:
                    if not active_streams.get(stream_id, {}).get("status") == "stopping":
                        log_message = {
                            "stream_id": stream_id,
                            "timestamp": datetime.now().isoformat(),
                            "message": "Stream ended or failed to get frame. Reconnecting...",
                            "type": "warning"
                        }
                        log_queue.put(log_message)
                        socketio.emit('log_message', log_message)
                        logger.info(f"Attempting to reconnect to stream {url}")
                        
                        # Try to reconnect
                        cap.release()
                        time.sleep(2)
                        
                        # If we've tried too many times, give up
                        reconnect_attempts += 1
                        if reconnect_attempts > MAX_RECONNECT_ATTEMPTS:
                            logger.error(f"Maximum reconnection attempts ({MAX_RECONNECT_ATTEMPTS}) reached for stream {url}")
                            log_message = {
                                "stream_id": stream_id,
                                "timestamp": datetime.now().isoformat(),
                                "message": f"Failed to reconnect after {MAX_RECONNECT_ATTEMPTS} attempts. Stopping stream.",
                                "type": "error"
                            }
                            log_queue.put(log_message)
                            socketio.emit('log_message', log_message)
                            active_streams[stream_id]["status"] = "error"
                            break
                        
                        # Try reconnecting with custom RTSP setup
                        if is_rtsp:
                            cap = setup_rtsp_capture(url)
                        else:
                            cap = cv2.VideoCapture(url)
                            
                        if not cap or not cap.isOpened():
                            logger.error(f"Failed to reconnect to stream {url}")
                            continue
                        
                        # Notify of successful reconnection
                        log_message = {
                            "stream_id": stream_id,
                            "timestamp": datetime.now().isoformat(),
                            "message": f"Successfully reconnected to stream after attempt {reconnect_attempts}",
                            "type": "info"
                        }
                        log_queue.put(log_message)
                        socketio.emit('log_message', log_message)
                        empty_frame_count = 0
                    else:
                        logger.info(f"Stream {stream_id} is stopping, breaking loop")
                        break
                
                # Wait a bit before retrying
                time.sleep(0.5)
                continue
            
            # Reset counters on successful frame read
            empty_frame_count = 0
            reconnect_attempts = 0
            
            # Process frame with YOLO model
            logger.debug(f"Processing frame {frame_count} from stream {stream_id}")
            
            try:
                # Use same confidence and IoU thresholds as test.py
                results = model.predict(frame, conf=0.4, iou=0.5)
                
                # Extract detection information
                frame_count += 1
                detection_count = 0
                detection_classes = {}
                detections_text = ""
                
                # Log the raw results for debugging
                logger.debug(f"Raw prediction results: {len(results)} result objects")
                
                # Check if we got valid results
                if not results or len(results) == 0:
                    logger.warning(f"No results returned from model for frame {frame_count}")
                    # Create a basic log message for frames with no predictions
                    log_message = {
                        "stream_id": stream_id,
                        "timestamp": datetime.now().isoformat(),
                        "frame_number": frame_count,
                        "message": f"{frame_count}: {frame.shape[0]}x{frame.shape[1]} 0 No detections",
                        "details": {
                            "classes": {},
                            "speed": "No speed information available",
                            "shape": f"{frame.shape[0]}x{frame.shape[1]}",
                            "valid_detections": 0
                        },
                        "raw_text": f"{frame_count}: {frame.shape[0]}x{frame.shape[1]} 0 No detections\nNo timing information available\n",
                        "type": "detection"
                    }
                    
                    # Add log to queue and emit via socketio
                    log_queue.put(log_message)
                    socketio.emit('log_message', log_message)
                    
                    # Sleep briefly to reduce CPU load
                    time.sleep(0.1)
                    continue
                
                valid_detections = []
                
                for result in results:
                    # Make sure the result has boxes attribute
                    if not hasattr(result, 'boxes') or len(result.boxes) == 0:
                        logger.debug(f"No boxes in result for frame {frame_count}")
                        continue
                        
                    boxes = result.boxes
                    
                    # Filter detections like in test.py
                    for box in boxes:
                        # Check if box has xyxy attribute and it's not empty
                        if not hasattr(box, 'xyxy') or len(box.xyxy) == 0:
                            logger.debug("Box missing xyxy data, skipping")
                            continue
                            
                        # Check if box has confidence and class attributes
                        if not hasattr(box, 'conf') or not hasattr(box, 'cls') or len(box.conf) == 0 or len(box.cls) == 0:
                            logger.debug("Box missing confidence or class data, skipping")
                            continue
                            
                        try:
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            
                            # Get minimum box size filter based on debug mode
                            min_box_width = 50 if active_streams[stream_id].get("debug_mode", False) else 100
                            
                            # Skip small boxes, matching test.py's approach but with adjustable threshold
                            if (x2 - x1 < min_box_width):
                                logger.debug(f"Skipping small detection box of size {x2-x1}x{y2-y1} (min size: {min_box_width})")
                                # Log which detection was skipped for debugging
                                try:
                                    cls = int(box.cls[0])
                                    conf = float(box.conf[0])
                                    class_name = model.model.names[cls]
                                    logger.info(f"SKIPPED detection due to small size: {class_name} (conf: {conf:.2f}) with box size {x2-x1}x{y2-y1}")
                                except Exception:
                                    pass
                                continue
                                
                            conf = float(box.conf[0])
                            cls = int(box.cls[0])
                            
                            # Check if class index is valid
                            if cls not in model.model.names:
                                logger.warning(f"Invalid class index: {cls}, skipping detection")
                                continue
                                
                            class_name = model.model.names[cls]
                            logger.info(f"DETECTED: {class_name} with confidence {conf:.2f}, box size {x2-x1}x{y2-y1}")
                            
                            # Extra logging for person names - matching test.py behavior
                            # Check if this is likely a person name (not a generic class like "person" or "face")
                            person_classes = ["face", "person", "Face", "Person"]
                            if class_name not in person_classes:
                                logger.info(f"Person identified: {class_name} - this matches test.py behavior")
                            
                            # Store valid detections
                            valid_detections.append({
                                "box": (x1, y1, x2, y2),
                                "conf": conf,
                                "cls": cls,
                                "class_name": class_name
                            })
                            
                            # Increment class count
                            if class_name in detection_classes:
                                detection_classes[class_name] += 1
                            else:
                                detection_classes[class_name] = 1
                        except Exception as e:
                            logger.warning(f"Error processing detection box: {str(e)}")
                            continue
                    
                    # Update detection count to match valid detections
                    detection_count = len(valid_detections)
                    
                    # Format like the test.py output - exactly matching test.py format
                    detections_text = f"{frame_count}: {frame.shape[0]}x{frame.shape[1]} {detection_count} "
                    
                    # For test.py output format, just add the names directly (no parentheses with confidence)
                    if valid_detections:
                        # Extract person names only for the main detection text, comma-separated if multiple
                        # From the example: "0: 384x640 1 Yash, 89.6ms"
                        person_names = [detection['class_name'] for detection in valid_detections]
                        detections_text += ", ".join(person_names)
                    else:
                        detections_text += "No valid detections"
                    
                    # Add timing information (format like test.py)
                    if hasattr(result, 'speed') and 'inference' in result.speed:
                        detections_text += f", {result.speed['inference']:.1f}ms"
                
                # Format speed information - exactly like test.py
                speed_info = "Speed information unavailable"
                image_shape = f"{frame.shape[1]}x{frame.shape[0]}"  # Default to frame dimensions
                
                # Safely access speed information
                if hasattr(results[0], 'speed'):
                    speed_dict = results[0].speed
                    preprocess_time = speed_dict.get('preprocess', 0)
                    inference_time = speed_dict.get('inference', 0)
                    postprocess_time = speed_dict.get('postprocess', 0)
                    if 'image_shape' in speed_dict:
                        image_shape = speed_dict['image_shape']
                    
                    speed_info = f"Speed: {preprocess_time:.1f}ms preprocess, {inference_time:.1f}ms inference, {postprocess_time:.1f}ms postprocess per image at shape {image_shape}"
                
                # Debug log the complete detection text
                logger.debug(f"Detection text: {detections_text}")
                logger.debug(f"Speed info: {speed_info}")
                
                # Only emit detection logs if we actually have detections
                if detection_count > 0:
                    logger.info(f"Found {detection_count} valid detections, emitting log")
                
                # Create log message with format identical to test.py
                log_message = {
                    "stream_id": stream_id,
                    "timestamp": datetime.now().isoformat(),
                    "frame_number": frame_count,
                    "message": detections_text,
                    "details": {
                        "classes": detection_classes,
                        "speed": speed_info,
                        "shape": image_shape,
                        "valid_detections": len(valid_detections),
                        "person_names": [d['class_name'] for d in valid_detections]  # Add person names specifically
                    },
                    "raw_text": f"{detections_text}\n{speed_info}",  # Format exactly like test.py output
                    "type": "detection"
                }
                
                # Add log to queue and emit via socketio
                log_queue.put(log_message)
                logger.debug(f"Emitting log message for frame {frame_count} with {detection_count} detections")
                
                # Actually emit the message
                try:
                    # Force the detection message through regardless of content for debugging
                    socketio.emit('log_message', log_message)
                    if detection_count > 0:
                        logger.info(f"Successfully emitted detection with {detection_count} objects")
                except Exception as e:
                    logger.error(f"Failed to emit log message: {str(e)}")
            
            except Exception as e:
                logger.error(f"Error during frame processing: {str(e)}")
                # Continue processing next frame despite errors
                
            # Sleep briefly to reduce CPU load
            time.sleep(0.1)
    
    except Exception as e:
        error_msg = f"Error during processing: {str(e)}"
        logger.error(error_msg)
        log_message = {
            "stream_id": stream_id,
            "timestamp": datetime.now().isoformat(),
            "message": error_msg,
            "type": "error"
        }
        log_queue.put(log_message)
        socketio.emit('log_message', log_message)
        active_streams[stream_id]["status"] = "error"
    
    finally:
        # Cleanup
        logger.info(f"Cleaning up resources for stream {stream_id}")
        cap.release()
        
        if stream_id in active_streams:
            if active_streams[stream_id]["status"] != "error":
                active_streams[stream_id]["status"] = "stopped"
                
            log_message = {
                "stream_id": stream_id,
                "timestamp": datetime.now().isoformat(),
                "message": f"Stream processing stopped",
                "type": "info"
            }
            log_queue.put(log_message)
            socketio.emit('log_message', log_message)
            logger.info(f"Stream {stream_id} processing completed")

@app.route('/')
def index():
    logger.info("Serving index page")
    # Return a simple API response instead of rendering a template
    return jsonify({
        "status": "running",
        "message": "YOLO CCTV Detection API is running",
        "endpoints": {
            "start_stream": "/api/start_stream",
            "stop_stream": "/api/stop_stream/<stream_id>",
            "stream_status": "/api/stream_status/<stream_id>",
            "active_streams": "/api/active_streams",
            "logs": "/api/logs/<stream_id>"
        }
    })

@app.route('/api/start_stream', methods=['POST'])
def start_stream():
    logger.info("Received request to start stream")
    data = request.json
    logger.debug(f"Request data: {data}")
    stream_url = data.get('url', '')
    debug_mode = data.get('debug_mode', False)
    
    if not stream_url:
        logger.error("No URL provided in request")
        return jsonify({"error": "URL is required"}), 400
    
    if not is_valid_url(stream_url):
        logger.error(f"Invalid URL format: {stream_url}")
        return jsonify({"error": "Invalid video URL format. Please provide a valid RTSP URL or video file URL"}), 400
    
    # Generate unique stream ID
    stream_id = f"stream_{int(time.time())}"
    logger.info(f"Generated stream ID: {stream_id} for URL: {stream_url}")
    
    # Create new stream entry
    active_streams[stream_id] = {
        "url": stream_url,
        "status": "starting",
        "start_time": datetime.now().isoformat(),
        "debug_mode": debug_mode
    }
    
    # If debug mode is enabled, set logging to DEBUG level
    if debug_mode:
        logger.setLevel(logging.DEBUG)
        logger.info("Debug mode enabled - setting logging level to DEBUG")
    
    # Start processing in a background thread
    logger.info(f"Starting thread for stream processing: {stream_id}")
    thread = threading.Thread(target=process_stream, args=(stream_id, stream_url))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "stream_id": stream_id,
        "status": "starting",
        "debug_mode": debug_mode
    })

@app.route('/api/stop_stream/<stream_id>', methods=['POST'])
def stop_stream(stream_id):
    logger.info(f"Received request to stop stream: {stream_id}")
    if stream_id not in active_streams:
        logger.error(f"Stream not found: {stream_id}")
        return jsonify({"error": "Stream not found"}), 404
    
    active_streams[stream_id]["status"] = "stopping"
    logger.info(f"Stream {stream_id} marked for stopping")
    
    return jsonify({
        "stream_id": stream_id,
        "status": "stopping"
    })

@app.route('/api/stream_status/<stream_id>', methods=['GET'])
def stream_status(stream_id):
    logger.info(f"Checking status of stream: {stream_id}")
    if stream_id not in active_streams:
        logger.error(f"Stream not found: {stream_id}")
        return jsonify({"error": "Stream not found"}), 404
    
    return jsonify({
        "stream_id": stream_id,
        "status": active_streams[stream_id]["status"],
        "url": active_streams[stream_id]["url"],
        "start_time": active_streams[stream_id]["start_time"]
    })

@app.route('/api/active_streams', methods=['GET'])
def get_active_streams():
    logger.info("Getting list of active streams")
    return jsonify({
        "streams": active_streams
    })

@app.route('/api/logs/<stream_id>', methods=['GET'])
def get_logs(stream_id):
    logger.info(f"Getting logs for stream: {stream_id}")
    # This would need a proper implementation to store and retrieve logs
    # For simplicity, we'll return recent logs from the queue
    if stream_id not in active_streams:
        logger.error(f"Stream not found: {stream_id}")
        return jsonify({"error": "Stream not found"}), 404
    
    logs = []
    # Copy logs from the queue without removing them
    temp_queue = queue.Queue()
    while not log_queue.empty():
        log = log_queue.get()
        if log["stream_id"] == stream_id:
            logs.append(log)
        temp_queue.put(log)
    
    # Restore logs to the original queue
    while not temp_queue.empty():
        log_queue.put(temp_queue.get())
    
    return jsonify({
        "stream_id": stream_id,
        "logs": logs
    })

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    logger.info(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"Client disconnected: {request.sid}")

if __name__ == '__main__':
    logger.info("===== YOLO CCTV Detection Application =====")
    logger.info(f"Using YOLO model: {MODEL_PATH}")
    if not os.path.exists(MODEL_PATH):
        logger.error(f"ERROR: Model file not found at {MODEL_PATH}")
        logger.error("Please update the MODEL_PATH variable in app.py to point to your YOLO model file.")
        sys.exit(1)
    logger.info("Detection approach: Using same filtering as test.py (min box width: 100px)")
    logger.info("Starting application server on http://0.0.0.0:5003")
    socketio.run(app, host='0.0.0.0', port=5003)
    # app.run(host='0.0.0.0', port=5003, debug=False) 