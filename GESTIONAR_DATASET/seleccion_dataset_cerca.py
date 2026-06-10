# -*- coding: utf-8 -*-
"""
Created on Fri May 22 18:02:27 2026

@author: RDUser-A6
"""

import os
import random
import shutil

# =========================
# PARAMETERS
# =========================

carpeta_origen = r"E:\Carlos\images_labels_cerca_paraLejos"
carpeta_destino = r"E:\Carlos\images_labels_cerca_paraLejos_selec"

num_imagenes = 405      # number of images to select
numero_inicio = 10001   # starting number (for renaming)

# valid image extensions
extensiones_imagen = [".jpg", ".jpeg", ".png"]

# =========================
# CREATE DESTINATION FOLDER
# =========================

os.makedirs(carpeta_destino, exist_ok=True)

# =========================
# SEARCH FOR IMAGES
# =========================

imagenes = []

for archivo in os.listdir(carpeta_origen):

    nombre, extension = os.path.splitext(archivo)

    if extension.lower() in extensiones_imagen:

        ruta_txt = os.path.join(carpeta_origen, nombre + ".txt")

        # verify that the label (txt file) exists
        if os.path.exists(ruta_txt):

            imagenes.append(archivo)

# =========================
# VERIFY QUANTITY
# =========================

if num_imagenes > len(imagenes):
    raise ValueError(
        f"Only {len(imagenes)} images found with corresponding labels."
    )

# =========================
# RANDOM SELECTION
# =========================

seleccionadas = random.sample(imagenes, num_imagenes)

# =========================
# COPY AND RENAME
# =========================

contador = numero_inicio

for imagen in seleccionadas:

    nombre_original, extension = os.path.splitext(imagen)

    txt_original = nombre_original + ".txt"

    # new file names
    nuevo_nombre = str(contador)

    nueva_imagen = nuevo_nombre + extension
    nuevo_txt = nuevo_nombre + ".txt"

    # source paths
    ruta_imagen_origen = os.path.join(carpeta_origen, imagen)
    ruta_txt_origen = os.path.join(carpeta_origen, txt_original)

    # destination paths
    ruta_imagen_destino = os.path.join(carpeta_destino, nueva_imagen)
    ruta_txt_destino = os.path.join(carpeta_destino, nuevo_txt)

    # copy files
    shutil.copy2(ruta_imagen_origen, ruta_imagen_destino)
    shutil.copy2(ruta_txt_origen, ruta_txt_destino)

    contador += 1

print(f"Successfully copied {num_imagenes} images.")

"""
import os

# =========================================
# PARAMETERS
# =========================================

carpeta = r"E:\Carlos\DATASETS\dataset_cerca_lejos_definitivo\images_labels_split\val\images"

numero_inicio = 40001

# valid image extensions
extensiones_imagen = [".jpg", ".jpeg", ".png"]

# =========================================
# GET IMAGES WITH THEIR CORRESPONDING TXT
# =========================================

archivos_validos = []

for archivo in os.listdir(carpeta):

    nombre, extension = os.path.splitext(archivo)

    if extension.lower() in extensiones_imagen:

        ruta_txt = os.path.join(carpeta, nombre + ".txt")

        # verify that the corresponding txt exists
        if os.path.exists(ruta_txt):

            archivos_validos.append((archivo, nombre + ".txt"))

# =========================================
# RENAME
# =========================================

contador = numero_inicio

for imagen, txt in archivos_validos:

    # extensions
    _, extension_imagen = os.path.splitext(imagen)

    # new file names
    nuevo_nombre = str(contador)

    nueva_imagen = nuevo_nombre + extension_imagen
    nuevo_txt = nuevo_nombre + ".txt"

    # full paths
    ruta_imagen_vieja = os.path.join(carpeta, imagen)
    ruta_txt_vieja = os.path.join(carpeta, txt)

    ruta_imagen_nueva = os.path.join(carpeta, nueva_imagen)
    ruta_txt_nueva = os.path.join(carpeta, nuevo_txt)

    # rename files
    os.rename(ruta_imagen_vieja, ruta_imagen_nueva)
    os.rename(ruta_txt_vieja, ruta_txt_nueva)

    contador += 1

print("Renaming completed successfully.")
"""