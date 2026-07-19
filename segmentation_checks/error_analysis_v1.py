# Script receives a root folder with the following structure: root>shortened directories>recording folders>segmented png files + original MHI png file
# (this is the output from the new colour segmentation code - v4)
# The script will ignore the MHI png files
# It outputs three reports: unconnected paths report, global summary with the number of segmented tracks per folder type
# (e.g., control 0h folders), and empty outputs report (segmented outputs that are empty)

# Script developed with the help of AI (Claude.AI)
# Last update: 14/09/2025

import os
import re
from pathlib import Path
import cv2
import numpy as np
from PIL import Image


def scan_folder_structure(root_folder):
    unconnected_paths = []
    folder_stats = []
    empty_files = []  # Added for empty file tracking

    # Convert to Path object for easier handling
    root_path = Path(root_folder)

    if not root_path.exists():
        print(f"Error: Root folder '{root_folder}' does not exist.")
        return

    # Find all folders that start with "shortened_"
    shortened_folders = [f for f in root_path.iterdir()
                         if f.is_dir() and f.name.startswith("shortened_")]

    if not shortened_folders:
        print("No folders starting with 'shortened_' found.")
        return

    print(f"Found {len(shortened_folders)} shortened folders:")

    # Process each shortened folder
    for shortened_folder in shortened_folders:
        print(f"\nProcessing: {shortened_folder.name}")

        # Find all subfolders in the shortened folder
        subfolders = [f for f in shortened_folder.iterdir() if f.is_dir()]

        for subfolder in subfolders:
            print(f"  Checking subfolder: {subfolder.name}")

            # Find all t(number).png files
            png_files = []
            for file in subfolder.iterdir():
                if file.is_file() and file.name.endswith('.png'):
                    # Check if filename matches t(number).png pattern
                    match = re.match(r't(\d+)\.png', file.name)
                    if match:
                        png_files.append((file.name, file))

            # Record folder statistics
            folder_stats.append({
                'folder': shortened_folder.name,
                'subfolder': subfolder.name,
                'total_files': len(png_files)
            })

            if png_files:
                print(f"    Found {len(png_files)} t(number).png files")

                # Check each PNG file for unconnected paths and empty files
                unconnected_count = 0
                empty_count = 0  # Added for empty file counting
                for filename, filepath in png_files:
                    try:
                        # Check for empty files first
                        if is_empty_file(filepath):
                            empty_files.append({
                                'folder': shortened_folder.name,
                                'subfolder': subfolder.name,
                                'file': filename,
                                'issue': 'File contains no white pixels (completely black)',
                                'type': 'empty_file'
                            })
                            empty_count += 1
                            print(f"      E {filename} - EMPTY FILE (no white pixels)")
                        elif has_unconnected_paths(filepath):
                            unconnected_paths.append({
                                'folder': shortened_folder.name,
                                'subfolder': subfolder.name,
                                'file': filename,
                                'issue': 'Contains multiple disconnected white line segments',
                                'type': 'unconnected_paths'
                            })
                            unconnected_count += 1
                            print(f"      X {filename} - UNCONNECTED PATHS DETECTED")
                        else:
                            print(f"      - {filename} - Connected path")
                    except Exception as e:
                        print(f"      ! Error processing {filename}: {str(e)}")

                # Update folder stats with both counts
                folder_stats[-1]['unconnected_files'] = unconnected_count
                folder_stats[-1]['empty_files'] = empty_count  # Added empty files count
            else:
                print(f"    No t(number).png files found")
                folder_stats[-1]['unconnected_files'] = 0
                folder_stats[-1]['empty_files'] = 0  # Added empty files count

    # Write results to txt files
    output_file = root_path / "unconnected_paths.txt"
    summary_file = root_path / "summary.txt"
    empty_file = root_path / "empty_outputs.txt"  # Added empty outputs file

    write_results_to_file(output_file, unconnected_paths, folder_stats)
    write_summary_file(summary_file, folder_stats)
    write_empty_files_report(empty_file, empty_files)  # Added empty files report

    if unconnected_paths:
        print(f"\nFound {len(unconnected_paths)} files with unconnected paths!")
        print(f"Results written to: {output_file}")
    else:
        print(f"\nNo unconnected paths found in any files.")
        print(f"Report written to: {output_file}")

    # Added empty files reporting
    if empty_files:
        print(f"Found {len(empty_files)} empty files!")
        print(f"Empty files report written to: {empty_file}")
    else:
        print(f"No empty files found.")
        print(f"Empty files report written to: {empty_file}")

    print(f"Summary written to: {summary_file}")


def is_empty_file(image_path):
    """
    Check if a PNG file is empty (contains no white pixels - completely black).
    Returns True if the file is empty, False otherwise.
    """
    try:
        # Load the image
        image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)

        if image is None:
            raise ValueError(f"Could not load image: {image_path}")

        # Check if there are any white pixels (pixel values > 127)
        white_pixels = np.where(image > 127)

        # If no white pixels found, file is empty
        return len(white_pixels[0]) == 0

    except Exception as e:
        print(f"Error checking if image is empty {image_path}: {str(e)}")
        return False


