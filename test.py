from ultralytics import YOLO
import cv2
import os
import random
from glob import glob
import matplotlib.pyplot as plt

MODEL_PATH = "/Users/tanishqsingh/Desktop/projects/YOLO_CCTV/runs/detect/train3/weights/best.pt"
INPUT_ROOT = "/Users/tanishqsingh/Desktop/projects/YOLO_CCTV/yolo_annotated_images/datasets"
OUTPUT_DIR = "/Users/tanishqsingh/Desktop/projects/YOLO_CCTV/outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

model = YOLO(MODEL_PATH)
class_names = model.model.names
image_paths = glob(os.path.join(INPUT_ROOT, "**", "*.jpg"), recursive=True)

random_batch = random.sample(image_paths, 10)

plt.figure(figsize=(16, 8))  

for idx, img_path in enumerate(random_batch):
    img = cv2.imread(img_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    results = model.predict(img, conf=0.4, iou=0.5)

    # print(results)

    for result in results:
        boxes = result.boxes
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            if(x2 - x1 < 100):
                continue
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            label = f"{class_names[cls]} ({conf:.2f})"
            cv2.rectangle(img_rgb, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img_rgb, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                        0.6, (0, 255, 0), 2)

    plt.subplot(2, 5, idx + 1)
    plt.imshow(img_rgb)
    plt.axis('off')
    plt.title(os.path.basename(img_path), fontsize=9)

plt.tight_layout()
grid_path = os.path.join(OUTPUT_DIR, "random_batch.png")
plt.savefig(grid_path)
print(f"[SAVED] {grid_path}")
plt.show()
