import sys
import json
import os
import subprocess

print(sys.executable)
print(os.getcwd())

ver = "2.2"

print("==============================")
print("Read JSON files + Insert into images EXIF :: version " + ver)
print("==============================")
print("")

# =========================================
# Input / Output folders
# =========================================

folder_UDP = r".\Photos-UDP"
folder_EXIF = folder_UDP + "_exif"

# Crear carpeta de salida si no existe
os.makedirs(folder_EXIF, exist_ok=True)

# =========================================
# Read JPG files
# =========================================

list_files = [
    os.path.splitext(f)[0]
    for f in os.listdir(folder_UDP)
    if f.endswith(".jpg")
]

print("Detected JPG files:")
print("")

for n in list_files:
    print(n)

print("")

# =========================================
# Process files
# =========================================

for file_index, file_name in enumerate(list_files):

    print("==========================")
    print("File " + str(file_index + 1) + ": " + file_name)
    print("==========================")
    print("")

    # JSON path
    json_path = os.path.join(folder_UDP, file_name + ".json")

    # JPG input path
    jpg_input = os.path.join(folder_UDP, file_name + ".jpg")

    # JPG output path
    jpg_output = os.path.join(
        folder_EXIF,
        file_name + "_exif.jpg"
    )

    # =====================================
    # Read JSON
    # =====================================

    try:

        with open(json_path) as f:
            j = json.load(f)

    except Exception as e:

        print("ERROR reading JSON:")
        print(e)
        print("")

        continue

    # =====================================
    # Build ExifTool command
    # =====================================

    cmd = [

        r".\exiftool",

        jpg_input,

        "-o",
        jpg_output,

        "-GPSLatitude=" + str(j["lat_dms"]),
        "-GPSLongitude=" + str(j["lon_dms"]),
        "-GPSLatitudeRef=" + str(j["lat_ref"]),
        "-GPSLongitudeRef=" + str(j["lon_ref"]),

        "-Comment=" + str(j)
    ]

    print("- Inserting EXIF metadata")
    print("")

    print("- Input image:")
    print(jpg_input)
    print("")

    print("- Output image:")
    print(jpg_output)
    print("")

    print("- Comment:")
    print(str(j))
    print("")

    print("- Command:")
    print(cmd)
    print("")

    # =====================================
    # Execute ExifTool
    # =====================================

    try:

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        print("STDOUT:")
        print(result.stdout)

        print("STDERR:")
        print(result.stderr)

    except Exception as e:

        print("ERROR executing ExifTool:")
        print(e)

    print("")

print("==============================")
print("PROCESS FINISHED")
print("==============================")