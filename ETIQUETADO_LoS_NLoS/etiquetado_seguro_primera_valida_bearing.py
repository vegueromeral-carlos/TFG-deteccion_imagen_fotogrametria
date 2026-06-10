# -*- coding: utf-8 -*-
"""
Created on Thu May 28 18:14:20 2026

@author: RDUser-A6
"""

# -*- coding: utf-8 -*-
"""
Created on Tue May 26 10:14:39 2026

@author: RDUser-A6
"""

# -*- coding: utf-8 -*-
"""
FULL MULTI-FRAME PHOTOGRAMMETRY PIPELINE

VERSIÓN FINAL:
- Tracking robusto
- Safe area MÁS permisiva
- Guardado de imágenes debug
- Filtro temporal de área
- Triangulación SIEMPRE mediante SVD
"""

import os
import cv2 as cv
import numpy as np
import subprocess
import ast

from ultralytics import YOLO

import math

# =========================================================
# CAMERA PARAMETERS
# =========================================================

IMAGE_WIDTH = 1920
IMAGE_HEIGHT = 1080

HFOV_DEG = 68.84
VFOV_DEG = 42.0

# =========================================================
# CAMERA INTRINSICS
# =========================================================

hfov_rad = np.radians(HFOV_DEG)
vfov_rad = np.radians(VFOV_DEG)

fx = IMAGE_WIDTH / (2 * np.tan(hfov_rad / 2))
fy = IMAGE_HEIGHT / (2 * np.tan(vfov_rad / 2))

cx = IMAGE_WIDTH / 2
cy = IMAGE_HEIGHT / 2

K = np.array([
    [fx, 0, cx],
    [0, fy, cy],
    [0, 0, 1]
])

# =========================================================
# USER PARAMETERS
# =========================================================

# MÁS GRANDE = MÁS PERMISIVO
SAFE_WINDOW_METERS = 250 #250 para asegurar que entra BS, 45 para asegurar que entra bs 1


camera_yaw_offset_deg = 3


WIDTH_RATIO_THRESHOLD = 0.35

MIN_BS_WIDTH = 2.5
MAX_BS_WIDTH = 5

BEARING_MODE_DISTANCE = 200

BEARING_PIXEL_THRESHOLD = 120 #threahold para aceptar en el bearing

# =========================================================
# YOLO MODEL
# =========================================================

model_path = (
    r"E:\Carlos\YOLO\PYTHON\TRAIN\runs\detect\train10\weights\best.pt"
)

yolo_model = YOLO(model_path)

# =========================================================
# BS POSITION
# =========================================================

"""
# BS 1
bs_lat = 36.737953
bs_lon = -4.559250
bs_alt = 58

"""
# BS 2
bs_lat = 36.738628
bs_lon = -4.553142
bs_alt = 48


# =========================================================
# FOLDERS
# =========================================================

folder_path = r"E:\Carlos\DATASETS\bs_2"

output_dir = r"E:\Carlos\YOLO\resultado_tracking"

os.makedirs(output_dir, exist_ok=True)

# =========================================================
# HAVERSINE
# =========================================================

def haversine_distance(lat1, lon1, lat2, lon2):

    R = 6371000

    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)

    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        np.sin(dlat / 2) ** 2 +
        np.cos(lat1) *
        np.cos(lat2) *
        np.sin(dlon / 2) ** 2
    )

    c = 2 * np.arctan2(
        np.sqrt(a),
        np.sqrt(1 - a)
    )

    return R * c

# =========================================================
# SAFE AREA
# =========================================================

def dynamic_safe_area_pixels(distance_m):

    hfov_rad = np.radians(HFOV_DEG)

    theta = 2 * np.arctan(
        (SAFE_WINDOW_METERS / 2) / distance_m
    )

    fraction = theta / hfov_rad

    width_px = fraction * IMAGE_WIDTH

    return width_px

# =========================================================
# EXPECTED WIDTH FROM DISTANCE
# =========================================================

