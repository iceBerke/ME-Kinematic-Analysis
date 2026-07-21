# The authors of the code are Max Riekeles and Berke Santos. Contact: riekeles@tu-berlin.de
#
# Grouping conventions and group-level statistics for the kinematic analysis.
# NO folder traversal, no track math - this module answers two questions:
#   1. which experimental condition does a recording belong to?  (extract_sample_group)
#   2. what are the mean / std / SEM of a group of tracks?        (calculate_group_averages)
# plus the writer for the human-readable summary report.
#
# Extracted from final_kin_param_extraction_v3/v4 so the grouping rules can be
# changed and re-run without re-processing the .npy tracks.
#
import re

import numpy as np

# Order of the per-track metric vector handed to calculate_group_averages().
SUMMARY_METRIC_ORDER = ["mean_velocity", "speed_dynamic", "straightness_index", "direction_change_rate"]


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
    """
    Calculate averages, standard deviations, and standard errors for a group of tracks.

    tracks_data is a list of 4-element sequences in SUMMARY_METRIC_ORDER, i.e.
    [mean_velocity, speed_dynamic, straightness_index, direction_change_rate].
    """
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


def group_tracks(track_rows):
    """
    Build the nested {shortened_dir: {experimental_condition: [metric_vector, ...]}}
    structure plus the 'combined' key that pools across shortened directories.

    track_rows: iterable of dicts with keys 'shortened_dir', 'experimental_condition'
    and the four SUMMARY_METRIC_ORDER metrics.

    Rows without both a shortened_dir and an experimental_condition are ignored
    (same rule as the original scripts).
    """
    grouped = {}
    combined = {}

    for row in track_rows:
        shortened_dir = row.get('shortened_dir')
        condition = row.get('experimental_condition')
        if not shortened_dir or not condition:
            continue

        metric_vector = [row[name] for name in SUMMARY_METRIC_ORDER]
        grouped.setdefault(shortened_dir, {}).setdefault(condition, []).append(metric_vector)
        combined.setdefault(condition, []).append(metric_vector)

    grouped_stats = {}
    for shortened_dir, conditions in grouped.items():
        grouped_stats[shortened_dir] = {}
        for condition, tracks_data in conditions.items():
            stats = calculate_group_averages(tracks_data)
            if stats:
                grouped_stats[shortened_dir][condition] = stats

    grouped_stats['combined'] = {}
    for condition, tracks_data in combined.items():
        stats = calculate_group_averages(tracks_data)
        if stats:
            grouped_stats['combined'][condition] = stats

    return grouped_stats


def _write_condition_block(f, stats):
    f.write(f"  Total Tracks: {stats['count']}\n")
    f.write(f"  Mean Velocity: {stats['mean_velocity']:.3f} ± {stats['std_velocity']:.3f} ({stats['sem_velocity']:.3f}) μm/s\n")
    f.write(f"  Speed Dynamic: {stats['speed_dynamic']:.3f} ± {stats['std_speed_dynamic']:.3f} ({stats['sem_speed_dynamic']:.3f})%\n")
    f.write(f"  Straightness Index: {stats['straightness_index']:.3f} ± {stats['std_straightness_index']:.3f} ({stats['sem_straightness_index']:.3f})\n")
    f.write(f"  Direction Change Rate: {stats['direction_change_rate']:.3f} ± {stats['std_direction_change_rate']:.3f} ({stats['sem_direction_change_rate']:.3f})\n\n")


def write_summary_file(output_file, grouped_data, subfolder_name, title_suffix="", extra_note=""):
    """
    Write summary statistics to file.

    title_suffix / extra_note reproduce the corrected-branch wording of the old
    v4 script (" - TEMPORALLY CORRECTED DATA" and the MHI-timepoint note); leave
    them empty for the uncorrected branch (old v3 wording).
    """
    title = f"SUMMARY STATISTICS FOR {subfolder_name}{title_suffix}"
    # encoding is explicit: the report contains 'μ', which the Windows default
    # (cp1252) cannot encode - the old v3/v4 scripts crashed here on Windows.
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(title + "\n")
        f.write("=" * (70 if title_suffix else 60) + "\n\n")
        f.write("Averages calculated for: Mean Velocity (μm/s), Speed Dynamic (%), Straightness Index, Direction Change Rate (/time)\n")
        f.write("Grouped by experimental condition (everything before _sampleX_recY pattern)\n")
        f.write("Each group combines all tracks from biological and technical replicates\n")
        f.write("Format: Mean ± StdDev (SEM) where SEM = Standard Error of the Mean\n")
        if extra_note:
            f.write(extra_note + "\n")
        f.write("\n")

        # Write by shortened directory
        for shortened_dir in sorted(grouped_data.keys()):
            if shortened_dir != 'combined':
                f.write(f"{shortened_dir.upper()} DIRECTORY:\n")
                f.write("-" * 40 + "\n")

                for experimental_condition in sorted(grouped_data[shortened_dir].keys()):
                    f.write(f"Experimental Condition: {experimental_condition}\n")
                    _write_condition_block(f, grouped_data[shortened_dir][experimental_condition])

        # Write combined across shortened directories
        if 'combined' in grouped_data:
            f.write("COMBINED ACROSS ALL SHORTENED DIRECTORIES:\n")
            f.write("-" * 50 + "\n")

            for experimental_condition in sorted(grouped_data['combined'].keys()):
                f.write(f"Experimental Condition: {experimental_condition}\n")
                _write_condition_block(f, grouped_data['combined'][experimental_condition])
