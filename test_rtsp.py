import cv2
import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_rtsp.py <video_or_rtsp_url> [fps]")
        sys.exit(1)
    
    url = sys.argv[1]
    target_fps = float(sys.argv[2]) if len(sys.argv) > 2 else 30.0
    frame_interval = int(30 / target_fps) if target_fps > 0 else 1

    cap = cv2.VideoCapture(url)
    
    if not cap.isOpened():
        print(f"Failed to open {url}")
        sys.exit(1)
    
    print(f"Opened {url} successfully. Press 'q' to quit.")
    
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Stream ended or failed to read.")
            break
        
        frame_count += 1
        if frame_count % frame_interval != 0:
            continue
        
        cv2.imshow("Stream", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
