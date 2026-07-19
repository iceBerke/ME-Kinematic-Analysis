# Script receives a root folder with the following structure: root>shortened directories>recording folders>segmented png files + original MHI png file
# (this is the output from the new colour segmentation code - v4)
# The script will ignore the MHI png files
# It outputs three reports: multiple tracks report, global summary with the number of segmented tracks per folder type
# (e.g., control 0h folders), and empty outputs report (segmented outputs that are empty)

# Script developed with the help of AI (Claude.AI)
# Last update: 14/09/2025

import os
import re
import gc
import psutil
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
from sklearn.cluster import DBSCAN


def check_memory_usage():
    """Check memory usage and force garbage collection if needed."""
    memory = psutil.virtual_memory()
    if memory.percent > 75:  # If memory usage > 75%
        print(f"    Memory usage: {memory.percent:.1f}% - Running garbage collection...")
        gc.collect()
        return True
    return False


def scan_folder_structure(root_folder):
    multiple_tracks_paths = []
    folder_stats = []
    empty_files = []

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
        check_memory_usage()  # Check memory at folder level

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

                # Check each PNG file for multiple tracks and empty files
                multiple_tracks_count = 0
                empty_count = 0
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
                        else:
                            # Check for multiple tracks using the grouping approach
                            track_count = count_tracks_with_grouping(filepath, min_area=50, grouping_distance=250)
                            if track_count > 1:
                                multiple_tracks_paths.append({
                                    'folder': shortened_folder.name,
                                    'subfolder': subfolder.name,
                                    'file': filename,
                                    'issue': f'Contains {track_count} separate tracks (grouped components)',
                                    'track_count': track_count,
                                    'type': 'multiple_tracks'
                                })
                                multiple_tracks_count += 1
                                print(f"      X {filename} - MULTIPLE TRACKS DETECTED ({track_count} tracks)")
                            else:
                                print(f"      - {filename} - Single track (or {track_count} tracks)")
                    except Exception as e:
                        print(f"      ! Error processing {filename}: {str(e)}")

                # Update folder stats with both counts
                folder_stats[-1]['multiple_tracks_files'] = multiple_tracks_count
                folder_stats[-1]['empty_files'] = empty_count

                # Force garbage collection after processing each subfolder
                if len(png_files) > 10:  # Only for subfolders with many files
                    gc.collect()
            else:
                print(f"    No t(number).png files found")
                folder_stats[-1]['multiple_tracks_files'] = 0
                folder_stats[-1]['empty_files'] = 0

    # Write results to txt files
    output_file = root_path / "multiple_tracks.txt"
    summary_file = root_path / "summary.txt"
    empty_file = root_path / "empty_outputs.txt"

    write_results_to_file(output_file, multiple_tracks_paths, folder_stats)
    write_summary_file(summary_file, folder_stats)
    write_empty_files_report(empty_file, empty_files)

    if multiple_tracks_paths:
        print(f"\nFound {len(multiple_tracks_paths)} files with multiple tracks!")
        print(f"Results written to: {output_file}")
    else:
        print(f"\nNo multiple tracks found in any files.")
        print(f"Report written to: {output_file}")

    if empty_files:
        print(f"Found {len(empty_files)} empty files!")
        print(f"Empty files report written to: {empty_file}")
    else:
        print(f"No empty files found.")
        print(f"Empty files report written to: {empty_file}")

    print(f"Summary written to: {summary_file}")


