# 003 — archive — implement

**IMPLEMENTED, STOPPED AT THE REVIEW GATE.** I appended one new section to
`DECISIONS.md`, using your proposed wording verbatim. Nothing is staged,
committed or pushed. The only index operation is the `git add -N`
(intent-to-add) that this prompt requires for the diff artifact.

**Your ruling is needed on one finding before commit: the git history does
not match the prompt's WHY.** The history records no move *into*
`alignment_1/` / `alignment_2/` and no revert of one. It shows the reverse:
both scripts were **added in** `alignment_1/` and `alignment_2/` by the
initial commit `5dc8797`, and **moved out to** `archive/` by `52c7a42`. The
move-and-revert the prompt describes exists only in the task-001 reports, as
renames that were staged, never committed, and then reverted. See §2. The
proposed wording also has five other claims that differ from CLAUDE.md, the
README or the tree (§4). As instructed, none of them was reworded.

**No test script was run.** There is no automated test suite (DECISIONS.md,
Tests), and this change touches nothing in `kinematics/`. §5 has the
character scan that the prompt asked for.

Scripts used, all outside the repository (session scratchpad):

```
preflight_003.sh        fetch, position, status, ls-files, history search
state_003.sh            carried-report hashes, CLAUDE.md L76/L90/L98, scope
append_003.py           appends the section (textwrap, width 79, LF)
scan_decisions_003.py   UTF-8 / BOM / control chars / line endings / widths
prefix_check_003.py     pre-edit DECISIONS.md is a byte prefix of post-edit
tests_003.sh            runs the scan on the before-copy and the live file
artifact_003.sh         add -N, artifact, outside regeneration, cmp, numstat
fill_003.py             pastes artifact_003.sh output into §6 of this report
compare_numstat_003.py  quoted numstat vs live artifact numstat
```

---

## 0. ARTIFACT NAME

The prompt marks `prompt_outputs/003-archive.diff.txt` as UNVERIFIED and asks
me to check it against the 001 and 002 artifacts:

```
-rw-r--r-- 1 berke.santos 1049089  53951 Sep 23 11:34 001-bootstrap.diff.txt
-rw-r--r-- 1 berke.santos 1049089 102473 Sep 23 15:11 002-docs.diff.txt
```

Both artifacts follow the pattern `NNN-<label>.diff.txt`, and
`003-archive.diff.txt` fits it. **No difference.**

---

## 1. PRE-FLIGHT

Output of `preflight_003.sh`, run before any edit:

```
=== git fetch ===
fetch exit=0
=== HEAD / origin/main ===
HEAD:        5fd03f5dddf0de2cd909e11f2652739a0c872295
origin/main: 5fd03f5dddf0de2cd909e11f2652739a0c872295
=== position (left=behind right=ahead) ===
0	0
=== git status --porcelain -uall ===
?? prompt_outputs/002-docs-commit.md
?? prompt_outputs/002-docs-push.md
=== staged (git diff --cached --name-only) ===
  (nothing above = nothing staged)
=== modified tracked (git diff --name-only) ===
  (nothing above = none)
=== git ls-files archive/final_kin_param_extraction_v3.py archive/final_kin_param_extraction_v4.py ===
archive/final_kin_param_extraction_v3.py
archive/final_kin_param_extraction_v4.py
=== git ls-files alignment_1 alignment_2 ===
alignment_1/blob_mhi_tracks_alignment_v4.py
alignment_1/mhi_overlay_copies_v1.py
alignment_1/mhi_overlay_v2.py
alignment_1/time_coordinates_conversions_v2.py
alignment_2/blob_mhi_tracks_alignment_v5.py
alignment_2/mhi_overlay_copies_v2.py
alignment_2/mhi_overlay_v3.py
alignment_2/time_coordinates_conversions_v3.py
```

Each claim checked:

- **HEAD and origin/main are both `5fd03f5`, zero ahead and zero behind** after
  `git fetch`: correct.
- **The only untracked files are the two carried 002 reports, and nothing is
  modified or staged:** correct.
- **Both scripts are tracked under `archive/`:** correct.

**CLAUDE.md places them in `archive/` at three spots:** correct, and the line
numbers are exactly the ones the prompt gave. Output of `state_003.sh`, which
uses `sed -n`:

