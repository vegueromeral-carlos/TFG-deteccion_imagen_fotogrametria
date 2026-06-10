# -*- coding: utf-8 -*-
"""
Created on Tue May 19 17:30:28 2026

@author: RDUser-A6
"""

import os
import random
import shutil
from math import floor

# =========================================================
# CONFIGURATION
# =========================================================

# SOURCE folder (the distorted one)
input_folder = r"E:\Carlos\imagenes_labels_vistas"

# Percentages
train_percent = 0.75
val_percent   = 0.15
test_percent  = 0.10

# Seed for reproducibility
random.seed(42)

# YOLO Classes
class_names = [
    "base_station"
]

# =========================================================
# CHECK PERCENTAGES
# =========================================================

total_percent = train_percent + val_percent + test_percent

if abs(total_percent - 1.0) > 0.001:
    raise ValueError("Percentages must sum up to 1.0")

# =========================================================
# CREATE FOLDERS
# =========================================================

output_folder = input_folder + "_split"

folders = [
    "train/images",
    "train/labels",
    "val/images",
    "val/labels",
    "test/images",
    "test/labels"
]

for folder in folders:
    os.makedirs(os.path.join(output_folder, folder), exist_ok=True)

# =========================================================
# FIND IMAGE + LABEL PAIRS
# =========================================================

image_extensions = [".jpg", ".jpeg", ".png", ".bmp"]

pairs = []

for file in os.listdir(input_folder):

    name, ext = os.path.splitext(file)

    if ext.lower() in image_extensions:

        txt_file = name + ".txt"

        txt_path = os.path.join(input_folder, txt_file)

        if os.path.exists(txt_path):

            pairs.append((file, txt_file))

# =========================================================
# GLOBAL SHUFFLE
# =========================================================

random.shuffle(pairs)

# =========================================================
# "BLOCK" TYPE DISTRIBUTION
# avoids:
# 80 train consecutive + 10 val + 10 test
# =========================================================

total = len(pairs)

n_train = floor(total * train_percent)
n_val   = floor(total * val_percent)
n_test  = total - n_train - n_val

print(f"[INFO] Total pairs: {total}")
print(f"[INFO] Train: {n_train}")
print(f"[INFO] Val:   {n_val}")
print(f"[INFO] Test:  {n_test}")

# =========================================================
# CREATE INTERLEAVED LISTS
# =========================================================

splits = (
    ["train"] * n_train +
    ["val"]   * n_val +
    ["test"]  * n_test
)

# second shuffle for better distribution
random.shuffle(splits)

# =========================================================
# COPY FILES
# =========================================================

counters = {
    "train": 0,
    "val": 0,
    "test": 0
}

for (image_file, txt_file), split in zip(pairs, splits):

    image_ext = os.path.splitext(image_file)[1]

    idx = counters[split]

    new_name = f"{idx:05d}"

    # source paths
    old_image = os.path.join(input_folder, image_file)
    old_label = os.path.join(input_folder, txt_file)

    # destination paths
    new_image = os.path.join(
        output_folder,
        split,
        "images",
        new_name + image_ext
    )

    new_label = os.path.join(
        output_folder,
        split,
        "labels",
        new_name + ".txt"
    )

    shutil.copy2(old_image, new_image)
    shutil.copy2(old_label, new_label)

    counters[split] += 1

print("\n[INFO] Dataset split successfully")

# =========================================================
# GENERATE d.yaml
# =========================================================

yaml_path = os.path.join(output_folder, "d.yaml")

with open(yaml_path, "w") as f:

    f.write(f"path: {output_folder}\n")
    f.write("train: train/images\n")
    f.write("val: val/images\n")
    f.write("test: test/images\n\n")

    f.write(f"nc: {len(class_names)}\n")

    f.write("names:\n")

    for i, name in enumerate(class_names):
        f.write(f"  {i}: {name}\n")

print(f"[INFO] YAML generated: {yaml_path}")