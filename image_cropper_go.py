import cv2
import os

image_folder = "datasets" 
output_folder = "yolo_annotated_images"  
os.makedirs(output_folder, exist_ok=True)

drawing = False
ix, iy = -1, -1
boxes = []
img_copy = None

def draw_box(event, x, y, flags, param):
    global ix, iy, drawing, img_copy, boxes

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y

    elif event == cv2.EVENT_MOUSEMOVE and drawing:
        img_copy = img.copy()
        cv2.rectangle(img_copy, (ix, iy), (x, y), (0, 255, 0), 2)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        x_min, x_max = min(ix, x), max(ix, x)
        y_min, y_max = min(iy, y), max(iy, y)
        boxes.append((x_min, y_min, x_max, y_max))
        cv2.rectangle(img_copy, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

def normalize_bbox(x_min, y_min, x_max, y_max, img_w, img_h):
    x_center = (x_min + x_max) / 2 / img_w
    y_center = (y_min + y_max) / 2 / img_h
    width = (x_max - x_min) / img_w
    height = (y_max - y_min) / img_h
    return x_center, y_center, width, height

for root, _, files in os.walk(image_folder):
    for file in files:
        if not file.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue

        img_path = os.path.join(root, file)
        rel_path = os.path.relpath(img_path, image_folder)
        out_img_path = os.path.join(output_folder, rel_path)
        out_txt_path = os.path.splitext(out_img_path)[0] + ".txt"

        if os.path.exists(out_txt_path):
            print(f"Skipping {rel_path} (already annotated)")
            continue

        print(f"\nAnnotating: {rel_path}")
        os.makedirs(os.path.dirname(out_img_path), exist_ok=True)

        img = cv2.imread(img_path)
        try: img_copy = img.copy()
        except:
            print(img_path, ": failed.")
            continue
        
        boxes = []

        cv2.namedWindow("Annotator", cv2.WINDOW_NORMAL)
        cv2.setMouseCallback("Annotator", draw_box)

        while True:
            cv2.imshow("Annotator", img_copy)
            key = cv2.waitKey(1) & 0xFF

            if key == ord('r'):
                img_copy = img.copy()
                boxes = []
                print("Boxes reset")

            elif key == ord('n'):
                break

            elif key == ord('q'):
                print("Quit")
                exit()

        cv2.imwrite(out_img_path, img)

        h, w = img.shape[:2]
        with open(out_txt_path, "w") as f:
            for box in boxes:
                x1, y1, x2, y2 = box
                x, y, bw, bh = normalize_bbox(x1, y1, x2, y2, w, h)
                f.write(f"0 {x:.6f} {y:.6f} {bw:.6f} {bh:.6f}\n")

        print(f"Saved: {out_txt_path}")

cv2.destroyAllWindows()
