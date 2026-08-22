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

## A standing requirement: the adopter's steps are written down as they are found

**Every phase carries the same extra exit criterion**: any step an adopting
repository would have to take, that this phase discovered or introduced, is in
[`08-adopting.md`](08-adopting.md), with the evidence that shows it worked.

This is not a documentation preference. Phase 4's criterion — *"no step required
knowledge held only by the author"* — is a test applied at the end, and a test
applied at the end cannot recover knowledge nobody wrote down at the time. This
plan is a ledger of **our** work; an adopter should never have to read it. When
§ G's Renovate work finished, the word "Renovate" appeared twenty-three times in
this file, once in the schema doc, and **nowhere** in the README or any
adopter-facing page. Everything learned in a day of it — that the config must be
on the default branch, that the onboarding pull request must be left alone
rather than closed, that a community feature may fetch without verifying — was
recorded only as our own history.

The test for the criterion is not "is it documented" but **"could someone who
has never seen this repository do it, and know that they had?"** So each step in
`08-adopting.md` carries how you know it worked, because a step performed is not
a step that succeeded. Adopter-facing steps are, in practice, the ones no tool
can take: platform state, app installations, account permissions, and token
scopes.

## How to write a criterion

**A criterion is one checkable sentence. The evidence for a tick goes in the
phase's review record, not in the criterion.**

This file is the list of outstanding work, and it can only carry that signal if
it is mostly outstanding work. On 2026-08-18 it had reached 65k with **69% of it
describing a finished phase** — the Phase 1.5 criteria alone ran 220 lines for 25
items, because each tick had acquired a paragraph of justification. The
justification was right to exist: a tick here has to be earned, and three
criteria in that phase were ticked and later found false. It was in the wrong
place.

So the evidence moves to a per-phase review document — for Phase 1.5,
[`09-phase-1.5-review.md`](09-phase-1.5-review.md) — and the criterion keeps the
statement a reader can check. Nothing is deleted; a criterion closed without
evidence recorded somewhere is the over-tick this plan exists to catch.

Rule of thumb: if a criterion needs more than three lines, the extra lines are
evidence and belong in the review.

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
      inherited from the base image — re-opened because `remoteUser` was stated
      in `devcontainer.json` and read by no assert: BLD-001 applied only to
      `container`, a predicate this repo does not satisfy because it builds from
      an `image:`, so the control skipped and a JSON key nothing verified stood
      in for a verdict. **Closed 2026-08-18** at register contract 7.
      BLD-001 now applies to `[container, devcontainer]` and
      `devcontainer_user_is_non_root` reads the key. It fails an absent user as
      well as a root one: a devcontainer naming neither `containerUser` nor
      `remoteUser` runs as whatever its base image uses, which may be root today
      and may become root on any digest bump — non-root by luck is not the
      property BLD-001 states. `containerUser: root` beside `remoteUser: vscode`
      fails too, being a container that runs as root whatever the tooling does.
      BLD-001 reports PASS here where it reported SKIPPED
- [x] `setup.sh` installs nothing unpinned and nothing unverified —
      **restated 2026-08-18, and closed on the restatement**. The original
      wording was "short enough not to need sectioning — anything longer is
      doing work that belongs in a feature", and the carried-debt note named
      `uv` and `gitleaks` as the work to move. That premise was measured and
      found false: **neither** community feature available for those tools
      verifies what it downloads. Each `curl`s a GitHub release tarball and
      extracts it — no checksum, no signature, no attestation — so moving
      `gitleaks` would have replaced a checksum-verified install with an
      unverified one while *appearing* to strengthen provenance, because
      `devcontainer-lock.json` would then pin the feature.
      It pins the installer, not the artefact. `03-devcontainer.md`'s preference
      ladder was corrected for the same reason: a feature earns rank 1 only if
      it verifies its own download, otherwise it ranks where its install method
      ranks.
      **Restating a criterion in order to close it is the move that most
      resembles cheating**, so three things guard this one. The evidence is
      recorded rather than asserted. The property is now machine-checked —
      `tests/test_devcontainer_setup.py` fails if a package install loses its
      pin, if a downloaded artefact loses its checksum, or if anything pipes
      curl to a shell, all three confirmed by breaking them. And the change was
      put to the repository's owner rather than taken unilaterally.
      Length was reduced where doing so cost nothing: the `gh-ee-skills` heredoc
      is now a reviewed file at `.devcontainer/bin/gh-ee-skills`, because an
      executable that lands on `PATH` belongs in a diff. 95 lines to 83 — but
      length is a symptom, not the property, and nothing checks it
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

