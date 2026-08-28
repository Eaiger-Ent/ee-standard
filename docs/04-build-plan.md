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
- [x] An ADR exists per control in `docs/adr/` — `0001`–`0013`, one per control
      Phase 0 wrote, and `0022` for SEC-003, added at register contract 22.
      Every `rationale_adr` reference in `controls.yaml` resolves to a live
      record; a control whose decision is a cross-cutting one cites that one
      rather than being given a `00NN` of its own.

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

**Phase 1 is development work.** If `register-check` is written on a host
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
- [x] `setup.sh` installs uv from a checksum-verified release artefact, and
      `ghcr.io/devcontainers/features/python:1` is gone from `devcontainer.json`
      and `devcontainer-lock.json` — **added 2026-08-24** by
      [ADR 0030](adr/0030-uv-is-bootstrapped-from-a-pinned-release.md), not
      re-opened: nothing ticked above became false. The criterion two rows up
      reasoned about `uv` and `gitleaks` and concluded that no community feature
      verifies its download; `pip install uv==0.12.5` is pinned and passes
      `tests/test_devcontainer_setup.py`, which asks a package install for a pin
      and a downloaded artefact for a checksum. ADR 0030 moves uv from the first
      category to the second, which is the stronger one, and takes the feature's
      three extensions, its autopep8 formatter binding and its second
      interpreter on `PATH` with it. **Closed 2026-08-24 by the rebuild**, not
      by a reading: uv 0.12.5 is at `/usr/local/bin/uv` from the release tarball
      and `/usr/local/python` no longer exists, `uv run python -V` reports
      3.14.7, the lock carries three features and none is `python:1`, DEV-001
      passes, no `ms-python.*` extension is installed, `check-auth.sh` reports
      `python — Python 3.14.7`, and gitleaks and the pre-commit hook still
      arrive — so the rest of `setup.sh` survived losing the interpreter it used
      to start with. The evidence is recorded in
      [ADR 0030](adr/0030-uv-is-bootstrapped-from-a-pinned-release.md)
      § Consequences, beside the prediction it settles. What the rebuild also
      showed is that removing the feature does not leave one interpreter: the
      base image ships `python3-minimal`, so `/usr/bin/python3` is 3.13.5. That
      falsified a claim rather than the decision, and is recorded as ADR 0030
      revision 2. The lock file is **not** an outstanding hand edit: the CLI
      writes `devcontainer-lock.json` on every `build` and `up`, so the rebuild
      regenerated it, and it wrote back what the hand edit already said — whose
      three `resolved` digests were then checked against what `ghcr.io` serves
      for the declared tags. What this does **not** close, tracked below, is the
      shipped template, a different artefact nobody has built

The last one was register debt, not container work: as `controls.yaml`
originally stood, a repo with a complete lock file and a floating image tag
passed DEV-001 — theme **T-1** inside the register itself. Closed at register
`v0.2.0` (contract 2) by widening DEV-001's `enforces` text and adding the
`devcontainer_image_digest_pinned` assertion, so Phase 1 implements the control
against complete text.

## Phase 1 — The checker

Build `register-check` as an ordinary executable. Python, installed from a
pinned version, no Claude anywhere near it — inside the Phase 0.5 container.

Implement in this order, because each stage is testable against the register that
already exists:

1. Schema validation (`register-check schema`) — the register validates itself
2. `kind: command` verification — shell out, exit code is the verdict
3. `kind: file` assertions — the closed set named in `controls.yaml`
4. Predicate evaluation — `SKIPPED (predicate)` distinct from `PASS`
5. The three meta-controls
6. Report rendering, ordered by tier then rung

`kind: remote` is deliberately deferred to Phase 3. It needs credentials, network
and a live repository, and building it now would mean stubbing exactly the part
that must not be stubbed.

### Exit criteria — phase 1

- [x] `register-check schema` passes against `controls.yaml`
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
- ~~`register-check --tier 1` and `register-check drift` are documented and do
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
  (latent until Tier 2 exists); `register-check --repo ../other` fails for any
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
  "validated by `register-check schema` on every commit" is scoped to commits
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
      prerequisites, what `register-adopt` needs before it can run, and what the
      template requires of a repository that copies it. `gate-secrets` (§ 3.1),
      `gate-quality` (§ 3.2), `gate-supply-chain` (§ 3.3), `gate-build` (§ 3.4),
      `gate-iac` (§ 3.5) and `gate-repo` (§ 3.6) have theirs written down, the
      template has § 2.0, and `register-adopt` has § 0 — the front door

- [x] `gate-secrets` deploys onto a repo with none of its config, and
      `register-check` then reports SEC-001 PASS for its local loci — closed
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
      own stamp, verified end to end in `tests/test_register_adopt.py`
- [x] Gates and checker share one assert implementation — verified by there
      being one copy, not by comparing two. Closed 2026-08-19: the copy is
      `register_check.asserts`, a gate reaches it only through
      `register-check run --control <ID>`, and a gate that deploys a control it
      does not name there fails a test
- [x] The editor locus is verified by exclusion, not by presence — **added
      2026-08-24** by
      [ADR 0029](adr/0029-the-editor-locus-is-configured-by-the-repository.md),
      points 3 and 4. Not re-opened: nothing ticked above became false.
      `stacks:` gains, per gate, the file-type binding its `editor_extension`
      must hold, and `linter-wired-at-all-loci` fails when another extension
      holds a gated file type. Today it asks only whether the pinned extension
      is installed, and `ghcr.io/devcontainers/features/python:1` bound Python
      files to autopep8 with `charliermarsh.ruff` installed alongside it the
      whole time — a state the assert reported as passing. Point 1 was already
      done: `.vscode/settings.json` is tracked and holds the bindings.
      **Closed 2026-08-24 at register contract 21.** `editor_binding` — a
      `language` and the `setting` that holds it — sits on the python lint gate
      and not on the typescript one, because eslint is not TypeScript's
      formatter and mandating that binding would mandate something no
      reasonable repository writes; omitting it asserts the gate holds no file
      type, the shape `coverage_key`'s absence already had.
      `linter-wired-at-all-loci` fails three states, each **observed failing**
      in `tests/test_gate_quality_deploy.py` rather than reasoned about: another
      extension holding the language, nobody holding it, and the binding
      restated in `devcontainer.json`. The second is the one that mattered —
      the autopep8 binding came from a feature, so no tracked file said
      anything, and an assert objecting only to a wrong value would have passed
      the state it exists to catch. `gate-quality` gained
      `templates/editor-settings.json` and a Step 3b, its `contractVersion`
      went to 3, and this repository's `.vscode/settings.json` gained the
      LNT-001 stamp that makes it the twelfth stamped artefact. Both points
      landed together, so the contract moved once rather than twice
