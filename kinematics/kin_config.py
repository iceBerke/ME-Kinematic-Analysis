# The authors of the code are Max Riekeles and Berke Santos. Contact: riekeles@tu-berlin.de
#
# Analysis settings for the kinematic analysis (stage 7).
#
# NOTE: the root data directory and the alignment branch are NOT here - they are
# machine-specific, so hard-coding them would put one person's paths in the
# repository. They are asked for when you run the analysis (or passed on the
# command line); see kin_prompt.py. This file holds only settings that are the
# same on every machine.
#
#     cd kinematics
#     python extract_track_metrics.py       # asks for path + branch, then runs everything
#     python summarize_track_metrics.py     # summary only (after changing the settings below)
#
from kin_metrics import DEFAULT_PARAMS

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

# The values above are the DEFAULTS. When the analysis is run interactively,
# each parameter is asked for in the terminal with its value here pre-filled
# (press Enter to keep it); non-interactive/argument-driven runs use them as-is.
# These two builders describe the parameters to the prompt (kin_prompt.py). The
# offered default always comes from the constants above - parameters are not
# remembered between runs (only the root directory and branch are).

def analysis_param_specs():
    """Per-track analysis parameters asked for by stage 7a (extract_track_metrics.py)."""
    return [
        {"key": "MAX_SPEED", "label": "Maximum speed (velocities above this are dropped)",
         "unit": "um/s", "kind": "float", "min": 0, "min_exclusive": True,
         "default": PARAMS["MAX_SPEED"]},
        {"key": "SMOOTHING_WINDOW", "label": "Smoothing window (1 = no smoothing)",
         "kind": "int", "min": 1, "default": PARAMS["SMOOTHING_WINDOW"]},
        {"key": "ANGLE_THRESHOLD", "label": "Direction-change angle threshold",
         "unit": "deg", "kind": "float", "min": 0, "default": PARAMS["ANGLE_THRESHOLD"]},
        {"key": "MIN_DISPLACEMENT", "label": "Minimum displacement (noise floor)",
         "unit": "um", "kind": "float", "min": 0, "default": PARAMS["MIN_DISPLACEMENT"]},
        {"key": "MIN_TIME_BETWEEN_DIRECTION_CHANGES",
         "label": "Minimum time between direction changes",
         "unit": "s", "kind": "float", "min": 0,
         "default": PARAMS["MIN_TIME_BETWEEN_DIRECTION_CHANGES"]},
    ]


def summary_filter_specs():
    """Summary-stage track filters asked for by 7a->7b and standalone 7b."""
    return [
        {"key": "MIN_TOTAL_TIME_S", "label": "Minimum total track time to include a track",
         "unit": "s", "kind": "float", "min": 0, "default": MIN_TOTAL_TIME_S},
        {"key": "MIN_DIRECTION_CHANGES",
         "label": "Minimum direction changes to include a track (none = keep all)",
         "kind": "int_or_none", "min": 0, "default": MIN_DIRECTION_CHANGES},
    ]

# --- BRANCH DEFINITIONS (no need to edit below) --------------------------

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


def settings(branch, root_data_dir):
    """
    Return the folder names and report wording for one alignment branch.

    branch: "corrected" (alignment_2, canonical) or "uncorrected" (alignment_1).
    """
    if branch not in _BRANCHES:
        raise ValueError(f"branch must be one of {sorted(_BRANCHES)}, got {branch!r}")
    resolved = dict(_BRANCHES[branch])
    resolved["results_dir"] = root_data_dir / resolved["results_dir_name"]
    return resolved