```
L76: 7. **Kinematic parameter extraction** — `kinematics/` (see **The `kinematics/` folder** below). **Unlike every other stage, this one is not configured by editing the script: `python extract_track_metrics.py` prompts for the root directory, the branch, and each analysis parameter** (or takes root+branch as command-line arguments), because root and branch are machine-specific and must not be hard-coded into the repo. The analysis parameters are prompted too, each pre-filled from its `kinematics/kin_config.py` default (Enter keeps it); those `kin_config.py` constants remain the defaults offered by the prompt and the values used by unattended runs. One invocation runs the whole stage. It reads `alignment_converted_results[_2]/` and writes per-track CSVs to `<root>/processed_results[_2]/`, then calls `summarize_track_metrics.py`, which reads those CSVs and writes the grouped summary statistics next to them. Tracks are grouped into experimental conditions by parsing subsubfolder names (`species_solute_time_sampleX_recY_changed`). This replaces the two per-branch scripts `final_kin_param_extraction_v3.py` and `final_kin_param_extraction_v4.py`, which — having been validated against the new stages on the full dataset — now live in `archive/` (unmodified, kept for reference only).
L90: | Kinematics (stage 7) | *superseded by* `kinematics/` (branch `"uncorrected"`); old: `archive/final_kin_param_extraction_v3.py` | *superseded by* `kinematics/` (branch `"corrected"`); old: `archive/final_kin_param_extraction_v4.py` |
L98: Within each branch the per-branch scripts (align → overlay → convert → collect; kinematics is now the shared `kinematics/` stage, with the old per-branch v3/v4 in `archive/`) are near-identical to the other branch's except for which `..._results[_2]/` folders and `mhi_overlay[_corrected].png` files they read and write; the actual logic is the same. Two exceptions where the branch scripts genuinely diverge in logic: the archived overlay v1 (missing 2048² resize) and the archived kinematics v2 (weaker `extract_sample_group` regex — v3/v4 also match `sampleX_..._recY` names with descriptors between, falling back to v2's exact pattern). The "overlay collect" and "kinematics" steps write to root-level folders (`mhi_overlays[_corrected]/`, `processed_results[_2]/`), gathering across all experiments — not per-branch data. **The corrected branch (`alignment_2/`) is canonical** — its `alignment_converted_results_2/` output is what the kinematic extraction (stage 7) consumes. `alignment_1/` exists only to reproduce the uncorrected-timing result for comparison; run it end-to-end (v4 → v2 overlay → v2 convert) if you want that, otherwise use `alignment_2/`.
```

These lines were not edited. §6 confirms that `DECISIONS.md` is the only
tracked file that changed.

---

## 2. GIT HISTORY OF THE TWO SCRIPTS — DIFFERS FROM THE PROMPT

Output of `preflight_003.sh`, continued:

