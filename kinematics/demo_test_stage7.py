# The authors of the code are Max Riekeles and Berke Santos. Contact: riekeles@tu-berlin.de
#
# DEMO / self-check for the stage-7 structural test (test_stage7_structure.py).
#
# The structural test itself needs a REAL dataset root on disk, which makes it
# awkward to convince yourself the test is actually doing its job. This demo
# needs NO real data: it fabricates a tiny synthetic segmentation_output/ tree in
# a temp folder and drives the *real* test functions against it, so you can watch
# the test both PASS on good data and CATCH deliberately broken output.
#
#     cd kinematics
#     python demo_test_stage7.py
#
# It writes only into temporary folders (removed at the end) and touches nothing
# in the repo or under any real dataset. Exit code is 0 if the test behaved
# correctly in every case, 1 otherwise.
#
# Two parts:
#   PART A - positive, end-to-end. Build a valid synthetic dataset for both
#            branches and run the test's run_branch(); expect PASS for each.
#   PART B - negative, checker-level. Hand-write good and broken CSVs and feed
#            them to the test's check_csv(); expect the broken ones to be caught.
#
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np

# Put kinematics/ on sys.path so importing the test (and its siblings) works
# whether this is run from the repo root or from inside kinematics/.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_stage7_structure as struct  # the real test - we reuse its functions

# ---------------------------------------------------------------------------
# Synthetic dataset definition (Part A)
# ---------------------------------------------------------------------------

SHORTENED_DIR = "shortened_5seconds"

# experiment subfolder -> recording subsubfolders (pattern-correct so that
# extract_sample_group() yields a condition and the tracks are groupable).
EXPERIMENTS = {
    "Copper_1": [
        "ecoli_control_24h_sample1_rec1_changed",
        "ecoli_control_24h_sample2_rec1_changed",
    ],
    "Lead_2": [
        "ecoli_lead_24h_sample1_rec1_changed",
    ],
}

# Both branches' input folders, so a single synthetic tree qualifies for both.
INPUT_SUBDIRS = ("alignment_converted_results", "alignment_converted_results_2")

TRACKS_PER_RECORDING = 2


def make_track(n_points=25, dt=0.1, step=1.0, wobble=1.0):
    """A zig-zag track as an (N, 3) array of [x_um, y_um, t_s].

    Steps are ~sqrt(step^2 + wobble^2)/dt um/s (~14 um/s here) - safely under the
    60 um/s speed filter - and the alternating y makes plenty of real direction
    changes, so compute_track_metrics() analyses it instead of skipping it.
    """
    idx = np.arange(n_points)
    t = idx * dt
    x = idx * step
    y = (idx % 2) * wobble
    return np.column_stack([x, y, t]).astype(float)


def build_synthetic_root(root):
    """Create segmentation_output/.../*_converted.npy for every branch."""
    seg = root / "segmentation_output"
    for experiment, recordings in EXPERIMENTS.items():
        for recording in recordings:
            rec_dir = seg / experiment / SHORTENED_DIR / recording
            for input_subdir in INPUT_SUBDIRS:
                aligned = rec_dir / input_subdir
                aligned.mkdir(parents=True, exist_ok=True)
                for k in range(1, TRACKS_PER_RECORDING + 1):
                    track = make_track(n_points=20 + k, step=1.0 + 0.1 * k)
                    np.save(aligned / f"aligned_blobs_t{k}_converted.npy", track)


def part_a():
    """Run the real structural test on synthetic data; expect PASS per branch."""
    print("PART A - end-to-end structural test on synthetic data")
    print("-" * 60)
    root = Path(tempfile.mkdtemp(prefix="me_demo_data_"))
    base_tmp = Path(tempfile.mkdtemp(prefix="me_demo_out_"))
    try:
        build_synthetic_root(root)
        results = []
        for branch_name in ("corrected", "uncorrected"):
            struct.run_branch(branch_name, root, base_tmp, results)
        ok = bool(results) and all(status == "PASS" for _, status in results)
        print(f"  => Part A {'OK' if ok else 'PROBLEM'}: "
              f"{', '.join(f'{b}={s}' for b, s in results)}")
        return ok
    finally:
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(base_tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# Checker-level cases (Part B)
# ---------------------------------------------------------------------------

HDR = struct.EXPECTED_HEADER
GOOD_ROW = ('sh_5seconds_t1,ecoli_control_24h_sample1_rec1,shortened_5seconds,'
            'ecoli_control_24h,10.5,2.1,20.0,0.85,1.5,1.9,3,"0.1;0.5;1.2"')

# name, csv text, expect_failure. The good case must produce ZERO failures; the
# rest must each produce at least one - that is the whole point of the test.
CASES = [
    ("good CSV",
     HDR + "\n" + GOOD_ROW,
     False),
    ("wrong header",
     "Not,The,Right,Header\n" + GOOD_ROW,
     True),
    ("bad track name",
     HDR + "\n" + GOOD_ROW.replace("sh_5seconds_t1", "banana", 1),
     True),
    ("non-numeric metric",
     HDR + "\n" + GOOD_ROW.replace(",10.5,", ",abc,", 1),
     True),
    ("too few fields",
     HDR + "\n" + "sh_5seconds_t1,ecoli_control_24h_sample1_rec1,shortened_5seconds",
     True),
]


def part_b():
    """Feed good/broken CSVs to check_csv(); good -> 0 failures, broken -> >=1."""
    print("\nPART B - check_csv() catches broken output")
    print("-" * 60)
    tmp = Path(tempfile.mkdtemp(prefix="me_demo_csv_"))
    all_ok = True
    try:
        for i, (name, text, expect_failure) in enumerate(CASES):
            csv_path = tmp / f"case_{i}_processed_results.csv"
            csv_path.write_text(text, encoding="utf-8")
            failures = []
            struct.check_csv(csv_path, failures)
            got_failure = len(failures) > 0
            ok = (got_failure == expect_failure)
            all_ok = all_ok and ok
            verdict = "OK" if ok else "PROBLEM"
            want = "should FAIL" if expect_failure else "should PASS clean"
            print(f"  {name:<20} {want:<18} -> "
                  f"{len(failures)} failure(s)  [{verdict}]")
        print(f"  => Part B {'OK' if all_ok else 'PROBLEM'}")
        return all_ok
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    print("Demo of the stage-7 structural test - no real data required.\n")
    a_ok = part_a()
    b_ok = part_b()
    print("\n" + "=" * 60)
    if a_ok and b_ok:
        print("DEMO RESULT: PASS - the structural test passes on good data "
              "and catches broken output.")
        sys.exit(0)
    print("DEMO RESULT: FAIL - the structural test did not behave as expected "
          "(see the [PROBLEM] lines above).")
    sys.exit(1)


if __name__ == "__main__":
    main()
