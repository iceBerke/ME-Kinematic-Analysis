# 003 — archive — gate

**AMENDED AND STAGED. STOPPED BEFORE COMMIT.** Three changes, and nothing
else:

- The *Why:* paragraph of the `DECISIONS.md` section "Superseded stage-7
  scripts" now carries your ruled text.
- `BACKLOG.md` is created with the two deferred items.
- Exactly the seven listed paths are staged, by explicit path.

Nothing is committed or pushed. The frozen implement report and the two
carried 002 reports are byte-identical to the values in the prompt, both
before and after staging (§1, §7).

**Every claim in the prompt checked out, with two small wording
differences in BACKLOG.md** (§4, D1–D2). One is a case difference in a
quotation. The other is a README sentence that the README itself qualifies
two lines later. Neither was reworded.

**No test script was run.** There is no automated test suite (DECISIONS.md,
Tests), and nothing in `kinematics/` is touched. §5 has the character scan.

Scripts used, all outside the repository (session scratchpad):

```
gate_pre_003.sh       report hashes, HEAD, status, 52c7a42, R6, ls-files, quotes
amend_003.py          replaces the Why paragraph; creates BACKLOG.md (79, LF)
gate_checks_003.py    prefix checks vs HEAD and pre-edit copy; character scan
measure_msg_003.py    proposed commit message, every line with its length
gate_stage_003.sh     add -N, artifact, outside regen, cmp, stage, numstat
fill_gate_003.py      pastes gate_stage_003.sh output into §7 of this report
```

---

## 0. RULINGS RECORDED

- **R1.** The *Why:* paragraph is replaced as in CHANGES 1. "for
  self-containment" is kept, and you vouch for that motive.
- **R2.** The clause "nor into `archive/` subfolders inside them" is kept.
- **R3.** The section stays at the end of `DECISIONS.md`.
- **R4.** The README's stale branch sequence is deferred to `BACKLOG.md`,
  and `BACKLOG.md` is created in this task.
- **Implement report, UNREQUESTED item 1** (CLAUDE.md undercounts the
  version-rule exceptions): deferred to `BACKLOG.md`.
- **Implement report, UNREQUESTED item 2** (cross-reference to R6):
  accepted, as the R6 citation inside R1's text. There is no separate
  "Supersedes" line.
- **Implement report, UNREQUESTED item 3** (autocrlf warning): dropped, no
  action.
- **Errata accepted.** The implement report's §8 withdrew
  `002-docs-push.md` §4 item 3 and closed the pending task-000 move. Both
  stand.

---

## 1. PRE-FLIGHT

Output of `gate_pre_003.sh`, run before any edit:

```
=== frozen + carried reports: bytes + sha256 ===
28600 bytes  prompt_outputs/003-archive-implement.md
db132562edd2d67dda41dac689af9fbee71284cd5287db96bbb418b2c9c604fa *prompt_outputs/003-archive-implement.md
14396 bytes  prompt_outputs/002-docs-commit.md
4b4b9fc137944764f75e4e6e9422aaddf76b684a443df74ed9a1234abcaf955c *prompt_outputs/002-docs-commit.md
10276 bytes  prompt_outputs/002-docs-push.md
86a4059124cf5c4fac1dfec2ed172c885e97c59311738b34087baffa965efe85 *prompt_outputs/002-docs-push.md
=== HEAD / origin/main ===
HEAD:        5fd03f5dddf0de2cd909e11f2652739a0c872295
origin/main: 5fd03f5dddf0de2cd909e11f2652739a0c872295
=== git status --porcelain -uall ===
 M DECISIONS.md
 A prompt_outputs/002-docs-commit.md
 A prompt_outputs/002-docs-push.md
 A prompt_outputs/003-archive-implement.md
?? prompt_outputs/003-archive.diff.txt
=== staged content (git diff --cached --name-only) ===
  (nothing above = nothing staged)
=== BACKLOG.md exists? ===
ls: cannot access 'BACKLOG.md': No such file or directory
```

- **All three protected reports match the prompt's values exactly**, in both
  byte count and SHA-256.
- The state is where the implement step left it. The ` A` entries are its
  intent-to-add markers, and nothing is staged.
- `BACKLOG.md` did not exist yet.

---

## 2. CHANGE 1 — DECISIONS.md *Why:* PARAGRAPH

