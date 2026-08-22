# ADR 0021: How Remote Verification Authenticates, and What It Refuses to Guess

**Status:** Accepted
**Date:** 2026-08-22

Phase 3's first slice makes `kind: remote` a verdict rather than a placeholder.
Doing that puts three rules into `src/standard_check/` — how the checker reaches
GitHub, which repository it asks about, and what each way of failing to get an
answer means. [ADR 0018](0018-register-checker-boundary.md) says an unreasoned
rule in the checker is the failure, not an exception to it, so this ADR is the
reason.

## Background

Until this slice, every `kind: remote` block returned
`SKIPPED (no credentials)` unconditionally. That was deliberate — stubbing the
part that must not be stubbed would have been worse — but it meant the two
controls the checker could not verify were exactly the two this repository would
have failed, which [ADR 0014](0014-satisfying-remote-locus-controls.md) named as
an audit gap rather than a protection gap.

Closing it needs answers to three questions no existing decision covers.

**What talks to GitHub.** The register cannot hold this: how a checker makes an
HTTPS request is not something a reasonable Equal Experts repository could need
to differ on, which is ADR 0018's own test for where a rule belongs.

**Which repository it asks about.** Also checker-shaped, but for a different
reason: git already records it. A repository that had to declare its own
`owner/name` in configuration would be carrying a second copy of a fact the
origin remote already holds — theme **T-2**, in a file whose whole purpose is to
prevent it — and the copy would go stale the day the repository moved.

**What a non-answer means.** This is the one that decides verdicts, and it is
the reason this ADR is more than a paragraph. A file assert that cannot read a
file has still learned something about the repository. A remote assert that
cannot read the platform has learned *nothing* about it, and the register's
whole argument is that a check which cannot answer must say so rather than pick
a side ([ADR 0016](0016-exit-codes-for-unverifiable-controls.md)).

## Alternatives Considered

### Transport: shell out to `gh`

`gh` is already this repository's documented way of reaching GitHub, and it owns
authentication, pagination and error text.

**Pros:** No credential handling in the checker at all, and consistency with
what a developer here already runs.
**Cons:** It makes a binary a dependency of Tier-1 verification. An adopter's CI
job can hand the checker a token in one line and may well not have `gh`, so a
control that *could* have been answered would report `UNCLASSIFIED` for want of
a tool — which is the checker declining to answer a question it had everything
it needed to answer. It also puts `gh`'s auth precedence between the operator
and the result, so "which token did that use" stops being readable from the
environment.

### Transport: add `httpx` or `requests`

**Pros:** Better timeout and retry semantics than the standard library, and
tidier call sites.
**Cons:** A runtime dependency every adopting repository inherits, for perhaps
forty lines of `urllib` — and a dependency in the tool that audits dependency
hygiene is a cost worth refusing.

### Identity: require explicit configuration

Name the repository in the register or in a config file.

**Pros:** Nothing inferred, nothing to misparse.
**Cons:** A second copy of what `git remote` already says, and one nobody
updates when a repository is renamed or transferred. It also adds a required
setup step to every adopter for a fact that is already on disk.

### Taxonomy: treat a rejected token as "no credentials"

Collapse "no token" and "401/403" into one skip, which is roughly how the build
plan phrases the criterion.

**Pros:** One state to explain, and both already deny a `0` exit.
**Cons:** They call for opposite acts. "No credentials" tells an operator to
supply a token; a 401 means the token they supplied is wrong, and a 403 means it
lacks the scope. An operator who reads "no credentials" against a configured
pipeline will go looking for the configuration they already did.

## Decision

**Transport is the standard library against a bearer token.**
`urllib.request` with `Authorization: Bearer`, reading `GITHUB_TOKEN` then
`GH_TOKEN` — the name a workflow conventionally exports and the name `gh` uses,
so an adopter authenticated either way needs no extra step. Note that GitHub
Actions does **not** place `GITHUB_TOKEN` in a step's environment: it is
available as `${{ github.token }}` and a workflow must pass it, which is a step
this repository's own `Standard` workflow now takes. The token is sent as a
header and never in a URL, which proxies and logs retain. A 15-second timeout
bounds it, because a remote block that hangs stalls an audit that has verdicts
for everything else.