def expected_width_pixels(
    reference_width_px,
    reference_distance,
    current_distance
):

    if current_distance <= 0:

        return reference_width_px

    expected_width = (
        reference_width_px *
        (reference_distance / current_distance)
    )

    return expected_width

# =========================================================
# ESTIMATE REAL BS WIDTH
# =========================================================

# =========================================================
# EXPECTED BS WIDTH RANGE
# =========================================================

def expected_bs_width_range_pixels(
    distance_m
):

    px_min = (
        fx *
        MIN_BS_WIDTH
    ) / distance_m

    px_max = (
        fx *
        MAX_BS_WIDTH
    ) / distance_m

    return px_min, px_max

# =========================================================
# BEARING
# =========================================================

def calculate_bearing(
    lat1,
    lon1,
    lat2,
    lon2
):

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)

    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlon = lon2 - lon1

    x = (
        math.sin(dlon)
        * math.cos(lat2)
    )

    y = (
        math.cos(lat1)
        * math.sin(lat2)
        -
        math.sin(lat1)
        * math.cos(lat2)
        * math.cos(dlon)
    )

    bearing = math.degrees(
        math.atan2(x, y)
    )

    bearing = (
        bearing + 360
    ) % 360

    return bearing

# =========================================================
# ANGULAR DIFFERENCE
# =========================================================

def angular_difference(a, b):

    diff = a - b

    while diff > 180:
        diff -= 360

    while diff < -180:
        diff += 360

    return diff

# =========================================================
# ANGLE -> PIXEL
# =========================================================

def angle_to_pixel(
    delta_angle,
    hfov,
    width
):

    half_fov = hfov / 2.0

    if abs(delta_angle) > half_fov:
        return None

    normalized = (
        delta_angle / half_fov
    )

    x_pixel = (
        normalized *
        (width / 2.0)
    ) + (width / 2.0)

    return int(x_pixel)

# =========================================================
# GPS TO ENU
# =========================================================

def gps_to_enu(
    lat,
    lon,
    alt,
    ref_lat,
    ref_lon,
    ref_alt
):

    R = 6378137

    d_lat = np.radians(lat - ref_lat)
    d_lon = np.radians(lon - ref_lon)

    x = d_lon * R * np.cos(np.radians(ref_lat))
    y = d_lat * R
    z = alt - ref_alt

    return np.array([x, y, z])

# =========================================================
# EULER NED -> ENU
# =========================================================

def euler_ned_to_enu_rotation(
    roll,
    pitch,
    yaw
):

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

# =========================================================
# PROJECTION MATRIX
# =========================================================

def build_projection_matrix(K, R, t):

    Rt = np.hstack((R, t.reshape(3, 1)))

    return K @ Rt

# =========================================================
# TRIANGULATION MULTIVIEW SVD
# =========================================================

def triangulate_multiview(
    projection_matrices,
    points_2d
):

    A = []

    for i in range(len(points_2d)):

        x, y = points_2d[i]

        P = projection_matrices[i]

        A.append(x * P[2] - P[0])
        A.append(y * P[2] - P[1])

    A = np.array(A)

    _, _, Vt = np.linalg.svd(A)

    X = Vt[-1]

    X = X[:3] / X[3]

    return X

# =========================================================
# EXIF
# =========================================================

def extract_exif_data(image_path):

    result = subprocess.run(
        [
            r"E:\Carlos\SCRIPTS DRON\exiftool.exe",
            image_path
        ],
        capture_output=True,
        text=True
    )

    output = result.stdout.splitlines()

    data_dict = {}

    for line in output:

        if ":" not in line:
            continue

        key, value = line.split(":", 1)

        data_dict[key.strip()] = value.strip()

    comment = data_dict["Comment"]

    comment_data = ast.literal_eval(comment)

    return {
        "lat": comment_data["lat"],
        "lon": comment_data["lon"],
        "alt": float(comment_data["alt"]),
        "roll": float(comment_data["roll"]),
        "pitch": float(comment_data["pitch"]),
        "yaw": float(comment_data["yaw"])
    }

