# The authors of the code are Max Riekeles and Berke Santos. Contact: riekeles@tu-berlin.de
#
# Terminal interaction for the kinematic analysis (stage 7): asks for the root
# data directory and which alignment branch to run. Kept separate from the
# analysis code so the stages stay importable and testable without a terminal.
#
# The two answers are machine-specific, so they are NOT hard-coded anywhere in
# the repository (unlike every other stage of this pipeline). They come from,
# in order of precedence:
#   1. command-line arguments:  python extract_track_metrics.py <root> <branch>
#   2. an interactive prompt, pre-filled with the values from the last run
#      (remembered in .kin_last_run.json next to this file, which is gitignored)
#   3. nothing - if there is no terminal to ask, the script exits with an
#      explanation instead of hanging on stdin that will never arrive.
#
import json
import sys
from pathlib import Path

# Branch choice -> the branches to run, in order.
BRANCH_CHOICES = {
    "corrected": ["corrected"],
    "uncorrected": ["uncorrected"],
    "both": ["corrected", "uncorrected"],
}

# Accepted shorthands for the branch prompt / command line
BRANCH_ALIASES = {
    "1": "corrected", "c": "corrected", "corrected": "corrected",
    "2": "uncorrected", "u": "uncorrected", "uncorrected": "uncorrected",
    "3": "both", "b": "both", "both": "both",
}

LAST_RUN_FILE = Path(__file__).parent / ".kin_last_run.json"

USAGE = """\
Usage:
  python {script}                      ask for the settings interactively
  python {script} <root> [<branch>]    supply them directly (no prompting)

  <root>    directory containing the segmentation_output/ folder
  <branch>  corrected | uncorrected | both   (default: corrected)

Examples:
  python {script} "D:/ME/Analysis_20_09" corrected
  python {script} /media/general-max-riekeles/MMT_3/ME/Analysis_20_09 both\
"""


# --- remembering the last run --------------------------------------------

