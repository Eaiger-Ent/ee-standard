# ADR 0007: Pin Devcontainer Image and Features

**Status:** Accepted
**Date:** 2026-08-16

Rationale for control **DEV-001** in `controls.yaml`.

## Background

The devcontainer is the environment every other gate runs inside. If it is not
reproducible, no result obtained in it quite is: two engineers building a month
apart from the same commit get different toolchains, and neither can tell.

The Dev Container specification pins features through
`devcontainer-lock.json`, but the lock file has no concept of the base image —
so the largest single input to the environment is the one a feature lock leaves
floating. That partial state is the dangerous one: the lock file's existence
makes the environment look solved while its foundation drifts. Both halves must
therefore be verified together — every feature resolved to a digest in the lock
file, and the `image` reference itself carrying an `@sha256:` digest.

## Alternatives Considered

### Option 1: Lock features only, track the image by tag

Commit `devcontainer-lock.json` and reference the image as `name:tag`.

**Pros:** Covered end to end by first-party CLI tooling; tags stay readable.
**Cons:** The image floats, so the environment is unpinned where it matters
most, while appearing pinned (theme T-1 — a stated standard nothing enforces).

### Option 2: Lock features and pin the image by digest

Commit the lock file covering every feature, and pin `image` by `@sha256:`
digest, with digest bumps proposed by the dependency updater (ADR 0004).

**Pros:** Every input to the environment is immutable; a rebuild reproduces the
container; updates arrive as reviewable diffs.
**Cons:** Digests are unreadable without the adjacent tag comment; two places
must be verified instead of one — which is exactly what the control's paired
assertions do.

## Decision

We will pin the devcontainer completely — `devcontainer-lock.json` covering
every feature named in `devcontainer.json`, and the base image referenced by
digest — recorded as control DEV-001 at `rung: blocking` with
`variance: narrowing-only`.

This is the discipline of ADR 0005 applied to the environment: an immutable
reference for everything that executes.

## Consequences

**Positive outcomes:**

- The environment is a function of the commit, not of the build date.
- A lock file quietly missing one feature is a verification failure, not an
  impression of safety.

**Trade-offs and risks:**

- The lock file is CLI-generated, so regenerating it needs the `devcontainer`
  CLI on the host — a documented operator step, not an in-container one.
- Image digest bumps depend on ADR 0004's proposals to avoid fossilising.

## Related ADRs

- [ADR 0005: Pin CI Actions to Commit SHAs](0005-pinned-ci-actions.md) — the
  same immutability rule for workflow dependencies.
- [ADR 0004: Automate Dependency Update Proposals](0004-automated-dependency-proposals.md)
  — proposes the digest bumps that keep pins current.
- [ADR 0006: Run Containers as a Non-Root User](0006-containers-run-unprivileged.md)
  — BLD-001, extended at contract 7 to the same `devcontainer.json` this control
  pins.

## References

- [Dev Container Features specification](https://containers.dev/implementors/features/)
- [Dev Container specification](https://containers.dev/implementors/spec/)