def has_unconnected_paths(image_path):
    try:
        # Load the image
        image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)

        if image is None:
            raise ValueError(f"Could not load image: {image_path}")

        # Threshold the image to create binary image (white lines on black background)
        # Assuming white lines have pixel values > 127
        _, binary = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY)

        # Find all white pixels (potential path pixels)
        white_pixels = np.where(binary == 255)

        if len(white_pixels[0]) == 0:
            # No white pixels found, no paths at all
            return False

        # Use connected components to find separate line segments
        num_labels, labels = cv2.connectedComponents(binary)

        # num_labels includes the background (label 0), so subtract 1
        num_white_components = num_labels - 1

        # If there's more than 1 connected component of white pixels, paths are unconnected
        if num_white_components > 1:
            # Additional check: make sure the components are significant (not just noise)
            component_sizes = []
            for i in range(1, num_labels):  # Skip background (label 0)
                component_size = np.sum(labels == i)
                component_sizes.append(component_size)

            # Filter out very small components (likely noise) - adjust threshold as needed
            significant_components = [size for size in component_sizes if size > 10]

            return len(significant_components) > 1

        return False

    except Exception as e:
        print(f"Error analyzing image {image_path}: {str(e)}")
        return False


def write_empty_files_report(empty_file, empty_files):
    """Write empty files report to a text file."""
    with open(empty_file, 'w', encoding='utf-8') as f:
        f.write("EMPTY FILES REPORT\n")
        f.write("=" * 30 + "\n")
        f.write("Files with no white pixels (completely black backgrounds)\n\n")

        if not empty_files:
            f.write("No empty files found.\n")
            f.write("All t(number).png files contain some white pixels.\n")
            return

        f.write(f"Found {len(empty_files)} empty files:\n\n")

        # Group by folder for better organization
        current_folder = ""
        for issue in empty_files:
            if issue['folder'] != current_folder:
                current_folder = issue['folder']
                f.write(f"Folder: {current_folder}\n")
                f.write("-" * 30 + "\n")

            f.write(f"  Subfolder: {issue['subfolder']}\n")
            f.write(f"  File: {issue['file']}\n")
            f.write(f"  Issue: {issue['issue']}\n")
            f.write("\n")


def write_summary_file(summary_file, folder_stats):
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("SUMMARY STATISTICS\n")
        f.write("=" * 30 + "\n\n")

        if not folder_stats:
            f.write("No folders analyzed.\n")
            return

        # Calculate summary statistics
        total_files = sum(stat['total_files'] for stat in folder_stats)
        total_unconnected = sum(stat['unconnected_files'] for stat in folder_stats)
        total_empty = sum(stat.get('empty_files', 0) for stat in folder_stats)  # Added empty files count

        f.write(f"Total shortened folders: {len(set(stat['folder'] for stat in folder_stats))}\n")
        f.write(f"Total subfolders: {len(folder_stats)}\n")
        f.write(f"Total t(number).png files: {total_files}\n")
        f.write(f"Files with unconnected paths: {total_unconnected}\n")
        f.write(f"Empty files (no white pixels): {total_empty}\n")  # Added empty files line
        if total_files > 0:
            unconnected_percentage = (total_unconnected / total_files) * 100
            empty_percentage = (total_empty / total_files) * 100  # Added empty percentage
            f.write(f"Unconnected paths percentage: {unconnected_percentage:.2f}%\n")
            f.write(f"Empty files percentage: {empty_percentage:.2f}%\n")  # Added empty percentage line

        f.write("\nPER FOLDER BREAKDOWN:\n")
        f.write("-" * 25 + "\n")

        # Group by shortened folder
        folders_dict = {}
        for stat in folder_stats:
            folder_name = stat['folder']
            if folder_name not in folders_dict:
                folders_dict[folder_name] = []
            folders_dict[folder_name].append(stat)

        for folder_name, subfolders in folders_dict.items():
            folder_total_files = sum(sub['total_files'] for sub in subfolders)
            folder_total_unconnected = sum(sub['unconnected_files'] for sub in subfolders)
            folder_total_empty = sum(sub.get('empty_files', 0) for sub in subfolders)  # Added empty files count

            f.write(f"\n{folder_name}:\n")
            f.write(f"  Subfolders: {len(subfolders)}\n")
            f.write(f"  Total files: {folder_total_files}\n")
            f.write(f"  Problem files: {folder_total_unconnected}\n")
            f.write(f"  Empty files: {folder_total_empty}\n")  # Added empty files line
            if folder_total_files > 0:
                folder_unconnected_percentage = (folder_total_unconnected / folder_total_files) * 100
                folder_empty_percentage = (folder_total_empty / folder_total_files) * 100  # Added empty percentage
                f.write(f"  Unconnected rate: {folder_unconnected_percentage:.2f}%\n")
                f.write(f"  Empty rate: {folder_empty_percentage:.2f}%\n")  # Added empty rate line

        # Add subfolder pattern analysis
        f.write("\nSUBFOLDER PATTERN ANALYSIS:\n")
        f.write("-" * 30 + "\n")

        # Group subfolders by their name pattern (first 3 underscore-separated parts)
        pattern_groups = {}
        for stat in folder_stats:
            subfolder_name = stat['subfolder']
            # Extract first 3 parts separated by underscores
            parts = subfolder_name.split('_')
            if len(parts) >= 3:
                pattern = '_'.join(parts[:3])
            else:
                pattern = subfolder_name  # Use full name if less than 3 parts

            if pattern not in pattern_groups:
                pattern_groups[pattern] = []
            pattern_groups[pattern].append(stat)

        for pattern, pattern_stats in pattern_groups.items():
            pattern_total_files = sum(sub['total_files'] for sub in pattern_stats)
            pattern_total_unconnected = sum(sub['unconnected_files'] for sub in pattern_stats)
            pattern_total_empty = sum(sub.get('empty_files', 0) for sub in pattern_stats)

            f.write(f"\n{pattern} folders:\n")
            f.write(f"  Count: {len(pattern_stats)} subfolders\n")
            f.write(f"  Total files: {pattern_total_files}\n")
            f.write(f"  Problem files: {pattern_total_unconnected}\n")
            f.write(f"  Empty files: {pattern_total_empty}\n")
            if pattern_total_files > 0:
                pattern_unconnected_percentage = (pattern_total_unconnected / pattern_total_files) * 100
                pattern_empty_percentage = (pattern_total_empty / pattern_total_files) * 100
                f.write(f"  Unconnected rate: {pattern_unconnected_percentage:.2f}%\n")
                f.write(f"  Empty rate: {pattern_empty_percentage:.2f}%\n")

            # List individual subfolders in this pattern
            f.write(f"  Subfolders:\n")
            for sub in pattern_stats:
                f.write(f"    {sub['subfolder']}: {sub['total_files']} files")
                if sub['unconnected_files'] > 0:
                    f.write(f" ({sub['unconnected_files']} unconnected)")
                if sub.get('empty_files', 0) > 0:
                    f.write(f" ({sub.get('empty_files', 0)} empty)")
                f.write(f"\n")


