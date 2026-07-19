# MHI-Track Blob Alignment Processor with Sequential Filtering and Temporal Correction
#
# This script processes Motion History Images (MHI) and track data to find temporal-spatial 
# alignment between detected blobs and tracked segments within a specified time tolerance.
# 
# NEW FEATURE: Sequential filtering of blobs using darkness, size, and solidity criteria
# to reduce false positives and duplicates in clustered blobs. This filtering step is only applied 
# after the blobs have been aligned with the tracks! The filtering ensures there is only one blob 
# per timepoint (per track) by: first ensuring the darkest blob is selected and, in case of a tie*, 
# it chooses based on a combined metric of solidity+area (largest and most solid blob is chosen).
# * tie is more of a similarity tie (i.e., there is a tolerance)
#
# TEMPORAL CORRECTION FEATURE: Instead of preserving original blob timepoints, this script now
# corrects blob timepoints using MHI data. When a blob passes the tolerance check, its timepoint
# is replaced with the actual movement time from the MHI at that spatial location. This addresses
# timing artifacts that cause artificially high velocities in motion analysis by ensuring temporal
# accuracy rather than just temporal tolerance. Output is saved to alignment_results_2/ to
# distinguish from the original non-corrected alignment results.
#
# EXPECTED DIRECTORY STRUCTURE:
# ============================
#
# root_directory/
# ├── segmentation_output/                    # Output folder (input/output for this script)
# │   ├── subfolder_1/                       # Mirrors data folder structure
# │   │   └── shortened_X/                   # Matches shortened folders in data
# │   │       └── subsubfolder_1/            # Matches data subsubfolders
# │   │           ├── npy_tracks/            # Track data files (INPUT)
# │   │           │   ├── track_001.npy      # Individual track segments
# │   │           │   ├── track_002.npy
# │   │           │   └── ...
# │   │           ├── blobs_subsubfolder_1.npy # Blob detection results (INPUT)
# │   │           │                          # Format: [x, y, timepoint, area, brightness, solidity]
# │   │           ├── alignment_summary.txt  # Summary of alignment results (CREATED BY THIS SCRIPT)
# │   │           └── alignment_results_2/   # Alignment output with temporal correction (CREATED BY THIS SCRIPT)
# │   │               └── aligned_blobs_subsubfolder_1.npy
# │   └── subfolder_2/
# │       └── shortened_Y/
# │           └── subsubfolder_2/
# │               ├── npy_tracks/
# │               ├── blobs_subsubfolder_2.npy
# │               ├── alignment_summary.txt  # Summary of alignment results (CREATED BY THIS SCRIPT)
# │               └── alignment_results_2/   # Alignment output with temporal correction (CREATED BY THIS SCRIPT)
# │                   └── aligned_blobs_subsubfolder_2.npy
# └── subfolder_1/                           # Data folders (input for MHI)
#     └── shortened_X/                       # Time-series experiment folders
#         └── subsubfolder_1/                # Individual recording sessions
#             ├── raw/                       # Original images (not used directly)
#             │   ├── image_00000.tif       # Timepoint 0
#             │   ├── image_00001.tif       # Timepoint 1
#             │   └── ...
#             ├── validate/                  # Validation data (INPUT)
#             │   └── MHI.npy               # Motion History Image (MHI.npy or mhi.npy)
#             └── other_folders/             # Other processing outputs (ignored)

# Script developed with the help of AI (Claude.AI)
# Last updated: 22/09/2025

# The authors of the code are Max Riekeles and Berke Santos. Contact: riekeles@tu-berlin.de
from pathlib import Path
import numpy as np
import cv2 as cv

