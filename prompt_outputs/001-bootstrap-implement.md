# 001 — bootstrap — implement

Task: insert the WORKING RULES block into CLAUDE.md, create `prompt_outputs/`,
report a read-only inventory and a rule-by-rule comparison.

**Stopped at the review gate: nothing staged, nothing committed, nothing pushed.**
The only exception is `git add -N` (intent-to-add) on new untracked files, which
this prompt explicitly requires so the diff artifact can see them; it records no
content in the index.

**No pipeline script, test script, or dataset was touched.** There is no
automated test suite in this repository. The two stage-7 test scripts
(`kinematics/test_stage7_structure.py`, `kinematics/demo_test_stage7.py`) are
hand-run: the first needs a real dataset root in its top-of-file
`ROOT_DIRECTORY`, the second fabricates a synthetic tree. Neither was run here,
as the prompt requires.

All measurement, insertion and verification was done with script files placed
outside the repository, under the session scratchpad:

```
claude_md_checks.py       measurements + defect checks D1-D4
insert_block.py           the insertion itself (byte level, anchor-guarded)
verify_unchanged.py       strips the inserted range and compares baselines
inventory.py              sections a-f
```

---

## 0. PROMPT CLAIMS CHECKED

| # | Claim in the prompt | Verdict |
|---|---|---|
| 1 | Intro line is line 3 | **CORRECT** |
| 2 | `## What this is` is line 5 | **CORRECT** |
| 3 | D1 (no-test-suite vs hand-run tests) | **CONFIRMED** |
| 4 | D2 (highest-version rule vs kept v1 / non-progression) | **CONFIRMED** |
| 5 | D3 (U+00B5 vs U+03BC both present) | **CONFIRMED** |
| 6 | `git add -N <every new untracked file, listed from git status>` | **DIVERGED** — at the time of listing there were no untracked files other than the ones this task creates; see §7 |
| 7 | cmp the remainder byte-for-byte against `git show HEAD:CLAUDE.md` | **DIVERGED** — cannot match raw; `core.autocrlf=true` stores LF in the blob while the worktree is CRLF. Both comparisons were run and are reported in §4 |

### 0.1 Repository state changed between Task 000 and Task 001

Task 000 ended with two staged renames and one unpushed commit. That state no
longer exists. This was not done by this task.

```
=== git status ===
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   CLAUDE.md

no changes added to commit (use "git add" and/or "git commit -a")
=== git status --porcelain ===
 M CLAUDE.md
=== on-disk presence of the four Task-000 paths ===
EXISTS   archive/final_kin_param_extraction_v3.py
EXISTS   archive/final_kin_param_extraction_v4.py
MISSING  alignment_1/final_kin_param_extraction_v3.py
MISSING  alignment_2/final_kin_param_extraction_v4.py
```

```
=== unpushed commits now ===
0
```

So: the `archive/` -> `alignment_N/` move was reverted in full (both files are
back in `archive/`, nothing staged, no untracked leftovers), and commit
`68cbcf3`, which Task 000 measured as one commit ahead of `origin/main`, is no
longer ahead. The inventory in §6 therefore describes `archive/` with 14 files,
not the 12 Task 000 left in the index.

---

## 1. RULE-BY-RULE COMPARISON WITH THE PRE-EDIT CLAUDE.md

CLAUDE.md as it stood before this edit is a pure architecture reference: it
documents what each script does, the data-flow stages, and the data-format
invariants. It contains no guidance about how a task is conducted — no reports,
no staging, no commit policy, no measurement discipline. The comparison reflects
that: ten of eleven items are SILENT.

Line numbers below are PRE-EDIT.

