# 001 — bootstrap — gate

Task: settle the rulings, record errata against the frozen implement report,
verify the CLAUDE.md edit is unchanged, regenerate and verify the diff artifact,
stage by explicit path, propose the commit message.

**Stopped before committing: nothing committed, nothing pushed.**

Carried report: `prompt_outputs/001-bootstrap-implement.md` — **frozen, not
edited by this step.** Corrections to it are recorded as errata in §2 below.

**No test script was run in this task.** Per ruling R1 there is no automated
test suite; the two hand-run scripts live in `kinematics/`, and this task
touches no file in `kinematics/`. Nothing here reads or writes a dataset.

Scripts used, all outside the repository, in the session scratchpad:

```
verify_gate.py      CLAUDE.md byte-identity + E1/E2 re-derived from the
                    frozen report's own pasted lists
measure_msg.py      commit-message subject/body length measurement
```

---

## 1. RULINGS RECORDED

### R1 — Tests

There is no automated test suite. Two hand-run scripts exist:

- `kinematics/test_stage7_structure.py` — needs a real dataset root in its
  top-of-file `ROOT_DIRECTORY`.
- `kinematics/demo_test_stage7.py` — synthetic, needs no data.

**Rule:** tasks touching `kinematics/` run `demo_test_stage7.py` before push,
and `test_stage7_structure.py` as well when a dataset root is available.
Everything else is manual-test-only.

**This task touches neither, so no test script is run here.**

### R2 — `prompt_outputs/` is tracked

Both the `.md` reports and the `.diff.txt` artifacts are tracked. Nothing is
added to `.gitignore`, and `.gitignore` was not modified by this task.

### R3 — CLAUDE.md content defects deferred to task 002

Deferred, not fixed here:

| Ref | Defect |
|---|---|
| D1 | "no test suite" versus the two hand-run stage-7 test scripts |
| D2 | "highest version number is the current one" versus kept `error_analysis_v1` and the "not a version progression" corrections |
| D3 | U+00B5 MICRO SIGN and U+03BC GREEK SMALL LETTER MU both used |
| D5 | "all three are kept" introducing four `correction_v*.py` scripts |
| D6 | the `archive/` scripts CLAUDE.md never names in full |