- [x] The devcontainer template builds, and DEV-001 passes against it — the
      template ships at `plugins/control-register/templates/devcontainer/` and
      DEV-001's and BLD-001's property blocks pass against a copy of it
      (`tests/test_devcontainer_template.py`). **Closed 2026-08-25 by Phase 4**,
      which is where it was deferred to on 2026-08-24 and for the reason given
      then: the consumer repository has to build the template from placeholders
      to exist at all, so doing it here would have been a rehearsal of the same
      build. Built on a macOS host with Docker 29.7.2 — `--no-cache` and then
      from clean — and run, ending in a container reporting `remoteUser: vscode`
      and every probe green.
      **It did not build first time, and that is what the criterion was for.**
      Three defects had to be fixed before it came up, none of which a file test
      could have caught: no Claude Code and no node, so the container could not
      run the skill that is the published route into the standard; no uv, while
      its own `setup.sh` called `uv sync --frozen`
      ([ADR 0034](adr/0034-the-template-bootstraps-uv.md)); and a lock file left
      covering one feature of two because `devcontainer up` reuses an existing
      container. The evidence, and the seven other things Phase 4 found, is in
      [`12-phase-4-review.md`](12-phase-4-review.md). The
      [ADR 0028](adr/0028-the-support-floor-is-what-we-run.md) revision 2 half
      stands as it was rewritten: `uv run python -V` at the pin, verified again
      here — with `.python-version` committed the consumer's container answers
      3.14.7, and without it 3.13.5
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
      `register-adopt` passed with zero failures, each recorded in
      `10-phase-2-review.md` under its own § Preflight P1–P11 heading. The
      `register-check` and `register-variance` skills are Phase 3's and Phase
      5's respectively, and are not this phase's to ship.
      **Re-opened 2026-08-25 by Phase 4** — the eighth criterion in this project
      ticked and later found false, and the first found from outside it. P9 is
      *"a called skill has `disable-model-invocation: true` and cannot be
      invoked via the Skill tool"*, which was true of all seven skills
      `register-adopt` dispatches, and it reported
      `{"skill": "register-adopt", "overall": "PASS", "fails": 0}`: the dispatch
      targets are named in prose, not in a field a checker resolves. So the
      front door had never been able to take its first step. The state is fixed
      — [ADR 0035](adr/0035-a-dispatched-skill-is-reachable.md), with the
      `README.md` note P9 itself prescribes — and the box stays open until the
      preflight is **re-run** over the changed skills, because a criterion
      closed on the reading that failed it once is closed on nothing
      ([`12-phase-4-review.md`](12-phase-4-review.md) § 10).
      **Re-closed 2026-08-26** on that re-run, over all **eight** skills — the
      set grew by `register-install` since the first pass — with every one
      reporting `"overall": "PASS", "fails": 0`. It did not pass first time:
      `gate-quality` failed P1 at 510 lines, and the 56 lines over the ceiling
      were two sections pasted into every skill they governed, so the fix was
      [ADR 0036](adr/0036-shared-skill-prose-has-one-home.md) rather than an
      edit to the longest file. **Two things this run reports and does not
      fail**, recorded because a green line that hides them is what re-opened
      this box: P4 is a WARN for the six skills [ADR 0035](adr/0035-a-dispatched-skill-is-reachable.md)
      took `disable-model-invocation` off, which is the accepted state and not
      a regression; and P9 still reports *no sub-skill invocations detected* for
      `register-adopt`, so the check that would have caught the original defect
      is still blind to a dispatch named in prose — this criterion is closed on
      the register's own tests, not on P9 having learned to see
      ([`12-phase-4-review.md`](12-phase-4-review.md) § The preflight re-run)
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

- [x] `gate-repo`'s ruleset payload is one GitHub's API accepts, and names the
      status checks the branch must require — found open by the second review on
      2026-08-21, **closed 2026-08-22** at register contract 19
      ([`10-phase-2-review.md`](10-phase-2-review.md) § What contract 19
      changed). `required_checks:` is the register's and is held to the
      workflows: a named context must come from a gating job that does not
      suppress its own failure. The record was re-transcribed and now matches
      the API response exactly. GOV-001's partial **narrowed** rather than
      dropped — whether the repository says a job is required is now answered
      from a file, and whether GitHub enforces it stays Phase 3's

- [x] `register-adopt` end-to-end on a scratch repo: plan → confirm → deploy →
      verify → commit, with the verify step genuinely able to fail — closed
      2026-08-21 by `tests/test_register_adopt.py`, which drives every gate in
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

- [x] Every adopter-facing step this phase introduces is in
      [`08-adopting.md`](08-adopting.md) with its evidence — the credentials
      `kind: remote` needs, the token scopes that create a ruleset, and how an
      adopter confirms their conformance run is a *required* status check —
      closed 2026-08-24 by Phase 3's eleventh slice. The first two were written
      as they were found; the third had a checklist row and nothing behind it,
      and so did the two steps the seventh and ninth slices introduced. **§ 4.2**
      is the chain from a control to a blocked merge — four links in four
      places, three of whose breaks leave a repository looking conformant — and
      ends where no report can: open a pull request whose required check fails
      and watch the merge button refuse. **§ 4.3** is the credential and
      `--require-complete` together, in that order, with the environment gate an
      adopter takes rather than the arrangement this repository takes.
      `tests/test_adopter_guide.py` derives the list from the register, so a
      control gaining a remote block fails the build until § 4.1 says what token
      answers it ([`11-phase-3-review.md`](11-phase-3-review.md)
      § The eleventh slice)

- [x] Remote verification passes against a real repository — closed 2026-08-22
      by Phase 3's first slice. `SEC-001` and `CI-001` both report `PASS`
      against `Eaiger-Ent/ee-standard`, the first `0` exit either has produced
      ([`11-phase-3-review.md`](11-phase-3-review.md) § Evidence)
- [x] With no credentials, remote checks report `SKIPPED (no credentials)` and
      the run does **not** exit 0 on that basis alone — **closed 2026-08-24**.
      The exit code has been `3` since 2026-08-17 and the reporting half was
      closed and tested on 2026-08-22; the workflow half is closed by the flip
      below, which turns that `3` into a failed check rather than a printed
      note. The one run that still tolerates `3` is a pull request from a fork,
      which cannot have the credential at all
