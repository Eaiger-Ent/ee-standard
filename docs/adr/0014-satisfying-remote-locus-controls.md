# ADR 0014: Make Remote-Locus Controls Satisfiable on This Repository

**Status:** Accepted
**Date:** 2026-08-17

Ratified decision from
[`04-build-plan.md`](../04-build-plan.md) § Phase 1.5 § Decisions required.

**Implemented 2026-08-17.** The repository is public
(`"visibility": "public"`), and the capability this decision existed to unlock is
confirmed live: `GET /rulesets` changed from `403 Upgrade to GitHub Pro or make
this repository public` to an empty list. The precondition was discharged first —
`gitleaks detect` found no leaks across the full history and
`.devcontainer/.env` has never been committed.

Two follow-on acts remain, and neither is this decision: the default-branch
ruleset must be created, and secret scanning push protection enabled. Both are
blocked on tooling rather than on judgement — the container's fine-grained PAT
lacks `Administration: write`, so both API calls return `403 Resource not
accessible by personal access token`. Until the ruleset exists,
[ADR 0015](0015-interim-branch-discipline.md) remains in force.

## Background

Two Tier-1 controls verify platform state rather than files. CI-001 asserts a
ruleset on the default branch requiring a pull request, a passing status check
and no force-push. SEC-001's third verification block asserts that secret
scanning push protection is enabled.

Neither can pass on this repository as it stands. Checked against
`Eaiger-Ent/ee-standard` on 2026-08-17: `GET /repos/.../rulesets` returns `403`
with the message *"Upgrade to GitHub Pro or make this repository public to
enable this feature"*; `security_and_analysis` is `null`; and
`GET /repos/.../branches/main` reports `"protected": false`. The repository is
private, owned by an organisation.

This is not a gap in the checker. It is a gap between the register's Tier-1
definition and the platform this repository actually runs on.
[`00-concepts.md`](../00-concepts.md) § Tiering defines Tier 1 as birth
conditions and states that *"a control that cannot be met at birth does not
belong in Tier 1"* — so the register currently defines a birth condition its own
defining repository cannot meet, which is theme **T-1** at the level of tiering
rather than of enforcement. It also makes Phase 1's "real gate" weaker than it
reads: the repo passes every control the checker can verify locally precisely
because the two it cannot verify are the two it would fail.

The exact plan-and-add-on matrix must be confirmed against GitHub's current
documentation before this ADR is ratified; the 403 message names the two
routes it accepts, and that message is the evidence relied on here.

## Alternatives Considered

### Option 1: Make the repository public

`ee-standard` is a control register, design documents and a conformance
checker. It holds no secrets: `.devcontainer/.env` is gitignored and has never
been committed, and `gitleaks detect` over the full history reports no leaks.

**Pros:** Rulesets and secret scanning push protection both become available,
so CI-001 and SEC-001 are satisfiable at no additional cost. It also resolves
two commitments the plan has already made elsewhere — Phase 4's exit criterion
that *"the devcontainer template is obtainable without access to a private
repo"*, and Phase 6's requirement that the plugin be installable from the
marketplace. Both point the same way.
**Cons:** Irreversible in practice, since anything published may be copied. It
needs a deliberate disclosure decision by the owning organisation, and a review
of the history for anything embarrassing rather than merely secret. Any
organisation policy on public repositories governs.

### Option 2: Upgrade the organisation's GitHub plan

Keep the repository private and buy the capability.

**Pros:** No disclosure decision; the register stays internal.
**Cons:** Recurring cost, and it may not be sufficient — the 403 covers
rulesets, but push protection on private repositories is a separate paid
capability, so this route needs both parts confirmed before it can be relied
on. It also leaves Phase 4's access-shaped single point of failure open.

### Option 3: Re-tier CI-001 to Tier 2

Accept that the control cannot be a birth condition here, move it to Tier 2
with an advisory window, and record the demotion.

**Pros:** Makes the register honest immediately, at no cost, and Tier 2 permits
a baseline.
**Cons:** CI-001 is the control that makes every *other* blocking control
unbypassable. Demoting it weakens the ratchet at its hinge, and the demotion
would be driven by one repository's billing plan rather than by anything about
the control. It is the last resort, not the cheap fix.

## Decision

We will make `ee-standard` a public repository, and keep CI-001 and SEC-001 at
Tier 1.

This option is chosen because it satisfies both controls without recurring cost
and simultaneously discharges two commitments the build plan has already
made — Phase 4's obtainable-template criterion and Phase 6's marketplace
installability. Option 2 solves less for more, and Option 3 weakens the control
that holds the rest of the ladder up, on grounds unrelated to the control's
merit.

Ratified on 2026-08-17. If the disclosure is later refused at organisation
level, this ADR is superseded by an Option 2 route rather than quietly
abandoned — the fallback is recorded, not assumed.

## Consequences

**Positive outcomes:**

- CI-001 and SEC-001 become verifiable rather than permanently skipped, so
  Phase 3 can close on evidence instead of on an exemption.
- Tier 1 keeps its meaning: every birth condition is one this repository meets.
- The devcontainer template and the plugin become obtainable without private
  access, closing a dependency Phase 4 already identified as a single point of
  failure.

**Trade-offs and risks:**

- Publication cannot be undone; the history review is a precondition, not a
  formality.
- The organisation may refuse, in which case this ADR is superseded by the
  Option 2 or Option 3 route and the fallback must be recorded, not assumed.
- Public issues and forks bring maintenance obligations this repository has not
  planned for.

## Related ADRs

- [ADR 0008: Protect the Default Branch by Ruleset](0008-protected-default-branch.md)
  — the control this decision unblocks.
- [ADR 0001: Block Secrets Before They Reach the Remote](0001-secrets-never-reach-the-remote.md)
  — its push-protection half depends on the same capability.
- [ADR 0015: Work on Branches While the Default Branch Is Unprotected](0015-interim-branch-discipline.md)
  — the interim posture until this decision lands.

## References

- [GitHub rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
- [About push protection](https://docs.github.com/en/code-security/secret-scanning/introduction/about-push-protection)
- [Setting repository visibility](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/setting-repository-visibility)
- [OpenSSF Baseline](https://baseline.openssf.org/)