# =========================================================
# DETECTION CLASS
# =========================================================

class Detection:

    def __init__(
        self,
        x1,
        y1,
        x2,
        y2,
        confidence
    ):

        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

        self.confidence = confidence

        self.center_x = (x1 + x2) / 2
        self.center_y = (y1 + y2) / 2

        self.width = x2 - x1
        self.height = y2 - y1

        self.area = self.width * self.height

# =========================================================
# FRAME CLASS
# =========================================================

class FrameData:

    def __init__(self, image_path):

        self.image_path = image_path

        self.lat = None
        self.lon = None
        self.alt = None

        self.roll = None
        self.pitch = None
        self.yaw = None

        self.los_detections = []

        self.selected_detection = None
        self.final_label = "NLoS"
        self.debug_image = None

# =========================================================
# PROCESS FRAME
# =========================================================

def process_frame(
    image_path,
    yolo_model,
    bs_lat,
    bs_lon
):

    frame = FrameData(image_path)

    exif = extract_exif_data(image_path)

    frame.lat = exif["lat"]
    frame.lon = exif["lon"]
    frame.alt = exif["alt"]

    frame.roll = exif["roll"]
    frame.pitch = exif["pitch"]
    frame.yaw = exif["yaw"]

    image = cv.imread(image_path)

    if image is None:

        print(f"Cannot read image: {image_path}")

        return frame

    image_height, image_width = image.shape[:2]

    center_x = image_width // 2

    # =====================================================
    # SAFE AREA
    # =====================================================

    distance_bs = haversine_distance(
        frame.lat,
        frame.lon,
        bs_lat,
        bs_lon
    )

    safe_width_px = dynamic_safe_area_pixels(
        distance_bs
    )

    tolerance_x = safe_width_px / 2

    left_limit = int(center_x - tolerance_x)
    right_limit = int(center_x + tolerance_x)

    # =====================================================
    # DRAW SAFE AREA
    # =====================================================

    cv.line(
        image,
        (center_x, 0),
        (center_x, image_height),
        (255, 0, 0),
        2
    )

    cv.line(
        image,
        (left_limit, 0),
        (left_limit, image_height),
        (0, 255, 255),
        2
    )

    cv.line(
        image,
        (right_limit, 0),
        (right_limit, image_height),
        (0, 255, 255),
        2
    )

    # =====================================================
    # YOLO
    # =====================================================

    results = yolo_model(
        image_path,
        conf=0.05,
        verbose=False
    )

    if len(results) > 0 and len(results[0].boxes) > 0:

        boxes = results[0].boxes

        for box in boxes:

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0]
            )

            confidence = float(box.conf[0])

            detection = Detection(
                x1,
                y1,
                x2,
                y2,
                confidence
            )

            # =============================================
            # SAFE AREA FILTER
            # =============================================

            if abs(
                detection.center_x - center_x
            ) <= tolerance_x:

                frame.los_detections.append(
                    detection
                )

                # =========================================
                # DRAW VALID DETECTION
                # =========================================

                cv.rectangle(
                    image,
                    (x1, y1),
                    (x2, y2),
                    (255, 255, 255),
                    2
                )

                cv.putText(
                    image,
                    f"{confidence:.2f}",
                    (x1, y1 - 10),
                    cv.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (255, 255, 255),
                    2
                )

            else:

                # =========================================
                # DRAW REJECTED DETECTION
                # =========================================

                cv.rectangle(
                    image,
                    (x1, y1),
                    (x2, y2),
                    (0, 0, 255),
                    2
                )

    # =====================================================
    # SAVE DEBUG IMAGE
    # =====================================================


    
    # =====================================================
    # FINAL FRAME LABEL
    # =====================================================

    frame.debug_image = image

    return frame

# =========================================================
# DRAW FINAL LABEL
# =========================================================