class ImageUtils:
    
    @staticmethod
    def get_x_y(point):
        """Extract x, y coordinates from a point array."""
        point_x = int(float(point[0]))
        point_y = int(float(point[1]))
        return point_x, point_y

    @staticmethod
    def get_region_boundaries(image, target_pixel, radius):
        """Get region boundaries around a target pixel within image bounds."""
        cx, cy = ImageUtils.get_x_y(target_pixel)

        cx_start = max(0, cx - radius)
        cx_end = min(image.shape[1] - 1, cx + radius)
        cy_start = max(0, cy - radius)
        cy_end = min(image.shape[0] - 1, cy + radius)

        return [cx_start, cx_end, cy_start, cy_end]

    @staticmethod
    def dilate_img(img, kernel_size):
        """Apply dilation to an image with specified kernel size."""
        dilation_kernel_size = kernel_size
        kernel_dilation = np.ones((dilation_kernel_size, dilation_kernel_size), np.uint8)
        kernel_erosion = np.ones((1, 1), np.uint8)
        erosion_img = cv.erode(img, kernel_erosion, iterations=1)
        dilation_img = cv.dilate(erosion_img, kernel_dilation, iterations=1)
        return dilation_img

    @staticmethod
    def fill_img(img, kernel_size):
        """Fill holes in an image using morphological closing."""
        structuring_kernel_size = kernel_size
        kernel = cv.getStructuringElement(cv.MORPH_RECT, (structuring_kernel_size, structuring_kernel_size))
        filled_img = cv.morphologyEx(img, cv.MORPH_CLOSE, kernel)
        return filled_img

def apply_temporal_filtering_to_track(aligned_blobs):
    """
    Apply temporal filtering to blobs aligned to a single track.
    For each timepoint with multiple blobs, select the best one using:
    1) Darkest blob (lowest brightness)
    2) If tied on brightness: largest area + highest solidity
    
    Args:
        aligned_blobs: numpy array with shape (n_blobs, 6) containing aligned blob data
                      [x, y, timepoint, area, brightness, solidity]
    
    Returns:
        filtered numpy array with maximum one blob per timepoint
    """
    if len(aligned_blobs) == 0:
        return aligned_blobs, 0, 0
    
    # Group blobs by timepoint
    timepoints = aligned_blobs[:, 2]  # timepoint column
    unique_timepoints = np.unique(timepoints)
    
    selected_blobs = []
    timepoints_with_multiple_blobs = 0
    total_blobs_removed = 0
    
    for timepoint in unique_timepoints:
        # Get all blobs at this timepoint
        timepoint_mask = timepoints == timepoint
        timepoint_blobs = aligned_blobs[timepoint_mask]
        
        if len(timepoint_blobs) == 1:
            # Only one blob at this timepoint, keep it
            selected_blobs.append(timepoint_blobs[0])
        else:
            # Multiple blobs at this timepoint, apply selection
            timepoints_with_multiple_blobs += 1
            total_blobs_removed += len(timepoint_blobs) - 1
            
            # Step 1: Find darkest blobs (lowest brightness)
            brightnesses = timepoint_blobs[:, 4]  # brightness column
            min_brightness = brightnesses.min()
            
            # Tolerance for considering blobs as "similarly dark"
            brightness_tolerance = 2.5
            darkest_mask = np.isclose(brightnesses, min_brightness, atol=brightness_tolerance)
            darkest_blobs = timepoint_blobs[darkest_mask]
            
            if len(darkest_blobs) == 1:
                selected_blobs.append(darkest_blobs[0])
            else:
                # Step 2: Among darkest blobs, select by area and solidity
                areas = darkest_blobs[:, 3]  # area column
                solidities = darkest_blobs[:, 5]  # solidity column
                
                # Normalize metrics to [0, 1] range for combining
                if np.ptp(areas) > 0:  # Avoid division by zero
                    normalized_areas = (areas - areas.min()) / np.ptp(areas)
                else:
                    normalized_areas = np.ones_like(areas)
                
                # Solidity should already be in [0, 1] range, but normalize just in case
                if np.ptp(solidities) > 0:
                    normalized_solidities = (solidities - solidities.min()) / np.ptp(solidities)
                else:
                    normalized_solidities = np.ones_like(solidities)
                
                # Combine metrics with equal weights
                combined_scores = 0.5 * normalized_areas + 0.5 * normalized_solidities
                
                # Select blob with highest combined score
                best_idx = np.argmax(combined_scores)
                selected_blobs.append(darkest_blobs[best_idx])
    
    # Convert back to numpy array
    if selected_blobs:
        filtered_blobs = np.array(selected_blobs)
    else:
        filtered_blobs = np.empty((0, 6))
    
    return filtered_blobs, timepoints_with_multiple_blobs, total_blobs_removed