`amend_003.py` replaced the old *Why:* paragraph, which ran from its
`*Why:*` to the end of the file. It wrapped your text with textwrap at
width 79 and wrote it with LF, the same method the implement step used. The
wording is yours, byte for byte, apart from line breaks.

**The claims in the text, checked against the files** (`gate_pre_003.sh`):

```
=== git show --stat --format='%h %s' 52c7a42 ===
52c7a42 Archive the superseded stage-7 scripts v3/v4

 CLAUDE.md                                                 | 6 +++---
 README.md                                                 | 9 ++++-----
 {alignment_1 => archive}/final_kin_param_extraction_v3.py | 0
 {alignment_2 => archive}/final_kin_param_extraction_v4.py | 0
 kinematics/extract_track_metrics.py                       | 6 +++---
 5 files changed, 10 insertions(+), 11 deletions(-)
=== 001-bootstrap-gate.md R6 (grep -n -A6 '### R6') ===
93:### R6 — Task 000 closed with no commit
94-
95-Closed. Its `settings.json` change lives outside the repository
96-(`~/.claude/settings.json`, `cleanupPeriodDays`). Its `archive/` ->
97-`alignment_N/` move was reverted and returns as its own later task. Nothing
98-from task 000 is staged or committed here.
99-
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

- **`52c7a42` is the archiving commit:** confirmed. It renames
  `alignment_1/…_v3.py` and `alignment_2/…_v4.py` into `archive/` (the
  implement report's §2 has the full `--follow` history).
- **R6 exists and supports the citation:** confirmed. It sits at
  `001-bootstrap-gate.md` L93. Its heading is "Task 000 closed with no
  commit", and its body says that the `archive/` -> `alignment_N/` move "was
  reverted". Together those support "tried in task 000 and reverted before
  commit". **R6 does not state the self-containment motive.** That half of
  the sentence rests on your ruling in R1, not on the cited file.
- **The four steps named are exactly what each folder holds:** confirmed.
  Each folder holds four tracked scripts, one per step: alignment, overlay,
  conversion and overlay-copies.
- **"every script in them is in live use":** this is your wording, and it
  resolves the implement report's M5, because it no longer claims "current".
  CLAUDE.md L82 calls both branches *"intentionally-kept"*.

**The rest of the file is untouched.** Output of `gate_checks_003.py`:

```
=== DECISIONS.md: committed HEAD blob is a byte prefix of the edited file ===
measured: HEAD bytes = 2722, edited bytes = 3503, prefix = True
VERDICT: everything above the section is byte-identical to HEAD
=== DECISIONS.md: heading + bold rule unchanged, only the Why paragraph replaced ===
measured: Why offset before = 2929, after = 2929
measured: bytes before the Why paragraph identical = True (2929 bytes)
measured: section heading..rule = bytes 2723..2929 of the edited file
VERDICT: heading and bold rule byte-identical; only the Why paragraph changed
measured: old Why paragraph bytes = 468, new = 574
```

The first check compares against the committed `HEAD:DECISIONS.md`. It
shows that everything above the new section is byte-identical to HEAD. The
second check compares against a copy taken just before this edit. It shows
that the heading, the bold rule and the blank line after it did not change
by a single byte.

The section as it now stands:

```
  L68  len=29 |## Superseded stage-7 scripts|
  L69  len= 0 ||
  L70  len=76 |**`final_kin_param_extraction_v3.py` and `_v4.py` stay in `archive/`.** They|
  L71  len=72 |are not moved into `alignment_1/` or `alignment_2/`, nor into `archive/`|
  L72  len=23 |subfolders inside them.|
  L73  len= 0 ||
  L74  len=75 |*Why:* both were stage 7 and were superseded by the `kinematics/` stage, so|
  L75  len=78 |nothing in the alignment directories uses them. Those directories are live run|
  L76  len=78 |directories — the alignment, overlay, conversion and overlay-collect steps run|
  L77  len=78 |from them — and every script in them is in live use, so moving the old scripts|
  L78  len=77 |back would put dead code among live scripts. Both lived in `alignment_1/` and|
  L79  len=66 |`alignment_2/` until `52c7a42` archived them; moving them back for|
  L80  len=65 |self-containment was tried in task 000 and reverted before commit|
  L81  len=45 |(`prompt_outputs/001-bootstrap-gate.md`, R6).|
