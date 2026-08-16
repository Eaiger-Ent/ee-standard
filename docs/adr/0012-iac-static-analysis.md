# ADR 0012: Statically Analyse Infrastructure Code Before Apply

**Status:** Accepted
**Date:** 2026-08-16

Rationale for control **IAC-001** in `controls.yaml`.

## Background

Infrastructure code turns a merge into cloud state. A misconfiguration that
would be a code review nit in an application — an open security group, an
unencrypted bucket, a wildcard IAM binding — is a live exposure the moment it
is applied, and applying is exactly what the pipeline exists to do. The last
cheap moment to catch it is static analysis before the plan is ever applied.

The tools are complementary rather than interchangeable: checkov evaluates
policy (is this configuration insecure?), tflint evaluates correctness (is
this provider usage wrong?). CIS benchmark expectations for cloud platforms
are encoded in the former. The `terraform` predicate scopes the control — a
repo with no `*.tf` skips it rather than failing it, which is what keeps a
Tier-1 placement honest for non-infrastructure repos.

## Alternatives Considered

### Option 1: Review and plan inspection only

Rely on human review of Terraform diffs and `terraform plan` output.

**Pros:** No tooling; plans show real effects.
**Cons:** Plan output is long precisely when it matters; misconfiguration
classes are checklist knowledge humans hold inconsistently; review pressure is
highest when infrastructure changes are urgent (theme T-4).

### Option 2: checkov and tflint in CI, exit codes blocking

Run both tools over all Terraform/OpenTofu in CI and at pre-commit, with their
exit codes blocking the merge.

**Pros:** Encoded policy applies uniformly and under deadline; findings arrive
before apply, at diff time; both tools are pinned, offline, and cheap.
**Cons:** Policy checks produce genuine false positives in legitimate designs,
so `justified` variance is required for recorded, expiring exceptions.

## Decision

We will run checkov and tflint over all infrastructure code in CI with
blocking exit codes, recorded as control IAC-001 at `rung: blocking` with
`variance: justified`.

`justified` rather than `forbidden` because policy tools are opinionated about
designs that are sometimes deliberate; the variance mechanism keeps each
exception owned, reasoned, and expiring instead of silent.

## Consequences

**Positive outcomes:**

- Misconfiguration classes are caught at diff time, before they are cloud
  state.
- Exceptions are visible baseline entries under the may-only-shrink rule.

**Trade-offs and risks:**

- Two tools mean two rule sets to keep pinned and current; ADR 0004's update
  proposals cover both.
- Static analysis cannot see cross-stack effects; plan review remains a human
  concern for architecture-level risk.

## Related ADRs

- [ADR 0009: Lint From One Pinned Definition at Every Locus](0009-single-lint-definition.md)
  — the same one-definition discipline for the analysis configs.
- [ADR 0004: Automate Dependency Update Proposals](0004-automated-dependency-proposals.md)
  — keeps both tools' pins current.

## References

- [Checkov](https://www.checkov.io/1.Welcome/What%20is%20Checkov.html)
- [tflint](https://github.com/terraform-linters/tflint)
- [CIS Google Cloud Platform Benchmark](https://www.cisecurity.org/benchmark/google_cloud_computing_platform)
