# ADR 0046: A Stamp in a Code Fence Is an Example

**Status:** Accepted
**Date:** 2026-08-31
**Revision:** 1

## Background

A provenance stamp is a comment naming the control, the deploying gate, the
gate's deployment contract and the register's version. `stamps_by_file` finds
them by `git grep` over every tracked file and parsing each hit
([ADR 0038](0038-the-stamp-records-the-deployment-contract.md)).

It excludes nothing. Any tracked file carrying a well-formed stamp is read as a
deployed artefact — including a document that is *explaining what a stamp looks
like*.

Three such examples exist in this repository, and all three are inside fenced
code blocks:

| Where | Contract | What it is |
| --- | --- | --- |
| `docs/00-concepts.md` § The provenance stamp | 5 | The format, documented |
| `docs/adr/0038-…` § the "after" example | 5 | What the field added looks like |
| `docs/adr/0038-…` § the "before" example | **none** | *"What a stamp records today"* |

**The third cannot be removed.** ADR 0038 is the decision that introduced
`gate-contract`; it has to show a stamp without one in order to explain what it
is adding. Any ADR that changes a format must display the format it is changing.

Two things follow, and the second is the reason this is not a report cosmetic.

**`register-check deployments` reports `gate-secrets` as `UNRECORDED` for
ever.** The gate was re-run on 2026-08-31 and all six of its real artefacts
carry `gate-contract: 7`; the report still reads `UNRECORDED`, because a
contract-less example in an ADR is counted beside them. Re-running the gate
again cannot change that, so the one action the report recommends is the one
action that does not work.

**And `provenance_stamp_present` can pass on documentation alone.** The same
scan backs SEC-001's stamp read-back. Measured, in a repository containing a
single Markdown file explaining the format and **no gate deployed at all**:

```text
✓ file: provenance_stamp_present — gate-secrets stamped 1 artefact for
  SEC-001 (docs/concepts.md)
```

A Tier-1 `blocking` control, satisfied by prose describing the thing it is
supposed to verify happened. That is [`09-phase-1.5-review.md`](../09-phase-1.5-review.md)
§ F exactly — a `node_modules` grep that a comment could satisfy — and the fix
there was to refuse it by construction rather than to remember it.

## Decision

**In a Markdown file, a stamp inside a fenced code block is an example and is
not a deployment.** `stamps_by_file` strips fenced blocks from `.md` and
`.markdown` files before parsing, and parses every other file whole.

Fence handling follows CommonMark: three or more backticks or tildes, up to
three leading spaces, closed by a fence of the same character and at least the
same length. A block left unclosed at end of file is fenced to the end — the
conservative direction, since the alternative is reading a truncated document's
example as an artefact.

## Why this is the checker's rule and not the register's

[ADR 0018](0018-register-checker-boundary.md) asks one question before a rule
may live in `src/register_check/`: *could a reasonable Equal Experts repository
need this to differ without changing the checker?*

**No.** A fenced code block is Markdown's construct for *displaying* text rather
than the text being in force. A repository needing a stamp inside a fence to
count as a deployment would be asking for a document about deployments to be a
deployment. That is a property of the format, like the predicate grammar and the
`GOV-\d{3}` ID pattern that ADR 0018 already assigns to the checker.

The alternative considered was a register field naming documentation paths —
`meta.documentation: [docs/]` or similar. Rejected for two reasons. It is
configuration for something that needs no configuration: nobody's `docs/` is a
deployment target. And it would be a **loosening instrument** — a register that
listed `.github/` there would hide real artefacts from the very check that
proves they exist, with no `variance` to catch it, since `meta` governs no
control.

## What this does not do

**It does not decide which files a gate should have stamped.** That list is the
plugin's `deploys.json`, and `provenance_stamp_present` says so in as many
words: *"each control now proves its own deployment was recorded, and no control
proves the deployment was complete."* This ADR removes a source of false
evidence; it does not make the evidence exhaustive.

**It does not reach a non-Markdown document.** A stamp quoted in a
reStructuredText file, or in a plain-text README, still counts. That is accepted
rather than overlooked: the marker's own comment syntax (`# ee-control:`) is a
Markdown heading outside a fence, so nobody writes one there by accident, and
every documentation format this repository uses is Markdown. A second format
arriving is a new decision, not a gap in this one.

**It does not change what a stamp means.** ADR 0038 defines the fields and this
changes none of them.

## Consequences

`gate-secrets` reads `CURRENT` after its 2026-08-31 re-run, which is what that
re-run was for. The other gates go on reading `UNRECORDED` until each is re-run,
which is correct and is the state ADR 0038 introduced deliberately.

**A control can no longer be satisfied by a document about controls.** The
measured false PASS above now fails, which is a stricter checker rather than a
looser one — the direction a fix to a verification defect must go.

`tests/test_provenance_stamps.py` gains the negative case, because a defect
proven by measurement should be held by a test rather than by this record. The
three examples in `docs/` stay exactly as they are: they are correct
documentation, and the checker was wrong to read them.
