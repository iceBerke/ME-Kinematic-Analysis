# The authors of the code are Max Riekeles and Berke Santos. Contact: riekeles@tu-berlin.de
#
# This script processes particle tracking data from a hierarchical folder structure.
# It calculates various motion metrics including velocity statistics, straightness index,
# direction changes, and speed dynamics for each track.
#
# UPDATED FOR TEMPORALLY CORRECTED DATA:
# This version processes temporally corrected tracking data from alignment_converted_results_2/
# folders, which contains blob data with MHI-corrected timepoints ensuring accurate timing
# information rather than potentially delayed detection timepoints.
#
# Expected folder structure:
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
# │   │           ├── alignment_results/     # Contains original .npy files (not used)
# │   │           │   └── aligned_blobs_*.npy # Original tracking data files
# │   │           ├── alignment_results_2/   # Contains temporally corrected .npy files (not used)
# │   │           │   └── aligned_blobs_*.npy # Temporally corrected tracking data files
# │   │           ├── alignment_converted_results/ # Contains original converted files (not used)
# │   │           │   └── *_converted.npy    # Original converted tracking data
# │   │           ├── alignment_converted_results_2/ # INPUT: Contains temporally corrected converted files
# │   │           │   └── *_converted.npy    # Temporally corrected converted tracking data (micrometers & seconds)
# │   │           ├── mhi_overlay_corrected.png # Final overlay output
# │   │           └── average_frequency.txt  # Contains acquisition frequency data
# │   └── subfolder_2/
# │       └── shortened_Y/
# │           └── subsubfolder_2_changed/
# │               ├── npy_tracks/
# │               ├── blobs_subsubfolder_2.npy
# │               ├── *_mhi.png
# │               ├── alignment_summary_corrected.txt
# │               ├── alignment_results/     # Contains original .npy files (not used)
# │               ├── alignment_results_2/   # Contains temporally corrected .npy files (not used)
# │               ├── alignment_converted_results/ # Contains original converted files (not used)
# │               ├── alignment_converted_results_2/ # INPUT: Temporally corrected source .npy files for processing
# │               ├── mhi_overlay_corrected.png
# │               └── average_frequency.txt
# ├── processed_results_2/                  # OUTPUT: Created by this script for temporally corrected data
# │   ├── Lead_1_processed_results.csv      # Analysis results for Lead_1 (temporally corrected)
# │   └── Copper_3_processed_results.csv    # Analysis results for Copper_3 (temporally corrected)
# ├── Lead_1/                               # Original data folders (XML source)
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
# └── Copper_3/                             # Additional data folders
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
# Script workflow:
# 1. Iterate through all directories in segmentation_output/ (e.g., Lead_1, Copper_3)
# 2. For each directory, find all alignment_converted_results_2/ directories recursively
# 3. Process all *_converted.npy files (containing temporally corrected x, y, t coordinates)
# 4. Calculate motion metrics with smoothing and filtering
# 5. Save individual track results as CSV files in processed_results_2/ directory
# 6. Group tracks by experimental condition and create summary statistics
#
# SUBSUBFOLDER NAMING PATTERN ASSUMED:
# (species_name)_(solute_or_control)_(time_of_exposure)_sampleX_recY_changed
# Examples:
# - ecoli_control_24h_sample1_rec1_changed
# - salmonella_treatment_48h_sample2_rec1_changed
# - yeast_lowsalt_72h_sample3_rec2_changed
#
# This pattern allows grouping of:
# - Biological replicates: sample1, sample2, sample3 (different biological samples)
# - Technical replicates: rec1, rec2 (different recordings of same sample)
# - Experimental conditions: everything before _sampleX_recY
#
# Input: *_converted.npy files with columns [x_um, y_um, time_s] (temporally corrected)
# Output: CSV files with comprehensive motion analysis metrics + summary statistics
#
import numpy as np
import math
from pathlib import Path
from scipy.ndimage import uniform_filter1d  # For applying a moving average (smoothing)
import re
from collections import defaultdict

# Root directory containing the segmentation_output folder
root_data_dir = Path("/media/general-max-riekeles/MMT_3/ME/Analysis_20_09")  # Update this path
segmentation_output_dir = root_data_dir / "segmentation_output"

