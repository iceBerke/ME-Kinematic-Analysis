# DESCRIPTION:
# This script calculates the acquisition frequency of time-series data by analyzing XML metadata files.
# It matches folders between segmentation output directories and corresponding data directories,
# extracts timing information from XML files, and calculates the average acquisition frequency
# based on the first and last timestamps.
#
# The script processes the following directory structure:
# root_directory/
# ├── segmentation_output/                    # Output folder (input/output for this script)
# │   ├── subfolder_1/                       # Mirrors data folder structure
# │   │   └── shortened_X/                   # Matches shortened folders in data
# │   │       └── subsubfolder_1_changed/   # Matches data subsubfolders (with "_changed" suffix)
# │   │           ├── npy_tracks/            # Track data files (not used by this script)
# │   │           │   ├── track_001.npy      # Individual track segments
# │   │           │   ├── track_002.npy
# │   │           │   └── ...
# │   │           ├── blobs_subsubfolder_1.npy # Blob detection results (not used by this script)
# │   │           ├── *_mhi.png              # MHI background image (INPUT - must exist)
# │   │           ├── alignment_summary.txt  # Summary of alignment results (ignored)
# │   │           ├── alignment_results/     # Alignment output (INPUT)
# │   │           │   └── aligned_blobs_*.npy # Processed blob files used for visualization
# │   │           ├── mhi_overlay.png        # Final overlay output (not used by this script)
# │   │           └── average_frequency.txt  # OUTPUT: Created by this script
# │   └── subfolder_2/
# │       └── shortened_Y/
# │           └── subsubfolder_2_changed/   # Matches data subsubfolders (with "_changed" suffix)
# │               ├── npy_tracks/
# │               ├── blobs_subsubfolder_2.npy
# │               ├── *_mhi.png              # MHI background image (INPUT)
# │               ├── alignment_summary.txt
# │               ├── alignment_results/     # INPUT: Contains .npy files to visualize
# │               │   └── aligned_blobs_*.npy
# │               ├── mhi_overlay.png        # Final overlay output (not used)
# │               └── average_frequency.txt  # OUTPUT: Created by this script
# ├── subfolder_1/                           # Data folders (XML source for this script)
# │   ├── subsubfolder_1/                    # Individual recording sessions - contains XML files directly
# │   │   ├── *.xml                          # XML metadata files (INPUT - used by this script)
# │   │   └── other_files/                   # Other processing outputs (ignored)
# │   ├── subsubfolder_2/                    # Another recording session
# │   │   ├── *.xml                          # XML metadata files (INPUT - used by this script)
# │   │   └── other_files/                   # Other processing outputs (ignored)
# │   └── shortened_X/                       # Time-series experiment folders (contains raw/validate)
# │       └── subsubfolder_1/                # Individual recording sessions
# │           ├── raw/                       # Original images (not used by this script)
# │           │   ├── image_00000.tif       # Timepoint 0
# │           │   ├── image_00001.tif       # Timepoint 1
# │           │   └── ...
# │           ├── validate/                  # Validation data (not used by this script)
# │           │   └── MHI.npy               # Motion History Image array
# │           └── other_folders/             # Other processing outputs (ignored)
# └── subfolder_2/                           # Data folders (XML source for this script)
#     ├── subsubfolder_1/                    # Individual recording sessions - contains XML files directly
#     │   ├── *.xml                          # XML metadata files (INPUT - used by this script)
#     │   └── other_files/                   # Other processing outputs (ignored)
#     ├── subsubfolder_2/                    # Another recording session
#     │   ├── *.xml                          # XML metadata files (INPUT - used by this script)
#     │   └── other_files/                   # Other processing outputs (ignored)
#     └── shortened_Y/                       # Time-series experiment folders (contains raw/validate)
#         └── subsubfolder_X/                # Individual recording sessions
#             ├── raw/                       # Original images (not used by this script)
#             ├── validate/                  # Validation data (not used by this script)
#             └── other_folders/             # Other processing outputs (ignored)
#
# WORKFLOW:
# 1. Scans segmentation_output for all subsubfolders (which end with "_changed")
# 2. For each subsubfolder, removes "_changed" suffix to find corresponding data folder
# 3. Looks for XML files in the matching data folder (root/subfolder_X/subsubfolder_Y/)
# 4. Extracts XML files from the data folder and sorts them by 'b0t' number
# 5. Calculates acquisition frequency based on first and last XML timestamps
# 6. Saves frequency results to average_frequency.txt in the segmentation output folder

