# Batch blob detector for both dark and bright blobs with NPY output
#
# PURPOSE:
# This script performs automated blob detection on time-series microscopy images stored in a complex
# directory structure. It detects both dark and bright circular features (blobs) in .tif images and
# saves the results as NumPy arrays containing x,y coordinates, timepoints, and blob sizes.
# The script is designed for high-throughput analysis of bacterial tracking experiments.
#
# DIRECTORY STRUCTURE EXPECTED:
# root_directory/
# ├── segmentation_output/                    <- Output folder (created/used by this script)
# │   ├── subfolder_1/                       <- Mirrors data folder structure
# │   │   └── shortened_X/                   <- Matches shortened folders in data
# │   │       └── subsubfolder_1/            <- Matches data subsubfolders
# │   │           ├── npy_tracks/            <- Existing tracking data (optional)
# │   │           └── blobs_subsubfolder_1.npy <- NPY FILES SAVED HERE
# │   └── subfolder_2/
# │       └── shortened_Y/
# │           └── subsubfolder_2/
# │               └── blobs_subsubfolder_2.npy
# └── subfolder_1/                           <- Data folders (input)
#     └── shortened_X/                       <- Time-series experiment folders
#         └── subsubfolder_1/                <- Individual recording sessions
#             ├── raw/                       <- IMAGES TO PROCESS (.tif files)
#             │   ├── image_00000.tif       <- Timepoint 0
#             │   ├── image_00001.tif       <- Timepoint 1
#             │   └── ...
#             └── other_folders/             <- Other processing outputs (ignored)
#
# OUTPUT FORMAT:
# Each NPY file contains an array with shape (n_blobs, 4) where columns are:
# [x_coordinate, y_coordinate, timepoint, blob_size]
#
# FILE STRUCTURE: One NPY file per subsubfolder containing ALL timepoints from that experiment.
# This is efficient for time-series analysis - a typical experiment with 30+ images and ~200 blobs
# per image will result in ~6000+ blobs in a single file (~200KB), which is optimal for loading
# and analyzing temporal patterns.
#
# IMAGE PROCESSING: All images are resized to 2048x2048 pixels before blob detection, regardless
# of original image dimensions. This means:
# - Blob coordinates are ALWAYS relative to 2048x2048 space
# - Original image aspect ratios may be distorted if not square
# - Provides consistent coordinate system across different experiments
# - If original images differ significantly from 2048x2048, consider modifying resize behavior
#
# PARAMETERS:
# Adjustable parameters include min/max area thresholds for both dark and bright blobs,
# CLAHE preprocessing settings, and minimum distance filtering between detected blobs.
# All parameters are hard-coded in the main section below - no command line interface.

# Script developed with the help of AI (Claude.AI)
# Last updated: 19/09/2025

# The authors of the code are Max Riekeles and Berke Santos. Contact: riekeles@tu-berlin.de
import cv2 as cv
import numpy as np
import re
from pathlib import Path
import glob


def detect_blobs_single_image(image_path,
                              min_distance=30,
                              clipLimit=0.6,
                              tileGridSize=(16, 16),
                              dark_minThreshold=0,
                              dark_maxThreshold=125,
                              dark_minArea=35,
                              dark_maxArea=800,
                              bright_minThreshold=90,
                              bright_maxThreshold=255,
                              bright_minArea=35,
                              bright_maxArea=800):
    # Load image in grayscale
    img = cv.imread(image_path, 0)
    if img is None:
        print(f"Error: Could not load image from {image_path}")
        return None

    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv.createCLAHE(clipLimit=clipLimit, tileGridSize=tileGridSize)
    img_resized = cv.resize(img, (2048, 2048), interpolation=cv.INTER_LINEAR)
    img_clahe = clahe.apply(img_resized)

    # Setup blob detector parameters for DARK blobs
    params_dark = cv.SimpleBlobDetector_Params()
    params_dark.minThreshold = dark_minThreshold
    params_dark.maxThreshold = dark_maxThreshold
    params_dark.filterByArea = True
    params_dark.minArea = dark_minArea
    params_dark.maxArea = dark_maxArea
    params_dark.filterByCircularity = False
    params_dark.filterByConvexity = False
    params_dark.filterByInertia = False

    # Setup blob detector parameters for BRIGHT blobs
    params_bright = cv.SimpleBlobDetector_Params()
    params_bright.minThreshold = bright_minThreshold
    params_bright.maxThreshold = bright_maxThreshold
    params_bright.filterByArea = True
    params_bright.minArea = bright_minArea
    params_bright.maxArea = bright_maxArea
    params_bright.filterByCircularity = False
    params_bright.filterByConvexity = False
    params_bright.filterByInertia = False

    # Create detectors
    detector_dark = cv.SimpleBlobDetector_create(params_dark)
    detector_bright = cv.SimpleBlobDetector_create(params_bright)

    # Detect dark blobs on CLAHE image
    keypoints_dark = detector_dark.detect(img_clahe)

    # Detect bright blobs on inverted CLAHE image
    img_inverted = cv.bitwise_not(img_clahe)
    keypoints_bright = detector_bright.detect(img_inverted)

    # Combine all keypoints
    keypoints = keypoints_dark + keypoints_bright

    # Filter keypoints by minimum distance
    filtered_keypoints = []
    for kp in keypoints:
        if all(np.linalg.norm(np.array(kp.pt) - np.array(k.pt)) >= min_distance for k in filtered_keypoints):
            filtered_keypoints.append(kp)

    return filtered_keypoints


