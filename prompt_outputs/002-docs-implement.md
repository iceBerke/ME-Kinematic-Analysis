# 002 — docs — implement

Task: fix five CLAUDE.md content defects, create `DECISIONS.md` and
`GOTCHAS.md`, add a pointer bullet to the working rules.

**Stopped at the review gate: nothing staged, nothing committed, nothing
pushed.** The only index operation is `git add -N` (intent-to-add), which this
prompt requires so the diff artifact can see new files; it records no content.

**No test script was run.** There is no automated test suite, and this task
touches no `kinematics/` path — §6 confirms the changed set is `CLAUDE.md`,
`DECISIONS.md` and `GOTCHAS.md`. No pipeline script ran and no dataset was
touched. No `.py`, `.gitignore` or `.gitattributes` file was created or
modified; line endings were not changed anywhere.

Scripts used, both outside the repository:

```
edit_claude_md.py   applies the six edits at byte level, CRLF preserved
verify_002.py       edits, changed file set, line endings, character scan
```

---

## 1. EVERY CLAIMED LINE NUMBER WAS CORRECT

The prompt gave post-edit line numbers from `001-bootstrap-implement.md` §5.
All six were verified in the live file **before** anything was written; the
edit script refuses to run otherwise.

```
========================================================================
VERIFYING EVERY CLAIMED LINE BEFORE TOUCHING ANYTHING
========================================================================
measured: D1 at L33 contains expected text = True
VERDICT: D1 is where the prompt claims (L33)
measured: D2 at L48 contains expected text = True
VERDICT: D2 is where the prompt claims (L48)
measured: D6 at L50 contains expected text = True
VERDICT: D6 is where the prompt claims (L50)
measured: D3 at L117 contains expected text = True
VERDICT: D3 is where the prompt claims (L117)
measured: D5 at L129 contains expected text = True
VERDICT: D5 is where the prompt claims (L129)
measured: POINTER anchor L27 matches exactly = True
VERDICT: POINTER anchor is the last working-rules bullet
measured: L28 is blank = True
VERDICT: the working-rules section ends at the anchor
```

No difference to report on placement. **Each of the five is a genuine defect**,
and D3 is a genuine defect with a complication — see §3.

---

## 2. THE SIX EDITS, BEFORE AND AFTER

Line numbers after the POINTER insertion shift by +1 from L28 onward.

### POINTER — new bullet, post-edit L28

```
BEFORE: (line did not exist)
AFTER  L28: - Project decisions are recorded in DECISIONS.md, and recurring mistakes in GOTCHAS.md.
```

Added as the last bullet of `## Working rules (how every task is run)`. This
makes the block differ from its source in the task-001 prompt by exactly one
line, which the prompt states is intended.

### D1 — L33 → L34

```
BEFORE L33: There is no package, no build, no test suite, and no CLI. Each `.py` file is a self-contained batch script run directly with `python <script>.py`. **All configuration lives in hard-coded constants inside the `if __name__ == "__main__":` block (or module-level constants near the top) — there are no command-line arguments.** To run anything you edit the `root_directory` (and related paths/parameters) at the bottom of the file, then execute it.

AFTER  L34: There is no package, no build, no **automated** test suite, and no CLI — the only tests are two hand-run scripts in `kinematics/`: `test_stage7_structure.py`, which needs a real dataset root, and `demo_test_stage7.py`, which is synthetic and needs no data. Each `.py` file is a self-contained batch script run directly with `python <script>.py`. **All configuration lives in hard-coded constants inside the `if __name__ == "__main__":` block (or module-level constants near the top) — there are no command-line arguments.** To run anything you edit the `root_directory` (and related paths/parameters) at the bottom of the file, then execute it.
```

"no package, no build, no CLI" is intact; only "test suite" gained
"**automated**", and the two scripts are now named where the claim is made
rather than only at L111.

### D2 — L48 → L49

```
BEFORE L48: Many scripts exist as `_v1`/`_v2`/`_v3`/`_v4`/`_v5` (and `_part1`/`_complete`) variants. **The highest version number is the current one**; lower versions are kept for history. When editing behavior, edit the latest version unless explicitly told otherwise.

AFTER  L49: Many scripts exist as `_v1`/`_v2`/`_v3`/`_v4`/`_v5` (and `_part1`/`_complete`) variants. **The highest version number is the current one unless this file says otherwise**; lower versions are kept for history. When editing behavior, edit the latest version unless explicitly told otherwise. Two sections do say otherwise, both deliberately: `segmentation_checks/` keeps `error_analysis_v1.py` alongside `_v3.py` because the two flag different defects, and the `segmentation_corrections/` scripts `correction_v1`–`_v4` are not a version progression at all — each solves a different segmentation defect.
```

