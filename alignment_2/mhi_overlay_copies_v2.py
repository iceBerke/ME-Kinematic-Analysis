# ============================================================================
# Copy MHI Overlays Script - UPDATED FOR TEMPORAL CORRECTION
# ============================================================================
#
# This script collects all mhi_overlay_corrected.png files created by the batch mhi
# alignment script and copies them to a centralized folder with standardized
# naming conventions (subfolder name + shortened directory name + subsubfolder name).
#
# UPDATED: Now specifically looks for mhi_overlay_corrected.png files which contain
# visualizations of temporally corrected blob data, ensuring the collected overlays
# represent accurate timing information rather than potentially delayed detection timepoints.
#
# Expected Input Structure:
# root_directory/
# └── segmentation_output/
#     ├── subfolder_1/
#     │   └── shortened_5/                   # Example shortened folder
#     │       └── subsubfolder_1/
#     │           └── mhi_overlay_corrected.png    # Source file (temporally corrected)
#     └── subfolder_2/
#         └── shortened_12/                  # Another shortened folder
#             └── subsubfolder_2/
#                 └── mhi_overlay_corrected.png    # Source file (temporally corrected)
#
# Output Structure:
# root_directory/
# └── mhi_overlays_corrected/                # Created by this script
#     ├── Lead_1_sh5_subsubfolder_1_corrected.png        # Renamed copy
#     └── Lead_2_sh10_subsubfolder_2_corrected.png       # Renamed copy
#
# Script Workflow:
# 1. Scans segmentation_output/ for all mhi_overlay_corrected.png files
# 2. Extracts subfolder name, shortened folder number and subsubfolder name
# 3. Creates mhi_overlays_corrected/ directory if it doesn't exist
# 4. Copies files with new naming convention: {subfolder_name}_sh{X}_{subsubfolder_name}_corrected.png

# Script developed with the help of AI (Claude.AI)
# Last updated: 22/09/2025

from pathlib import Path
import shutil
import re
import gc


def extract_shortened_number(shortened_folder_name):
    """Extract number from shortened folder name (e.g., 'shortened_5' -> '5')"""
    match = re.search(r'shortened_(\d+)', shortened_folder_name)
    if match:
        return match.group(1)
    return None


def find_all_mhi_overlays_corrected(segmentation_output_path):
    """Find all mhi_overlay_corrected.png files and extract path information with memory efficiency"""
    overlay_files = []
    segmentation_path = Path(segmentation_output_path)

    if not segmentation_path.exists():
        print(f"Error: segmentation_output path does not exist: {segmentation_output_path}")
        return overlay_files

    try:
        # Use pathlib for efficient directory traversal
        subfolders = [item for item in segmentation_path.iterdir() if item.is_dir()]

        for subfolder_path in subfolders:
            # Process one subfolder at a time to minimize memory usage
            try:
                shortened_folders = [item for item in subfolder_path.iterdir() if item.is_dir()]

                for shortened_path in shortened_folders:
                    # Extract number from shortened folder
                    shortened_num = extract_shortened_number(shortened_path.name)
                    if shortened_num is None:
                        print(f"Warning: Could not extract number from folder: {shortened_path.name}")
                        continue

                    # Process subsubfolders
                    try:
                        subsubfolders = [item for item in shortened_path.iterdir() if item.is_dir()]

                        for subsubfolder_path in subsubfolders:
                            # Check for mhi_overlay_corrected.png (UPDATED filename)
                            overlay_file = subsubfolder_path / "mhi_overlay_corrected.png"
                            if overlay_file.exists() and overlay_file.is_file():
                                overlay_files.append({
                                    'source_path': overlay_file,
                                    'shortened_num': shortened_num,
                                    'subfolder_name': subfolder_path.name,
                                    'subsubfolder_name': subsubfolder_path.name,
                                    'new_name': f"{subfolder_path.name}_sh{shortened_num}_{subsubfolder_path.name}_corrected.png"
                                })

                        # Clean up subsubfolders list from memory
                        del subsubfolders

                    except (PermissionError, OSError) as e:
                        print(f"Warning: Could not access {shortened_path}: {e}")
                        continue

                # Clean up shortened_folders list from memory
                del shortened_folders

            except (PermissionError, OSError) as e:
                print(f"Warning: Could not access {subfolder_path}: {e}")
                continue

        # Clean up subfolders list from memory
        del subfolders

        # Force garbage collection after directory traversal
        gc.collect()

    except (PermissionError, OSError) as e:
        print(f"Error accessing segmentation_output directory: {e}")
        return []

    return overlay_files


def copy_file_with_verification(source_path, destination_path):
    """Copy file with memory-efficient verification"""
    try:
        # Use shutil.copy2 for efficient copying with metadata preservation
        shutil.copy2(source_path, destination_path)

        # Verify copy success and get file size
        if destination_path.exists():
            file_size = destination_path.stat().st_size
            return True, file_size
        else:
            return False, "Destination file not found after copy"

    except Exception as e:
        return False, str(e)


