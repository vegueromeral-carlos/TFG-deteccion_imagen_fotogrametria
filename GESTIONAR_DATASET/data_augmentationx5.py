# -*- coding: utf-8 -*-
"""
Created on Wed May 20 13:37:46 2026

@author: RDUser-A6
"""

import os
import cv2 as cv
import numpy as np
import shutil
#import random

# =========================================================
# SOURCE FOLDER
# =========================================================

input_folder = r"E:\Carlos\YOLO\dataset_modelo\images_labels"

# =========================================================
# DESTINATION FOLDER
# =========================================================

output_folder = input_folder + "_x5"

os.makedirs(output_folder, exist_ok=True)

# =========================================================
# IMAGE EXTENSIONS
# =========================================================

image_extensions = [".jpg", ".jpeg", ".png", ".bmp"]

# =========================================================
# AUGMENTATION FUNCTIONS
# =========================================================

# ---------------------------------------------------------
# 1. GAUSSIAN NOISE
# ---------------------------------------------------------

def gaussian_noise(image):

    mean = 0
    sigma = 30

    gauss = np.random.normal(
        mean,
        sigma,
        image.shape
    ).astype(np.float32)

    noisy = image.astype(np.float32) + gauss

    noisy = np.clip(noisy, 0, 255).astype(np.uint8)

    return noisy

# ---------------------------------------------------------
# 2. SALT AND PEPPER
# ---------------------------------------------------------

def salt_pepper(image):

    output = np.copy(image)

    prob = 0.08

    # Salt
    num_salt = int(prob * image.size * 0.5)

    coords = [
        np.random.randint(0, i - 1, num_salt)
        for i in image.shape[:2]
    ]

    output[coords[0], coords[1]] = 255

    # Pepper
    num_pepper = int(prob * image.size * 0.5)

    coords = [
        np.random.randint(0, i - 1, num_pepper)
        for i in image.shape[:2]
    ]

    output[coords[0], coords[1]] = 0

    return output

# ---------------------------------------------------------
# 3. BLUR
# ---------------------------------------------------------

def blur_image(image):

    return cv.GaussianBlur(image, (7, 7), 0)

# ---------------------------------------------------------
# 4. DARK
# ---------------------------------------------------------

def turn_dark(image):

    factor = 0.3

    dark = (image * factor).astype(np.uint8)

    return dark

# =========================================================
# ITERATE THROUGH DATASET
# =========================================================

for file in os.listdir(input_folder):

    name, ext = os.path.splitext(file)

    if ext.lower() not in image_extensions:
        continue

    image_path = os.path.join(input_folder, file)

    label_path = os.path.join(input_folder, name + ".txt")

    # Check label
    if not os.path.exists(label_path):

        print(f"[WARNING] Missing label for: {file}")
        continue

    # =====================================================
    # READ IMAGE
    # =====================================================

    image = cv.imread(image_path)

    if image is None:

        print(f"[ERROR] Could not load: {file}")
        continue

    # =====================================================
    # COPY ORIGINAL
    # =====================================================

    original_image_name = f"{name}_original{ext}"
    original_label_name = f"{name}_original.txt"

    shutil.copy2(
        image_path,
        os.path.join(output_folder, original_image_name)
    )

    shutil.copy2(
        label_path,
        os.path.join(output_folder, original_label_name)
    )

    # =====================================================
    # AUGMENTATIONS
    # =====================================================

    augmentations = {

        "gaussian": gaussian_noise(image),

        "sp": salt_pepper(image),

        "blur": blur_image(image),

        "dark": turn_dark(image)
    }

    # =====================================================
    # SAVE RESULTS
    # =====================================================

    for aug_name, aug_image in augmentations.items():

        new_image_name = f"{name}_{aug_name}{ext}"

        new_label_name = f"{name}_{aug_name}.txt"

        # Save image
        cv.imwrite(
            os.path.join(output_folder, new_image_name),
            aug_image
        )

        # Copy corresponding label
        shutil.copy2(
            label_path,
            os.path.join(output_folder, new_label_name)
        )

    print(f"[OK] Processed: {file}")

print("\n[END] Data augmentation completed.")