def draw_final_label(frame):

    image = frame.debug_image.copy()

    if frame.final_label == "LoS":

        color = (0, 255, 0)
        text = "LoS"

    else:

        color = (0, 0, 255)
        text = "NLoS"

    cv.putText(
        image,
        text,
        (10, 50),
        cv.FONT_HERSHEY_SIMPLEX,
        1.2,
        color,
        3
    )

    output_path = os.path.join(
        output_dir,
        os.path.basename(frame.image_path)
    )

    cv.imwrite(
        output_path,
        image
    )

# =========================================================
# SELECT REFERENCE FRAME
# =========================================================

# =========================================================
# SELECT REFERENCE FRAME
# =========================================================

# =========================================================
# SELECT REFERENCE FRAME
# =========================================================

def select_reference_frame(frames):

    for frame in frames:

        if len(frame.los_detections) == 0:

            frame.final_label = "NLoS"

            draw_final_label(frame)

            continue

        distance_bs = haversine_distance(
            frame.lat,
            frame.lon,
            bs_lat,
            bs_lon
        )

        reference_valid = False

        # =============================================
        # CHECK DETECTIONS IN ORDER
        # =============================================

        for det in frame.los_detections:

            

            px_min, px_max = (
                expected_bs_width_range_pixels(
                distance_bs
                )
            )

            print("")
            print("REFERENCE CHECK")
            print("================")

            print(
                f"Image: "
                f"{frame.image_path}"
                )

            print(
                f"Distance: "
                f"{distance_bs:.2f} m"
                )

            print(
                f"BBox width: "
                f"{det.width:.2f} px"
                )

            print(
                f"Expected range: "
                f"{px_min:.2f} px "
                f"- "
                f"{px_max:.2f} px"
                )

            # =========================================
            # PIXEL RANGE FILTER
            # =========================================

            if (
                    px_min
                    <= det.width
                    <= px_max
            ):

            # =========================================
            # REAL SIZE FILTER
            # =========================================

            

                frame.selected_detection = det

                frame.final_label = "LoS"

                draw_final_label(frame)

                print("")
                print(
                    "REFERENCE FRAME ACCEPTED"
                )

                reference_valid = True
                frame.selected_detection = det
                return frame

            print("")
            print(
                "Rejected as reference "
                "(unrealistic BS size)"
            )

        # =============================================
        # ALL DETECTIONS FAILED
        # =============================================

        if not reference_valid:

            frame.final_label = "NLoS"

            draw_final_label(frame)

    return None

# =========================================================
# BUILD CAMERA DATA
# =========================================================

def build_camera_data(final_frames):

    projection_matrices = []

    drone_positions = []

    ref_lat = final_frames[0].lat
    ref_lon = final_frames[0].lon
    ref_alt = final_frames[0].alt

    for frame in final_frames:

        pos = gps_to_enu(
            frame.lat,
            frame.lon,
            frame.alt,
            ref_lat,
            ref_lon,
            ref_alt
        )

        drone_positions.append(pos)

        yaw = (
            frame.yaw +
            np.radians(camera_yaw_offset_deg)
        )

        R = euler_ned_to_enu_rotation(
            frame.roll,
            frame.pitch,
            yaw
        )

        R = R.T

        t = -R @ pos

        P = build_projection_matrix(
            K,
            R,
            t
        )

        projection_matrices.append(P)

    return projection_matrices, drone_positions

# =========================================================
# EXTRACT 2D POINTS
# =========================================================

def extract_points_2d(final_frames):

    points_2d = []

    for frame in final_frames:

        det = frame.selected_detection

        points_2d.append((
            det.center_x,
            det.center_y
        ))

    return points_2d

# =========================================================
# VALIDATE TRIANGULATION
# =========================================================

