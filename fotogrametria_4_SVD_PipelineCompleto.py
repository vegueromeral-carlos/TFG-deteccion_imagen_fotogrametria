# -*- coding: utf-8 -*-
"""
FULL PIPELINE:
Images -> YOLO -> 2D detections -> EXIF GPS/ATTITUDE ->
Projection matrices -> Multiview triangulation ->
Estimated distance -> Comparison with real BS distance
"""

import numpy as np
import os
import subprocess
import ast
from ultralytics import YOLO

# =========================
# CAMERA INTRINSICS
# =========================

width = 1920
height = 1080

# REAL CAMERA FOV
fov_x_deg = 68.84
fov_y_deg = 42.0

# Convert to radians
fov_x = np.radians(fov_x_deg)
fov_y = np.radians(fov_y_deg)

# Focal lengths in pixels
fx = width / (2 * np.tan(fov_x / 2))
fy = height / (2 * np.tan(fov_y / 2))

# Principal point
cx = width / 2
cy = height / 2

# Intrinsic matrix
K = np.array([
    [fx, 0, cx],
    [0, fy, cy],
    [0, 0, 1]
])

# =========================
# YOLO MODEL
# =========================

model_path = r"E:\Carlos\YOLO\PYTHON\TRAIN\runs\detect\train10\weights\best.pt"

model = YOLO(model_path)

# =========================
# BS REAL POSITION
# =========================
"""
#BASE STATION 2 (WHITE) 500m
bs_lat = 36.738628
bs_lon = -4.553142
bs_alt = 0
"""

#BASE STATION 1 (BLACK) 100m
bs_lat = 36.737953
bs_lon = -4.559250
bs_alt = 0


# =========================
# CAMERA YAW OFFSET
# =========================
# Small correction because:
# drone yaw != exact camera optical yaw

camera_yaw_offset_deg = 3

# =========================
# HELPER FUNCTIONS
# =========================

def gps_to_enu(lat, lon, alt, ref_lat, ref_lon, ref_alt):
    """
    Convert GPS coordinates to local ENU coordinates.
    """

    R = 6378137

    d_lat = np.radians(lat - ref_lat)
    d_lon = np.radians(lon - ref_lon)

    x = d_lon * R * np.cos(np.radians(ref_lat))
    y = d_lat * R
    z = alt - ref_alt

    return np.array([x, y, z])


def euler_ned_to_enu_rotation(roll, pitch, yaw):
    """
    Convert MAVLink NED angles to ENU rotation matrix.
    Angles already in radians.
    """
    
    yaw_enu = np.pi / 2 - yaw
    pitch_enu = -pitch
    roll_enu = roll

    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(roll_enu), -np.sin(roll_enu)],
        [0, np.sin(roll_enu), np.cos(roll_enu)]
    ])

    Ry = np.array([
        [np.cos(pitch_enu), 0, np.sin(pitch_enu)],
        [0, 1, 0],
        [-np.sin(pitch_enu), 0, np.cos(pitch_enu)]
    ])

    Rz = np.array([
        [np.cos(yaw_enu), -np.sin(yaw_enu), 0],
        [np.sin(yaw_enu), np.cos(yaw_enu), 0],
        [0, 0, 1]
    ])

    return Rz @ Ry @ Rx


def build_projection_matrix(K, R, t):
    """
    Build projection matrix P = K[R|t]
    """

    Rt = np.hstack((R, t.reshape(3, 1)))

    return K @ Rt


def triangulate_multiview(projection_matrices, points_2d):
    """
    Multiview triangulation using DLT + SVD.
    """

    A = []

    for i in range(len(points_2d)):

        x, y = points_2d[i]

        P = projection_matrices[i]

        A.append(x * P[2] - P[0])
        A.append(y * P[2] - P[1])

    A = np.array(A)

    # Solve AX = 0 using SVD
    _, _, Vt = np.linalg.svd(A)

    # Solution = vector with minimum error
    X = Vt[-1]

    # Homogeneous -> Euclidean
    X = X[:3] / X[3]

    return X


# =========================
# EXIF FUNCTIONS
# =========================

