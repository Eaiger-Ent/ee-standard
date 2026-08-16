# ADR 0006: Run Containers as a Non-Root User

**Status:** Accepted
**Date:** 2026-08-16

Rationale for control **BLD-001** in `controls.yaml`.

## Background

A container that runs as root hands any code execution inside it root's
capabilities: package installation, file ownership changes across mounted
volumes, and a materially better starting position for a container escape.
Almost no application workload needs any of that at runtime — root is the
default, not a requirement.

CIS Docker Benchmark §4.1 states the rule directly: create and use a non-root
user for the container. The failure mode this control targets is inheritance —
an image that happens to run unprivileged today because of its base, until a
base change silently alters it (theme T-3, declared but unreachable: the
property is believed, not stated).

## Alternatives Considered

### Option 1: Rely on base images and runtime policy

Choose base images that drop privileges, and enforce non-root at the
orchestrator if one exists.

**Pros:** No Dockerfile changes; platform policy covers many images at once.
**Cons:** The property lives outside the repo, so a base image change or a
policy gap flips it silently; nothing in review shows the regression.

### Option 2: Require an explicit non-root USER in every Dockerfile's final stage

Every Dockerfile's final stage declares a `USER` that is neither `root` nor
numeric `0`, checked as a file assertion and reinforced by hadolint at error
threshold.

**Pros:** The property is stated in the reviewed artefact; regression is a
visible diff; verification is offline and cheap at every locus.
**Cons:** Occasional genuine root-at-runtime needs (device access, privileged
init) must restructure to drop privileges — no baseline escape hatch exists.

## Decision

We will require the final stage of every Dockerfile to declare a non-root
user explicitly, recorded as control BLD-001 at `rung: blocking` with
`variance: forbidden`.

Explicit statement was chosen over inheritance because a security property that
is not written down cannot be reviewed, and this register's premise is that
unwritten properties decay.

## Consequences

**Positive outcomes:**

- Code execution inside a conforming container starts unprivileged.
- The `container` predicate scopes the control: a repo with no Dockerfile skips
  it rather than failing it.

**Trade-offs and risks:**

- Workloads assuming root fail at container start when first conformant — an
  intentionally early and diagnosable failure.
- File-permission friction with bind mounts moves to image build time, where it
  belongs.

## Related ADRs

- [ADR 0007: Pin Devcontainer Image and Features](0007-pinned-devcontainer-features.md)
  — the devcontainer states its non-root user explicitly for the same reason.

## References

- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker)
- [hadolint](https://github.com/hadolint/hadolint)
