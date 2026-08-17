# ADR 0015: Work on Branches While the Default Branch Is Unprotected

**Status:** Proposed
**Date:** 2026-08-17

Open decision from
[`04-build-plan.md`](../04-build-plan.md) § Phase 1.5 § Decisions required.
This record states the recommendation and is not ratified.

## Background

`main` reports `"protected": false`. Nothing requires a pull request, nothing
requires a passing check, and force-push is permitted. Every blocking control in
the register expresses its verdict as a CI check, so while this holds, all of
them are advisory in fact whatever their `rung` says — the enforcement chain has
a bypass at its final link.

This is not hypothetical. All five Phase 1 commits were pushed directly to
`main`, and the conformance workflow reported success *after* each push rather
than gating it. That is theme **T-3** — the gates are declared and, at the merge,
unreachable.

CI-001 exists to close this. Its mechanism became *available* on 2026-08-17,
when [ADR 0014](0014-satisfying-remote-locus-controls.md) was implemented and the
repository went public: the rulesets API changed from `403` to an empty list. But
available is not applied — no ruleset exists, and `main` still reports
`"protected": false`.

That distinction is the correction this ADR needed, and it is why the interval is
longer than first written. Publication makes protection *possible*; a separate
act makes it *real*. So this ADR's sunset condition is **not** "ADR 0014 is acted
on" but "a default-branch ruleset exists and CI-001 verifies against it". The
question it settles is how to behave until then. Leaving that unaddressed is
theme **T-4**: a known failure absorbed rather than surfaced.

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

- [ADR 0014: Make Remote-Locus Controls Satisfiable on This Repository](0014-satisfying-remote-locus-controls.md)
  — implemented 2026-08-17, which made enforcement possible but not yet real.
  This ADR is superseded by [ADR 0008](0008-protected-default-branch.md) once the
  ruleset exists and CI-001 verifies against it, not on publication alone.
- [ADR 0008: Protect the Default Branch by Ruleset](0008-protected-default-branch.md)
  — the control this interim posture stands in for, and does not satisfy.

## References

- [GitHub rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
- [Trunk-based development](https://trunkbaseddevelopment.com/)
