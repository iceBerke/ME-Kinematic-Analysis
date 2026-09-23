# DECISIONS

Project decisions that would otherwise be re-litigated, each with its reason.
Recurring mistakes live in [GOTCHAS.md](GOTCHAS.md).

## Tests

**There is no automated test suite.** Two test scripts exist, and both are run
by hand, from `kinematics/`:

- `test_stage7_structure.py` — needs a real dataset root, set in its
  top-of-file `ROOT_DIRECTORY`.
- `demo_test_stage7.py` — synthetic, needs no data at all.

**Rule.** A task that touches `kinematics/` runs `demo_test_stage7.py` before
push, and `test_stage7_structure.py` as well when a dataset root is available.
Everything else in this repository is manual-test-only.

*Why:* the pipeline is a set of standalone batch scripts over a large dataset
that does not live in the repository, so there is nothing for an automated
suite to run against. Stage 7 is the exception — it was split into importable
modules — which is why it alone has test scripts, and why they are still
hand-run rather than wired into anything.

## `prompt_outputs/`

**Tracked** — both the `.md` reports and the `.diff.txt` artifacts.

*Why:* they are the audit trail for a cleanup being done ahead of publication.
A record of what was changed, checked and ruled on only has value if it is
versioned alongside the changes it describes.

## Commit trailers

**Supersedes the ruling recorded as R5 in
`prompt_outputs/001-bootstrap-gate.md`,** which required two trailers.

Every commit carries **exactly one trailer**:

```
Co-Authored-By: <the model running the session> <noreply@anthropic.com>
```

The approved commit message never includes it. **COMMIT** appends it. **PUSH**
verifies that exactly one `Co-Authored-By` trailer is present, but does **not**
check which model it names — that value is whatever Claude Code supplied at
commit time and is not the author's to approve.

**The `Claude-Session` trailer is dropped.** Its value is not obtainable from
inside a session: a session exposes only a UUID, while the trailer URLs used a
`session_01…` identifier, and nothing maps one to the other. Requiring it
blocked a commit outright, as `prompt_outputs/001-bootstrap-commit.md` records.

*Note:* nothing in the repository enforces any of this — there is no
`commit.template`, no `prepare-commit-msg` hook and no `trailer.*` config — so
each COMMIT step names the trailer deliberately.

## Line endings

**Deferred to its own task.** Nothing in this cleanup normalises line endings.

The repository currently holds **8 CRLF and 41 LF** tracked text files, has no
`.gitattributes`, and runs with `core.autocrlf=true`.

*Why deferred:* normalising would produce a large whitespace-only diff, and
mixing that with content changes would make both unreviewable.

## Superseded stage-7 scripts

**`final_kin_param_extraction_v3.py` and `_v4.py` stay in `archive/`.** They
are not moved into `alignment_1/` or `alignment_2/`, nor into `archive/`
subfolders inside them.

*Why:* both were stage 7 and were superseded by the `kinematics/` stage, so
nothing in the alignment directories uses them. Those directories are live run
directories — the alignment, overlay, conversion and overlay-collect steps run
from them — and every script in them is in live use, so moving the old scripts
back would put dead code among live scripts. Both lived in `alignment_1/` and
`alignment_2/` until `52c7a42` archived them; moving them back for
self-containment was tried in task 000 and reverted before commit
(`prompt_outputs/001-bootstrap-gate.md`, R6).
