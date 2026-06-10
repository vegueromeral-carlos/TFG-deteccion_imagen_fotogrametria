# -*- coding: utf-8 -*-
"""
Created on Thu Feb 26 10:34:07 2026

@author: RDuser-A6
"""

from ultralytics import YOLO
import torch

if __name__ == "__main__":

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Tuning on: {device}")

    model = YOLO("yolov8s.pt")

    model.tune(
        data=r"E:\Carlos\DATASETS\dataset_cerca_lejos_definitivo\images_labels_split\d.yaml",

        # TRAINING
        epochs=50,
        iterations=6,

        imgsz=640,          
        batch=8,
        optimizer="AdamW",

        workers=0,
        device=device,

        # SEARCH SPACE CENTER
        lr0=0.003,
        lrf=0.01,
        weight_decay=0.0005,

        # AUGMENTATION
        mosaic=0.5,
        scale=0.5,
        fliplr=0.5,

        hsv_h=0.01,
        hsv_s=0.3,
        hsv_v=0.2,

        degrees=0.0,
        translate=0.1,

        # EXPERIMENT NAME
        name="bs_tuning_v1"
    )

    print("Hyperparameter tuning finished.")