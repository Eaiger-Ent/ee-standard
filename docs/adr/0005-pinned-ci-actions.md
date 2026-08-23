# ADR 0005: Pin CI Actions to Commit SHAs

**Status:** Accepted
**Date:** 2026-08-16
**Revision:** 2

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
history), so variance is `justified` rather than forbidden. *(The variance
conclusion here was overtaken at contract 3 — see § Decision. The cost it names
is real; the value it reached for could not be implemented.)*

## Decision

We will require every third-party action reference in every workflow to be a
full commit SHA, with owner-published actions exempt, recorded as control
SUP-003 at `rung: blocking` with `variance: justified`.

`justified` variance keeps the rare legitimate exception recorded, owned, and
expiring instead of silent.

**Amended 2026-08-17 at register contract 3: the variance is
`narrowing-only`.** The clause above is overtaken, and only that clause — the
SHA-pinning decision, the owner-published exemption and the reasoning for both
stand unchanged, and this ADR remains SUP-003's `rationale_adr`.

`justified` was removed from the vocabulary because its anti-loophole mechanism
was structurally unreachable: a justified weakening was supposed to become a
baseline entry, and SUP-003 is Tier 1, where the validator rejects any baseline
at all. The value permitted weakenings it had no way to record.
[ADR 0024](0024-variance-vocabulary-is-direction-only.md) holds that decision;
it was taken at contract 3 and recorded there on 2026-08-23, which is why this
amendment is dated to the change and not to its writing.

`narrowing-only` is stricter, so nothing SUP-003 passed before the change fails
after it. The Option 2 case above — a required action publishing no stable
history — is now answered by narrowing `applies_to`, by an allow-list in the
verify block's `args:`, or by a reviewed change to the control's register entry.
What is gone is standing permission to deviate without one.

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
- [ADR 0007: Pin Devcontainer Image and Features](0007-pinned-devcontainer-features.md)
  — the same immutability discipline applied to the environment.
- [ADR 0024: Keep Only Direction Values in the Variance Vocabulary](0024-variance-vocabulary-is-direction-only.md)
  — overtakes this ADR's `variance: justified` clause, and nothing else in it.

## References

- [SLSA v1.0 Build levels](https://slsa.dev/spec/v1.0/levels)

## Revision History

| Rev | Date | What changed | Ratified by |
| --- | --- | --- | --- |
| 1 | 2026-08-16 | Original decision: SUP-003, third-party actions pinned to 40-character commit SHAs, owner-published actions exempt. | Nathan Carney |
| 2 | 2026-08-17 | Variance `justified` → `narrowing-only` at register contract 3, per [ADR 0024](0024-variance-vocabulary-is-direction-only.md). The SHA-pinning decision and the owner exemption are unchanged. Option 2's variance conclusion annotated as overtaken. | Nathan Carney |

Revisions before 2026-08-23 are backfilled from the amendments in the body and from git, per [ADR 0025](0025-an-amendment-is-a-recorded-revision.md); they were not recorded at the time.
