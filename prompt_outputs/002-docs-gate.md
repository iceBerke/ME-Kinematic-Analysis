# 002 — docs — gate

Task: drop the proposed marker, rewrap the pointer bullet, record the rulings
and errata, stage by explicit path, propose the commit message.

**Stopped before committing: nothing committed, nothing pushed.** The only
index operations are the `git add -N` this prompt requires and the ten explicit
`git add` paths it names.

**No test script was run.** There is no automated test suite, and this task
touches no `kinematics/` path — §3 confirms the only file changed is
`CLAUDE.md`. No pipeline script ran and no dataset was touched.

Carried reports, frozen and not edited: `002-docs-implement.md`, and task 001's
`001-bootstrap-commit.md`, `-commit-2.md`, `-commit-3.md`, `001-bootstrap-push.md`.

Scripts used, both outside the repository:

```
gate_edits.py        applies C1 and C2 at byte level, CRLF preserved
verify_gate_002.py   changed file set, line endings, character scan, sweeps
measure_msg.py       commit-message length measurement
```

---

## 1. RULINGS RECORDED

### R7 — D3 accepted as implemented

Replacing the two literal U+03BC characters with their codepoint names was
correct. Normalising them to U+00B5, as the implement prompt asked, would have
left the paragraph describing a crash that would not occur: the crash is caused
by cp1252 being unable to encode U+03BC, and cp1252 encodes U+00B5 without
error. The implement report's §3 holds the two measurements that establish
this.

### R8 — the rest of the CLAUDE.md edits accepted as written

D1, D2, D5, D6 and the pointer bullet stand as implemented. Only the marker
removal (C1) and the rewrap (C2) remained, and both are done in §2.

### R9 — U+26A0 U+FE0F is left alone deliberately

The warning sign followed by VARIATION SELECTOR-16 at what is now L78 is valid
UTF-8, renders correctly, and changing it would be churn. **Recorded so a later
task does not reopen it.** It was raised as an incidental observation in the
implement report's §6 and is now closed.

---

## 2. THE TWO CHANGES

### C1 — remove the proposed marker, L118 (unchanged number: this edit removes no line)

Claimed at post-edit L118, and it was there:

```
measured: L118 contains ' *(Proposed, task 002:' = True
measured: L118 ends with ')*' = True
VERDICT: C1 marker is at L118 as claimed
```

**BEFORE, L118:**

```
- **Encoding fixes.** The old scripts write a mu character to the summary with the platform default encoding, which **crashes on Windows** (cp1252): they use U+03BC GREEK SMALL LETTER MU, which cp1252 cannot encode, rather than U+00B5 MICRO SIGN, which it can. Their `SPEED FILTER` progress line carries the same character, so on a Windows console that `print` raised `UnicodeEncodeError` inside the `try`, and the bare `except` logged every speed-filtered track as a failed track. The new code opens report/CSV files with `encoding='utf-8'` and keeps console output ASCII. *(Proposed, task 002: the two literal mu characters here were replaced by codepoint names rather than normalised to U+00B5, which would have made this paragraph false.)*
```

**AFTER, now L119** (the C2 rewrap above it pushed it down by one):

```
- **Encoding fixes.** The old scripts write a mu character to the summary with the platform default encoding, which **crashes on Windows** (cp1252): they use U+03BC GREEK SMALL LETTER MU, which cp1252 cannot encode, rather than U+00B5 MICRO SIGN, which it can. Their `SPEED FILTER` progress line carries the same character, so on a Windows console that `print` raised `UnicodeEncodeError` inside the `try`, and the bare `except` logged every speed-filtered track as a failed track. The new code opens report/CSV files with `encoding='utf-8'` and keeps console output ASCII.
```

```
measured: characters removed = 170
measured: removed text = | *(Proposed, task 002: the two literal mu characters here were replaced by codepoint names rather than normalised to U+00B5, which would have made this paragraph false.)*|
measured: line length 743 -> 573
VERDICT: the sentence now ends at 'keeps console output ASCII.'
VERDICT: both codepoint names survive untouched
```

Exactly the parenthetical and the single space before it were removed, 170
characters. The sentence naming U+03BC and U+00B5 is untouched.

### C2 — rewrap the pointer bullet, L28

Claimed at post-edit L28, and it was there:

```
measured: L28 == expected pointer bullet = True
measured: L28 length = 87
VERDICT: C2 pointer bullet is at L28 as claimed
```

**BEFORE, L28 — one line, 87 columns:**

