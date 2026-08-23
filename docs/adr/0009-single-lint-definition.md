# ADR 0009: Lint From One Pinned Definition at Every Locus

**Status:** Accepted
**Date:** 2026-08-16
**Revision:** 1

Rationale for control **LNT-001** in `controls.yaml`.

## Background

The predecessor's most expensive defects traced to one pattern: the same rule
existing in three places and drifting between them — one lint config for the
editor, another for pre-commit, a third inlined in CI (theme T-2). Once the
editor and CI disagree, engineers learn to distrust the editor, and the cheap
feedback loop stops being used; findings then arrive at the most expensive
locus, or are suppressed there (theme T-4).

The control therefore targets the relationship, not the tool: one pinned linter
version reading one configuration at editor, pre-commit, and CI, with no
failure suppression in the CI invocation.

## Alternatives Considered

### Option 1: Per-locus configuration

Let the editor, hooks, and CI each carry their own lint setup.

**Pros:** Each locus can be tuned independently; no coordination needed to
change one.
**Cons:** Divergence is guaranteed over time; every disagreement erodes trust
in the earliest, cheapest signal; the drift is invisible until a CI failure
contradicts a clean editor.

### Option 2: One pinned tool and config, referenced by every locus

A single configuration file and a single pinned tool version, referenced —
never copied — by the editor integration, the pre-commit hook, and the CI
step; CI's invocation checked for suppression (`|| true`,
`continue-on-error`, exit-zero flags).

**Pros:** Drift between loci becomes structurally impossible rather than
discouraged; a rule change is one reviewable edit; the wiring itself is
mechanically checkable.
**Cons:** Version bumps must land at all loci in one change — a coordination
cost the pinning tooling absorbs.

## Decision

We will run the configured linter from one pinned version and one
configuration at editor, pre-commit, and CI, with no failure suppression in
the CI invocation, recorded as control LNT-001 at `rung: blocking` with
`variance: narrowing-only`.

Narrowing-only variance lets a repo add rules or tighten thresholds locally
while making any loosening a register change first.

## Consequences

**Positive outcomes:**

- The editor's verdict is trustworthy because it is CI's verdict, sooner.
- Suppressed failures — the quiet way lint gates die — are a verification
  failure in their own right.

**Trade-offs and risks:**

- The verification asserts wiring shape, not lint output; a rule set that is
  weak everywhere passes — rule strength is a review concern, drift is the
  control's.
- Editor wiring is the least standardised locus and carries the most
  assertion nuance.

## Related ADRs

- [ADR 0013: One Markdown Rule Set](0013-one-markdown-rule-set.md) — the same
  principle applied to prose.
- [ADR 0010: Strict Typing From Birth](0010-strict-typing-from-birth.md) — the
  companion quality gate.
- [ADR 0011: Make Test Failures Terminal](0011-test-failures-are-terminal.md)
  — TST-001; the same no-suppression rule applied to the test command.
- [ADR 0012: Statically Analyse Infrastructure Code Before Apply](0012-iac-static-analysis.md)
  — IAC-001, which applies this one-definition discipline to the analysis
  configs.
- [ADR 0018: Draw the Boundary Between Register and Checker](0018-register-checker-boundary.md)
  — moved this control's tool versions and per-locus evidence into the register.
- [ADR 0019: Verify Exemptions Against the Files a Repository Tracks](0019-exemptions-cannot-hide-tracked-files.md)
  — LNT-001's `.claude/**` exclusion was the instance that prompted it.

## References

- [Ruff rules](https://docs.astral.sh/ruff/rules/)
- [pre-commit](https://pre-commit.com/)