def load_last_run():
    """Return {'root': str, 'branch': str} from the last run, or {} if unavailable."""
    try:
        with open(LAST_RUN_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_last_run(root, branch_choice):
    """Remember this run's settings as defaults for the next one (best effort)."""
    try:
        with open(LAST_RUN_FILE, "w", encoding="utf-8") as f:
            json.dump({"root": str(root), "branch": branch_choice}, f, indent=2)
    except OSError:
        pass  # a non-writable folder must not break the analysis


# --- parsing / validation -------------------------------------------------

def clean_path(text):
    """
    Turn typed or pasted text into a Path.

    Tolerates what a terminal paste actually contains: surrounding quotes (the
    VSCode/Explorer 'Copy as path' commands add them), stray whitespace, and a
    '~' home shortcut. Both slash directions work on Windows.
    """
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        text = text[1:-1].strip()
    return Path(text).expanduser()


def path_problem(root, require_segmentation_output=True):
    """Return a human-readable problem with this root directory, or None if it is usable."""
    if not root.exists():
        return "that path does not exist"
    if not root.is_dir():
        return "that path is a file, not a directory"
    if require_segmentation_output and not (root / "segmentation_output").is_dir():
        return "no segmentation_output/ folder inside it"
    return None


def parse_branch(text):
    """Map typed input to a branch choice, or None if it is not recognised."""
    return BRANCH_ALIASES.get(text.strip().lower())


def is_interactive():
    try:
        return sys.stdin is not None and sys.stdin.isatty()
    except (AttributeError, ValueError):
        return False


# --- prompts --------------------------------------------------------------

def _ask(prompt, default=None):
    """Read one line; blank input returns the default. Ctrl-C/Ctrl-D exits cleanly."""
    suffix = f"\n  [{default}]: " if default else "\n  : "
    try:
        answer = input(prompt + suffix).strip()
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        sys.exit(1)
    return answer or (str(default) if default is not None else "")


def prompt_root(default=None, require_segmentation_output=True):
    """Ask for the root data directory until a usable one is given."""
    while True:
        answer = _ask("Root data directory (must contain segmentation_output/; q to quit)", default)
        if not answer:
            print("  Please enter a path.\n")
            continue
        if answer.strip().lower() == "q":
            print("Cancelled.")
            sys.exit(1)

        root = clean_path(answer)
        problem = path_problem(root, require_segmentation_output)
        if problem is None:
            return root
        print(f"  Cannot use {root} - {problem}.\n")


def prompt_branch(default="corrected"):
    """Ask which alignment branch(es) to process."""
    print("\nWhich alignment branch?")
    print("  1) corrected    MHI-corrected timepoints (canonical)  -> processed_results_2/")
    print("  2) uncorrected  original detection timepoints         -> processed_results/")
    print("  3) both         runs 1 then 2")
    while True:
        answer = _ask("Choice", default)
        choice = parse_branch(answer)
        if choice:
            return choice
        print("  Please answer 1, 2 or 3 (or corrected / uncorrected / both).\n")


# --- analysis parameters --------------------------------------------------
#
# Each stage passes resolve_settings a list of "param specs" describing the
# numeric analysis settings it wants asked for. A spec is a dict:
#   {"key", "label", "default", "kind", ["unit", "min", "min_exclusive"]}
# 'kind' is 'float', 'int', or 'int_or_none' (the last also accepts 'none' to
# disable the setting). The offered default is always the spec's 'default'
# (i.e. the value in kin_config.py) - parameters are deliberately NOT
# remembered between runs, unlike the root directory and branch.

def _fmt_value(value):
    """Human-readable form of a parameter value (None shows as 'none')."""
    return "none" if value is None else str(value)


def _parse_param(text, spec):
    """
    Parse one typed parameter value against its spec.

    Returns (ok, value, error_message); error_message is None when ok is True.
    """
    kind = spec["kind"]
    text = text.strip()
    if kind == "int_or_none" and text.lower() in ("none", "off", "na", "null", "-"):
        return True, None, None
    try:
        value = int(text) if kind in ("int", "int_or_none") else float(text)
    except ValueError:
        if kind == "int_or_none":
            return False, None, "enter a whole number, or 'none' to disable it"
        if kind == "int":
            return False, None, "enter a whole number"
        return False, None, "enter a number"
    minimum = spec.get("min")
    if minimum is not None:
        if spec.get("min_exclusive"):
            if not value > minimum:
                return False, None, f"must be greater than {minimum}"
        elif not value >= minimum:
            return False, None, f"must be at least {minimum}"
    return True, value, None


def _prompt_one_param(spec):
    """Ask for a single parameter, re-asking on bad input. Blank keeps the default."""
    label = f"{spec['label']} ({spec['unit']})" if spec.get("unit") else spec["label"]
    default_str = _fmt_value(spec["default"])
    while True:
        try:
            raw = input(f"  {label}\n    [{default_str}]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled.")
            sys.exit(1)
        if raw == "":
            return spec["default"]
        ok, value, error = _parse_param(raw, spec)
        if ok:
            return value
        print(f"    {error}.\n")


def prompt_params(param_specs):
    """Prompt for each parameter in turn; returns {key: value}. Blank keeps the default."""
    if not param_specs:
        return {}
    print("\nAnalysis parameters (press Enter to keep the shown default):")
    return {spec["key"]: _prompt_one_param(spec) for spec in param_specs}


def param_defaults(param_specs):
    """Every spec's default value, without prompting (used for unattended runs)."""
    return {spec["key"]: spec["default"] for spec in (param_specs or [])}


def _print_params(param_specs, params):
    """Echo the parameter values that will be used, one per line."""
    for spec in (param_specs or []):
        unit = f" {spec['unit']}" if spec.get("unit") else ""
        print(f"  {spec['key']:<38} {_fmt_value(params[spec['key']])}{unit}")


def confirm(root, choice, param_specs=None, params=None):
    print("\n" + "-" * 60)
    print(f"Root data directory : {root}")
    print(f"Branch(es) to run   : {', '.join(BRANCH_CHOICES[choice])}")
    if param_specs:
        print("Parameters          :")
        _print_params(param_specs, params)
    print("-" * 60)
    answer = _ask("Proceed?", "Y").strip().lower()
    if answer not in ("y", "yes"):
        print("Cancelled.")
        sys.exit(1)


# --- entry point ----------------------------------------------------------

def resolve_settings(argv=None, script_name="extract_track_metrics.py",
                     require_segmentation_output=True, title="Kinematic analysis (stage 7)",
                     param_specs=None):
    """
    Work out the root directory, branches and analysis parameters for this run.

    param_specs: optional list of parameter specs (see the "analysis parameters"
    section above). When given and the run is interactive, each is asked for
    with its default pre-filled; otherwise the defaults are used unchanged.

    Returns {'root': Path, 'branches': [str, ...], 'choice': str, 'params': dict}.
    Exits with a message on --help, bad arguments, cancellation, or when there
    is no terminal available to ask.
    """
    argv = list(sys.argv[1:] if argv is None else argv)
    usage = USAGE.format(script=script_name)

    if any(a in ("-h", "--help") for a in argv):
        print(usage)
        sys.exit(0)

    if len(argv) > 2:
        print(f"ERROR: expected at most 2 arguments, got {len(argv)}.\n\n{usage}")
        sys.exit(2)

    arg_root = clean_path(argv[0]) if len(argv) >= 1 else None
    arg_choice = None
    if len(argv) >= 2:
        arg_choice = parse_branch(argv[1])
        if arg_choice is None:
            print(f"ERROR: unknown branch {argv[1]!r}.\n\n{usage}")
            sys.exit(2)

    # Non-interactive: everything must come from the command line.
    if not is_interactive():
        if arg_root is None:
            print("ERROR: no terminal available to ask for the settings, and none were "
                  f"given on the command line.\n\n{usage}")
            sys.exit(2)
        problem = path_problem(arg_root, require_segmentation_output)
        if problem is not None:
            print(f"ERROR: cannot use {arg_root} - {problem}.")
            sys.exit(2)
        choice = arg_choice or "corrected"
        params = param_defaults(param_specs)
        print(f"Root data directory : {arg_root}")
        print(f"Branch(es) to run   : {', '.join(BRANCH_CHOICES[choice])}")
        _print_params(param_specs, params)
        save_last_run(arg_root, choice)
        return {"root": arg_root, "branches": BRANCH_CHOICES[choice],
                "choice": choice, "params": params}

    # Interactive: ask for whatever the command line did not supply.
    print(f"\n=== {title} ===\n")
    last = load_last_run()
    asked = False  # did we actually prompt for anything?

    if arg_root is not None:
        problem = path_problem(arg_root, require_segmentation_output)
        if problem is None:
            root = arg_root
            print(f"Root data directory : {root}")
        else:
            print(f"Cannot use {arg_root} - {problem}.\n")
            root = prompt_root(last.get("root"), require_segmentation_output)
            asked = True
    else:
        root = prompt_root(last.get("root"), require_segmentation_output)
        asked = True

    if arg_choice is not None:
        choice = arg_choice
    else:
        choice = prompt_branch(last.get("branch", "corrected"))
        asked = True

    # Prompt for the parameters only on a genuinely interactive run. If both
    # root and branch came from the command line (asked is False) we skip them
    # and use the defaults, so a fully argument-driven run never stalls on a
    # prompt - matching how confirmation is handled just below.
    if asked and param_specs:
        params = prompt_params(param_specs)
    else:
        params = param_defaults(param_specs)

    # Only confirm what was typed here. If both values came from the command
    # line there is nothing to check back on, and asking would defeat the point
    # of passing them (and stall an unattended run that merely looks like a TTY).
    if asked:
        confirm(root, choice, param_specs, params)
    else:
        print(f"Branch(es) to run   : {', '.join(BRANCH_CHOICES[choice])}")
        _print_params(param_specs, params)
    save_last_run(root, choice)
    return {"root": root, "branches": BRANCH_CHOICES[choice],
            "choice": choice, "params": params}
