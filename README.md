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
> Linux-style and typically need rewriting for your machine. Stage 7 (`kinematics/`) follows
> the same hard-coded-constant convention, but its constants sit in `kin_config.py` rather
> than in the script you run.

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
`kinematics/` folder. It is also the only stage not configured by editing the script
itself: open `kinematics/kin_config.py` in a text editor and change the two hard-coded
constants at the top (there are still no command-line arguments), then run the pipeline.

```python
ROOT_DATA_DIR = Path("D:/ME/Analysis_20_09")   # folder holding segmentation_output/
BRANCH = "corrected"                            # or "uncorrected"
```

```bash
cd kinematics
python extract_track_metrics.py     # per-track CSVs, then the summary statistics
python summarize_track_metrics.py   # optional: re-summarize existing CSVs only
```

`BRANCH = "corrected"` reproduces the old `alignment_2/…_v4.py`, `"uncorrected"` the old
`alignment_1/…_v3.py`; the two write to `processed_results_2/` and `processed_results/`
respectively, so both can be produced without overwriting each other. The superseded
`alignment_1/…_v3.py` / `alignment_2/…_v4.py` remain in place until the new scripts have
been validated on the full dataset.

## Repository structure

```
segmentation/             Stages 1–2: colour-segment MHIs into track masks
blob_detection/           Stage 3 + tuning, inspection, and cleanup helpers
frame_rate/               Stage 5: acquisition frequency (shared by both branches)
alignment_1/              Uncorrected timing branch (stages 4, 6, 7 + visualisation)
alignment_2/              Corrected timing branch (canonical; stages 4, 6, 7 + visualisation)
kinematics/               Stage 7: config + metrics/grouping modules + two runnable stages
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