- [x] `standard-check schema` passes against `controls.yaml`
- [x] Running against this repo produces a report with no `UNCLASSIFIED` verdicts
      arising from checker bugs (as opposed to genuine ambiguity) — re-opened as
      vacuously true, **closed 2026-08-17**: `UNCLASSIFIED` now has two
      producers (an absent tool, and GOV-002 with no comparison point), so the
      criterion has content. This repo's own run reports none of either
- [x] A deliberately broken register fails schema validation with a message
      naming the field — exercised in `tests/test_schema.py`, one test per
      breakage class
- [x] An unknown `assert` name is a schema **error**, not a skipped check — the
      closed set is derived from the checker's assert registries, so it cannot
      drift from the implementation
- [x] `SKIPPED (predicate)` and `SKIPPED (no credentials)` render distinctly and
      neither is counted as a pass in the exit code — re-opened because a
      no-credentials skip left the code at 0, **closed 2026-08-17**: it now
      yields exit `3` under ADR 0016, while a predicate skip stays `0` because
      not-applicable is a legitimate pass
- [x] The checker's own repo passes every control it can verify locally

The last one is the real gate. If the standard repo cannot satisfy its own
Tier-1 controls, they are not birth conditions.

Four of the boxes above and in phase 0.5 were re-opened by the review that
follows. They are listed unticked with a pointer rather than quietly left green:
a ledger that records only the optimistic reading is the thing this repo exists
to prevent.

## Phase 1.5 — Remediation

Phases 0, 0.5 and 1 closed their exit criteria. A review of the result found
that several were met in letter rather than in substance, and — more seriously —
that the checker's failure modes point the wrong way. In multiple places it
either **aborts without producing any verdict**, or **reports green for
something it never examined**. For a conformance tool those are the only two
failures that matter.

This phase exists because of one line in Phase 2: *"Gates and checker share one
assert implementation — verified by there being one copy."* Every defect below
would be copied into six `gate-*` skills and become six times more expensive to
correct. The principle that put the checker before the template applies again:
fix the checker before anything derives from it.

Nothing here is new scope. It is the distance between what Phase 1 claimed and
what Phase 1 delivered.

### What it found, and how it closed

Recorded in [`09-phase-1.5-review.md`](09-phase-1.5-review.md): the findings
`§ A`–`§ G` that the code still cites, the five decisions it required (all
ratified as ADRs 0014–0018), and the evidence behind every tick below.

That document is closed. This one is the list of outstanding work, so a finished
phase's forensics live there.

### Carried debt — recorded, not gating

- ADR 0013's unsupported line-length passage — **closed**: git history shows
  DOC-001 was introduced already at 250, the commit message said "from the
  previous 80", and the ADR said 120. Three numbers for one event, cited as the
  register's canonical precedent. The passage is removed.
- ~~`standard-check --tier 1` and `standard-check drift` are documented and do
  not work~~ — **closed 2026-08-18**, by correcting the documents rather than
  the code. `02-skill-family.md` and `CLAUDE.md` now say `run --tier 1`, the
  non-existent `drift` subcommand is gone from both, and
  [`08-adopting.md`](08-adopting.md) documents the working forms including that
  `--repo` precedes the subcommand. Found by testing every command in the new
  adoption guide before publishing it: a guide that documents a command which
  prints usage is worse than no guide, and would have been the first thing a new
  adopter hit.
- ~~`uv` and `gitleaks` belong in pinned features~~ — **withdrawn 2026-08-18,
  on measurement.** Neither available community feature verifies what it
  downloads, so the move would have brought both under `devcontainer-lock.json`
  while removing the checksum that makes the gitleaks install trustworthy. The
  Phase 0.5 criterion was restated as the property this note was reaching for,
  and is now machine-checked. What survives as debt is smaller and real: the
  **arm64 gitleaks digest in `setup.sh` is compared by nothing** — the register
  records one checksum and `tool_versions_match_register` checks that one, so
  the second architecture's digest is a checksum nobody checks, which is the
  shape of problem this phase kept finding.