def write_results_to_file(output_file, unconnected_paths, folder_stats):
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Unconnected Paths Detection Report\n")
        f.write("=" * 50 + "\n")
        f.write(f"Analysis completed on: {Path.cwd()}\n\n")

        # Write folder statistics first
        f.write("FOLDER STATISTICS\n")
        f.write("-" * 30 + "\n")
        for stat in folder_stats:
            f.write(f"Folder: {stat['folder']}\n")
            f.write(f"  Subfolder: {stat['subfolder']}\n")
            f.write(f"  Total t(number).png files: {stat['total_files']}\n")
            f.write(f"  Files with unconnected paths: {stat['unconnected_files']}\n")
            f.write(f"  Empty files: {stat.get('empty_files', 0)}\n")  # Added empty files line
            f.write("\n")

        f.write("\n" + "=" * 50 + "\n\n")

        # Write detailed unconnected paths report
        if not unconnected_paths:
            f.write("No files with unconnected paths were found.\n")
            f.write("All t(number).png files contain single, connected white line paths.\n")
            return

        f.write(f"DETAILED UNCONNECTED PATHS REPORT\n")
        f.write("-" * 40 + "\n")
        f.write(f"Found {len(unconnected_paths)} files with unconnected paths:\n\n")

        # Group by folder for better organization
        current_folder = ""
        for issue in unconnected_paths:
            if issue['folder'] != current_folder:
                current_folder = issue['folder']
                f.write(f"Folder: {current_folder}\n")
                f.write("-" * 30 + "\n")

            f.write(f"  Subfolder: {issue['subfolder']}\n")
            f.write(f"  File: {issue['file']}\n")
            f.write(f"  Issue: {issue['issue']}\n")
            f.write("\n")


def main():
    print("Unconnected Path Detection Tool")
    print("=" * 40)
    print("This tool analyzes PNG files with white lines on black backgrounds")
    print("to detect cases where the white line is broken into multiple segments.\n")

    # Check if required libraries are available
    try:
        import cv2
        import numpy as np
    except ImportError:
        print("Error: Required libraries not found!")
        print("Please install OpenCV and NumPy:")
        print("pip install opencv-python numpy pillow")
        return

    # HARD CODE YOUR ROOT FOLDER PATH HERE:
    root_folder = "/media/berke-dhm/MMT_3/ME/ME_part2/Data/segmentation_output/Copper_4"  # Replace with your actual path

    # Uncomment the lines below if you want to use input prompt instead:
    # root_folder = input("Enter the path to the root folder: ").strip()
    # root_folder = root_folder.strip('"\'')

    if not root_folder or root_folder == r"C:\path\to\your\root\folder":
        print("Error: Please update the root_folder variable with your actual folder path.")
        print("Edit the script and change the line:")
        print('root_folder = r"C:\\path\\to\\your\\root\\folder"')
        print("to your actual folder path.")
        return

    if not os.path.exists(root_folder):
        print(f"Error: Folder '{root_folder}' does not exist.")
        return

    print(f"Starting analysis of: {root_folder}")
    print("-" * 50)

    scan_folder_structure(root_folder)


if __name__ == "__main__":
    main()