```
=== git log --all --oneline -- (v3 path, v4 path, alignment_N paths) ===
52c7a42 Archive the superseded stage-7 scripts v3/v4
R100	alignment_1/final_kin_param_extraction_v3.py	archive/final_kin_param_extraction_v3.py
R100	alignment_2/final_kin_param_extraction_v4.py	archive/final_kin_param_extraction_v4.py
dee9589 Strip redundant 'colour_segmentation_' prefix from script filenames
R100	alignment_1/colour_segmentation_final_kin_param_extraction_v3.py	alignment_1/final_kin_param_extraction_v3.py
R100	alignment_2/colour_segmentation_final_kin_param_extraction_v4.py	alignment_2/final_kin_param_extraction_v4.py
R100	archive/colour_segmentation_final_kin_param_extraction_v2.py	archive/final_kin_param_extraction_v2.py
5dc8797 Initial commit: organized ME kinematic-analysis pipeline
A	alignment_1/colour_segmentation_final_kin_param_extraction_v3.py
A	alignment_2/colour_segmentation_final_kin_param_extraction_v4.py
A	archive/colour_segmentation_final_kin_param_extraction_v2.py
=== git log --all --follow --oneline --name-status archive/final_kin_param_extraction_v3.py ===
52c7a42 Archive the superseded stage-7 scripts v3/v4
R100	alignment_1/final_kin_param_extraction_v3.py	archive/final_kin_param_extraction_v3.py
dee9589 Strip redundant 'colour_segmentation_' prefix from script filenames
R100	alignment_1/colour_segmentation_final_kin_param_extraction_v3.py	alignment_1/final_kin_param_extraction_v3.py
5dc8797 Initial commit: organized ME kinematic-analysis pipeline
A	alignment_1/colour_segmentation_final_kin_param_extraction_v3.py
=== git log --all --follow --oneline --name-status archive/final_kin_param_extraction_v4.py ===
52c7a42 Archive the superseded stage-7 scripts v3/v4
R100	alignment_2/final_kin_param_extraction_v4.py	archive/final_kin_param_extraction_v4.py
dee9589 Strip redundant 'colour_segmentation_' prefix from script filenames
R100	alignment_2/colour_segmentation_final_kin_param_extraction_v4.py	alignment_2/final_kin_param_extraction_v4.py
5dc8797 Initial commit: organized ME kinematic-analysis pipeline
A	alignment_2/colour_segmentation_final_kin_param_extraction_v4.py
=== git log --all --oneline -i --grep=archive / --grep=revert ===
5fd03f5 Fix CLAUDE.md defects; add DECISIONS and GOTCHAS
eac7caf Docs: README table of every hard-coded path a user must edit
52c7a42 Archive the superseded stage-7 scripts v3/v4
8dd7fe9 Split stage-7 kinematics into kinematics/ (metrics, grouping, 2 stages)
7d35df6 Fix stale run example in CLAUDE.md
5dc8797 Initial commit: organized ME kinematic-analysis pipeline
=== git reflog (all, last 40) ===
5fd03f5 origin/main@{0} update by push
5fd03f5 main@{0} commit: Fix CLAUDE.md defects; add DECISIONS and GOTCHAS
5fd03f5 HEAD@{0} commit: Fix CLAUDE.md defects; add DECISIONS and GOTCHAS
cb4666a origin/main@{1} update by push
cb4666a main@{1} commit (amend): Add working-rules section and task 001 reports
cb4666a HEAD@{1} commit (amend): Add working-rules section and task 001 reports
9ff3abd main@{2} commit: Add working-rules section and task 001 reports
9ff3abd HEAD@{2} commit: Add working-rules section and task 001 reports
68cbcf3 origin/main@{2} update by push
68cbcf3 main@{3} commit: demo_test_stage7.py: add --keep to materialise the synthetic tree on disk
68cbcf3 HEAD@{3} commit: demo_test_stage7.py: add --keep to materialise the synthetic tree on disk
a1afb5c origin/main@{3} update by push
a1afb5c main@{4} commit: Add demo_test_stage7.py: no-data self-check for the stage-7 structural test
a1afb5c HEAD@{4} commit: Add demo_test_stage7.py: no-data self-check for the stage-7 structural test
c9883fc origin/main@{4} update by push
c9883fc main@{5} commit: Docs: drop equivalence-test mentions from CLAUDE.md (to be re-added later)
c9883fc HEAD@{5} commit: Docs: drop equivalence-test mentions from CLAUDE.md (to be re-added later)
adee6be origin/main@{5} update by push
adee6be main@{6} commit (amend): Gitignore local .claude/ settings; set stage-7 test ROOT_DIRECTORY to local root
adee6be HEAD@{6} commit (amend): Gitignore local .claude/ settings; set stage-7 test ROOT_DIRECTORY to local root
901f02a main@{7} commit: Gitignore local .claude/ settings; set stage-7 test ROOT_DIRECTORY to local root
901f02a HEAD@{7} commit: Gitignore local .claude/ settings; set stage-7 test ROOT_DIRECTORY to local root
dd80f56 origin@{0} fetch
dd80f56 origin/main@{6} update by push
dd80f56 main@{8} commit: Fix stage-7 structural test's track-name check for alphanumeric shortened dirs
dd80f56 HEAD@{8} commit: Fix stage-7 structural test's track-name check for alphanumeric shortened dirs
eac7caf main@{9} commit: Docs: README table of every hard-coded path a user must edit
eac7caf HEAD@{9} commit: Docs: README table of every hard-coded path a user must edit
52c7a42 main@{10} commit: Archive the superseded stage-7 scripts v3/v4
52c7a42 HEAD@{10} commit: Archive the superseded stage-7 scripts v3/v4
5d995e7 main@{11} commit: Add structural regression test for stage 7
5d995e7 HEAD@{11} commit: Add structural regression test for stage 7
d939e7c main@{12} commit: Drop the redundant PARAMS copy; DEFAULT_PARAMS is the sole per-track default
d939e7c HEAD@{12} commit: Drop the redundant PARAMS copy; DEFAULT_PARAMS is the sole per-track default
17069e9 main@{13} commit: Prompt for the analysis parameters too, defaulting from kin_config.py
17069e9 HEAD@{13} commit: Prompt for the analysis parameters too, defaulting from kin_config.py
ed0fd9d origin/main@{7} update by push
ed0fd9d main@{14} commit: Prompt for root path and branch instead of hard-coding them
ed0fd9d HEAD@{14} commit: Prompt for root path and branch instead of hard-coding them
3b36f97 origin/main@{8} update by push
=== git stash list ===
  (nothing above = no stashes)
```

