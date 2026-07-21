# The authors of the code are Max Riekeles and Berke Santos. Contact: riekeles@tu-berlin.de
#
# THE ONLY FILE YOU EDIT TO RUN THE KINEMATIC ANALYSIS (stage 7).
#
# Set ROOT_DATA_DIR and BRANCH below, then run:
#
#     cd kinematics
#     python extract_track_metrics.py       # per-track metrics -> CSV, then the summary
#     python summarize_track_metrics.py     # summary only (re-run after changing grouping/filters)
#
# Both scripts read their settings from here, so the branch is stated once.
#
from pathlib import Path

from kin_metrics import DEFAULT_PARAMS

# --- WHAT TO ANALYSE -----------------------------------------------------

# Root directory containing the segmentation_output folder
ROOT_DATA_DIR = Path("/media/general-max-riekeles/MMT_3/ME/Analysis_20_09")  # Update this path

# Which alignment branch to analyse:
#   "corrected"   - alignment_2 branch, MHI-corrected timepoints (canonical;
#                   what the old final_kin_param_extraction_v4.py did)
#   "uncorrected" - alignment_1 branch, original detection timepoints
#                   (what the old final_kin_param_extraction_v3.py did)
BRANCH = "corrected"

# --- HOW TO ANALYSE ------------------------------------------------------

# Per-track analysis thresholds; see kin_metrics.DEFAULT_PARAMS for the full list.
PARAMS = dict(DEFAULT_PARAMS)
# PARAMS["MAX_SPEED"] = 60           # µm/s
# PARAMS["SMOOTHING_WINDOW"] = 1     # 1 = no smoothing
# PARAMS["ANGLE_THRESHOLD"] = 30     # degrees

# Track filters applied when grouping (summary stage only - the per-track CSV
# always keeps every track). Defaults are no-ops, matching the old scripts.
MIN_TOTAL_TIME_S = 0.0
MIN_DIRECTION_CHANGES = None

# Run the summary stage automatically at the end of extract_track_metrics.py.
SUMMARIZE_AFTER_EXTRACTION = True

# --- DERIVED SETTINGS (no need to edit below) ----------------------------

_BRANCHES = {
    "corrected": {
        "input_subdir": "alignment_converted_results_2",
        "results_dir_name": "processed_results_2",
        "banner": "Processing temporally corrected tracking data from alignment_converted_results_2/ folders",
        "title_suffix": " - TEMPORALLY CORRECTED DATA",
        "extra_note": "NOTE: Analysis performed on temporally corrected data with MHI-adjusted timepoints",
    },
    "uncorrected": {
        "input_subdir": "alignment_converted_results",
        "results_dir_name": "processed_results",
        "banner": "Processing uncorrected tracking data from alignment_converted_results/ folders",
        "title_suffix": "",
        "extra_note": "",
    },
}


def settings():
    """Return the folder names and report wording for the configured BRANCH."""
    if BRANCH not in _BRANCHES:
        raise ValueError(f"BRANCH must be one of {sorted(_BRANCHES)}, got {BRANCH!r}")
    resolved = dict(_BRANCHES[BRANCH])
    resolved["results_dir"] = ROOT_DATA_DIR / resolved["results_dir_name"]
    return resolved
