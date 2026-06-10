# -*- coding: utf-8 -*-
"""
Detección de estaciones base LoS / NLoS
"""

import os
import cv2 as cv
from ultralytics import YOLO

# =========================================================
# CONFIGURACIÓN
# =========================================================

# Modelo entrenado
model = YOLO(
    r"E:\Carlos\YOLO\PYTHON\TRAIN\runs\detect\train10\weights\best.pt"
)

# Carpeta con imágenes
image_folder = r"E:\Carlos\YOLO\imagenes_prueba"

# Carpeta salida
save_dir = r"E:\Carlos\YOLO\resultado"

# Crear carpeta si no existe
os.makedirs(save_dir, exist_ok=True)

# Extensiones válidas
valid_extensions = [".jpg", ".jpeg", ".png", ".bmp"]

# =========================================================
# RECORRER IMÁGENES
# =========================================================

for file_name in os.listdir(image_folder):

    ext = os.path.splitext(file_name)[1].lower()

    if ext not in valid_extensions:
        continue

    image_path = os.path.join(image_folder, file_name)

    print("\n=================================================")
    print(f"Procesando: {file_name}")

    # =====================================================
    # INFERENCIA YOLO
    # =====================================================

    results = model(
        image_path,
        conf=0.10)

    # =====================================================
    # CARGAR IMAGEN
    # =====================================================

    image = cv.imread(image_path)

    if image is None:

        print(f"No se pudo cargar: {image_path}")
        continue

    # =====================================================
    # DIMENSIONES
    # =====================================================

    image_height, image_width = image.shape[:2]

    # Centro horizontal imagen
    center_x = image_width // 2

    # =====================================================
    # ÁREA SEGURA
    # =====================================================

    # Cuanto mayor el threshold:
    # más permisiva será la zona LoS

    threshold = 0.4

    tolerance_x = image_width * threshold

    # =====================================================
    # DIBUJAR ÁREA SEGURA
    # =====================================================

    # Línea central azul
    cv.line(
        image,
        (center_x, 0),
        (center_x, image_height),
        (255, 0, 0),
        2
    )

    # Límites amarillos
    left_limit = int(center_x - tolerance_x)
    right_limit = int(center_x + tolerance_x)

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
    # VARIABLES
    # =====================================================

    detected = False
    visible = "NLoS"

    los_count = 0
    nlos_count = 0

    # =====================================================
    # DETECCIONES
    # =====================================================

    if len(results) > 0 and len(results[0].boxes) > 0:

        boxes = results[0].boxes

        for box in boxes:

            # =================================================
            # DATOS BBOX
            # =================================================

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            confidence = float(box.conf[0])

            class_id = int(box.cls[0])

            # Centro horizontal bbox
            box_center_x = (x1 + x2) / 2

            # =================================================
            # DEBUG
            # =================================================

            print(f"center_x imagen: {center_x}")
            print(f"center_x bbox:   {box_center_x}")
            print(f"diferencia:      {abs(box_center_x - center_x)}")
            print(f"tolerancia:      {tolerance_x}")

            # =================================================
            # LoS
            # =================================================

            if abs(box_center_x - center_x) <= tolerance_x:

                detected = True
                visible = "LoS"

                los_count += 1

                label = f"LoS {confidence:.2f}"

                # bbox verde
                cv.rectangle(
                    image,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

                # texto verde
                cv.putText(
                    image,
                    label,
                    (x1, y1 - 10),
                    cv.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (0, 255, 0),
                    2
                )

                print(
                    f"Detección LoS válida "
                    f"- confianza: {confidence:.2f}"
                )

            # =================================================
            # NLoS
            # =================================================

            else:

                nlos_count += 1

                label = f"NLoS {confidence:.2f}"

                # bbox roja
                cv.rectangle(
                    image,
                    (x1, y1),
                    (x2, y2),
                    (0, 0, 255),
                    2
                )

                # texto rojo
                cv.putText(
                    image,
                    label,
                    (x1, y1 - 10),
                    cv.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (0, 0, 255),
                    2
                )

                print(
                    f"Detección fuera del área segura "
                    f"- confianza: {confidence:.2f}"
                )

    # =====================================================
    # RESULTADO FINAL
    # =====================================================

    if detected:

        visible = "LoS"

        result_text = f"LoS ({los_count})"

        cv.putText(
            image,
            result_text,
            (10, 50),
            cv.FONT_HERSHEY_SIMPLEX,
            1.2,
            (0, 255, 0),
            3
        )

        print(f"Resultado final: {result_text}")

    else:

        visible = "NLoS"

        result_text = "NLoS"

        cv.putText(
            image,
            result_text,
            (10, 50),
            cv.FONT_HERSHEY_SIMPLEX,
            1.2,
            (0, 0, 255),
            3
        )

        print("Resultado final: NLoS")

    # =====================================================
    # GUARDAR RESULTADO
    # =====================================================

    output_path = os.path.join(save_dir, file_name)

    cv.imwrite(output_path, image)

    print(f"Guardado en: {output_path}")

# =========================================================
# FIN
# =========================================================

print("\nProceso finalizado.")

"""
# -*- coding: utf-8 -*-  CÓDIGO, SOLO UNA DETECCIÓN POR FOTO LoS

Created on Wed May 20 11:05:36 2026

@author: RDUser-A6


import os
import cv2 as cv
from ultralytics import YOLO

# =========================================================
# CONFIGURACIÓN
# =========================================================

model = YOLO(r"E:\Carlos\YOLO\PYTHON\TRAIN\runs\detect\train3\weights\best.pt")

# Carpeta con imágenes
image_folder = r"E:\Carlos\YOLO\imagenes_prueba"

# Carpeta salida
save_dir = r"E:\Carlos\YOLO\resultado"

os.makedirs(save_dir, exist_ok=True)

# Extensiones válidas
valid_extensions = [".jpg", ".jpeg", ".png", ".bmp"]

# =========================================================
# RECORRER IMÁGENES
# =========================================================

for file_name in os.listdir(image_folder):

    ext = os.path.splitext(file_name)[1].lower()

    if ext not in valid_extensions:
        continue

    image_path = os.path.join(image_folder, file_name)

    print("\n=================================================")
    print(f"Procesando: {file_name}")

    # =====================================================
    # YOLO
    # =====================================================

    results = model(image_path, conf = 0.05)

    image = cv.imread(image_path)

    if image is None:
        print(f"No se pudo cargar: {image_path}")
        continue

    image_height, image_width = image.shape[:2]

    center_x = image_width // 2

    # Área segura horizontal
    threshold = 0.4 #para más alto este threshold, más permisiva es el área
    tolerance_x = image_width * threshold

    detected = False
    visible = "NLoS"

    # =====================================================
    # DETECCIONES
    # =====================================================

    if len(results) > 0 and len(results[0].boxes) > 0:
        
        boxes = results[0].boxes

        for box in boxes:
            
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            confidence = float(box.conf[0])

            class_id = int(box.cls[0])

            box_center_x = (x1 + x2) / 2

            # =============================================
            # COMPROBAR ÁREA SEGURA
            # =============================================
            print(f"center_x imagen: {center_x}")
            print(f"center_x bbox:   {box_center_x}")
            print(f"diferencia:      {abs(box_center_x - center_x)}")
            print(f"tolerancia:      {tolerance_x}")
            
            if abs(box_center_x - center_x) <= tolerance_x:
                print("hola")
                detected = True
                visible = "LoS"

                label = f"{class_id} {confidence:.2f}"

                # bbox verde
                cv.rectangle(
                    image,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

                cv.putText(
                    image,
                    label,
                    (x1, y1 - 10),
                    cv.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (36, 255, 12),
                    2
                )

                print(
                    f"Detección válida "
                    f"(LoS) - confianza: {confidence:.2f}"
                )

                break

    # =====================================================
    # SI NO HAY DETECCIÓN VÁLIDA
    # =====================================================

    if not detected:

        visible = "NLoS"

        cv.putText(
            image,
            "NLoS",
            (10, 50),
            cv.FONT_HERSHEY_SIMPLEX,
            1.2,
            (0, 0, 255),
            3
        )

        print("Resultado: NLoS")

    else:

        cv.putText(
            image,
            "LoS",
            (10, 50),
            cv.FONT_HERSHEY_SIMPLEX,
            1.2,
            (0, 255, 0),
            3
        )

        print("Resultado: LoS")

    # =====================================================
    # GUARDAR RESULTADO
    # =====================================================

    output_path = os.path.join(save_dir, file_name)

    cv.imwrite(output_path, image)

    print(f"Guardado en: {output_path}")

print("\nProceso finalizado.")

"""