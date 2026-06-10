# -*- coding: utf-8 -*-
"""
Created on Wed May 20 12:14:31 2026

@author: RDUser-A6
"""

from ultralytics import YOLO

# Modelo
model = YOLO(
    r"E:\Carlos\YOLO\PYTHON\TRAIN\runs\detect\train10\weights\best.pt"
)

# Inferencia sobre carpeta
results = model.predict(

    source=r"E:\Carlos\tfg",

    imgsz=640,
    conf=0.05,

    save=True,
    save_txt=True,
    save_conf=True,

    verbose=True
)

print("Predicción finalizada.")