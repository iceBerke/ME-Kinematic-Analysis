# Script to merge multiple PNG images with white segments on black backgrounds
# Creates a single image with all white segments combined
# HARDCODED PATHS VERSION - NO COMMAND LINE USAGE

# Script developed with the help of AI (Claude.AI)
# Last update: 16/09/2025

import cv2
import numpy as np
from pathlib import Path


def merge_specific_files(file_paths, output_path):
    """
    Merge specific image files by their paths.

    Args:
        file_paths: List of paths to PNG files
        output_path: Path where to save the merged image

    Returns:
        True if successful, False otherwise
    """
    if not file_paths:
        print("No files provided for merging")
        return False

    print(f"Merging {len(file_paths)} specific files:")
    for file_path in file_paths:
        print(f"  - {Path(file_path).name}")

    # Read the first image to get dimensions
    first_image = cv2.imread(file_paths[0], cv2.IMREAD_GRAYSCALE)
    if first_image is None:
        print(f"Error: Could not read first image '{file_paths[0]}'")
        return False

    height, width = first_image.shape
    print(f"Image dimensions: {width}x{height}")

    # Create a black background image
    merged_image = np.zeros((height, width), dtype=np.uint8)

    # Process each file
    for file_path in file_paths:
        print(f"Processing: {Path(file_path).name}")

        # Read the image
        image = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)

        if image is None:
            print(f"Warning: Could not read '{file_path}', skipping...")
            continue

        # Check if dimensions match
        if image.shape != (height, width):
            print(f"Warning: '{Path(file_path).name}' has different dimensions, resizing...")
            image = cv2.resize(image, (width, height))

        # Add white pixels from this image to the merged image
        merged_image = np.maximum(merged_image, image)

    # Save the merged image
    success = cv2.imwrite(output_path, merged_image)

    if success:
        print(f"\nMerged image saved as: {output_path}")

        # Print statistics
        total_white_pixels = np.sum(merged_image > 127)
        total_pixels = height * width
        coverage_percent = (total_white_pixels / total_pixels) * 100

        print(f"Statistics:")
        print(f"  - Total white pixels: {total_white_pixels:,}")
        print(f"  - Image coverage: {coverage_percent:.2f}%")

        return True
    else:
        print(f"Error: Failed to save merged image to '{output_path}'")
        return False


def main():
    print("Image Merger Tool")
    print("=" * 30)
    print("Merging specific PNG files with hardcoded paths\n")

    # HARDCODE YOUR FILE PATHS HERE:
    files_to_merge = [
        "/media/berke-dhm/MMT_3/ME/ME_Biological/Data/New_Analysis/segmentation_output/Lead_3/shortened_10seconds/ecoli_pb10_0h_sample3_rec4.tif_files_changed/t12_1.png",
        "/media/berke-dhm/MMT_3/ME/ME_Biological/Data/New_Analysis/segmentation_output/Lead_3/shortened_10seconds/ecoli_pb10_0h_sample3_rec4.tif_files_changed/t12_3.png"
    ]

    # HARDCODE YOUR OUTPUT PATH HERE:
    output_file = "/media/berke-dhm/MMT_3/ME/ME_Biological/Data/New_Analysis/segmentation_output/Lead_3/shortened_10seconds/ecoli_pb10_0h_sample3_rec4.tif_files_changed/t12_merged.png"

    # Check if paths are still default/example
    if not files_to_merge:
        print("Please update the file paths in the script:")
        print("1. Edit the 'files_to_merge' list with your actual PNG file paths")
        print("2. Edit the 'output_file' with your desired output path")
        print("3. Remove this check and hardcode your real paths")
        return

    try:
        success = merge_specific_files(files_to_merge, output_file)

        if success:
            print(f"\nSuccess! Merged image created at: {output_file}")
        else:
            print("\nFailed to create merged image.")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()