```
- Project decisions are recorded in DECISIONS.md, and recurring mistakes in GOTCHAS.md.
```

**AFTER, L28–L29:**

```
- Project decisions are recorded in DECISIONS.md, and recurring mistakes
  in GOTCHAS.md.
```

```
measured: words = 12
measured: resulting lines = 2
    line 1: len= 72  |- Project decisions are recorded in DECISIONS.md, and recurring mistakes|
    line 2: len= 16  |  in GOTCHAS.md.|
VERDICT: every wrapped line is within 72 columns
measured: rejoined == original = True
VERDICT: wording is preserved exactly; only breaks and indent changed
VERDICT: continuation lines use the two-space indent
```

**Line lengths: 72 and 16.** The wording is preserved exactly — the script
rejoins the wrapped lines and confirms they reproduce the original string byte
for byte, so only the break and the indent changed.

**A measured difference from the prompt's description.** The prompt says every
other bullet in the block "wraps at roughly 72 characters". One does not — it
is 73:

```
measured: existing lines wider than 72 = 1
    len=73  |- Anything tests cannot reach needs a manual run by the user before push.|
VERDICT: the block wraps at roughly 72 columns (widest existing line is 73)
```

This first ran as a hard assertion that nothing exceeded 72, and the script
refused to write anything until I relaxed it to match the measured reality.
"Roughly 72" is accurate; strictly-72 is not. I wrapped at 72, which is the
width the other ten wrapped bullets use, and which the greedy fill the block
already follows produces for this text.

---

## 3. VERIFICATION

### CLAUDE.md is the only file this step changed

```
     M CLAUDE.md
     A DECISIONS.md
     A GOTCHAS.md
     A prompt_outputs/001-bootstrap-commit-2.md
     A prompt_outputs/001-bootstrap-commit-3.md
     A prompt_outputs/001-bootstrap-commit.md
     A prompt_outputs/001-bootstrap-push.md
     A prompt_outputs/002-docs-implement.md
    ?? prompt_outputs/002-docs.diff.txt

measured: modified tracked files = ['CLAUDE.md']
VERDICT: CLAUDE.md is the only modified tracked file
measured: README.md appears in git status = False
VERDICT: README.md untouched
measured: .py / .gitignore / .gitattributes in git status = []
VERDICT: no .py file, no .gitignore, no .gitattributes touched
```

`git status` alone cannot show that `DECISIONS.md` and `GOTCHAS.md` are
untouched *by this step*, since both are new files and appear whole either way.
So they were reconstructed from the implement step's own diff artifact and
compared:

```
--- the two new files vs what the implement step produced ---
measured: DECISIONS.md  implement-step bytes=2722 sha=e712f4a118d9260b
measured: DECISIONS.md  current        bytes=2722 sha=e712f4a118d9260b
VERDICT: DECISIONS.md is unchanged by this step
measured: GOTCHAS.md  implement-step bytes=1723 sha=019c98473b9de35f
measured: GOTCHAS.md  current        bytes=1723 sha=019c98473b9de35f
VERDICT: GOTCHAS.md is unchanged by this step
```

### Line endings still uniformly CRLF

```
measured: BEFORE  bytes= 28483  CRLF=142  bare-LF=0
measured: AFTER   bytes= 28316  CRLF=143  bare-LF=0
VERDICT: bare-LF is 0 before and after - uniformly CRLF
VERDICT: CRLF 142 -> 143, +1 for the C2 rewrap only
```

Bytes fell by 167 — the 170 removed marker characters, less the 3 bytes the
rewrap adds (one CRLF plus the two-space indent, minus the space it replaced).

### The two touched lines, character by character

```
--- C2 pointer bullet ---
L28 len=72: - Project decisions are recorded in DECISIONS.md, and recurring mistakes
    measured: non-ASCII characters on L28 = 0 (pure ASCII)
L29 len=16:   in GOTCHAS.md.
    measured: non-ASCII characters on L29 = 0 (pure ASCII)

--- C1 encoding bullet ---
L119 len=573: - **Encoding fixes.** The old scripts write a mu character ... keeps console output ASCII.
    measured: non-ASCII characters on L119 = 0 (pure ASCII)
VERDICT: C1 line now ends at 'keeps console output ASCII.'
VERDICT: both codepoint names survive on the C1 line
```

**All three lines are pure ASCII — there is no non-ASCII character on any line
this step touched.** That is the whole point of C1's original rewording: the
paragraph now describes the two codepoints by name instead of printing either.

### Sweeps