```

---

## 3. CHANGE 2 — BACKLOG.md

`amend_003.py` created `BACKLOG.md` at the repository root. It uses your
proposed content verbatim, with each paragraph wrapped by textwrap at width
79 and LF line endings. Headings and blank-line spacing follow
`DECISIONS.md` and `GOTCHAS.md`: a title, then an intro paragraph whose
last sentence carries the cross-links, then `##` items. The file as
created, from `gate_checks_003.py`:

```
  L1   len= 9 |# BACKLOG|
  L2   len= 0 ||
  L3   len=71 |Deferred work, each item with what is wrong and where it came from. Not|
  L4   len=75 |append-only: the task that completes an item removes it. Items are cited by|
  L5   len=75 |name. Project decisions live in [DECISIONS.md](DECISIONS.md), and recurring|
  L6   len=37 |mistakes in [GOTCHAS.md](GOTCHAS.md).|
  L7   len= 0 ||
  L8   len=32 |## README: stale branch sequence|
  L9   len= 0 ||
  L10  len=79 |`README.md` describes each alignment branch as a self-contained sequence ending|
  L11  len=77 |in kinematics ("align → overlay (visualisation) → convert → overlay-collect →|
  L12  len=74 |kinematics"). Stage 7 is now the shared `kinematics/` stage and belongs to|
  L13  len=15 |neither branch.|
  L14  len= 0 ||
  L15  len=66 |*Deferred from task 003:* a README fix, outside that task's scope.|
  L16  len= 0 ||
  L17  len=50 |## CLAUDE.md: version-rule exceptions undercounted|
  L18  len= 0 ||
  L19  len=72 |The "Versioned scripts" section says two sections are exceptions to "the|
  L20  len=77 |highest version number is the current one", naming `segmentation_checks/` and|
  L21  len=78 |`segmentation_corrections/`. The two-branch section is a third: `alignment_1/`|
  L22  len=71 |keeps lower versions than `alignment_2/` as live scripts, deliberately.|
  L23  len= 0 ||
  L24  len=69 |*Deferred from task 003:* a CLAUDE.md fix, outside that task's scope.|
```

**A style note, not a defect.** The existing two files put their
cross-link on its own line, directly under the title. In `BACKLOG.md` it is
the last sentence of the intro paragraph, because that is how your proposed
content has it.

---

## 4. THE SENTENCES THE TWO BACKLOG ITEMS DESCRIBE

Output of `gate_pre_003.sh`, where `sed` prints the line number above each
line:

```
=== README.md L114-L118 ===
114
Each branch is a self-contained sequence: align → overlay (visualisation) → convert →
115
overlay-collect → kinematics.
116

117
Stage 7 is the exception: the two branch scripts have been replaced by the shared
118
`kinematics/` folder, and it is the only stage that **asks** for its settings instead of
=== CLAUDE.md L50 ===
50
Many scripts exist as `_v1`/`_v2`/`_v3`/`_v4`/`_v5` (and `_part1`/`_complete`) variants. **The highest version number is the current one unless this file says otherwise**; lower versions are kept for history. When editing behavior, edit the latest version unless explicitly told otherwise. Two sections do say otherwise, both deliberately: `segmentation_checks/` keeps `error_analysis_v1.py` alongside `_v3.py` because the two flag different defects, and the `segmentation_corrections/` scripts `correction_v1`–`_v4` are not a version progression at all — each solves a different segmentation defect.
=== CLAUDE.md L82 ===
82
Stages 4 (alignment) and 6 (unit conversion) each exist in two intentionally-kept variants that form **two parallel end-to-end branches**. The alignment step and its matching conversion step are grouped together per branch:
```

**Item "README: stale branch sequence".** The sentence is README
L114–L115. The quotation in `BACKLOG.md` matches it character for
character, arrows included.

- **D1.** README L117–L118 already qualify that sentence: *"Stage 7 is the
  exception: the two branch scripts have been replaced by the shared
  `kinematics/` folder"*. So the README is **self-contradictory across
  three lines**, rather than stale with nothing correcting it. The backlog
  item is still accurate, but whoever fixes it should edit L114–L115 and
  L117 together. Not reworded.

**Item "CLAUDE.md: version-rule exceptions undercounted".** The sentence is
CLAUDE.md L50: *"Two sections do say otherwise, both deliberately:
`segmentation_checks/` … and the `segmentation_corrections/` scripts …"*.
The item's description matches, and L82 confirms that the two-branch
section keeps both variants on purpose.

