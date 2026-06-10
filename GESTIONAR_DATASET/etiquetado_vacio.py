# -*- coding: utf-8 -*-
"""
Created on Tue May 19 13:12:44 2026

@author: RDUser-A6
"""

import os
import shutil

# =====================================================
# CONFIGURATION
# =====================================================

# Source folder (original images)
carpeta_vacia = r"E:\Carlos\DATASETS\dataset_cerca_lejos_definitivo\sin_bs"

# Destination folder for renamed images
carpeta_sin_bs = r"E:\Carlos\DATASETS\dataset_cerca_lejos_definitivo\vacio"

# Destination folder for empty labels
carpeta_sin_bs_l = r"E:\Carlos\DATASETS\dataset_cerca_lejos_definitivo\vacio_l"

# Number of images you want to copy
num_imagenes = 200

# Starting number for the naming sequence
numero_inicio = 55555

# =====================================================
# CREATE DESTINATION FOLDERS IF THEY DO NOT EXIST
# =====================================================

os.makedirs(carpeta_sin_bs, exist_ok=True)
os.makedirs(carpeta_sin_bs_l, exist_ok=True)

# =====================================================
# GET IMAGES
# =====================================================

# Valid extensions
extensiones = [".jpg", ".jpeg", ".png", ".bmp"]

# List of images
imagenes = [
    f for f in os.listdir(carpeta_vacia)
    if os.path.splitext(f)[1].lower() in extensiones
]

# Sort them (optional but recommended)
imagenes.sort()

# Take only the desired number of images
imagenes = imagenes[:num_imagenes]

# =====================================================
# COPY, RENAME AND CREATE EMPTY TXT FILES
# =====================================================

for i, imagen in enumerate(imagenes):

    # New name format (padded with zeros if less than 4 digits)
    nuevo_nombre = f"{numero_inicio + i:04d}"

    # Original extension
    extension = os.path.splitext(imagen)[1]

    # Source path
    ruta_origen = os.path.join(carpeta_vacia, imagen)

    # Destination path for the image
    ruta_destino_imagen = os.path.join(
        carpeta_sin_bs,
        nuevo_nombre + extension
    )

    # Copy image
    shutil.copy2(ruta_origen, ruta_destino_imagen)

    # Create empty txt file
    ruta_txt = os.path.join(
        carpeta_sin_bs_l,
        nuevo_nombre + ".txt"
    )

    open(ruta_txt, "w").close()

# =====================================================
# END
# =====================================================

print(f"Successfully copied {len(imagenes)} images.")
print("Process completed successfully.")