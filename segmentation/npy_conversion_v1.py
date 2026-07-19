# Convert individual track png images (1024x1024) to npy files
# Provide root directory and consider the following folder structure:
# root directory (e.g., segmentation output folder) > experiment folder > shortened folder > recording folders containing the png files

# Script developed with the help of AI (Claude.AI)
# Last updated: 19/09/2025

# The authors of the code are Max Riekeles and Berke Santos. Contact: riekeles@tu-berlin.de
from PIL import Image
import numpy as np
from pathlib import Path
import re

def process_folder(root_folder):
    root_path = Path(root_folder)
    total_images_processed = 0

    # Iterate through each subfolder in the root folder
    for subfolder_path in root_path.iterdir():

        # Check if it's a directory
        if subfolder_path.is_dir():
            subfolder_count = 0
            print(f"Processing subfolder: {subfolder_path.name}")

            # Look for subsubfolders with pattern "shortened_(number)"
            for subsubfolder_path in subfolder_path.iterdir():

                # Check if it's a directory and matches the pattern "shortened_(number)"
                if subsubfolder_path.is_dir() and re.match(r'shortened_\d+', subsubfolder_path.name):

                    # Look for subsubsubfolders containing the t images
                    for subsubsubfolder_path in subsubfolder_path.iterdir():

                        if subsubsubfolder_path.is_dir():
                            # Create npy_tracks folder inside this directory
                            npy_tracks_folder = subsubsubfolder_path / 'npy_tracks'
                            npy_tracks_folder.mkdir(exist_ok=True)

                            # Process t images in this folder
                            folder_count = process_t_images_in_folder(subsubsubfolder_path, npy_tracks_folder)
                            subfolder_count += folder_count

            print(f"Total t images processed in {subfolder_path.name}: {subfolder_count}")
            total_images_processed += subfolder_count

    print(f"Total t images processed across all subfolders: {total_images_processed}")

def process_t_images_in_folder(folder_path, npy_tracks_folder):
    t_image_count = 0

    for file_path in folder_path.iterdir():
        # Only process files that match the pattern t(number).png
        if file_path.is_file() and re.match(r't\d+\.png$', file_path.name):
            output_npy_file = npy_tracks_folder / f"{file_path.stem}.npy"

            if process_image(file_path, output_npy_file):
                t_image_count += 1
                print(f"  Processed: {file_path.name}")

    return t_image_count

def process_image(input_file, output_npy_file):
    try:
        # Open the image
        image = Image.open(input_file)

        # Resize the image to 2048x2048
        resized_image = image.resize((2048, 2048))

        # Convert the resized image to 8-bit grayscale
        grayscale_image = resized_image.convert("L")

        # Convert the grayscale image to a NumPy array
        image_array = np.array(grayscale_image, dtype=np.uint8)

        # Save the NumPy array as an .npy file
        np.save(output_npy_file, image_array)

        return True

    except Exception as e:
        print(f"Error processing {input_file}: {e}")
        return False

# Example usage - replace with your actual root directory path
root_folder = "/media/general-max-riekeles/MMT_3/ME/ME_part2/Data/segmentation_output"
process_folder(root_folder)