def validate_triangulation(
    triangulated_point,
    drone_positions,
    final_frames,
    bs_lat,
    bs_lon
):

    center_index = (
        len(drone_positions) // 2
    )

    drone_center = drone_positions[
        center_index
    ]

    triangulated_distance = np.linalg.norm(
        triangulated_point - drone_center
    )

    gps_distances = []

    for frame in final_frames:

        d = haversine_distance(
            frame.lat,
            frame.lon,
            bs_lat,
            bs_lon
        )

        gps_distances.append(d)

    gps_mean_distance = np.mean(
        gps_distances
    )

    error = abs(
        triangulated_distance -
        gps_mean_distance
    )

    print("")
    print("VALIDATION")
    print("==========")

    print(
        f"Triangulated distance: "
        f"{triangulated_distance:.2f} m"
    )

    print(
        f"GPS expected distance: "
        f"{gps_mean_distance:.2f} m"
    )

    print(
        f"Error: {error:.2f} m"
    )

    threshold_m = 15

    if error < threshold_m:

        print("")
        print("FINAL DECISION: LoS")

        return "LoS"

    print("")
    print("FINAL DECISION: NLoS")

    return "NLoS"


# =========================================================
# PROCESS COMPLETE FOLDER
# =========================================================

def process_bs_folder():

    image_files = sorted([
        f for f in os.listdir(folder_path)
        if f.lower().endswith(
            ('.jpg', '.jpeg')
        )
    ])

    frames = []

    # =====================================================
    # PROCESS ALL FRAMES
    # =====================================================

    for img_name in image_files:

        image_path = os.path.join(
            folder_path,
            img_name
        )

        frame = process_frame(
            image_path,
            yolo_model,
            bs_lat,
            bs_lon
        )

        frames.append(frame)
        
    
    # =====================================================
    # GLOBAL DISTANCE
    # =====================================================

    mean_distance = np.mean([

        haversine_distance(
            frame.lat,
            frame.lon,
            bs_lat,
            bs_lon
        )

        for frame in frames
    ])

    print("")
    print("==============================")
    print(f"MEAN DISTANCE: {mean_distance:.2f} m")
    print("==============================")

    

    # =====================================================
    # SHORT DISTANCE MODE
    # =====================================================

    if mean_distance <= BEARING_MODE_DISTANCE:



        # =====================================================
        # SELECT REFERENCE FRAME
        # =====================================================

        reference_frame = select_reference_frame(
            frames
            )



        if reference_frame is None:

            print("No reference frame found")

            return []

        # =====================================================
        # REFERENCE DETECTION
        # =====================================================

        reference_detection = (
            reference_frame.selected_detection
            )

        reference_distance = haversine_distance(
            reference_frame.lat,
            reference_frame.lon,
            bs_lat,
            bs_lon
            )

        reference_width_px = (
            reference_detection.width
            )

        print("")
        print("REFERENCE GEOMETRY")
        print("==================")

        print(
            f"Reference distance: "
            f"{reference_distance:.2f} m"
            )

        print(
            f"Reference width: "
            f"{reference_width_px:.2f} px"
            )

        # =====================================================
        # FINAL FRAMES
        # =====================================================

        final_frames = []

        final_frames.append(reference_frame)
    
        reference_frame.final_label = "LoS"
        
        
        # =============================================
        # DRAW REFERENCE SELECTED DETECTION
        # =============================================

        det = reference_frame.selected_detection

        cv.rectangle(
            reference_frame.debug_image,
            (
                int(det.x1),
                int(det.y1)
                ),
            (
                int(det.x2),
                int(det.y2)
                ),
            (0, 255, 0),
            3
            )

        cv.circle(
            reference_frame.debug_image,
            (
                int(det.center_x),
                int(det.center_y)
                ),
            6,
            (255, 0, 0),
            -1
            )



        draw_final_label(reference_frame)

        reference_found = False

        # =====================================================
        # PROCESS REMAINING FRAMES
        # =====================================================

        for frame in frames:

            if frame == reference_frame:

                reference_found = True
                continue

            if not reference_found:

                continue

            # =================================================
            # NO LOS DETECTIONS
            # =================================================

            if len(frame.los_detections) == 0:

                print("")
                print(
                    f"NLoS discarded: "
                    f"{frame.image_path}"
                    )

                continue

            # =================================================
            # CURRENT DISTANCE
            # =================================================

            current_distance = haversine_distance(
                frame.lat,
                frame.lon,
                bs_lat,
                bs_lon
                )

            expected_width = expected_width_pixels(
                reference_width_px,
                reference_distance,
                current_distance
                )

            print("")
            print("==============================")
            print(f"FRAME: {frame.image_path}")
            print("==============================")

            print(
                f"Current distance: "
                f"{current_distance:.2f} m"
                )

            print(
                f"Expected width: "
                f"{expected_width:.2f} px"
                )

        
            selected_detection = None
            
            valid_detections = []

            # =================================================
            # CHECK DETECTIONS
            # =================================================

            for det in frame.los_detections:
                
                ratio = (
                    det.width /
                    expected_width
                    )

                error = abs(1 - ratio)

                print("")

                print(
                    f"Detected width: "
                    f"{det.width:.2f} px"
                    )

                print(
                    f"Width ratio: "
                    f"{ratio:.2f}"
                    )

                print(
                    f"Geometry error: "
                    f"{error:.2f}"
                    )

                # =============================================
                # VALID GEOMETRY
                # =============================================

                if error < WIDTH_RATIO_THRESHOLD:

                    valid_detections.append(det)

                    print("")
                    print(
                        "VALID GEOMETRY"
                        )

            # =================================================
            # NO VALID GEOMETRY
            # =================================================

            if len(valid_detections) == 0:
                
                print("")
                print(
                    "FRAME DISCARDED "
                    "(geometry)"
                    )

                frame.final_label = "NLoS"

                draw_final_label(frame)

                continue

            # =================================================
            # SHORT DISTANCE -> OLD PIPELINE
            # =================================================
            
            if current_distance <= BEARING_MODE_DISTANCE:

                selected_detection = (
                    valid_detections[0]
                    )

                print("")
                print(
                    "SHORT DISTANCE MODE"
                    )

            # =================================================
            # LONG DISTANCE -> BEARING
            # =================================================

            else:

                print("")
                print(
                    "LONG DISTANCE "
                    "BEARING MODE"
                    )

                # =============================================
                # YAW
                # =============================================

                yaw_deg = math.degrees(
                    frame.yaw
                    )

                yaw_deg = yaw_deg % 360

                yaw_deg += camera_yaw_offset_deg

                # =============================================
                # BEARING BS
                # =============================================

                bearing_bs = calculate_bearing(
                    frame.lat,
                    frame.lon,
                    bs_lat,
                    bs_lon
                    )

                delta = angular_difference(
                    bearing_bs,
                    yaw_deg
                    )

                expected_x = angle_to_pixel(
                    delta,
                    HFOV_DEG,
                    IMAGE_WIDTH
                    )

                print(
                    f"Bearing BS: "
                    f"{bearing_bs:.2f}"
                    )

                print(
                    f"Yaw: "
                    f"{yaw_deg:.2f}"
                    )

                print(
                    f"Expected X: "
                    f"{expected_x}"
                    )

                # =============================================
                # OUTSIDE FOV
                # =============================================

                if expected_x is None:

                    print("")
                    print(
                        "BS OUTSIDE FOV"
                        )

                    frame.final_label = "NLoS"

                    draw_final_label(frame)

                    continue

                # =============================================
                # DRAW EXPECTED X
                # =============================================

                cv.line(
                    frame.debug_image,
                    (expected_x, 0),
                    (
                        expected_x,
                        IMAGE_HEIGHT
                        ),
                    (0, 255, 255),
                    2
                    )

                best_bearing_error = 1e9

                # =============================================
                # CHECK VALID DETECTIONS
                # =============================================

                for det in valid_detections:

                    bearing_error = abs(
                        det.center_x -
                        expected_x
                        )

                    print("")

                    print(
                        f"Center X: "
                        f"{det.center_x:.2f}"
                        )

                    print(
                        f"Bearing error: "
                        f"{bearing_error:.2f}"
                        )

                    # =========================================
                    # BEARING FILTER
                    # =========================================

                    if (
                            bearing_error <
                            BEARING_PIXEL_THRESHOLD
                            ):

                        # =====================================
                        # BEST DETECTION
                        # =====================================

                        if (
                                bearing_error <
                                best_bearing_error
                                ):

                            best_bearing_error = (
                                bearing_error
                                )

                            selected_detection = det

                # =============================================
                # NO VALID BEARING
                # =============================================

                if selected_detection is None:

                    print("")

                    print(
                        "FRAME DISCARDED "
                        "(bearing)"
                        )

                    frame.final_label = "NLoS"

                    draw_final_label(frame)

                    continue

                print("")

                print(
                    f"BEST BEARING ERROR: "
                    f"{best_bearing_error:.2f}"
                    )

            # =================================================
            # VALID DETECTION
            # =================================================

            frame.selected_detection = (
                selected_detection
                )

            frame.final_label = "LoS"

            # =============================================
            # DRAW ONLY SELECTED
            # =============================================

            det = selected_detection
            
            cv.rectangle(
                frame.debug_image,
                (
                    int(det.x1),
                    int(det.y1)
                    ),
                (
                    int(det.x2),
                    int(det.y2)
                    ),
                (0, 255, 0),
                3
                )

            cv.circle(
                frame.debug_image,
                (
                    int(det.center_x),
                    int(det.center_y)
                    ),
                6,
                (255, 0, 0),
                -1
                )

            draw_final_label(frame)

            final_frames.append(frame)

            print("")

            print("FRAME ACCEPTED")



        return final_frames
    
    
    # =====================================================
    # LONG DISTANCE MODE
    # =====================================================

    else:

        print("")
        print("==============================")
        print("LONG DISTANCE BEARING MODE")
        print("==============================")

        final_frames = []

        # =============================================
        # PROCESS EACH FRAME
        # =============================================

        for frame in frames:

            if len(frame.los_detections) == 0:

                frame.final_label = "NLoS"

                draw_final_label(frame)

                continue

            current_distance = haversine_distance(
                frame.lat,
                frame.lon,
                bs_lat,
                bs_lon
            )

            # =========================================
            # ABSOLUTE WIDTH FILTER
            # =========================================

            px_min, px_max = (
                expected_bs_width_range_pixels(
                    current_distance
                )
            )

            valid_detections = []

            for det in frame.los_detections:

                print("")
                print("====================")
                print(frame.image_path)

                print(
                    f"Width: {det.width:.2f}"
                )

                print(
                    f"Expected: "
                    f"{px_min:.2f} - "
                    f"{px_max:.2f}"
                )

                # =====================================
                # VERY PERMISSIVE FILTER
                # =====================================

                
                # =====================================
                # DISTANCE-DEPENDENT TOLERANCE
                # =====================================

                if current_distance < 150:

                    width_multiplier = 1.0

                elif current_distance < 300:

                    width_multiplier = 1.4

                elif current_distance < 450:

                    width_multiplier = 1.8

                else:

                    width_multiplier = 2.5

                # =====================================
                # WIDTH FILTER
                # =====================================

                if (
                        px_min
                        <= det.width
                        <= px_max * width_multiplier
                        ):

                    valid_detections.append(det)

                    print("VALID WIDTH")



                    

            # =========================================
            # NO VALID WIDTHS
            # =========================================

            if len(valid_detections) == 0:

                frame.final_label = "NLoS"

                draw_final_label(frame)

                continue

            # =========================================
            # BEARING
            # =========================================

            yaw_deg = math.degrees(
                frame.yaw
            )

            yaw_deg = yaw_deg % 360

            yaw_deg += camera_yaw_offset_deg

            bearing_bs = calculate_bearing(
                frame.lat,
                frame.lon,
                bs_lat,
                bs_lon
            )

            delta = angular_difference(
                bearing_bs,
                yaw_deg
            )

            expected_x = angle_to_pixel(
                delta,
                HFOV_DEG,
                IMAGE_WIDTH
            )

            print("")
            print(
                f"Bearing: "
                f"{bearing_bs:.2f}"
            )

            print(
                f"Yaw: "
                f"{yaw_deg:.2f}"
            )

            print(
                f"Expected X: "
                f"{expected_x}"
            )

            # =========================================
            # OUTSIDE FOV
            # =========================================

            if expected_x is None:

                frame.final_label = "NLoS"

                draw_final_label(frame)

                continue

            cv.line(
                frame.debug_image,
                (expected_x, 0),
                (
                    expected_x,
                    IMAGE_HEIGHT
                ),
                (255, 0, 255),
                2
            )

            # =========================================
            # BEST DETECTION
            # =========================================

            best_det = None

            best_error = 1e9

            for det in valid_detections:

                err = abs(
                    det.center_x -
                    expected_x
                )

                print(
                    f"Center X: "
                    f"{det.center_x:.2f}"
                )

                print(
                    f"Bearing error: "
                    f"{err:.2f}"
                )

                if err < BEARING_PIXEL_THRESHOLD:

                    if err < best_error:

                        best_error = err

                        best_det = det

            # =========================================
            # NO VALID BEARING
            # =========================================

            if best_det is None:

                frame.final_label = "NLoS"

                draw_final_label(frame)

                continue

            # =========================================
            # ACCEPT
            # =========================================

            frame.selected_detection = best_det

            frame.final_label = "LoS"

            final_frames.append(frame)

            cv.rectangle(
                frame.debug_image,
                (
                    int(best_det.x1),
                    int(best_det.y1)
                ),
                (
                    int(best_det.x2),
                    int(best_det.y2)
                ),
                (0, 255, 0),
                3
            )

            draw_final_label(frame)

        return final_frames



