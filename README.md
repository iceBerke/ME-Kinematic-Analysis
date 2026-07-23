# ME — Kinematic Analysis of Bacterial Motility

Image-analysis pipeline for the "ME" paper (Max Riekeles & Berke Santos, TU Berlin —
riekeles@tu-berlin.de). It detects and tracks motile bacteria in time-lapse microscopy
recordings, aligns detections to their motion tracks, and extracts per-track **kinematic
parameters** (velocity, straightness, direction-change rate, speed dynamics) grouped by
experimental condition.

Experiments are organised by exposure condition (e.g. `Lead_1`, `Copper_3`, `Nickel_1`,
`Zinc_3`) with `ecoli_control_*` baselines.

> These are standalone batch scripts, not an installable package. There is **no CLI** —
> each script is run directly (`python <script>.py`) after editing the hard-coded
> `root_directory` (and parameters) near the bottom of the file. Paths in the scripts are
> Linux-style and typically need rewriting for your machine. Stage 7 (`kinematics/`) is the
> exception: it **asks** for the data path, the branch, and the analysis parameters when you
> run it, so no machine-specific path is stored in the repository.

## Installation

```bash
pip install -r requirements.txt
```

Requires Python 3.9+ and the packages in `requirements.txt` (OpenCV, NumPy, SciPy,
scikit-image, scikit-learn, matplotlib, Pillow, psutil, python-dateutil).

## Data layout

The scripts operate on a `root_directory` that holds both the raw data and a parallel
`segmentation_output/` tree mirroring it. The hierarchy is always three levels:

```
<experiment>/            e.g. Lead_1, Copper_3, Nickel_1
  <shortened_N>/         time-series interval, e.g. shortened_5seconds
    <recording>/         individual recording session (often suffixed "_changed")
      raw/               source microscopy frames (*.tif)
      validate/          coloured MHI (*_color.tif) + MHI.npy
```

Processing artifacts are written into the mirrored
`segmentation_output/<experiment>/<shortened_N>/<recording>/`.

An **MHI** (Motion History Image) encodes, per pixel, the time a bacterium moved through
it. Coloured MHIs are produced upstream by an external tool (there is no MHI-generation
script here); this pipeline consumes them.

## Paths to edit before running

There is no config file: each script hard-codes its path(s) as a constant near the bottom
(inside `if __name__ == "__main__":`) or, for a few, at the top of the file. The committed
values are the original authors' Linux paths — **rewrite them for your machine before
running.** The variable name and what it should point to differ from script to script, so
the table lists every path a user edits. (Archived scripts in `archive/` are superseded and
not meant to be run.)

> **Stage 7 is the exception:** `kinematics/extract_track_metrics.py` and
> `summarize_track_metrics.py` *ask* for the path at runtime (or take it as a command-line
> argument), so there is nothing to edit in them. Their analysis *values* still have code
> defaults — per-track thresholds in `kinematics/kin_metrics.py` (`DEFAULT_PARAMS`), the two
> summary filters in `kinematics/kin_config.py`.

| Script | Variable to edit | Point it at |
|---|---|---|
| `segmentation/track_segmentation_v4.py` | `root_directory` | dataset root |
| `segmentation/npy_conversion_v1.py` | `root_folder` | the `segmentation_output/` directory |
| `blob_detection/blob_detection_v3_memory_optimized.py` | `root_directory` | dataset root |
| `blob_detection/blob_parameters_check_v3.py` | `image_path` | a single `raw/*.tif` frame |
| `blob_detection/check_blobs_npy.py` | `NPY_FILE_PATH` | a single `blobs_*.npy` |
| `blob_detection/blob_detection_cleanup.py` | `segmentation_output_path` | the `segmentation_output/` directory |
| `frame_rate/frame_rate_v1.py` | `root_directory` | dataset root |
| `alignment_1/blob_mhi_tracks_alignment_v4.py`, `alignment_2/blob_mhi_tracks_alignment_v5.py` | `root_directory` | dataset root |
| `alignment_1/mhi_overlay_v2.py`, `alignment_2/mhi_overlay_v3.py` | `segmentation_output_path` | the `segmentation_output/` directory |
| `alignment_1/time_coordinates_conversions_v2.py`, `alignment_2/time_coordinates_conversions_v3.py` | `ROOT_DIRECTORY` | dataset root |
| `alignment_1/mhi_overlay_copies_v1.py`, `alignment_2/mhi_overlay_copies_v2.py` | `root_directory_path` | dataset root |
| `kinematics/test_stage7_structure.py` | `ROOT_DIRECTORY` | dataset root (structural regression test) |
| `segmentation_checks/error_analysis_v1.py`, `error_analysis_v3.py` | `root_folder` | one experiment folder under `segmentation_output/` |
| `segmentation_corrections/correction_v1.py`, `_v2.py`, `_v3.py` | `image_path` | a single track PNG (`t<N>.png`) |
| `segmentation_corrections/correction_v4.py` | `output_file` (plus the hand-listed input PNGs in the script) | the merged-output PNG path |
| `utils/copy_rename_MHIs.py` | `parent_directory` | the folder of `.tif`s to copy |
| `utils/copy_color_mhis_and_normal_mhis.py` | `src_directory`, `dest_directory` | source and destination folders |

## Pipeline

Run the stages in order. Detected-blob arrays are `(n, 6)` = `[x, y, timepoint, area,
brightness, solidity]`, in a 2048×2048 coordinate space (every image is resized to 2048²
before detection); real-world units are applied only at the conversion stage.