# Create processed_results_2 directory for temporally corrected data
processed_results_dir = root_data_dir / "processed_results_2"
processed_results_dir.mkdir(exist_ok=True)

# Threshold for significant direction change (in degrees)
ANGLE_THRESHOLD = 30

# Minimum displacement to consider (to filter out noise)
MIN_DISPLACEMENT = 0.01  # Adjust based on your data scale

# Minimum time allowed between subsequent direction changes (in seconds)
MIN_TIME_BETWEEN_DIRECTION_CHANGES = 0.1

# Maximum speed to consider (in µm/s)
MAX_SPEED = 60  # µm/s

# Smoothing window size (for the moving average filter)
SMOOTHING_WINDOW = 1  # Window = 1 means NO SMOOTHING - preserves all original position data
                      # This maintains all genuine biological movements (including sharp turns)
                      # but also keeps any tracking noise/jitter in the data

# Function to calculate angle between two vectors
def calculate_angle(v1, v2):
    dot_prod = np.dot(v1, v2)
    mag1 = np.linalg.norm(v1)
    mag2 = np.linalg.norm(v2)
    if mag1 == 0 or mag2 == 0:
        return np.nan
    cos_theta = dot_prod / (mag1 * mag2)
    cos_theta = max(min(cos_theta, 1), -1)  # Clamp cos_theta to avoid NaNs due to floating point errors
    angle = math.acos(cos_theta)
    return np.degrees(angle)

# Function to smooth data using a moving average filter
def smooth_data(data, window_size):
    return uniform_filter1d(data, size=window_size)

def extract_sample_group(subsubfolder_name):
    """
    Extract experimental condition from subsubfolder name up to _sampleX_recY pattern.
    
    ASSUMED PATTERN: (species_name)_(solute_or_control)_(time_of_exposure)_sampleX_recY
    OR WITH DESCRIPTORS: (species_name)_(solute_or_control)_(time_of_exposure)_sampleX_descriptor_recY
    Examples: 
    - 'ecoli_control_24h_sample1_rec1_changed' -> 'ecoli_control_24h'
    - 'ecoli_control_24h_sample2_2_rec1_changed' -> 'ecoli_control_24h'
    - 'salmonella_treatment_48h_sample1_dilution_rec2_changed' -> 'salmonella_treatment_48h'
    
    The pattern groups biological triplicates and technical replicates under the same 
    experimental condition, ignoring any additional descriptors between sample and rec.
    """
    # Remove '_changed' suffix if present
    clean_name = subsubfolder_name.replace('_changed', '') if subsubfolder_name.endswith('_changed') else subsubfolder_name
    
    # More flexible pattern: match everything up to _sampleX_...anything..._recY
    # This handles cases like _sample1_2_rec1 or _sample2_dilution_rec1
    pattern = r'(.+?)_sample\d+.*?_rec\d+'
    match = re.search(pattern, clean_name)
    if match:
        experimental_condition = match.group(1)
        return experimental_condition
    
    # Fallback: try simpler pattern for cases without descriptors
    simple_pattern = r'(.+?)_sample\d+_rec\d+'
    simple_match = re.search(simple_pattern, clean_name)
    if simple_match:
        experimental_condition = simple_match.group(1)
        return experimental_condition
    
    # If no sample pattern found, return the clean name (fallback)
    return clean_name