def main(root_directory, MHI_TIME_TOLERANCE, APPLY_TEMPORAL_FILTERING=True):

    print(f"Processing root directory: {root_directory}")
    print(f"Temporal correction: ENABLED - Blob timepoints will be corrected using MHI data")
    print(f"Temporal filtering (one blob per timepoint per track): {'ENABLED' if APPLY_TEMPORAL_FILTERING else 'DISABLED'}")
    
    # Define paths
    root_path = Path(root_directory)
    segmentation_output_dir = root_path / "segmentation_output"
    
    if not segmentation_output_dir.exists():
        print(f"Error: segmentation_output directory not found at {segmentation_output_dir}")
        return
    
    # Initialize global statistics tracking
    global_stats = {
        'total_subfolders_processed': 0,
        'total_subfolders_successful': 0,
        'total_subfolders_failed': 0,
        'total_track_files_processed': 0,
        'total_track_files_successful': 0,
        'total_track_files_failed': 0,
        'total_aligned_blobs': 0,
        'failed_subfolders': [],
        'successful_subfolders': []
    }
    
    # Walk through the segmentation_output structure to find processing targets
    for subfolder_path in segmentation_output_dir.iterdir():
        if not subfolder_path.is_dir():
            continue
            
        for shortened_path in subfolder_path.iterdir():
            if not shortened_path.is_dir():
                continue
                
            for subsubfolder_path in shortened_path.iterdir():
                if not subsubfolder_path.is_dir():
                    continue
                
                global_stats['total_subfolders_processed'] += 1
                subfolder_path_str = f"{subfolder_path.name}/{shortened_path.name}/{subsubfolder_path.name}"
                
                # Process this subsubfolder and get results
                success, track_stats = process_subsubfolder(root_path, subfolder_path.name, shortened_path.name, 
                                       subsubfolder_path.name, MHI_TIME_TOLERANCE, APPLY_TEMPORAL_FILTERING)
                
                if success:
                    global_stats['total_subfolders_successful'] += 1
                    global_stats['successful_subfolders'].append(subfolder_path_str)
                    global_stats['total_track_files_processed'] += track_stats['total_tracks']
                    global_stats['total_track_files_successful'] += track_stats['successful_tracks']
                    global_stats['total_track_files_failed'] += track_stats['failed_tracks']
                    global_stats['total_aligned_blobs'] += track_stats['total_aligned_blobs']
                else:
                    global_stats['total_subfolders_failed'] += 1
                    global_stats['failed_subfolders'].append(subfolder_path_str)
    
    # Print final summary
    print_global_summary(global_stats)

def process_subsubfolder(root_path, subfolder, shortened_folder, subsubfolder, 
                        MHI_TIME_TOLERANCE, APPLY_TEMPORAL_FILTERING):

    print(f"Processing: {subfolder}/{shortened_folder}/{subsubfolder}")
    
    # Initialize return values
    success = False
    track_stats = {
        'total_tracks': 0,
        'successful_tracks': 0,
        'failed_tracks': 0,
        'total_aligned_blobs': 0
    }
    
    try:
        # Define paths
        data_path = root_path / subfolder / shortened_folder / subsubfolder
        segmentation_path = root_path / "segmentation_output" / subfolder / shortened_folder / subsubfolder
        
        # Required input paths
        validate_folder = data_path / "validate"
        tracks_folder = segmentation_path / "npy_tracks"
        
        # Look for MHI file (files ending with mhi.npy, case insensitive)
        mhi_file = None
        if validate_folder.exists():
            for file_path in validate_folder.iterdir():
                if file_path.is_file() and file_path.name.lower().endswith('mhi.npy'):
                    mhi_file = file_path
                    break
        
        # Input: existing blob detection results
        blobs_input_file = segmentation_path / f"blobs_{subsubfolder}.npy"
        
        # Output: alignment results directory with temporal correction
        alignment_results_dir = segmentation_path / "alignment_results_2"
        
        # Validate required paths exist
        if not validate_folder.exists():
            print(f"  Skipping: validate folder not found at {validate_folder}")
            return success, track_stats
            
        if mhi_file is None:
            print(f"  Skipping: Neither MHI.npy nor mhi.npy found in {validate_folder}")
            return success, track_stats
            
        if not blobs_input_file.exists():
            print(f"  Skipping: blobs file not found at {blobs_input_file}")
            return success, track_stats
        
        if not tracks_folder.exists():
            print(f"  Skipping: npy_tracks folder not found at {tracks_folder}")
            return success, track_stats
        
        # Check if there are any track files
        track_files = [f for f in tracks_folder.iterdir() if f.suffix == '.npy']
        if not track_files:
            print(f"  Skipping: no .npy track files found in {tracks_folder}")
            return success, track_stats
        
        print(f"  Found {len(track_files)} track files and blob detection results")
        
        # Process the dataset
        summary_file = segmentation_path / "alignment_summary_corrected.txt"
        dataset_success, dataset_track_stats = process_dataset(mhi_file, blobs_input_file, tracks_folder, alignment_results_dir, 
                       summary_file, MHI_TIME_TOLERANCE, APPLY_TEMPORAL_FILTERING)
        
        success = dataset_success
        track_stats = dataset_track_stats
        
        return success, track_stats
        
    except Exception as e:
        print(f"  ERROR processing {subfolder}/{shortened_folder}/{subsubfolder}: {e}")
        return success, track_stats