Both exceptions named, matching what L124/L125 and L129 already say.

### D6 — L50 → L51, one sentence appended

```
BEFORE L50: ...the archived `_part1` is the obsolete first generation that emits only 4 columns (`x,y,t,size`) with no brightness/solidity and is incompatible with the rest of the pipeline.

AFTER  L51: ...is incompatible with the rest of the pipeline. Archived variants are referred to throughout this file by their version suffix (`_v1`, `_v2`, `_ME_complete`, `_part1`, …) rather than by full filename; the files themselves are listed in `archive/`.
```

Per the ruling the seven names are **not** listed. They were verified against
`git ls-files` anyway, since the prompt said to check the list before relying
on it — see §4.

### D3 — L117 → L118

```
BEFORE L117: - **Encoding fixes.** The old scripts write `μ` to the summary with the platform default encoding, which **crashes on Windows** (cp1252); and their `SPEED FILTER` progress line also contains `μ`, so on a Windows console that `print` raised `UnicodeEncodeError` inside the `try`, and the bare `except` logged every speed-filtered track as a failed track. The new code opens report/CSV files with `encoding='utf-8'` and keeps console output ASCII.

AFTER  L118: - **Encoding fixes.** The old scripts write a mu character to the summary with the platform default encoding, which **crashes on Windows** (cp1252): they use U+03BC GREEK SMALL LETTER MU, which cp1252 cannot encode, rather than U+00B5 MICRO SIGN, which it can. Their `SPEED FILTER` progress line carries the same character, so on a Windows console that `print` raised `UnicodeEncodeError` inside the `try`, and the bare `except` logged every speed-filtered track as a failed track. The new code opens report/CSV files with `encoding='utf-8'` and keeps console output ASCII. *(Proposed, task 002: the two literal mu characters here were replaced by codepoint names rather than normalised to U+00B5, which would have made this paragraph false.)*
```

**This is the one place the instruction could not be followed literally.**
Full reasoning in §3.

### D5 — L129 → L130

```
BEFORE L129: ...They are **not a version progression** — each solves a *different* segmentation defect, so all three are kept:

AFTER  L130: ...They are **not a version progression** — each solves a *different* segmentation defect, so all four are kept:
```

### Nothing else moved

```
measured: pre-edit lines  = 141
measured: post-edit lines = 142
measured: untouched pre-edit lines = 136
measured: untouched post-edit lines = 136
VERDICT: every line other than the six targets is byte-identical
```

---

## 3. D3 — FOR YOUR RULING

The prompt says to normalise all three micro/mu characters to U+00B5 and to
report if doing so at L117 would alter its meaning. **It would, and the
paragraph would become false.**

Two measured facts settle it.

**Fact 1 — cp1252 encodes U+00B5 and cannot encode U+03BC:**

```
measured: U+00B5 MICRO SIGN              cp1252 -> b'\xb5'   ENCODES FINE
measured: U+03BC GREEK SMALL LETTER MU   cp1252 -> UnicodeEncodeError: character maps to <undefined>
```

**Fact 2 — the old scripts really do use U+03BC, in exactly the places L117
describes:**

```
--- archive/final_kin_param_extraction_v3.py ---
  U+00B5 MICRO SIGN (c2 b5) count: 2
  U+03BC GREEK MU   (ce bc) count: 4
--- archive/final_kin_param_extraction_v4.py ---
  U+00B5 MICRO SIGN (c2 b5) count: 2
  U+03BC GREEK MU   (ce bc) count: 4

=== the actual lines containing a mu in v4 ===
126:# Maximum speed to consider (in µm/s)
127:MAX_SPEED = 60  # µm/s
236:        f.write("Averages calculated for: Mean Velocity (μm/s), ...
252:                    f.write(f"  Mean Velocity: ... μm/s\n")
266:                f.write(f"  Mean Velocity: ... μm/s\n")
381:                            print(f"    SPEED FILTER: ... (>{MAX_SPEED} μm/s)")
```