| # | Stage | Script |
|---|-------|--------|
| 1 | Track segmentation | `segmentation/track_segmentation_v4.py` |
| 2 | Track PNG → NPY masks | `segmentation/npy_conversion_v1.py` |
| 3 | Blob detection | `blob_detection/blob_detection_v3_memory_optimized.py` |
| 4 | MHI–track–blob alignment | `alignment_2/…_blob_mhi_tracks_alignment_v5.py` |
| 5 | Acquisition frequency | `frame_rate/frame_rate_v1.py` |
| 6 | Pixel→µm / frame→s conversion | `alignment_2/…_time_coordinates_conversions_v3.py` |
| 7 | Kinematic parameter extraction | `kinematics/extract_track_metrics.py` (runs the summary too) |

Tune blob-detection parameters per experiment with
`blob_detection/blob_parameters_check_v3.py` (single-image visual
check) before running stage 3.

### Two alignment branches

Stages 4, 6 and 7 exist in two parallel branches that differ only in **timing**:

- **`alignment_2/` (corrected — canonical):** at alignment, each blob's timepoint is
  replaced with the MHI movement-time at its location, fixing high-velocity artifacts.
  This branch's output feeds the final results.
- **`alignment_1/` (uncorrected):** keeps original detection timepoints. Kept for
  comparison against the corrected results.

Each branch is a self-contained sequence: align → overlay (visualisation) → convert →
overlay-collect → kinematics.

Stage 7 is the exception: the two branch scripts have been replaced by the shared
`kinematics/` folder, and it is the only stage that **asks** for its settings instead of
being edited — the data path and the branch are specific to your machine (so they are not
stored in the repository), and the analysis parameters are prompted too, pre-filled from
`kin_config.py`.

```bash
cd kinematics
python extract_track_metrics.py     # per-track CSVs, then the summary statistics
python summarize_track_metrics.py   # optional: re-summarize existing CSVs only
```

```
=== Kinematic analysis (stage 7) ===

Root data directory (must contain segmentation_output/; q to quit)
  [D:\ME\Analysis_20_09]:            <- last used; press Enter to accept

Which alignment branch?
  1) corrected    MHI-corrected timepoints (canonical)  -> processed_results_2/
  2) uncorrected  original detection timepoints         -> processed_results/
  3) both         runs 1 then 2
  [1]:

Analysis parameters (press Enter to keep the shown default):
  Maximum speed (um/s)
    [60]:                             <- each parameter pre-filled from the code defaults
  Smoothing window (1 = no smoothing)
    [1]:
  ... (angle threshold, min displacement, min time between direction changes,
       min total track time, min direction changes)
```

`corrected` reproduces the old `alignment_2/…_v4.py`, `uncorrected` the old
`alignment_1/…_v3.py`; the two write to `processed_results_2/` and `processed_results/`
respectively, so `both` runs them in one go without overwriting anything. Your last
**root and branch** are remembered in `kinematics/.kin_last_run.json` (gitignored) and
offered as the defaults next time; the analysis parameters are always offered from the
code defaults, not from the previous run.

After root and branch, every analysis parameter is asked for with its code default
pre-filled — press Enter to keep it, or type a new value for this run. The
`summarize_track_metrics.py` stage only asks for the two summary track filters (the
per-track parameters are already baked into the CSVs).

For unattended runs, pass root and branch as arguments; nothing is asked and the
parameters fall back to their code defaults:

```bash
python extract_track_metrics.py "D:/ME/Analysis_20_09" both
```

Those code defaults are the values the prompts pre-fill (and the values unattended runs
use). They live in two places: the **per-track thresholds** (speed, angle, smoothing,
displacement, timing) in `kinematics/kin_metrics.py` (`DEFAULT_PARAMS`), and the **two
summary track filters** in `kinematics/kin_config.py`. Edit them there to change what is
offered. The superseded per-branch scripts (`final_kin_param_extraction_v3.py` /
`_v4.py`) have been validated against the new stage and moved to `archive/`.

**Regression test.** `kinematics/test_stage7_structure.py` runs stage 7 against a real
dataset and checks the *structure* of the output it produces — the right set of CSV and
summary files, correct CSV columns, well-formed rows (field count, `sh_<suffix>_t<n>` track
names such as `sh_5seconds_t1`, numeric metric columns) — but not the metric values, so it
stays valid as you change the analysis. Point its top-of-file `ROOT_DIRECTORY` at a
dataset root and run `python test_stage7_structure.py`; it writes into a temporary folder
outside your data (leaving any existing `processed_results[_2]/` untouched) and cleans up,
exiting 0 on pass and 1 on failure.

## Repository structure

```
segmentation/             Stages 1–2: colour-segment MHIs into track masks
blob_detection/           Stage 3 + tuning, inspection, and cleanup helpers
frame_rate/               Stage 5: acquisition frequency (shared by both branches)
alignment_1/              Uncorrected timing branch (stages 4, 6 + visualisation)
alignment_2/              Corrected timing branch (canonical; stages 4, 6 + visualisation)
kinematics/               Stage 7: prompt + config + metrics/grouping modules + two stages
segmentation_checks/      Batch QA of segmentation output (fragmentation / multi-track)
segmentation_corrections/ Manual per-image track fix-ups (split / merge)
utils/                    MHI file-management helpers
archive/                  Superseded script versions, kept for history
```

See `CLAUDE.md` for a detailed developer reference (per-script behaviour, folder
conventions, and version history).

## Authors

Max Riekeles and Berke Santos, TU Berlin. Contact: riekeles@tu-berlin.de.
Scripts were developed with AI assistance.
