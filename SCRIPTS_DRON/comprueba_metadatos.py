import subprocess
#check the metadata contained in a photo
img_path = r"E:\Carlos\DATASETS\bs_2"

result = subprocess.run(
    [r"E:\Carlos\SCRIPTS DRON\exiftool.exe", img_path],
    capture_output=True,
    text=True
)

print(result.stdout)