- [x] The `Standard` workflow's Conformance step passes `--require-complete` and
      no longer tolerates exit `3` — **closed 2026-08-24**. This is the flip
      [ADR 0016](adr/0016-exit-codes-for-unverifiable-controls.md)
      § Ratified tolerance deferred to this phase, and leaving the tolerance in
      place after remote verification worked would have been the silence that
      ADR was written to stop.

      It was recorded here for months as *blocked on a token, not on the flip*,
      and the token was the smaller half. Two things had to land and neither
      alone was enough: `PLATFORM_READ_TOKEN` (contract 25) let SEC-001 and
      SEC-003 answer in CI, and GOV-001 dropping its `partial:` (contract 26)
      removed the thing that denied the run a `0` **by design** whatever the
      credentials. ADR 0016's 2026-08-23 amendment had named only the first, so
      the bound it moved to was itself short by one thing — recorded in that
      ADR's revision 5 rather than smoothed over.

      **One case is named rather than left.** A pull request from a fork
      receives no repository secret, so SEC-001's remote block cannot answer and
      that run tolerates `3`, and only `3` — a verified violation still fails
      it. The bound is a fact about the platform rather than a phase:
      a fork does not get the secret. `tests/test_conformance_step.py` runs the
      step's own script with the checker stubbed and asserts both branches,
      because a carve-out nobody exercises is one that quietly becomes general,
      which is what happened to the tolerance it replaces
      ([`11-phase-3-review.md`](11-phase-3-review.md) § The ninth slice).

      What ADR 0022 records about the cost of a stronger token, and the controls
      the register needed **before** one was introduced, stands as written; so
      does its finding that SEC-002 could not see a platform token at all,
      because `cloud_credentials:` names only cloud provider keys

- [x] GOV-001 correctly fails a repo whose lint workflow exists but is not a
      required status check — closed 2026-08-24 at register contract 26. The
      meta-control now reads which status checks GitHub enforces on the default
      branch and fails a check the register requires and the platform does not:
      a ruleset recorded in the repository and never applied protects nothing,
      so a control credited to that job is reached from a step nothing waits
      for. Its `partial:` is gone because the property is **verified**, not
      waived — without a token it reports `SKIPPED (no credentials)` and says
      which half it did verify
      ([`11-phase-3-review.md`](11-phase-3-review.md) § The eighth slice)
- [x] GOV-002 fails when a baseline file grows by one line — **already
      satisfied** by Phase 1.5's first criterion, which made GOV-002 compare
      against the default branch's merge-base. GOV-002 reads the register, not
      platform state, so nothing here is deferred to this phase; the box is
      listed for completeness of the meta-control set
- [x] GOV-003 fails on a control past `review_by` — closed 2026-08-24 by
      Phase 3's second slice, which built nothing: the check has held since
      the checker was first written, and the same verdict covers an expired
      `partial:` declaration, which is the same expiry mechanism
      ([`11-phase-3-review.md`](11-phase-3-review.md) § The second slice)
- [x] `gate-repo` confirms before every remote mutation, independently of the
      plan-level confirmation — closed 2026-08-24 by Phase 3's tenth slice. The
      gate made three calls that change platform state and confirmed one of
      them: `PUT /rulesets/{id}` was a line of prose inside the *create*
      question's own step, and `DELETE /branches/{branch}/protection` was not
      written down at all — the two that can *reduce* protection. Each now has
      its own question naming its own change, and
      `tests/test_gate_repo_confirmation.py` **enumerates** them rather than
      counting them: every `gh api` in the skill carrying a method other than
      `GET` must appear in the skill's own table and have a question standing
      between it and the call before it, so a fourth mutation fails the build
      until it has both ([`11-phase-3-review.md`](11-phase-3-review.md)
      § The tenth slice)

### What moved to Phase 5, and why

Two criteria stood here until 2026-08-24 and now stand in Phase 5. They tested
`register-variance` — the skill that classifies a delta's direction — and that
skill does not exist. Nor does the classifier behind it: there is nothing in
`src/` that reads a delta and reports *narrowing* or *loosening*, and
`02-skill-family.md` has always listed that skill as **Phase 5's**.

So this phase was written to test, in a consumer repository, machinery a later
phase builds. Leaving it would have made Phase 4 unclosable by its own terms —
the error this plan has already made twice, most recently by putting the
devcontainer in Phase 2.

| Criterion | Where it is now |
| --- | --- |
| Weakening is **caught** | Stays here. The checker does it today |
| Weakening is **classified** by direction | Phase 5, beside the skill that classifies |
| The three known `UNCLASSIFIED` cases report as `UNCLASSIFIED` | Phase 5, same reason: they are the cases where *classification* declines to guess |

The split is recorded rather than performed silently for the reason this file
gives everywhere else: a criterion that quietly gets easier is indistinguishable
from one that was met.

### The one place this repository does not do what it asks of everyone else

[ADR 0022](adr/0022-a-platform-token-ci-carries.md) requirement 6 says this
belongs here, and here is why: **this repository holds its platform token as an
ordinary repository secret — that ADR's Option 1 — while the standard asks an
adopter for the deployment-environment gate, its Option 3.** The secret is
`PLATFORM_READ_TOKEN`, set on 2026-08-24, and the register names it from
contract 25.

It is a posture difference rather than an exception, and it rests on a fact
about this organisation rather than about the arrangement. The six accounts that
could read a repository secret here are organisation owners who already hold
admin on this repository, so the credential grants its readers nothing they did
not have. An adopter's contributors are not organisation owners, so the same
secret in the same place is a real exfiltration path for them — reachable, as
that ADR corrected itself to say, by a pull request that edits the workflow's
own trigger list.

Three things follow, and none of them is optional.

1. **It may not appear in `controls.yaml`.** It did, from contract 22 until
   contract 24's follow-on: the comment introducing `platform_credentials:`
   said that *ADR 0022 chose Option 1*, which is true of this repository and was
   read by every repository the register reaches. Removing it is what closed the
   requirement.
2. **It may not appear under `plugins/`**, which is what an adopter installs. A
   gate that deployed this arrangement would hand an authoring environment's
   convenience to a build project whose contributors are strangers.
3. **`tests/test_posture.py` fails the build if either happens**, and fails it
   equally if this section is deleted — an undocumented divergence between what
   this repository does and what it asks of everyone else is indistinguishable
   from an oversight. The requirement says of itself that it is the one most
   likely to be skipped, because nothing breaks when it is. That test is what
   breaks.

