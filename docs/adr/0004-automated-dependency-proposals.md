# ADR 0004: Automate Dependency Update Proposals

**Status:** Accepted
**Date:** 2026-08-16

Rationale for control **SUP-002** in `controls.yaml`.

## Background

Pinning everything (ADR 0003, ADR 0005, ADR 0007) freezes the world at a known
state. Left alone, that state ages: security fixes do not arrive, and the
eventual catch-up upgrade is large, risky, and postponed for exactly that
reason. Pinning without a paired update mechanism converts supply-chain risk
into staleness risk rather than removing it.

OpenSSF Scorecard's Maintained and Dependency-Update-Tool checks encode the
industry consensus: pinned dependencies plus an automated proposer of updates.
The proposals arrive as pull requests, so every version change passes the same
review and CI gates as any other change.

## Alternatives Considered

### Option 1: Manual periodic upgrades

Rely on engineers to schedule dependency reviews.

**Pros:** No configuration; full human control of timing.
**Cons:** Decays the moment attention moves elsewhere (theme T-1); security
patches wait for someone to remember; the gap between pin and upstream grows
until upgrading becomes a project.

### Option 2: Automated update proposals covering every ecosystem

A Dependabot or Renovate configuration that covers every ecosystem present in
the repo — language packages, GitHub Actions, and the devcontainer image among
them.

**Pros:** Updates arrive continuously as small reviewable PRs; coverage is a
file shape a checker can assert; the same mechanism proposes digest bumps for
the artefacts other controls pin.
**Cons:** PR noise if left untuned; an ecosystem added later can be missed —
which is why the verification checks coverage, not mere presence.

## Decision

We will require an automated dependency update configuration covering every
ecosystem present in the repository, recorded as control SUP-002 at
`rung: blocking` with `variance: narrowing-only`.

The coverage requirement is the substance: a Dependabot file that watches one
ecosystem while three exist passes a presence check and fails the actual
intent.

## Consequences

**Positive outcomes:**

- Every pin in the repo has a mechanism proposing its next value as a
  reviewable diff.
- Update effort is amortised into small steps instead of saved up as a
  migration.

**Trade-offs and risks:**

- Proposal PRs consume review attention; grouping and scheduling configuration
  is the tuning knob, and narrowing-only variance permits it.
- Automated proposals still require humans to merge them — an unmerged backlog
  is visible, which is the best that mechanism can guarantee.

## Related ADRs

- [ADR 0003: Install Dependencies From a Committed Lockfile](0003-frozen-dependency-resolution.md)
  — the pinning that makes proposals meaningful.
- [ADR 0007: Pin Devcontainer Image and Features](0007-pinned-devcontainer-features.md)
  — relies on this control for digest bumps.
- [ADR 0005: Pin CI Actions to Commit SHAs](0005-pinned-ci-actions.md)
  — SUP-003, whose SHA bumps this control proposes.
- [ADR 0012: Statically Analyse Infrastructure Code Before Apply](0012-iac-static-analysis.md)
  — IAC-001, whose two analysers this control keeps current.

## References

- [OpenSSF Scorecard](https://scorecard.dev/)
- [Dependabot](https://docs.github.com/en/code-security/dependabot/working-with-dependabot)
