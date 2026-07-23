# The authors of the code are Max Riekeles and Berke Santos. Contact: riekeles@tu-berlin.de
#
# STRUCTURAL regression test for stage 7 (the kinematics/ folder).
#
# Runs stage 7 end-to-end on a real dataset and checks the OUTPUT FILE STRUCTURE
# it produces - not the metric values. The point is to catch plumbing
# regressions (a file that stops being written, a renamed column, broken track
# naming, a crash on real data) while you change the analysis maths, whose
# numbers are *meant* to change and so are deliberately NOT asserted here.
#
# HOW TO USE
#   Edit ROOT_DIRECTORY below to point at a dataset root on your machine (the
#   same kind of path you would type at the extract_track_metrics.py prompt),
#   then run:
#       cd kinematics
#       python test_stage7_structure.py
#   Exit code is 0 on PASS, 1 on FAIL, so it can be used as a check.
#
# WHAT IT TOUCHES
#   It only READS the stage-6 inputs (segmentation_output/.../
#   alignment_converted_results[_2]/*_converted.npy). The root may already be
#   fully processed - the test never reads, writes or deletes your real
#   processed_results[_2]/ folders. It regenerates the output into a temporary
#   directory OUTSIDE the dataset root and removes it when finished, so nothing
#   under ROOT_DIRECTORY is created or changed.
#
# WHAT IT CHECKS (per branch)
#   1. exactly one <experiment>_processed_results.csv per experiment subfolder
#      that actually contains this branch's converted inputs;
#   2. each CSV's header matches extract_track_metrics.CSV_HEADER exactly;
#   3. each row is well formed: right field count, sh_<suffix>_t<n> track name,
#      numeric metric columns;
#   4. one <experiment>_summary_statistics.txt for every experiment whose CSV
#      held groupable tracks (a shortened_ dir + an experimental condition).
#
import csv
import io
import re
import shutil
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

# Put this script's own directory (kinematics/) on sys.path so the sibling
# imports below resolve whether the test is run from the repo root or from here.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import kin_config as cfg
import extract_track_metrics as extract
import summarize_track_metrics as summarize
from kin_metrics import DEFAULT_PARAMS

# --- EDIT THIS: the dataset root to test against -------------------------
# A directory containing segmentation_output/ with the stage-6 converted
# tracks. This is the ONLY line that is machine-specific.
ROOT_DIRECTORY = "/media/general-max-riekeles/MMT_3/ME/Analysis_20_09"  # UPDATE THIS PATH

# Which branches to check. "both" mirrors a full run; drop one if you only have
# that branch's converted inputs on disk.
BRANCHES = ["corrected", "uncorrected"]

# -------------------------------------------------------------------------

# track names are sh_<suffix>_t<n>, or t<n> when there is no shortened_ dir. The
# shortened-dir token is whatever follows "shortened_" (e.g. 5seconds, 10seconds),
# so it is alphanumeric, not just digits.
TRACK_NAME_RE = re.compile(r"^(sh_\w+_)?t\d+$")

# When a systematic mismatch hits every row, cap how many per-file row failures we
# record so one bad CSV can't emit thousands of near-identical lines.
MAX_ROW_FAILURES_PER_FILE = 5
EXPECTED_HEADER = extract.CSV_HEADER.rstrip("\n")
NUM_COLUMNS = len(EXPECTED_HEADER.split(","))
# metric columns that must parse as a float (nan is allowed and parses fine)
FLOAT_COLUMNS = (4, 5, 6, 7, 8, 9)


def qualifying_experiments(seg_output, input_subdir):
    """Experiment subfolders that actually hold this branch's converted inputs."""
    experiments = set()
    for subfolder in sorted(p for p in seg_output.iterdir() if p.is_dir()):
        for aligned in subfolder.rglob(input_subdir):
            if any(aligned.glob("*_converted.npy")):
                experiments.add(subfolder.name)
                break
    return experiments


