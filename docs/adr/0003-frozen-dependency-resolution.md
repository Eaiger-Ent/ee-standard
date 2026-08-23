# ADR 0003: Install Dependencies From a Committed Lockfile

**Status:** Accepted
**Date:** 2026-08-16
**Revision:** 1

Rationale for control **SUP-001** in `controls.yaml`.

## Background

A build that re-resolves its dependencies takes whatever the registry serves at
that moment. Two runs of the same commit can differ, a compromised or yanked
upstream release walks straight in, and "works on my machine" stops being
diagnosable because no two machines resolved the same graph.

The OpenSSF Baseline treats a committed lockfile with frozen installation as
table stakes for supply-chain integrity. The predecessor's variant of this
failure was theme T-2 — one definition copied, then diverged — arriving as
environments that each resolved their own versions of nominally identical
dependencies.

## Alternatives Considered

### Option 1: Version ranges resolved at install time

Declare ranges in the manifest and let each environment resolve them.

**Pros:** Always picks up compatible fixes without a commit.
**Cons:** Builds are non-reproducible; upstream compromise or breakage arrives
unreviewed; CI green and local red can both be true for the same commit.

### Option 2: Committed lockfile, frozen installs everywhere

Commit a lockfile for every package manager in use and require CI to install
from it in frozen mode — resolution failure, not re-resolution, when the
manifest and lockfile disagree.

**Pros:** Every environment installs the same graph; updates arrive as
reviewable diffs; frozen mode turns drift into a loud failure.
**Cons:** Updates require a commit — which is the point, but adds ceremony that
must be automated to stay tolerable.

## Decision

We will require a committed lockfile for every package manager in use and
frozen-mode installation in CI, recorded as control SUP-001 at `rung: blocking`
with `variance: narrowing-only`.

Frozen mode is the half that makes the lockfile real: a lockfile that CI quietly
re-resolves past is theme T-1, a stated standard nothing enforces.

## Consequences

**Positive outcomes:**

- The same commit produces the same dependency graph on every machine and in CI.
- Dependency changes are visible in review rather than implicit in timing.

**Trade-offs and risks:**

- Update ceremony is real; ADR 0004's automated proposals are the mitigation,
  not an optional extra.
- Frozen installs fail loudly when the manifest changes without the lockfile —
  a deliberate cost, paid at commit time instead of at incident time.

## Related ADRs

- [ADR 0004: Automate Dependency Update Proposals](0004-automated-dependency-proposals.md)
  — makes the lockfile discipline sustainable.
- [ADR 0005: Pin CI Actions to Commit SHAs](0005-pinned-ci-actions.md) — the
  same pinning discipline applied to the workflow's own dependencies.

## References

- [OpenSSF Baseline](https://baseline.openssf.org/)
