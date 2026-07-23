# The authors of the code are Max Riekeles and Berke Santos. Contact: riekeles@tu-berlin.de
#
# STAGE 7a of the pipeline - per-track kinematic metrics.
#
# Walks the segmentation_output tree, loads every converted track (.npy with
# columns [x_um, y_um, time_s]), computes its motion metrics via kin_metrics,
# and writes one CSV per experiment subfolder into the results directory.
#
# This is the expensive pass (it reads every track file). The grouping and
# summary statistics are a separate, cheap step (summarize_track_metrics.py,
# which reads only the CSVs written here) and run automatically at the end
# unless kin_config.SUMMARIZE_AFTER_EXTRACTION is turned off.
#
# THIS IS THE SCRIPT TO RUN for a full kinematic analysis:
#     cd kinematics && python extract_track_metrics.py
# All settings - including which branch to analyse - are in kin_config.py.
# One script replaces both of the old ones (now in archive/):
#   archive/final_kin_param_extraction_v3.py -> branch "uncorrected"
#   archive/final_kin_param_extraction_v4.py -> branch "corrected"   (canonical)
#
# Expected folder structure (mirrors the rest of the pipeline):
# root_directory/
# ├── segmentation_output/
# │   └── <experiment>/                     # e.g. Lead_1, Copper_3
# │       └── shortened_<N>/
# │           └── <recording>_changed/
# │               ├── alignment_converted_results/    # INPUT (uncorrected branch)
# │               │   └── *_converted.npy
# │               └── alignment_converted_results_2/  # INPUT (corrected branch)
# │                   └── *_converted.npy
# └── processed_results[_2]/                # OUTPUT
#     └── <experiment>_processed_results.csv
#
# SUBSUBFOLDER NAMING PATTERN ASSUMED:
# (species_name)_(solute_or_control)_(time_of_exposure)_sampleX_recY_changed
# e.g. ecoli_control_24h_sample1_rec1_changed
#
import numpy as np
from collections import defaultdict

from kin_grouping import extract_sample_group
from kin_metrics import compute_track_metrics

# CSV columns written per track. Shortened_Dir and Experimental_Condition are
# new relative to the old v3/v4 CSVs - summarize_track_metrics.py groups on them,
# so the summary stage never has to re-derive them from the folder tree.
CSV_HEADER = (
    "Track,Subsubfolder,Shortened_Dir,Experimental_Condition,"
    "Mean_Velocity_um_s,Std_Velocity_um_s,Speed_Dynamic_percent,Straightness_Index,"
    "Direction_Change_Rate,Total_Time_s,Num_Direction_Changes,Direction_Change_Timepoints\n"
)

# Metric columns are written with 6 decimals (the old scripts used 3). The
# summary stage now averages the CSV values, so the extra digits keep its output
# identical to the old in-memory averaging.
METRIC_FORMAT = ".6f"


def find_shortened_dir(session_path):
    """Return the name of the enclosing shortened_<N> directory, or None."""
    for parent in session_path.parents:
        if parent.name.startswith('shortened_'):
            return parent.name
    return None


def build_track_name(shortened_dir, index):
    """Simplified track identifier: sh_<suffix>_t<index> where <suffix> is the
    shortened_ dir's suffix (e.g. shortened_5seconds -> sh_5seconds_t1); just
    t<index> when there is no shortened_ dir."""
    if shortened_dir:
        shortened_prefix = shortened_dir.replace('shortened_', 'sh_')
        return f"{shortened_prefix}_t{index}"
    return f"t{index}"


def process_subfolder(subfolder, output_file, input_subdir, params):
    """
    Process one experiment subfolder (e.g. Lead_1) and write its per-track CSV.

    Returns (sessions, tracks_processed, tracks_failed).
    """
    sessions = 0
    tracks_processed = 0
    tracks_failed = 0

    # Find all converted-results directories within this subfolder
    alignment_converted_paths = list(subfolder.rglob(input_subdir))

    if not alignment_converted_paths:
        print(f"  WARNING: No {input_subdir} directories found in {subfolder.name}")
        return 0, 0, 0

    track_counter = defaultdict(int)  # Counter for tracks per session

    with open(output_file, mode='w', encoding='utf-8') as f:
        f.write(CSV_HEADER)

        for alignment_dir in alignment_converted_paths:
            sessions += 1
            session_name = alignment_dir.parent.name
            print(f"  Processing session: {session_name}")

            npy_files = list(alignment_dir.glob('*_converted.npy'))
            if not npy_files:
                print(f"    WARNING: No *_converted.npy files found in {alignment_dir}")
                continue

            shortened_dir = find_shortened_dir(alignment_dir.parent)
            clean_session_name = (session_name[:-len('_changed')]
                                  if session_name.endswith('_changed') else session_name)
            experimental_condition = extract_sample_group(session_name)
            counter_key = f"{shortened_dir}_{session_name}" if shortened_dir else session_name

            for filepath in npy_files:
                try:
                    data = np.load(filepath)
                    if data.shape[1] < 3:
                        print(f"    SKIP: {filepath.name} - insufficient columns")
                        tracks_failed += 1
                        continue

                    x, y, t = data[:, 0], data[:, 1], data[:, 2]
                    metrics = compute_track_metrics(x, y, t, params)
                    del data, x, y

                    if metrics["skip_reason"] is not None:
                        print(f"    SKIP: {filepath.name} - {metrics['skip_reason']}")
                        tracks_failed += 1
                        del t
                        continue

                    # Report speed filtering if any velocities were removed
                    if metrics["num_velocities_removed"] > 0:
                        # ASCII only: a 'μ' here made this print raise UnicodeEncodeError on a
                        # Windows console, which the except below then logged as a failed track.
                        print(f"    SPEED FILTER: {filepath.name} - removed "
                              f"{metrics['num_velocities_removed']} out of {metrics['num_velocities']} "
                              f"velocity measurements (>{params['MAX_SPEED']} um/s)")

                    track_counter[counter_key] += 1
                    full_track_name = build_track_name(shortened_dir, track_counter[counter_key])

                    timepoints_str = ";".join(f"{tp:.3f}" for tp in metrics["direction_change_timepoints"])

                    f.write(
                        f"{full_track_name},{clean_session_name},{shortened_dir or ''},{experimental_condition or ''},"
                        f"{metrics['mean_velocity']:{METRIC_FORMAT}},{metrics['std_velocity']:{METRIC_FORMAT}},"
                        f"{metrics['speed_dynamic']:{METRIC_FORMAT}},{metrics['straightness_index']:{METRIC_FORMAT}},"
                        f"{metrics['direction_change_rate']:{METRIC_FORMAT}},{metrics['total_time']:.3f},"
                        f"{metrics['num_direction_changes']},\"{timepoints_str}\"\n"
                    )

                    tracks_processed += 1
                    del t, metrics

                except Exception as e:
                    print(f"    ERROR: {filepath.name} - {e}")
                    tracks_failed += 1
                    continue

    return sessions, tracks_processed, tracks_failed