**What the history shows:**

- `5dc8797` (initial commit) **added** the v3 script in `alignment_1/` and the
  v4 script in `alignment_2/`. Both still had their `colour_segmentation_`
  prefix.
- `dee9589` dropped that prefix from both names, and both stayed where they
  were.
- `52c7a42`, *"Archive the superseded stage-7 scripts v3/v4"*, **moved both
  out of** `alignment_1/` and `alignment_2/` into `archive/` (R100).

**What the history does not show:** a commit that moves either script *from*
`archive/` *into* `alignment_N/`, or a commit that reverts such a move. Neither
exists across all refs. The last 40 reflog entries record none, and there are
no stashes.

**Where the move and revert are recorded.** They appear only in the task-001
reports, as an uncommitted state:

- `001-bootstrap-implement.md` §0.1 says: *"Task 000 ended with two staged
  renames and one unpushed commit … the `archive/` -> `alignment_N/` move was
  reverted in full."*
- `001-bootstrap-gate.md` R6 says: *"Its `archive/` -> `alignment_N/` move was
  reverted and returns as its own later task."*

**The reason "for self-containment" is recorded nowhere.** I searched the tree
case-insensitively for `self-contain`. Every hit is about something else: the
CLAUDE.md L35 "self-contained batch script", the README L77 demo row, the
README L114 branch sequence (see M3 in §4), and quotations of those lines
inside the 001/002 reports and diffs.

So the claim that the scripts "were once moved into alignment_1/ and
alignment_2/ … then reverted" is true only of a working-tree state that was
never committed. The *committed* history shows the opposite: they were
**moved out of** those folders. A future session that runs `git log --follow`
will see that the scripts once lived in `alignment_N/` and that `52c7a42`
archived them, and it will find no move back and no revert.

---

## 3. THE CHANGE

