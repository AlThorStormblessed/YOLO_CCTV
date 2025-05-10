#!/usr/bin/env python3
"""
Run script for YOLO CCTV Detection Application
Provides easy access to various application features
"""

import argparse
import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_PORT = 5002
DEFAULT_HOST = "0.0.0.0"
DEFAULT_RTSP_URL = "rtsp://admin123:admin123@103.100.219.14:8555/11"
MODEL_PATH = "../runs/detect/train3/weights/best.pt"

def check_requirements():
    """Check if all required packages are installed"""
    logger.info("Checking requirements...")
    try:
        import flask
        import flask_socketio
        import flask_cors
        import cv2
        import ultralytics
        logger.info("All required packages are installed.")
        return True
    except ImportError as e:
        logger.error(f"Missing requirement: {e}")
        return False

def check_model():
    """Check if the YOLO model file exists"""
    model_path = os.path.abspath(MODEL_PATH)
    if os.path.exists(model_path):
        logger.info(f"YOLO model found: {model_path}")
        return True
    else:
        logger.error(f"YOLO model not found at: {model_path}")
        return False

def start_app(host, port, debug, model_path=None):
    """Start the Flask application"""
    if not check_requirements():
        logger.error("Missing requirements. Please install required packages.")
        return False
    
    # If model path is provided, set it as an environment variable
    if model_path:
        logger.info(f"Using custom model path: {model_path}")
        os.environ["YOLO_MODEL_PATH"] = model_path
    else:
        model_path = MODEL_PATH
        
    if not os.path.exists(os.path.abspath(model_path)):
        logger.warning(f"YOLO model not found at: {model_path}")
        logger.warning("The application may not work correctly.")
    else:
        logger.info(f"Found YOLO model at: {model_path}")
    
    logger.info(f"Starting application on {host}:{port}")
    if debug:
        logger.info("Debug mode enabled")
    
    # Import app here to avoid loading it during argument parsing
    try:
        from app import app, socketio
        # Use socketio.run instead of app.run
        socketio.run(app, debug=debug, host=host, port=port, allow_unsafe_werkzeug=True)
        return True
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        return False

def test_rtsp(url, attempts, timeout):
    """Test RTSP connection"""
    logger.info(f"Testing RTSP connection to: {url}")
    try:
        from test_rtsp import test_rtsp_connection
        result = test_rtsp_connection(url, attempts, timeout)
        return result
    except Exception as e:
        logger.error(f"Error during RTSP test: {str(e)}")
        return False

def run_test_script():
    """Run the test.py script"""
    logger.info("Running test.py script")
    test_script = "../test.py"
    if not os.path.exists(test_script):
        logger.error(f"Test script not found at: {test_script}")
        return False
    
    try:
        logger.info("Starting test.py execution:")
        result = subprocess.run([sys.executable, test_script], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE,
                              text=True)
        
        print("\n--- Test Script Output ---")
        print(result.stdout)
        
        if result.stderr:
            print("\n--- Test Script Errors ---")
            print(result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error running test script: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='YOLO CCTV Detection Application Runner')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Start app command
    start_parser = subparsers.add_parser('start', help='Start the web application')
    start_parser.add_argument('--host', type=str, default=DEFAULT_HOST,
                            help=f'Host to bind the server to (default: {DEFAULT_HOST})')
    start_parser.add_argument('--port', type=int, default=DEFAULT_PORT,
                            help=f'Port to run the server on (default: {DEFAULT_PORT})')
    start_parser.add_argument('--debug', action='store_true',
                            help='Run the application in debug mode')
    start_parser.add_argument('--model', type=str, default=MODEL_PATH,
                            help=f'Path to YOLO model (default: {MODEL_PATH})')
    
    # Test RTSP connection command
    rtsp_parser = subparsers.add_parser('test-rtsp', help='Test RTSP connection')
    rtsp_parser.add_argument('--url', type=str, default=DEFAULT_RTSP_URL,
                           help=f'RTSP URL to test (default: {DEFAULT_RTSP_URL})')
    rtsp_parser.add_argument('--attempts', type=int, default=3,
                           help='Number of connection attempts (default: 3)')
    rtsp_parser.add_argument('--timeout', type=int, default=10,
                           help='Connection timeout in seconds (default: 10)')
    
    # Run test.py command
    test_parser = subparsers.add_parser('test', help='Run the test.py script')
    
    # Parse arguments
    args = parser.parse_args()
    
    # If no command is provided, show help
    if not args.command:
        parser.print_help()
        return
    
    # Execute the requested command
    if args.command == 'start':
        success = start_app(args.host, args.port, args.debug, args.model)
    elif args.command == 'test-rtsp':
        success = test_rtsp(args.url, args.attempts, args.timeout)
    elif args.command == 'test':
        success = run_test_script()
    else:
        parser.print_help()
        return
    
    # Set exit code based on success
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main() 