**Identity comes from the origin remote, and `--github-repo owner/name`
overrides it.** Inference is the default because git holds the fact; the
override exists for the cases inference cannot serve — a fork, a mirror, and a
checkout being audited on behalf of another repository, which Phase 4's consumer
repo will need. An override that is not a well-formed `owner/name` is refused
rather than sent.

**Four outcomes, and only two of them are about the repository.**

| What happened | Verdict | What it tells the operator |
| --- | --- | --- |
| No token in the environment | `SKIPPED (no credentials)` | Supply one |
| A token, and no repository to ask about | `UNCLASSIFIED` | Name one with `--github-repo` |
| 401, 403, 404, timeout, unparseable body | `UNCLASSIFIED` | Fix the token, its scope, or the network |
| An answer that does not settle the control | `UNCLASSIFIED` | Nothing yet — the token cannot see the setting |
| An answer | `PASS` / `FAIL` | The control holds, or it does not |

The last two rows are the ones worth stating. GitHub omits
`security_and_analysis` from the response given to a caller without
administration access, so a token that cannot *see* push protection would
otherwise report it **off** on a repository where it is **on** — a violation
manufactured entirely by not having looked. The asserts raise rather than return
`False` for that case, and for every transport failure.

The mirror of that rule matters as much: an effective-rules response of `[]` is
an **answer**. The platform said the branch has no rules in force, and reporting
that as unverified would be the same substitution in the other direction.

Both refusals deny the run a `0` exit (ADR 0016), so neither can be read as a
pass. They are distinguished for the person reading the report, not for the exit
code.

## Consequences

**Positive outcomes:**

- CI-001 and SEC-001 are verified rather than permanently skipped, closing the
  audit gap ADR 0014 recorded when it made this repository public.
- The checker has no new runtime dependency and needs no binary on `PATH`, so a
  CI job with a token can answer a remote control.
- A report now distinguishes "nobody asked", "we asked and could not see", and
  "we asked and the answer is no" — three states an operator resolves
  differently.
- `rulesets.py` gives the recorded artefact and the platform response **one**
  reading of what the register requires, so the file block and the remote block
  cannot come to disagree about what "protected" means.

**Trade-offs and risks:**

- The checker now owns HTTP error handling it did not before. It is bounded to
  one module and one method, and every failure collapses to `Unreadable`.
- A token's *scope* decides which remote controls can answer. The Actions
  `GITHUB_TOKEN` can read branch rules on a public repository but not
  `security_and_analysis`, which needs repository administration read — so
  SEC-001's remote block reports `UNCLASSIFIED` in CI while passing under an
  admin-scoped token locally. This is the gate on Phase 3's
  `--require-complete` flip: flipping it first would turn every CI run red for
  a control that holds. Recorded here rather than discovered there.
- `UNCLASSIFIED` is now reachable for reasons outside the repository — a network
  failure makes an audit incomplete. That is correct, and it is why exit `3`
  exists, but it means a flaky network yields a non-zero exit rather than a
  silent pass.

## Related ADRs

- [ADR 0014: Make Remote-Locus Controls Satisfiable on This Repository](0014-satisfying-remote-locus-controls.md)
  — recorded the audit gap this closes.
- [ADR 0016: Exit Codes for Unverifiable Controls](0016-exit-codes-for-unverifiable-controls.md)
  — the vocabulary this taxonomy is spelled in.
- [ADR 0018: The Register–Checker Boundary](0018-register-checker-boundary.md)
  — the rule that requires this ADR to exist.
- [ADR 0008: Protect the Default Branch by Ruleset](0008-protected-default-branch.md)
  — the control the ruleset assert verifies.
- [ADR 0001: Block Secrets Before They Reach the Remote](0001-secrets-never-reach-the-remote.md)
  — the control the push-protection assert verifies.
- [ADR 0022: What Must Be True Before CI Carries a Platform Token](0022-a-platform-token-ci-carries.md)
  — takes up the token-scope trade-off recorded in § Consequences above.

## References

- [Get a repository](https://docs.github.com/en/rest/repos/repos#get-a-repository)
- [Get rules for a branch](https://docs.github.com/en/rest/repos/rules#get-rules-for-a-branch)
- [Authenticating to the REST API](https://docs.github.com/en/rest/authentication/authenticating-to-the-rest-api)
- [Automatic token authentication in GitHub Actions](https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication)
