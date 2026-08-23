# ADR 0008: Protect the Default Branch by Ruleset

**Status:** Accepted
**Date:** 2026-08-16
**Revision:** 1

Rationale for control **CI-001** in `controls.yaml`.

## Background

Every other blocking control in this register expresses its verdict as a CI
check. If the default branch accepts direct pushes, force-pushes, or merges
without that check passing, then every one of those controls is advisory in
fact whatever the register says — the enforcement chain has a bypass at its
final link.

This is platform state, not file state. No tracked file records whether branch
protection exists, which is why it is the classic quiet regression: relaxed
during an incident, never restored, and invisible to every on-disk audit
(theme T-3, declared but unreachable). The OpenSSF Baseline lists branch
protection among its core expectations for exactly this reason, and trunk-based
development depends on the trunk being the branch whose green is trustworthy.

## Alternatives Considered

### Option 1: Convention — merge via PR by agreement

Document that changes go through pull requests with passing checks.

**Pros:** No configuration; no admin friction.
**Cons:** Unenforced convention is theme T-1; the bypass gets used precisely
under the deadline pressure it should resist; nothing detects the drift.

### Option 2: A GitHub ruleset, verified by reading platform state back

A ruleset on the default branch requiring a pull request, at least one passing
status check, and forbidding force-push — verified `kind: remote` by reading
the ruleset back through the API.

**Pros:** The bypass is mechanically closed; verification catches silent
relaxation; rulesets are layerable and API-readable, which suits both
deployment and audit.
**Cons:** Verification needs credentials and network, so local runs report
`SKIPPED (no credentials)` — a verdict deliberately distinct from a pass.

## Decision

We will protect the default branch with a GitHub ruleset requiring a pull
request and a passing status check and forbidding force-push, verified against
live platform state, recorded as control CI-001 at `rung: blocking` with
`variance: forbidden`.

Ruleset state is read back rather than trusted because the failure mode being
targeted is precisely a protection that everyone believes is still on.

## Consequences

**Positive outcomes:**

- Every blocking control's CI verdict becomes unbypassable rather than
  customary.
- Silent relaxation of protection is a reportable verification failure.

**Trade-offs and risks:**

- The only Tier-1 control that cannot be verified offline; a run without
  credentials is explicitly incomplete rather than falsely green.
- Admin emergencies need a deliberate, visible ruleset change — the friction is
  the feature.

## Related ADRs

- [ADR 0001: Block Secrets Before They Reach the Remote](0001-secrets-never-reach-the-remote.md)
  — its push-protection half lives in the same platform-state locus.
- [ADR 0011: Test Failures Are Terminal](0011-test-failures-are-terminal.md) —
  the check this ruleset makes unbypassable.
- [ADR 0015: Work on Branches While the Default Branch Is Unprotected](archive/0015-interim-branch-discipline.md)
  — **superseded by this ADR** on 2026-08-17. It proposed a convention to stand
  in for this control while no ruleset existed; creating the ruleset made the
  convention redundant before it was ever ratified.
- [ADR 0014: Make Remote-Locus Controls Satisfiable on This Repository](0014-satisfying-remote-locus-controls.md)
  — made this control satisfiable at all on this repository.
- [ADR 0017: Report a Partially Implemented Control as Partial](0017-partial-verification-is-reported.md)
  — CI-001 was the first control to declare a partial while its ruleset was
  unread.
- [ADR 0021: How Remote Verification Authenticates](0021-how-remote-verification-authenticates.md)
  — how the ruleset state this control requires is actually read back, and what
  an empty effective-rules answer means.

## References

- [OpenSSF Baseline](https://baseline.openssf.org/)
- [GitHub rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
- [Trunk-based development](https://trunkbaseddevelopment.com/)
