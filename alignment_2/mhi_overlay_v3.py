# ============================================================================
# RESIZES TO 2048x2048 PIXELS THE ORIGINAL MHIs - UPDATED FOR TEMPORAL CORRECTION
# ============================================================================
#
# This script processes the aligned blob results by creating overlay visualizations
# on Motion History Images (MHI). It batch processes an entire directory structure,
# drawing colored circles representing aligned blobs from alignment results onto the
# existing MHI images.
#
# UPDATED: Now uses alignment_results_2/ folder which contains temporally corrected
# blob data. This ensures visualizations show blobs with accurate timing information
# rather than potentially delayed detection timepoints.
#
# Expected Directory Structure:
# root_directory/
# ├── segmentation_output/                    # Output folder (input/output for this script)
# │   ├── subfolder_1/                       # Mirrors data folder structure
# │   │   └── shortened_X/                   # Matches shortened folders in data
# │   │       └── subsubfolder_1/            # Matches data subsubfolders
# │   │           ├── npy_tracks/            # Track data files (not used by this script)
# │   │           │   ├── track_001.npy      # Individual track segments
# │   │           │   ├── track_002.npy
# │   │           │   └── ...
# │   │           ├── blobs_subsubfolder_1.npy # Blob detection results (not used by this script)
# │   │           ├── *_mhi.png              # MHI background image (INPUT - must exist)
# │   │           ├── alignment_summary_corrected.txt  # Summary of corrected alignment results (ignored)
# │   │           ├── alignment_results_2/   # Corrected alignment output (INPUT)
# │   │           │   └── aligned_blobs_*.npy # Processed blob files with temporal correction
# │   │           └── mhi_overlay_corrected.png # Final overlay output (CREATED BY THIS SCRIPT)
# │   └── subfolder_2/
# │       └── shortened_Y/
# │           └── subsubfolder_2/
# │               ├── npy_tracks/
# │               ├── blobs_subsubfolder_2.npy
# │               ├── *_mhi.png              # MHI background image (INPUT)
# │               ├── alignment_summary_corrected.txt
# │               ├── alignment_results_2/   # INPUT: Contains temporally corrected .npy files
# │               │   └── aligned_blobs_*.npy
# │               └── mhi_overlay_corrected.png # OUTPUT: Created by this script
# └── subfolder_1/                           # Data folders (not used by this script)
#     └── shortened_X/                       # Time-series experiment folders
#         └── subsubfolder_1/                # Individual recording sessions
#             ├── raw/                       # Original images (not used)
#             │   ├── image_00000.tif       # Timepoint 0
#             │   ├── image_00001.tif       # Timepoint 1
#             │   └── ...
#             ├── validate/                  # Validation data (not used)
#             │   └── MHI.npy               # Motion History Image array
#             └── other_folders/             # Other processing outputs (ignored)
#
# Script Workflow:
# 1. Recursively finds all subsubfolders in segmentation_output/
# 2. For each subsubfolder:
#    - Locates the *_mhi.png background image
#    - Finds all .npy files in alignment_results_2/ folder (temporally corrected data)
#    - Loads blob coordinates from each .npy file
#    - Draws colored circles on the MHI image (different color per file)
#    - Saves the final overlay as mhi_overlay_corrected.png
#
# Input Files:
# - *_mhi.png: Background Motion History Image (must exist in each subsubfolder)
# - alignment_results_2/*.npy: Temporally corrected blob coordinate files with format [x, y, timepoint, ...]
#
# Output Files:
# - mhi_overlay_corrected.png: Final visualization with all corrected blobs overlaid (created in each subsubfolder)
#

# Script developed with the help of AI (Claude.AI)
# Last update: 22/09/2025

import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw
import os
import glob
from pathlib import Path
import gc


def load_blob_data(npy_file):
    """Load blob data with memory-efficient error handling"""
    try:
        data = np.load(npy_file)
        print(f"  Loaded {len(data)} corrected blobs from {Path(npy_file).name}")
        return data
    except Exception as e:
        print(f"  Error loading {npy_file}: {e}")
        return None