def main(root_data_dir, input_subdir, results_dir_name, params, banner=None):
    segmentation_output_dir = root_data_dir / "segmentation_output"
    processed_results_dir = root_data_dir / results_dir_name
    processed_results_dir.mkdir(exist_ok=True)

    if banner:
        print(banner)
        print("=" * 80)

    total_subfolders = 0
    total_sessions = 0
    total_tracks_processed = 0
    total_tracks_failed = 0
    subfolder_results = []

    for subfolder in segmentation_output_dir.iterdir():
        if not subfolder.is_dir():
            continue

        total_subfolders += 1
        print(f"Processing {subfolder.name}...")

        output_file = processed_results_dir / f'{subfolder.name}_processed_results.csv'
        sessions, processed, failed = process_subfolder(subfolder, output_file, input_subdir, params)

        total_sessions += sessions
        total_tracks_processed += processed
        total_tracks_failed += failed
        subfolder_results.append((subfolder.name, sessions, processed, failed))

        print(f"  Completed {subfolder.name}: {processed} tracks processed, {failed} failed")

    print("\n" + "=" * 60)
    print("PROCESSING SUMMARY")
    print("=" * 60)
    print(f"Total subfolders processed: {total_subfolders}")
    print(f"Total sessions found: {total_sessions}")
    print(f"Total tracks successfully processed: {total_tracks_processed}")
    print(f"Total tracks failed: {total_tracks_failed}")
    total_attempted = total_tracks_processed + total_tracks_failed
    print(f"Success rate: {total_tracks_processed / total_attempted * 100:.1f}%"
          if total_attempted > 0 else "Success rate: N/A")

    print("\nPer-subfolder breakdown:")
    for subfolder_name, sessions, processed, failed in subfolder_results:
        print(f"  {subfolder_name}: {sessions} sessions, {processed} processed, {failed} failed")

    print(f"\nResults saved in: {processed_results_dir}")


if __name__ == "__main__":
    # The root directory and branch are asked for (or given on the command line);
    # the analysis settings come from kin_config.py.
    import kin_config as cfg
    import summarize_track_metrics
    from kin_prompt import resolve_settings

    # Ask for the per-track analysis parameters and the summary track filters
    # (each pre-filled with its kin_config.py default) alongside root + branch.
    analysis_specs = cfg.analysis_param_specs()
    filter_specs = cfg.summary_filter_specs()
    run = resolve_settings(script_name="extract_track_metrics.py",
                           param_specs=analysis_specs + filter_specs)

    chosen = run["params"]
    # analysis_specs covers all per-track keys; compute_track_metrics merges these
    # over kin_metrics.DEFAULT_PARAMS internally, so no base dict is needed here.
    params = {spec["key"]: chosen[spec["key"]] for spec in analysis_specs}
    min_total_time_s = chosen["MIN_TOTAL_TIME_S"]
    min_direction_changes = chosen["MIN_DIRECTION_CHANGES"]

    for branch_name in run["branches"]:
        branch = cfg.settings(branch_name, run["root"])

        print("\n" + "=" * 80)
        main(run["root"], branch["input_subdir"], branch["results_dir_name"],
             params, banner=branch["banner"])

        if cfg.SUMMARIZE_AFTER_EXTRACTION:
            print()
            summarize_track_metrics.main(
                branch["results_dir"],
                title_suffix=branch["title_suffix"], extra_note=branch["extra_note"],
                min_total_time_s=min_total_time_s, min_direction_changes=min_direction_changes)
        else:
            print("Run summarize_track_metrics.py to produce the summary statistics.")

    if len(run["branches"]) > 1:
        print("\n" + "=" * 80)
        print(f"Finished all branches: {', '.join(run['branches'])}")