| Rule | Verdict | Evidence in CLAUDE.md |
|---|---|---|
| Heading `## Working rules (how every task is run)` | SILENT | No section about task conduct exists. Headings are: `# CLAUDE.md`, `## What this is`, `## Running`, `## Versioned scripts`, `## The pipeline (data flow)`, `## Data-format invariants (critical when editing)`, plus four `###` subsections. |
| Reports in `prompt_outputs/`, `NNN-<label>-<step>.md`, append-only, errata forward | SILENT | No mention of `prompt_outputs`, reports, or errata anywhere in the file. |
| Every claim in a prompt is unverified; report differences | SILENT | Nothing about handling instructions or claims. |
| Do only what the prompt names; "UNREQUESTED — ACCEPT OR DROP" | SILENT | Nothing about scope discipline. |
| Every figure comes from a pasted command; quote, never restate | SILENT | Nothing about evidence or figures. |
| Diff artifact via `git diff --output=`, verified by cmp outside the repo | SILENT | The file never mentions git usage. |
| Measure with a script file, never a one-liner or heredoc | SILENT | No measurement guidance. |
| Stage by explicit path, never glob or `git add .` | SILENT | No staging guidance. |
| Never commit without an approved message; never push without separate approval | SILENT | No commit or push guidance. |
| Commit messages: 50/72, imperative | SILENT | No commit-message convention. |
| Anything tests cannot reach needs a manual run by the user before push | **TENSION** (see §2) | L9: "There is no package, no build, no test suite, and no CLI." L87 describes `test_stage7_structure.py` as a hand-run structural check needing a real dataset root. |

No rule CONFLICTS with CLAUDE.md in the sense of contradicting a statement it
makes. The single tension is the last rule, raised in §2 for ruling.

### 1.1 Duplication check

No inserted rule duplicates guidance CLAUDE.md already gives in its own words.
The nearest neighbours, and why they do not overlap:

- L24: "**The highest version number is the current one**; lower versions are
  kept for history. When editing behavior, edit the latest version unless
  explicitly told otherwise." — a rule about *which file to edit*, not about how
  a task is run or reported.
- L82: "**Do not reintroduce `ROOT_DATA_DIR`/`BRANCH` here**; they were
  deliberately removed so no one's local paths land in git." — a specific
  prohibition about one module's contents, not a general working rule.
- L116: "Add new experiments there, not by forking the script." — again
  file-level, not process-level.

---

## 2. POINTS FOR RULING

### 2.1 The last rule versus "there is no test suite"

The inserted rule reads:

```
- Anything tests cannot reach needs a manual run by the user before push.
```

CLAUDE.md states, at pre-edit L9 / post-edit L33:

> There is no package, no build, no test suite, and no CLI.

and at pre-edit L87 / post-edit L111 describes the only test scripts as hand-run
and dataset-dependent:

> - **`test_stage7_structure.py`** (standalone regression test, run by hand) — a
> **structural** check ... Edit the top-of-file `ROOT_DIRECTORY` ... to a real
> dataset root, then `python test_stage7_structure.py`.

Read literally against this repository, "anything tests cannot reach" is
*everything except stage 7's structural shape on a machine that has the data*.
The rule is therefore either near-universal or needs its scope narrowed. This is
the same underlying inconsistency as defect D1, now imported into the rules.
**Not resolved — for your ruling.** The block was inserted verbatim as
instructed.

### 2.2 Heading level

The block's own `##` is correct and was kept unchanged. Surrounding headings,
quoted from the post-edit file:

```
  L1: # CLAUDE.md
  L5: ## Working rules (how every task is run)
  L29: ## What this is
```

The block sits between the document's single `#` title and the first existing
`##` section, so `##` makes it a sibling of `## What this is` and a child of
`# CLAUDE.md`. No change needed.

### 2.3 Should `prompt_outputs/` be gitignored or tracked?

CLAUDE.md is **silent** — it contains no mention of `prompt_outputs` (the only
occurrence in the post-edit file is inside the block just inserted).

`.gitignore` is **silent** — it has no entry matching `prompt_outputs`. Its
full contents are quoted in §6d. The entries it does carry are `__pycache__/`,
`*.py[cod]`, `*.egg-info/`, `build/`, `dist/`, `.venv/`, `venv/`, `env/`,
`.env`, `.idea/`, `.vscode/`, `.DS_Store`, `Thumbs.db`, `.claude/`,
`kinematics/.kin_last_run.json`, plus two commented-out data patterns.