def draw_all_blobs_on_image(image_path, all_blob_coordinates, output_path, blob_color, blob_size):
    """Draw blobs on image with memory-efficient processing"""
    img = None
    draw = None
    try:
        # Load the image
        img = Image.open(image_path)

        # Convert to RGB if needed (for drawing)
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # RESIZE IMAGE TO 2048x2048
        img = img.resize((2048, 2048), Image.LANCZOS)

        # Get image dimensions for boundary checking (now 2048x2048)
        img_width, img_height = img.size

        # Create a drawing context
        draw = ImageDraw.Draw(img)

        # Draw all blobs with memory-efficient batch processing
        blob_count = 0
        if all_blob_coordinates:
            for x, y in all_blob_coordinates:
                # Constrain to image boundaries
                x = max(0, min(img_width - 1, int(x)))
                y = max(0, min(img_height - 1, int(y)))

                # Draw a circle for each blob
                draw.ellipse([x - blob_size, y - blob_size, x + blob_size, y + blob_size],
                             fill=blob_color, outline=blob_color)
                blob_count += 1

        # Save the image (will be 2048x2048)
        img.save(output_path)
        print(f"  Drew {blob_count} corrected blobs on image (resized to 2048x2048)")
        return True

    except Exception as e:
        print(f"  Error processing {image_path}: {e}")
        return False
    finally:
        # Explicitly clean up image objects
        if draw is not None:
            del draw
        if img is not None:
            del img
        # Force garbage collection
        gc.collect()


def find_mhi_png_image(folder_path):
    """Find PNG file ending with '_mhi.png' in the given folder"""
    png_files = []
    for file in os.listdir(folder_path):
        if file.lower().endswith('.png') and os.path.isfile(os.path.join(folder_path, file)):
            png_files.append(file)

    for png_file in png_files:
        if png_file.lower().endswith('_mhi.png'):
            return os.path.join(folder_path, png_file)

    return None


def collect_all_blobs(blob_data):
    """Extract x,y coordinates from blob data with memory-efficient processing"""
    all_blobs = []

    if blob_data is not None and len(blob_data) > 0:
        # Process in chunks to be more memory efficient
        chunk_size = 1000  # Process 1000 blobs at a time
        for i in range(0, len(blob_data), chunk_size):
            chunk = blob_data[i:i + chunk_size]
            for row in chunk:
                if len(row) >= 2:  # Ensure we have at least x, y
                    x, y = row[0], row[1]
                    all_blobs.append((x, y))

            # Force garbage collection after each chunk
            if i > 0 and i % (chunk_size * 10) == 0:  # Every 10k blobs
                gc.collect()

    return all_blobs


def process_single_subsubfolder(subsubfolder_path, color_list, blob_size):
    """Process a single subsubfolder for blob visualization with memory optimization"""

    print(f"\nProcessing: {subsubfolder_path}")

    # Define paths - UPDATED to use alignment_results_2
    alignment_results_path = os.path.join(subsubfolder_path, "alignment_results_2")

    # Check if alignment_results_2 folder exists
    if not os.path.exists(alignment_results_path):
        print(f"  Warning: alignment_results_2 folder not found")
        return False, "alignment_results_2 folder not found"

    # Find MHI PNG image in the subsubfolder
    mhi_image_path = find_mhi_png_image(subsubfolder_path)
    if mhi_image_path is None:
        print(f"  Warning: No _mhi.png image found")
        return False, "No _mhi.png image found"

    print(f"  Found MHI image: {Path(mhi_image_path).name}")

    # Get all npy files from alignment_results_2
    npy_files = glob.glob(os.path.join(alignment_results_path, "*.npy"))
    print(f"  Found {len(npy_files)} .npy files in alignment_results_2 (temporally corrected)")

    if not npy_files:
        print("  No .npy files found in alignment_results_2!")
        return False, "No .npy files found in alignment_results_2"

    # Set output path - UPDATED filename to indicate corrected data
    output_path = os.path.join(subsubfolder_path, "mhi_overlay_corrected.png")

    current_image_path = mhi_image_path
    total_processed = 0
    total_blobs = 0

    try:
        # Process each npy file with memory management
        for npy_file in sorted(npy_files):  # Sort for consistent processing order
            print(f"  Processing: {Path(npy_file).name}")

            # Load blob data
            blob_data = load_blob_data(npy_file)
            if blob_data is None:
                continue

            # Collect all blobs
            current_blob_coords = collect_all_blobs(blob_data)
            blob_count = len(current_blob_coords)
            print(f"    Found {blob_count} total corrected blobs")
            total_blobs += blob_count

            # Free the original blob_data array immediately
            del blob_data
            gc.collect()

            # Cycle through colors
            blob_color = color_list[total_processed % len(color_list)]
            print(f"    Using color: {blob_color}")

            if current_blob_coords:
                # Draw all blobs on the image
                if draw_all_blobs_on_image(current_image_path, current_blob_coords, output_path, blob_color, blob_size):
                    current_image_path = output_path  # Use the updated image for next iteration
                    total_processed += 1
                else:
                    print(f"    Failed to process {Path(npy_file).name}")
                    return False, f"Failed to draw blobs from {Path(npy_file).name}"

            # Clean up coordinates immediately
            del current_blob_coords
            gc.collect()

        print(f"  SUCCESS: Processed {total_processed} files with {total_blobs} total corrected blobs")
        print(f"  Output saved to: {output_path}")
        return True, f"Processed {total_processed} files, {total_blobs} corrected blobs"

    except Exception as e:
        error_msg = f"Exception during processing: {str(e)}"
        print(f"  ERROR: {error_msg}")
        return False, error_msg
    finally:
        # Final cleanup
        gc.collect()