def copy_mhi_overlays_corrected(root_directory_path):
    print(f"Starting temporally corrected MHI overlay collection from: {root_directory_path}")
    print("Looking for mhi_overlay_corrected.png files (temporally corrected visualizations)")
    print("=" * 80)

    # Define paths using pathlib - UPDATED output directory name
    root_path = Path(root_directory_path)
    segmentation_output_path = root_path / "segmentation_output"
    mhi_overlays_dir = root_path / "mhi_overlays_corrected"

    # Check if segmentation_output exists
    if not segmentation_output_path.exists():
        print(f"Error: segmentation_output directory not found at: {segmentation_output_path}")
        return {"total": 0, "successful": 0, "failed": 0, "success_rate": 0.0}

    # Find all mhi_overlay_corrected.png files
    overlay_files = find_all_mhi_overlays_corrected(segmentation_output_path)

    print(f"Found {len(overlay_files)} mhi_overlay_corrected.png files")

    if not overlay_files:
        print("No mhi_overlay_corrected.png files found!")
        print("Make sure you've run the temporally corrected MHI visualization script first.")
        return {"total": 0, "successful": 0, "failed": 0, "success_rate": 0.0}

    # Create mhi_overlays_corrected directory if it doesn't exist
    if not mhi_overlays_dir.exists():
        mhi_overlays_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {mhi_overlays_dir}")
    else:
        print(f"Using existing directory: {mhi_overlays_dir}")

    # Initialize tracking variables
    successful_copies = []
    failed_copies = []
    copy_details = {}

    # Process files one at a time to minimize memory usage
    total_files = len(overlay_files)

    for i, file_info in enumerate(overlay_files, 1):
        print(f"\n[{i}/{total_files}] Processing: {file_info['new_name']}")

        source_path = file_info['source_path']
        destination_path = mhi_overlays_dir / file_info['new_name']

        # Check if source file exists
        if not source_path.exists():
            failed_copies.append(file_info['new_name'])
            copy_details[file_info['new_name']] = "Source file not found"
            print(f"  FAILED: Source file not found")
            continue

        # Copy the file with verification
        success, result = copy_file_with_verification(source_path, destination_path)

        if success:
            successful_copies.append(file_info['new_name'])
            copy_details[file_info['new_name']] = f"Copied successfully ({result} bytes)"
            print(f"  SUCCESS: Copied to {file_info['new_name']} ({result} bytes)")
        else:
            failed_copies.append(file_info['new_name'])
            copy_details[file_info['new_name']] = f"Failed: {result}"
            print(f"  FAILED: {result}")

        # Periodic memory cleanup every 10 files
        if i % 10 == 0:
            gc.collect()

    # Final cleanup
    del overlay_files
    gc.collect()

    # Calculate summary statistics
    successful_count = len(successful_copies)
    failed_count = len(failed_copies)
    success_rate = (successful_count / total_files * 100) if total_files > 0 else 0

    # Print detailed summary
    print("\n" + "=" * 80)
    print("TEMPORALLY CORRECTED MHI OVERLAY COPYING COMPLETE")
    print("=" * 80)
    print(f"SUMMARY STATISTICS:")
    print(f"   Total corrected files found: {total_files}")
    print(f"   Successful copies: {successful_count}")
    print(f"   Failed copies: {failed_count}")
    print(f"   Success rate: {success_rate:.1f}%")
    print(f"   Output directory: {mhi_overlays_dir}")

    # Show successful copies
    if successful_copies:
        print(f"\nSUCCESSFUL COPIES ({len(successful_copies)}):")
        for filename in successful_copies:
            print(f"   + {filename}")

    # Show failed copies with reasons
    if failed_copies:
        print(f"\nFAILED COPIES ({len(failed_copies)}):")
        for filename in failed_copies:
            print(f"   - {filename} - {copy_details[filename]}")

    print(f"\nNote: These overlays contain temporally corrected blob visualizations")
    print("=" * 80)

    # Clean up tracking variables before return
    result = {
        "total": total_files,
        "successful": successful_count,
        "failed": failed_count,
        "success_rate": success_rate,
        "successful_copies": successful_copies.copy(),
        "failed_copies": failed_copies.copy(),
        "output_directory": str(mhi_overlays_dir),
        "details": copy_details.copy()
    }

    # Final memory cleanup
    del successful_copies, failed_copies, copy_details
    gc.collect()

    return result


# Example usage
if __name__ == "__main__":
    # Set your root directory path here (the parent of segmentation_output/)
    root_directory_path = "/media/general-max-riekeles/MMT_3/ME/Analysis_20_09"

    # Run the copying process for temporally corrected overlays
    results = copy_mhi_overlays_corrected(root_directory_path)

    # Optional: Print final summary
    if results["total"] > 0:
        print(f"\nFinal Summary:")
        print(f"  {results['successful']}/{results['total']} corrected overlay files copied successfully")
        print(f"  Files saved to: {results['output_directory']}")
    else:
        print(f"\nNo temporally corrected overlay files were found.")
        print(f"Make sure to run the corrected MHI visualization script first.")
