# ADR 0015: Work on Branches While the Default Branch Is Unprotected

**Status:** Superseded
**Date:** 2026-08-17
**Superseded by:** [ADR 0008: Protect the Default Branch by Ruleset](../0008-protected-default-branch.md)
**Revision:** 1

Superseded by [ADR 0008](../0008-protected-default-branch.md) on 2026-08-17, the
same day it was written, and **never ratified** — the gap it proposed to bridge
by convention was closed by real enforcement before the proposal was decided.
The `default-branch-protection` ruleset (id `20937135`) makes CI-001's
requirement mechanical, so a convention standing in for it has nothing left to
do.

ADR 0008 is dated 2026-08-16, a day *earlier* than this ADR. The supersession is
not backwards: ADR 0008 recorded CI-001 as a control before the platform could
satisfy it, this ADR proposed a convention to stand in for it in the meantime,
and the ruleset landed the same day this was written — so the stand-in was
overtaken by the thing it stood in for, which had been decided first.

Kept rather than deleted because the interval was real: every Phase 1 commit
reached `main` ungated, and this record is what makes that visible instead of
tidied away.

One correction it earned along the way, worth carrying into future interim
measures: an earlier revision set its sunset at "a ruleset exists **and** CI-001
verifies against it". That was over-tight. This ADR existed because *nothing
enforced*; enforcement now exists, and whether the checker can read it back is
CI-001's audit concern, not this ADR's reason to exist. Conflating enforcement
with verification would have kept a dead stopgap alive through all of Phase 3.

## Background

At the time of writing, `main` reported `"protected": false`. Nothing required a
pull request, nothing required a passing check, and force-push was permitted.
Every blocking control in
the register expresses its verdict as a CI check, so while this held, all of
them were advisory in fact whatever their `rung` said — the enforcement chain had
a bypass at its final link.

This is not hypothetical. All five Phase 1 commits were pushed directly to
`main`, and the conformance workflow reported success *after* each push rather
than gating it. That is theme **T-3** — the gates are declared and, at the merge,
unreachable.

CI-001 exists to close this, and did. Its mechanism became *available* on
2026-08-17, when [ADR 0014](../0014-satisfying-remote-locus-controls.md) was
implemented and the repository went public: the rulesets API changed from `403`
to an empty list. Availability was not application, though — for a few hours the
capability existed and no ruleset did, so `main` stayed unprotected and this
ADR's interval stayed open.

That distinction is the one thing this ADR is worth remembering for. Publication
made protection *possible*; creating the ruleset made it *real*, and the two
were not the same act. Anyone reading the plan would have assumed the first
implied the second. The interval closed the same day, when the ruleset was
created and a direct push to `main` was refused with
`push declined due to repository rule violations`.

## Alternatives Considered

### Option 1: Change nothing until ADR 0014 lands

Continue pushing to `main`; rely on the register to record that CI-001 is
unsatisfied.

**Pros:** No workflow change; fastest for a single author.
**Cons:** The habit that will have to change later goes on being reinforced,
and every direct push is a merge that no gate examined. If ADR 0014 stalls, the
interval becomes the status quo silently.

### Option 2: Adopt branch-and-pull-request by convention now

Work on branches, open a pull request, wait for the `Standard` and `Lint`
workflows, and merge only when they pass — with nothing enforcing any of it.

**Pros:** The gates start actually gating, at the only point where they can
today. The workflow is identical to the one CI-001 will later make mandatory, so
ratifying ADR 0014 changes nothing about how work is done. Costs nothing and
starts immediately.
**Cons:** Convention is not enforcement, and this ADR must not be mistaken for
satisfying CI-001. A lapse leaves no trace, which is exactly why the register
continues to report the control as unsatisfied.

## Decision

We will work on branches and merge through pull requests with passing checks
from now on, while continuing to report CI-001 as unsatisfied until its ruleset
exists.

Convention is chosen over waiting because the alternative reinforces a habit
that must change anyway, and because the checks already exist and already pass —
the only thing missing is the discipline to consult them before merging rather
than after pushing. This decision deliberately does **not** touch the register:
CI-001 stays `blocking` and unsatisfied, because a convention that nothing
verifies is precisely what the register refuses to count as a control.

## Consequences

**Positive outcomes:**

- Every change from here on is examined by the gates before it reaches `main`.
- The working practice matches the enforced one, so ADR 0014 becomes a
  formalisation rather than a migration.
- The gap stays visible: the checker keeps reporting CI-001 as unverified, so
  nobody can mistake the convention for the control.

**Trade-offs and risks:**

- Unenforced discipline fails silently and under exactly the deadline pressure
  it is meant to resist; this is a mitigation, not a fix.
- Solo pull requests carry review overhead with no reviewer, which tempts
  self-merging without reading the checks — the practice is worth nothing if the
  checks are not consulted.

## Related ADRs

- [ADR 0014: Make Remote-Locus Controls Satisfiable on This Repository](../0014-satisfying-remote-locus-controls.md)
  — implemented 2026-08-17, which made enforcement possible but not yet real.
  This ADR is superseded by [ADR 0008](../0008-protected-default-branch.md) once the
  ruleset exists and CI-001 verifies against it, not on publication alone.
- [ADR 0008: Protect the Default Branch by Ruleset](../0008-protected-default-branch.md)
  — the control this interim posture stands in for, and does not satisfy.

## References

- [GitHub rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
- [Trunk-based development](https://trunkbaseddevelopment.com/)
