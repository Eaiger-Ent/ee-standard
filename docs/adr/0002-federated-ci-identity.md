# ADR 0002: Federate CI Cloud Identity via OIDC

**Status:** Accepted
**Date:** 2026-08-16

Rationale for control **SEC-002** in `controls.yaml`.

## Background

A long-lived cloud key stored as a CI secret is a standing liability: it works
for anyone who obtains it, from anywhere, until someone notices and rotates it.
Exfiltration via a compromised action, a leaked log, or an over-scoped fork
workflow turns one stolen string into durable cloud access.

Workload identity federation replaces the stored key with a short-lived token
minted per job from the CI provider's OIDC identity. There is nothing durable to
steal, and access is scoped to the workflow that requested it. NIST SSDF PW.9
frames this as protecting the integrity of the build's credentials; theme T-5
(the credential boundary least defended) is the local history that makes it
Tier 1 here.

## Alternatives Considered

### Option 1: Static cloud keys in CI secrets, with rotation policy

Store provider keys as repository secrets and rotate on a schedule.

**Pros:** Works everywhere; simplest to set up; no trust configuration in the
cloud account.
**Cons:** The key is valid between rotations regardless of who holds it;
rotation is a policy that decays (theme T-1); every secret store and log line
becomes part of the attack surface.

### Option 2: OIDC workload identity federation, static keys forbidden

CI authenticates by exchanging its OIDC token for short-lived cloud credentials;
the register forbids any workflow referencing a static cloud key secret.

**Pros:** No durable credential exists to leak; access is scoped and expiring;
the absence of key references is mechanically checkable in workflow files.
**Cons:** Requires one-time federation setup per cloud account; some third-party
services still demand static keys and need case-by-case handling.

## Decision

We will require CI to obtain cloud access exclusively through OIDC workload
identity federation, and verify that no workflow references a static cloud key
secret, recorded as control SEC-002 at `rung: blocking` with
`variance: forbidden`.

The check is written as a file-shaped assertion over workflows because that is
what a repository can verify without cloud credentials; the federation setup
itself lives in the cloud account.

## Consequences

**Positive outcomes:**

- A compromised workflow or log leak yields at most a token that has already
  expired by the time it is used.
- The verification runs offline, so every locus can enforce it.

**Trade-offs and risks:**

- Detection is by pattern over workflow files, so an unusually named key secret
  can evade it; review remains the backstop.
- Services without OIDC support force an explicit, recorded exception rather
  than a quiet one — which is the intended friction.

## Related ADRs

- [ADR 0001: Block Secrets Before They Reach the Remote](0001-secrets-never-reach-the-remote.md)
  — the same boundary, defended at commit time rather than build time.
- [ADR 0022: What Must Be True Before CI Carries a Platform Token](0022-a-platform-token-ci-carries.md)
  — applies this ADR's argument to platform tokens, and records that SEC-002's
  `cloud_credentials:` list cannot see one.

## References

- [NIST SP 800-218 (SSDF)](https://csrc.nist.gov/pubs/sp/800/218/final)
- [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation)