def calculate_group_averages(tracks_data):
    """Calculate averages, standard deviations, and standard errors for a group of tracks."""
    if not tracks_data:
        return None
    
    # Extract data arrays for each metric
    velocities = np.array([track[0] for track in tracks_data])
    speed_dynamics = np.array([track[1] for track in tracks_data])
    straightness_indices = np.array([track[2] for track in tracks_data])
    direction_change_rates = np.array([track[3] for track in tracks_data])
    count = len(tracks_data)
    
    # Calculate means
    mean_velocity = np.mean(velocities)
    mean_speed_dynamic = np.mean(speed_dynamics)
    mean_straightness_index = np.mean(straightness_indices)
    mean_direction_change_rate = np.mean(direction_change_rates)
    
    # Calculate standard deviations
    std_velocity = np.std(velocities, ddof=1) if count > 1 else 0  # Use sample std (ddof=1)
    std_speed_dynamic = np.std(speed_dynamics, ddof=1) if count > 1 else 0
    std_straightness_index = np.std(straightness_indices, ddof=1) if count > 1 else 0
    std_direction_change_rate = np.std(direction_change_rates, ddof=1) if count > 1 else 0
    
    # Calculate standard errors (std / sqrt(n))
    sem_velocity = std_velocity / np.sqrt(count) if count > 0 else 0
    sem_speed_dynamic = std_speed_dynamic / np.sqrt(count) if count > 0 else 0
    sem_straightness_index = std_straightness_index / np.sqrt(count) if count > 0 else 0
    sem_direction_change_rate = std_direction_change_rate / np.sqrt(count) if count > 0 else 0
    
    return {
        'count': count,
        'mean_velocity': mean_velocity,
        'std_velocity': std_velocity,
        'sem_velocity': sem_velocity,
        'speed_dynamic': mean_speed_dynamic,
        'std_speed_dynamic': std_speed_dynamic,
        'sem_speed_dynamic': sem_speed_dynamic,
        'straightness_index': mean_straightness_index,
        'std_straightness_index': std_straightness_index,
        'sem_straightness_index': sem_straightness_index,
        'direction_change_rate': mean_direction_change_rate,
        'std_direction_change_rate': std_direction_change_rate,
        'sem_direction_change_rate': sem_direction_change_rate
    }

def write_summary_file(output_file, grouped_data, subfolder_name):
    """Write summary statistics to file."""
    with open(output_file, 'w') as f:
        f.write(f"SUMMARY STATISTICS FOR {subfolder_name} - TEMPORALLY CORRECTED DATA\n")
        f.write("="*70 + "\n\n")
        f.write("Averages calculated for: Mean Velocity (μm/s), Speed Dynamic (%), Straightness Index, Direction Change Rate (/time)\n")
        f.write("Grouped by experimental condition (everything before _sampleX_recY pattern)\n")
        f.write("Each group combines all tracks from biological and technical replicates\n")
        f.write("Format: Mean ± StdDev (SEM) where SEM = Standard Error of the Mean\n")
        f.write("NOTE: Analysis performed on temporally corrected data with MHI-adjusted timepoints\n\n")
        
        # Write by shortened directory
        for shortened_dir in sorted(grouped_data.keys()):
            if shortened_dir != 'combined':
                f.write(f"{shortened_dir.upper()} DIRECTORY:\n")
                f.write("-" * 40 + "\n")
                
                for experimental_condition in sorted(grouped_data[shortened_dir].keys()):
                    stats = grouped_data[shortened_dir][experimental_condition]
                    f.write(f"Experimental Condition: {experimental_condition}\n")
                    f.write(f"  Total Tracks: {stats['count']}\n")
                    f.write(f"  Mean Velocity: {stats['mean_velocity']:.3f} ± {stats['std_velocity']:.3f} ({stats['sem_velocity']:.3f}) μm/s\n")
                    f.write(f"  Speed Dynamic: {stats['speed_dynamic']:.3f} ± {stats['std_speed_dynamic']:.3f} ({stats['sem_speed_dynamic']:.3f})%\n")
                    f.write(f"  Straightness Index: {stats['straightness_index']:.3f} ± {stats['std_straightness_index']:.3f} ({stats['sem_straightness_index']:.3f})\n")
                    f.write(f"  Direction Change Rate: {stats['direction_change_rate']:.3f} ± {stats['std_direction_change_rate']:.3f} ({stats['sem_direction_change_rate']:.3f})\n\n")
        
        # Write combined across shortened directories
        if 'combined' in grouped_data:
            f.write("COMBINED ACROSS ALL SHORTENED DIRECTORIES:\n")
            f.write("-" * 50 + "\n")
            
            for experimental_condition in sorted(grouped_data['combined'].keys()):
                stats = grouped_data['combined'][experimental_condition]
                f.write(f"Experimental Condition: {experimental_condition}\n")
                f.write(f"  Total Tracks: {stats['count']}\n")
                f.write(f"  Mean Velocity: {stats['mean_velocity']:.3f} ± {stats['std_velocity']:.3f} ({stats['sem_velocity']:.3f}) μm/s\n")
                f.write(f"  Speed Dynamic: {stats['speed_dynamic']:.3f} ± {stats['std_speed_dynamic']:.3f} ({stats['sem_speed_dynamic']:.3f})%\n")
                f.write(f"  Straightness Index: {stats['straightness_index']:.3f} ± {stats['std_straightness_index']:.3f} ({stats['sem_straightness_index']:.3f})\n")
                f.write(f"  Direction Change Rate: {stats['direction_change_rate']:.3f} ± {stats['std_direction_change_rate']:.3f} ({stats['sem_direction_change_rate']:.3f})\n\n")