```
measured: lines containing U+03BC in CLAUDE.md = 0 []
VERDICT: no U+03BC anywhere in CLAUDE.md
measured: lines containing U+00B5 in CLAUDE.md = 1 [109]
measured: 'CLAUDE.md'      occurrences of 'Proposed, task 002' = 0
VERDICT: 'Proposed, task 002' appears nowhere in CLAUDE.md
measured: 'DECISIONS.md'   occurrences of 'Proposed, task 002' = 0
VERDICT: 'Proposed, task 002' appears nowhere in DECISIONS.md
measured: 'GOTCHAS.md'     occurrences of 'Proposed, task 002' = 0
VERDICT: 'Proposed, task 002' appears nowhere in GOTCHAS.md
```

No U+03BC anywhere. The single U+00B5 is the `µm/s` unit, now at L109.

---

## 4. ERRATA AGAINST THE FROZEN IMPLEMENT REPORT

`002-docs-implement.md` is frozen and was **not edited**.

### E1 — CONFIRMED

Its §9 numstat block shows `002-docs-implement.md` at **444** added lines. The
correct figure is **475**. Verified both ways:

```
=== E1: what the frozen implement report SS9 says ===
  431:444	0	prompt_outputs/002-docs-implement.md

=== E1: the frozen report's actual line count ===
  lines: 475

=== E1: live numstat for that path ===
475	0	prompt_outputs/002-docs-implement.md
```

The report's own line count and git's numstat agree on 475, so **475 is
correct and 444 is stale**. The other rows are unaffected, exactly as this
prompt says.

This is not an error so much as the fixed point that cannot be reached: the
report was 444 lines when the figure was measured, and quoting the figure into
it made it 475. The frozen report predicted this in the same section:

```
436:**The usual self-reference caveat.** This report is inside the artifact while
437-quoting the artifact's own numstat, so the two cannot both be final at the same
438-instant. The block above was measured when the artifact was first generated;
```

Its caveat named the right two rows and the right reason; only the number it
had already printed could not be updated.

### Nothing else believed wrong

Re-reading the frozen report against the current files, no other figure or
claim in it is wrong. Its line numbers (L108 for U+00B5, L118 for the encoding
bullet) were correct when written and have since shifted by +1 because of C2;
that is this step's doing, not an error in that report.

---

## 5. STAGING

Staged by explicit path only — no globs, no `.`, no `-A` — exactly the ten
paths this prompt names.

```
=== git status ===
On branch main
Your branch is up to date with 'origin/main'.

Changes to be committed:
  (use "git restore --staged <file>..." to unstage)
	modified:   CLAUDE.md
	new file:   DECISIONS.md
	new file:   GOTCHAS.md
	new file:   prompt_outputs/001-bootstrap-commit-2.md
	new file:   prompt_outputs/001-bootstrap-commit-3.md
	new file:   prompt_outputs/001-bootstrap-commit.md
	new file:   prompt_outputs/001-bootstrap-push.md
	new file:   prompt_outputs/002-docs-gate.md
	new file:   prompt_outputs/002-docs-implement.md
	new file:   prompt_outputs/002-docs.diff.txt


=== git diff --cached --numstat ===
7	5	CLAUDE.md
66	0	DECISIONS.md
39	0	GOTCHAS.md
367	0	prompt_outputs/001-bootstrap-commit-2.md
367	0	prompt_outputs/001-bootstrap-commit-3.md
327	0	prompt_outputs/001-bootstrap-commit.md
297	0	prompt_outputs/001-bootstrap-push.md
393	0	prompt_outputs/002-docs-gate.md
475	0	prompt_outputs/002-docs-implement.md
2429	0	prompt_outputs/002-docs.diff.txt
```

`git status` shows **no other modified or untracked file**, so nothing outside
the ten named paths was staged and nothing else needed reporting. `CLAUDE.md`
is the only modification, at 7 added and 5 removed: the five replaced lines
from the implement step, plus C1's shortened line and C2's two lines in place
of one.

Per §6 the two self-referential rows were re-staged after this measurement;
their converged figures are in the chat reply.

---

## 6. DIFF ARTIFACT

Regenerated with the prescribed command and verified by `cmp` against a
regeneration written outside the repository.

```
=== cmp artifact vs external regeneration ===
cmp: EXIT 0 - identical

=== artifact numstat ===
7	5	CLAUDE.md
66	0	DECISIONS.md
39	0	GOTCHAS.md
367	0	prompt_outputs/001-bootstrap-commit-2.md
367	0	prompt_outputs/001-bootstrap-commit-3.md
327	0	prompt_outputs/001-bootstrap-commit.md
297	0	prompt_outputs/001-bootstrap-push.md
393	0	prompt_outputs/002-docs-gate.md
475	0	prompt_outputs/002-docs-implement.md
```

