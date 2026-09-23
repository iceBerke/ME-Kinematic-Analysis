# GOTCHAS

Mistakes that have already cost a round of work here, and what to do instead.
Project decisions live in [DECISIONS.md](DECISIONS.md).

## `git log --format=%B` is not the stored commit message

**What went wrong.** A byte-for-byte comparison of a commit message against the
approved text reported a difference at the last line. The message was correct;
the comparison was not. `git log -1 --format=%B` terminates its *output* with a
newline that is not part of the stored message, so the extracted text came back
one byte longer than the approved file and the comparison failed.

**What to do instead.** Read the commit object and take everything after the
first blank line:

```bash
git cat-file commit <ref>
```

Anything that compares a commit message byte for byte — against an approved
text, or before and after an amend — must use this, not `--format=%B`.

## `git commit --amend` always rewrites the committer date

**What went wrong.** Amending a commit to append a trailer changed more than
the message: the committer timestamp moved too, which is why `git commit
--amend` then printed a `Date:` line. Nothing was done wrong, but a check
written to assert that "nothing but the message changed" would have failed on
it.

**What is and is not preserved.** Author name, author email and **author date**
are preserved. The **tree hash is unchanged**, as is the parent. Only the
**committer date** is rewritten, and it is rewritten on every amend, even when
only the message changes.

**What to do instead.** Verify an amend by comparing the tree hash, the parent,
and the message — not the committer date. A check that compares committer dates
will fail on any amended commit, and no flag avoids it.