# =========================================================
# PHOTOGRAMMETRY
# =========================================================

def photogrammetry_pipeline(
    final_frames
):

    print("")
    print("PHOTOGRAMMETRY")
    print("==============")

    if len(final_frames) <= 1:

        print("Not enough LoS frames")

        return None, "NLoS"
    
    # =====================================================
    # LONG DISTANCE MODE
    # =====================================================

    mean_distance = np.mean([

        haversine_distance(
            frame.lat,
            frame.lon,
            bs_lat,
            bs_lon
        )

        for frame in final_frames
    ])

    print("")
    print(
        f"Mean BS distance: "
        f"{mean_distance:.2f} m"
    )

    # =====================================================
    # BEARING MODE
    # =====================================================

    if mean_distance > BEARING_MODE_DISTANCE:

        print("")
        print(
            "LONG DISTANCE MODE "
            "(NO TRIANGULATION)"
        )

        if len(final_frames) >= 2:

            print("")
            print(
                "FINAL DECISION: LoS"
            )

            return None, "LoS"

        print("")
        print(
            "FINAL DECISION: NLoS"
        )

        return None, "NLoS"



    (
        projection_matrices,
        drone_positions
    ) = build_camera_data(final_frames)

    points_2d = extract_points_2d(
        final_frames
    )

    print(
        "Using multiview SVD triangulation"
    )

    triangulated_point = (
        triangulate_multiview(
            projection_matrices,
            points_2d
        )
    )

    print("")

    final_label = validate_triangulation(
        triangulated_point,
        drone_positions,
        final_frames,
        bs_lat,
        bs_lon
    )

    return (
        triangulated_point,
        final_label
    )

# =========================================================
# MAIN
# =========================================================

def main():

    final_frames = process_bs_folder()

    (
        triangulated_point,
        final_label
    ) = photogrammetry_pipeline(
        final_frames
    )

    print("")
    print("==============================")
    print("FINAL PIPELINE RESULT")
    print("==============================")

    print(
        f"Final label: {final_label}"
    )

    if triangulated_point is not None:

        print("")

# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()