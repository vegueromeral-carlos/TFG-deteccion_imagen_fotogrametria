# -*- coding: utf-8 -*-
"""
Created on Fri Feb 20 12:47:59 2026

@author: RDuser-A6
"""

from ultralytics import YOLO
import torch
#import os 


if __name__ == '__main__':
    # Check if a GPU is available and use it if so, as it is much faster 
    # for executing model training
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Training on: {device}")


    # Next, we load a default YOLOv8 base model 
    # to start training from
    model = YOLO("yolov8m.pt") # We could choose a different one


    # Moving on to the training phase
    results = model.train(
        data=r"E:\Carlos\imagenes_labels_vistas_split\d.yaml",

        # TRAINING
        epochs=300,
        imgsz=640,                
        batch=4,
        device=device,
        workers=0,

        # OPTIMIZER
        optimizer="AdamW",
        lr0=0.00296,
        lrf=0.0127,
        weight_decay=0.00051,

        # EARLY STOPPING
        patience=40,

        # LOGS
        verbose=True,

        # ALBUMENTATIONS
        mosaic=0.15,                

        mixup=0.0,
        cutmix=0.0,
        copy_paste=0.0,

        degrees=0.0,
        translate=0.1,
        scale=0.25,

        fliplr=0.5,
        flipud=0.0,

        hsv_h=0.01,
        hsv_s=0.3,
        hsv_v=0.2
    )

print("Training finished")