- ~~Ignore paths on a `narrowing-only` control with `baseline: null`~~ —
  **closed 2026-08-18** by [ADR 0019](adr/0019-exemptions-cannot-hide-tracked-files.md),
  which states the property (an exemption may not hide a tracked file) in place
  of the prohibition and has the checker verify it. It carried a Phase 2 exit
  criterion, which is met before the phase starts.
- ~~The meta-controls are in-process assertions declared `kind: command`~~ —
  **closed 2026-08-18** (§ H5). The exception is real and forced: a meta-control
  returns a three-valued `Verdict` and a `kind: file` assert returns a boolean.
  It is now written down in the schema doc and `CLAUDE.md`, and bounded by the
  validator — only a meta-control, and only for its own id.
- ~~`npx --no-install` falls back to `PATH`~~ — **closed 2026-08-18** by
  [ADR 0020](adr/0020-a-locus-reaches-the-pinned-artefact.md), at register
  contract 10. A `lockfile` tool records `invocation` — how the pinned artefact
  is reached — the way a `literal` tool records `pinned_at`, and every locus is
  verified against it. It carries a new Phase 2 criterion above, because the
  template has to answer the same question for every tool it installs.
- Three smaller ones, all § H8: GOV-001's full-run short-circuit accepts
  `run --tier 1` and `--repo ../other` as evidence for every blocking control
  (latent until Tier 2 exists); `standard-check --repo ../other` fails for any
  repository without its own `controls.yaml`, which is every adopter, and exits
  `1` where the CLI reserves `2` for that class. The third — `runner.py`'s
  every-block-narrowed-out path returning `SKIPPED (predicate)` — was
  **accepted as designed on 2026-08-18**: narrowing is the feature, a repository
  matching none of a control's shapes has nothing to run, and coverage grows by
  adding a shape.
- No repo-root `LICENSE`, though `pyproject.toml` declares Apache-2.0 and
  `05-promotion.md` requires every plugin to ship a copy of it. **Not gating for
  this phase, but gating for Phase 6** — `check_plugin_license.py` fails without
  it, so it now carries a Phase 6 exit criterion rather than sitting here alone.
- `.devcontainer/.env` is mode `0644` while holding a live OAuth token and two
  PATs. A `chmod 600` in `fetch-secrets.sh` costs nothing, and the docs present
  that file as the credential boundary (theme T-5).
- Title-versus-mechanism drift: DEV-001's title says features only; LNT-001's
  says "lint **and format**" while nothing checks formatting; TYP-001 enforces
  "no per-file opt-out" without reading `[[tool.mypy.overrides]]`; SUP-002's
  title is broader than what passes, since the npm and curl pins are precisely
  the two Dependabot cannot propose.
- Doc sweep: the schema doc's rung enum omits `blocking (baselined)`;
  "validated by `standard-check schema` on every commit" is scoped to commits
  touching the register; "every URL in the register is verified to resolve" has
  no mechanism (all thirteen do resolve today); `03-devcontainer.md` lists a
  `claude-user-settings.json` that does not exist; CLAUDE.md's "sixteen
  controls" miscount is **closed**, corrected when its § Documents gained a full
  index; the README drops "third-party" from SUP-003, which the owner-exemption
  depends on;
  `06-devcontainer-setup.md`'s description of `setup.sh` omits three of its jobs;
  and the README's "remote *halves* report SKIPPED" understates the report, which
  renders the whole of SEC-001 as `SKIPPED (no credentials)` because a control's
  verdict is the worst of its blocks.

### Exit criteria — phase 1.5

