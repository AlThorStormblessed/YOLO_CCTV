# YOLO_CCTV

## Dataset

Annotated images are given in yolo_annotated_images/, with raw images in datasets/.

## Training

Augmentation and label transformations are done in main.ipynb, dividing images and labels into yolo_dataset/ within yolo_annotated_images/. Dataset.yaml is also given in yolo_annotated_images/yolo_dataset/.

Training is done by running the command `yolo detect train model=yolov8n.pt data=yolo_annotated_images/yolo_dataset/dataset.yaml epochs=200 imgsz=640 device=0` (changing arguments as required).

## Testing

Testing of a particular run can be done on random images by running test.py, changing weights. Best weights so far are present in train3 and train4. 


## Deepface model

The cell with class FaceClassifier(nn.Module) etc should be run to test the model on input frame.
