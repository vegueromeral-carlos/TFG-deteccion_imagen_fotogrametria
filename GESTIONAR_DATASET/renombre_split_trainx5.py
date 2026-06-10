# -*- coding: utf-8 -*-
"""
Created on Wed May 20 13:59:32 2026

@author: RDUser-A6
"""

import os
import random

# =========================================================
# FOLDER
# =========================================================

folder = r"E:\Carlos\train_images_labels_x5"

# =========================================================
# EXTENSIONS
# =========================================================

image_extensions = [".jpg", ".jpeg", ".png", ".bmp"]

# =========================================================
# FIND IMAGE + LABEL PAIRS
# =========================================================

pairs = []

for file in os.listdir(folder):

    name, ext = os.path.splitext(file)

    if ext.lower() in image_extensions:

        txt_file = name + ".txt"

        txt_path = os.path.join(folder, txt_file)

        if os.path.exists(txt_path):

            pairs.append((file, txt_file))

        else:

            print(f"[WARNING] Missing label for: {file}")

# =========================================================
# SHUFFLE
# =========================================================

random.shuffle(pairs)

print(f"[INFO] Pairs found: {len(pairs)}")

# =========================================================
# STEP 1
# TEMPORARY RENAMING
# avoids name conflicts
# =========================================================

temp_pairs = []

for idx, (image_file, txt_file) in enumerate(pairs):

    image_ext = os.path.splitext(image_file)[1]

    temp_image = f"temp_{idx:06d}{image_ext}"
    temp_label = f"temp_{idx:06d}.txt"

    old_image_path = os.path.join(folder, image_file)
    old_label_path = os.path.join(folder, txt_file)

    temp_image_path = os.path.join(folder, temp_image)
    temp_label_path = os.path.join(folder, temp_label)

    os.rename(old_image_path, temp_image_path)
    os.rename(old_label_path, temp_label_path)

    temp_pairs.append((temp_image, temp_label))

# =========================================================
# STEP 2
# FINAL RENAMING
# =========================================================

for idx, (temp_image, temp_label) in enumerate(temp_pairs):

    image_ext = os.path.splitext(temp_image)[1]

    final_image = f"{idx:06d}{image_ext}"
    final_label = f"{idx:06d}.txt"

    temp_image_path = os.path.join(folder, temp_image)
    temp_label_path = os.path.join(folder, temp_label)

    final_image_path = os.path.join(folder, final_image)
    final_label_path = os.path.join(folder, final_label)

    os.rename(temp_image_path, final_image_path)
    os.rename(temp_label_path, final_label_path)

    print(f"[OK] {final_image}")

print("\n[END] Shuffle and renaming completed.")