I appended one section at the end of `DECISIONS.md` with `append_003.py`,
which wraps at 79 characters (the file's widest existing line, L45) and writes
LF. The wording is your proposal, byte for byte, apart from line breaks. The
section as it now stands, from the scan in §5:

```
  L68  len=29 |## Superseded stage-7 scripts|
  L69  len= 0 ||
  L70  len=76 |**`final_kin_param_extraction_v3.py` and `_v4.py` stay in `archive/`.** They|
  L71  len=72 |are not moved into `alignment_1/` or `alignment_2/`, nor into `archive/`|
  L72  len=23 |subfolders inside them.|
  L73  len= 0 ||
  L74  len=71 |*Why:* both were superseded by `kinematics/extract_track_metrics.py`, a|
  L75  len=72 |different stage, so they have no tie to the alignment directories. Those|
  L76  len=77 |directories are live run directories — the alignment, overlay, conversion and|
  L77  len=77 |overlay-collect steps run from them — and every script in them is current, so|
  L78  len=77 |moving the old scripts there would put dead code among live scripts. The move|
  L79  len=74 |was once made for self-containment and reverted; this records why it stays|
  L80  len= 9 |reverted.|
```

The section follows the style of the existing entries: a `##` heading, a bold
rule, then a `*Why:*` paragraph. It is separated from the Line endings entry
by one blank line.

The existing content was not touched. Output of `state_003.sh`:

```
=== append-only check ===
measured: pre-edit bytes  = 2722
measured: post-edit bytes = 3397
measured: appended bytes  = 675
measured: pre-edit is a byte prefix of post-edit = True
VERDICT: existing content untouched; change is append-only
```

---

## 4. PROPOSED WORDING CHECKED AGAINST CLAUDE.md AND THE TREE

**Confirmed:**

- **"the alignment, overlay, conversion and overlay-collect steps run from
  them":** `git ls-files alignment_1 alignment_2` (§1) lists exactly four
  scripts per folder. They are an alignment, an overlay, a conversion and an
  overlay-copies script, and they match the four CLAUDE.md table rows L86–L89
  one to one. The only other entries on disk are untracked `__pycache__/`
  folders.
- **"superseded"**, and that the scripts stay in `archive/`: this agrees with
  CLAUDE.md L76, L90 and L98.

**Differences.** None of these was reworded; each is for your ruling.

- **M1. "superseded by `kinematics/extract_track_metrics.py`"**
  CLAUDE.md names the replacement as the `kinematics/` stage, not one file.
  L90 says *"superseded by `kinematics/`"*, and L76 says *"This replaces the
  two per-branch scripts"*, where "This" is the whole stage 7. That stage is
  7a `extract_track_metrics.py` plus 7b `summarize_track_metrics.py`, and the
  summary report is what v3/v4 used to write too.
  *Suggested:* `kinematics/`.
- **M2. "a different stage"**
  v3 and v4 *were* stage 7: L90's row is headed "Kinematics (stage 7)". Their
  replacement is the same stage. It is different only from the stages that
  run in `alignment_N/`, which are 4 (alignment) and 6 (conversion), plus the
  overlay steps. Read literally, "a different stage" is inaccurate.
- **M3. "they have no tie to the alignment directories"**
  The committed history contradicts this. Both scripts lived in
  `alignment_1/` and `alignment_2/` from `5dc8797` until `52c7a42` (§2).
  CLAUDE.md still describes them as per-branch: L90 places v3 in the
  uncorrected column and v4 in the corrected column, and L98 calls them *"the
  old per-branch v3/v4"*. The README (unchanged, out of scope) goes further.
  Its L114–L115 read: *"Each branch is a self-contained sequence: align →
  overlay (visualisation) → convert → overlay-collect → kinematics."* That
  sentence is plausibly where the self-containment motive came from.
  What the scripts lack is a *live* tie, not any tie.
- **M4. "The move was once made for self-containment and reverted"**
  There is no trace of this in git (§2), and "self-containment" is recorded
  nowhere. The one move that git *does* record went the other way. See the
  ruling point in §7.
- **M5. "every script in them is current"**
  This is true under the branch section: L82 calls both branches
  *"intentionally-kept"*. It does not hold under the literal version rule.
  CLAUDE.md L50 names only **two** exceptions to "highest version is
  current", `segmentation_checks/` and `segmentation_corrections/`. Yet
  `alignment_1/` holds `_v4`/`_v2`/`_v2`/`_v1`, while `alignment_2/` holds
  `_v5`/`_v3`/`_v3`/`_v2` of the same four scripts. L98 also says that
  `alignment_1/` *"exists only to reproduce the uncorrected-timing result for
  comparison"*. So "current" means "live and kept on purpose", not "latest
  version". See UNREQUESTED item 1.
- **M6. "nor into `archive/` subfolders inside them"**
  That option is recorded nowhere. The case-insensitive search for
  `archive/` subfolders, `alignment_N/archive` and `alignment_1/archive` found
  no match in the tree. As a rule it is harmless, but nothing in the record
  says it was ever proposed.

---

## 5. TESTS

**No test script was run.** There is no automated test suite (DECISIONS.md,
Tests), and both hand-run scripts cover `kinematics/`, which this change does
not touch. §6 shows that `DECISIONS.md` is the only tracked file changed.

The character scan uses a script file (`scan_decisions_003.py`, driven by
`tests_003.sh`) and runs on a copy of `DECISIONS.md` taken before the edit and
on the live file:

```
######## BEFORE (pre-edit copy of DECISIONS.md) ########
measured: bytes           = 2722
measured: sha256          = e712f4a118d9260bb798c62d6f9cdb47eb6fe67f2b841f219d3da05a4d4c6f81
measured: utf-8 decode    = ok
VERDICT: valid UTF-8
measured: first 3 bytes   = b'# D'
VERDICT: no BOM
measured: control chars other than TAB/CR/LF = 0 []
VERDICT: no stray control characters
measured: CRLF=0 bare-LF=66 bare-CR=0
VERDICT: line-ending style = LF
measured: ends with newline = True
measured: lines (split on newline) = 67
measured: longest line in file = 79 chars (L45)
measured: non-ASCII chars in file = ['U+2014', 'U+2026']
measured: section '## Superseded stage-7 scripts' not present
######## AFTER (DECISIONS.md in the working tree) ########
measured: file            = DECISIONS.md
measured: bytes           = 3397
measured: sha256          = 0fca324bfdad7bc51f8122b01a817fcd0f06bcb4cbbcb838f6e616f82d28eac7
measured: utf-8 decode    = ok
VERDICT: valid UTF-8
measured: first 3 bytes   = b'# D'
VERDICT: no BOM
measured: control chars other than TAB/CR/LF = 0 []
VERDICT: no stray control characters
measured: CRLF=0 bare-LF=80 bare-CR=0
VERDICT: line-ending style = LF
measured: ends with newline = True
measured: lines (split on newline) = 81
measured: longest line in file = 79 chars (L45)
measured: non-ASCII chars in file = ['U+2014', 'U+2026']
measured: new section = L68-L80 (13 lines)
measured: longest line in new section = 77 chars (L76)
```

The BEFORE block's first line, which gives the scratchpad path of the copy, is
left out above. The full output, including the per-line listing, is in §3.

- **Valid UTF-8, no BOM, no control characters other than TAB, CR and LF:**
  PASS.
- **Longest line of the new section:** 77 characters (L76–L78). The file's
  widest line is still 79.
- **Line endings:** LF before and LF after. Unchanged.
- **No new character types:** the non-ASCII set is still exactly U+2014 and
  U+2026. The new section's em dashes are U+2014, the same codepoint the file
  already used.

---

## 6. SCOPE, CARRIED REPORTS AND DIFF ARTIFACT

Output of `artifact_003.sh`, run last, after this report was complete:

```
=== git add -N (new untracked files, from git status) ===
exit=0
=== generate artifact ===
exit=0
=== regenerate the same diff OUTSIDE the repo ===
exit=0
=== cmp artifact vs external regeneration ===
cmp: EXIT 0 - identical
=== artifact numstat (git apply --numstat on the artifact) ===
14	0	DECISIONS.md
386	0	prompt_outputs/002-docs-commit.md
295	0	prompt_outputs/002-docs-push.md
530	0	prompt_outputs/003-archive-implement.md
=== tracked files changed vs HEAD, intent-to-add excluded (git diff HEAD --name-only --diff-filter=M) ===
DECISIONS.md
=== staged content (git diff --cached --name-only) ===
  (nothing above = nothing staged)
=== git status --porcelain -uall ===
 M DECISIONS.md
 A prompt_outputs/002-docs-commit.md
 A prompt_outputs/002-docs-push.md
 A prompt_outputs/003-archive-implement.md
?? prompt_outputs/003-archive.diff.txt
=== carried reports after the artifact run: bytes + sha256 ===
14396 bytes  prompt_outputs/002-docs-commit.md
4b4b9fc137944764f75e4e6e9422aaddf76b684a443df74ed9a1234abcaf955c *prompt_outputs/002-docs-commit.md
10276 bytes  prompt_outputs/002-docs-push.md
86a4059124cf5c4fac1dfec2ed172c885e97c59311738b34087baffa965efe85 *prompt_outputs/002-docs-push.md
```

**Scope.** `DECISIONS.md` is the only tracked file that changed, and nothing
is staged. In the status list, the ` A` entries are intent-to-add markers from
the required `git add -N`, not staged content. The last `??` entry is the
artifact itself. `CLAUDE.md`, `GOTCHAS.md`, `README.md`, `archive/`,
`alignment_1/` and `alignment_2/` are unchanged.

**Carried reports: unchanged.** Before any edit, `state_003.sh` measured:

```
=== carried reports: bytes + sha256 ===
14396 bytes  prompt_outputs/002-docs-commit.md
4b4b9fc137944764f75e4e6e9422aaddf76b684a443df74ed9a1234abcaf955c *prompt_outputs/002-docs-commit.md
10276 bytes  prompt_outputs/002-docs-push.md
86a4059124cf5c4fac1dfec2ed172c885e97c59311738b34087baffa965efe85 *prompt_outputs/002-docs-push.md
```

The final block of `artifact_003.sh`'s output measures them again after the
run. Both carried reports are in the artifact as new files.

**Artifact.** The artifact and the regeneration written outside the
repository are byte-identical (cmp exit 0).

This report is inside the artifact and also quotes the artifact's numstat. To
keep both final at once, I pasted `artifact_003.sh`'s output into the block
above with `fill_003.py` and re-ran the script until the output stopped
changing. Once the block has a fixed number of lines, this report's own
numstat row stays the same, so the pasted numstat is final.
`compare_numstat_003.py` confirmed that the quoted numstat matches the
regenerated artifact. Its output is in the chat reply, because pasting it here
would change the artifact.

---

## 7. POINTS FOR YOUR RULING

**P1. The last sentence of the *Why:* paragraph.** It is kept as written until
you rule.

Git has no trace of the move and revert (§2). The history holds a different
event, the archiving in `52c7a42`, which is what `git log --follow` will show
a future reader. The options:

- **Keep.** The sentence is accurate only against the task-001 reports, and
  its motive ("self-containment") is recorded nowhere.
- **Drop.** The rule and the rest of the *Why:* still stand without it.
  However, the one fact most likely to make a future session reopen the
  question goes unexplained: that the scripts once lived in `alignment_N/`.
- **Reword (recommended),** so that it points at what can actually be
  checked. For example: *"Both lived in `alignment_1/` and `alignment_2/`
  until `52c7a42` archived them; moving them back was tried in task 000 and
  reverted before commit (`prompt_outputs/001-bootstrap-gate.md`, R6). This
  records why they stay in `archive/`."* Whether to keep "for
  self-containment" is your call, since only you can vouch for that motive.

**P2. M1 to M3, M5 and M6 in §4.** Each is a factual difference in the
proposed wording. My recommendations: M1, write `kinematics/` instead of the
single file; M2 and M3, replace "a different stage, so they have no tie to the
alignment directories" with wording about having no *live* tie (for example,
"so nothing in the alignment directories uses them"). M5 and M6 are
acceptable as written if you accept those readings.

