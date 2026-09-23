# BACKLOG

Deferred work, each item with what is wrong and where it came from. Not
append-only: the task that completes an item removes it. Items are cited by
name. Project decisions live in [DECISIONS.md](DECISIONS.md), and recurring
mistakes in [GOTCHAS.md](GOTCHAS.md).

## README: stale branch sequence

`README.md` describes each alignment branch as a self-contained sequence ending
in kinematics ("align → overlay (visualisation) → convert → overlay-collect →
kinematics"). Stage 7 is now the shared `kinematics/` stage and belongs to
neither branch.

*Deferred from task 003:* a README fix, outside that task's scope.

## CLAUDE.md: version-rule exceptions undercounted

The "Versioned scripts" section says two sections are exceptions to "the
highest version number is the current one", naming `segmentation_checks/` and
`segmentation_corrections/`. The two-branch section is a third: `alignment_1/`
keeps lower versions than `alignment_2/` as live scripts, deliberately.

*Deferred from task 003:* a CLAUDE.md fix, outside that task's scope.