Adopter-facing guidance for the arrangement they *should* take is in
[`08-adopting.md`](08-adopting.md) § 3.1, which names the deployment environment
and says why a branch policy is a guard a pull request cannot edit.

## Phase 4 — The consumer repo

The actual test. A second repository that did not author the standard, set up
end to end by following only the published instructions.

Sequence, per [`03-devcontainer.md`](03-devcontainer.md):

1. Create the repo with the `.devcontainer/` template, substituted
2. Run `/register-adopt` — it deploys the gates
3. Run `register-check` — it passes
4. Deliberately weaken something, and confirm the checker catches it. Whether
   the **direction** of the weakening is classified is Phase 5's, with the skill
   that does it — see § What moved to Phase 5, and why.

### Before this phase can start

None of this is an exit criterion. These are the things Phase 4 cannot begin
without, listed because the phase is the first that runs outside this
repository and every one of them was found by asking rather than by building.
Each was decided on 2026-08-24.

| What | Decision | How you know it is met |
| --- | --- | --- |
| A machine that can build a devcontainer | A **macOS host with Docker** and the devcontainer CLI. This container has no Docker, which is why Phase 2's template-build criterion was deferred here | **Met** 2026-08-25: Docker 29.7.2, `devcontainer` 0.88.0. `devcontainer build --workspace-folder .` completes on the host. The template's `fetch-secrets.sh` reads the macOS Keychain, so a non-macOS host needs that script adapted first, and the adaptation is then part of what this phase measures the guide on |
| The consumer repository's stack | **Python + uv**, so `uv run register-check` resolves as the register's `invocation` says | It exercises LNT-001, TYP-001, TST-001, SUP-001/003, BLD-001, DEV-001, SEC-001/003 and CI-001. It proves nothing about a repository that is not a Python project, and [ADR 0032](adr/0032-the-checker-is-installed-from-a-tagged-ref.md) records that as unsolved rather than covered |
| Where it lives | **Eaiger-Ent**, where `gh` is already authenticated and every platform act in § 1 is grantable without waiting on anyone | Note what it does not test: the same accounts hold admin here, which is the fact that lets this repository take a posture it does not publish. The adopter's environment gate is exercised by configuration, not by a different threat model |
| How the plugin reaches the consumer | **Submitted to the ee-skills marketplace**, so the consumer installs it the way any Equal Experts repository will | **Taken a different way on 2026-08-25**, because Phase 6 forbids submitting anything before Phase 4 has run and this row made that circular. `.claude-plugin/marketplace.json` now exists — Phase 6's *"installable as one plugin"* criterion needs it regardless — and the consumer installed `control-register` from this directory as a marketplace, exactly as `ee-skills` is registered on this host. The deviation is real and bounded: Phase 6's last criterion re-adopts from the marketplace copy, which is where installing-as-published gets tested |
| How the checker reaches the consumer | A dependency pinned to a **tagged git ref**, placed by `register-install` ([ADR 0032](adr/0032-the-checker-is-installed-from-a-tagged-ref.md)) | **Met** 2026-08-25, register contract 29: the skill exists, `tools.register-check.install` names the address and `ecosystems.python.git_dependency` the spelling, and `v0.1.0` is cut. `tests/test_register_install.py` fails the build if the register pins a tag nobody cut, or one whose commit declares a different version |
| The names | `control-register`, `register-check`, `register-adopt` ([ADR 0031](adr/0031-the-plugin-is-named-for-the-register.md)) | **Met** — both moves landed before the consumer repository existed. Move 1 at register contract 27, move 2 at contract 28, so nothing wrong was written into a second repository |
| `project-init` installed | It is in the ee-skills marketplace and is **not installed here** | **Met** 2026-08-25 — installed from the `ee-skills` marketplace and run in the consumer repository, which is what produced the measurement. It is **no longer a prerequisite of anything**: the route does not run it ([ADR 0037](adr/0037-the-template-is-the-whole-devcontainer-step.md)), and the row is kept because the measurement it bought is what that decision rests on |

### Exit criteria — phase 4

The evidence for every row below is in
[`12-phase-4-review.md`](12-phase-4-review.md), which also records the fifteen
things the phase found that no criterion asked about — three of which made the
published route impossible to follow rather than awkward, and six of which came
out of judging the last row below rather than out of running the adoption.

**One criterion was retired rather than met, on 2026-08-26.** It read
*`project-init` and `register-adopt` compose without fighting over
`devcontainer.json`*, and this phase answered it: they do not. `project-init`
Step 4 replaces the template's digest-pinned image with the floating tag
`mcr.microsoft.com/devcontainers/python:3.12` — failing DEV-001's image pin, at a
version below the register's floor — and adds `node:1` beside the template's
`node:2`, leaving a lock file covering neither. The order is forced, because
`project-init` requires `devcontainer.json` to exist.

It is retired rather than open because
[ADR 0037](adr/0037-the-template-is-the-whole-devcontainer-step.md) took
`project-init` off the route: the shipped template produces a configured
`.devcontainer/`, and no document of this standard now instructs an adopter to
run it. A criterion asking whether two skills compose cannot be met by a route
that runs one of them, and leaving it open would gate this phase on a change to a
repository nobody here owns. Recorded here rather than deleted, because a
criterion that silently disappears is indistinguishable from one nobody noticed.

- [x] Every step the consumer repo needed is in
      [`08-adopting.md`](08-adopting.md) **before** the criterion below is
      judged. This phase is the one that measures the guide: anything the
      operator had to ask about, work out, or already know is a gap in it, and
      the fix belongs in the guide rather than in a reply to the question.
      **Closed 2026-08-25** with five gaps found and written: § 0.1, where the
      register comes from at all — the guide named a file nothing shipped and
      nothing told you how to obtain; § 2.0's install-cache path, since the path
      it gave is one only this repository has; the host Keychain values, without
      which `initializeCommand` exits 1 and the container never starts; the
      three uv placeholders and the rule that they are substituted unquoted; and
      § 0's warning that `gate-build` writes a file Claude Code treats as
      sensitive, which cost this phase two runs before it was recognised

