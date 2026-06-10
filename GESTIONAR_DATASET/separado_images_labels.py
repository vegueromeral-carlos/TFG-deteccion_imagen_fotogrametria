# -*- coding: utf-8 -*-

import os
import shutil

# =========================================================
# SOURCE FOLDER
# =========================================================

input_folder = r"E:\Carlos\train_images_labels_x5"

# =========================================================
# DESTINATION FOLDER
# =========================================================

output_folder = os.path.join(input_folder, "train")

images_folder = os.path.join(output_folder, "images")
labels_folder = os.path.join(output_folder, "labels")

# Create folders
os.makedirs(images_folder, exist_ok=True)
os.makedirs(labels_folder, exist_ok=True)

# =========================================================
# IMAGE EXTENSIONS
# =========================================================

image_extensions = [".jpg", ".jpeg", ".png", ".bmp"]

# =========================================================
# FIXED FILE LIST
# avoids issues while copying
# =========================================================

files = os.listdir(input_folder)

# =========================================================
# ITERATE THROUGH FILES
# =========================================================

for file in files:

    # ignore train folder
    if file == "train":
        continue

    file_path = os.path.join(input_folder, file)

    # ignore folders
    if not os.path.isfile(file_path):
        continue

    name, ext = os.path.splitext(file)

    # =====================================================
    # IMAGES
    # =====================================================

    if ext.lower() in image_extensions:

        destination = os.path.join(images_folder, file)

        shutil.copyfile(file_path, destination)

        print(f"[IMG] {file}")

    # =====================================================
    # LABELS
    # =====================================================

    elif ext.lower() == ".txt":

        destination = os.path.join(labels_folder, file)

        shutil.copyfile(file_path, destination)

        print(f"[LBL] {file}")

print("\n[END] Process completed successfully.")