**Recommendation (PROPOSED, not implemented):** track `prompt_outputs/`. The
reports are the audit trail for a cleanup being done ahead of publication, and
the working rules make them append-only with errata carried forward — a history
that only has value if it is versioned alongside the changes it describes. The
regenerated `.diff.txt` artifacts will churn, which is the one argument for
ignoring them; if that churn is unwanted, the narrower option is to track the
`.md` reports and ignore only `prompt_outputs/*.diff.txt`. Nothing was added to
`.gitignore` in this task.

---

## 3. INSERTION

Performed by `insert_block.py`, which reads the target as bytes, refuses to run
unless the claimed anchors are exactly where the prompt says, and splices the
block in using the file's own terminator.

```
measured: target terminator = CRLF (CRLF=117, bare LF=0)
measured: lines before insert = 117
measured: L3 = intro line              -> anchor OK (claimed 3)
measured: L4 = blank                   -> separator already present
measured: L5 = '## What this is'       -> anchor OK (claimed 5)
measured: block lines                  = 23
measured: lines inserted (block + 1 blank) = 24
measured: lines after insert  = 141
measured: bytes before        = 26079
measured: bytes after         = 27349
measured: inserted line range = L5..L28
VERDICT: inserted; no pre-existing line object was modified (slice splice only)
EXIT=0
```

**Line endings of the inserted text: CRLF**, matching the file, which was and
remains uniformly CRLF. Note the difference from the prompt's implied arithmetic:
the block is 23 lines and 24 lines were inserted, because the blank line that
separates the block from `## What this is` is new while the blank line above the
block (L4) already existed.

Total lines before: **117**. Total lines after: **141**. Inserted: **24**.
(The prompt's claimed anchors at L3/L5 were both correct; the file has 117
lines, not 118 — an editor showing a phantom final line after the trailing
newline would say 118.)

Post-edit placement, quoted from `claude_md_checks.py`:

```
measured: L1 = '# CLAUDE.md'
measured: L2 = ''
measured: L3 = 'This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.'
measured: L4 = ''
measured: L5 = '## Working rules (how every task is run)'
measured: intro line number(s)        = [3]  (claimed 3)
measured: '## What this is' line no.  = [29]  (claimed 5)
```

Exactly one blank line on each side, as required.

---

## 4. INSERTION VERIFICATION

### 4.1 One hunk, pure addition

```
=== git diff HEAD --numstat -- CLAUDE.md ===
24	0	CLAUDE.md

=== hunk headers for CLAUDE.md ===
hunk count: 1
@@ -2,6 +2,30 @@

=== deleted-line count (lines starting with a single '-') ===
0
=== added-line count (lines starting with a single '+') ===
23
```

One hunk. Zero deleted lines. The added-line grep reports 23 rather than 24
because the pattern `^+[^+]` cannot match the added blank line, which is a bare
`+`; the numstat above gives the true 24/0.

### 4.2 Every pre-existing line is byte-identical

`verify_unchanged.py` strips lines L5..L28 back out of the post-edit file and
compares the remainder against two baselines.

```
measured: post-edit lines        = 141
measured: removing 1-based range = L5..L28 (24 lines)
measured: file ends with terminator = True
measured: removed lines          = 24
measured: remainder lines        = 117
measured: first removed line     = '## Working rules (how every task is run)'
measured: last  removed line     = ''
measured: remainder bytes        = 26079

--- A. remainder  vs  pre-edit working-tree snapshot (raw bytes) ---
measured: baseline bytes = 26079  remainder bytes = 26079
VERDICT: IDENTICAL - no pre-existing line changed

--- B1. remainder  vs  git show HEAD:CLAUDE.md (raw bytes) ---
measured: blob bytes = 25962  remainder bytes = 26079
measured: blob CRLF count = 0
VERDICT: DIFFERS (expected: autocrlf=true stores LF, worktree is CRLF)

--- B2. remainder normalised to LF  vs  git show HEAD:CLAUDE.md ---
measured: blob bytes = 25962  normalised remainder bytes = 25962
VERDICT: IDENTICAL - no pre-existing line changed
```

Confirmed externally with `cmp`:

