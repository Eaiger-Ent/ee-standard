# ADR 0011: Make Test Failures Terminal

**Status:** Accepted
**Date:** 2026-08-16
**Revision:** 1

Rationale for control **TST-001** in `controls.yaml`.

## Background

A test suite only gates anything if its exit code is the build's verdict. The
predecessor retrospective's theme T-4 — failures absorbed rather than surfaced
— names the many ways that link gets cut while the tests keep running: an
`|| true` added during an incident, a `continue-on-error:` that outlived its
reason, a report step that swallows the status of the run before it. Each
leaves a green pipeline over a red suite, which is strictly worse than no suite
because it manufactures confidence.

NIST SSDF PW.8 requires executable testing with results acted on; the acting-on
is the half this control makes mechanical. The check is therefore about the
chain, not the tests: the test command runs in CI, and no step between its exit
code and the job's verdict can absorb a non-zero status.

## Alternatives Considered

### Option 1: Tests run in CI, chain integrity by review

Add the test step and trust review to catch suppression.

**Pros:** Nothing to build; suppression is usually visible in a diff.
**Cons:** Suppression is added under exactly the pressure that defeats review,
and removed never; nothing detects the accumulated state, only the change.

### Option 2: Assert the chain mechanically

Verify that the test command runs in CI, that its exit code is the job's
verdict, and that no suppression construct (`|| true`, `continue-on-error:`,
exit-zero flags, `set +e`) sits in the chain.

**Pros:** The quiet failure mode becomes a loud verification failure; the
assertion is offline and cheap; the state is checked, not just the diff.
**Cons:** Suppression detection is pattern-based over workflow files and can
be evaded by obscure constructions; review remains the backstop for
creativity.

## Decision

We will require the test command to run in CI with its exit code as the job's
verdict and no failure suppression anywhere in the chain, recorded as control
TST-001 at `rung: blocking` with `variance: forbidden`.

Variance is forbidden because there is no narrowing direction for "failures
fail the build" — any local deviation is precisely the defect.

## Consequences

**Positive outcomes:**

- A red suite cannot coexist with a green pipeline.
- Incident-time suppression becomes a change the checker rejects the day
  after, not a permanent quiet legacy.

**Trade-offs and risks:**

- Flaky tests become build-blocking, forcing fixes or deletion — deliberate,
  since a tolerated flake is an absorbed failure.
- The control asserts that tests run and block, not that they are good; test
  quality remains a human concern.

## Related ADRs

- [ADR 0008: Protect the Default Branch by Ruleset](0008-protected-default-branch.md)
  — makes this control's verdict unbypassable at the merge.
- [ADR 0009: Lint From One Pinned Definition at Every Locus](0009-single-lint-definition.md)
  — shares the no-suppression assertion.
- [ADR 0010: Enforce Strict Static Typing From Birth](0010-strict-typing-from-birth.md)
  — TYP-001; the same terminal-exit-code discipline for the type checker.
- [ADR 0016: Give "Could Not Verify" Its Own Exit Code](0016-exit-codes-for-unverifiable-controls.md)
  — the same principle applied to the checker's own exit status.

## References

- [NIST SP 800-218 (SSDF)](https://csrc.nist.gov/pubs/sp/800/218/final)
- [The Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)
