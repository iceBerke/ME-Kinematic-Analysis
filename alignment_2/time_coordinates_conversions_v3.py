# ==============================================================================
# Data Processing Script for Blob Tracking Coordinate Conversion - UPDATED FOR TEMPORAL CORRECTION
# ==============================================================================
#
# Description:
# This script processes filtered blob tracking data (.npy files) and converts
# coordinates from pixel space to real-world units (micrometers) and time from
# frame numbers to seconds using acquisition frequency data.
#
# UPDATED: Now processes temporally corrected alignment results from alignment_results_2/
# folder, which contains blob data with MHI-corrected timepoints. This ensures the
# converted data has accurate timing information rather than potentially delayed
# detection timepoints, addressing high-velocity artifacts in motion analysis.
#
# Input Requirements:
# - Root directory containing segmentation_output/ folder structure
# - Each processing folder must contain:
#   * average_frequency.txt (with "Average Frequency: X.X Hz" format)
#   * alignment_results_2/ folder with temporally corrected .npy tracking data files
#
# Output:
# - Creates *_converted.npy files with scaled coordinates and timing
# - X,Y coordinates converted to micrometers
# - Time points converted to seconds using acquisition frequency
# - Output saved to alignment_converted_results_2/ to distinguish from original conversions
#
# Resizing takes into account the original image size (2560x1920 pixels) and the converted size
# (2048x2048 pixels) used for the blob detection and alignment processes
# It also takes into account the blob size (in microns) of the device utilized (camera + 40x objective)
#
# File Structure Expected:
# root_directory/
# ├── segmentation_output/                    # Main processing output folder
# │   ├── subfolder_1/                       # Mirrors data folder structure
# │   │   └── shortened_X/                   # Time-series experiment folders
# │   │       └── subsubfolder_1_changed/   # Individual recording sessions (with "_changed" suffix)
# │   │           ├── npy_tracks/            # Track data files (not used by this script)
# │   │           │   ├── track_001.npy
# │   │           │   └── ...
# │   │           ├── blobs_subsubfolder_1.npy # Blob detection results (not used)
# │   │           ├── *_mhi.png              # MHI background image
# │   │           ├── alignment_summary_corrected.txt  # Summary of corrected alignment results
# │   │           ├── alignment_results_2/   # INPUT: Contains temporally corrected .npy files to process
# │   │           │   └── aligned_blobs_*.npy # Temporally corrected tracking data files
# │   │           ├── alignment_converted_results_2/ # OUTPUT: Created by this script
# │   │           │   └── *_converted.npy    # Converted tracking data (micrometers & seconds)
# │   │           ├── mhi_overlay_corrected.png # Final overlay output
# │   │           └── average_frequency.txt  # INPUT: Contains acquisition frequency data
# │   └── subfolder_2/
# │       └── shortened_Y/
# │           └── subsubfolder_2_changed/
# │               ├── npy_tracks/
# │               ├── blobs_subsubfolder_2.npy
# │               ├── *_mhi.png
# │               ├── alignment_summary_corrected.txt
# │               ├── alignment_results_2/   # INPUT: Temporally corrected source .npy files
# │               ├── alignment_converted_results_2/ # OUTPUT: Converted .npy files
# │               ├── mhi_overlay_corrected.png
# │               └── average_frequency.txt
# ├── subfolder_1/                           # Original data folders (XML source)
# │   ├── subsubfolder_1/                    # Direct XML recording sessions
# │   │   ├── *.xml                          # XML metadata files
# │   │   └── other_files/                   # Other processing outputs
# │   ├── subsubfolder_2/
# │   │   ├── *.xml
# │   │   └── other_files/
# │   └── shortened_X/                       # Time-series experiment folders
# │       └── subsubfolder_1/                # Individual recording sessions
# │           ├── raw/                       # Original images
# │           │   ├── image_00000.tif       # Timepoint 0
# │           │   ├── image_00001.tif       # Timepoint 1
# │           │   └── ...
# │           ├── validate/                  # Validation data
# │           │   └── MHI.npy               # Motion History Image array
# │           └── other_folders/             # Other processing outputs
# └── subfolder_2/                           # Additional data folders
#     ├── subsubfolder_1/
#     │   ├── *.xml
#     │   └── other_files/
#     ├── subsubfolder_2/
#     │   ├── *.xml
#     │   └── other_files/
#     └── shortened_Y/
#         └── subsubfolder_X/
#             ├── raw/
#             ├── validate/
#             └── other_folders/
#
# Script developed with the help of AI (Claude.AI)
# Last updated: 23/09/2025
#
# Authors: Max Riekeles and Berke Santos
# Contact: riekeles@tu-berlin.de
# ==============================================================================

