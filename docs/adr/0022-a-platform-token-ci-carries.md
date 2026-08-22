# ADR 0022: What Must Be True Before CI Carries a Platform Token

**Status:** Proposed
**Date:** 2026-08-22

Phase 3's first slice made `kind: remote` real and immediately produced a
question it cannot answer for itself. SEC-001's remote block reports
`UNCLASSIFIED` in CI because the Actions `GITHUB_TOKEN` cannot read
`security_and_analysis` — that needs repository administration read. Until it
can, `--require-complete` cannot be turned on, and
[ADR 0016](0016-exit-codes-for-unverifiable-controls.md) § Ratified tolerance
stays in force past the phase that was supposed to end it.

The obvious fix is to give the workflow a stronger token. This ADR records what
the register would have to gain **first**, because the obvious fix introduces
precisely the class of thing
[ADR 0002](0002-federated-ci-identity.md) exists to forbid, into the CI of the
repository that defines the standard.

## Background

### What is actually missing

One header on one endpoint. `GET /repos/{owner}/{repo}` returns
`security_and_analysis` only to a caller with repository administration access;
for anyone else the object is **absent**, not `disabled`. SEC-001's assert
refuses to read that absence as "push protection is off"
([ADR 0021](0021-how-remote-verification-authenticates.md)), so the honest
verdict is `UNCLASSIFIED` and the run cannot exit `0`.