def count_tracks_with_grouping(image_path, min_area=50, grouping_distance=250):
    """
    Count the number of distinct tracks in an image using the grouping approach.
    Returns the number of tracks (groups of connected components).
    """
    image = None
    binary = None
    labels = None
    try:
        # Read the image
        image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")

        # Convert to binary if not already
        _, binary = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY)

        # Find connected components
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)

        # Filter components by area and collect valid ones
        valid_components = []
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if area >= min_area:
                valid_components.append({
                    'label': i,
                    'centroid': centroids[i],
                    'area': area,
                    'stats': stats[i]
                })

        if len(valid_components) == 0:
            return 0

        # Group components by proximity using DBSCAN clustering
        if len(valid_components) > 1:
            # Extract centroids for clustering
            centroids_array = np.array([comp['centroid'] for comp in valid_components])

            # Use DBSCAN to group nearby components
            clustering = DBSCAN(eps=grouping_distance, min_samples=1).fit(centroids_array)

            # Count unique cluster labels (number of tracks)
            num_tracks = len(set(clustering.labels_))
            return num_tracks
        else:
            # Only one component, so it's one track
            return 1

    except Exception as e:
        print(f"Error analyzing tracks in {image_path}: {str(e)}")
        return 0
    finally:
        # Explicit memory cleanup
        if image is not None:
            del image
        if binary is not None:
            del binary
        if labels is not None:
            del labels
        # Force garbage collection for large images
        gc.collect()


def is_empty_file(image_path):
    """
    Check if a PNG file is empty (contains no white pixels - completely black).
    Returns True if the file is empty, False otherwise.
    """
    image = None
    try:
        # Load the image
        image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)

        if image is None:
            raise ValueError(f"Could not load image: {image_path}")

        # Check if there are any white pixels (pixel values > 127)
        # Use a more memory-efficient approach for large images
        white_pixel_count = np.count_nonzero(image > 127)

        # If no white pixels found, file is empty
        return white_pixel_count == 0

    except Exception as e:
        print(f"Error checking if image is empty {image_path}: {str(e)}")
        return False
    finally:
        # Explicit memory cleanup
        if image is not None:
            del image
        gc.collect()


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
        total_multiple_tracks = sum(stat['multiple_tracks_files'] for stat in folder_stats)
        total_empty = sum(stat.get('empty_files', 0) for stat in folder_stats)

        f.write(f"Total shortened folders: {len(set(stat['folder'] for stat in folder_stats))}\n")
        f.write(f"Total subfolders: {len(folder_stats)}\n")
        f.write(f"Total t(number).png files: {total_files}\n")
        f.write(f"Files with multiple tracks: {total_multiple_tracks}\n")
        f.write(f"Empty files (no white pixels): {total_empty}\n")
        if total_files > 0:
            multiple_tracks_percentage = (total_multiple_tracks / total_files) * 100
            empty_percentage = (total_empty / total_files) * 100
            f.write(f"Multiple tracks percentage: {multiple_tracks_percentage:.2f}%\n")
            f.write(f"Empty files percentage: {empty_percentage:.2f}%\n")

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
            folder_total_multiple_tracks = sum(sub['multiple_tracks_files'] for sub in subfolders)
            folder_total_empty = sum(sub.get('empty_files', 0) for sub in subfolders)

            f.write(f"\n{folder_name}:\n")
            f.write(f"  Subfolders: {len(subfolders)}\n")
            f.write(f"  Total files: {folder_total_files}\n")
            f.write(f"  Multiple tracks files: {folder_total_multiple_tracks}\n")
            f.write(f"  Empty files: {folder_total_empty}\n")
            if folder_total_files > 0:
                folder_multiple_tracks_percentage = (folder_total_multiple_tracks / folder_total_files) * 100
                folder_empty_percentage = (folder_total_empty / folder_total_files) * 100
                f.write(f"  Multiple tracks rate: {folder_multiple_tracks_percentage:.2f}%\n")
                f.write(f"  Empty rate: {folder_empty_percentage:.2f}%\n")

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
            pattern_total_multiple_tracks = sum(sub['multiple_tracks_files'] for sub in pattern_stats)
            pattern_total_empty = sum(sub.get('empty_files', 0) for sub in pattern_stats)

            f.write(f"\n{pattern} folders:\n")
            f.write(f"  Count: {len(pattern_stats)} subfolders\n")
            f.write(f"  Total files: {pattern_total_files}\n")
            f.write(f"  Multiple tracks files: {pattern_total_multiple_tracks}\n")
            f.write(f"  Empty files: {pattern_total_empty}\n")
            if pattern_total_files > 0:
                pattern_multiple_tracks_percentage = (pattern_total_multiple_tracks / pattern_total_files) * 100
                pattern_empty_percentage = (pattern_total_empty / pattern_total_files) * 100
                f.write(f"  Multiple tracks rate: {pattern_multiple_tracks_percentage:.2f}%\n")
                f.write(f"  Empty rate: {pattern_empty_percentage:.2f}%\n")

            # List individual subfolders in this pattern
            f.write(f"  Subfolders:\n")
            for sub in pattern_stats:
                f.write(f"    {sub['subfolder']}: {sub['total_files']} files")
                if sub['multiple_tracks_files'] > 0:
                    f.write(f" ({sub['multiple_tracks_files']} multiple tracks)")
                if sub.get('empty_files', 0) > 0:
                    f.write(f" ({sub.get('empty_files', 0)} empty)")
                f.write(f"\n")