- [x] **The adopter ends up with a pinned interpreter, not a floor.**
      **Closed 2026-08-25, and the decision is neither of the two the criterion
      offered.** No gate writes `.python-version` and the guide is not what
      carries it: `tool_versions_match_register` already fails a
      `source: toolchain` tool whose file is absent or untracked, so the
      register insists there is a pin without choosing anyone's interpreter —
      which it could not do anyway, since
      [ADR 0027](adr/0027-the-interpreter-is-a-pinned-tool.md) makes the file
      the authority and the register holds no version. Judged the way the
      criterion asks, by what the consumer repo has: with the file committed its
      container answers **3.14.7**, without it **3.13.5**, and removing it adds
      `python is sourced from .python-version, which is not tracked` to SUP-001's
      verdict. A gate writing the file from whatever the container resolved
      would have written 3.13.5 here, which is the accident
      [ADR 0028](adr/0028-the-support-floor-is-what-we-run.md) raised the floor
      to stop

- [x] The consumer repo reaches full Tier-1 conformance — **closed 2026-08-26**.
      `Eaiger-Ent/ee-standard-consumer` reports **12 passed, 0 failed**, one
      skipped by predicate (`terraform`), and 3/3 meta-controls, against register
      contract 30. CI-001 and GOV-001 both pass, which needed a ruleset GitHub
      actually enforces rather than one recorded in a file. The run exits `3`
      and not `0`, for one reason and the same one this repository has locally:
      SEC-003's remote blocks are answerable only inside a GitHub Actions job,
      so a developer's own token settles nothing about the credential CI
      carries. Both workflows are green on push and pull_request, and Dependabot
      has opened two pull requests of its own, so SUP-002 holds in fact
      ([`12-phase-4-review.md`](12-phase-4-review.md))
- [x] No step required knowledge held only by the author — judged after the row
      above, since the steps it would judge have not all been taken.
      **Closed 2026-08-26, and it did not pass as written**: re-walking
      [`08-adopting.md`](08-adopting.md) from the adopter's position — no
      plugin, no register, no container — found **six** steps carrying
      knowledge the guide does not. Two of them stand in front of everything
      else: § 0's first line is a slash command and nothing said how to install
      the plugin it lives in, and § 2.0 named four template placeholders,
      offered no substitution command, and gave no source at all for
      `{{UV_SHA256_AARCH64}}` — a value the consumer repository carries because
      the operator knew where uv publishes its checksums. The other four are a
      hand-written release tag one release stale, eighteen examples reaching
      the checker off `PATH` against § 2.3's own rule, `security
      add-generic-password` unmarked as macOS, and no way to see whether the
      pre-commit hook is installed. All six are closed in the guide and three
      are held by `tests/test_adopter_guide.py`, so they cannot silently
      return; the route itself needed no new artefact. What this does **not**
      claim is that someone who has never seen this repository has followed the
      repaired guide — the criterion's own wording admits no test can perform
      that, and Phase 6's re-adoption from the marketplace copy is the next
      occasion to try it ([`12-phase-4-review.md`](12-phase-4-review.md)
      § The last criterion)
- [x] Weakening a `narrowing-only` control is **caught** — the checker fails it,
      naming the control and what was weakened. **Closed 2026-08-26** in three
      shapes rather than one, each weakening made in the consumer repository and
      watched being caught, then reverted: a threshold raised above the
      register's (`line length ceiling is 400, above the register's 250`), an
      exemption hiding a tracked file (`'README.md' excludes 1 tracked file(s)
      the repository authors`), and a pin removed (`image reference is not
      digest-pinned`). Whether the *direction* is classified is Phase 5's, and
      § What moved to Phase 5, and why records the split rather than leaving the
      shortened sentence to be read as a quiet retreat
- [x] **The devcontainer template is obtainable without access to a private
      repo.** `ee-skills-incubator` is private and not a GitHub template; if that
      is the only source, the plan has an access-shaped single point of failure.
      Resolved by a `templates/devcontainer/` directory in the plugin, and
      **exercised 2026-08-25**: the consumer copied it out of a plugin install
      cache with access to no private repository at all

## Phase 5 — Staleness and the sweep

Wire the mechanism that keeps deployments current.

- `deploys.json` sidecars, with contract versions
- The `skill-update` widening (submission 2 in
  [`05-promotion.md`](05-promotion.md))
- A scheduled sweep running `register-check` across repos, reporting rather than
  fixing

### Exit criteria — phase 5

- [x] Every adopter-facing step this phase introduces is in
      [`08-adopting.md`](08-adopting.md) with its evidence — how a repository
      opts into the sweep, and how its owner reads a staleness report.
      **Closed 2026-08-27** with the sweep itself: § 4.4 is how the report is
      read, § 3.0 the pre-push locus, § 3.1 SEC-002's wiring, § 4.1 SUP-004's
      credential (it needs none, which is the surprising row), § 4.4 the
      declination record, and § 4.5 how a repository opts in — a `schedule:`
      line, a template to copy, and the two register edits that go with it.
      Checklist rows 7d, 7e, 11a and 11b carry the evidence

- [x] Bumping a gate's version *without* changing its output produces **no**
      redeployment recommendation
- [x] Bumping its contract version *does*
- [x] `skill-update` reports an owed deployment where every plugin is current,
      and does not print *Already done* over it.

      **Closed 2026-08-28.** The criterion needs two things true at once — an
      empty update list *and* an owed deployment — and the first is the hard
      half, because the marketplace moves. Three runs on one day each found a
      different plugin stale (`lint-md`, then `skill-preflight`, then
      `ee-skills-contribute`; the marketplace HEAD went `f75deae` → `85bab6d` →
      `d83e1c6`), so each took the Success path and said nothing about this.

      The state is **made** rather than waited for: run it once to empty the
      list, then again immediately. The second run found all seven plugins
      current, did not stop at Step 2.6, ran `register-check deployments` at
      Step 2.7, and printed **Deployment owed** naming five gates:

      ```text
      **Status:** Deployment owed

      **No changes made.** All installed ee-skills plugins are already at their
      latest versions. A deployment is outstanding, so this is not "already
      done":

        gate-build           UNRECORDED      contract 3   BLD-001, DEV-001
        gate-quality         UNRECORDED      contract 6   LNT-001, TYP-001, TST-001
        gate-repo            UNRECORDED      contract 4   CI-001
        gate-secrets         UNRECORDED      contract 6   SEC-001, SEC-002, SEC-003
        gate-supply-chain    UNRECORDED      contract 6   SUP-001, SUP-002, SUP-003, SUP-004
      ```

      The five gates are `UNRECORDED` under
      [ADR 0038](adr/0038-the-stamp-records-the-deployment-contract.md) and will
      be until each next deploys, which is why the *owed* half of the condition
      holds here at all. Two properties the run demonstrates and neither is
      incidental: the reconciliation is **through the checker**, so there is no
      second implementation to disagree with `register-check`; and the skill
      **deployed nothing** — it reported, which is the whole job