def extract_timepoint_from_filename(filename):
    # Look for pattern with underscores followed by numbers at the end
    match = re.search(r'_(\d+)(?:\.\w+)?$', filename)
    if match:
        return int(match.group(1))
    else:
        # Fallback: try to find any number sequence in the filename
        numbers = re.findall(r'\d+', filename)
        if numbers:
            return int(numbers[-1])  # Take the last number found
        else:
            return 0  # Default timepoint if no number found


def process_batch_blob_detection(root_directory,
                                 segmentation_folder_name="segmentation_output",
                                 subfolder_parameters=None,
                                 default_parameters=None):
    # Set default parameters if not provided
    if default_parameters is None:
        default_parameters = {
            'min_distance': 30,
            'clipLimit': 0.6,
            'tileGridSize': (16, 16),
            'dark_minThreshold': 0,
            'dark_maxThreshold': 125,
            'dark_minArea': 35,
            'dark_maxArea': 800,
            'bright_minThreshold': 90,
            'bright_maxThreshold': 255,
            'bright_minArea': 35,
            'bright_maxArea': 800
        }

    if subfolder_parameters is None:
        subfolder_parameters = {}

    root_path = Path(root_directory)
    segmentation_path = root_path / segmentation_folder_name

    if not segmentation_path.exists():
        print(f"Error: Segmentation folder not found at {segmentation_path}")
        return

    # Process each subfolder in segmentation_output
    for subfolder in segmentation_path.iterdir():
        if not subfolder.is_dir():
            continue

        subfolder_name = subfolder.name
        print(f"\nProcessing subfolder: {subfolder_name}")

        # Get parameters for this specific subfolder
        if subfolder_name in subfolder_parameters:
            current_params = subfolder_parameters[subfolder_name].copy()
            # Fill in any missing parameters with defaults
            for key, value in default_parameters.items():
                if key not in current_params:
                    current_params[key] = value
            print(f"  Using custom parameters for {subfolder_name}")
        else:
            current_params = default_parameters.copy()
            print(f"  Using default parameters for {subfolder_name}")

        # Print current parameters for this subfolder
        print(f"  Parameters: {current_params}")

        # Look for corresponding data folder in root directory
        data_folder = root_path / subfolder_name
        if not data_folder.exists():
            print(f"Warning: No corresponding data folder found for {subfolder_name}")
            continue

        # Process each shortened_* folder
        shortened_folders = glob.glob(str(data_folder / "shortened_*"))
        for shortened_folder in shortened_folders:
            shortened_path = Path(shortened_folder)
            shortened_name = shortened_path.name

            print(f"  Processing {shortened_name}")

            # Find corresponding shortened folder in segmentation_output
            seg_shortened_path = subfolder / shortened_name
            if not seg_shortened_path.exists():
                print(f"    Warning: No corresponding segmentation folder for {shortened_name}")
                continue

            # Process each subsubfolder
            for subsubfolder in shortened_path.iterdir():
                if not subsubfolder.is_dir():
                    continue

                print(f"    Processing subsubfolder: {subsubfolder.name}")

                # Look for raw folder
                raw_folder = subsubfolder / "raw"
                if not raw_folder.exists():
                    print(f"      No 'raw' folder found in {subsubfolder.name}")
                    continue

                # Find corresponding output location in segmentation_output
                output_folder = seg_shortened_path / subsubfolder.name
                output_folder.mkdir(parents=True, exist_ok=True)

                # Process all images in raw folder
                image_extensions = ['*.tif', '*.tiff', '*.png', '*.jpg', '*.jpeg']
                image_files = []
                for ext in image_extensions:
                    image_files.extend(glob.glob(str(raw_folder / ext)))

                if not image_files:
                    print(f"      No images found in {raw_folder}")
                    continue

                print(f"      Found {len(image_files)} images")

                # Process each image and collect blob data
                all_blob_data = []

                for image_file in sorted(image_files):  # Sort to ensure consistent ordering
                    image_path = Path(image_file)
                    timepoint = extract_timepoint_from_filename(image_path.name)

                    # Detect blobs using current subfolder parameters
                    keypoints = detect_blobs_single_image(str(image_path), **current_params)

                    if keypoints is not None:
                        # Convert keypoints to array format: [x, y, t, size]
                        for kp in keypoints:
                            blob_data = [kp.pt[0], kp.pt[1], timepoint, kp.size]
                            all_blob_data.append(blob_data)

                # Save blob data as NPY file
                if all_blob_data:
                    blob_array = np.array(all_blob_data)
                    output_filename = f"blobs_{subsubfolder.name}.npy"
                    output_path = output_folder / output_filename

                    np.save(output_path, blob_array)
                    print(f"      Saved {len(all_blob_data)} blobs to {output_path}")
                    print(f"      Array shape: {blob_array.shape} (columns: x, y, t, size)")
                else:
                    print(f"      No blobs detected in {subsubfolder.name}")