def extract_exif_data(image_path):

    result = subprocess.run(
        [r"E:\Carlos\SCRIPTS DRON\exiftool.exe", image_path],
        capture_output=True,
        text=True
    )

    output = result.stdout.splitlines()

    data_dict = {}

    for line in output:

        if ":" not in line:
            continue

        key, value = line.split(":", 1)

        key = key.strip()
        value = value.strip()

        data_dict[key] = value

    # =====================
    # COMMENT
    # =====================

    comment = data_dict["Comment"]

    comment_data = ast.literal_eval(comment)

    roll = float(comment_data["roll"])
    pitch = float(comment_data["pitch"])
    yaw = float(comment_data["yaw"])

    alt = float(comment_data["alt"])

    return {
        "lat": comment_data["lat"],
        "lon": comment_data["lon"],
        "alt": alt,
        "roll": roll,
        "pitch": pitch,
        "yaw": yaw
    }


# =========================
# LOAD IMAGES
# =========================

image_folder = r"E:\Carlos\DATASETS\bs_1"

image_files = sorted([
    f for f in os.listdir(image_folder)
    if f.lower().endswith((".jpg", ".jpeg"))
])

if len(image_files) < 2:
    raise ValueError("At least 2 images are required")

print("")
print("========== IMAGES ==========")

for img in image_files:
    print(img)

# =========================
# LOAD CAMERAS FROM EXIF
# =========================

cameras = []

for img_name in image_files:

    path = os.path.join(image_folder, img_name)

    cam_data = extract_exif_data(path)

    cameras.append(cam_data)

# =========================
# REFERENCE SYSTEM
# =========================

ref_lat = cameras[0]["lat"]
ref_lon = cameras[0]["lon"]
ref_alt = cameras[0]["alt"]

# =========================
# BUILD CAMERA MATRICES
# =========================

projection_matrices = []
drone_positions = []

for i, cam in enumerate(cameras):

    pos = gps_to_enu(
        cam["lat"],
        cam["lon"],
        cam["alt"],
        ref_lat,
        ref_lon,
        ref_alt
    )

    drone_positions.append(pos)

    # =====================
    # CAMERA ORIENTATION
    # =====================

    roll = cam["roll"]

    pitch = cam["pitch"]

    # Apply yaw correction
    yaw = (
        cam["yaw"]
        + np.radians(camera_yaw_offset_deg)
    )

    # Rotation matrix
    R = euler_ned_to_enu_rotation(
        roll,
        pitch,
        yaw
    )

    # World-to-camera convention
    R = R.T

    # Translation
    t = -R @ pos

    # Projection matrix
    P = build_projection_matrix(K, R, t)

    projection_matrices.append(P)

    print("")
    print(f"Camera {i}")
    print("Position ENU:", pos)
    print("Roll:", roll)
    print("Pitch:", pitch)
    print("Yaw:", yaw)

# =========================
# YOLO DETECTION
# =========================

points_2d = []

print("")
print("========== YOLO DETECTIONS ==========")

for img_name in image_files:

    image_path = os.path.join(image_folder, img_name)

    results = model(image_path, verbose=False, conf = 0.05)

    boxes = results[0].boxes

    if len(boxes) == 0:
        raise ValueError(f"No detection found in {img_name}")

    # First detection only
    box = boxes[0]

    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()

    # Horizontal center
    x_px = (x1 + x2) / 2
    # Vertical center
    y_px = (y1 + y2) / 2

    points_2d.append((x_px, y_px))

    print(f"{img_name}")
    print(f"Center: ({x_px:.2f}, {y_px:.2f})")

# =========================
# CONSISTENCY CHECK
# =========================

print("")
print("========== CONSISTENCY ==========")

print("Number of cameras:", len(cameras))
print("Number of detections:", len(points_2d))

if len(cameras) != len(points_2d):

    raise ValueError(
        "Mismatch between cameras and detections"
    )

# =========================
# TRIANGULATION
# =========================

print("")
print("========== TRIANGULATION ==========")

final_point = triangulate_multiview(
    projection_matrices,
    points_2d
)


# =========================
# DISTANCE ESTIMATION
# =========================

center_index = len(drone_positions) // 2

central_pos = drone_positions[center_index]

estimated_distance = np.linalg.norm(
    final_point - central_pos
)

# =========================
# REAL BS DISTANCE
# =========================

bs_position = gps_to_enu(
    bs_lat,
    bs_lon,
    bs_alt,
    ref_lat,
    ref_lon,
    ref_alt
)


real_distance = np.linalg.norm(
    bs_position - central_pos
)

# =========================
# ERROR
# =========================

distance_error = abs(
    real_distance - estimated_distance
)

# =========================
# RESULTS
# =========================

print("")
print(f"Estimated distance to object: {estimated_distance:.2f} m")

print(f"Real distance to BS:          {real_distance:.2f} m")

print(f"Absolute error:               {distance_error:.2f} m")