- **D2.** The item quotes *"the highest version number is the current
  one"* with a lowercase "the". The source at L50 reads *"**The highest
  version number is the current one unless this file says otherwise**"*,
  with a capital T, in bold, and continuing past the quoted part. The
  difference is case only, inside a mid-sentence quotation. Not reworded.

---

## 5. TESTS

**No test script was run.** There is no automated test suite (DECISIONS.md,
Tests), and this task touches nothing in `kinematics/` and no `.py` file
(§7).

Character scan, from the script file `gate_checks_003.py` (the per-line
listings are in §2 and §3):

```
--- DECISIONS.md ---
measured: bytes = 3503
measured: utf-8 decode = ok  -> VERDICT: valid UTF-8
measured: first 3 bytes = b'# D'  -> VERDICT: no BOM
measured: control chars other than TAB/CR/LF = 0 []  -> VERDICT: none
measured: CRLF=0 bare-LF=81 bare-CR=0  -> VERDICT: line endings = LF
measured: ends with newline = True, ends with blank line = False
measured: lines = 81; longest = 79 chars (L45)  -> VERDICT: within 79
measured: non-ASCII = ['U+2014', 'U+2026']
--- BACKLOG.md ---
measured: bytes = 1059
measured: utf-8 decode = ok  -> VERDICT: valid UTF-8
measured: first 3 bytes = b'# B'  -> VERDICT: no BOM
measured: control chars other than TAB/CR/LF = 0 []  -> VERDICT: none
measured: CRLF=0 bare-LF=24 bare-CR=0  -> VERDICT: line endings = LF
measured: ends with newline = True, ends with blank line = False
measured: lines = 24; longest = 79 chars (L10)  -> VERDICT: within 79
measured: non-ASCII = ['U+2192']
```

Both files are valid UTF-8, with no BOM and no stray control characters,
and both are pure LF. `DECISIONS.md` is still LF, as it was before and as
the implement report measured, so its line endings are not changed.

- In `DECISIONS.md`, the longest line is still the pre-existing L45, and no
  new-section line exceeds 78 characters.
- In `BACKLOG.md`, the longest line is 79 characters, at L10.
- `BACKLOG.md`'s only non-ASCII character is U+2192, the arrow in the
  README quotation.

---

## 6. PROPOSED COMMIT MESSAGE

The message is measured by the script file `measure_msg_003.py`. It has no
trailer: COMMIT appends the one agreed trailer, per DECISIONS.md.

```
measured: bytes = 471, sha256 = ee5499bcd31482d60c6075fe3078c9137b49f6e1f8af5c08da4ac230407710df
measured: non-ASCII chars = []
measured: CR present = False
measured: trailer-like lines = []
L1   len=40 max=50  OK  |Record archive/ decision; add BACKLOG.md|
L2   len= 0  blank separator: OK
L3   len=58 max=72  OK  |Record in DECISIONS.md that the superseded stage-7 scripts|
L4   len=66 max=72  OK  |final_kin_param_extraction_v3.py and _v4.py stay in archive/. This|
L5   len=60 max=72  OK  |closes the move left pending by R6 in 001-bootstrap-gate.md.|
L6   len= 0 max=72  OK  ||
L7   len=64 max=72  OK  |Create BACKLOG.md with two deferred docs fixes: the stale branch|
L8   len=69 max=72  OK  |sequence in README.md and the undercounted version-rule exceptions in|
L9   len=10 max=72  OK  |CLAUDE.md.|
L10  len= 0 max=72  OK  ||
L11  len=68 max=72  OK  |Add the task 003 reports and diff artifact, and the carried task 002|
L12  len=24 max=72  OK  |commit and push reports.|
measured: subject = 40, longest body line = 69
VERDICT: all lines within limits
```

The message is in the imperative mood and pure ASCII. Its bytes and hash
are those of the scratchpad file `proposed_msg_003.txt`, which ends with a
single LF.

**Every claim in it holds against the staged set** (§7):

- **"stay in archive/"**: this is the rule paragraph of the new
  `DECISIONS.md` section.
- **"closes the move left pending by R6"**: R6 says the move "returns as
  its own later task" (§2), and this entry settles it.
- **"two deferred docs fixes"**: these are the README item and the
  CLAUDE.md item in `BACKLOG.md`.
- **"the task 003 reports and diff artifact"**: these are
  `003-archive-implement.md`, `003-archive-gate.md` and
  `003-archive.diff.txt`.