def check_csv(csv_path, failures):
    """Structural checks on one *_processed_results.csv; returns True if groupable."""
    lines = csv_path.read_text(encoding="utf-8").splitlines()
    if not lines:
        failures.append(f"{csv_path.name}: file is empty (no header)")
        return False
    if lines[0] != EXPECTED_HEADER:
        failures.append(f"{csv_path.name}: header mismatch\n"
                        f"        got : {lines[0]}\n        want: {EXPECTED_HEADER}")
        return False

    groupable = False
    row_failures = []  # collected locally so we can cap them per file
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for line_no, row in enumerate(reader, start=2):
            if len(row) != NUM_COLUMNS:
                row_failures.append(f"{csv_path.name} line {line_no}: {len(row)} fields, "
                                    f"expected {NUM_COLUMNS}")
                continue
            if not TRACK_NAME_RE.match(row[0]):
                row_failures.append(f"{csv_path.name} line {line_no}: bad track name {row[0]!r}")
            for idx in FLOAT_COLUMNS:
                try:
                    float(row[idx])
                except ValueError:
                    row_failures.append(f"{csv_path.name} line {line_no}: non-numeric value "
                                        f"{row[idx]!r} in column {idx}")
            if row[2] and row[3]:  # Shortened_Dir and Experimental_Condition both set
                groupable = True

    failures.extend(row_failures[:MAX_ROW_FAILURES_PER_FILE])
    if len(row_failures) > MAX_ROW_FAILURES_PER_FILE:
        failures.append(f"{csv_path.name}: +{len(row_failures) - MAX_ROW_FAILURES_PER_FILE} "
                        f"more row-level problem(s) not shown")
    return groupable


def run_branch(branch_name, root, base_tmp, results):
    """Run stage 7 for one branch into a temp dir and check its output structure."""
    branch = cfg.settings(branch_name, root)
    expected = qualifying_experiments(root / "segmentation_output", branch["input_subdir"])

    if not expected:
        print(f"[SKIP] {branch_name}: no experiments contain "
              f"{branch['input_subdir']}/*_converted.npy")
        results.append((branch_name, "SKIP"))
        return

    out_dir = base_tmp / f"{branch_name}_results"
    failures = []

    # main() writes to root / results_dir_name; passing an absolute path makes
    # that join resolve to out_dir, so nothing is written under the dataset root.
    # stage 7 is chatty - capture its output and only show it if the branch fails.
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            extract.main(root, branch["input_subdir"], str(out_dir),
                         dict(DEFAULT_PARAMS), banner=None)
            summarize.main(out_dir, title_suffix=branch["title_suffix"],
                           extra_note=branch["extra_note"],
                           min_total_time_s=cfg.MIN_TOTAL_TIME_S,
                           min_direction_changes=cfg.MIN_DIRECTION_CHANGES)
    except Exception as exc:
        # stage 7 is chatty; on a crash only the tail is useful for the traceback context.
        print(f"[FAIL] {branch_name}: stage 7 raised {type(exc).__name__}: {exc}")
        tail = buf.getvalue().splitlines()[-15:]
        if tail:
            print("    last stage-7 output:")
            for line in tail:
                print(f"      {line}")
        results.append((branch_name, "FAIL"))
        return

    csvs = {p.name[:-len("_processed_results.csv")]: p
            for p in out_dir.glob("*_processed_results.csv")}
    produced = set(csvs)

    # 1) one CSV per qualifying experiment, no more, no fewer
    for missing in sorted(expected - produced):
        failures.append(f"missing CSV for experiment {missing}")
    for unexpected in sorted(produced - expected):
        failures.append(f"unexpected CSV for {unexpected}")

    # 2 + 3) CSV structure, and 4) a matching summary file
    summaries = 0
    for exp, csv_path in sorted(csvs.items()):
        groupable = check_csv(csv_path, failures)
        summary = out_dir / f"{exp}_summary_statistics.txt"
        if summary.exists():
            summaries += 1
            if summary.stat().st_size == 0:
                failures.append(f"empty summary file for {exp}")
        elif groupable:
            failures.append(f"missing summary for {exp} (its CSV had groupable tracks)")

    status = "PASS" if not failures else "FAIL"
    print(f"[{status}] {branch_name}: {len(produced)} experiment CSV(s), {summaries} summary file(s)")
    # Only the structural failures are printed - not stage 7's (voluminous) stdout,
    # which would bury them.
    for msg in failures:
        print(f"    - {msg}")
    results.append((branch_name, status))


def main():
    root = Path(ROOT_DIRECTORY).expanduser()
    if not (root / "segmentation_output").is_dir():
        sys.exit(f"ERROR: {root} has no segmentation_output/ - set ROOT_DIRECTORY correctly.")

    base_tmp = Path(tempfile.mkdtemp(prefix="me_stage7_structure_"))
    print(f"Testing stage-7 output structure against: {root}")
    print(f"(temporary output in {base_tmp}, removed at the end)\n")

    results = []
    try:
        for branch_name in BRANCHES:
            run_branch(branch_name, root, base_tmp, results)
    finally:
        shutil.rmtree(base_tmp, ignore_errors=True)

    print("\n" + "=" * 60)
    for branch_name, status in results:
        print(f"  {branch_name}: {status}")
    failed = [b for b, status in results if status == "FAIL"]
    if failed:
        print(f"RESULT: FAIL ({', '.join(failed)})")
        sys.exit(1)
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
