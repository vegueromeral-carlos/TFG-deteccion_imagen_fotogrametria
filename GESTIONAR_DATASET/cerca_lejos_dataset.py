# -*- coding: utf-8 -*-
"""
Created on Thu Jun 18 18:28:37 2026

@author: RDUser-A6
"""


import os
import shutil

# ============================================================
# Configuration
# ============================================================

# Folder containing the images and YOLO labels
SOURCE_FOLDER = "dataset"

# Area threshold
# If at least one bounding box has an area smaller than this
# threshold, the sample will be classified as "far".
AREA_THRESHOLD = 0.011

# Output folders
NEAR_FOLDER = os.path.join(SOURCE_FOLDER, "cerca")
FAR_FOLDER = os.path.join(SOURCE_FOLDER, "lejos")

# ============================================================
# Create output folders if they do not exist
# ============================================================

os.makedirs(NEAR_FOLDER, exist_ok=True)
os.makedirs(FAR_FOLDER, exist_ok=True)

# ============================================================
# Process all YOLO label files
# ============================================================

txt_files = [f for f in os.listdir(SOURCE_FOLDER) if f.endswith(".txt")]

print(f"Found {len(txt_files)} label files.")
print(f"Area threshold: {AREA_THRESHOLD}")
print("-" * 50)

for txt_file in txt_files:

    txt_path = os.path.join(SOURCE_FOLDER, txt_file)
    base_name = os.path.splitext(txt_file)[0]

    areas = []

    # --------------------------------------------------------
    # Read all bounding boxes from the label file
    # YOLO format:
    # class x_center y_center width height
    # --------------------------------------------------------
    with open(txt_path, "r") as f:
        lines = f.readlines()

    for line in lines:

        parts = line.strip().split()

        # Skip malformed lines
        if len(parts) != 5:
            continue

        _, x_center, y_center, width, height = map(float, parts)

        area = width * height
        areas.append(area)

    # Skip empty label files
    if not areas:
        print(f"[WARNING] {txt_file}: no valid labels found.")
        continue

    # --------------------------------------------------------
    # Classification rule
    # If at least one box is smaller than the threshold,
    # classify the sample as FAR.
    # --------------------------------------------------------
    if min(areas) < AREA_THRESHOLD:
        destination_folder = FAR_FOLDER
        classification = "lejos"
    else:
        destination_folder = NEAR_FOLDER
        classification = "cerca"

    # --------------------------------------------------------
    # Copy label file
    # --------------------------------------------------------
    shutil.copy2(
        txt_path,
        os.path.join(destination_folder, txt_file)
    )

    # --------------------------------------------------------
    # Copy associated image if found
    # --------------------------------------------------------
    image_found = False

    for extension in [".jpg", ".jpeg", ".png", ".bmp"]:

        image_name = base_name + extension
        image_path = os.path.join(SOURCE_FOLDER, image_name)

        if os.path.exists(image_path):

            shutil.copy2(
                image_path,
                os.path.join(destination_folder, image_name)
            )

            image_found = True
            break

    # --------------------------------------------------------
    # Console output
    # --------------------------------------------------------
    print(
        f"{base_name} -> {classification} "
        f"(minimum area = {min(areas):.6f})"
    )

    if not image_found:
        print(
            f"  Warning: image file not found for {base_name}"
        )

print("-" * 50) #Linear console separator
print("Processing completed successfully.")

