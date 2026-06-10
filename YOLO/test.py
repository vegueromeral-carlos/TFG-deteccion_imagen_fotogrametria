# -*- coding: utf-8 -*-
"""
Created on Wed May 20 10:53:04 2026

@author: RDUser-A6
"""

from ultralytics import YOLO

# Load the custom trained model weights
model = YOLO(r"E:\Carlos\YOLO\PYTHON\TRAIN\runs\detect\train10\weights\best.pt")

# Run validation on the test dataset split
metrics = model.val(
    data=r"E:\Carlos\DATASETS\dataset_cerca_lejos_definitivo\images_labels_split\d.yaml",
    split="test",
    imgsz=640,
    conf=0.15,
    save=True,
    workers=0 
)

print("Test finished")