**All 26 met, 2026-08-18.** Each links to its evidence in
[the review](09-phase-1.5-review.md#how-each-criterion-closed). The first 25 were
ticked that morning; a review of the closed phase the same day
([§ H](09-phase-1.5-review.md#h--what-a-review-of-the-closed-phase-found))
re-opened three, added a twenty-sixth, and closed all four. **Seven criteria in
this phase have been ticked and later found false** — that rate, not the count
above it, is what the phase should be judged by, and it is the argument for
reviewing Phase 2 the same way before it closes.

- [x] GOV-002 fails on a baseline grown in a **commit**, not only in a dirty
      worktree
- [x] No assert can abort the run — a read or parse failure is a verdict naming
      the file, and later controls are still evaluated
- [x] A target that is not a git repository is an error, never a page of
      `SKIPPED (predicate)`
- [x] A `run:` string containing a shell operator is rejected at schema time
- [x] The `container` predicate and BLD-001's assert agree on what a Dockerfile is
- [x] DOC-001 verifies its three loci and the ceiling its `enforces` names
- [x] The exit code distinguishes "no credentials" from "all clear" per
      [ADR 0016](adr/0016-exit-codes-for-unverifiable-controls.md) — `3`, `1`,
      `0`, and `--require-complete`
- [x] A control whose tool is absent reports `UNCLASSIFIED`, distinct from FAIL
- [x] GOV-001 measures reachability from a step that **can fail a merge** —
      matched as an invocation rather than a substring, in a workflow that runs
      on push or pull_request. **Re-opened and re-closed 2026-08-18** (§ H1): a
      `workflow_dispatch`-only workflow marked every blocking control reachable
      while TST-001 read the same file correctly. Widened, not restated to fit
- [x] Every verification block declares the `kind` it actually is
- [x] Every row in § D has a test that fails before its fix and passes after —
      `tests/test_section_d.py`
- [x] Every tool has one recorded authority, and every locus is verified against
      it — **re-opened and re-closed twice**: first because `gitleaks` was
      compared at no locus while the assert reported PASS, then on 2026-08-18
      (§ H2) because the loci were four filenames inside the checker. They are
      `tools.<tool>.pinned_at` now, and a declared site that is missing, or that
      holds no pin, is a verdict
- [x] Tools that can have their duplication eliminated, do —
      `markdownlint-cli2` moved to `package-lock.json`
- [x] The two remaining `literal` tools are reconciled by machine — Renovate
      installed, its dashboard reporting all six managed sites
- [x] SUP-002's title matches what it verifies — made true, not narrowed
- [x] `variance: justified` is implementable or removed — removed, with `free`
- [x] Every `lint-md`-deployed artefact carries a provenance stamp, and the
      amend submission is raised —
      [ee-skills-incubator#530](https://github.com/EqualExperts/ee-skills-incubator/issues/530)
- [x] The stamp format carries the **register contract number**
- [x] The unrecorded weakening is closed — removed, not recorded, because a
      Tier-1 baseline is rejected by the schema
- [x] The register rejects unknown keys, at every level
- [x] ADRs 0014–0018 are ratified
- [x] [ADR 0018](adr/0018-register-checker-boundary.md) is **implemented** —
      every rule its ratified test moves is in the register, and every rule that
      stays carries its reason in the ADR. **Re-opened and re-closed 2026-08-18**
      (§ H3, § H4): the cloud-key names had never moved. Four passes now, ending
      at contract 8
- [x] A repository in any ecosystem the register defines is **verified** by
      SUP-001 rather than skipped by it — added and closed 2026-08-18 (§ H3).
      `applies_to: [always]`, and `frozen_install` per ecosystem, so a Go repo
      with no `go.sum` fails where it used to skip
- [x] [ADR 0017](adr/0017-partial-verification-is-reported.md) is **implemented**
- [x] [ADR 0014](adr/0014-satisfying-remote-locus-controls.md) is **implemented**
      — the repository is public
- [x] The default-branch ruleset exists and push protection is enabled, so
      CI-001 and SEC-001 hold *in fact*

Whether the checker can *verify* that platform state is Phase 3's `kind: remote`
work. Requiring it here would have made the phase unclosable by its own terms,
which is the error this plan already made once by putting the devcontainer in
Phase 2.

## Phase 2 — The gates and the template

Build the `gate-*` skills and the devcontainer template together, because the
gates are what make the template's output verifiable.

Order within the phase: `gate-secrets` first, as the reference implementation.
It exercises every locus (`pre-commit`, `ci`, and `remote` in Phase 3), so
whatever shape works for it works for the rest. `gate-quality` second, as the
first gate owning more than one control — where "grouped by the artefact they
write" has to hold for three controls sharing two files. The others follow.

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

- [x] Every adopter-facing step this phase introduces is in
      [`08-adopting.md`](08-adopting.md) with its evidence — the gate skills'
      prerequisites, what `standard-adopt` needs before it can run, and what the
      template requires of a repository that copies it. `gate-secrets` (§ 3.1),
      `gate-quality` (§ 3.2), `gate-supply-chain` (§ 3.3), `gate-build` (§ 3.4),
      `gate-iac` (§ 3.5) and `gate-repo` (§ 3.6) have theirs written down, the
      template has § 2.0, and `standard-adopt` has § 0 — the front door

- [x] `gate-secrets` deploys onto a repo with none of its config, and
      `standard-check` then reports SEC-001 PASS for its local loci — closed
      2026-08-19 against a throwaway repository, since this one has wired
      `gitleaks` by hand since Phase 0.5. Evidence, including each artefact
      deleted in turn and watched failing, in
      [`10-phase-2-review.md`](10-phase-2-review.md)
- [x] Every gate writes a provenance stamp its own verify step reads back —
      holds for all six gates, and the mechanism the
      rest inherit is in place: `provenance_stamp_present`, and a schema rule
      that rejects a register where it and `deployed_by` name different gates.
      Open until the gates exist. Reading back is now **per control**: a gate
      that wrote every artefact and recorded only one of them fails the other
      two. What no control proves is that the deployment was *complete* — how
      many artefacts, at which loci — because that list is the plugin's
      `deploys.json` and reading it is Phase 5's sweep
      ([ADR 0018](adr/0018-register-checker-boundary.md) § Applied — fifth pass).
      **Closed 2026-08-21**: all six gates exist and each control reads back its
      own stamp, verified end to end in `tests/test_standard_adopt.py`
- [x] Gates and checker share one assert implementation — verified by there
      being one copy, not by comparing two. Closed 2026-08-19: the copy is
      `standard_check.asserts`, a gate reaches it only through
      `standard-check run --control <ID>`, and a gate that deploys a control it
      does not name there fails a test
- [ ] The devcontainer template builds, and DEV-001 passes against it — the
      template ships at `plugins/ee-standard/templates/devcontainer/` and
      DEV-001's and BLD-001's property blocks pass against a copy of it
      (`tests/test_devcontainer_template.py`). **Open on the other half**: this
      devcontainer has no Docker, so nothing here has built it, and a tick on a
      build nobody ran is the over-tick this plan exists to catch. The commands
      are in [`08-adopting.md`](08-adopting.md) § 2.0
- [x] The template pins no tool version by hand. Every tool it installs is
      either sourced from a lockfile the consumer repo already commits, or from
      a single toolchain file ([§ G](09-phase-1.5-review.md#g--tool-version-reconciliation)'s
      action 2) — never a literal inside
      `setup.sh`. **Closed 2026-08-21** as a grep rather than a reading, because
      [ADR 0020](adr/0020-a-locus-reaches-the-pinned-artefact.md) named this
      criterion in advance as one a template could meet *in letter*
      ([`10-phase-2-review.md`](10-phase-2-review.md) § The criterion that
      needed a test rather than a review)
- [x] The rule for exemptions in a deployed config is decided and **checkable**
      before any gate skill deploys one (§ H7) — closed 2026-08-18 by
      [ADR 0019](adr/0019-exemptions-cannot-hide-tracked-files.md): an exemption
      may scope a gate to what git does not track, and may never hide a file it
      does. DOC-001's config now carries none at all

- [x] Every locus's invocation **resolves to** the pinned artefact, shown by
      deleting the artefact and watching that locus fail — not inferred from
      where the version is recorded ([ADR 0020](adr/0020-a-locus-reaches-the-pinned-artefact.md)).
      The criterion above is about the *source* of a version; `npx --no-install`
      satisfied it while falling through to `PATH` (§ H6). Shown for DOC-001,
      and now measured for the quality gates too: contract 12 moved their four
      `stacks:` invocations to the artefact-reaching form, and deleting the
      artefact makes `uv run` reinstall the pin or fail — never fall through
      ([ADR 0020](adr/0020-a-locus-reaches-the-pinned-artefact.md) § Applied to
      the quality gates). That residual — `uv run` falling through when the tool
      is absent from the project altogether — closed at register contract 13,
      where `stack_tool_pinned_in_lockfile` made the pin's existence a verdict
      ([`10-phase-2-review.md`](10-phase-2-review.md) § The pin's existence).
      Contract 14 added SUP-003's two, whose gate is the checker itself. Open
      for no loci: every gate now writes and verifies each locus its controls
      declare

- [x] Every SKILL.md passes preflight P1–P11 — all six gates and
      `standard-adopt` pass with zero failures, each recorded in
      `10-phase-2-review.md` under its own § Preflight P1–P11 heading. The
      `standard-check` and `standard-variance` skills are Phase 3's and Phase
      5's respectively, and are not this phase's to ship
- [x] Every control's declared `locus:` is read by something. Found open in
      Phase 2: SUP-003, BLD-001, DEV-001 and IAC-001 each declared
      `[pre-commit, ci]` and verified only their property, so a repository with
      no pre-commit hook of any kind reported PASS
      ([`10-phase-2-review.md`](10-phase-2-review.md) § It found a locus nothing
      had ever read). **Closed 2026-08-21** across contracts 14, 15 and 16, with
      one assert reading the control's own `locus:` list rather than knowing two
      by name. Contract 16 also closed two ways a CI step could be credited as a
      locus without gating anything: a suppressed step, and the step that
      *installs* a tool rather than running it
      ([`10-phase-2-review.md`](10-phase-2-review.md) § What this slice found in
      the other four gates)

- [ ] `gate-repo`'s ruleset payload is one GitHub's API accepts, and names the
      status checks the branch must require — **found open by the second review,
      2026-08-21** ([`10-phase-2-review.md`](10-phase-2-review.md) § 2). The
      rule is spelled `{ "type": "required_status_checks" }` with no
      `parameters`, which the REST schema requires, so the apply call 422s; and
      a rule naming no context requires no check, which
      `ruleset_recorded_matches_register` cannot see because it tests only that
      a rule of that type is present. This repository's recorded ruleset is
      therefore not the transcription its header claims — the platform requires
      `standard-check` and `lint-md`, and the file names neither. Closing it
      likely lets GOV-001 drop its partial

- [x] `standard-adopt` end-to-end on a scratch repo: plan → confirm → deploy →
      verify → commit, with the verify step genuinely able to fail — closed
      2026-08-21 by `tests/test_standard_adopt.py`, which drives every gate in
      the skill's own dispatch order through their shipped templates and watches
      the verify step fail on a suppressed lint step. **What is proved is that
      the pipeline works, not that a model follows the prose**; that limit is
      recorded in [`10-phase-2-review.md`](10-phase-2-review.md) § What is
      proved, and what is not

That last clause matters. A verify step that has never been observed failing is
not known to work — deliberately break a deployed config and confirm the run
reports it.

## Phase 3 — Remote controls and meta-controls

The locus that gets forgotten, done deliberately.

Implement `kind: remote`: GitHub push protection state, branch ruleset shape,
and the presence of a workflow that can actually fail. `gate-repo` itself shipped
in Phase 2 at register contract 17, and already applies the ruleset via the API —
what is deferred here is *verifying* the platform state it produces, which is the
half no file can answer.

Then GOV-001, which is the highest-value control in the register and cannot be
finished before this phase: proving a `blocking` control is *reachable from a CI
step that can fail* requires reading platform state, not files. A workflow file
that exists but is not a required check is precisely theme **T-3** — declared but
unreachable — and only a remote check catches it.

### Exit criteria — phase 3

- [ ] Every adopter-facing step this phase introduces is in
      [`08-adopting.md`](08-adopting.md) with its evidence — the credentials
      `kind: remote` needs, the token scopes that create a ruleset, and how an
      adopter confirms their conformance run is a *required* status check

- [ ] Remote verification passes against a real repository
- [ ] With no credentials, remote checks report `SKIPPED (no credentials)` and
      the run does **not** exit 0 on that basis alone — satisfied for the exit
      code since 2026-08-17 (it is `3`), outstanding for the workflow
- [ ] The `Standard` workflow's Conformance step passes `--require-complete` and
      no longer tolerates exit `3`. This is the flip ADR 0016 § Ratified
      tolerance defers to this phase: the tolerance exists only because remote
      verification does not, so implementing it here is what ends it. Leaving
      the tolerance in place after remote verification works would be the
      silence ADR 0016 was written to stop
- [ ] GOV-001 correctly fails a repo whose lint workflow exists but is not a
      required status check
- [x] GOV-002 fails when a baseline file grows by one line — **already
      satisfied** by Phase 1.5's first criterion, which made GOV-002 compare
      against the default branch's merge-base. GOV-002 reads the register, not
      platform state, so nothing here is deferred to this phase; the box is
      listed for completeness of the meta-control set
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

- [ ] Every step the consumer repo needed is in
      [`08-adopting.md`](08-adopting.md) **before** the criterion below is
      judged. This phase is the one that measures the guide: anything the
      operator had to ask about, work out, or already know is a gap in it, and
      the fix belongs in the guide rather than in a reply to the question

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

- [ ] Every adopter-facing step this phase introduces is in
      [`08-adopting.md`](08-adopting.md) with its evidence — how a repository
      opts into the sweep, and how its owner reads a staleness report

- [ ] Bumping a gate's version *without* changing its output produces **no**
      redeployment recommendation
- [ ] Bumping its contract version *does*
- [ ] `skill-update` reports an owed deployment where every plugin is current,
      and does not print *Already done* over it
- [ ] The sweep runs unattended and produces a report nobody has to ask for
- [ ] A repo that has never deployed is distinguishable from one deployed and
      current, and from one deployed and stale
- [ ] Taking an upstream skill release is a supported operation with a recorded
      outcome: **redeployed**, or **declined with the disagreement named**.
      Refreshing a provenance stamp by hand — recording a redeployment that did
      not happen — is not one of the outcomes
- [ ] A deployment behind because nobody has redeployed is distinguishable from
      one behind because the release would revert a narrowing this register
      holds. The first is a chore; the second is a decision, and reporting them
      the same way trains everyone to ignore both

The first two criteria are the whole noise argument, expressed as a test. If a
documentation-only release triggers a recommendation, the mechanism will be
ignored within a month and the phase has failed regardless of what else passes.

### Accepting an upstream skill release

A skill the family does not own will keep shipping. The benefit of those
releases is the reason to depend on a marketplace at all, so *not* taking them
is a cost, not a safe default — but taking one blindly reverts whatever this
register narrowed. `lint-md` is the worked example, and it is carried here
rather than in Phase 6 because the amendment is only half of it: raising an
issue is Phase 6's, and being **able to accept the answer** is this phase's.

The current state, measured 2026-08-22: `lint-md@1.0.7` is installed and is the
marketplace latest; the deployed stamps read `lint-md@1.0.6`. Re-running the
skill today changes nothing — six of seven steps hit a presence check and the
seventh prompts — so the deployment is not *at risk*, it is *unrefreshable*: the
stamp would claim 1.0.7 wrote artefacts 1.0.7 would not write. That is the gap
this phase closes.

Four rows separate the installed skill from what this register will accept. Two
are ours to argue upstream, two are plain defects:

| Row | What 1.0.7 does | Why it cannot be deployed here |
| --- | --- | --- |
| 1 | Writes `npx --no-install markdownlint-cli2` at every locus | [ADR 0020](adr/0020-a-locus-reaches-the-pinned-artefact.md) measured `--no-install` falling through to `PATH`; the register pins `tools.markdownlint-cli2.invocation` to `node_modules/.bin/markdownlint-cli2` |
| 2 | Writes `.claude/**` into `ignores` | Right intention, wrong mechanism — see below |
| 3 | Guards that step with `grep -q "node_modules"` | Matches this repo's *comment* explaining why the list was removed, so the skip is a coincidence of wording |
| 4 | Prompts to overwrite `.markdownlint.yaml` | Does not recognise an `ee-control:` header, so accepting drops the DOC-001 stamp |

Row 2 is the one to get right, because the exclusion is **correct in intent**.
Two different things share the `.claude` prefix:

- **Claude's auto-memory** — `~/.claude/projects/*/memory/*.md`. A feature this
  repository neither owns nor authors, and its files have no reason to satisfy
  DOC-001. Genuinely out of scope.
- **The repository's own `.claude/`** — `hooks/md-lint.py` and `settings.json`
  today, both tracked, both authored here. Squarely in scope.

An `ignores` entry cannot tell them apart, and it is aimed at the wrong one: the
memory files live under `$HOME`, outside the repository, so a repo-root
`**/*.md` glob never reaches them — 49 files linted, none of them memory. The
only locus that *could* reach one is the PostToolUse hook, which already skips
them by location (incubator [#409](https://github.com/EqualExperts/ee-skills-incubator/issues/409)).
So the exclusion is already achieved, by a mechanism that names the real reason.
What `ignores: ["\.claude/**"]` adds is hiding anything the repository later
authors under `.claude/` — which is what
[ADR 0019](adr/0019-exemptions-cannot-hide-tracked-files.md) forbids and
`markdown_gate_wired_at_all_loci` fails.

The general rule this phase owes a mechanism to: **an exclusion is scoped by
what it is for, not by where it sits.** A path outside the repository is out of
scope by location and needs no exemption; a path inside it is in scope and an
exemption weakens the control. A skill that cannot express the difference should
be told so, not worked around locally.

## Phase 6 — Promotion

Per [`05-promotion.md`](05-promotion.md), in the order given there: the
`CONTRIBUTING.md` corrections first (small, independent, establishes contact),
then `ee-standard` plus the `governance` category, then the `skill-update`
amendment — plus the `lint-md` amendment identified in Phase 1.5 § F, which
makes four.

### Exit criteria — phase 6

- [ ] [`08-adopting.md`](08-adopting.md) describes installing from the
      marketplace, and its § Status table is true on the day of release — a
      guide that still calls the shipped machinery "not built" is the mirror of
      one that describes tooling which does not exist

- [ ] A repo-root `LICENSE` exists and is copied into the plugin —
      `check_plugin_license.py` fails without it, and `pyproject.toml` already
      declares Apache-2.0. Carried as debt since Phase 1.5, gating here
- [ ] How `/skill-submit-new` reaches skills that live in a plugin directory is
      decided and done. It resolves `<name>/SKILL.md` in the project or
      user-level Claude skills directory, and this repository's are in
      `plugins/ee-standard/skills/` — a copy, a symlink, or a fifth submission
      teaching it the plugin layout ([`05-promotion.md`](05-promotion.md) §
      What the incubator actually holds)
- [ ] Every skill in the family is submitted, and every issue names the **same**
      `promote-config.json` entry. `/skill-submit-new` is per skill and its
      generated entry is `{"skills": ["<name>"]}`, so the default outcome of
      nine issues is nine single-skill plugins rather than one
- [ ] All the submissions raised: the family (one issue per skill), the
      `governance` category, the `skill-update` widening, the `CONTRIBUTING.md`
      corrections, and what remains of the `lint-md` amendment from Phase 1.5
      § F. `lint-md@1.0.7` shipped most of #530 on 2026-08-20 and **#530 is
      closed** — its closing comment records `npx --no-install` as the fix, so
      this is a **new** amendment arguing against a shipped decision rather than
      a follow-up on an open one, and it must carry ADR 0020's measurement
      rather than assert the conclusion. Four rows, not two: the ADR 0020
      invocation, the ADR 0019 exemption, the `node_modules` guard that matches
      prose, and the overwrite prompt that does not recognise a provenance
      header — enumerated in § Accepting an upstream skill release
- [ ] `ee-standard` installable from the marketplace **as one plugin**, with
      every skill in it — not as one plugin per skill
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

The plan's dependencies are strict in three places and loose everywhere else:
Phase 0.5 gates Phase 1, Phase 1.5 gates Phase 2 (because Phase 2 copies the
assert layer into six skills), Phase 1 gates everything after it, and Phase 4
gates Phase 6. Phases 2 and 3 can overlap once the checker's assert interface is
settled.

The genuine risk is Phase 4 revealing something Phases 1–3 assumed. That is the
purpose of Phase 4, and discovering it there costs a rework; discovering it after
promotion costs a marketplace amendment and everyone who already installed it.
