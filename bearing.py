# -*- coding: utf-8 -*-

"""
YOLO + GPS + YAW + hFoV
Filtro geométrico horizontal para estaciones base

FUNCIONAMIENTO:
- Lee GPS + yaw desde metadatos del dron
- Calcula bearing hacia la BS
- Estima dónde debería aparecer horizontalmente
- Ejecuta YOLO
- Selecciona la caja más coherente geométricamente
- Guarda imagen resultado
"""

import cv2 as cv
import math
import subprocess
import ast

from ultralytics import YOLO


# =========================================================
# CONFIGURACIÓN
# =========================================================

IMAGE_PATH = (
    r"E:/Carlos/DATASETS/bs_2/dron_20260520_175239_exif.jpg"
)

MODEL_PATH = (
    r"E:\Carlos\YOLO\PYTHON\TRAIN\runs\detect\train8\weights\best.pt"
)

EXIFTOOL_PATH = (
    r"E:\Carlos\SCRIPTS DRON\exiftool.exe"
)

OUTPUT_PATH = (
    r"E:\Carlos\resultado.jpg"
)

# =========================================================
# BS REAL
# =========================================================

BS_LAT = 36.738628
BS_LON = -4.553142

# =========================================================
# CÁMARA
# =========================================================

HFOV_DEG = 68.84

CONF_THRESHOLD = 0.15


# =========================================================
# EXTRACT EXIF
# =========================================================

def extract_exif_data(image_path):

    result = subprocess.run(
        [
            EXIFTOOL_PATH,
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

    # =====================================================
    # COMMENT
    # =====================================================

    comment = data_dict["Comment"]

    comment_data = ast.literal_eval(comment)

    # =====================================================
    # RETURN
    # =====================================================

    return {

        "lat": float(comment_data["lat"]),

        "lon": float(comment_data["lon"]),

        "yaw": float(comment_data["yaw"])
    }


# =========================================================
# GPS + YAW
# =========================================================

def extract_gps_and_yaw(image_path):

    exif = extract_exif_data(image_path)

    lat = exif["lat"]

    lon = exif["lon"]

    yaw_rad = exif["yaw"]

    # rad -> deg
    yaw_deg = math.degrees(yaw_rad)

    yaw_deg = yaw_deg % 360

    print("\n========== DRONE ==========")

    print(f"Latitude:  {lat}")
    print(f"Longitude: {lon}")

    print(f"Yaw rad:   {yaw_rad}")
    print(f"Yaw deg:   {yaw_deg:.2f}°")

    return lat, lon, yaw_deg


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

    x = math.sin(dlon) * math.cos(lat2)

    y = (
        math.cos(lat1) * math.sin(lat2)
        -
        math.sin(lat1) *
        math.cos(lat2) *
        math.cos(dlon)
    )

    bearing = math.degrees(
        math.atan2(x, y)
    )

    bearing = (bearing + 360) % 360

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

    # fuera del FoV
    if abs(delta_angle) > half_fov:
        return None

    normalized = delta_angle / half_fov

    x_pixel = (
        normalized *
        (width / 2.0)
    ) + (width / 2.0)

    return int(x_pixel)


# =========================================================
# MAIN
# =========================================================

def main():

    # =====================================================
    # LOAD IMAGE
    # =====================================================

    image = cv.imread(IMAGE_PATH)

    if image is None:

        raise Exception(
            "No se pudo cargar la imagen"
        )

    height, width = image.shape[:2]

    print("\n========== IMAGE ==========")

    print(f"Width:  {width}")
    print(f"Height: {height}")

    # =====================================================
    # GPS + YAW
    # =====================================================

    lat_drone, lon_drone, yaw = (
        extract_gps_and_yaw(
            IMAGE_PATH
        )
    )

    # =====================================================
    # BEARING BS
    # =====================================================

    bearing_bs = calculate_bearing(
        lat_drone,
        lon_drone,
        BS_LAT,
        BS_LON
    )

    print("\n========== BS ==========")

    print(
        f"Bearing to BS: "
        f"{bearing_bs:.2f}°"
    )

    # =====================================================
    # ANGULAR DIFFERENCE
    # =====================================================

    delta = angular_difference(
        bearing_bs,
        yaw
    )

    print("\n========== GEOMETRY ==========")

    print(
        f"Angular difference: "
        f"{delta:.2f}°"
    )

    # =====================================================
    # EXPECTED X
    # =====================================================

    expected_x = angle_to_pixel(
        delta,
        HFOV_DEG,
        width
    )

    # =====================================================
    # BS OUTSIDE IMAGE
    # =====================================================

    if expected_x is None:

        print("\nBS OUTSIDE CAMERA FOV")

        cv.imwrite(
            OUTPUT_PATH,
            image
        )

        print(
            f"\nSaved: {OUTPUT_PATH}"
        )

        return

    print(
        f"Expected X pixel: "
        f"{expected_x}"
    )

    # =====================================================
    # DRAW EXPECTED LINE
    # =====================================================

    cv.line(
        image,
        (expected_x, 0),
        (expected_x, height),
        (0, 255, 255),
        2
    )

    # =====================================================
    # YOLO
    # =====================================================

    model = YOLO(MODEL_PATH)

    results = model(
        IMAGE_PATH,
        conf=CONF_THRESHOLD,
        verbose=False
    )

    # =====================================================
    # BEST BOX
    # =====================================================

    best_box = None

    best_error = 1e9

    # =====================================================
    # PROCESS DETECTIONS
    # =====================================================

    if (
        len(results) > 0
        and
        len(results[0].boxes) > 0
    ):

        boxes = results[0].boxes

        for box in boxes:

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0]
            )

            confidence = float(
                box.conf[0]
            )

            center_x = int(
                (x1 + x2) / 2
            )

            error = abs(
                center_x - expected_x
            )

            print("\nBOX")

            print(
                f"Center X: {center_x}"
            )

            print(
                f"Error: {error:.2f}"
            )

            print(
                f"Conf: {confidence:.3f}"
            )

            # =============================================
            # DRAW ALL RED
            # =============================================

            cv.rectangle(
                image,
                (x1, y1),
                (x2, y2),
                (0, 0, 255),
                2
            )

            # =============================================
            # BEST
            # =============================================

            if error < best_error:

                best_error = error

                best_box = (
                    x1,
                    y1,
                    x2,
                    y2,
                    center_x,
                    confidence
                )

    # =====================================================
    # DRAW BEST BOX
    # =====================================================

    if best_box is not None:

        (
            x1,
            y1,
            x2,
            y2,
            center_x,
            confidence
        ) = best_box

        # =============================================
        # GREEN BOX
        # =============================================

        cv.rectangle(
            image,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            3
        )

        # =============================================
        # CENTER
        # =============================================

        center_y = int(
            (y1 + y2) / 2
        )

        cv.circle(
            image,
            (center_x, center_y),
            6,
            (255, 0, 0),
            -1
        )

        # =============================================
        # TEXT
        # =============================================

        cv.putText(
            image,
            f"BEST | err={best_error:.1f}px",
            (x1, y1 - 10),
            cv.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        print("\n========== BEST BOX ==========")

        print(
            f"Best error: "
            f"{best_error:.2f} px"
        )

    else:

        print("\nNo YOLO detections")

    # =====================================================
    # SAVE RESULT
    # =====================================================

    cv.imwrite(
        OUTPUT_PATH,
        image
    )

    print(f"\nSaved result: {OUTPUT_PATH}")


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()