- [x] The sweep runs unattended and produces a report nobody has to ask for.
      **Closed 2026-08-27**, and as **two** scheduled runs rather than one.
      `register-check.yml` gained a `schedule:` trigger, because several
      controls can start failing with no commit — SUP-004 reads what a project
      published, GOV-003 expires on a date, and SEC-001's and SEC-003's remote
      blocks read platform state an administrator can change. The sweep itself,
      `.github/workflows/conformance-sweep.yml`, runs `register-check
      deployments` — the report with no other home — writes it to the job
      summary on every run, and keeps **one** tracking issue: opened when
      something is owed, edited while it persists, closed when it clears.

      It runs `deployments` and not the full audit **on purpose**: the audit
      needs gitleaks, markdownlint and the rest, and installing them here would
      be a second copy of the conformance workflow's setup, free to drift from
      it. The run that already knows how to install its tools is the run that
      got the schedule.

      It does not fail on findings — a red scheduled workflow is a notification
      people learn to dismiss, and staleness is reported and never enforced. It
      fails only when the sweep could not run
- [x] A repo that has never deployed is distinguishable from one deployed and
      current, and from one deployed and stale
- [x] Taking an upstream skill release is a supported operation with a recorded
      outcome: **redeployed**, or **declined with the disagreement named**.
      Refreshing a provenance stamp by hand — recording a redeployment that did
      not happen — is not one of the outcomes.

      **Closed 2026-08-27.** `deployment-decisions.yaml` at the repository root
      records a declination — the skill, the version, the reason, the ADR and an
      expiry — and `register-check deployments` reads it back
      ([ADR 0042](adr/0042-a-deploying-skill-reads-local-configuration.md)
      revision 2). The `lint-md@1.0.7` entry is the first, so the 1.0.6 stamp is
      now a decision with a reason on record rather than a chore nobody got to,
      and refreshing the stamp by hand is still not one of the outcomes.

      Two rules keep it a record rather than an opt-out, and both are checked:
      an entry covers **the version it names and no later one**, so a new
      release re-opens the question; and it **expires**, because one that never
      does is the `variance: justified` loophole contract 3 removed. Three ways
      the record can stop being true — expired, superseded by a deployment, or
      naming a skill nothing stamps — each **fail** the command, where a stale
      *deployment* only recommends. A malformed file exits `2` rather than
      reading as no declinations, which would report every declined deployment
      as a chore.

      **Extended 2026-08-28**, because the first of those two rules was stated
      and not applied. `lint-md` moved to 1.0.8 and the 1.0.7 entry went on
      reading as live at exit `0`, under a report printing *"a declination
      covers the version it names and no later one"* — the comparison was
      against the **stamp**, never against what is **installed**. There are now
      four ways the record can stop being true, and the fourth reads the
      harness's plugin inventory
      ([ADR 0043](adr/0043-a-declination-is-reconciled-against-the-installed-skill.md)).
      A run that cannot see one — CI has no plugins installed — reports the
      question as unreconciled rather than answering it in the repository's
      favour
- [x] A deployment behind because nobody has redeployed is distinguishable from
      one behind because the release would revert a narrowing this register
      holds. The first is a chore; the second is a decision, and reporting them
      the same way trains everyone to ignore both

- [x] A weakening of a `narrowing-only` control is **classified by direction**,
      not merely caught. Moved here from Phase 4 on 2026-08-24 with the skill
      that performs it — `register-variance`, named by
      [ADR 0031](adr/0031-the-plugin-is-named-for-the-register.md) — because
      neither it nor the classifier behind it exists, and a phase cannot test
      machinery a later phase builds (Phase 4 § What moved to Phase 5, and why)
- [x] The three known `UNCLASSIFIED` cases report as `UNCLASSIFIED`, not as a
      guess in either direction — a rule replaced by a differently named rule
      covering overlapping ground, a threshold whose direction depends on the
      metric's polarity, and a config expressed as executable code rather than
      declarative data ([`01-register-schema.md`](01-register-schema.md)
      § `variance`). Moved from Phase 4 with the criterion above: these are the
      cases where classification declines to guess, so they cannot be judged
      before something classifies.

      **Both closed 2026-08-27** at register contract 33
      ([ADR 0040](adr/0040-a-declined-classification-is-a-verdict.md)), by
      `register-check variance` and the `register-variance` skill that reports
      it. The three cases fall out of the mechanism rather than being handled
      specially, which is what makes declining a verdict rather than a
      fallthrough — and `variance.polarity` is what makes the second of them
      *fixable in one line of register* rather than a permanent shrug.
      `tests/test_variance.py` holds each case by name

