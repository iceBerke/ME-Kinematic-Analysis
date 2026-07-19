# Separate different tracks from a same image and save them in the same folder with _1, _2, etc. suffixes
# Input just needs to be the path of the image

# Script developed with the help of AI (Claude.AI)
# Last update: 14/09/2025

import cv2 as cv
import numpy as np
from pathlib import Path


def separate_tracks_simple(image_path, min_area):
    # Convert to Path object for easier handling
    input_path = Path(image_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input image not found: {image_path}")

    # Read the image
    image = cv.imread(str(input_path), cv.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Could not load image: {image_path}")

    print(f"Processing: {input_path.name}")

    # Convert to binary if not already
    _, binary = cv.threshold(image, 127, 255, cv.THRESH_BINARY)

    # Find connected components
    num_labels, labels, stats, centroids = cv.connectedComponentsWithStats(binary, connectivity=8)

    # Get file parts for naming
    parent_folder = input_path.parent
    file_stem = input_path.stem  # filename without extension
    file_ext = input_path.suffix  # extension with dot

    output_paths = []
    segment_count = 0

    print(f"Found {num_labels - 1} connected components")

    # Process each component (skip background label 0)
    for i in range(1, num_labels):
        area = stats[i, cv.CC_STAT_AREA]

        if area < min_area:
            print(f"Skipping component {i} (area: {area} < {min_area})")
            continue

        # Create mask for this component only
        component_mask = (labels == i).astype(np.uint8) * 255

        # Create output filename
        segment_count += 1
        output_filename = f"{file_stem}_{segment_count}{file_ext}"
        output_path = parent_folder / output_filename

        # Save the segment
        success = cv.imwrite(str(output_path), component_mask)

        if success:
            output_paths.append(str(output_path))
            print(f"Saved segment {segment_count}: {output_filename} (area: {area})")
        else:
            print(f"Failed to save segment {segment_count}: {output_filename}")

    print(f"Created {len(output_paths)} segment images")
    return output_paths


# Example usage:
if __name__ == "__main__":
    # Example: if you have an image at "/path/to/tracks.png"
    # This will create "/path/to/tracks_1.png", "/path/to/tracks_2.png", etc.

    image_path = "/media/berke-dhm/MMT_3/ME/ME_Biological/Data/New_Analysis/segmentation_output/Zinc_3/shortened_5seconds/ecoli_control_0h_sample3_rec4.tif_files_changed/t8.png" # Replace with your image path

    try:
        output_files = separate_tracks_simple(image_path, min_area=10)
        print(f"\nSuccess! Created {len(output_files)} files:")
        for file_path in output_files:
            print(f"  - {file_path}")
    except Exception as e:
        print(f"Error: {e}")