def write_results_to_file(output_file, multiple_tracks_paths, folder_stats):
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Multiple Tracks Detection Report\n")
        f.write("=" * 50 + "\n")
        f.write(f"Analysis completed on: {Path.cwd()}\n\n")

        # Write folder statistics first
        f.write("FOLDER STATISTICS\n")
        f.write("-" * 30 + "\n")
        for stat in folder_stats:
            f.write(f"Folder: {stat['folder']}\n")
            f.write(f"  Subfolder: {stat['subfolder']}\n")
            f.write(f"  Total t(number).png files: {stat['total_files']}\n")
            f.write(f"  Files with multiple tracks: {stat['multiple_tracks_files']}\n")
            f.write(f"  Empty files: {stat.get('empty_files', 0)}\n")
            f.write("\n")

        f.write("\n" + "=" * 50 + "\n\n")

        # Write detailed multiple tracks report
        if not multiple_tracks_paths:
            f.write("No files with multiple tracks were found.\n")
            f.write("All t(number).png files contain single tracks (or are empty).\n")
            return

        f.write(f"DETAILED MULTIPLE TRACKS REPORT\n")
        f.write("-" * 40 + "\n")
        f.write(f"Found {len(multiple_tracks_paths)} files with multiple tracks:\n\n")

        # Group by folder for better organization
        current_folder = ""
        for issue in multiple_tracks_paths:
            if issue['folder'] != current_folder:
                current_folder = issue['folder']
                f.write(f"Folder: {current_folder}\n")
                f.write("-" * 30 + "\n")

            f.write(f"  Subfolder: {issue['subfolder']}\n")
            f.write(f"  File: {issue['file']}\n")
            f.write(f"  Issue: {issue['issue']}\n")
            f.write(f"  Track count: {issue.get('track_count', 'unknown')}\n")
            f.write("\n")


def main():
    print("Multiple Tracks Detection Tool")
    print("=" * 40)
    print("This tool analyzes PNG files with white lines on black backgrounds")
    print("to detect cases where there are multiple separate tracks using grouping.\n")

    # Check if required libraries are available
    try:
        import cv2
        import numpy as np
        from sklearn.cluster import DBSCAN
        import psutil
    except ImportError:
        print("Error: Required libraries not found!")
        print("Please install OpenCV, NumPy, scikit-learn, and psutil:")
        print("pip install opencv-python numpy pillow scikit-learn psutil")
        return

    # Show initial memory status
    memory = psutil.virtual_memory()
    print(
        f"Initial memory usage: {memory.percent:.1f}% ({memory.used / (1024 ** 3):.1f}GB / {memory.total / (1024 ** 3):.1f}GB)")
    print()

    # HARD CODE YOUR ROOT FOLDER PATH HERE:
    root_folder = "/media/general-max-riekeles/MMT_3/ME/Analysis_20_09/segmentation_output/Zinc_3"  # Replace with your actual path

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

    # Show final memory status
    memory = psutil.virtual_memory()
    print(
        f"\nFinal memory usage: {memory.percent:.1f}% ({memory.used / (1024 ** 3):.1f}GB / {memory.total / (1024 ** 3):.1f}GB)")


if __name__ == "__main__":
    main()