import numpy as np
from pathlib import Path


# Function to extract the average frequency from the file
def get_average_frequency(file_path):
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith("Average Frequency:"):
                    frequency = float(line.split(":")[1].strip().split()[0])
                    return frequency
    except FileNotFoundError:
        print(f"Average frequency file not found: {file_path}")
    return None


def process_npy_files_corrected(root_directory, pixel_size_um, processed_resolution, camera_resolution):
    """
    Process temporally corrected .npy files in the segmentation_output folder structure

    Parameters:
    root_directory: Path to the root directory
    pixel_size_um: Physical size per pixel in micrometers (from camera sensor)
    processed_resolution: tuple (width, height) of processed image resolution (tracking data)
    camera_resolution: tuple (width, height) of original camera image resolution

    Returns:
    dict: Processing summary with success/failure statistics
    """

    # Initialize processing summary
    summary = {
        'total_folders_processed': 0,
        'total_files_processed': 0,
        'total_files_skipped': 0,
        'successful_conversions': [],
        'failed_conversions': [],
        'skipped_files': [],
        'missing_frequency_files': [],
        'empty_files': [],
        'folders_without_alignment_results_2': [],
        'folders_without_npy_files': []
    }

    root_path = Path(root_directory)
    segmentation_output_path = root_path / "segmentation_output"

    if not segmentation_output_path.exists():
        print(f"Segmentation output directory not found: {segmentation_output_path}")
        summary['error'] = f"Root segmentation_output directory not found: {segmentation_output_path}"
        return summary

    print("Processing temporally corrected alignment results from alignment_results_2/ folders")
    print("=" * 80)

    # Loop through all subfolders within the segmentation_output folder
    for subfolder in segmentation_output_path.iterdir():
        if not subfolder.is_dir():
            continue

        print(f"Processing subfolder: {subfolder.name}")

        # Look for shortened_* folders within each subfolder
        for shortened_folder in subfolder.iterdir():
            if not (shortened_folder.is_dir() and shortened_folder.name.startswith("shortened_")):
                continue

            print(f"  Processing shortened folder: {shortened_folder.name}")

            # Look for subsubfolder_*_changed folders
            for changed_folder in shortened_folder.iterdir():
                if not (changed_folder.is_dir() and changed_folder.name.endswith("_changed")):
                    continue

                print(f"    Processing changed folder: {changed_folder.name}")

                # Read the average frequency from the 'average_frequency.txt' file
                average_frequency_file = changed_folder / 'average_frequency.txt'

                # Get the average frequency
                average_frequency = get_average_frequency(average_frequency_file)
                if average_frequency is None:
                    print(f"    Could not find the 'Average Frequency' in {average_frequency_file}. Skipping folder.")
                    summary['missing_frequency_files'].append(str(average_frequency_file))
                    continue

                # Look for alignment_results_2 folder (UPDATED)
                alignment_results_path = changed_folder / "alignment_results_2"
                if not alignment_results_path.exists():
                    print(f"    No alignment_results_2 folder found in {changed_folder.name}. Skipping.")
                    print(f"    (Make sure to run the temporal correction alignment script first)")
                    summary['folders_without_alignment_results_2'].append(str(changed_folder))
                    continue

                # Create output directory for converted results (UPDATED name)
                output_dir = changed_folder / "alignment_converted_results_2"
                output_dir.mkdir(exist_ok=True)
                print(f"    Output directory: {output_dir.name}")

                # Get a list of all .npy files in the alignment_results_2 folder
                npy_files = list(alignment_results_path.glob("*.npy"))

                if not npy_files:
                    print(f"    No .npy files found in {alignment_results_path}. Skipping.")
                    summary['folders_without_npy_files'].append(str(alignment_results_path))
                    continue

                print(f"    Found {len(npy_files)} temporally corrected .npy files to process")
                summary['total_folders_processed'] += 1

                # Pre-calculate scaling factors for efficiency
                # Convert from processed image coordinates to real-world micrometers
                x_scale = camera_resolution[0] * pixel_size_um / processed_resolution[0]
                y_scale = camera_resolution[1] * pixel_size_um / processed_resolution[1]
                time_scale = 1 / average_frequency

                # Process each npy file
                for npy_file in npy_files:
                    print(f"      Processing corrected file: {npy_file.name}")

                    try:
                        # Load data with memory mapping for large files
                        data = np.load(npy_file, mmap_mode='r')

                        if data.size == 0:
                            print(f"      Empty data in {npy_file.name}. Skipping.")
                            summary['empty_files'].append(str(npy_file))
                            summary['total_files_skipped'] += 1
                            continue

                        # Check if output file already exists in the new directory
                        converted_file_path = output_dir / f"{npy_file.stem}_converted.npy"
                        if converted_file_path.exists():
                            print(f"      Converted file already exists: {converted_file_path.name}. Skipping.")
                            summary['skipped_files'].append({
                                'input': str(npy_file),
                                'output': str(converted_file_path),
                                'reason': 'File already exists'
                            })
                            summary['total_files_skipped'] += 1
                            continue

                        # Create output array with only x, y, t columns for memory efficiency
                        converted_data = np.empty((data.shape[0], 3), dtype=np.float64)

                        # Apply scaling to only the first 3 columns
                        # Note: timepoints in data are already corrected using MHI values
                        converted_data[:, 0] = data[:, 0] * x_scale  # Scale x coordinates
                        converted_data[:, 1] = data[:, 1] * y_scale  # Scale y coordinates
                        converted_data[:, 2] = data[:, 2] * time_scale  # Scale corrected time points

                        # Save the converted data
                        np.save(converted_file_path, converted_data)
                        print(f"      Converted corrected data saved to {converted_file_path.name}")

                        # Record successful conversion
                        summary['successful_conversions'].append({
                            'input': str(npy_file),
                            'output': str(converted_file_path),
                            'data_points': data.shape[0],
                            'frequency_used': average_frequency,
                            'temporally_corrected': True
                        })
                        summary['total_files_processed'] += 1

                        # Clear memory explicitly for large datasets
                        del converted_data
                        del data

                    except Exception as e:
                        print(f"      Error processing {npy_file.name}: {e}")
                        summary['failed_conversions'].append({
                            'input': str(npy_file),
                            'error': str(e)
                        })

    return summary