The U+00B5 occurrences are in comments (126–127); the U+03BC occurrences are
the summary writes (236, 252, 266) and the `SPEED FILTER` progress line (381)
— precisely the two things L117 blames for the crash.

So L117's `μ` was **a faithful quotation, not an inconsistency**. Replacing it
with `µ` would have produced a paragraph asserting that a character cp1252
encodes without complaint crashes on cp1252.

**What I did instead.** I removed both literal U+03BC characters — satisfying
"no U+03BC remains in CLAUDE.md" — by naming the codepoints in prose rather
than printing them, and said explicitly which one cp1252 cannot encode. The
paragraph is now both mu-literal-free and true, and is more precise than
before. It is **marked in the file as proposed**, in the trailing italic
parenthetical quoted in §2.

The two U+00B5 in the archived scripts' comments were **not** touched — this
task must not modify any `.py` file.

**Your options:** accept the reworded paragraph and drop the "(Proposed…)"
marker in a follow-up; or revert L117 to the original literal `μ` and record
instead that the mixed codepoints there are deliberate.

Note also that L107 (now **L108**) was already U+00B5 MICRO SIGN, so D3
required no change there:

```
measured: U+00B5 MICRO SIGN occurrences = 1 [108]
```

All of D3's actual work was at L117.

---

## 4. THE TWO LISTS THE PROMPT SAID TO VERIFY

### D5 — the number of `correction_v*.py` files

```
=== D5: correction_v*.py files, by command ===
  segmentation_corrections/correction_v1.py
  segmentation_corrections/correction_v2.py
  segmentation_corrections/correction_v3.py
  segmentation_corrections/correction_v4.py
count: 4
```

**Four.** "all three" was wrong; "all four" is correct.

### D6 — the seven archive/ names

```
=== D6: tracked archive/ files ===
  archive/blob_detection_ME_complete.py
  archive/blob_detection_ME_part1.py
  archive/blob_detection_v2.py
  archive/blob_parameters_check_v1.py
  archive/blob_parameters_check_v2.py
  archive/error_analysis_v2.py
  archive/final_kin_param_extraction_v2.py
  archive/final_kin_param_extraction_v3.py
  archive/final_kin_param_extraction_v4.py
  archive/mhi_overlay_v1.py
  archive/track_segmentation_ancient_v1.py
  archive/track_segmentation_ancient_v2.py
  archive/track_segmentation_v2.py
  archive/track_segmentation_v3.py
count: 14
```

All seven names the prompt lists exist and are tracked. They are the first
seven rows above. Per the ruling they are **not** listed in CLAUDE.md.

---

## 5. NEW FILES

`DECISIONS.md` and `GOTCHAS.md` were created in the repository root, LF
endings, matching the existing reports.

`DECISIONS.md` records exactly the four rulings the prompt lists — tests,
`prompt_outputs/`, commit trailers, line endings — each with its reason. **No
ruling was invented.** The trailer entry states in the file itself that it
supersedes R5.

`GOTCHAS.md` records exactly the two entries the prompt lists, each with what
went wrong and what to do instead: the `git log --format=%B` output terminator,
and `git commit --amend` rewriting the committer date.

---

## 6. VERIFICATION

### Only the three intended files changed

```
     M CLAUDE.md
    ?? DECISIONS.md
    ?? GOTCHAS.md
    ?? prompt_outputs/001-bootstrap-commit-2.md
    ?? prompt_outputs/001-bootstrap-commit-3.md
    ?? prompt_outputs/001-bootstrap-commit.md
    ?? prompt_outputs/001-bootstrap-push.md

measured: modified tracked files = ['CLAUDE.md']
VERDICT: CLAUDE.md is the only modified tracked file
measured: the two new files present as untracked = ['DECISIONS.md', 'GOTCHAS.md']
VERDICT: DECISIONS.md and GOTCHAS.md are both new files
measured: touched .py / .gitignore / .gitattributes = []
VERDICT: no .py file, no .gitignore, no .gitattributes touched
measured: changed .md outside prompt_outputs/ = ['CLAUDE.md', 'DECISIONS.md', 'GOTCHAS.md']
VERDICT: exactly CLAUDE.md plus the two new files
```

The four `prompt_outputs/001-*` files are task 001's untracked reports, riding
with this task's commit as instructed. They were not edited.

### Line endings unchanged