# Main execution
if __name__ == "__main__":
    # HARD-CODED ROOT DIRECTORY - Modify this to match your actual root directory
    root_directory = "/media/general-max-riekeles/MMT_3/ME/ME_Biological/Data/New_Analysis"

    # DEFAULT blob detection parameters (used when no subfolder-specific parameters are provided)
    default_params = {
        'min_distance': 30,
        'clipLimit': 0.6,
        'tileGridSize': (16, 16),
        'dark_minThreshold': 0,
        'dark_maxThreshold': 125,
        'dark_minArea': 35,
        'dark_maxArea': 800,
        'bright_minThreshold': 90,
        'bright_maxThreshold': 255,
        'bright_minArea': 35,
        'bright_maxArea': 800
    }

    # SUBFOLDER-SPECIFIC PARAMETERS
    # Define custom parameters for specific subfolders here
    # Only include parameters you want to override - missing ones will use defaults
    # SUBFOLDER-SPECIFIC PARAMETERS
    # Define custom parameters for specific subfolders here
    # Only include parameters you want to override - missing ones will use defaults
    subfolder_params = {
        'Lead_1': {
            'min_distance': 30,
            'clipLimit': 0.6,
            'tileGridSize': (16, 16),
            'dark_minThreshold': 0,
            'dark_maxThreshold': 125,
            'dark_minArea': 35,
            'dark_maxArea': 800,
            'bright_minThreshold': 80,  # Changed from default 90 to 80
            'bright_maxThreshold': 255,
            'bright_minArea': 50,  # Changed from default 35 to 50
            'bright_maxArea': 800
        },
        'Lead_2': {
            'min_distance': 30,
            'clipLimit': 0.6,
            'tileGridSize': (16, 16),
            'dark_minThreshold': 0,
            'dark_maxThreshold': 125,
            'dark_minArea': 30,  # Changed from default 35 to 30
            'dark_maxArea': 800,
            'bright_minThreshold': 80,  # Changed from default 90 to 80
            'bright_maxThreshold': 255,
            'bright_minArea': 50,  # Changed from default 35 to 50
            'bright_maxArea': 800
        },
        'Lead_3': {
            'min_distance': 30,
            'clipLimit': 0.6,
            'tileGridSize': (16, 16),
            'dark_minThreshold': 0,
            'dark_maxThreshold': 125,
            'dark_minArea': 35,
            'dark_maxArea': 800,
            'bright_minThreshold': 100,  # Changed from default 90 to 100
            'bright_maxThreshold': 255,
            'bright_minArea': 50,  # Changed from default 35 to 50
            'bright_maxArea': 800
        },
        'Lead_4': {
            'min_distance': 30,
            'clipLimit': 0.6,
            'tileGridSize': (16, 16),
            'dark_minThreshold': 0,
            'dark_maxThreshold': 125,
            'dark_minArea': 35,
            'dark_maxArea': 800,
            'bright_minThreshold': 100,  # Changed from default 90 to 100
            'bright_maxThreshold': 255,
            'bright_minArea': 50,  # Changed from default 35 to 50
            'bright_maxArea': 800
        },
        'Zinc_3': {
            'min_distance': 30,
            'clipLimit': 0.6,
            'tileGridSize': (16, 16),
            'dark_minThreshold': 0,
            'dark_maxThreshold': 125,
            'dark_minArea': 35,
            'dark_maxArea': 800,
            'bright_minThreshold': 90,  # Same as default
            'bright_maxThreshold': 255,
            'bright_minArea': 35,  # Same as default
            'bright_maxArea': 800
        }
    }

    print(f"Starting batch blob detection...")
    print(f"Root directory: {root_directory}")
    print(f"Default parameters: {default_params}")
    print(f"Custom subfolder parameters defined for: {list(subfolder_params.keys())}")

    # Run batch processing with custom parameters per subfolder
    process_batch_blob_detection(
        root_directory=root_directory,
        subfolder_parameters=subfolder_params,
        default_parameters=default_params
    )

    print("\nBatch processing complete!")
