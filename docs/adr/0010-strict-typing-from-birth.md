# ADR 0010: Enforce Strict Static Typing From Birth

**Status:** Accepted
**Date:** 2026-08-16
**Revision:** 1

Rationale for control **TYP-001** in `controls.yaml`.

## Background

Static typing is cheapest at the moment a repository is born and grows more
expensive every day it is deferred: untyped code accretes, the eventual
migration becomes a project, and the project gets postponed. Strictness follows
the same curve — a checker run in permissive mode invites per-file opt-outs
that quietly hollow it out until "typed" describes the configuration rather
than the code.

Tier 1 of this register is defined as birth conditions: properties a greenfield
repo can satisfy from its first commit at near-zero cost. Strict typing
qualifies precisely there, and only there — which is why the control belongs in
Tier 1 with no baseline, while a legacy adopter would negotiate a baseline
under a different tier.

## Alternatives Considered

### Option 1: Gradual typing, tightened later

Start permissive and ratchet strictness as the codebase matures.

**Pros:** No up-front friction; suits legacy code with untyped history.
**Cons:** "Later" requires a decision nothing forces (the predecessor's
excellent-tools-parked-at-advisory failure); every permissive month adds
migration cost; opt-outs accumulate without a shrink-only mechanism.

### Option 2: Strict mode from the first commit, opt-outs only via a baseline

mypy in strict mode (or `tsc --strict`) over all first-party source in CI,
blocking, with per-file opt-outs impossible beyond a recorded baseline — and
the baseline `null` for Tier-1 repos.

**Pros:** A greenfield repo pays near nothing; the type system's guarantees
hold everywhere rather than somewhere; any tolerated exception is visible and
shrink-only.
**Cons:** Strict mode's friction lands on day one — genuinely a cost for
exploratory code, and the reason this is a birth condition rather than a
retrofit demand.

## Decision

We will run the type checker in strict mode over all first-party source in CI,
blocking, with no per-file opt-out beyond the recorded baseline, recorded as
control TYP-001 at `rung: blocking` with `variance: narrowing-only`.

## Consequences

**Positive outcomes:**

- A class of defects is excluded from the first commit instead of migrated
  toward later.
- Any weakening is a visible baseline entry under the may-only-shrink rule,
  never a quiet config edit.

**Trade-offs and risks:**

- Strictness pushes back on quick scripts; the answer is typing them, and the
  control deliberately does not blink first.
- Third-party stubs are sometimes missing; dependency choice absorbs that cost
  where possible.

## Related ADRs

- [ADR 0009: Lint From One Pinned Definition at Every Locus](0009-single-lint-definition.md)
  — shares the locus and suppression discipline.
- [ADR 0011: Test Failures Are Terminal](0011-test-failures-are-terminal.md) —
  the third quality gate of the trio.

## References

- [mypy command line — strict mode](https://mypy.readthedocs.io/en/stable/command_line.html)
- [Python typing specification](https://typing.python.org/en/latest/spec/)
