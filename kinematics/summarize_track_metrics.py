# The authors of the code are Max Riekeles and Berke Santos. Contact: riekeles@tu-berlin.de
#
# STAGE 7b of the pipeline - group statistics over the per-track metrics.
#
# Reads the CSVs written by extract_track_metrics.py and writes one
# <experiment>_summary_statistics.txt per experiment subfolder, grouping tracks
# by shortened_ directory and experimental condition (and pooling across
# shortened_ directories under "combined").
#
# This step touches no .npy files, so grouping rules, track filters and the
# report layout can be iterated in seconds without re-running the expensive
# extraction pass.
#
# Input:  <root>/processed_results[_2]/<experiment>_processed_results.csv
# Output: <root>/processed_results[_2]/<experiment>_summary_statistics.txt
#
import csv
from pathlib import Path

from kin_grouping import SUMMARY_METRIC_ORDER, group_tracks, write_summary_file

# CSV column -> metric name used by kin_grouping
CSV_METRIC_COLUMNS = {
    "Mean_Velocity_um_s": "mean_velocity",
    "Speed_Dynamic_percent": "speed_dynamic",
    "Straightness_Index": "straightness_index",
    "Direction_Change_Rate": "direction_change_rate",
}


def read_track_rows(csv_path, min_total_time_s=0.0, min_direction_changes=None):
    """
    Read one *_processed_results.csv into the row dicts group_tracks() expects.

    Optional filters (both no-ops by default, i.e. same behaviour as the old
    combined script):
        min_total_time_s      : drop tracks shorter than this duration
        min_direction_changes : drop tracks with fewer direction changes
    """
    rows = []
    dropped = 0

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        missing = [c for c in list(CSV_METRIC_COLUMNS) + ["Shortened_Dir", "Experimental_Condition"]
                   if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(
                f"{csv_path.name} is missing column(s) {missing}. This file was probably written by "
                "the old final_kin_param_extraction_v3/v4 script - re-run extract_track_metrics.py."
            )

        for record in reader:
            total_time = float(record["Total_Time_s"])
            num_changes = int(record["Num_Direction_Changes"])
            if total_time < min_total_time_s:
                dropped += 1
                continue
            if min_direction_changes is not None and num_changes < min_direction_changes:
                dropped += 1
                continue

            row = {
                "shortened_dir": record["Shortened_Dir"],
                "experimental_condition": record["Experimental_Condition"],
            }
            for column, metric in CSV_METRIC_COLUMNS.items():
                row[metric] = float(record[column])
            rows.append(row)

    return rows, dropped


def main(results_dir, title_suffix="", extra_note="", min_total_time_s=0.0, min_direction_changes=None):
    csv_files = sorted(results_dir.glob("*_processed_results.csv"))

    if not csv_files:
        print(f"No *_processed_results.csv files found in {results_dir}")
        print("Run extract_track_metrics.py first.")
        return

    for csv_path in csv_files:
        subfolder_name = csv_path.name[:-len("_processed_results.csv")]
        print(f"Summarizing {subfolder_name}...")

        try:
            rows, dropped = read_track_rows(csv_path, min_total_time_s, min_direction_changes)
        except ValueError as e:
            print(f"  ERROR: {e}")
            continue

        if dropped:
            print(f"  Filtered out {dropped} track(s) by the configured track filters")

        grouped_stats = group_tracks(rows)
        # group_tracks always adds 'combined'; nothing to report if that is the only key
        if len(grouped_stats) <= 1 and not grouped_stats.get('combined'):
            print(f"  WARNING: no tracks with both a shortened_ directory and an experimental "
                  f"condition in {csv_path.name} - no summary written")
            continue

        summary_file = results_dir / f'{subfolder_name}_summary_statistics.txt'
        write_summary_file(summary_file, grouped_stats, subfolder_name,
                           title_suffix=title_suffix, extra_note=extra_note)
        print(f"  Summary statistics saved to: {summary_file.name}")

    print(f"\nSummaries written to: {results_dir}")


if __name__ == "__main__":
    # --- CONFIGURATION ---------------------------------------------------
    # Root directory containing the processed_results[_2] folder
    ROOT_DATA_DIR = Path("/media/general-max-riekeles/MMT_3/ME/Analysis_20_09")  # Update this path

    # Must match the BRANCH used in extract_track_metrics.py
    BRANCH = "corrected"

    # Track filters applied before grouping. Defaults are no-ops and reproduce
    # the old scripts exactly; raise them to exclude short/immobile tracks.
    MIN_TOTAL_TIME_S = 0.0
    MIN_DIRECTION_CHANGES = None

    if BRANCH == "corrected":
        RESULTS_DIR_NAME = "processed_results_2"
        TITLE_SUFFIX = " - TEMPORALLY CORRECTED DATA"
        EXTRA_NOTE = "NOTE: Analysis performed on temporally corrected data with MHI-adjusted timepoints"
    elif BRANCH == "uncorrected":
        RESULTS_DIR_NAME = "processed_results"
        TITLE_SUFFIX = ""
        EXTRA_NOTE = ""
    else:
        raise ValueError(f"BRANCH must be 'corrected' or 'uncorrected', got {BRANCH!r}")
    # ---------------------------------------------------------------------

    main(ROOT_DATA_DIR / RESULTS_DIR_NAME,
         title_suffix=TITLE_SUFFIX, extra_note=EXTRA_NOTE,
         min_total_time_s=MIN_TOTAL_TIME_S, min_direction_changes=MIN_DIRECTION_CHANGES)