```
=== cmp A: post-minus-block  vs  pre-edit worktree snapshot ===
cmp: EXIT 0 - files are identical

=== cmp B1: post-minus-block (CRLF)  vs  git show HEAD:CLAUDE.md (LF) ===
...claude_md_POST_minus_block.md ...claude_md_HEAD_blob.md differ: byte 12, line 1
cmp exit=1

=== cmp B2: post-minus-block normalised to LF  vs  git show HEAD:CLAUDE.md ===
cmp: EXIT 0 - files are identical
```

**Why B1 differs, and why that is not a defect.** The prompt asks for a
byte-for-byte cmp against `git show HEAD:CLAUDE.md`. That cannot succeed as
stated in this repository:

```
=== core.autocrlf ===
true
=== .gitattributes present? ===
NO - no .gitattributes in repo root
=== HEAD blob size of CLAUDE.md (bytes) ===
25962
=== working tree CLAUDE.md size (bytes) ===
26079
```

With `core.autocrlf=true` and no `.gitattributes`, git stores LF and checks out
CRLF, so blob and worktree differ by exactly one byte per line (26079 - 25962 =
117 = the pre-edit line count) before any edit is made. Baseline A is therefore
the exact byte-for-byte test (against a snapshot of the working-tree file taken
before the edit, whose sha256 matched the live file), and B2 is the
like-for-like test against the blob. Both pass.

### 4.3 D4 — CRLF and LF counts for CLAUDE.md, before and after

Before:

```
measured: bytes                = 26079
measured: total lines          = 117
measured: CRLF terminators     = 117
measured: bare-LF terminators  = 0
measured: bare-CR terminators  = 0
measured: file ends with newline = True
VERDICT: line endings are uniformly CRLF
```

After:

```
measured: bytes                = 27349
measured: total lines          = 141
measured: CRLF terminators     = 141
measured: bare-LF terminators  = 0
measured: bare-CR terminators  = 0
measured: file ends with newline = True
VERDICT: line endings are uniformly CRLF
```

D4 verdict: CRLF 117 -> 141, LF 0 -> 0. The file was uniformly CRLF before and
is uniformly CRLF after; the insertion introduced no mixed endings.

---

## 5. DEFECT CHECKS (verified, NOT fixed)

Line numbers are given pre-edit and post-edit. The insertion shifts every line
from the old L5 onward by +24.

### D1 — CONFIRMED

```
--- D1: 'no test suite' vs the two hand-run stage-7 test scripts ---
measured: lines containing 'no test suite'        = 1
measured: lines naming a stage-7 test script      = 1
  claim   L9: There is no package, no build, no test suite, and no CLI. ...
  counter L87: - **`test_stage7_structure.py`** (standalone regression test, run by hand) — ...
VERDICT: D1 CONFIRMED
```

| | pre-edit | post-edit |
|---|---|---|
| "no test suite" claim | L9 | **L33** |
| stage-7 test scripts described | L87 | **L111** |

Quoted, pre-edit L9:

> There is no package, no build, no test suite, and no CLI. Each `.py` file is a
> self-contained batch script run directly with `python <script>.py`.

Quoted, pre-edit L87 (both test scripts are described in this one bullet):

> - **`test_stage7_structure.py`** (standalone regression test, run by hand) — a
> **structural** check, deliberately *not* a numeric one ... A companion
> **`demo_test_stage7.py`** (run by hand, no real data) fabricates a tiny
> synthetic `segmentation_output/` tree ...

Note a measurement detail: the checker counts **one** line naming a stage-7 test
script, not two, because `demo_test_stage7.py` is documented inside the same
bullet as `test_stage7_structure.py` rather than on its own line.

### D2 — CONFIRMED

```
--- D2: 'highest version is current' vs kept v1 / non-progression ---
measured: lines stating the highest-version rule  = 1
measured: lines naming error_analysis_v1          = 1
measured: lines saying 'not a version progression'= 1
  rule      L24: Many scripts exist as `_v1`/`_v2`/`_v3`/`_v4`/`_v5` ...
  kept-v1   L100: - **`error_analysis_v1.py`** — flags **fragmentation**: ...
  non-prog  L105: These are **run by hand on a single hard-coded image path** ...
VERDICT: D2 CONFIRMED
```