def print_processing_summary_corrected(summary):
    """
    Print a comprehensive summary of the processing results for corrected data

    Parameters:
    summary: dict containing processing statistics and results
    """

    print("\n" + "=" * 80)
    print("TEMPORALLY CORRECTED DATA PROCESSING SUMMARY")
    print("=" * 80)

    # Check if there was a critical error
    if 'error' in summary:
        print(f"CRITICAL ERROR: {summary['error']}")
        return

    # Overall statistics
    total_attempted = summary['total_files_processed'] + summary['total_files_skipped'] + len(
        summary['failed_conversions'])
    success_rate = (summary['total_files_processed'] / total_attempted * 100) if total_attempted > 0 else 0

    print(f"OVERALL STATISTICS:")
    print(f"   - Folders processed: {summary['total_folders_processed']}")
    print(f"   - Corrected files successfully converted: {summary['total_files_processed']}")
    print(f"   - Files skipped: {summary['total_files_skipped']}")
    print(f"   - Files failed: {len(summary['failed_conversions'])}")
    print(f"   - Success rate: {success_rate:.1f}%")

    # Successful conversions
    if summary['successful_conversions']:
        print(f"\nSUCCESSFUL CONVERSIONS ({len(summary['successful_conversions'])} files):")
        total_data_points = 0
        for conversion in summary['successful_conversions']:
            print(f"   - {Path(conversion['input']).name} -> {Path(conversion['output']).name}")
            print(
                f"     Data points: {conversion['data_points']}, Frequency: {conversion['frequency_used']:.2f} Hz (Temporally Corrected)")
            total_data_points += conversion['data_points']
        print(f"   Total corrected data points processed: {total_data_points:,}")

    # Failed conversions
    if summary['failed_conversions']:
        print(f"\nFAILED CONVERSIONS ({len(summary['failed_conversions'])} files):")
        for failure in summary['failed_conversions']:
            print(f"   - {Path(failure['input']).name}: {failure['error']}")

    # Skipped files
    if summary['skipped_files']:
        print(f"\nSKIPPED FILES ({len(summary['skipped_files'])} files):")
        for skipped in summary['skipped_files']:
            print(f"   - {Path(skipped['input']).name}: {skipped['reason']}")

    # Empty files
    if summary['empty_files']:
        print(f"\nEMPTY FILES ({len(summary['empty_files'])} files):")
        for empty_file in summary['empty_files']:
            print(f"   - {Path(empty_file).name}")

    # Missing frequency files
    if summary['missing_frequency_files']:
        print(f"\nMISSING FREQUENCY FILES ({len(summary['missing_frequency_files'])} folders):")
        for missing in summary['missing_frequency_files']:
            print(f"   - {missing}")

    # Folders without alignment_results_2
    if summary['folders_without_alignment_results_2']:
        print(f"\nFOLDERS WITHOUT ALIGNMENT_RESULTS_2 ({len(summary['folders_without_alignment_results_2'])} folders):")
        print("   These folders need temporal correction alignment processing first:")
        for folder in summary['folders_without_alignment_results_2']:
            print(f"   - {Path(folder).name}")

    # Folders without npy files
    if summary['folders_without_npy_files']:
        print(f"\nFOLDERS WITHOUT NPY FILES ({len(summary['folders_without_npy_files'])} folders):")
        for folder in summary['folders_without_npy_files']:
            print(f"   - {folder}")

    # Final status
    print(f"\n{'=' * 80}")
    if summary['total_files_processed'] > 0 and len(summary['failed_conversions']) == 0:
        print("TEMPORALLY CORRECTED DATA PROCESSING COMPLETED SUCCESSFULLY!")
        print("Output files contain blob data with accurate MHI-corrected timing")
    elif summary['total_files_processed'] > 0:
        print("TEMPORALLY CORRECTED DATA PROCESSING COMPLETED WITH SOME ISSUES")
    else:
        print("NO CORRECTED FILES WERE PROCESSED")
        print("Make sure to run the temporal correction alignment script first")
    print("=" * 80)


