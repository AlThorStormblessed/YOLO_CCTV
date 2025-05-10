#!/usr/bin/env python3
import cv2
import time
import os
import argparse
import sys

def test_rtsp_connection(rtsp_url, max_attempts=3, timeout=5):
    """Test if an RTSP connection can be established and read frames"""
    print(f"Testing RTSP connection to: {rtsp_url}")
    print(f"OpenCV version: {cv2.__version__}")
    
    # Configure OpenCV for RTSP over TCP
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
    
    # Try to connect multiple times
    for attempt in range(1, max_attempts + 1):
        print(f"\nAttempt {attempt}/{max_attempts}:")
        
        try:
            # Create VideoCapture with shorter timeouts
            cap = cv2.VideoCapture(rtsp_url)
            
            # Set timeout parameters
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, timeout * 1000)  # Convert to milliseconds
            cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, timeout * 1000)  # Convert to milliseconds
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)  # Small buffer
            
            # Check if connection is opened
            if not cap.isOpened():
                print(f"  Failed to open connection")
                cap.release()
                time.sleep(2)  # Wait before retry
                continue
                
            print(f"  ✓ Connection opened successfully")
            
            # Try to read frames
            frame_count = 0
            start_time = time.time()
            frames_to_test = 10
            
            print(f"  Attempting to read {frames_to_test} frames:")
            success = True
            
            for i in range(frames_to_test):
                ret, frame = cap.read()
                if not ret:
                    print(f"  ✗ Failed to read frame {i+1}")
                    success = False
                    break
                    
                frame_count += 1
                print(f"  ✓ Read frame {frame_count} - Shape: {frame.shape}")
                
                # Break after 5 successful frames to avoid long-running test
                if frame_count >= 5:
                    break
            
            elapsed = time.time() - start_time
            
            if frame_count > 0:
                print(f"\nTest SUCCESSFUL:")
                print(f"  - Read {frame_count} frames in {elapsed:.2f} seconds")
                print(f"  - FPS: {frame_count / elapsed:.2f}")
                cap.release()
                return True
            else:
                print("\nTest FAILED: Could not read any frames")
        
        except Exception as e:
            print(f"  ✗ Error during test: {str(e)}")
        
        finally:
            if 'cap' in locals() and cap is not None:
                cap.release()
        
        print("  Waiting 2 seconds before next attempt...")
        time.sleep(2)
    
    print("\nFAILED: Could not establish a stable connection after multiple attempts")
    return False

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test RTSP Connection')
    parser.add_argument('--url', '-u', type=str, 
                        default='rtsp://admin123:admin123@103.100.219.14:8555/11', 
                        help='RTSP URL to test')
    parser.add_argument('--attempts', '-a', type=int, default=3,
                        help='Maximum number of connection attempts')
    parser.add_argument('--timeout', '-t', type=int, default=10,
                        help='Timeout in seconds for connection')
    
    args = parser.parse_args()
    
    print("RTSP Connection Tester")
    print("=====================")
    
    result = test_rtsp_connection(args.url, args.attempts, args.timeout)
    
    if not result:
        print("\nRecommendations:")
        print("1. Verify the RTSP URL is correct")
        print("2. Check if the RTSP stream is accessible from your network")
        print("3. Try increasing the timeout value")
        print("4. Test with a different RTSP stream if available")
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main() 