| | pre-edit | post-edit |
|---|---|---|
| highest-version rule | L24 | **L48** |
| `error_analysis_v1.py` kept beside `_v3` | L100 | **L124** |
| "not a version progression" | L105 | **L129** |

Quoted, pre-edit L24:

> **The highest version number is the current one**; lower versions are kept for
> history. When editing behavior, edit the latest version unless explicitly told
> otherwise.

Quoted, pre-edit L100 (v1 is current, not superseded):

> - **`error_analysis_v1.py`** — flags **fragmentation**: any image with ≥2
> disconnected white components (>10 px).

Quoted, pre-edit L105:

> They are **not a version progression** — each solves a *different* segmentation
> defect, so all three are kept

A second-order observation from the same line: L105 says "all three are kept"
while the section it introduces lists **four** scripts, `correction_v1.py`
through `correction_v4.py`. Reported, not fixed; not one of D1-D3.

### D3 — CONFIRMED

```
--- D3: U+00B5 MICRO SIGN vs U+03BC GREEK SMALL LETTER MU ---
measured: U+00B5 MICRO SIGN occurrences          = 1
measured: U+03BC GREEK SMALL LETTER MU occurrences = 2
  U+00B5 MICRO SIGN                L83 col 146: ...)`, which takes one track in µm/s and returns a metrics dic...
  U+03BC GREEK SMALL LETTER MU     L93 col 46: ...es.** The old scripts write `μ` to the summary with the pla...
  U+03BC GREEK SMALL LETTER MU     L93 col 193: ...progress line also contains `μ`, so on a Windows console th...
VERDICT: D3 CONFIRMED (both codepoints present)
```

Three occurrences in total, two distinct codepoints:

| Codepoint | Name | pre-edit | post-edit | Context |
|---|---|---|---|---|
| U+00B5 | MICRO SIGN | L83 col 146 | **L107** col 146 | "takes one track in µm/s" |
| U+03BC | GREEK SMALL LETTER MU | L93 col 46 | **L117** col 46 | "The old scripts write `μ` to the summary" |
| U+03BC | GREEK SMALL LETTER MU | L93 col 193 | **L117** col 193 | "progress line also contains `μ`" |

### D4

Reported in §4.3 above, before and after.

---

## 6. READ-ONLY INVENTORY

Produced by `inventory.py`, which reads git metadata and file bytes only. Source
of the file list is `git ls-files`, i.e. the index, which per §0.1 currently
matches HEAD.

### a. Tracked file tree by folder

```
<repo root>  (4 files)
    .gitignore
    CLAUDE.md
    README.md
    requirements.txt

alignment_1/  (4 files)
    blob_mhi_tracks_alignment_v4.py
    mhi_overlay_copies_v1.py
    mhi_overlay_v2.py
    time_coordinates_conversions_v2.py

alignment_2/  (4 files)
    blob_mhi_tracks_alignment_v5.py
    mhi_overlay_copies_v2.py
    mhi_overlay_v3.py
    time_coordinates_conversions_v3.py

archive/  (14 files)
    blob_detection_ME_complete.py
    blob_detection_ME_part1.py
    blob_detection_v2.py
    blob_parameters_check_v1.py
    blob_parameters_check_v2.py
    error_analysis_v2.py
    final_kin_param_extraction_v2.py
    final_kin_param_extraction_v3.py
    final_kin_param_extraction_v4.py
    mhi_overlay_v1.py
    track_segmentation_ancient_v1.py
    track_segmentation_ancient_v2.py
    track_segmentation_v2.py
    track_segmentation_v3.py

blob_detection/  (4 files)
    blob_detection_cleanup.py
    blob_detection_v3_memory_optimized.py
    blob_parameters_check_v3.py
    check_blobs_npy.py

frame_rate/  (1 files)
    frame_rate_v1.py

kinematics/  (8 files)
    demo_test_stage7.py
    extract_track_metrics.py
    kin_config.py
    kin_grouping.py
    kin_metrics.py
    kin_prompt.py
    summarize_track_metrics.py
    test_stage7_structure.py

segmentation/  (2 files)
    npy_conversion_v1.py
    track_segmentation_v4.py

segmentation_checks/  (2 files)
    error_analysis_v1.py
    error_analysis_v3.py

