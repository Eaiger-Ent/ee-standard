# ADR 0005: Pin CI Actions to Commit SHAs

**Status:** Accepted
**Date:** 2026-08-16

Rationale for control **SUP-003** in `controls.yaml`.

## Background

A workflow step that references a third-party action by tag or branch executes
whatever that ref points at when the job runs. Tags are mutable: the
`tj-actions/changed-files` compromise demonstrated an attacker retargeting
existing version tags at malicious code, instantly poisoning every workflow
that trusted the tag. The workflow file did not change; what it executed did.

SLSA's build-level guidance treats an immutable reference as a precondition for
a trustworthy build. A 40-character commit SHA is the only reference GitHub
guarantees immutable, so it is the only reference that makes a third-party
action's content part of the reviewed change history.

## Alternatives Considered

### Option 1: Pin to version tags

Reference actions as `owner/action@v4`.

**Pros:** Human-readable; picks up patch releases automatically.
**Cons:** Tags are mutable, so the reference does not identify the code; an
upstream compromise propagates silently to every consumer (theme T-3 — the
declared version is not what runs).

### Option 2: Pin to full commit SHAs, first-party actions exempt

Every `uses:` of a third-party action references a 40-character commit SHA;
actions published by the repository owner are exempt because their integrity is
already this organisation's own responsibility.

**Pros:** The reference is immutable; upgrades are explicit diffs proposed by
the update mechanism (ADR 0004); the rule is mechanically checkable over
workflow files.
**Cons:** SHAs are unreadable without the conventional trailing version
comment; exceptional cases exist (a required action that publishes no stable
history), so variance is `justified` rather than forbidden.

## Decision

We will require every third-party action reference in every workflow to be a
full commit SHA, with owner-published actions exempt, recorded as control
SUP-003 at `rung: blocking` with `variance: justified`.

`justified` variance keeps the rare legitimate exception recorded, owned, and
expiring instead of silent.

## Consequences

**Positive outcomes:**

- An upstream tag retarget cannot change what this repository executes.
- Action upgrades become reviewable diffs with a before and after SHA.

**Trade-offs and risks:**

- Readability depends on the `# vX.Y.Z` convention beside each SHA being kept
  accurate — the comment can lie, but the SHA cannot.
- Automated update proposals (ADR 0004) are required to keep pinned SHAs from
  fossilising.

## Related ADRs

- [ADR 0003: Install Dependencies From a Committed Lockfile](0003-frozen-dependency-resolution.md)
  — the same immutability discipline for package graphs.
- [ADR 0004: Automate Dependency Update Proposals](0004-automated-dependency-proposals.md)
  — proposes the SHA bumps.

## References

- [SLSA v1.0 Build levels](https://slsa.dev/spec/v1.0/levels)