**P3. Placement.** At the end of the file, as proposed, and I recommend it.
The file has no topical order: its entries run Tests, `prompt_outputs/`,
Commit trailers, Line endings, which is the order the rulings were made.
Appending keeps that order, and no other position fits better.

---

## 8. ERRATA TO EARLIER REPORTS

- `002-docs-push.md` §4 item 3 lists the 73-column working-rules bullet at
  CLAUDE.md L27 as one character over. Per this prompt it is inherited
  verbatim from WORKFLOW.md and **is not a defect**, so that item is
  withdrawn. It is not fixed or re-flagged here.
- `002-docs-push.md` §4 item 5 and `001-bootstrap-gate.md` R6 both carry task
  000's `archive/` -> `alignment_N/` move as pending "as its own later task".
  Per this prompt's ruling, **the move is dropped**, so it is no longer
  pending.
- **This report, one breach of the working rules.** While editing, I checked
  append-only once with a `python -c` one-liner, which breaks "measure with a
  script file, never a shell one-liner". I discarded that result and re-ran
  the check as the script file `prefix_check_003.py`. The output quoted in §3
  comes from the script file.

---

## 9. UNREQUESTED — ACCEPT OR DROP

None of these is implemented.

1. **CLAUDE.md L50 undercounts the exceptions to the version rule.** It says
   *"Two sections do say otherwise"*, but the two-branch section (L80–L98)
   also keeps lower versions as live scripts: `alignment_1/`'s `_v4`/`_v2`/
   `_v1` sit alongside `alignment_2/`'s `_v5`/`_v3`/`_v2`. This is the same
   gap as M5.
2. **DECISIONS.md has no cross-reference to R6.** The Commit trailers entry
   opens with *"Supersedes the ruling recorded as R5 in …"*. This new
   decision likewise closes R6's *"returns as its own later task"*, so a
   matching "Supersedes R6" line would keep the audit trail consistent.
3. **Git warns about `DECISIONS.md` line endings.** `git diff HEAD` prints
   *"warning: in the working copy of 'DECISIONS.md', LF will be replaced by
   CRLF the next time Git touches it"* (`core.autocrlf=true`, no
   `.gitattributes`). The file is LF before and after this task (§5). This is
   task 004's territory and is recorded only so the warning is not mistaken
   for a change made here.