Nothing else in the register needs a stronger token. CI-001's remote block
passes on the Actions token today, verified on the run that merged
[#42](https://github.com/Eaiger-Ent/ee-standard/pull/42).

### Why "just add a PAT secret" is not a small change

**SEC-002 cannot see it.** The control is *CI authenticates without a long-lived
cloud credential*, and `no-static-cloud-keys` scans workflows for the seven
names in `cloud_credentials:` — all cloud provider keys. A secret called
`GH_ADMIN_TOKEN` matches none of them, so SEC-002 would report `PASS` over a
workflow carrying a long-lived, administratively-scoped credential.

That is theme **T-3** — declared but unreachable — arriving in the control whose
entire purpose is to prevent a standing credential in CI. The register would be
green about the exact thing it had just stopped being true.

**A `pull_request` run hands secrets to the code in the pull request.** GitHub
withholds secrets only from workflows triggered by a **forked** repository; a
pull request from a branch in this repository receives them. The `Standard`
workflow runs on `pull_request`. Log masking is not a mitigation — a base64
round-trip defeats it — so any secret available to that job is readable by
whatever the pull request's branch tells it to run.

The blast radius here is bounded but must be stated rather than assumed. This
repository has five admin collaborators and five with read. Read-only
collaborators cannot push a branch, so they would have to fork, and forks get no
secrets. The exposure is therefore to the five who already hold admin — which
matters enormously for *what kind* of token is acceptable, and is the whole of
the next point.

**The token must grant no more than its readers already have.** A fine-grained
token scoped to this one repository with `Administration: read` gives an admin
nothing they do not already possess, so its exposure to admins is a non-event. A
**classic** PAT carries its owner's access to *every* repository they can
reach — so exfiltrating it from a pull request would grant access to
repositories the reader has no rights to. That is a genuine privilege
escalation, and it is the difference between an acceptable instrument and an
unacceptable one.

**A PAT belongs to a person.** When they leave, CI breaks or the credential
orphans. ADR 0002 rejected static cloud keys partly on theme **T-1** — rotation
is a policy that decays — and a token whose renewal depends on one individual
remembering decays the same way.

## Alternatives Considered

### Option 1: A fine-grained PAT, and the controls to govern it

Add a repository secret holding a fine-grained token scoped to this repository
with `Administration: read` only, and add the controls below so the register can
see and hold it.

**Pros:** Closes the one gap. Cheap to create. The exposure to same-repo pull
requests is a non-event *provided* the token is fine-grained and single-repo,
because its readers are already admins.
**Cons:** Requires three new register facts and at least one new control before
it is safe to add — see § What the register must gain. It is still a standing
credential, still owned by a person, and the correctness of "fine-grained and
single-repo" is only partly machine-checkable.

### Option 2: A GitHub App installation token

Register an org-owned App with `Administration: read` on this repository, and
mint a one-hour installation token per run with
[`actions/create-github-app-token`](https://github.com/actions/create-github-app-token).

**Pros:** The credential CI *uses* is short-lived and job-scoped, which is
ADR 0002's own argument applied to the platform instead of the cloud. Ownership
is the organisation, not a person, so it survives someone leaving. Permissions
are declared on the App and reviewable.
**Cons:** The App's **private key** is still a long-lived repository secret with
the same `pull_request` exposure — the durable credential moves rather than
disappearing, and a leaked private key is worse than a leaked read-only PAT
because it mints tokens. Setup is org-level and needs someone with organisation
admin. Most of the controls in § What the register must gain are still required,
now pointed at the private key.

### Option 3: Put the credential behind a gate a pull request cannot edit

Keep `${{ github.token }}` in the `pull_request` run, and give the
administration-scoped credential to a separate job that a pull request cannot
cause to run with that credential attached.

**The first draft of this option was wrong, and the correction is the whole
point.** It originally said: trigger the job on `push: branches: [main]` or
`schedule`, since a pull request cannot alter what runs on `main`. The second
half is true and the first does not follow — **the trigger list lives in the
workflow file, and for a `pull_request` event GitHub runs the file from the pull
request's own ref.** A branch could add `pull_request:` to that workflow's `on:`
block, or delete an `if: github.event_name != 'pull_request'` guard, and
self-trigger the job with the secret attached. Any guard written in YAML is a
guard the attacker is editing.

The gate has to be **server-side**, which means a
[deployment environment](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments):
configured in repository settings, not in a file, and therefore outside what a
pull request can touch. The secret is an *environment* secret rather than a
repository secret, and the environment carries either or both of:

- a **deployment branch policy** naming `main`. A `pull_request` run's ref is
  `refs/pull/N/merge`, which is not a branch and matches no branch pattern, so
  the job cannot reach the secret; and
- **required reviewers** — *"A workflow job cannot access environment secrets
  until approval is granted by required approvers."*

Both are available on public repositories at every current plan tier, which this
repository is ([ADR 0014](0014-satisfying-remote-locus-controls.md)).

```yaml
jobs:
  platform-state:
    environment: platform-state      # the load-bearing line, not the `on:` block
    steps:
      - name: Push protection
        env:
          GITHUB_TOKEN: ${{ secrets.PLATFORM_READ_TOKEN }}
        run: uv run standard-check --require-complete run --control SEC-001
```

A pull request that copies this job into its own branch is refused by the
environment gate whatever its YAML says.

**Pros:** The exfiltration path is removed by platform configuration rather than
bounded by convention, and the mechanism is not in the repository a pull request
can rewrite. It is also the honest shape: whether push protection is on is a
property of the *repository*, not of a proposed change, so asking it per pull
request was always slightly the wrong question.
**Cons:** It does not let the `pull_request` run exit `0`, so it does not by
itself unblock `--require-complete` there. It splits conformance across two
workflows, and a scheduled check that fails is noticed later than one that blocks
a merge. It also adds platform state that nothing in the register verifies —
an environment whose branch policy is later widened would silently undo this,
which is requirement 5 below.

**Two limits, stated rather than implied.** This makes exfiltration *recorded*
rather than impossible: anything merged to `main` runs with the credential, so
the attacker must land a permanent, attributable commit instead of opening and
closing a pull request silently. And that gain is weaker here than it sounds,
because this repository's ruleset sets `required_approving_review_count: 0` — a
pull request merges on passing checks with **no human review**, so "it reached
`main`" currently means "CI went green", not "somebody looked". Required
reviewers on the environment compensate for exactly that, which is why they are
listed above rather than treated as optional.

### Option 4: Record that the block is not answerable from CI, and flip anyway

Declare SEC-001's remote block `partial` for the CI locus, with an expiry, and
pass `--require-complete`.

**Pros:** No credential anywhere. Uses machinery the register already has
([ADR 0017](0017-partial-verification-is-reported.md)).
**Cons:** A `partial` block denies the run a `0` exit by design, so this does not
work as stated — the flip would still fail. Making it work would mean weakening
what `partial` does, which is a change to the verdict vocabulary for the
convenience of one control. Refused on that basis rather than on effort.

## Decision

**Not yet taken.** This ADR is `Proposed`, and it exists to stop the token being
added before the controls that govern it.

What *is* settled is the precondition: **no platform token may be introduced
into CI until the register can see it.** Adding the secret first and the
controls afterwards would mean a period in which SEC-002 reports `PASS` over a
standing administrative credential — and this repository's own review record
([`09-phase-1.5-review.md`](../09-phase-1.5-review.md) § H) is a list of what
happens when a control is credited for something it never read.

The recommendation, to be ratified or rejected: **Option 3 for the credential's
location, and Option 2 for its kind, if a credential is introduced at all.**
Option 3 moves the exfiltration path behind platform configuration a pull request
cannot edit, and Option 2's short-lived token is ADR 0002's own reasoning applied
consistently. Option 1 is acceptable only with every requirement in the next
section in place, and Option 4 is refused because it would weaken `partial` to
suit one control.

**One empirical check is owed before Option 3 is relied on.** The branch-policy
behaviour above follows from documented semantics and has *not* been tested on
this repository. This repository's own record is a list of what happens when a
mechanism is credited without being observed
([`09-phase-1.5-review.md`](../09-phase-1.5-review.md) § H), so it should be
tested the cheap way — an environment holding a non-secret dummy value, and one
throwaway pull request that tries to read it — before any real credential
depends on it.

## What the register must gain

These are the requirement, stated so it can be reviewed before anything is
built. Each is a register fact or a control, not a rule in the checker
([ADR 0018](0018-register-checker-boundary.md)).

### 1. A control that can see a platform token at all

SEC-002 stays cloud-scoped: its title, its `enforces`, its NIST PW.9 citation
and ADR 0002 are all about cloud identity, and broadening it would make one
control mean two things. A platform token needs its own entry.

Proposed **SEC-003 — *CI carries no long-lived platform token except one the
register names***, at `rung: blocking`, `variance: forbidden`, `baseline: null`,
`locus: [ci]`. A file assert reads every workflow for a secret reference and
fails any that is not in a register-held allow-list. The allow-list is the point:
this repository intends to carry exactly one, and an enumerated exception is the
"explicit, recorded exception rather than a quiet one" that ADR 0002 § Trade-offs
calls the intended friction.

### 2. A register fact naming what may be carried, and where

`platform_credentials:`, beside `cloud_credentials:`, holding for each permitted
secret its name, the workflow triggers it may appear under, and the maximum
lifetime it may have. Which secrets a repository carries is a fact about that
repository, so it belongs in the register (ADR 0018), and holding the permitted
**triggers** there is what makes Option 3 checkable rather than a convention.

### 3. Expiry must be verified, not promised

A `kind: remote` assert `platform_token_expires_within`, reading the
`github-authentication-token-expiration` response header — confirmed present on
a live call while writing this ADR — against a maximum from the register. Without
it, "we will use a short-expiry token" is exactly the decaying policy ADR 0002
rejected Option 1 for. A token with no expiry, or one beyond the register's
maximum, fails.

### 4. A classic token must be refused

Classic PATs return `X-OAuth-Scopes` on API responses; fine-grained tokens do
not. The header's **presence** therefore identifies the instrument, and the same
remote assert can fail a classic token outright. This is the check that
distinguishes "grants its readers nothing new" from "grants its readers access
to every repository its owner can reach", and it is the one that makes the
`pull_request` exposure tolerable rather than merely bounded.

Note the limit honestly: this identifies the *kind* of token, not its scope. No
API lets a fine-grained token enumerate its own permissions, so "scoped to this
repository, `Administration: read` only" stays a human act recorded at issue
time. It must be written down as such rather than implied to be checked.

### 5. The environment gate is itself unverified platform state

Option 3 depends on a deployment branch policy and, ideally, required reviewers.
Both are platform state, and nothing in the register reads them — so an
environment whose branch policy was later widened to "all branches" would
silently return the credential to every pull request, with every control still
green.

That is the same shape as the audit gap
[ADR 0014](0014-satisfying-remote-locus-controls.md) recorded and Phase 3 closed:
a protection that holds in fact and is proven by nothing. If Option 3 is taken,
its environment configuration needs a `kind: remote` block of its own reading
`GET /repos/{owner}/{repo}/environments/{name}` — otherwise the mechanism
protecting the credential is the one thing in this design nobody checks.

### 6. The adopter-facing consequence

Whatever is decided, [`08-adopting.md`](08-adopting.md) owes it a section under
the standing requirement in [`04-build-plan.md`](04-build-plan.md): an adopter
whose CI reports SEC-001 `UNCLASSIFIED` will reach for a PAT, and the guide
currently gives them no steer at all. That is a gap this ADR opens and Phase 3
must close before its adopter criterion can be ticked.

## Consequences

**Positive outcomes:**

- The `--require-complete` flip stops being blocked on an unexamined judgement
  call and becomes a decision with a written basis.
- SEC-002's blind spot is recorded whether or not a token is ever introduced.
  A repository could add a platform token tomorrow for an unrelated reason and
  the register would not see it; that is now known rather than latent.
- If Option 3 is taken, the credential never reaches pull-request-authored code,
  which is a stronger property than any of the controls above can verify.

**Trade-offs and risks:**

- Six requirements to close one `UNCLASSIFIED`. That is a poor ratio, and it is
  a legitimate reason to accept the tolerance for longer rather than to build all
  of it. Note that Option 3 does not escape the ratio — it removes the
  exfiltration path but adds requirement 5, because the gate protecting the
  credential would otherwise be the one thing nobody checks.
- Requirement 4 checks the token's kind, not its scope. Over-reading it as
  "the register verifies the token is minimal" would be the substitution this
  repository keeps catching.
- Leaving ADR 0016's tolerance in place while this is decided is itself a cost.
  It was written to end at Phase 3, and it is now ending later for a reason
  rather than by drift — but only this ADR records that reason.

## Related ADRs

- [ADR 0002: Federate CI Cloud Identity via OIDC](0002-federated-ci-identity.md)
  — the control this decision would sit beside, and whose argument applies to
  platform tokens as much as to cloud keys.
- [ADR 0021: How Remote Verification Authenticates](0021-how-remote-verification-authenticates.md)
  — recorded the token-scope trade-off this ADR exists to resolve.
- [ADR 0016: Give "Could Not Verify" Its Own Exit Code](0016-exit-codes-for-unverifiable-controls.md)
  — the tolerance that stays in force until this is settled.
- [ADR 0017: Report a Partially Implemented Control as Partial](0017-partial-verification-is-reported.md)
  — the machinery Option 4 would have to weaken.
- [ADR 0001: Block Secrets Before They Reach the Remote](0001-secrets-never-reach-the-remote.md)
  — the control whose remote half is the thing that cannot be verified.

## References

- [Managing your personal access tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- [Using secrets in GitHub Actions](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets)
- [Generating an installation access token for a GitHub App](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-an-installation-access-token-for-a-github-app)
- [`actions/create-github-app-token`](https://github.com/actions/create-github-app-token)
- [Managing environments for deployment](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)
- [REST API endpoints for deployment environments](https://docs.github.com/en/rest/deployments/environments)
- [NIST SP 800-218 (SSDF)](https://csrc.nist.gov/pubs/sp/800/218/final)