# Script developed with the help of AI (Claude.AI)
# Last updated: 23/09/2025

# The authors of the code are Max Riekeles and Berke Santos. Contact: riekeles@tu-berlin.de

from pathlib import Path
import xml.etree.ElementTree as ET
from datetime import datetime
from dateutil import parser
import re

# Results tracking
results = {
    'successful': [],
    'failed': [],
    'no_xml_files': [],
    'no_matching_folder': [],
    'extraction_errors': []
}


def extract_acquisition_time(xml_file):
    """Extracts the AcquisitionTime from the XML metadata file."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        time_element = root.find('.//AcquisitionTime')
        if time_element is not None and time_element.text:
            return parser.parse(time_element.text)
        return None
    except Exception as e:
        results['extraction_errors'].append(f"Error parsing {xml_file.name}: {str(e)}")
        return None
    finally:
        # Clear the tree from memory
        if 'tree' in locals():
            del tree


def extract_file_number(xml_filename):
    """Extracts the file number from the filename using regex to find the 'b0t' pattern."""
    match = re.search(r'b0t(\d+)', xml_filename.name)
    if match:
        return int(match.group(1))
    else:
        results['extraction_errors'].append(f"Could not extract file number from: {xml_filename.name}")
        return None


def get_xml_time_range(xml_files):
    """Get time range and file numbers from sorted XML files. Returns (first_time, last_time, first_num, last_num, total_files)."""
    if not xml_files:
        return None

    # Sort files based on the 'b0t' number - memory efficient sorting
    xml_files.sort(key=lambda f: extract_file_number(f) or 0)

    # Get first and last files
    first_xml = xml_files[0]
    last_xml = xml_files[-1]

    # Extract times
    first_time = extract_acquisition_time(first_xml)
    last_time = extract_acquisition_time(last_xml)

    if not first_time or not last_time:
        return None

    # Extract file numbers
    first_number = extract_file_number(first_xml)
    last_number = extract_file_number(last_xml)

    if first_number is None or last_number is None:
        return None

    total_files = last_number - first_number + 1
    return first_time, last_time, first_number, last_number, total_files


def process_matched_folders(segmentation_path, data_path):
    """Processes matched folders and calculates frequency. Returns True if successful."""

    try:
        # Get XML files list (memory efficient - generator converted to list only when needed)
        xml_files = [f for f in data_path.glob("*.xml") if f.is_file()]

        if not xml_files:
            results['no_xml_files'].append(str(data_path))
            return False

        # Get time range and file info
        time_info = get_xml_time_range(xml_files)
        if not time_info:
            results['failed'].append(f"{data_path.name}: Could not extract time information")
            return False

        first_time, last_time, first_number, last_number, total_files = time_info

        # Calculate time difference in seconds
        time_diff_seconds = (last_time - first_time).total_seconds()

        if time_diff_seconds == 0:
            results['failed'].append(f"{data_path.name}: Zero time difference")
            return False

        # Calculate frequency
        frequency = total_files / time_diff_seconds

        # Save results to file
        result_file = segmentation_path / "average_frequency.txt"
        with open(result_file, 'w') as f:
            f.write(f"Average Frequency: {frequency} Hz\n")
            f.write(f"Total Files: {total_files}\n")
            f.write(f"Time Difference: {time_diff_seconds} seconds\n")
            f.write(f"First File Number: {first_number}\n")
            f.write(f"Last File Number: {last_number}\n")
            f.write(f"First Time: {first_time}\n")
            f.write(f"Last Time: {last_time}\n")

        results['successful'].append({
            'segmentation_path': str(segmentation_path),
            'data_path': str(data_path),
            'frequency': frequency,
            'total_files': total_files,
            'time_diff': time_diff_seconds
        })

        return True

    except Exception as e:
        results['failed'].append(f"{data_path.name}: Unexpected error - {str(e)}")
        return False


def find_matching_paths():
    """Find matching paths between segmentation_output and data folders."""
    segmentation_output = root_directory / "segmentation_output"

    if not segmentation_output.exists():
        results['failed'].append(f"Segmentation output directory not found: {segmentation_output}")
        return

    # Process folders efficiently without storing all paths in memory
    for subfolder in segmentation_output.iterdir():
        if not subfolder.is_dir():
            continue

        for shortened_folder in subfolder.iterdir():
            if not shortened_folder.is_dir():
                continue

            for subsubfolder in shortened_folder.iterdir():
                if not subsubfolder.is_dir():
                    continue

                # Extract the path components to match with data structure
                subsubfolder_name = subsubfolder.name
                subfolder_name = subfolder.name

                # Remove "_changed" suffix from subsubfolder name to match data folder
                if subsubfolder_name.endswith("_changed"):
                    data_subsubfolder_name = subsubfolder_name.replace("_changed", "")
                else:
                    data_subsubfolder_name = subsubfolder_name

                # Construct the corresponding data path: root/subfolder_X/subsubfolder_Y
                data_path = root_directory / subfolder_name / data_subsubfolder_name

                if data_path.exists() and data_path.is_dir():
                    # Process the matching folders
                    process_matched_folders(subsubfolder, data_path)
                else:
                    results['no_matching_folder'].append(
                        f"Segmentation: {subsubfolder} -> Expected data at: {data_path}")


def print_results_summary():
    """Print a comprehensive summary of all operations."""
    print("\n" + "=" * 80)
    print("PROCESSING RESULTS SUMMARY")
    print("=" * 80)

    # Successful operations
    if results['successful']:
        print(f"\nSUCCESSFUL OPERATIONS ({len(results['successful'])}):")
        print("-" * 50)
        for i, success in enumerate(results['successful'], 1):
            print(f"{i}. Frequency: {success['frequency']:.4f} Hz")
            print(f"   Files: {success['total_files']}, Duration: {success['time_diff']:.2f}s")
            print(f"   Data: {success['data_path']}")
            print(f"   Output: {success['segmentation_path']}/average_frequency.txt")
            print()
    else:
        print(f"\nNO SUCCESSFUL OPERATIONS")

    # Failed operations
    if results['failed']:
        print(f"\nFAILED OPERATIONS ({len(results['failed'])}):")
        print("-" * 50)
        for i, failure in enumerate(results['failed'], 1):
            print(f"{i}. {failure}")

    # No XML files found
    if results['no_xml_files']:
        print(f"\nFOLDERS WITH NO XML FILES ({len(results['no_xml_files'])}):")
        print("-" * 50)
        for i, folder in enumerate(results['no_xml_files'], 1):
            print(f"{i}. {folder}")

    # No matching folders
    if results['no_matching_folder']:
        print(f"\nNO MATCHING DATA FOLDERS ({len(results['no_matching_folder'])}):")
        print("-" * 50)
        for i, mismatch in enumerate(results['no_matching_folder'], 1):
            print(f"{i}. {mismatch}")

    # Extraction errors
    if results['extraction_errors']:
        print(f"\nEXTRACTION ERRORS ({len(results['extraction_errors'])}):")
        print("-" * 50)
        for i, error in enumerate(results['extraction_errors'], 1):
            print(f"{i}. {error}")

    # Overall statistics
    total_processed = len(results['successful']) + len(results['failed']) + len(results['no_xml_files']) + len(
        results['no_matching_folder'])
    success_rate = (len(results['successful']) / total_processed * 100) if total_processed > 0 else 0

    print(f"\n" + "=" * 80)
    print(f"OVERALL STATISTICS")
    print(f"Total folders processed: {total_processed}")
    print(f"Success rate: {success_rate:.1f}%")
    print("=" * 80)


def main():
    """Main function to run the matching and processing."""
    if not root_directory.exists():
        print(f"ERROR: Root directory does not exist: {root_directory}")
        print("Please update the 'root_directory' variable with the correct path.")
        return

    print(f"Starting frequency calculation for: {root_directory}")
    print("Processing...")

    # Run the main processing
    find_matching_paths()

    # Print comprehensive results
    print_results_summary()


if __name__ == "__main__":
    # Set the root directory path here
    root_directory = Path("/media/general-max-riekeles/MMT_3/ME/Analysis_20_09")  # UPDATE THIS PATH
    main()