def find_all_subsubfolders(segmentation_output_path):
    """Find all subsubfolders in the directory structure"""
    subsubfolders = []

    # Walk through segmentation_output directory
    for subfolder in os.listdir(segmentation_output_path):
        subfolder_path = os.path.join(segmentation_output_path, subfolder)
        if not os.path.isdir(subfolder_path):
            continue

        # Look for shortened_X folders
        for shortened_folder in os.listdir(subfolder_path):
            shortened_path = os.path.join(subfolder_path, shortened_folder)
            if not os.path.isdir(shortened_path):
                continue

            # Look for subsubfolders
            for subsubfolder in os.listdir(shortened_path):
                subsubfolder_path = os.path.join(shortened_path, subsubfolder)
                if os.path.isdir(subsubfolder_path):
                    subsubfolders.append(subsubfolder_path)

    return sorted(subsubfolders)


def batch_process_blob_visualization(segmentation_output_path, color_list, blob_size):
    """
    Main function to batch process all subsubfolders for blob visualization using corrected data.

    Args:
        segmentation_output_path: Path to the root segmentation_output directory
        color_list: List of colors to cycle through for different npy files
        blob_size: Size of the blob circles to draw

    Returns:
        dict: Summary of processing results
    """

    print(f"Starting batch processing of temporally corrected blob data: {segmentation_output_path}")
    print("Using alignment_results_2/ folders (temporally corrected data)")
    print("=" * 80)

    # Find all subsubfolders
    subsubfolders = find_all_subsubfolders(segmentation_output_path)

    print(f"Found {len(subsubfolders)} subsubfolders to process")

    if not subsubfolders:
        print("No subsubfolders found! Check the directory structure.")
        return {"total": 0, "successful": 0, "failed": 0, "success_rate": 0.0}

    # Initialize tracking variables
    successful_folders = []
    failed_folders = []
    processing_details = {}

    # Process each subsubfolder with memory management
    for i, subsubfolder_path in enumerate(subsubfolders, 1):
        print(f"\n[{i}/{len(subsubfolders)}] " + "=" * 60)

        try:
            success, details = process_single_subsubfolder(subsubfolder_path, color_list, blob_size)

            folder_name = os.path.relpath(subsubfolder_path, segmentation_output_path)
            processing_details[folder_name] = details

            if success:
                successful_folders.append(folder_name)
                print(f"SUCCESS: {folder_name}")
            else:
                failed_folders.append(folder_name)
                print(f"FAILED: {folder_name} - {details}")

        except Exception as e:
            folder_name = os.path.relpath(subsubfolder_path, segmentation_output_path)
            error_msg = f"Unexpected error: {str(e)}"
            failed_folders.append(folder_name)
            processing_details[folder_name] = error_msg
            print(f"FAILED: {folder_name} - {error_msg}")

        # Periodic memory cleanup
        if i % 5 == 0:  # Every 5 folders
            print(f"\n[Memory cleanup after {i} folders]")
            gc.collect()

    # Calculate summary statistics
    total_folders = len(subsubfolders)
    successful_count = len(successful_folders)
    failed_count = len(failed_folders)
    success_rate = (successful_count / total_folders * 100) if total_folders > 0 else 0

    # Print detailed summary
    print("\n" + "=" * 80)
    print("BATCH PROCESSING COMPLETE - TEMPORALLY CORRECTED VISUALIZATION")
    print("=" * 80)
    print(f"SUMMARY STATISTICS:")
    print(f"   Total subsubfolders processed: {total_folders}")
    print(f"   Successful: {successful_count}")
    print(f"   Failed: {failed_count}")
    print(f"   Success rate: {success_rate:.1f}%")

    # Show successful folders
    if successful_folders:
        print(f"\nSUCCESSFUL FOLDERS ({len(successful_folders)}):")
        for folder in successful_folders:
            print(f"   + {folder} - {processing_details[folder]}")

    # Show failed folders with reasons
    if failed_folders:
        print(f"\nFAILED FOLDERS ({len(failed_folders)}):")
        for folder in failed_folders:
            print(f"   - {folder} - {processing_details[folder]}")

    print(f"\nOutput files: mhi_overlay_corrected.png (contains temporally corrected blob positions)")
    print("=" * 80)

    # Return summary for programmatic use
    return {
        "total": total_folders,
        "successful": successful_count,
        "failed": failed_count,
        "success_rate": success_rate,
        "successful_folders": successful_folders,
        "failed_folders": failed_folders,
        "details": processing_details
    }


