from PIL import Image
from pillow_heif import register_heif_opener
import os


register_heif_opener()

def convert_heic_to_jpg(heic_filepath, jpg_filepath):
    """Converts an HEIC image to JPG format.

    Args:
        heic_filepath: Path to the input HEIC file.
        jpg_filepath: Path to save the output JPG file.
    """
    try:
        img = Image.open(heic_filepath)
        cimg = img.convert('RGB')
        cimg = cimg.resize((cimg.width // 4, cimg.height // 4))
        cimg.save(jpg_filepath, "jpeg")
        print(f"Converted {heic_filepath} to {jpg_filepath}")
    except Exception as e:
         print(f"Error converting {heic_filepath}: {e}")

def convert_directory_heic_to_jpg(src_path, dest_path):
    """Converts all HEIC images in a directory to JPG format.

    Args:
        dir_path: Path to the directory containing HEIC files.
    """
    for filename in os.listdir(src_path):
        if filename.lower().endswith(('.heic', '.heif')):
            heic_filepath = os.path.join(src_path, filename)
            jpg_filepath = os.path.join(dest_path, filename[:-5] + '.jpg')
            convert_heic_to_jpg(heic_filepath, jpg_filepath)

src_path = "D:/capstone/datasets/hayden_butte1/raw"
dest_path = "D:/capstone/datasets/hayden_butte1/low_res"
convert_directory_heic_to_jpg(src_path, dest_path)
