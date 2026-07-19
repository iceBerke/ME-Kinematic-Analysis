import cv2 as cv
import numpy as np
import os
import shutil
from pathlib import Path

def process_image_for_tracks(image_path, colors, output_folder, min_area):
    """
    Process an image to extract tracks of specified colors, remove isolated points, and save the results.
    """
    original_image = cv.imread(image_path, cv.IMREAD_COLOR)
    if original_image is None:
        raise ValueError(f"Image not loaded properly: {image_path}")

    print(f"Image loaded: {image_path}")
    print(f"Image shape: {original_image.shape}")
    print(f"Image dtype: {original_image.dtype}")

    track_counter = 1

    for color in colors:
        color_np = np.array(color[::-1], dtype=np.uint8)
        print(f"Processing color: {color_np[::-1]}")

        mask = cv.inRange(original_image, color_np, color_np)
        non_zero_count = np.count_nonzero(mask)
        print(f"Non-zero pixels in mask for color {color}: {non_zero_count}")

        if non_zero_count > 0:
            # Remove small objects (isolated points)
            nb_components, output, stats, centroids = cv.connectedComponentsWithStats(mask, connectivity=8)
            sizes = stats[1:, -1]
            nb_components = nb_components - 1

            img2 = np.zeros((output.shape))
            for i in range(0, nb_components):
                if sizes[i] >= min_area:
                    img2[output == i + 1] = 255

            # Create the final track image
            track_image = np.zeros_like(original_image)
            track_image[img2 > 0] = [255, 255, 255]  # Draw the track in white

            track_image_path = os.path.join(output_folder, f"t{track_counter}.png")
            cv.imwrite(track_image_path, track_image)

            print(f"Saved {track_image_path}")
            track_counter += 1
        else:
            print(f"No pixels detected for color {color}")

def find_mhi_color_images(root_directory):
    """
    Find all *mhi*_color.tif images in validate folders and return their paths with metadata.
    """
    root_path = Path(root_directory)
    mhi_images = []

    # Walk through the directory structure
    for experiment_dir in root_path.iterdir():
        if not experiment_dir.is_dir():
            continue

        print(f"Scanning experiment directory: {experiment_dir.name}")

        # Look for shortened_* folders
        for item in experiment_dir.rglob("shortened_*"):
            if not item.is_dir():
                continue

            shortened_folder = item.name
            print(f"  Found shortened folder: {shortened_folder}")

            # Look for rec folders within shortened folders
            for rec_folder in item.iterdir():
                if not rec_folder.is_dir():
                    continue

                print(f"    Scanning rec folder: {rec_folder.name}")

                # Look for validate folder
                validate_folder = rec_folder / "validate"
                if not validate_folder.exists():
                    print(f"      No validate folder found in {rec_folder.name}")
                    continue

                # Find *mhi*_color.tif file
                mhi_color_files = list(validate_folder.glob("*mhi*_color.tif"))
                mhi_png_files = list(validate_folder.glob("*mhi*.png"))

                if mhi_color_files:
                    mhi_color_file = mhi_color_files[0]  # Take the first match
                    mhi_png_file = mhi_png_files[0] if mhi_png_files else None

                    mhi_images.append({
                        'mhi_color_path': mhi_color_file,
                        'mhi_png_path': mhi_png_file,
                        'experiment_name': experiment_dir.name,
                        'shortened_folder': shortened_folder,
                        'rec_folder': rec_folder.name
                    })
                    print(f"      Found MHI color file: {mhi_color_file.name}")
                    if mhi_png_file:
                        print(f"      Found MHI png file: {mhi_png_file.name}")
                else:
                    print(f"      No *mhi*_color.tif file found in {validate_folder}")

    return mhi_images

def process_all_mhi_images(root_directory, colors, min_area):
    """
    Process all MHI color images found in the directory structure.
    """
    root_path = Path(root_directory)
    segmentation_output_dir = root_path / "segmentation_output"

    # Find all MHI images
    mhi_images = find_mhi_color_images(root_directory)

    if not mhi_images:
        print("No MHI color images found!")
        return

    print(f"\nFound {len(mhi_images)} MHI color images to process")

    for mhi_data in mhi_images:
        print(f"\nProcessing: {mhi_data['mhi_color_path']}")

        # Create output directory structure
        output_dir = (segmentation_output_dir /
                      mhi_data['experiment_name'] /
                      mhi_data['shortened_folder'] /
                      mhi_data['rec_folder'])

        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Process the MHI color image for track segmentation
            process_image_for_tracks(
                str(mhi_data['mhi_color_path']),
                colors,
                str(output_dir),
                min_area
            )

            # Copy the MHI png file if it exists
            if mhi_data['mhi_png_path'] and mhi_data['mhi_png_path'].exists():
                destination_png = output_dir / mhi_data['mhi_png_path'].name
                shutil.copy2(mhi_data['mhi_png_path'], destination_png)
                print(f"Copied MHI png to: {destination_png}")
            else:
                print("No corresponding MHI png file found to copy")

        except ValueError as e:
            print(f"Error processing {mhi_data['mhi_color_path']}: {e}")

    print(f"\nProcessing complete! Results saved in: {segmentation_output_dir}")

# Usage
root_directory = "/media/berke-dhm/MMT_3/ME/ME_Biological/Data/New_Analysis"  # Update this path

colors = [
    (254, 209, 209),
    (226, 209, 209),
    (211, 209, 209),
    (189, 209, 209),
    (171, 209, 209),
    (145, 209, 209),
    (1, 209, 209),
    (254, 254, 254),
    (254, 231, 254),
    (254, 220, 254),
    (254, 204, 254),
    (254, 182, 254),
    (254, 254, 236),
    (254, 254, 220),
    (254, 254, 203),
    (254, 254, 184),
    (254, 254, 160),
    (254, 254, 1),
    (226, 254, 254),
    (211, 254, 254),
    (189, 254, 254),
    (171, 254, 254),
    (145, 254, 254),
    (1, 254, 254),
    (1, 182, 254),
    (1, 220, 254),
    (1, 254, 1),
    (1, 254, 184),
    (254, 182, 1),
    (189, 182, 1),
    (214, 214, 214),
    (214, 254, 214),
    (214, 253, 214),
    (214, 250, 214),
    (214, 249, 214),
    (214, 248, 214),
    (214, 246, 214),
    (214, 245, 214),
    (214, 244, 214),
    (214, 242, 214),
    (214, 241, 214),
    (214, 240, 214),
    (214, 236, 214),
    (214, 232, 214),
    (214, 229, 214),
    (214, 228, 214),
    (214, 225, 214),
    (214, 224, 214),
    (214, 221, 214),
    (214, 217, 214),
    (214, 214, 254),
    (214, 214, 253),
    (214, 214, 250),
    (214, 214, 249),
    (214, 214, 246),
    (214, 214, 245),
    (214, 214, 242),
    (214, 214, 241),
    (214, 214, 238),
    (214, 214, 229),
    (214, 214, 225),
    (214, 214, 221),
    (214, 214, 217),
    (214, 214, 209),
    (214, 214, 199),
    (214, 214, 181),
    (214, 214, 179)
]

# Run the processing
process_all_mhi_images(root_directory, colors, min_area=25)
