# ADR 0026: Write an ADR Once, and Archive It When It Stops Being Active

**Status:** Accepted
**Date:** 2026-08-23
**Revision:** 1

## Background

[ADR 0024](0024-variance-vocabulary-is-direction-only.md) established that an
Accepted ADR is amended in place rather than superseded when its decision stands
and its record has gone stale. [ADR 0025](0025-an-amendment-is-a-recorded-revision.md)
made those amendments visible as numbered revisions. Read together they answer
"how do I amend an ADR" thoroughly and leave "should I" unasked, which is the
wrong emphasis and the reason this ADR exists.

An ADR is a record of a decision taken at a moment, by people who knew what they
knew then. Its value is that it is a fixed point: a reader can trust that what
they are reading is what was decided, and a decision that reads differently
depending on when you open it is not a record of anything. The original pattern
treats an accepted ADR as immutable, and every mechanism this repository has
added since — revisions, history tables, ratifiers — makes departing from that
cheaper. Cheap departure from a good default produces drift, and drift in the
decision record is the failure this repository was founded on.

Seven ADRs are currently amended. That count is not evidence that amendment is
normal; it is an artefact of this repository amending its own process three times
in a week — 0024, 0025 and this one — while a corpus written over eight days
caught up with a register that moved nineteen contracts. Four of the seven
amendments are `## Applied — pass N` sections recording implementation of a
decision that never changed, which is arguably not amendment at all.

The second problem is smaller and purely one of navigation. `docs/adr/` holds 26
files, of which 25 are live decisions and one — [ADR 0015](archive/0015-interim-branch-discipline.md)
— was superseded the day it was written and never ratified. A reader opening the
directory cannot tell which is which without opening files or greping statuses,
and the ratio only gets worse: a corpus that accumulates for two years is mostly
history, presented as though it were current.

## Alternatives Considered

### Option 1: The status field is already the answer; change nothing