(The implement report numbered the last two as findings inside §5 and §6c rather
than as D5/D6; the numbering here follows this prompt's ruling.)

### R4 — `.gitattributes` deferred to its own task

Normalising line endings would produce a large whitespace-only diff that must
not be mixed with content changes. The implement report measured the current
split as `CRLF=8, LF=41` with no `.gitattributes` and `core.autocrlf=true`.

### R5 — Commit trailers

Every commit for this project keeps Claude Code's `Co-Authored-By` trailer and
the `Claude-Session` trailer. **The approved message excludes them; COMMIT adds
exactly those two; PUSH verifies them.**

Existing format on the three most recent commits:

```
=== trailers on the last 3 commits ===
--- 68cbcf3
Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01QFdYr8j8nGbkwR2qXpyvep
--- a1afb5c
Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01QFdYr8j8nGbkwR2qXpyvep
--- c9883fc
Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01QFdYr8j8nGbkwR2qXpyvep
```

Two values change for this commit and are surfaced in §7, not decided here: the
model name in the `Co-Authored-By` line, and the `Claude-Session` URL, which is
not derivable from the repository.

### R6 — Task 000 closed with no commit

Closed. Its `settings.json` change lives outside the repository
(`~/.claude/settings.json`, `cleanupPeriodDays`). Its `archive/` ->
`alignment_N/` move was reverted and returns as its own later task. Nothing
from task 000 is staged or committed here.

---

## 2. ERRATA AGAINST THE FROZEN IMPLEMENT REPORT

Each correction was re-derived from the frozen report's **own pasted c1/c2
lists** by `verify_gate.py`, not taken on faith from this prompt.

```
========================================================================
C2. ERRATA E1/E2 - RE-DERIVED FROM THE FROZEN REPORT'S OWN LISTS
========================================================================
measured: c1 header declares  = 13
measured: c1 entries parsed   = 13
measured: c2 header declares  = 11
measured: c2 entries parsed   = 11
VERDICT: list lengths match their headers

--- E1: 'the six archive/ scripts in c1' ---
measured: c1 entries under archive/ = 7
    archive/blob_detection_ME_complete.py
    archive/blob_detection_ME_part1.py
    archive/blob_detection_v2.py
    archive/blob_parameters_check_v1.py
    archive/blob_parameters_check_v2.py
    archive/error_analysis_v2.py
    archive/final_kin_param_extraction_v2.py
measured: frozen prose says 'the six archive/ scripts in c1' = True
VERDICT: E1 CORRECT - prose says six, the list holds 7; the right count is 7

--- E2: 'accounts for 8 of the 11 c2 entries and 7 of the 13 c1 entries' ---
measured: c1 entries under alignment_1/ or alignment_2/ = 6
    alignment_1/blob_mhi_tracks_alignment_v4.py
    alignment_1/mhi_overlay_copies_v1.py
    alignment_2/mhi_overlay_copies_v2.py
    alignment_1/mhi_overlay_v2.py
    alignment_2/mhi_overlay_v3.py
    alignment_1/time_coordinates_conversions_v2.py
measured: c1 entries elsewhere = 0
measured: c2 entries that are elided table labels (start '..._') = 8
measured: frozen prose says '7 of the 13 c1 entries' = True
measured: arithmetic 6 + 7 = 13  (c1 total = 13)
VERDICT: E2 CORRECT - prose says 7, the c1 figure is 6; 6 + 7 = 13 checks out

--- why 8 elided c2 labels correspond to only 6 c1 entries ---
    blob_mhi_tracks_alignment_v4.py            named with full path at L-; in c1: yes
    blob_mhi_tracks_alignment_v5.py            named with full path at L[71]; in c1: NO
    mhi_overlay_copies_v1.py                   named with full path at L-; in c1: yes
    mhi_overlay_copies_v2.py                   named with full path at L-; in c1: yes
    mhi_overlay_v2.py                          named with full path at L-; in c1: yes
    mhi_overlay_v3.py                          named with full path at L-; in c1: yes
    time_coordinates_conversions_v2.py         named with full path at L-; in c1: yes
    time_coordinates_conversions_v3.py         named with full path at L[73]; in c1: NO
measured: elided labels also named with a full path elsewhere = 2
VERDICT: consistent - 8 table labels minus 2 named in full = 6 c1 entries
```

### E1 — CONFIRMED CORRECT

`001-bootstrap-implement.md` §6c prose reads "the genuinely unmentioned files
are the **six** `archive/` scripts in c1", then lists six names followed by
"plus `final_kin_param_extraction_v2.py`" — seven names in all. **The correct
count is seven**, matching the seven `archive/` entries in the pasted c1 list.

### E2 — CONFIRMED CORRECT

§6c prose reads the elision "accounts for 8 of the 11 c2 entries and **7** of
the 13 c1 entries". **The c1 figure is 6, not 7.** Six `alignment_*/` files are
named only in truncated form in the branch table; the remaining seven c1 entries
are the `archive/` scripts of E1. **6 + 7 = 13**, matching the pasted c1 list
exactly, which the prose's 7 + 7 = 14 would have overshot.

The reason the 8 elided table labels yield only 6 unmentioned files is measured
above: `blob_mhi_tracks_alignment_v5.py` and `time_coordinates_conversions_v3.py`
are also named with their full paths elsewhere in CLAUDE.md — at post-edit L71
(stage 4) and L73 (stage 6), because they are the canonical branch's scripts —
so those two never enter c1. 8 − 2 = 6.

### E3 — CORRECTED HERE

§7 of the frozen report states that the artifact `cmp` output "are in the chat
reply for this task" rather than in the report. That output is pasted in §4
below so the figure lives with the task.

### E4 — a further defect, not in this prompt's list

§6e of the frozen report says "Full per-file table is in the scratchpad
`inventory_output.txt`". That file is in the session scratchpad, outside the
repository and not committed, so the pointer will dangle once the session ends.
The working rule is to quote figures rather than point at where they live. The
frozen report does quote the totals (`CRLF=8, LF=41`) and the eight CRLF files
in full, so no figure is actually missing from the record — only the 41 LF rows
are unquoted. Recorded as a weakness in the frozen report; **no fix applied**,
since the report is frozen and this prompt's scope does not include re-running
the inventory.

Nothing else in the frozen report is believed wrong; see §7.

---

## 3. CLAUDE.md IS UNCHANGED

No change to CLAUDE.md was made by this step. Verified by rebuilding the
expected post-edit file from the frozen pre-edit snapshot plus the verbatim
block, then comparing bytes:

```
========================================================================
C1. IS CLAUDE.md BYTE-IDENTICAL TO WHAT THE IMPLEMENT STEP LEFT?
========================================================================
method: rebuild pre-edit snapshot + block with the same splice, then
        compare bytes against the live file.

measured: frozen pre-edit snapshot bytes = 26079
measured: frozen pre-edit snapshot lines = 117
measured: block lines                    = 23
measured: rebuilt expected bytes         = 27349
measured: live CLAUDE.md bytes           = 27349
measured: live CLAUDE.md lines           = 141
measured: live CRLF terminators          = 141
measured: live bare-LF terminators       = 0
VERDICT: IDENTICAL - CLAUDE.md is exactly what implement left
```

Confirmed externally with `cmp` and `sha256sum`:

```
=== cmp: live CLAUDE.md  vs  expected rebuild (pre-snapshot + block) ===
cmp: EXIT 0 - identical

=== sha256 of both ===
7b9ae10aba8220bc2d1185598f2c7d5239698dc659f06d5269e45baf1ab0eeab *CLAUDE.md
7b9ae10aba8220bc2d1185598f2c7d5239698dc659f06d5269e45baf1ab0eeab */c/.../claude_md_EXPECTED_post.md
```

The diff against HEAD is still exactly one hunk, 24 added, 0 deleted:

```
=== diff vs HEAD for CLAUDE.md ===
24	0	CLAUDE.md
hunk count: 1
@@ -2,6 +2,30 @@
```

---

## 4. DIFF ARTIFACT

Regenerated with the prescribed command and verified by `cmp` against a
regeneration written outside the repository.

```
=== generate artifact ===
exit=0

=== regenerate the same diff OUTSIDE the repo ===
exit=0

=== cmp artifact vs external regeneration ===
cmp: EXIT 0 - identical
```

The artifact and the regeneration written outside the repository are identical.

Whether the **staged** artifact matches the file on disk, after the final
re-stage described in §7.1:

```
=== cmp: staged blob  vs  file on disk ===
cmp: EXIT 0 - identical
```

Note on the `git` warnings suppressed above: each of these commands also emits
`warning: in the working copy of '<report>', LF will be replaced by CRLF the
next time Git touches it`. The reports are written LF while the repository has
no `.gitattributes` and `core.autocrlf=true` — the condition deferred by R4.

---

## 5. STAGING

Staged by explicit path only — no globs, no `.`, no `-A` — exactly the four
paths this prompt names.

```
=== git status ===
On branch main
Your branch is up to date with 'origin/main'.

Changes to be committed:
  (use "git restore --staged <file>..." to unstage)
	modified:   CLAUDE.md
	new file:   prompt_outputs/001-bootstrap-gate.md
	new file:   prompt_outputs/001-bootstrap-implement.md
	new file:   prompt_outputs/001-bootstrap.diff.txt


=== git diff --cached --numstat ===
24	0	CLAUDE.md
389	0	prompt_outputs/001-bootstrap-gate.md
821	0	prompt_outputs/001-bootstrap-implement.md
1257	0	prompt_outputs/001-bootstrap.diff.txt
```

`git status` shows no other modified or untracked file, so nothing outside the
four named paths was staged and nothing else needed reporting. All four entries
are additions; `CLAUDE.md` is the only modification and it is the same 24/0 as
§3.

Per §7.1 the two self-referential entries were re-staged after this measurement;
their final line counts are in the chat reply.

---

## 6. PROPOSED COMMIT MESSAGE

Per R5 the message below **excludes** the two trailers; COMMIT adds exactly
`Co-Authored-By` and `Claude-Session`.

```
Add working-rules section and task 001 reports

Insert the rules that govern every task at the top of CLAUDE.md, above
the architecture reference, as a pure addition: one hunk, nothing that
was already there is touched.

Start prompt_outputs/ as the task record, holding the implement and
gate reports for task 001 and the diff artifact they are verified
against. Reports and artifacts are both tracked.

Deferred to their own tasks: the CLAUDE.md content defects the
inventory turned up, and .gitattributes line-ending normalisation.
```

Measured by `measure_msg.py`, a script file outside the repository, printing
each line beside its length and verdict:

```
subject  len= 46  max=50  OK  |Add working-rules section and task 001 reports|
line 2   blank separator: OK
body L3   len= 70  max=72  OK  |Insert the rules that govern every task at the top of CLAUDE.md, above|
body L4   len= 70  max=72  OK  |the architecture reference, as a pure addition: one hunk, nothing that|
body L5   len= 29  max=72  OK  |was already there is touched.|
body L6   len=  0  max=72  OK  ||
body L7   len= 67  max=72  OK  |Start prompt_outputs/ as the task record, holding the implement and|
body L8   len= 65  max=72  OK  |gate reports for task 001 and the diff artifact they are verified|
body L9   len= 48  max=72  OK  |against. Reports and artifacts are both tracked.|
body L10  len=  0  max=72  OK  ||
body L11  len= 62  max=72  OK  |Deferred to their own tasks: the CLAUDE.md content defects the|
body L12  len= 66  max=72  OK  |inventory turned up, and .gitattributes line-ending normalisation.|

longest body line: 70
RESULT: PASS
EXIT=0
```

The subject deliberately avoids restating the hunk figures, which live in §3.

---

## 7. POINTS FOR RULING

### 7.1 The diff artifact's chicken-and-egg, and how it was handled

**Yes, staging the artifact creates one, and it does not fully close.** Three
facts set the shape of the problem:

1. The artifact is generated from `git diff HEAD`, which compares the **working
   tree** to HEAD. Staging does not change that output, so staging CLAUDE.md and
   the two reports leaves the artifact still accurate — the artifact does not
   need regenerating merely because something was staged.
2. The artifact excludes itself by pathspec, so its own bytes never appear in
   it. That part is self-consistent by construction.
3. But this report is *in* the artifact, and this report quotes the artifact's
   `cmp` result and the post-staging `git status` / numstat. Every time those
   are appended, the report grows, and the artifact that contains the report
   goes stale. Pasting a figure that describes the file you are pasting it into
   has no fixed point.

**Handling, in order:** the report was written complete except for §4 and §5;
`git add -N` was applied to the untracked files by explicit path; the artifact
was generated and `cmp`-verified; the four paths were staged; `git status` and
`git diff --cached --numstat` were captured and written into §4 and §5; then the
artifact was regenerated so it reflects this finished report, and
`001-bootstrap-gate.md` and `001-bootstrap.diff.txt` were re-staged by explicit
path so the index matches disk.

**Consequence, stated plainly:** the numstat block in §5 is the measurement
taken when the four paths were first staged. The final re-stage changed the line
counts of exactly two entries — `001-bootstrap-gate.md` (this file, which grew
by §4 and §5) and `001-bootstrap.diff.txt` (which grew by the same amount). The
converged final numstat is in the chat reply for this task. `CLAUDE.md` and
`001-bootstrap-implement.md` are unaffected and their figures are final in §5.

Whether the staged artifact matches the file on disk is answered by `cmp` in §4.

### 7.2 Anything else in the frozen report now believed wrong

Beyond E1–E3, one item: **E4** in §2 above, the dangling scratchpad pointer in
§6e. It is a process weakness rather than a wrong figure.

Two things checked and found **not** wrong, for the record:

- §0.1's account of the reverted task-000 state and the no-longer-ahead commit
  still matches `git status` and `git rev-list --count origin/main..main`.
- §6c's c2 reading — that the `..._` entries are table elisions and that
  `colours_MHIs.py`, `colours_MHIs_validate_output.py` and `merge_v1.py` are
  former names rather than missing files — is confirmed by the measurement in
  §2, which additionally supplies the L71/L73 evidence the frozen report did not
  have.

### 7.3 Two trailer values I will not invent

R5 fixes *which* trailers are added but not their values, and neither is
derivable from the repository:

- **`Co-Authored-By` model name.** The last three commits say
  `Claude Opus 4.8 (1M context)`. This session is a different model, so copying
  that line verbatim would misattribute. Claude Code's current attribution line
  is `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.
- **`Claude-Session` URL.** Every prior commit carries
  `https://claude.ai/code/session_01QFdYr8j8nGbkwR2qXpyvep`. That is the *old*
  session's URL; this session's is not something I can read from the repo.

Ruling needed on both before COMMIT. I will not fabricate a session URL, and I
will not reuse the previous one as if it were this session's.

---

## 8. UNREQUESTED — ACCEPT OR DROP

Not implemented; listed for ruling.

1. **Task 002 scope** — fix D1, D2, D3, D5, D6 in CLAUDE.md per R3.
2. **`.gitattributes` task** — per R4, as its own whitespace-only change.
3. **Re-run the inventory into a committed file** so §6e's full 49-row
   line-ending table stops living only in the scratchpad (E4).
4. **Task 000's move** — returns as its own task per R6; the commit message for
   it was already measured and approved-in-principle in that task's report,
   which was never written to `prompt_outputs/` because the folder did not exist
   yet. It exists only in that task's chat reply.
