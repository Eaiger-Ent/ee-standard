# Build plan

Seven phases, each with exit criteria that can be checked rather than felt.

The ordering principle: **the checker is built before the template.** A template
without a checker produces repos that are conformant on the day they are created
and unmeasured thereafter — which is the predecessor's failure, reproduced
faster. With the checker first, every subsequent phase has an objective test, and
the template can be validated by generating a repo and running the checker
against it.

That principle governs the **shipped template**, which stays in Phase 2. It does
not govern **this repo's own environment**, which comes first — see Phase 0.5.
The two are different artefacts and conflating them is what put the devcontainer
in the wrong phase originally.

## Phase 0 — The register

**Done.** `controls.yaml` exists with 13 Tier-1 controls and 3 meta-controls,
every standard URL verified to resolve.

### Exit criteria — phase 0

- [x] Every control cites an external standard with a resolving URL
- [x] Every control has an owner, a `review_by`, and a variance policy
- [x] Tier-1 controls carry `baseline: null`
- [x] An ADR exists per control in `docs/adr/` — thirteen records,
      `0001`–`0013`, one per `rationale_adr` reference in `controls.yaml`.

## Phase 0.5 — This repo's own devcontainer

**Before any code is written.** All development on this repository happens
inside a container; nothing in Phase 1 is written against a host toolchain.

Operator instructions, including the macOS Keychain values that must be set on
the host first, are in
[`06-devcontainer-setup.md`](06-devcontainer-setup.md).

This is not the shipped template — that is still Phase 2's deliverable, and is
built by generalising this one. What Phase 2 gains is a working reference to
generalise from rather than a specification to implement blind.

Two reasons this cannot wait:

**Phase 1 is development work.** If `standard-check` is written on a host
toolchain, the first thing the standard repo does is violate the premise it
exists to enforce.

**Phase 1's own exit criteria already require it.** The last criterion — "the
checker's own repo passes every control it can verify locally", called "the real
gate" — includes DEV-001. A repo with no `.devcontainer/` cannot pass DEV-001,
so Phase 1 cannot close without one. Deferring the devcontainer to Phase 2 makes
Phase 1 unclosable by its own terms.

### Exit criteria — phase 0.5

- [x] The container builds from a clean clone on a host with only the required
      Keychain value set
- [x] `image` is pinned by `@sha256:` digest, and the digest matches what the
      registry serves
- [x] `devcontainer-lock.json` is committed and pins **every** feature named in
      `devcontainer.json` — a lock file covering three of four features reads as
      solved and is not
- [x] `.devcontainer/.env` is gitignored, and `git log --all -- .devcontainer/.env`
      is empty
- [x] The container's final user is not root, stated explicitly rather than
      inherited from the base image
- [x] `setup.sh` is short enough not to need sectioning — anything longer is
      doing work that belongs in a feature
- [x] DEV-001's `enforces` text in `controls.yaml` covers the image digest as
      well as the lock file, matching what
      [`03-devcontainer.md`](03-devcontainer.md) already claims it verifies

The last one was register debt, not container work: as `controls.yaml`
originally stood, a repo with a complete lock file and a floating image tag
passed DEV-001 — theme **T-1** inside the register itself. Closed at register
`v0.2.0` (contract 2) by widening DEV-001's `enforces` text and adding the
`devcontainer_image_digest_pinned` assertion, so Phase 1 implements the control
against complete text.

## Phase 1 — The checker

Build `standard-check` as an ordinary executable. Python, installed from a
pinned version, no Claude anywhere near it — inside the Phase 0.5 container.

Implement in this order, because each stage is testable against the register that
already exists:

1. Schema validation (`standard-check schema`) — the register validates itself
2. `kind: command` verification — shell out, exit code is the verdict
3. `kind: file` assertions — the closed set named in `controls.yaml`
4. Predicate evaluation — `SKIPPED (predicate)` distinct from `PASS`
5. The three meta-controls
6. Report rendering, ordered by tier then rung

`kind: remote` is deliberately deferred to Phase 3. It needs credentials, network
and a live repository, and building it now would mean stubbing exactly the part
that must not be stubbed.

### Exit criteria — phase 1

- [ ] `standard-check schema` passes against `controls.yaml`
- [ ] Running against this repo produces a report with no `UNCLASSIFIED` verdicts
      arising from checker bugs (as opposed to genuine ambiguity)
- [ ] A deliberately broken register fails schema validation with a message
      naming the field
- [ ] An unknown `assert` name is a schema **error**, not a skipped check
- [ ] `SKIPPED (predicate)` and `SKIPPED (no credentials)` render distinctly and
      neither is counted as a pass in the exit code
- [ ] The checker's own repo passes every control it can verify locally

The last one is the real gate. If the standard repo cannot satisfy its own
Tier-1 controls, they are not birth conditions.

## Phase 2 — The gates and the template

Build the `gate-*` skills and the devcontainer template together, because the
gates are what make the template's output verifiable.

Order within the phase: `gate-secrets` first, as the reference implementation.
It exercises every locus (`pre-commit`, `ci`, and `remote` in Phase 3), so
whatever shape works for it works for the rest. The others follow it.

Alongside them, the `.devcontainer/` **template** per
[`03-devcontainer.md`](03-devcontainer.md) — image digest-pinned,
`devcontainer-lock.json` present, `setup.sh` short.

The template is a generalisation of this repo's own container from Phase 0.5,
not a fresh implementation: strip the ee-standard-specific parts (the Python
version, the volume name, `markdownlint-cli2` as a hard dependency), keep the
structure. Anything the generalisation cannot carry across is a sign the
original was wired to this repo in a way the spec did not intend, and should be
fixed in both.