# Example usage
if __name__ == "__main__":
    # Set your root segmentation_output directory path here
    segmentation_output_path = "/media/general-max-riekeles/MMT_3/ME/Analysis_20_09/segmentation_output"

    # Define color list (same as original)
    color_list = [
        'red', 'darkblue', 'forestgreen', 'gold', 'crimson', 'turquoise', 'chocolate',
        'blue', 'limegreen', 'orange', 'lavender', 'steelblue', 'khaki', 'hotpink',
        'green', 'coral', 'mediumblue', 'darkorange', 'plum', 'lightblue', 'sienna',
        'yellow', 'darkgreen', 'violet', 'lightsalmon', 'royalblue', 'tan', 'deeppink',
        'purple', 'seagreen', 'goldenrod', 'powderblue', 'firebrick', 'wheat', 'orchid',
        'pink', 'mediumseagreen', 'darksalmon', 'skyblue', 'darkred', 'burlywood', 'indigo',
        'brown', 'lightgreen', 'peachpuff', 'lightskyblue', 'indianred', 'darkkhaki', 'thistle',
        'black', 'palegreen', 'moccasin', 'deepskyblue', 'lightcoral', 'saddlebrown', 'mediumpurple',
        'white', 'springgreen', 'papayawhip', 'dodgerblue', 'mistyrose', 'peru', 'mediumorchid',
        'gray', 'mediumspringgreen', 'lightgoldenrodyellow', 'cornflowerblue', 'rosybrown', 'sandybrown', 'darkorchid',
        'cyan', 'lawngreen', 'lemonchiffon', 'cadetblue', 'tomato', 'navajowhite', 'darkviolet',
        'magenta', 'chartreuse', 'lightyellow', 'teal', 'orangered', 'bisque', 'blueviolet',
        'lime', 'greenyellow', 'palegoldenrod', 'maroon', 'lightpink', 'blanchedalmond', 'mediumvioletred',
        'navy', 'olive', 'darkgoldenrod', 'silver', 'salmon', 'cornsilk', 'palevioletred',
        'beige', 'ivory', 'linen', 'fuchsia', 'lightgray', 'darkgray', 'dimgray',
        'slategray', 'lightslategray', 'gainsboro', 'whitesmoke', 'grey', 'lightgrey', 'darkgrey',
        'dimgrey', 'slategrey', 'lightslategrey'
    ]

    # Run batch processing for temporally corrected data
    results = batch_process_blob_visualization(
        segmentation_output_path=segmentation_output_path,
        color_list=color_list,
        blob_size=5
    )
