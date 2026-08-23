# ADR 0017: Report a Partially Implemented Control as Partial

**Status:** Accepted
**Date:** 2026-08-17
**Revision:** 1

Ratified decision from
[`09-phase-1.5-review.md`](../09-phase-1.5-review.md) § Decisions required.

**Not yet implemented.** Acceptance settles the mechanism, not the code: the
register has no field for a partial declaration, GOV-001 still prints an
unqualified `PASS`, and no expiry is enforced. Phase 1.5's exit criteria track
that work.

## Background

GOV-001's title claims that *"every blocking control is reachable from a CI step
that can fail"*. [`00-concepts.md`](../00-concepts.md) calls it the control
aimed at the predecessor's most dangerous failure: a gate that was configured,
believed in, and unreachable. The README is more specific still — the sharpest
instance was a lint workflow that existed, was believed in, and **was not a
required status check**.

The build plan concedes that this cannot be checked yet: GOV-001 *"cannot be
finished before this phase [3] — proving a `blocking` control is reachable from a
CI step that can fail requires reading platform state, not files."* The
implementation reads workflow YAML only, and reports an unqualified `PASS`.

So the guard against theme **T-3** is currently blind to T-3 and says nothing
about being blind. It is worse than a gap, because the report actively asserts
the property. Two details make it concrete: reachability is decided by a
substring test over step text, and any step invoking `standard-check` bare
short-circuits every control at once.

The contrast within the same report is instructive. A `kind: remote` block
announces its own incompleteness — `SKIPPED (no credentials)` — and the summary
footer says the report is incomplete. A partially implemented *control* has no
such vocabulary, so it borrows the vocabulary of a fully verified one.

## Alternatives Considered

### Option 1: Leave the PASS and document the limitation

Keep the verdict; rely on the build plan to record that GOV-001 is partial.

**Pros:** No change to the report or the schema.
**Cons:** A reader of the report cannot know, and the report is what CI and the
sweep consume. Documenting a lie elsewhere does not stop it being asserted here —
this is the definition of a control becoming theatre.

### Option 2: Report it `UNCLASSIFIED` until Phase 3

Treat any knowingly incomplete verification as unclassifiable.

**Pros:** Honest, and reuses an existing verdict with no schema change.
**Cons:** Discards a real result. GOV-001's file-level half genuinely passes, and
collapsing "half-verified" into "unknown" loses the signal that the half which
*can* be checked is clean — which is most of the value between now and Phase 3.

### Option 3: Report the computed verdict plus an explicit partial annotation

A verification block may declare itself not yet fully implemented, naming what it
cannot see. The control renders the verdict it can compute, followed by a
`partial:` line, and the run is incomplete in the sense of
[ADR 0016](0016-exit-codes-for-unverifiable-controls.md).

GOV-001 would read `PASS` with
`partial: CI-step reachability requires platform state (Phase 3)`.

**Pros:** No verdict overstates its evidence, and no result is thrown away. The
mechanism generalises to any control that gains a locus later, which is the
normal direction of travel. It composes with ADR 0016, so a partial control
cannot leave a clean exit code.
**Cons:** Needs a schema field so the register — not the checker — declares what
is unimplemented, otherwise the checker becomes a second source of truth about
its own coverage. And "partial" is comfortable: without pressure it becomes
permanent.

## Decision

We will let a verification block declare itself partially implemented in the
register, render the computed verdict alongside a `partial:` annotation naming
the unverified property, and require an expiry date on every such declaration.

The expiry is the part that keeps this from becoming a loophole, and it is
already the register's answer to the same problem elsewhere: `review_by` plus
GOV-003 turn silence into a build failure, and a partial declaration past its
expiry fails the same way. Option 2 was rejected because discarding a valid
half-result makes the report less useful without making it more honest, and
Option 1 because the report is the artefact people read.

Ratified on 2026-08-17. The schema addition it requires carries a
`register_contract` bump, so it lands before Phase 2's gate skills read that
contract. GOV-001's own partial declaration expires when Phase 3 gives it
platform state to read — ADR 0014's implementation was a precondition for that,
not the whole of it.

## Consequences

**Positive outcomes:**

- Every verdict in the report is backed by evidence of the kind it claims.
- GOV-001 can ship its file-level value immediately without asserting the
  platform-level property it cannot see.
- Coverage becomes a register fact rather than a checker implementation detail,
  so it is reviewable in the same place as everything else.

**Trade-offs and risks:**

- A schema addition, and therefore a `register_contract` bump and a deployment
  contract change — the cost of doing this properly rather than in the checker.
- Expiries need enforcing or they rot; the mechanism is GOV-003's, so the
  enforcement already exists, but the dates need choosing deliberately.
- Overuse would let controls ship indefinitely half-built. The expiry bounds it;
  review has to police the intent.

## Related ADRs

- [ADR 0016: Give "Could Not Verify" Its Own Exit Code](0016-exit-codes-for-unverifiable-controls.md)
  — how a partial control affects the run's exit status.
- [ADR 0014: Make Remote-Locus Controls Satisfiable on This Repository](0014-satisfying-remote-locus-controls.md)
  — its implementation is the precondition for GOV-001 dropping its partial
  annotation; Phase 3 reading the platform state is what actually does it.
- [ADR 0008: Protect the Default Branch by Ruleset](0008-protected-default-branch.md)
  — the platform state GOV-001 must eventually read.
- [ADR 0018: Draw the Boundary Between Register and Checker](0018-register-checker-boundary.md)
  — the partial-declaration field landed in the same contract-3 pass.
- [ADR 0022: What Must Be True Before CI Carries a Platform Token](0022-a-platform-token-ci-carries.md)
  — refused an Option 4 that would have weakened this machinery for one
  control's convenience.
- [ADR 0023: Choose the Smallest Model a Task Can Be Trusted To](0023-smallest-model-a-task-can-be-trusted-to.md)
  — AGT-001 declares its unverifiable runtime half as a partial under this ADR.

## References

- [OpenSSF Baseline](https://baseline.openssf.org/)