### Exit criteria — phase 2

- [ ] `gate-secrets` deploys onto a repo with none of its config, and
      `standard-check` then reports SEC-001 PASS for its local loci
- [ ] Every gate writes a provenance stamp its own verify step reads back
- [ ] Gates and checker share one assert implementation — verified by there
      being one copy, not by comparing two
- [ ] The devcontainer template builds, and DEV-001 passes against it
- [ ] Every SKILL.md passes preflight P1–P11
- [ ] `standard-adopt` end-to-end on a scratch repo: plan → confirm → deploy →
      verify → commit, with the verify step genuinely able to fail

That last clause matters. A verify step that has never been observed failing is
not known to work — deliberately break a deployed config and confirm the run
reports it.

## Phase 3 — Remote controls and meta-controls

The locus that gets forgotten, done deliberately.

Implement `kind: remote`: GitHub push protection state, branch ruleset shape,
and the presence of a workflow that can actually fail. Build `gate-repo` to
create the ruleset via the API.

Then GOV-001, which is the highest-value control in the register and cannot be
finished before this phase: proving a `blocking` control is *reachable from a CI
step that can fail* requires reading platform state, not files. A workflow file
that exists but is not a required check is precisely theme **T-3** — declared but
unreachable — and only a remote check catches it.

### Exit criteria — phase 3

- [ ] Remote verification passes against a real repository
- [ ] With no credentials, remote checks report `SKIPPED (no credentials)` and
      the run does **not** exit 0 on that basis alone
- [ ] GOV-001 correctly fails a repo whose lint workflow exists but is not a
      required status check
- [ ] GOV-002 fails when a baseline file grows by one line
- [ ] GOV-003 fails on a control past `review_by`
- [ ] `gate-repo` confirms before every remote mutation, independently of the
      plan-level confirmation

## Phase 4 — The consumer repo

The actual test. A second repository that did not author the standard, set up
end to end by following only the published instructions.

Sequence, per [`03-devcontainer.md`](03-devcontainer.md):

1. Create the repo with the `.devcontainer/` template
2. Run `/project-init` — it configures the devcontainer for the stack
3. Run `/standard-adopt` — it deploys the gates
4. Run `standard-check` — it passes
5. Deliberately weaken something. Confirm the checker catches it, and that
   `standard-variance` classifies the direction correctly.

### Exit criteria — phase 4

- [ ] The consumer repo reaches full Tier-1 conformance
- [ ] No step required knowledge held only by the author
- [ ] `project-init` and `standard-adopt` compose without fighting over
      `devcontainer.json`
- [ ] Weakening a `narrowing-only` control is caught and classified
- [ ] The three known `UNCLASSIFIED` cases report as `UNCLASSIFIED`, not as a
      guess in either direction
- [ ] **The devcontainer template is obtainable without access to a private
      repo.** `ee-skills-incubator` is private and not a GitHub template; if that
      is the only source, the plan has an access-shaped single point of failure.
      Resolve by a public template repo or a `templates/devcontainer/` directory
      in the plugin.

## Phase 5 — Staleness and the sweep

Wire the mechanism that keeps deployments current.

- `deploys.json` sidecars, with contract versions
- The `skill-update` widening (submission 2 in
  [`05-promotion.md`](05-promotion.md))
- A scheduled sweep running `standard-check` across repos, reporting rather than
  fixing

### Exit criteria — phase 5

- [ ] Bumping a gate's version *without* changing its output produces **no**
      redeployment recommendation
- [ ] Bumping its contract version *does*
- [ ] `skill-update` reports an owed deployment where every plugin is current,
      and does not print *Already done* over it
- [ ] The sweep runs unattended and produces a report nobody has to ask for
- [ ] A repo that has never deployed is distinguishable from one deployed and
      current, and from one deployed and stale

The first two criteria are the whole noise argument, expressed as a test. If a
documentation-only release triggers a recommendation, the mechanism will be
ignored within a month and the phase has failed regardless of what else passes.

## Phase 6 — Promotion

Per [`05-promotion.md`](05-promotion.md), in the order given there: the
`CONTRIBUTING.md` corrections first (small, independent, establishes contact),
then `ee-standard` plus the `governance` category, then the `skill-update`
amendment.

### Exit criteria — phase 6

- [ ] All three submissions raised
- [ ] `ee-standard` installable from the marketplace
- [ ] The consumer repo re-adopts from the *marketplace* copy and still passes —
      proving the plugin works when installed, not only when developed

## What is deliberately not in scope

| Excluded | Why |
| --- | --- |
| Tier 2 and Tier 3 controls | Tier 1 must be proven end to end first. Adding controls is cheap once the machinery works and expensive before. |
| Auto-fix | Notify, never redeploy. Proposed fixes are a Phase 5+ conversation, and only ever as a PR. |
| Non-GitHub platforms | `remote` verification is GitHub-shaped. Another platform means another assert set, which is a real project, not a flag. |
| Replacing `lint-md`, `project-init`, `devcontainer-check` | They work. The standard composes with them. |

## Sequencing risk

The plan's dependencies are strict in two places and loose everywhere else:
Phase 0.5 gates Phase 1, Phase 1 gates everything after it, and Phase 4 gates
Phase 6. Phases 2 and 3 can overlap once the checker's assert interface is
settled.

The genuine risk is Phase 4 revealing something Phases 1–3 assumed. That is the
purpose of Phase 4, and discovering it there costs a rework; discovering it after
promotion costs a marketplace amendment and everyone who already installed it.