def process_dataset(mhi_file, blobs_input_file, tracks_folder, alignment_results_dir, 
                   summary_file, MHI_TIME_TOLERANCE, APPLY_TEMPORAL_FILTERING):

    # Initialize tracking variables
    mhi = None
    blobs = None
    
    try:
        # Load MHI data with proper memory management
        print(f"    Loading MHI from: {mhi_file}")
        mhi_ = np.load(mhi_file)
        mhi = cv.resize(mhi_.astype(float), (2048, 2048), interpolation=cv.INTER_CUBIC)
        print(f"    Loaded MHI with shape: {mhi_.shape} -> resized to {mhi.shape}")
        
        # Clear original MHI from memory
        del mhi_
        
        # Load blob detection results with memory management
        print(f"    Loading blobs from: {blobs_input_file}")
        blobs = np.load(blobs_input_file)
        original_blob_count = len(blobs)
        print(f"    Loaded {original_blob_count} blobs from detection results")
        
        # Validate blob format
        if len(blobs) > 0 and blobs.shape[1] != 6:
            print(f"    Warning: Expected 6 columns in blob data, got {blobs.shape[1]}")
            print(f"    Expected format: [x, y, timepoint, area, brightness, solidity]")
        
    except Exception as e:
        print(f"    Error loading input files: {e}")
        # Clean up any partially loaded data
        if mhi is not None:
            del mhi
        if blobs is not None:
            del blobs
        return False, {
            'total_tracks': 0, 
            'successful_tracks': 0, 
            'failed_tracks': 0, 
            'total_aligned_blobs': 0
        }
    
    if len(blobs) == 0:
        print("    Warning: No blobs found to process")
        # Clean up memory
        del mhi, blobs
        return False, {
            'total_tracks': 0, 
            'successful_tracks': 0, 
            'failed_tracks': 0, 
            'total_aligned_blobs': 0
        }
    
    # Ensure output directory exists
    try:
        alignment_results_dir.mkdir(exist_ok=True)
    except Exception as e:
        print(f"    Error creating output directory: {e}")
        # Clean up memory
        del mhi, blobs
        return False, {
            'total_tracks': 0, 
            'successful_tracks': 0, 
            'failed_tracks': 0, 
            'total_aligned_blobs': 0
        }
    
    # Initialize track processing statistics
    track_stats = {
        'total_tracks': 0,
        'successful_tracks': 0,
        'failed_tracks': 0,
        'total_aligned_blobs': 0
    }
    track_summary = []  # Store summary info for each track
    
    # Initialize temporal filtering statistics
    total_timepoints_with_multiple_blobs = 0
    total_blobs_removed_by_temporal_filtering = 0
    
    # Get list of track files
    track_files = [f for f in tracks_folder.iterdir() if f.suffix == '.npy']
    track_stats['total_tracks'] = len(track_files)
    
    # Process each track file with proper memory management
    for track_path in track_files:
        track_segment = None
        try:
            # Load track segment
            track_segment = np.load(track_path, allow_pickle=True)
            
            # Handle 3D track segments by taking first channel
            if len(track_segment.shape) == 3 and track_segment.shape == (2048, 2048, 3):
                track_segment = track_segment[:, :, 0]
            
            print(f"    Processing track: {track_path.name} with shape: {track_segment.shape}")
            
            # STEP 1: Find aligned blobs with temporal correction
            blobs_on_track_segment = get_blobs_on_segment_with_correction(blobs, track_segment, mhi, MHI_TIME_TOLERANCE)
            
            if len(blobs_on_track_segment) > 0:
                # Convert to numpy array for easier processing
                aligned_blobs = np.array(blobs_on_track_segment)
                
                # STEP 2: Apply temporal filtering (one blob per timepoint per track)
                if APPLY_TEMPORAL_FILTERING:
                    filtered_blobs, timepoints_with_multiple, blobs_removed = apply_temporal_filtering_to_track(aligned_blobs)
                    total_timepoints_with_multiple_blobs += timepoints_with_multiple
                    total_blobs_removed_by_temporal_filtering += blobs_removed
                    
                    print(f"      Track alignment: {len(aligned_blobs)} blobs found (with temporal correction)")
                    if timepoints_with_multiple > 0:
                        print(f"      Temporal filtering: {timepoints_with_multiple} timepoints had multiple blobs")
                        print(f"      Removed {blobs_removed} duplicate blobs, kept {len(filtered_blobs)}")
                    else:
                        print(f"      No temporal duplicates found, kept all {len(filtered_blobs)} blobs")
                else:
                    filtered_blobs = aligned_blobs
                    print(f"      Found {len(filtered_blobs)} aligned blobs with temporal correction (no temporal filtering)")
                
                # STEP 3: Sort blobs by time (timepoint is in column 2)
                if len(filtered_blobs) > 0:
                    sorted_blobs = filtered_blobs[filtered_blobs[:, 2].argsort()]
                    
                    # Generate output filename for this specific track
                    track_name_without_ext = track_path.stem
                    output_filename = f"aligned_blobs_{track_name_without_ext}.npy"
                    output_path = alignment_results_dir / output_filename
                    
                    # Save aligned and filtered blobs for this track
                    np.save(output_path, sorted_blobs)
                    
                    print(f"      Final result: {len(sorted_blobs)} blobs saved to {output_filename} (temporally corrected)")
                    track_stats['total_aligned_blobs'] += len(sorted_blobs)
                    track_stats['successful_tracks'] += 1
                    
                    # Add to summary
                    if APPLY_TEMPORAL_FILTERING and blobs_removed > 0:
                        track_summary.append(f"{track_path.name}: {len(sorted_blobs)} aligned blobs (removed {blobs_removed} temporal duplicates, corrected timepoints)")
                    else:
                        track_summary.append(f"{track_path.name}: {len(sorted_blobs)} aligned blobs (corrected timepoints)")
                else:
                    print(f"      No blobs remaining after temporal filtering for {track_path.name}")
                    track_stats['successful_tracks'] += 1  # Still considered successful processing
                    track_summary.append(f"{track_path.name}: 0 aligned blobs (all removed by temporal filtering)")
            else:
                print(f"      No aligned blobs found for {track_path.name}")
                track_stats['successful_tracks'] += 1  # Still considered successful processing
                track_summary.append(f"{track_path.name}: 0 aligned blobs")
                
        except Exception as e:
            print(f"    Error processing track {track_path.name}: {e}")
            track_stats['failed_tracks'] += 1
            track_summary.append(f"{track_path.name}: ERROR - {str(e)}")
        finally:
            # Clean up track segment from memory
            if track_segment is not None:
                del track_segment
    
    print(f"    Track processing summary:")
    print(f"      Total tracks: {track_stats['total_tracks']}")
    print(f"      Successful: {track_stats['successful_tracks']}")
    print(f"      Failed: {track_stats['failed_tracks']}")
    print(f"      Total final aligned blobs (temporally corrected): {track_stats['total_aligned_blobs']}")
    
    if APPLY_TEMPORAL_FILTERING:
        print(f"    Temporal filtering summary:")
        print(f"      Timepoints with multiple blobs: {total_timepoints_with_multiple_blobs}")
        print(f"      Total blobs removed: {total_blobs_removed_by_temporal_filtering}")
    
    # Save summary to text file
    try:
        save_alignment_summary(summary_file, track_summary, track_stats['total_aligned_blobs'], mhi_file, 
                              blobs_input_file, MHI_TIME_TOLERANCE, APPLY_TEMPORAL_FILTERING, 
                              original_blob_count, track_stats, total_timepoints_with_multiple_blobs, total_blobs_removed_by_temporal_filtering)
    except Exception as e:
        print(f"    Error saving summary file: {e}")
    
    # Clean up memory before returning
    del mhi, blobs
    
    # Determine overall success (successful if at least some tracks were processed successfully)
    overall_success = track_stats['successful_tracks'] > 0
    
    return overall_success, track_stats