The artifact and the regeneration written outside the repository are identical.

**Same self-reference caveat as before, and it is what E1 records.** This
report sits inside the artifact while quoting the artifact's own numstat, so
neither can be final at the instant the other is measured. The blocks above
were taken when the ten paths were first staged; the artifact was then
regenerated so it reflects this finished report, `cmp` against a fresh outside
regeneration was rerun and again returned exit 0, and
`prompt_outputs/002-docs-gate.md` and `prompt_outputs/002-docs.diff.txt` were
re-staged by explicit path so index and disk agree. Only those two rows move
between the two measurements; the other eight are final above. The converged
figures are in the chat reply.

---

## 7. PROPOSED COMMIT MESSAGE

Per `DECISIONS.md` the message carries **no trailer**; the COMMIT step appends
exactly one `Co-Authored-By`.

```
Fix CLAUDE.md defects; add DECISIONS and GOTCHAS

Correct five defects the task 001 inventory found in CLAUDE.md: the
claim that no test suite exists, the highest-version rule that two
sections contradict, the two different micro/mu codepoints, a count
of three where four scripts are listed, and archived scripts that
are never named in full.

Record the rulings behind this cleanup in DECISIONS.md and the
mistakes that have already cost a round of work in GOTCHAS.md, and
add a working-rules bullet pointing at both.
```

Measured by `measure_msg.py`, a script file outside the repository:

```
subject  len= 48  max=50  OK  |Fix CLAUDE.md defects; add DECISIONS and GOTCHAS|
line 2   blank separator: OK
body L3   len= 67  max=72  OK  |Correct five defects the task 001 inventory found in CLAUDE.md: the|
body L4   len= 66  max=72  OK  |claim that no test suite exists, the highest-version rule that two|
body L5   len= 67  max=72  OK  |sections contradict, the two different micro/mu codepoints, a count|
body L6   len= 65  max=72  OK  |of three where four scripts are listed, and archived scripts that|
body L7   len= 24  max=72  OK  |are never named in full.|
body L8   len=  0  max=72  OK  ||
body L9   len= 62  max=72  OK  |Record the rulings behind this cleanup in DECISIONS.md and the|
body L10  len= 66  max=72  OK  |mistakes that have already cost a round of work in GOTCHAS.md, and|
body L11  len= 44  max=72  OK  |add a working-rules bullet pointing at both.|

longest body line: 67
RESULT: PASS
EXIT=0
```

Confirmed trailer-free:

```
=== no trailer present in the proposed message? ===
0 - no trailer, as DECISIONS.md requires
```

The body covers all three required subjects: the five defect fixes, the two new
files, and the pointer bullet.

---

## 8. POINTS FOR RULING

### 8.1 The rewrap changes the block-vs-source comparison — by one more line

**Yes, and the number moves from one to two.** Measured against the verbatim
source block:

```
=== source block (task 001 prompt, verbatim) ===
  source lines: 23

=== the block as it now stands in CLAUDE.md (L5..L29) ===
  current lines: 25

=== diff: source block vs current block ===
23a24,25
> - Project decisions are recorded in DECISIONS.md, and recurring mistakes
>   in GOTCHAS.md.
```

The implement report said the block differs from its source "by exactly one
line, which the prompt states is intended". After C2 it differs by **two
lines**, because the pointer bullet now occupies two. Nothing else changed: the
diff is a pure append at the end, so all 23 original lines remain byte-identical
and in order.

So the honest statement is: **one added bullet, two added lines.** If a future
task verifies the block against its source by line count, it should expect 25,
not 24.

### 8.2 Anything else wrong in the frozen implement report

Nothing beyond E1 — see §4.

---

## 9. UNREQUESTED — ACCEPT OR DROP

Not implemented; listed for ruling.

1. **The 73-column bullet** at L27, `- Anything tests cannot reach needs a
   manual run by the user before push.`, is one character over the width every
   other line respects. Rewrapping it would be a one-line whitespace change;
   leaving it keeps the block byte-identical to its approved source.
2. **`.gitattributes`** remains its own task per the line-endings decision.
3. **Task 000's move**, still pending.
4. **Nothing enforces the `Co-Authored-By` trailer** — no `commit.template`, no
   hook, no `trailer.*` config. Recorded in `DECISIONS.md`, still unenforced.