`**Status:** Superseded` is in every non-active ADR's header. `grep -l
'Superseded\|Deprecated' docs/adr/*.md` lists them. Leave the directory flat and
record the write-once norm in `CLAUDE.md`.

**Pros:** Nothing moves, no link breaks, and the status field stays the single
encoding of whether an ADR is active — no second place for that fact to live, and
therefore no way for the two to disagree. Every tool that globs `docs/adr/*.md`,
including the whole `adr-toolkit` family, keeps seeing the whole corpus.

**Cons:** It answers the question only for someone who already knows to ask it.
The failure is a reader opening the directory, seeing 26 equally-weighted
filenames, and reading a superseded decision as current — and a header field
inside a file does not reach them until after they have opened it. It also does
not scale: one superseded ADR in 26 is noise a careful reader can absorb, and
forty in a hundred is not.

### Option 2: A `docs/adr/archive/` directory for Superseded and Deprecated ADRs

Move an ADR into `archive/` when it reaches a terminal, non-active status. It
keeps its number forever; numbers are never reused.

**Pros:** The active corpus is what the directory listing shows, which is the
form the question is actually asked in. It scales — the active set stays legible
however much history accumulates. And the correspondence between location and
status is mechanically checkable in both directions, so the second encoding
Option 1 rightly warns about cannot drift.

**Cons:** Every inbound link to a moved ADR breaks and must be rewritten, once
per archiving. The `adr-toolkit` family globs `docs/adr/*.md`, so archived ADRs
silently leave the corpus `/adr-consistency` checks — defensible for a frozen
record, but it is a reduction in coverage rather than a free win. And it does
create the second encoding of "is this active", which is only safe because it is
enforced.

### Option 3: Delete non-active ADRs

Git holds every deleted file forever. Remove them from the tree.

**Pros:** The strongest possible answer to "which are active" — only active ones
exist. No links to rewrite, because nothing links to a file that is gone.

**Cons:** ADR 0015 records that every Phase 1 commit reached `main` ungated, and
its own header says it is kept "rather than deleted because the interval was
real". Deleting it deletes the evidence of a gap, which is precisely the tidying
this repository refuses. A superseded decision also explains why the current one
looks as it does, and that context is worth more than the directory hygiene.

### Option 4: An index file listing active and archived ADRs

Keep the directory flat and add `docs/adr/README.md` enumerating both sets.

**Pros:** Navigation solved with no file moved and no link broken; a reader gets
titles and one-line summaries as well as status.

**Cons:** A hand-maintained list of files that sits beside the files. It is wrong
the first time someone adds an ADR without updating it, and being wrong is worse
than being absent because it is trusted. This is theme **T-2** in its most
ordinary form, and this repository has a checker precisely because such lists
drift.

## Decision

**We will write an ADR once.** An accepted ADR stands on its own and is not
edited to reflect later thinking. Amendment under ADR 0024 is the exception, not
the method, and is permitted only where both of these hold:

- the decision itself is unchanged, and
- the record has become **factually false** — it asserts something about the
  world that is no longer true.

ADR 0016's "expires by construction" is the model case: the decision (exit-code
semantics) was untouched, and the ADR asserted a bound that had stopped holding.
Anything that changes *what was decided* is a new ADR that supersedes the old
one, however small the change looks. When in doubt, supersede — a redundant ADR
costs a file, and an ADR that quietly no longer means what it says costs the
corpus its credibility.

Recording implementation progress — the `## Applied — pass N` sections in ADRs
0018, 0019 and 0020 — is not amendment and does not require a revision, because
it adds evidence that the decision was carried out rather than changing it. The
revision counter tracks changes to the decision record, not to the world.

**We will also add `docs/adr/archive/`**, and move an ADR into it when it reaches
a terminal non-active status — `Superseded` or `Deprecated`. `Draft` and
`Proposed` ADRs stay in the active directory: they are live work, not history.

Option 2 is chosen over Option 1 because the question "which of these is current"
is asked by looking at a directory, and an answer that requires opening files
does not reach the person asking. Option 1's real objection — that location and
status are then two encodings of one fact — is answered by enforcing the
correspondence rather than by trusting it: `tests/test_adr_revisions.py` fails an
`Accepted` ADR under `archive/` and a `Superseded` one outside it, in both
directions. Option 3 destroys evidence this repository has an explicit habit of
keeping, and Option 4 builds the hand-maintained list that this repository owns a
checker to avoid.

### An archived ADR keeps its number, and its number is never reused

ADR 0015 stays ADR 0015 at `docs/adr/archive/0015-interim-branch-discipline.md`.
Every reference to "ADR 0015" anywhere in this repository stays correct; only the
path changes. Reusing a number would make every historical reference ambiguous,
including the ones in commit messages that cannot be rewritten.

### A live control's `rationale_adr` may never point into the archive

The register cites an ADR as the reasoning behind a control. If that ADR is
archived while the control is live, the control's stated reasoning is a decision
the corpus has marked as no longer current. The schema already requires the path
to resolve, so a naive move fails loudly — but it fails with "file does not
exist", which diagnoses the symptom. The test names the actual rule.

Superseding a control's rationale ADR therefore means repointing `rationale_adr`
at the replacement in the same change, which is a `register_contract` question
to answer at the time rather than a rule to fix here.

### What archiving costs, stated rather than discovered

The `adr-toolkit` family globs `docs/adr/*.md`. An archived ADR leaves the corpus
that `/adr-consistency` scans, so it will no longer be checked for contradictions
against live decisions, and its links will no longer be verified. That is
acceptable for a frozen record and it is a real reduction, not a free win. The
local test checks what still matters for an archived ADR — that it is genuinely
non-active, that it names its replacement, and that the replacement resolves.

## Consequences

**Positive outcomes:**

- `ls docs/adr/` answers "what decisions are in force" without opening a file,
  and keeps answering it as the corpus grows.
- "Should I amend or supersede" has a two-clause test instead of an inference
  from three ADRs about mechanism.
- The distinction between amending a decision and recording its implementation is
  written down, which retires the question of whether ADR 0018's five `Applied`
  passes were five amendments.
- Location and status cannot disagree, because both directions are checked.

**Trade-offs and risks:**

- Archiving breaks inbound links, once per archived ADR. Three were rewritten
  here; a future archiving pays the same cost, and a missed one is a broken link
  rather than a wrong answer.
- Archived ADRs leave the `/adr-consistency` corpus, as above.
- "Factually false" is a judgement, and a determined author can call any
  unwelcome amendment a correction. The counter is that supersession is the
  cheap, always-safe option, so the incentive runs the right way — but the rule
  is a norm with a test for its form, not for its application.
- This ADR narrows guidance given three days ago in ADRs 0024 and 0025 without
  amending either, on the grounds that their decisions are unchanged and this one
  sits above them. That is the correct reading, and it is also exactly the
  judgement call the paragraph above admits is soft.

## Related ADRs

- [ADR 0024: Keep Only Direction Values in the Variance Vocabulary](0024-variance-vocabulary-is-direction-only.md)
  — established amend-in-place over supersession; this ADR makes that the
  exception rather than the method.
- [ADR 0025: Record an Amendment as a Numbered Revision](0025-an-amendment-is-a-recorded-revision.md)
  — the mechanism for the exception, and the test extended here to enforce the
  status-location correspondence.
- [ADR 0008: Protect the Default Branch by Ruleset](0008-protected-default-branch.md)
  — superseded ADR 0015, making it the first and so far only inhabitant of the
  archive.

## References

- [Michael Nygard, *Documenting Architecture Decisions*](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
  — "we will keep ADRs in the project repo... if a decision is reversed, we will
  keep the old one around, but mark it as superseded", which is the immutability
  default this ADR restores.
- [`adr-toolkit@0.1.11`](https://github.com/EqualExperts/ee-skills-incubator)
  — `adr-status/adr-lifecycle-rules.md`, which owns the five status values and
  models no archive.