def save_alignment_summary(summary_file, track_summary, total_aligned_blobs, mhi_file, 
                          blobs_input_file, MHI_TIME_TOLERANCE, APPLY_TEMPORAL_FILTERING, 
                          original_blob_count, track_stats, total_timepoints_with_multiple_blobs, total_blobs_removed_by_temporal_filtering):

    from datetime import datetime
    
    try:
        with open(summary_file, 'w') as f:
            f.write("MHI-Track Blob Alignment Summary with Temporal Correction\n")
            f.write("=" * 60 + "\n\n")
            
            # Processing info
            f.write(f"Processed on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"MHI file: {mhi_file.name}\n")
            f.write(f"Blobs file: {blobs_input_file.name}\n")
            f.write(f"Original blob count: {original_blob_count}\n")
            f.write(f"Time tolerance: {MHI_TIME_TOLERANCE}\n")
            f.write(f"Temporal correction: ENABLED - Blob timepoints corrected using MHI data\n")
            f.write(f"Temporal filtering (one blob per timepoint per track): {'ENABLED' if APPLY_TEMPORAL_FILTERING else 'DISABLED'}\n")
            f.write("\n")
            
            # Track processing statistics
            f.write("Track Processing Statistics:\n")
            f.write("-" * 30 + "\n")
            f.write(f"Total track files found: {track_stats['total_tracks']}\n")
            f.write(f"Successfully processed: {track_stats['successful_tracks']}\n")
            f.write(f"Failed to process: {track_stats['failed_tracks']}\n")
            if track_stats['total_tracks'] > 0:
                success_rate = (track_stats['successful_tracks'] / track_stats['total_tracks']) * 100
                f.write(f"Processing success rate: {success_rate:.1f}%\n")
            f.write("\n")
            
            # Temporal filtering statistics
            if APPLY_TEMPORAL_FILTERING:
                f.write("Temporal Filtering Statistics:\n")
                f.write("-" * 30 + "\n")
                f.write(f"Timepoints with multiple blobs: {total_timepoints_with_multiple_blobs}\n")
                f.write(f"Total blobs removed by temporal filtering: {total_blobs_removed_by_temporal_filtering}\n")
                f.write(f"Final aligned blobs after filtering: {total_aligned_blobs}\n")
                f.write("\n")
            
            # Per-track results
            f.write("Results per track file:\n")
            f.write("-" * 30 + "\n")
            for track_info in track_summary:
                f.write(f"{track_info}\n")
            
            f.write("\n")
            f.write("-" * 30 + "\n")
            f.write(f"Total final aligned blobs (temporally corrected): {total_aligned_blobs}\n")
            
            # Calculate alignment statistics
            tracks_with_alignments = len([t for t in track_summary if "ERROR" not in t and ": 0 " not in t])
            f.write(f"Track files with aligned blobs: {tracks_with_alignments}\n")
            
            if track_stats['successful_tracks'] > 0:
                alignment_rate = (tracks_with_alignments / track_stats['successful_tracks']) * 100
                f.write(f"Alignment success rate: {alignment_rate:.1f}%\n")
                
                if tracks_with_alignments > 0:
                    avg_blobs_per_track = total_aligned_blobs / tracks_with_alignments
                    f.write(f"Average aligned blobs per successful track: {avg_blobs_per_track:.2f}\n")
        
        print(f"    Summary saved to: {summary_file.name}")
        
    except Exception as e:
        print(f"    Error saving summary file: {e}")

def print_global_summary(global_stats):
    """Print comprehensive summary of all processing results."""
    print("\n" + "="*60)
    print("GLOBAL PROCESSING SUMMARY")
    print("="*60)
    
    print(f"\nSubfolder Processing:")
    print(f"  Total subfolders found: {global_stats['total_subfolders_processed']}")
    print(f"  Successfully processed: {global_stats['total_subfolders_successful']}")
    print(f"  Failed to process: {global_stats['total_subfolders_failed']}")
    
    if global_stats['total_subfolders_processed'] > 0:
        subfolder_success_rate = (global_stats['total_subfolders_successful'] / global_stats['total_subfolders_processed']) * 100
        print(f"  Subfolder success rate: {subfolder_success_rate:.1f}%")
    
    print(f"\nTrack File Processing:")
    print(f"  Total track (.npy) files found: {global_stats['total_track_files_processed']}")
    print(f"  Successfully processed: {global_stats['total_track_files_successful']}")
    print(f"  Failed to process: {global_stats['total_track_files_failed']}")
    
    if global_stats['total_track_files_processed'] > 0:
        track_success_rate = (global_stats['total_track_files_successful'] / global_stats['total_track_files_processed']) * 100
        print(f"  Track file success rate: {track_success_rate:.1f}%")
    
    print(f"\nAlignment Results:")
    print(f"  Total aligned blobs across all datasets: {global_stats['total_aligned_blobs']}")
    
    if global_stats['total_track_files_successful'] > 0:
        avg_blobs_per_track = global_stats['total_aligned_blobs'] / global_stats['total_track_files_successful']
        print(f"  Average aligned blobs per successful track: {avg_blobs_per_track:.2f}")
    
    # List successful subfolders
    if global_stats['successful_subfolders']:
        print(f"\nSuccessful Subfolders ({len(global_stats['successful_subfolders'])}):")
        for subfolder in global_stats['successful_subfolders']:
            print(f"  ✓ {subfolder}")
    
    # List failed subfolders
    if global_stats['failed_subfolders']:
        print(f"\nFailed Subfolders ({len(global_stats['failed_subfolders'])}):")
        for subfolder in global_stats['failed_subfolders']:
            print(f"  ✗ {subfolder}")
    
    print("\n" + "="*60)
    print("PROCESSING COMPLETE")
    print("="*60)

def in_time_tolerance_range(point, mhi, MHI_TIME_TOLERANCE):
    """Check if a point is within time tolerance of the MHI."""
    if MHI_TIME_TOLERANCE is None:
        return True

    center_x, center_y = ImageUtils.get_x_y(point)
    center_time_point = int(float(point[2]))  # timepoint is in column 2
    time_on_mhi = mhi[center_y, center_x]

    return time_on_mhi - MHI_TIME_TOLERANCE <= center_time_point <= time_on_mhi + MHI_TIME_TOLERANCE

def get_blobs_on_segment_with_correction(blobs, track_segment, mhi, MHI_TIME_TOLERANCE):
    """
    Find blobs that fall on a track segment within time tolerance and correct their timepoints.
    
    This function performs temporal correction by replacing blob timepoints with MHI values
    at their spatial locations. This fixes timing artifacts from blob detection that cause
    artificially high velocities in motion analysis.
    
    Args:
        blobs: numpy array of blob data [x, y, timepoint, area, brightness, solidity]
        track_segment: 2D array representing spatial track
        mhi: Motion History Image containing actual movement times
        MHI_TIME_TOLERANCE: tolerance for temporal alignment check
        
    Returns:
        list: blobs with corrected timepoints that passed spatial and temporal alignment
    """
    blobs_on_track_segment = []
    for blob in blobs:
        blob_x, blob_y = ImageUtils.get_x_y(blob)

        # Check spatial alignment
        if (0 <= blob_y < track_segment.shape[0] and 
            0 <= blob_x < track_segment.shape[1] and
            track_segment[blob_y, blob_x] > 0):
            
            # Check temporal alignment using tolerance
            if in_time_tolerance_range(blob, mhi, MHI_TIME_TOLERANCE):
                # Create corrected blob with MHI timepoint
                corrected_blob = blob.copy()
                time_on_mhi = mhi[blob_y, blob_x]
                corrected_blob[2] = time_on_mhi  # Replace timepoint with MHI value
                blobs_on_track_segment.append(corrected_blob)

    return blobs_on_track_segment

if __name__ == '__main__':
    # User configuration
    root_directory = "/media/general-max-riekeles/MMT_3/ME/Analysis_20_09"
    MHI_TIME_TOLERANCE = 5
    
    # Temporal filtering parameter
    APPLY_TEMPORAL_FILTERING = True  # Set to False to allow multiple blobs per timepoint per track

    root_path = Path(root_directory)
    if not root_path.exists():
        print(f"Error: Root directory not found: {root_directory}")
    else:
        main(root_directory, MHI_TIME_TOLERANCE, APPLY_TEMPORAL_FILTERING)