- **"the carried task 002 commit and push reports"**: these are
  `002-docs-commit.md` and `002-docs-push.md`.

**Not edited.**

---

## 7. ARTIFACT, STAGING AND FINAL STATE

Output of `gate_stage_003.sh`, run last, after this report was complete:

```
=== untracked before add -N (git ls-files --others --exclude-standard) ===
=== git add -N BACKLOG.md prompt_outputs/003-archive-gate.md ===
exit=0
=== generate artifact ===
exit=0
=== regenerate the same diff OUTSIDE the repo ===
exit=0
=== cmp artifact vs external regeneration ===
cmp: EXIT 0 - identical
=== artifact numstat (git apply --numstat on the artifact) ===
24	0	BACKLOG.md
15	0	DECISIONS.md
386	0	prompt_outputs/002-docs-commit.md
295	0	prompt_outputs/002-docs-push.md
465	0	prompt_outputs/003-archive-gate.md
530	0	prompt_outputs/003-archive-implement.md
=== stage by explicit path ===
exit=0
=== git diff --cached --numstat ===
24	0	BACKLOG.md
15	0	DECISIONS.md
386	0	prompt_outputs/002-docs-commit.md
295	0	prompt_outputs/002-docs-push.md
465	0	prompt_outputs/003-archive-gate.md
530	0	prompt_outputs/003-archive-implement.md
1753	0	prompt_outputs/003-archive.diff.txt
=== worktree vs index (git diff --name-only; empty = all staged as on disk) ===
=== git status --porcelain -uall ===
A  BACKLOG.md
M  DECISIONS.md
A  prompt_outputs/002-docs-commit.md
A  prompt_outputs/002-docs-push.md
A  prompt_outputs/003-archive-gate.md
A  prompt_outputs/003-archive-implement.md
A  prompt_outputs/003-archive.diff.txt
=== frozen + carried reports after staging: bytes + sha256 ===
28600 bytes  prompt_outputs/003-archive-implement.md
db132562edd2d67dda41dac689af9fbee71284cd5287db96bbb418b2c9c604fa *prompt_outputs/003-archive-implement.md
14396 bytes  prompt_outputs/002-docs-commit.md
4b4b9fc137944764f75e4e6e9422aaddf76b684a443df74ed9a1234abcaf955c *prompt_outputs/002-docs-commit.md
10276 bytes  prompt_outputs/002-docs-push.md
86a4059124cf5c4fac1dfec2ed172c885e97c59311738b34087baffa965efe85 *prompt_outputs/002-docs-push.md
```

**Staging list against git status.** The block comes from the script's
final pass. By then the first pass had already added every file, so its
"untracked before add -N" list is empty. The status list after staging
shows exactly the seven listed paths, all staged, with nothing unstaged and
nothing untracked. **No file is missing from the list, and nothing outside
it is staged.**

**Everything staged matches the working tree.** `git diff --name-only`
prints nothing.

**No `kinematics/` path and no `.py` file** is in the staged set.

**The protected reports are still byte-identical** to the prompt's values
after staging.

**The artifact matches an outside regeneration.** `cmp` against the
regeneration written outside the repository returned exit 0.

**Why the pasted block can be final.** This report sits inside both the
artifact and the staged set, and it quotes the numstat of both, so the two
depend on each other. `fill_gate_003.py` pasted the script's output into
the block above, and I re-ran the script until pasting changed nothing.
Once the block has a fixed number of lines, the line counts it quotes no
longer move. The final pass re-staged this exact file, so the index,
the artifact and this block agree.

---

## 8. ERRATA TO EARLIER REPORTS

None found. The implement report's §8 errata stand as accepted (§0).

---

## 9. UNREQUESTED — ACCEPT OR DROP

None of these is implemented.

1. **Fix README L114–L115 and L117 together** when the BACKLOG item is
   worked (D1). The backlog item could name L117 too, so that the person
   fixing it sees both lines.
2. **Match the quotation in BACKLOG.md to its source** (D2): a capital "The"
   and, optionally, the full clause "unless this file says otherwise".
3. **Nothing in the tree points at BACKLOG.md** except BACKLOG.md itself.
   CLAUDE.md's pointer bullet deliberately stays as it is in this task, and
   `DECISIONS.md` and `GOTCHAS.md` do not link to it either. A later task
   could add those links.