segmentation_corrections/  (4 files)
    correction_v1.py
    correction_v2.py
    correction_v3.py
    correction_v4.py

utils/  (2 files)
    copy_color_mhis_and_normal_mhis.py
    copy_rename_MHIs.py

measured: folders = 11
measured: total tracked files = 49
```

### b. Tracked `.py` per top-level folder

```
  alignment_1                  4
  alignment_2                  4
  archive                      14
  blob_detection               4
  frame_rate                   1
  kinematics                   8
  segmentation                 2
  segmentation_checks          2
  segmentation_corrections     4
  utils                        2

measured: total tracked .py files = 45
measured: top-level folders holding .py = 10
```

### c. CLAUDE.md name coverage, both directions

```
measured: distinct .py names mentioned in CLAUDE.md = 43
measured: distinct tracked .py basenames            = 45

c1. TRACKED .py NOT MENTIONED BY NAME IN CLAUDE.md (13):
    archive/blob_detection_ME_complete.py
    archive/blob_detection_ME_part1.py
    archive/blob_detection_v2.py
    alignment_1/blob_mhi_tracks_alignment_v4.py
    archive/blob_parameters_check_v1.py
    archive/blob_parameters_check_v2.py
    archive/error_analysis_v2.py
    archive/final_kin_param_extraction_v2.py
    alignment_1/mhi_overlay_copies_v1.py
    alignment_2/mhi_overlay_copies_v2.py
    alignment_1/mhi_overlay_v2.py
    alignment_2/mhi_overlay_v3.py
    alignment_1/time_coordinates_conversions_v2.py

c2. NAMES CLAUDE.md MENTIONS THAT ARE NOT A TRACKED .py (11):
    ..._blob_mhi_tracks_alignment_v4.py            CLAUDE.md L[84] | not on disk
    ..._blob_mhi_tracks_alignment_v5.py            CLAUDE.md L[84] | not on disk
    ..._mhi_overlay_copies_v1.py                   CLAUDE.md L[87] | not on disk
    ..._mhi_overlay_copies_v2.py                   CLAUDE.md L[87] | not on disk
    ..._mhi_overlay_v2.py                          CLAUDE.md L[85] | not on disk
    ..._mhi_overlay_v3.py                          CLAUDE.md L[85] | not on disk
    ..._time_coordinates_conversions_v2.py         CLAUDE.md L[86] | not on disk
    ..._time_coordinates_conversions_v3.py         CLAUDE.md L[86] | not on disk
    colours_MHIs.py                                CLAUDE.md L[68] | not on disk
    colours_MHIs_validate_output.py                CLAUDE.md L[68] | not on disk
    merge_v1.py                                    CLAUDE.md L[134] | not on disk
```

Reading of c1 and c2 together, offered as interpretation rather than as a new
figure:

- The `..._`-prefixed entries in c2 are not real filenames. They are the
  abbreviated cell labels in the branch-comparison table (post-edit L84-L87),
  where the leading path is elided. Each corresponds to a file that does exist,
  and that elision is exactly why those same files show up in c1 as
  "not mentioned by name" — the table names them only in truncated form. This
  accounts for 8 of the 11 c2 entries and 7 of the 13 c1 entries.
- `colours_MHIs.py` and `colours_MHIs_validate_output.py` (post-edit L68) are
  deliberate historical references: CLAUDE.md gives them as the *former* names
  of `track_segmentation_ancient_v1.py` / `_v2.py`. Likewise `merge_v1.py`
  (post-edit L134) is given as the former name of `correction_v4.py`. All three
  are correctly described as old names, not as present files.
- The genuinely unmentioned files are the six `archive/` scripts in c1 that no
  line names: `blob_detection_ME_complete.py`, `blob_detection_ME_part1.py`,
  `blob_detection_v2.py`, `blob_parameters_check_v1.py`,
  `blob_parameters_check_v2.py`, `error_analysis_v2.py`, plus
  `final_kin_param_extraction_v2.py`. CLAUDE.md refers to each of these by
  version suffix only — for example post-edit L50 says "The archived
  `_ME_complete`/`_v2` variants" and L125 says "(The archived `_v2` is v3
  without the memory management...)" — so they are described, but never by
  their full filename.

### d. `.gitignore`, and the status of three specific paths

```
measured: .gitignore exists, 474 bytes
measured: tracked by git = yes
--- contents ---
# Python
__pycache__/
*.py[cod]
*.egg-info/
build/
dist/