# Hard-coded parameters - modify these as needed
if __name__ == "__main__":
    # Directory configuration
    ROOT_DIRECTORY = "/media/general-max-riekeles/MMT_3/ME/Analysis_20_09"  # Update this path

    # Image conversion parameters
    PIXEL_SIZE_UM = 0.055  # Physical size per pixel in micrometers (camera sensor)
    PROCESSED_RESOLUTION = (2048, 2048)  # (width, height) of processed images (tracking data)
    CAMERA_RESOLUTION = (2560, 1920)  # (width, height) of original camera images

    print("Starting temporally corrected data processing...")
    print(f"Root directory: {ROOT_DIRECTORY}")
    print(f"Pixel size: {PIXEL_SIZE_UM} μm")
    print(f"Processed resolution: {PROCESSED_RESOLUTION}")
    print(f"Camera resolution: {CAMERA_RESOLUTION}")
    print("Processing alignment_results_2/ folders (temporally corrected data)")
    print("-" * 50)

    # Process files and get summary
    processing_summary = process_npy_files_corrected(ROOT_DIRECTORY, PIXEL_SIZE_UM, PROCESSED_RESOLUTION,
                                                     CAMERA_RESOLUTION)

    # Print comprehensive summary
    print_processing_summary_corrected(processing_summary)
