from ultralytics import YOLO
import cv2
import os
from datetime import datetime

# Paths
MODEL_PATH = "/Users/tanishqsingh/Desktop/projects/YOLO_CCTV/runs/detect/train3/weights/best.pt"
OUTPUT_DIR = "/Users/tanishqsingh/Desktop/projects/YOLO_CCTV/outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load YOLO model
model = YOLO(MODEL_PATH)
class_names = model.model.names

# Open webcam (0 = default camera)
cap = cv2.VideoCapture(0)

print("[INFO] Press 'q' to quit...")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Predict on current frame
    results = model.predict(frame, conf=0.4, iou=0.5)

    # Draw detections
    for result in results:
        boxes = result.boxes
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            if (x2 - x1 < 100):  # Skip small boxes
                continue
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            label = f"{class_names[cls]} ({conf:.2f})"
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (0, 255, 0), 2)

    # Show frame
    cv2.imshow("YOLO Live Feed", frame)

    # Exit on 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
