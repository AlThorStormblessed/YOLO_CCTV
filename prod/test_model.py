#!/usr/bin/env python3
"""
Test script for face detection model.

This script tests the YOLO face detection model on sample images
and displays the results with bounding boxes.
"""

import argparse
import cv2
import os
import matplotlib.pyplot as plt
from ultralytics import YOLO
import numpy as np

def test_model(model_path, image_dir, confidence=0.4, iou=0.5, min_face_width=100):
    """
    Test face detection model on sample images.
    
    Args:
        model_path: Path to the YOLO model
        image_dir: Directory with test images
        confidence: Detection confidence threshold
        iou: IOU threshold
        min_face_width: Minimum width for detected faces
    """
    print(f"Testing model: {model_path}")
    try:
        # Load model
        model = YOLO(model_path)
        class_names = model.model.names
        print(f"Model loaded successfully. Class names: {class_names}")
        
        # Get image paths
        image_paths = []
        for ext in ['.jpg', '.jpeg', '.png']:
            image_paths.extend([
                os.path.join(image_dir, f) for f in os.listdir(image_dir) 
                if f.lower().endswith(ext)
            ])
        
        if not image_paths:
            print(f"No images found in {image_dir}")
            return
        
        print(f"Found {len(image_paths)} images for testing")
        
        # Set up figure for display
        fig_size = min(5, len(image_paths))
        plt.figure(figsize=(16, 16))
        
        # Process each image
        for idx, img_path in enumerate(image_paths[:9]):  # Process up to 9 images
            print(f"Processing {img_path}")
            img = cv2.imread(img_path)
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Run detection
            results = model.predict(img, conf=confidence, iou=iou)
            
            face_count = 0
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    # Skip small detections
                    if (x2 - x1) < min_face_width:
                        continue
                    
                    face_count += 1
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    label = f"{class_names[cls]} ({conf:.2f})"
                    
                    # Draw bounding box
                    cv2.rectangle(img_rgb, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(img_rgb, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                                0.6, (0, 255, 0), 2)
            
            # Display image
            plt.subplot(3, 3, idx + 1)
            plt.imshow(img_rgb)
            plt.axis('off')
            plt.title(f"{os.path.basename(img_path)} - {face_count} faces", fontsize=9)
        
        plt.tight_layout()
        plt.savefig("model_test_results.png")
        print(f"Test results saved to model_test_results.png")
        plt.show()
        
    except Exception as e:
        print(f"Error testing model: {str(e)}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Test face detection model')
    parser.add_argument('--model', default="/Users/tanishqsingh/Desktop/projects/YOLO_CCTV/runs/detect/train3/weights/best.pt", 
                        help='Path to YOLO model weights')
    parser.add_argument('--image-dir', default="/Users/tanishqsingh/Desktop/projects/YOLO_CCTV/yolo_annotated_images/datasets", 
                        help='Directory with test images')
    parser.add_argument('--confidence', type=float, default=0.4,
                        help='Detection confidence threshold')
    parser.add_argument('--iou', type=float, default=0.5,
                        help='IOU threshold')
    parser.add_argument('--min-face-width', type=int, default=100,
                        help='Minimum width for detected faces')
    
    args = parser.parse_args()
    
    test_model(
        args.model, 
        args.image_dir, 
        args.confidence, 
        args.iou, 
        args.min_face_width
    )

if __name__ == "__main__":
    main() 