# Virtual environments
.venv/
venv/
env/
.env

# Editors / OS
.idea/
.vscode/
.DS_Store
Thumbs.db

# Claude Code local settings (machine-specific permissions)
.claude/

# Machine-specific settings remembered between kinematic-analysis runs
kinematics/.kin_last_run.json

# Pipeline data & outputs (kept outside the repo — see README)
# Uncomment if you ever place sample data inside the repo tree:
# *.npy
# *.tif
--- end ---
```

Per-path determination, both commands pasted verbatim:

```
########## archive/__pycache__/
--- git check-ignore -v ---
.gitignore:2:__pycache__/	archive/__pycache__/
check-ignore exit=0
--- git ls-files --error-unmatch ---
error: pathspec 'archive/__pycache__/' did not match any file(s) known to git
Did you forget to 'git add'?
ls-files exit=1
--- exists on disk? ---
EXISTS

########## .claude/settings.local.json
--- git check-ignore -v ---
.gitignore:21:.claude/	.claude/settings.local.json
check-ignore exit=0
--- git ls-files --error-unmatch ---
error: pathspec '.claude/settings.local.json' did not match any file(s) known to git
Did you forget to 'git add'?
ls-files exit=1
--- exists on disk? ---
EXISTS

########## kinematics/.kin_last_run.json
--- git check-ignore -v ---
.gitignore:24:kinematics/.kin_last_run.json	kinematics/.kin_last_run.json
check-ignore exit=0
--- git ls-files --error-unmatch ---
error: pathspec 'kinematics/.kin_last_run.json' did not match any file(s) known to git
Did you forget to 'git add'?
ls-files exit=1
--- exists on disk? ---
EXISTS
```

| Path | Verdict | Ignored by |
|---|---|---|
| `archive/__pycache__/` | **IGNORED** (not tracked; exists on disk) | `.gitignore:2:__pycache__/` |
| `.claude/settings.local.json` | **IGNORED** (not tracked; exists on disk) | `.gitignore:21:.claude/` |
| `kinematics/.kin_last_run.json` | **IGNORED** (not tracked; exists on disk) | `.gitignore:24:kinematics/.kin_last_run.json` |

None of the three is "neither" and none is tracked: all three are ignored, all
three exist on disk. Each is matched by a distinct `.gitignore` line, and the
last two match what CLAUDE.md says about them at post-edit L105
(`.kin_last_run.json` is "**Gitignored** — it is the only place a
machine-specific path is stored").

### e. Line endings per tracked text file

```
measured: .gitattributes exists = False
measured: core.autocrlf = true
```

Full per-file table is in the scratchpad `inventory_output.txt`; the totals and
the CRLF files are what matter here:

```
measured totals: CRLF=8, LF=41
```

The eight CRLF files:

```
CLAUDE.md                                               141      0  CRLF
README.md                                               213      0  CRLF
alignment_1/blob_mhi_tracks_alignment_v4.py             650      0  CRLF
alignment_2/blob_mhi_tracks_alignment_v5.py             681      0  CRLF
archive/final_kin_param_extraction_v2.py                492      0  CRLF
archive/final_kin_param_extraction_v3.py                509      0  CRLF
archive/final_kin_param_extraction_v4.py                526      0  CRLF
blob_detection/blob_detection_v3_memory_optimized.py    737      0  CRLF
```

The other 41 tracked text files are uniformly LF. No file is MIXED, and no
`.gitattributes` exists to normalise any of this — with `core.autocrlf=true`,
what is on disk depends on how each file was first added.

### f. Runnable scripts versus imported-only modules

Measured signal: presence of an `if __name__ == "__main__"` guard, and whether
any other tracked `.py` imports the module by name.

In the stage order CLAUDE.md gives (post-edit L66-L74), the scripts a user runs
directly are:

| Stage | Script | `__main__` guard |
|---|---|---|
| 1 Track segmentation | `segmentation/track_segmentation_v4.py` | no (module-level loop) |
| 2 PNG->NPY | `segmentation/npy_conversion_v1.py` | no (module-level loop) |
| 3 Blob detection | `blob_detection/blob_detection_v3_memory_optimized.py` | yes |
| 3 (tuning) | `blob_detection/blob_parameters_check_v3.py` | yes |
| 4 Alignment | `alignment_2/blob_mhi_tracks_alignment_v5.py` (branch 1: `alignment_1/..._v4.py`) | yes |
| 4b Overlay | `alignment_2/mhi_overlay_v3.py` (branch 1: `alignment_1/mhi_overlay_v2.py`) | yes |
| 5 Frame rate | `frame_rate/frame_rate_v1.py` | yes |
| 6 Unit conversion | `alignment_2/time_coordinates_conversions_v3.py` (branch 1: `..._v2.py`) | yes |
| 6b Overlay collect | `alignment_2/mhi_overlay_copies_v2.py` (branch 1: `..._v1.py`) | yes |
| 7a Kinematics | `kinematics/extract_track_metrics.py` | yes |
| 7b Summary | `kinematics/summarize_track_metrics.py` | yes |

The imported-only modules — never run directly, no `__main__` guard, imported by
other tracked files:

```
kinematics/kin_config.py                                 False            4  IMPORTED-ONLY module
kinematics/kin_grouping.py                               False            2  IMPORTED-ONLY module
kinematics/kin_metrics.py                                False            4  IMPORTED-ONLY module
kinematics/kin_prompt.py                                 False            2  IMPORTED-ONLY module
```

These four are exactly the modules CLAUDE.md describes as "prompt, config, two
pure modules" at post-edit L102, and `kinematics/` is the only folder where any
tracked file imports another.

Three `kinematics/` files are both runnable and imported:

```
kinematics/extract_track_metrics.py                       True            2  runnable + imported
kinematics/summarize_track_metrics.py                     True            3  runnable + imported
kinematics/test_stage7_structure.py                       True            1  runnable + imported
```

Everything else (QA, corrections, utilities, and all of `archive/`) is a
standalone runnable script. Nine tracked scripts run as a module-level loop with
no guard: the two `segmentation/` stage scripts, both `utils/` scripts, and five
`archive/` scripts. This matters for the working rule about measurement — such a
file cannot be imported for inspection without executing its batch loop.

---

## 7. `git add -N` AND THE DIFF ARTIFACT

Per §0.1, the working tree held exactly one modification (`CLAUDE.md`) and no
untracked files before this task created `prompt_outputs/`. The untracked files
listed from `git status` at the time of staging were therefore only this task's
own outputs. They were recorded with `git add -N` by explicit path — no glob, no
`git add .` — so the diff artifact can see them. `-N` records intent-to-add
only; no content is staged.

The artifact was then written with the prescribed command and verified by `cmp`
against a regeneration produced outside the repository. The pasted command
outputs for this section are in the chat reply for this task; the artifact
itself is `prompt_outputs/001-bootstrap.diff.txt`, which by construction
excludes itself and therefore contains this report plus the CLAUDE.md hunk.

---

## 8. UNREQUESTED — ACCEPT OR DROP

Not implemented; listed for ruling.

1. **Resolve D1** by rewording post-edit L33 ("no test suite") to acknowledge the
   two hand-run stage-7 test scripts, or by narrowing the working rule in §2.1.
2. **Resolve D2** by qualifying the highest-version rule at post-edit L48 with
   the two documented exceptions (`segmentation_checks/`,
   `segmentation_corrections/`).
3. **Resolve D3** by normalising all three micro/mu occurrences to one codepoint.
4. **Fix "all three are kept"** at post-edit L129, which introduces four scripts.
5. **Add a `.gitattributes`** to stop the CRLF/LF split recorded in §6e from
   depending on `core.autocrlf` and on which machine first added each file.
6. **Decide `prompt_outputs/` tracking** per §2.3.
7. **Name the seven `archive/` scripts explicitly** in CLAUDE.md per §6c, or
   state deliberately that archived variants are referenced by suffix only.