- [x] **A version bump that leaves a checksum behind fails something.** Renovate
      proposed uv `0.12.5` → `0.12.6` (#74) and bumped the version literal at all
      four sites the register names, leaving all **three** sha256 digests at
      0.12.5's values — two in `.devcontainer/setup.sh`, one in
      `tools.uv.sha256`. Every check passed. What that PR would have merged is a
      container that cannot build: `sha256sum -c` exits `1` on a tarball whose
      digest names the previous release, which is the right behaviour and the
      last line of defence rather than the first. **Added 2026-08-26**, after
      fixing it by hand. `tool_versions_match_register` reconciles *versions*
      across `pinned_at`, and nothing reconciles a digest with anything: the
      register's own comment says a bump *"still needs a human"*, and no check
      makes one. Two halves, and only the first is free: an **offline** test that
      `.devcontainer/setup.sh`'s x86_64 `UV_SHA` equals `tools.uv.sha256` catches
      a half-finished human edit but not a bot that moved neither; catching the
      bot needs a **network** comparison against the release's published
      `<asset>.sha256`, which is a decision about whether that is a control and
      where it runs, not a test to add quietly. The aarch64 digest is compared by
      nothing at all and is already recorded that way
      ([`09-phase-1.5-review.md`](09-phase-1.5-review.md)).

      **Closed 2026-08-27** at register contract 34, with **both** halves and a
      control of their own, SUP-004
      ([ADR 0041](adr/0041-a-pinned-digest-is-checked-against-what-was-published.md)).
      The network half is what the row said was not free, and it is the only one
      that fails #74's actual shape: that bump left the register and `setup.sh`
      agreeing *with each other*, so the offline reconciliation passes it.
      Measured both ways before either was written.

      Two things the row did not anticipate. Both projects publish a **checksum
      manifest** — uv `sha256.sum`, gitleaks `gitleaks_<version>_checksums.txt` —
      so one mechanism reads both, where the per-asset `.sha256` the row names
      404s for gitleaks and would have covered one pinned tool of two. And a
      manifest lists every architecture, so **the aarch64 digest this row records
      as compared by nothing is now compared** — the register names it in
      `checksums.also` and the same fetch checks it.

      It is a new control rather than a block on SUP-001, and that is forced:
      SUP-001 declares a `pre-push` locus from contract 31, so a remote block on
      it would put a network fetch in front of every push and refuse one taken
      offline

- [x] **A developer can run what CI runs, before pushing, in one wired step.**
      Today they cannot, and the gap is not evenly spread: `uv run pre-commit run
      --all-files` covers ruff, mypy, gitleaks, markdown and three controls,
      while `uv run pytest` and a full `uv run register-check` have **no**
      pre-commit equivalent at all — `ci` is TST-001's only declared locus, and
      the pre-commit hooks run three controls of fourteen. So a green commit is
      silent about the two checks most likely to fail a pull request, and
      `CLAUDE.md` § Commands closes it by asking a person to remember four
      commands. **Added 2026-08-26**, after a PR's failures turned out to be
      hosted-runner acquisition rather than the change — which is a different
      problem, and made the absence of a local equivalent the expensive part.
      The shape is a **`pre-push` locus**, and it is a register change before it
      is a config one: `locus:` gains a fourth value, the controls that want it
      declare it, the contract bumps, and `gate-quality` writes and stamps the
      hook like any other. What must not happen is a script in `scripts/` that
      lists CI's steps — that is a second copy of the CI definition, free to
      drift from the workflow it mirrors. Judge it by deleting a passing test
      and watching the push refuse.

      **Closed 2026-08-27** over two slices, at register contracts 31 and 32
      ([ADR 0039](adr/0039-a-push-is-a-locus.md)). The judge passes: a deleted
      test refuses the push, measured rather than reasoned about.

      **What "what CI runs" means here, stated because the literal reading is
      unreachable.** Every control whose verification a developer's machine can
      *finish* now declares a local locus — TST-001, SUP-001, SUP-002 and
      SEC-002 gained `pre-push`; the rest already had `pre-commit`. Three things
      remain CI's alone and none of them is a gap this row can close: SEC-003
      and SEC-001 carry `kind: remote` blocks that answer only where the
      credential is, CI-001 is `locus: [remote]` outright, and the three
      meta-controls declare no locus at all because the schema forbids it. A
      hook that ran the full audit would exit `3` on every one of those and
      refuse every push, which is why the hooks name their controls. So a green
      push is a promise about the controls that name a local locus, and reading
      it as *CI will pass* is the substitution this register spends most of its
      asserts refusing

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

**The route out is a contract, not an argument** — [ADR 0042](adr/0042-a-deploying-skill-reads-local-configuration.md),
accepted 2026-08-27 and **shipped upstream in `lint-md@1.0.8`** the next day.
Both rows above are about **values**, and arguing values one at a time resolves
two of them and leaves the mechanism that produced them in place: the next
release picks a value this register disagrees with somewhere else. So a
deploying skill takes the values it writes as *input* — read from a
repository-local file keyed by skill name, absent file meaning today's
behaviour. Rows 1 and 2 are one line of local configuration each, and
`.claude/skill-config.yaml` here holds both.

#### Where the four rows stand at 1.0.9

Measured 2026-08-28 against the installed skill rather than its release notes,
because three of the four had moved and none of the three was announced as a
move. Re-measured against 1.0.9 the same day: the four rows below are unchanged
by that release — its `local-config.md` defaults are byte-identical and Step 1
still offers the overwrite prompt — and what 1.0.9 does move is #627, two rows
further down:

| Row | State | Evidence |
| --- | --- | --- |
| 1 `npx --no-install` | **Configurable, default unchanged** | `local-config.md` § What is read: `invocation` defaults to `npx --no-install markdownlint-cli2`; this repository sets the register's pinned path and, from 1.0.9, gets it at **every** locus — the PostToolUse hook was the exception and is #627 below |
| 2 `.claude/**` in `ignores` | **Configurable, default unchanged** | Same table: the default list still contains `.claude/**`. `ignores: []` set here means *ignore nothing*, because a present key replaces the default rather than merging with it |
| 3 the `grep -q "node_modules"` guard | **Closed** | 1.0.7's Step 2b guard is gone. 1.0.8 reads the file with a YAML parser and compares the `ignores` list against the configured one, in as many words: *"parsing the YAML rather than grepping it"* |
| 4 the overwrite prompt | **Open, unchanged** | Step 1 still offers *"Overwrite and reconfigure, or abort?"* with no reading of an `ee-control:` header, so accepting it drops the DOC-001 stamp |

Rows 1 and 2 are the ones whose shape changed rather than whose answer did, and
the distinction decides what submission 4 argues. The **value** is settled here
and only here: a repository that does not know to write
`.claude/skill-config.yaml` gets `npx --no-install` and an exemption over
`.claude/**`.

That does not retire rows 1 and 2 as things to raise. `ignores: []` set locally
stops `.claude/**` reaching *this* repository and not anyone else's, and
ADR 0019's argument is about any repository — a mechanism for expressing
disagreement is not a substitute for saying the thing is wrong. That sentence
was written while the mechanism was still a proposal, and it carries more weight
now that the mechanism has shipped, because a configuration key that answers the
complaint locally is the most comfortable possible reason to stop making it.

Two further rows were filed as
[#627](https://github.com/EqualExperts/ee-skills-incubator/issues/627):
`local-config.md` said `invocation` reaches *"every locus … the PostToolUse
hook"* while Step 3a was a plain `cp` of a script with the invocation
hardcoded, so the configured value never arrived there; and that shipped
script's shebang resolved from `PATH`, which `tests/test_toolchain_pin.py`
fails. **Both shipped in `lint-md@1.0.9` and #627 is closed** (COMPLETED,
2026-08-28). 1.0.9's Step 3a substitutes `invocation` into the copied script and
verifies the value landed, and the script it copies carries
`#!/usr/bin/env -S uv run python`. Measured here the same day: `/lint-md` at
1.0.9 wrote `.claude/hooks/md-lint.py` from the release unedited, and the four
divergences that file used to carry are gone. So this is the one row of the six
that closed by being fixed upstream rather than by being made configurable, and
it is **not** submission 4's any more.

The general rule this phase owes a mechanism to: **an exclusion is scoped by
what it is for, not by where it sits.** A path outside the repository is out of
scope by location and needs no exemption; a path inside it is in scope and an
exemption weakens the control. A skill that cannot express the difference should
be told so, not worked around locally.

## Phase 6 — Promotion

Per [`05-promotion.md`](05-promotion.md), in the order given there: the
`CONTRIBUTING.md` corrections first (small, independent, establishes contact),
then `control-register` plus the `governance` category, then the `skill-update`
amendment — plus the `lint-md` amendment identified in Phase 1.5 § F, and the
`skill-submit-new` layout amendment [ADR 0033](adr/0033-the-submission-tool-reaches-the-skills-by-symlink.md)
adds, which makes five. The last is deliberately last: the symlinks settle this
repository's own path, so the general fix is never on the critical path.

**None of them could be raised until Phase 4 had run** —
[`05-promotion.md`](05-promotion.md) § Before submitting anything, and it was
this repository's own rule rather than a maintainer's, which is what made it the
kind that gets quietly downgraded when everything else is finished. **It was not
downgraded: Phase 4 ran, and closed 6/6 on 2026-08-26.** The rule is recorded
here in the past tense rather than deleted, because the reason it held is the
reason the submissions are worth reading — the plugin has been deployed onto a
repository that did not author it, and the twenty-six things that found are in
[`12-phase-4-review.md`](12-phase-4-review.md). What is prepared, and what each
submission now argues, is the table in that section; the `lint-md` amendment in
particular is three rows smaller than the plan first described, for which see
§ Accepting an upstream skill release above.

### Exit criteria — phase 6

- [ ] [`08-adopting.md`](08-adopting.md) describes installing from the
      marketplace, and its § Status table is true on the day of release — a
      guide that still calls the shipped machinery "not built" is the mirror of
      one that describes tooling which does not exist

- [x] A repo-root `LICENSE` exists and is copied into the plugin —
      `check_plugin_license.py` fails without it, and `pyproject.toml` already
      declares Apache-2.0. Carried as debt since Phase 1.5, gating here.
      **Done 2026-08-25**: stock Apache-2.0 with the copyright line filled in,
      at the root and at `plugins/control-register/LICENSE`, held byte-identical
      by `tests/test_skill_links.py` — each plugin is copied into its own
      install cache, so a single root licence does not follow it, and two that
      disagree is a worse problem than one that is missing
- [x] How `/skill-submit-new` reaches skills that live in a plugin directory is
      decided and done. It resolves `<name>/SKILL.md` in the project or
      user-level Claude skills directory, and this repository's are in
      `plugins/control-register/skills/` ([`05-promotion.md`](05-promotion.md) §
      What the incubator actually holds).
      **Decided 2026-08-25** by
      [ADR 0033](adr/0033-the-submission-tool-reaches-the-skills-by-symlink.md):
      tracked symlinks at `.claude/skills/<name>`, so there is one definition
      and a second reference rather than a copy, and the amendment teaching the
      tool about plugin layouts is submission 5 rather than a blocker.
      `tests/test_skill_links.py` derives the link set from the plugin in both
      directions, so a ninth skill added without a link fails the build instead
      of being found missing while eight issues are being written
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
      rather than assert the conclusion. **Three rows at `lint-md@1.0.8`, not
      the four the plan first named**: the ADR 0020 invocation and the ADR 0019
      exemption, both now *defaults* rather than fixed behaviour, and the
      overwrite prompt that does not recognise a provenance header. The
      `node_modules` guard that matched prose is closed, measured rather than
      assumed, and the two filed as
      [#627](https://github.com/EqualExperts/ee-skills-incubator/issues/627) are
      closed too — shipped in `lint-md@1.0.9` on 2026-08-28 and taken here the
      same day — all of it enumerated in § Accepting an upstream skill release
- [ ] `control-register` installable from the marketplace **as one plugin**, with
      every skill in it — not as one plugin per skill
- [ ] The consumer repo re-adopts from the *marketplace* copy and still passes —
      proving the plugin works when installed, not only when developed
- [ ] **DOC-001 has a route for an adopter who cannot see `ee-skills`.** Added
      2026-08-25 by Phase 4, which found that the marketplace holding `lint-md`
      is **private**: every plan this repository produces rows DOC-001 as
      *dispatch elsewhere*, and elsewhere is somewhere an outside adopter cannot
      go. Phase 4 resolved it by copying the skill into the consumer's
      `.claude/skills/`, which is a copy of another plugin's skill living in the
      adopter's repository and going stale silently — recorded as what happened,
      not as a recommendation
      ([`12-phase-4-review.md`](12-phase-4-review.md) § 12). It is the same
      access-shaped single point of failure the devcontainer template was moved
      into this plugin to escape, and it belongs here because the answer is a
      publication decision rather than a code change

## What is deliberately not in scope

| Excluded | Why |
| --- | --- |
| Tier 2 and Tier 3 controls | Tier 1 must be proven end to end first. Adding controls is cheap once the machinery works and expensive before. **[ADR 0023](adr/0023-smallest-model-a-task-can-be-trusted-to.md)'s `AGT-001` is the first Tier-2 control queued behind this** — Accepted 2026-08-23, and deliberately unimplemented until Phase 4 has proven Tier 1. |
| Auto-fix | Notify, never redeploy. Proposed fixes are a Phase 5+ conversation, and only ever as a PR. |
| Non-GitHub platforms | `remote` verification is GitHub-shaped. Another platform means another assert set, which is a real project, not a flag. |
| Replacing `lint-md` or `devcontainer-check` | They work. The standard composes with them. `project-init` was in this row until 2026-08-26 and is not replaced either — it is simply not on the route ([ADR 0037](adr/0037-the-template-is-the-whole-devcontainer-step.md)). |

## Sequencing risk

The plan's dependencies are strict in three places and loose everywhere else:
Phase 0.5 gates Phase 1, Phase 1.5 gates Phase 2 (because Phase 2 copies the
assert layer into six skills), Phase 1 gates everything after it, and Phase 4
gates Phase 6. Phases 2 and 3 can overlap once the checker's assert interface is
settled.

The genuine risk is Phase 4 revealing something Phases 1–3 assumed. That is the
purpose of Phase 4, and discovering it there costs a rework; discovering it after
promotion costs a marketplace amendment and everyone who already installed it.