# Process all subfolder_ directories in the segmentation_output
total_subfolders = 0
total_sessions = 0
total_tracks_processed = 0
total_tracks_failed = 0
subfolder_results = []

print("Processing temporally corrected tracking data from alignment_converted_results_2/ folders")
print("="*80)

for subfolder in segmentation_output_dir.iterdir():
    if subfolder.is_dir():
        total_subfolders += 1
        print(f"Processing {subfolder.name}...")
        
        # Track statistics for this subfolder
        subfolder_sessions = 0
        subfolder_tracks_processed = 0
        subfolder_tracks_failed = 0
        
        # Output CSV file to save the metrics for all tracks in the current subfolder
        output_file = processed_results_dir / f'{subfolder.name}_processed_results.csv'
        
        # Find all alignment_converted_results_2 directories within this subfolder
        alignment_converted_paths = list(subfolder.rglob("alignment_converted_results_2"))
        
        if not alignment_converted_paths:
            print(f"  WARNING: No alignment_converted_results_2 directories found in {subfolder.name}")
            print(f"  (Make sure to run the temporally corrected coordinate conversion script first)")
            subfolder_results.append((subfolder.name, 0, 0, 0))
            continue
        
        # Prepare the output CSV file for writing
        # Also prepare data collection for summary statistics
        track_data_for_summary = defaultdict(lambda: defaultdict(list))  # {shortened_dir: {experimental_condition: [track_data]}}
        track_counter = defaultdict(int)  # Counter for tracks per session
        
        with open(output_file, mode='w') as f:
            # Write CSV header
            f.write("Track,Subsubfolder,Mean_Velocity_um_s,Std_Velocity_um_s,Speed_Dynamic_percent,Straightness_Index,Direction_Change_Rate,Total_Time_s,Num_Direction_Changes,Direction_Change_Timepoints\n")
            
            # Process each alignment_converted_results_2 directory
            for alignment_dir in alignment_converted_paths:
                subfolder_sessions += 1
                print(f"  Processing temporally corrected session: {alignment_dir.parent.name}")
                
                # Get the session identifier (subsubfolder_()_changed)
                session_name = alignment_dir.parent.name
                
                # Find all .npy files in alignment_converted_results_2 (looking for converted files)
                npy_files = list(alignment_dir.glob('*_converted.npy'))
                
                if not npy_files:
                    print(f"    WARNING: No *_converted.npy files found in {alignment_dir}")
                    continue
                
                # Process each npy file in the current alignment_converted_results_2 folder
                for filepath in npy_files:
                    try:
                        # Load data efficiently
                        data = np.load(filepath)
                        if data.shape[1] < 3:
                            print(f"    SKIP: {filepath.name} - insufficient columns")
                            subfolder_tracks_failed += 1
                            continue
                            
                        x, y, t = data[:, 0], data[:, 1], data[:, 2]

                        if len(x) < 2:
                            print(f"    SKIP: {filepath.name} - track too short")
                            subfolder_tracks_failed += 1
                            continue

                        # Apply smoothing to x and y coordinates
                        x_smooth = smooth_data(x, SMOOTHING_WINDOW)
                        y_smooth = smooth_data(y, SMOOTHING_WINDOW)

                        # Calculate displacements and time differences
                        dx = np.diff(x_smooth)
                        dy = np.diff(y_smooth)
                        dt = np.diff(t)

                        # Calculate instantaneous velocities
                        displacements = np.sqrt(dx ** 2 + dy ** 2)
                        
                        # Avoid division by zero
                        valid_dt_mask = dt > 0
                        if not np.any(valid_dt_mask):
                            print(f"    SKIP: {filepath.name} - invalid time differences")
                            subfolder_tracks_failed += 1
                            continue
                            
                        velocities = np.divide(displacements, dt, out=np.zeros_like(displacements), where=valid_dt_mask)

                        # Apply speed filter
                        valid_speeds_mask = (velocities <= MAX_SPEED) & valid_dt_mask
                        filtered_velocities = velocities[valid_speeds_mask]
                        filtered_displacements = displacements[valid_speeds_mask]
                        filtered_dt = dt[valid_speeds_mask]
                        filtered_t = ((t[:-1] + t[1:]) / 2)[valid_speeds_mask]

                        # Skip if no valid speeds are left after filtering
                        if len(filtered_velocities) == 0:
                            print(f"    SKIP: {filepath.name} - no valid velocities after filtering")
                            subfolder_tracks_failed += 1
                            continue

                        # Report speed filtering if any velocities were removed
                        num_removed = len(velocities) - len(filtered_velocities)
                        if num_removed > 0:
                            print(f"    SPEED FILTER: {filepath.name} - removed {num_removed} out of {len(velocities)} velocity measurements (>{MAX_SPEED} μm/s)")

                        # Calculate mean and standard deviation of filtered velocities
                        mean_velocity = np.mean(filtered_velocities)
                        std_velocity = np.std(filtered_velocities)

                        # Calculate speed dynamic (stdv as a percentage of mean speed)
                        speed_dynamic = (std_velocity / mean_velocity) * 100 if mean_velocity != 0 else np.nan

                        # Calculate net displacement and path length
                        net_displacement = np.sqrt((x_smooth[-1] - x_smooth[0]) ** 2 + (y_smooth[-1] - y_smooth[0]) ** 2)
                        path_length = np.sum(filtered_displacements)
                        straightness_index = net_displacement / path_length if path_length != 0 else np.nan

                        # Calculate turning angles and store timepoints of significant direction changes
                        direction_changes = 0
                        significant_timepoints = []
                        last_direction_change_time = None

                        for i in range(1, len(dx)):
                            v1 = np.array([dx[i - 1], dy[i - 1]])
                            v2 = np.array([dx[i], dy[i]])

                            if np.linalg.norm(v1) < MIN_DISPLACEMENT or np.linalg.norm(v2) < MIN_DISPLACEMENT:
                                continue

                            angle = calculate_angle(v1, v2)
                            if not np.isnan(angle) and angle > ANGLE_THRESHOLD:
                                if last_direction_change_time is None:
                                    direction_changes += 1
                                    significant_timepoints.append(t[i])
                                    last_direction_change_time = t[i]
                                else:
                                    if t[i] - last_direction_change_time >= MIN_TIME_BETWEEN_DIRECTION_CHANGES:
                                        direction_changes += 1
                                        significant_timepoints.append(t[i])
                                        last_direction_change_time = t[i]

                        total_time = t[-1] - t[0]
                        direction_change_rate = direction_changes / total_time if total_time > 0 else np.nan

                        # Create track identifier with shortened directory info and counter
                        track_name = filepath.stem
                        
                        # Extract shortened directory from path
                        shortened_dir = None
                        session_path = alignment_dir.parent
                        for parent in session_path.parents:
                            if parent.name.startswith('shortened_'):
                                shortened_dir = parent.name
                                break
                        
                        # Clean session name (remove _changed suffix)
                        clean_session_name = session_name.replace('_changed', '') if session_name.endswith('_changed') else session_name
                        
                        # Create track counter key (shortened_dir + session)
                        counter_key = f"{shortened_dir}_{session_name}" if shortened_dir else session_name
                        track_counter[counter_key] += 1
                        
                        # Create simplified track identifier: sh_X_tN
                        if shortened_dir:
                            shortened_prefix = shortened_dir.replace('shortened_', 'sh_')
                            full_track_name = f"{shortened_prefix}_t{track_counter[counter_key]}"
                        else:
                            # Fallback if shortened directory not found
                            full_track_name = f"t{track_counter[counter_key]}"

                        # Convert timepoints list to string for CSV
                        timepoints_str = ";".join([f"{tp:.3f}" for tp in significant_timepoints])

                        # Write per-track metrics to CSV
                        f.write(f"{full_track_name},{clean_session_name},{mean_velocity:.3f},{std_velocity:.3f},{speed_dynamic:.3f},{straightness_index:.3f},{direction_change_rate:.3f},{total_time:.3f},{direction_changes},\"{timepoints_str}\"\n")
                        
                        # Extract experimental condition from subsubfolder name for summary statistics
                        experimental_condition = extract_sample_group(session_name)  # Use session_name (subsubfolder name)
                        if experimental_condition and shortened_dir:
                            # Store data for summary: [mean_velocity, speed_dynamic, straightness_index, direction_change_rate]
                            track_summary_data = [mean_velocity, speed_dynamic, straightness_index, direction_change_rate]
                            track_data_for_summary[shortened_dir][experimental_condition].append(track_summary_data)
                        
                        subfolder_tracks_processed += 1

                        # Clear variables to save memory
                        del data, x, y, t, x_smooth, y_smooth, dx, dy, dt, displacements, velocities
                        del filtered_velocities, filtered_displacements, filtered_dt, filtered_t

                    except Exception as e:
                        print(f"    ERROR: {filepath.name} - {e}")
                        subfolder_tracks_failed += 1
                        continue

        # Generate summary statistics after processing all tracks
        if track_data_for_summary:
            print(f"  Generating summary statistics for {subfolder.name}...")
            
            # Calculate averages by shortened directory
            grouped_stats = {}
            combined_data = defaultdict(list)  # For combining across shortened directories
            
            for shortened_dir, experimental_conditions in track_data_for_summary.items():
                grouped_stats[shortened_dir] = {}
                for experimental_condition, tracks_data in experimental_conditions.items():
                    # Calculate averages for this shortened_dir and experimental condition
                    stats = calculate_group_averages(tracks_data)
                    if stats:
                        grouped_stats[shortened_dir][experimental_condition] = stats
                        # Also add to combined data
                        combined_data[experimental_condition].extend(tracks_data)
            
            # Calculate combined averages across shortened directories
            grouped_stats['combined'] = {}
            for experimental_condition, tracks_data in combined_data.items():
                stats = calculate_group_averages(tracks_data)
                if stats:
                    grouped_stats['combined'][experimental_condition] = stats
            
            # Write summary file
            summary_file = processed_results_dir / f'{subfolder.name}_summary_statistics.txt'
            write_summary_file(summary_file, grouped_stats, subfolder.name)
            print(f"  Summary statistics saved to: {summary_file.name}")
        
        # Update totals
        total_sessions += subfolder_sessions
        total_tracks_processed += subfolder_tracks_processed
        total_tracks_failed += subfolder_tracks_failed
        subfolder_results.append((subfolder.name, subfolder_sessions, subfolder_tracks_processed, subfolder_tracks_failed))
        
        print(f"  Completed {subfolder.name}: {subfolder_tracks_processed} tracks processed, {subfolder_tracks_failed} failed")

# Print summary
print("\n" + "="*80)
print("TEMPORALLY CORRECTED DATA PROCESSING SUMMARY")
print("="*80)
print(f"Total subfolders processed: {total_subfolders}")
print(f"Total sessions found: {total_sessions}")
print(f"Total tracks successfully processed: {total_tracks_processed}")
print(f"Total tracks failed: {total_tracks_failed}")
print(f"Success rate: {total_tracks_processed/(total_tracks_processed + total_tracks_failed)*100:.1f}%" if (total_tracks_processed + total_tracks_failed) > 0 else "Success rate: N/A")

print("\nPer-subfolder breakdown:")
for subfolder_name, sessions, processed, failed in subfolder_results:
    print(f"  {subfolder_name}: {sessions} sessions, {processed} processed, {failed} failed")

print(f"\nResults saved in: {processed_results_dir}")
print("Temporally corrected track metrics and direction change timepoints saved as CSV files.")
print("Analysis performed on data with MHI-corrected timepoints for accurate motion timing.")