```
measured: BEFORE  bytes= 27349  CRLF=141  bare-LF=0
measured: AFTER   bytes= 28483  CRLF=142  bare-LF=0
VERDICT: bare-LF count is 0 before and after - no line ending changed
VERDICT: CRLF count 141 -> 142, +1 for the one inserted line
```

CLAUDE.md was and remains uniformly CRLF; the single CRLF increase is the
POINTER bullet. The two new files are uniformly LF (`CRLF=0  bare-LF=66` and
`CRLF=0  bare-LF=39`).

### Character scan

All three files: **valid UTF-8, no BOM, no control characters beyond tab, CR
and LF.**

```
--- CLAUDE.md ---
measured: decodes as UTF-8 = True (28483 bytes)
measured: starts with UTF-8 BOM = False
measured: control characters beyond tab/CR/LF = 0 []
measured: distinct non-ASCII characters = 12
    U+00B2  SUPERSCRIPT TWO                    x6   lines [70, 71, 97, 99, 99, 99]
    U+00B5  MICRO SIGN                         x1   lines [108]
    U+00D7  MULTIPLICATION SIGN                x5   lines [74, 74, 74, 140, 140]
    U+2013  EN DASH                            x3   lines [49, 72, 72]
    U+2014  EM DASH                            x71  lines [13, 32, 34, 34, 49, 51, 67, 67] ...(+63 more)
    U+2026  HORIZONTAL ELLIPSIS                x7   lines [51, 70, 73, 77, 123, 132, 141]
    U+2192  RIGHTWARDS ARROW                   x27  lines [69, 69, 69, 69, 70, 73, 74, 74] ...(+19 more)
    U+2265  GREATER-THAN OR EQUAL TO           x2   lines [125, 132]
    U+2500  BOX DRAWINGS LIGHT HORIZONTAL      x4   lines [59, 59, 60, 60]
    U+2514  BOX DRAWINGS LIGHT UP AND RIGHT    x2   lines [59, 60]
    U+26A0  WARNING SIGN                       x1   lines [77]
    U+FE0F  VARIATION SELECTOR-16              x1   lines [77]
measured: U+03BC GREEK SMALL LETTER MU occurrences = 0 []
VERDICT: no U+03BC remains in CLAUDE.md

--- DECISIONS.md ---
measured: distinct non-ASCII characters = 2
    U+2014  EM DASH                            x8   lines [11, 13, 21, 22, 27, 46, 54, 55]
    U+2026  HORIZONTAL ELLIPSIS                x1   lines [51]

--- GOTCHAS.md ---
measured: distinct non-ASCII characters = 1
    U+2014  EM DASH                            x3   lines [21, 22, 38]
```

**No U+03BC remains in CLAUDE.md.** One U+00B5 MICRO SIGN remains, at L108,
which is the `µm/s` unit and is the character D3 normalises *to*.

One incidental observation, not acted on: L77 carries U+26A0 WARNING SIGN
followed by U+FE0F VARIATION SELECTOR-16 — the emoji presentation of the
warning triangle. It is not a defect and is outside this task's scope.

---

## 7. ERRATA — R5 IS SUPERSEDED

`prompt_outputs/001-bootstrap-gate.md` is committed and frozen, and was **not
edited**. Recording here, as the working rules require:

Its **ruling R5** — "every commit for this project keeps Claude Code's
`Co-Authored-By` trailer and the `Claude-Session` trailer … COMMIT adds exactly
those two; PUSH verifies them" — **is superseded** by the trailer ruling now in
`DECISIONS.md`.

**Why.** R5 required a `Claude-Session` value that cannot be obtained from
inside a session: a session exposes only a UUID, the trailer URLs use a
`session_01…` identifier, and nothing maps one to the other. That made R5
unsatisfiable, and it blocked a commit outright — the whole of
`prompt_outputs/001-bootstrap-commit.md` is the record of that stop. The
replacement keeps `Co-Authored-By` alone, drops `Claude-Session`, and says
PUSH does not check which model the trailer names.

The gate report's §7.3, which flagged both values as undeterminable, was
correct; only its §1 R5 statement is superseded.

---

## 8. README.md — REPEATS NONE OF THE FIVE (not edited)

Checked by command, not edited:

