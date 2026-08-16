# ADR 0001: Block Secrets Before They Reach the Remote

**Status:** Accepted
**Date:** 2026-08-16

Rationale for control **SEC-001** in `controls.yaml`. The register entry is the
control; this record explains why it exists and why it sits where it does.

## Background

A credential that reaches the remote is compromised, whatever happens next.
History rewrites are unreliable, forks and clones retain the commit, and
platform caches outlive the rewrite — so the only defensible boundary is
*before* the push, with the platform as a second net behind it.

The predecessor retrospective identified the credential boundary as the least
defended one (theme T-5): secret hygiene was policy rather than mechanism, and
nothing in the path from editor to remote would actually refuse a secret. A
stated standard that nothing enforces is theme T-1; this control exists to close
both at the most consequential point.

## Alternatives Considered

### Option 1: Detection after push (scheduled or CI-only scanning)

Run a secret scanner in CI or on a schedule and alert on findings.

**Pros:** No local tooling; nothing for contributors to install.
**Cons:** Every finding is already an incident — the secret has reached the
remote and must be rotated. Alerts arrive after the damage, and alert fatigue
absorbs them (theme T-4).

### Option 2: Layered prevention — local hook, CI job, and platform push protection

Run gitleaks as a pre-commit hook and a CI job, and enable GitHub secret
scanning push protection on the repository.

**Pros:** The cheapest catch is the earliest one; three independent layers mean
a bypassed hook is still caught by CI and the platform; push protection covers
pushes that never ran the hook at all.
**Cons:** Requires the hook to be installed locally and the remote setting to be
verified — platform state no file records, which needs a `remote` verification.

## Decision

We will prevent secrets from reaching the remote with three layers — a gitleaks
pre-commit hook, a gitleaks CI job, and GitHub push protection — and verify all
three, recorded as control SEC-001 at `rung: blocking` with
`variance: forbidden`.

Prevention was chosen over detection because a detected secret is a rotation
incident, not a save. Variance is forbidden because there is no legitimate
narrowing or loosening of "no secrets in commits".

## Consequences

**Positive outcomes:**

- A leaked credential is stopped at the developer's machine in the common case,
  and at the platform boundary in the worst case.
- The remote half is read back from platform state, so silently disabled push
  protection is a verification failure, not a memory.

**Trade-offs and risks:**

- Scanner false positives can block a legitimate commit; the answer is rule
  tuning in the shared config, never a skipped hook.
- The `remote` verification needs credentials, so local runs report it as
  `SKIPPED (no credentials)` — which is deliberately never counted as a pass.

## Related ADRs

- [ADR 0008: Protect the Default Branch by Ruleset](0008-protected-default-branch.md)
  — the other control whose enforcement lives in platform state, not files.

## References

- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [GitHub push protection](https://docs.github.com/en/code-security/secret-scanning/introduction/about-push-protection)
- [EE Supply Chain Security Handbook](https://github.com/EqualExperts/ee-supply-chain-security-handbook)