```
--- D1: 'no test suite' / test-suite claims ---
76:| `kinematics/test_stage7_structure.py` | `ROOT_DIRECTORY` | dataset root (structural regression test) |
77:| `kinematics/demo_test_stage7.py` | — | none (self-contained demo, no paths to edit) |
176:**Regression test.** `kinematics/test_stage7_structure.py` runs stage 7 against a real
185:To sanity-check the test itself without any data, run `python demo_test_stage7.py` — it

--- D2: highest-version rule ---
  (no match)

--- D3: mu characters ---
  U+00B5 count: 1
  U+03BC count: 0

--- D5: 'all three' / correction counts ---
79:| `segmentation_corrections/correction_v1.py`, `_v2.py`, `_v3.py` | `image_path` | a single track PNG (`t<N>.png`) |
80:| `segmentation_corrections/correction_v4.py` | `output_file` (plus the hand-listed input PNGs in the script) | the merged-output PNG path |

--- D6: archive mentions ---
54:the table lists every path a user edits. (Archived scripts in `archive/` are superseded and
174:`_v4.py`) have been validated against the new stage and moved to `archive/`.
```

| Defect | In README? | Evidence |
|---|---|---|
| D1 | **No** | README never claims there is no test suite; it documents both scripts correctly, including that the demo needs no data. |
| D2 | **No** | No highest-version rule anywhere. |
| D3 | **No** | One U+00B5, zero U+03BC — already consistent, and consistent with CLAUDE.md's surviving U+00B5. |
| D5 | **No** | README lists `correction_v1/_v2/_v3` and `_v4` in separate rows and never counts them. |
| D6 | **No** | Mentions `archive/` as a folder; names no archived script by a wrong name. |

README repeats none of the five defects, so no follow-up is needed there.
**README.md was not modified.**

---

## 9. DIFF ARTIFACT

Regenerated with the prescribed command and verified by `cmp` against a
regeneration written outside the repository.

```
=== generate artifact ===
exit=0

=== regenerate the same diff OUTSIDE the repo ===
exit=0

=== cmp artifact vs external regeneration ===
cmp: EXIT 0 - identical

=== artifact numstat ===
6	5	CLAUDE.md
66	0	DECISIONS.md
39	0	GOTCHAS.md
367	0	prompt_outputs/001-bootstrap-commit-2.md
367	0	prompt_outputs/001-bootstrap-commit-3.md
327	0	prompt_outputs/001-bootstrap-commit.md
297	0	prompt_outputs/001-bootstrap-push.md
444	0	prompt_outputs/002-docs-implement.md
```

The artifact and the regeneration written outside the repository are identical.

**The usual self-reference caveat.** This report is inside the artifact while
quoting the artifact's own numstat, so the two cannot both be final at the same
instant. The block above was measured when the artifact was first generated;
the artifact was then regenerated so it reflects this finished report, and
`cmp` against a fresh outside regeneration was rerun and again returned exit 0.
Only two rows move between those two measurements — this report and the
artifact itself. The converged numstat is in the chat reply. `CLAUDE.md`,
`DECISIONS.md`, `GOTCHAS.md` and the four carried task-001 reports are
unaffected and their figures above are final.

---

## 10. POINTS FOR RULING

1. **D3's rewording** — §3. The literal normalisation the prompt asked for would
   have made the paragraph false. I removed both U+03BC by naming the codepoints
   instead, and marked the paragraph as proposed in the file. Accept and drop
   the marker, or revert to the literal `μ` and record the mixed codepoints as
   deliberate.
2. **No neighbouring line needed rewording.** Each of D1, D2, D5, D6 and POINTER
   is self-contained; the surrounding passages stay coherent without further
   edits. D3 is the sole case where keeping the passage true required changing
   how the sentence is phrased, and it is the same line, not a neighbour.
3. **The "(Proposed, task 002: …)" marker is publication-visible.** CLAUDE.md is
   going toward publication, so this marker should be removed once ruled on.

---

## 11. UNREQUESTED — ACCEPT OR DROP

Not implemented; listed for ruling.

1. **Drop the "(Proposed…)" marker** from L118 once D3 is ruled on.
2. **L77's emoji variation selector** (U+26A0 U+FE0F) could be plain U+26A0, or
   the warning could be worded instead of drawn.
3. **`.gitattributes`** remains task 004 per the line-endings decision.
4. **Task 000's move**, still pending.
5. **Nothing enforces the `Co-Authored-By` trailer** — no `commit.template`, no
   hook, no `trailer.*` config. Now recorded in `DECISIONS.md`, but still
   unenforced.
