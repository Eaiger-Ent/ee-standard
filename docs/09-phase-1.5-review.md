# Phase 1.5 — the review, and how it closed

A closed record. Phase 1.5 finished on 2026-08-18 with all 25 exit criteria met;
this document is what it found and what each fix was, kept because the code still
cites it.

**`§ A` through `§ G` anywhere in this repository — in an assert's docstring, a
test, an ADR — refer to the sections below.** They were sections of
[`04-build-plan.md`](04-build-plan.md) until 2026-08-18, and were moved here when
that file had grown to 65k with two thirds of it describing finished work. The
build plan is the list of *outstanding* work; a completed phase's forensics
diluted the signal it exists to carry.

The section letters are unique across the project, so the citations did not
change and did not need to.

## Why this phase existed

Phases 0, 0.5 and 1 closed their exit criteria. A review of the result found that
several were met in letter rather than in substance, and — more seriously — that
the checker's failure modes pointed the wrong way. In multiple places it either
**aborted without producing any verdict**, or **reported green for something it
never examined**. For a conformance tool those are the only two failures that
matter.

The phase existed because of one line in Phase 2: *"Gates and checker share one
assert implementation — verified by there being one copy."* Every defect below
would have been copied into six `gate-*` skills and become six times more
expensive to correct.

## The findings

### A — Verdicts that overstate what was checked

| Defect | Now | Required |
| --- | --- | --- |
| GOV-002 cannot fail in CI. `_previous_content` falls back `origin/main` → `main` → `HEAD`, so once a growth is committed, "previous" *is* the grown file. Confirmed: growth uncommitted → FAIL; same growth committed → PASS | Catches dirty worktrees only | Compare against the default branch's merge-base, and fail closed when no comparison point exists |
| DOC-001 asserts only that a config file exists. Confirmed: `line_length: 100000` plus a 1600-character line passes; deleting the CI step, the pre-commit hook or the editor hook also passes | **Closed** at contract 5 — `markdown_gate_wired_at_all_loci` | A `doc_gate_wired_at_all_loci` assert mirroring LNT-001's, plus an assertion on the ceiling the register names |
| A control whose tool is missing reports FAIL. `hadolint`, `checkov` and `tflint` are absent from this container, so any repo with a `Dockerfile` or a `.tf` gets "command not found" | "Cannot verify" is indistinguishable from "violates" | `UNCLASSIFIED` — the verdict already exists for exactly this |
| GOV-001 derives reachability from a substring test, and any bare `standard-check` step short-circuits every control | `pip install standard-check` would mark all controls reachable | Match invocations, not substrings; see § Decisions for how loudly it should admit being partial |
| `SKIPPED (no credentials)` leaves the exit code at 0 | CI is green while SEC-001's remote half and all of CI-001 are unverified | See § Decisions |

### B — Runs that abort instead of reporting

A `kind: command` block that explodes degrades to FAIL. A `kind: file` assert
runs in-process, so one exception kills the run before anything is rendered.

Confirmed triggers: a tracked file deleted from the worktree (`git ls-files`
still lists it); `repos:` with nothing under it; `updates:` empty;
`"features": null`; `customizations.vscode: null`; a malformed `pyproject.toml`;
unparseable YAML; and — most likely to meet a real repo — **a `tsconfig.json`
containing a trailing comma**, which is legal JSONC that `tsc` accepts and
`strip_jsonc` does not handle. `YAMLError` is guarded in the register loader and
nowhere else.

Two more crashes: `words.index("install")` raises `ValueError` on
`npm install-ci-test` (a real npm command whose `\b` boundary the regex
matches), surfacing as a SUP-001 failure whose operator-facing message is a
Python traceback; and if `git` is absent from `PATH` the checker crashes rather
than reporting.

**Required:** every assert returns a verdict. A read or parse failure is a FAIL
naming the file and the reason, and the run continues to the next control.

### C — Environments that silently look conformant

| Defect | Confirmed behaviour |
| --- | --- |
| `_git_ls` swallows any non-zero `git` exit and returns an empty set, so every file predicate goes false | A non-git directory holding a root-running `Dockerfile`, an `AWS_SECRET_ACCESS_KEY` in a workflow and a `pyproject.toml` reports eight predicate skips and exits 0. The reason given — "predicate not satisfied" — is false; the files are on disk. A typo'd `--repo` path behaves identically. This is also the path taken when git refuses a repo for dubious ownership |
| `gitleaks detect` is git-history-only | In a non-git directory it prints "0 commits scanned … no leaks found" and exits 0, so SEC-001 shows a green tick for a scan that examined nothing |
| The `container` predicate is an exact basename match; `repo.dockerfiles()` accepts `Dockerfile.*` and `*.Dockerfile` | A repo whose only container file is `Dockerfile.prod` ending in `USER root` reports `BLD-001 SKIPPED (predicate)`, while the assert called directly returns FAIL. A skip hides a violation the checker can already detect |
| `runner.py` uses `shlex.split` with no shell | `run: "true && false"` becomes `['true', '&&', 'false']` and exits 0. The schema accepts such strings, so a future `pytest && mypy` would silently check only pytest |

### D — Assert precision

False negatives — the assert passes while the control's `enforces` does not hold:

| Control | Input that passes |
| --- | --- |
| SEC-002 | `aws-access-key-id: ${{ secrets.PROD_KEY }}` — the scan is a case-sensitive substring match over seven uppercase names |
| TST-001 | `pip install pytest==8.0.0` with no test invocation; and a `workflow_dispatch`-only workflow, because `on:` is never read (theme T-3) |
| SUP-003 | A job-level reusable workflow `uses: owner/repo/.github/workflows/x.yml@main` — only `jobs.*.steps` is walked |
| LNT-001, TST-001 | `continue-on-error: "true"` as a string, and the `\|\| :` idiom, both outside the suppression set |
| TYP-001 | `strict = true` alongside `[[tool.mypy.overrides]] module=["*"] ignore_errors=true` |
| SUP-002 | `renovate.json` containing `{"enabled": false}` — any renovate filename is accepted unparsed |
| SUP-001 | An unpinned `requirements.txt` counted as a lockfile; a TS repo with no workflows at all passing the frozen-install check vacuously; `pip3`, `poetry`, `pdm` unmatched |
| BLD-001 | `ARG USERNAME=root` with `USER ${USERNAME}` — the literal token is compared, never expanded |

False positives — conformant repos that fail:

| Input | Cause |
| --- | --- |
| `pip install \` with the pinned package on a continuation line | Physical lines are iterated |
| CI that lints via `pre-commit run --all-files` | A literal `ruff check` string is required |
| mypy configured in `mypy.ini` | Only `[tool.mypy]` is read |
| An editor locus via `.vscode/extensions.json`, no devcontainer | The check demands a devcontainer extension entry, inventing a hidden LNT-001 dependency on DEV-001's artefact |
| `npm run test`, `make test`, `tox`, `gradle`, `rspec` | The test-command regex lists six spellings |
| A devcontainer using `build.dockerfile` instead of `image` | DEV-001 demands an `image` key; the Dockerfile's own `FROM` pin is never checked |
| `uses: docker://alpine@sha256:<64 hex>` | 40 hex characters are required |

### E — Register and schema gaps

**No tool version exists anywhere in the register**, while four documents state
that one does — `03-devcontainer.md`, `06-devcontainer-setup.md`,
`00-concepts.md` and a comment in `setup.sh` all describe pinning "from the
version recorded in the register". The consequence is pin-many-and-hope:
`markdownlint-cli2@0.23.2` in four places, gitleaks `8.30.1` and its checksum in
two each, `uv==0.12.5` in two, none authoritative. A comment in `lint.yml`
instructs humans to "change all three together" where there are four. Separately,
`02-skill-family.md` § Version policy describes a per-control
`pinned`/`floating-minor`/`latest` field that exists in neither the schema doc
nor the register — and because the validator accepts unknown keys, adding it
would be silently ignored rather than rejected.

**`variance` is read by no code path**, and one of its four values cannot be
implemented as specified: SUP-003 and IAC-001 are `tier: 1` with
`variance: justified` and `baseline: null`, but `00-concepts.md` says a justified
weakening *is* a baseline entry, and the validator rejects any Tier-1 control
carrying a baseline. The mechanism that stops `justified` becoming a loophole is
structurally unreachable for both controls that use it. `CLAUDE.md` compounds it
by listing only two of the four values. `UNCLASSIFIED` is likewise unreachable
from every code path.

**The `kind: command` / `kind: file` taxonomy has been subverted.** **All eight**
`standard-check assert …` blocks are file-shape assertions declared as commands —
not five of seven, as this section previously recorded; the count was re-measured
on 2026-08-17 against the register's own loader. ADR 0002 even describes SEC-002
as "a file-shaped assertion" while the register calls it a command.

This is not cosmetic — GOV-001 derives reachability from `kind: command` blocks
and ignores `kind: file` ones, so the miscategorisation decides that control's
verdict. Measured against the register as it stands, GOV-001 sees:

| What GOV-001 sees | Controls | Consequence |
| --- | --- | --- |
| The bare token `standard-check` | SEC-002, SUP-001, SUP-003, LNT-001, TYP-001, TST-001 | Six blocking controls collapse to one indistinguishable token; any CI step containing that substring marks all six reachable |
| No `kind: command` block at all | SUP-002, DEV-001 | Blocking, `ci`, verified only by file asserts. `commands` is empty, so `reached` is always false and they can pass only via the bare-invocation short-circuit |
| A distinct tool token | SEC-001, BLD-001, IAC-001, DOC-001 | The only four where the reachability test measures anything |

So neither branch of GOV-001 measures reachability: with a bare `standard-check`
step every control passes vacuously, and without one SUP-002 and DEV-001 fail
however well they are wired. This is the control the register calls its
highest-value one, and the guard against theme **T-3**.

**Demonstrated on 2026-08-17, not merely reasoned about.** Adding exit-code
handling to the workflow's Conformance step — `… && status=0 || status=$?`,
which changes nothing about what runs — flipped GOV-001 from PASS to
`FAIL: blocking controls with no reachable CI step: SUP-002, DEV-001`. The old
pattern required the CI line to be *exactly* the invocation, so the verdict
depended on shell punctuation rather than on whether anything was checked. The
full-run half is fixed; the per-control substring test remains.

**The checker has become a second source of truth** for rules recorded nowhere
in the register: ruff/eslint/mypy/pytest as the mandated tools, the
`charliermarsh.ruff` extension ID, the test-command spellings, a Python-and-Node
lockfile map that lets Go, Rust and Java repos pass SUP-001 with no lockfile, the
Dependabot ecosystem spellings, the seven-name cloud-key list, the suppression
patterns, the predicate grammar, the `GOV-\d{3}` pattern, `rationale_adr` file
existence, strict semver, and the Tier-1 baseline rule. Phase 2's shared assert
implementation inherits all of it, so the boundary needs deciding here: what
belongs in the register, and what is legitimately the checker's business.

The lockfile map is the measured harm: it knows Python and Node, so a Go, Rust or
Java repository with no lockfile passes SUP-001. That exemption was never
decided — it is which dictionary keys someone wrote — and because the register
does not record it, no review and no `review_by` date will ever surface it.
Recorded as [ADR 0018](adr/0018-register-checker-boundary.md).

### F — Deployment and provenance

`lint-md` owns both `.pre-commit-config.yaml` and `.github/workflows/lint.yml`,
and both were hand-edited in Phase 1. Its own templates write
`actions/checkout@v6` (a floating tag, failing SUP-003) and an unversioned
`npm install -g markdownlint-cli2`, so a re-run reverts the pins and turns
SUP-003 red. That implies a **fourth promotion submission** — an amend against
`lint-md` — which [`05-promotion.md`](05-promotion.md) § Submission order does
not list.

Three of the four `lint-md`-deployed artefacts carry no `ee-control:` stamp,
though `CLAUDE.md` states as fact that they do. The one that has a stamp reads
`register: v0.1.0` against a v0.2.0 register, making the repo's only deployed
artefact stale by the definition in `00-concepts.md` — and the stamp format
carries no contract number, so the documented noise control cannot be evaluated
from a stamp at all.

**Closed.** All five artefacts are stamped, the format now carries
`register-contract:`, and each stamp records the hand-edits made since
deployment — which is the amend's scope written down rather than remembered.
The amend was raised on 2026-08-18 as
[ee-skills-incubator#530](https://github.com/EqualExperts/ee-skills-incubator/issues/530),
the fourth submission Phase 6 tracks. It is a submission, not a merge: until a
maintainer ships it, re-running `lint-md` here still reverts the pins, so the
deployment stays un-refreshable and Phase 6's criterion holds the follow-up.

That last clause is a **Phase 5 dependency, not a cosmetic one**. Phase 5's first
two exit criteria — a version bump must produce no redeployment recommendation, a
contract bump must — are the whole noise argument expressed as a test, and
neither can be evaluated against a stamp that does not carry the contract number.
Fixing the format here is what makes Phase 5 testable; deferring it means
discovering the gap in the phase that depends on it.

Phase 1 also introduced an unrecorded weakening: `extend-exclude = [".claude"]`
in `pyproject.toml` and `.claude/**` in the markdownlint config are what
`00-concepts.md` names as weakening ("adding an ignore path"), applied to
`narrowing-only` controls whose `baseline: null` the schema doc says means no
exemptions are possible.

**Closed by removal.** Both are gone, and the file behind them conforms. The
count of four artefacts above was itself a consequence of the exclusion: there
are five, and `.claude/hooks/md-lint.py` was invisible to a search that ruff had
been told to skip. An exemption hides more than the rule it exempts.

### G — Tool version reconciliation

Closed at register contract 4, except for one part that turned out to rest on a
tool nobody had checked was installed.

**What holds now.** The register's `tools:` section records a `source` per tool
rather than a bare version, because "the version exists in exactly one place" is
not achievable — a tool installed by a package manager necessarily appears in
that manager's manifest too. Two sources:

| `source` | Meaning | Duplication | Here |
| --- | --- | --- | --- |
| `lockfile` | A package manager owns the version; every locus invokes the tool through it | **Eliminated** | `markdownlint-cli2`, via `package-lock.json` |
| `literal` | Nothing owns it; the version lives in the register and each locus repeats it | Reconciled, not removed | `uv`, `gitleaks` |

`markdownlint-cli2` went from five hand-kept pins to the manifest/lockfile pair
that owns it. `uv` bootstraps the Python environment so it cannot come from it,
and `gitleaks` is a release binary — neither has an ecosystem this repo locks.

**The finding.** The `literal` half was written to rely on Renovate custom
managers: a `# renovate: datasource=…` annotation above each literal, so one PR
updates every site together. **Renovate is not installed on this repository** —
no config, no bot pull requests. What *is* running is Dependabot (PR #1, bumping
`actions/checkout`), and Dependabot has no equivalent of a custom manager: it
updates ecosystems it recognises and will not touch `GITLEAKS_VERSION=8.30.1` in
a shell script or `uv==0.12.5` in a workflow step.

So the annotations are syntactically correct and currently inert. `uv` and
`gitleaks` are held by exactly one mechanism — `tool_versions_match_register`
failing the build when the copies disagree. That catches drift between loci; it
does not propose the upgrade, so nobody is told when a new version ships.

This is the same defect already recorded under § Carried debt as
title-versus-mechanism drift: *"SUP-002's title is broader than what passes,
since the npm and curl pins are precisely the two Dependabot cannot propose."*
That entry predates this work and is now the live constraint rather than a
footnote.

**Actions, one of which must be chosen.** This is not deferrable past Phase 2:
the shipped devcontainer template inherits whichever pattern is chosen, and
every consumer repo in Phase 4 inherits it again.

| Action | What it costs | What it buys |
| --- | --- | --- |
| **1. Install Renovate** on the org or this repo | An app installation and a `renovate.json`; optionally retires Dependabot so one bot runs | The annotations already written start working, with no further change. Cheapest path to a proposing mechanism |
| **2. Adopt `mise`** — a `mise.toml` pinning `uv` and `gitleaks`, read by the devcontainer and by `jdx/mise-action` in CI | New tooling in the template, and a devcontainer feature to install it | Collapses both literals into one authority that a bot *can* update, and gives consumer repos a toolchain file rather than pins scattered through scripts. The answer that scales to Phase 4 |
| **3. Accept it** | Nothing | The two tools stay drift-checked but never auto-proposed. Honest, provided SUP-002's title is narrowed to match, so the register stops claiming a coverage it does not have |

Recommended: **1 now, 2 when the Phase 2 template is built.** Option 1 makes the
existing annotations live for the cost of an install; option 2 is the shape the
template should ship, because a consumer repo that pins tools inside `setup.sh`
reproduces this problem in every repo that adopts the standard. Option 3 is only
acceptable with the SUP-002 title change, because leaving the title as it stands
is the register asserting a mechanism that is not running — theme **T-3** inside
the register itself.

**Correction, 2026-08-18: option 2 is not an escape from option 1.** The table
above reads as though `mise` were an independent route to a proposing mechanism.
It is not. Dependabot has no `mise` manager; Renovate does. So adopting `mise`
replaces two custom managers with one native one — a real simplification, and
still the right shape for the template — but it does **not** remove the need for
Renovate to be installed. Whichever of 1 and 2 is chosen, the same app
installation is the precondition. Only option 3 avoids it, by giving up the
mechanism and narrowing the title to say so.

**Chosen 2026-08-17: action 1**, with action 2 kept for the Phase 2 template as
recommended. What that decision has and has not delivered:

**Done — the configuration.** `renovate.json` exists at the repository root,
enabling `custom.regex` and **nothing else**. Two custom managers read the
`# renovate:` annotations: one for PyPI literals, one for GitHub-release
literals with `extractVersionTemplate` stripping the tag's leading `v`. The
register's own `tools:` table is annotated too and is named first among the
managed files — it is the authority, so a proposal that bumped the loci and left
it behind is a proposal `tool_versions_match_register` rejects. The gitleaks
rule carries `prBodyNotes` telling the reviewer to update the four checksums the
bot cannot compute; an unrevised checksum fails the install step rather than
passing silently, which is the right direction but still a red build, so it is
said in the PR body rather than left to be discovered.

**Both bots run, and deliberately do not overlap.** Renovate covers only what
Dependabot cannot see — the two version literals. Dependabot keeps the four
package ecosystems it understands. Widening `enabledManagers` would duplicate
every ecosystem proposal; retiring Dependabot before the Renovate install is
confirmed would leave nothing proposing anything, which is the § G trap with the
bots exchanged. `dependency_update_config_covers_all_ecosystems` was corrected
to see this: a `renovate.json` narrowed to custom managers is no longer read as
blanket coverage on the strength of its filename, and the repo would fail
SUP-002 if `.github/dependabot.yml` were deleted while it stands.

**Done — the check that the mechanism is not inert.** The § G failure was an
annotation that was correct and read by nothing. A manager whose regex matched
no line would fail in exactly the same silent way, so
`tests/test_renovate_managers.py` compares the annotations, the manager patterns
and the register against each other: every annotation is matched by some
manager, every match extracts the version the register records, and every
`literal` tool is annotated at the register **and** at every locus that pins it.
The first of those failed on its first run — the annotations are indented inside
a YAML mapping — which is the discrimination the test exists to prove.

**Closed 2026-08-18.** The app was installed on this repository and the
mechanism is confirmed running, not assumed: Dependency Dashboard
[#14](https://github.com/Eaiger-Ent/ee-standard/issues/14) reports `regex (6)`
and no other manager. Renovate auto-closed its own onboarding PR once
`renovate.json` reached the default branch, which is what proves it read this
config rather than the default one it proposed.

**Two things this taught, worth keeping.**

*Config on a branch is config that does not exist.* Renovate reads from the
default branch. While `renovate.json` sat unmerged on a feature branch the app
saw an unconfigured repository and opened an onboarding PR carrying a **default**
config — every manager enabled, duplicating Dependabot exactly as
`enabledManagers` was written to prevent. Merging that PR would have installed
the opposite of the intent. It must be left alone rather than closed, because
closing an onboarding PR unmerged is Renovate's signal to disable itself.

*The count is the check.* The dashboard first reported **five** managed sites
where the register implies six. That single digit found a missing annotation in
`.devcontainer/setup.sh` and, behind it, `tool_versions_match_register`
comparing gitleaks at no locus at all while reporting PASS — the § A defect, in
the assert a Phase 1.5 criterion had already been ticked on. The count is now
derived from the register and asserted in `tests/test_renovate_managers.py`, so
the next missing annotation is a failing test rather than a number someone
happens to read.

### Decisions required before Phase 2

These are not code, and they are not the author's to settle alone. Each is
recorded as an ADR — the ADR holds the options, the recommendation and the
consequences, so this table stays an index and does not become a second copy of
the reasoning. Ratifying one means moving it to `Accepted` via `/adr-approve`.
All five are now settled; none is yet fully implemented, and the exit criteria
below — not this table — track that.

| Decision | Recorded in | Why it cannot be deferred |
| --- | --- | --- |
| This repository cannot satisfy CI-001 or SEC-001's remote half. `GET /rulesets` returned 403 ("Upgrade to GitHub Pro or make this repository public"), `security_and_analysis` was null, and `main` reported `protected: false` | [ADR 0014](adr/0014-satisfying-remote-locus-controls.md) — **Accepted and implemented** 2026-08-17 | Settled: the repository is public and both controls stay Tier 1. The capability is confirmed live (`GET /rulesets` now returns `[]`). Two follow-on acts remain — create the ruleset, enable push protection — both blocked on a PAT lacking `Administration: write`, not on any decision |
| `main` was unprotected, so every blocking gate was bypassable | [ADR 0015](adr/0015-interim-branch-discipline.md) — **Superseded** by [ADR 0008](adr/0008-protected-default-branch.md) 2026-08-17, never ratified | Closed by enforcement rather than by convention: the ruleset makes CI-001 mechanical, so the proposed stopgap was redundant before it was decided |
| Whether `SKIPPED (no credentials)` should leave a non-zero exit, a distinct exit code, or a warning | [ADR 0016](adr/0016-exit-codes-for-unverifiable-controls.md) — **Accepted** 2026-08-17, not yet implemented | Decided: exit `3` for a run with no violation but something it could not verify, `1` for a verified violation, `0` only when every applicable control was verified, and `--require-complete` promotes `3` to `1`. Predicate skips stay `0`. Phase 2's gates inherit these semantics, so the code follows before they are written |
| How a partially-implemented control reports its own incompleteness | [ADR 0017](adr/0017-partial-verification-is-reported.md) — **Accepted** 2026-08-17, not yet implemented | Decided: the register — not the checker — declares a verification block partially implemented with an expiry, and the report renders the computed verdict plus a `partial:` line. The schema addition carries a `register_contract` bump, so it lands before Phase 2's skills read that contract |
| Which verdict-deciding rules belong in the register and which are legitimately the checker's business | [ADR 0018](adr/0018-register-checker-boundary.md) — **Accepted** 2026-08-17, **implemented** over contracts 3, 5 and 6 | Decided by one test: could a reasonable EE repository need this to differ without changing the checker? Yes → the register (mandated tools, lockfile ecosystems, test-command spellings, cloud-key names, Dependabot ecosystems, suppression patterns). No → the checker, with a recorded reason (predicate grammar, ID pattern, semver strictness, `rationale_adr` existence, the Tier-1 baseline rule). The move batches into ADR 0017's `register_contract` bump |

## How each criterion closed

The exit criteria as they stood when the phase closed, with the evidence for
each tick. [`04-build-plan.md`](04-build-plan.md) now carries these as short
checkable statements; the reasoning is here.

Keeping it matters more than where it lives. Three criteria in this phase were
ticked and later found false — `gitleaks` compared at no locus, `remoteUser`
read by no assert, and a feature-preference ladder that would have made an
install worse. The evidence is what makes the next tick trustworthy.

### The criteria, as they read on closing

- [x] GOV-002 fails on a baseline grown in a **commit**, not only in a dirty
      worktree — it now compares against the merge-base with the default branch
      on a branch, and the parent commit on the default branch itself, and names
      which reference it used
- [x] No assert can abort the run: a read or parse failure is a verdict naming
      the file, and later controls are still evaluated. The confirmed triggers
      are fixed at source too — trailing commas in JSONC, `None`-valued config
      sections, and `npm install-ci-test`
- [x] A target that is not a git repository is an error, never a page of
      `SKIPPED (predicate)` verdicts. `schema` and `explain` are exempt: they
      read the register, not the repository
- [x] A register `run:` string containing a shell operator is either rejected at
      schema time or executed correctly — never silently truncated. Rejected at
      schema time: giving the register a shell would make every `run:` string an
      injection surface for no gain the register needs
- [x] The `container` predicate and BLD-001's assert agree on what a Dockerfile is
- [x] DOC-001 verifies its three loci and the ceiling its `enforces` names —
      `markdown_gate_wired_at_all_loci` replaces the existence check at register
      contract 5. The ceiling may narrow and never widen, per the control's
      `narrowing-only` variance, and all three declared loci are read. The
      ceiling, the tool name and the editor extension id come from the verify
      block's `args:` (ADR 0018, second pass) rather than from the checker. Its
      first run failed this repository, correctly: DOC-001 declares an `editor`
      locus and the devcontainer installed only `charliermarsh.ruff`, so the
      locus had never been wired at all — a gap the existence check could not
      have found
- [x] The exit code distinguishes "no credentials" from "all clear", per
      [ADR 0016](adr/0016-exit-codes-for-unverifiable-controls.md) — `3` for
      unverified-but-no-violation, `1` for a verified violation, `0` only for a
      fully verified run, and `--require-complete` promotes `3` to `1`. A
      predicate skip still exits `0`. This repo now reports exit `3`: nine
      controls pass, none fails, and CI-001 and SEC-001 are unverified.
      The `Standard` workflow **tolerates `3` and nothing else** until Phase 3,
      per ADR 0016 § Ratified tolerance — the flip to `--require-complete` is
      held by a Phase 3 criterion, because `standard-check` is a required check
      and a hard failure here would freeze the branch against its own repair
- [x] A control whose tool is absent reports `UNCLASSIFIED`, distinct from FAIL,
      and a meta-control that cannot reach a comparison point does the same —
      GOV-002 with no resolvable HEAD is `UNCLASSIFIED`, not a fabricated
      violation. `UNCLASSIFIED` now has producers, so Phase 1's re-opened
      criterion is no longer vacuous
- [x] GOV-001 matches **invocations, not substrings**: a step is evidence for a
      control only if it actually runs that control's verification. Both
      degenerate readings in § E are gone. The full-run case matches an
      invocation — a command word at the start of a command, optionally behind
      `uv run` — so `pip install standard-check` is no longer evidence that
      anything is checked, and shell punctuation around the invocation no longer
      changes the verdict. The per-control case matches each block's own tool or
      assert name, so the six controls that collapsed to the token
      `standard-check` are distinguishable and a control verified only by file
      asserts can be reached on its own evidence
- [x] Every verification block declares the `kind` it actually is. No file-shape
      assertion is declared `kind: command`, and GOV-001 can find a blocking `ci`
      control reachable through its `kind: file` blocks — otherwise SUP-002 and
      DEV-001 remain permanently unreachable by construction. All eight moved to
      `kind: file` at contract 3; the two assert modules now share one namespace,
      so which module implements an assertion is no longer a register fact
- [x] Every row in § D has a test that fails before its fix and passes after —
      `tests/test_section_d.py`, one test per row. Verified by restoring the
      pre-fix assert modules and re-running: all 18 fail, then all 18 pass. One
      of them originally passed against the old code for a reason unrelated to
      its row (the vacuous python branch caught it), and was strengthened until
      it discriminated — which is the failure mode this criterion exists to rule
      out
- [x] **Every tool has one recorded authority, and every locus is verified
      against it.** **Re-opened and re-closed 2026-08-18**: it was ticked while
      `gitleaks` was compared at *no* locus. `tool_versions_match_register`
      matched the tool name case-sensitively, so `GITLEAKS_VERSION=8.30.1` — the
      spelling used at both loci that install it — never matched `gitleaks`.
      Drifting `setup.sh` to `9.99.9` left the assert reporting PASS, and its
      own message said "2 version pin(s)" where the register implies four. Fixed
      by matching case-insensitively **and** by failing when a `literal` tool is
      pinned at no known locus: silence reading as a pass is the verdict
      overstating what was checked (§ A), which is what this phase is for. Now
      4 pins, and drift at either gitleaks locus fails.
      The original wording — "no version string exists in more
      than one place" — is not achievable and was ticked while plainly false,
      which is the over-tick this plan exists to catch. A tool installed by a
      package manager necessarily appears in that manager's manifest as well,
      so "one place" was never the right target. The register's `tools:`
      section now records a `source` per tool:
      `lockfile` (a package manager owns the version; the loci invoke the tool
      through it, so there is nothing to keep in step) or `literal` (nothing
      owns it; the version lives in the register and each locus repeats it).
      `tool_versions_match_register` verifies both cases
- [x] Tools that *can* have their duplication eliminated, do.
      `markdownlint-cli2` moved to `package-lock.json` as its authority:
      `package.json` declares it, every locus runs `npx --no-install
      markdownlint-cli2`, and the four hand-kept pins are gone — including the
      pre-commit mirror's `rev:`, which was a copy nothing compared. Register
      contract 4, because DOC-001's `verify` changed
- [x] The two remaining `literal` tools are reconciled by machine, not by a
      human remembering — **closed 2026-08-18**. § G action 1 was chosen, the
      Renovate app was installed, and the mechanism is confirmed running rather
      than assumed: Dependency Dashboard
      [#14](https://github.com/Eaiger-Ent/ee-standard/issues/14) reports
      **`regex (6)`** — `uv` and `gitleaks` each managed at the register and at
      both loci that pin them — and reports no other manager, so Dependabot's
      four ecosystems are not duplicated. Renovate closed its own onboarding PR
      once `renovate.json` reached the default branch, which is the confirmation
      that it read *this* config rather than a default one.
      The verification earned its keep. The dashboard first reported **five**
      sites where the register implies six, and that one-digit discrepancy found
      two defects: a missing annotation in `.devcontainer/setup.sh`, and — far
      worse — `tool_versions_match_register` comparing gitleaks at **no** locus
      while reporting PASS. Both fixed; see the authority criterion above, which
      was re-opened and re-closed for it
- [x] SUP-002's title matches what it verifies — **closed 2026-08-18** by the
      mechanism existing, not by narrowing the words. It claims dependency
      updates are proposed automatically; Dependabot proposes the four package
      ecosystems and Renovate proposes the two literals, which between them is
      every dependency this repository pins. The title needed no change because
      it is now true. Ticking it before the install would have been the register
      asserting a mechanism that was not running — theme T-3 inside the register
      itself, and the reason this box stayed open through three sessions
- [x] `variance: justified` is implementable or removed from the vocabulary, and
      `CLAUDE.md` lists whatever survives — **removed** at contract 3, with
      `free`. `justified`'s anti-loophole mechanism was that a weakening becomes
      a baseline entry, and the validator rejects any Tier-1 baseline, so it was
      structurally unreachable for both users. SUP-003 and IAC-001 are now
      `narrowing-only`, which is stricter, so nothing was loosened
- [x] Every `lint-md`-deployed artefact this repo has edited carries a
      provenance stamp, and the amend submission against `lint-md` is raised —
      raised 2026-08-18 as
      [ee-skills-incubator#530](https://github.com/EqualExperts/ee-skills-incubator/issues/530).
      **Five** artefacts are stamped, not four:
      `.markdownlint.yaml`, `.markdownlint-cli2.yaml`, `.github/workflows/lint.yml`,
      `.claude/hooks/md-lint.py`, and — at the hook rather than at the top of the
      file — `.pre-commit-config.yaml`, which holds hooks for five controls and
      whose whole-file stamp would have claimed the other four. Each names the
      hand-edits made since deployment, which is what gave the amend a written
      scope rather than a remembered one. The submission proposes
      `package-lock.json` as the single authority at every locus, a SHA-pinned
      `actions/checkout`, and a `ruff`/`mypy --strict`-clean hook script
- [x] The stamp format carries the **register contract number**, not only the
      register version, so Phase 5's first two criteria are evaluable from a
      stamp. Format is now
      `ee-control: ID  ee-skill: name@version  register: vX.Y.Z  register-contract: N`
      — the version moves for a typo in a comment, the contract only when what
      gets deployed could differ, so a stamp carrying only the version goes
      stale on every release and tells a reader nothing. `tests/test_provenance_stamps.py`
      checks that every stamp parses, names a control the register defines, and
      does not claim a contract the register has not reached. It deliberately
      does **not** fail a stale stamp: staleness is a redeployment
      recommendation, and a test that failed the build on one would be enforcing
      redeployment, which "notify, never redeploy" rules out. Reporting the
      stale-but-valid case stays Phase 5's sweep
- [x] The unrecorded weakening is closed: `extend-exclude = [".claude"]` in
      `pyproject.toml` and `.claude/**` in the markdownlint config are either
      removed, or recorded in the register as the variance they are. A
      `narrowing-only` control with `baseline: null` admits no exemptions, so
      leaving them undeclared is the repository that authored the variance rule
      breaking it. **Removed, not recorded** — recording was not available: both
      controls are Tier 1 with `baseline: null`, and the schema rejects a Tier-1
      baseline, so there was no honest place to put an exemption. The exclusion
      rested on "lint-md owns that file", which was already false in fact — this
      repository edited it at `bd23bfb` — and it was hiding **eleven** LNT-001
      violations. `.claude/hooks/md-lint.py` now conforms to ruff and to strict
      mypy, which `[tool.mypy] files` was widened to cover, and its three paths
      (clean file, unfixable file, missing file) were exercised after the
      rewrite. It is also a **fifth** deployed artefact: § F counted four
      because the exclusion made this one invisible to the count
- [x] The register rejects unknown keys — at every level: document, `meta`,
      control, `standard`, `also_see` entry, verify block and `partial`. It
      immediately earned its place by surfacing `also_see`, a real field
      carrying external URLs that was accepted and validated by nothing; it is
      now allowed and its URLs are checked like `standard.url`
- [x] ADRs 0014–0018 are ratified — each moved from `Proposed` to `Accepted`, or
      superseded by a recorded alternative. 5 of 5 done: 0014 Accepted and
      implemented, 0015 Superseded by 0008 without ever being ratified, 0016,
      0017 and 0018 Accepted 2026-08-17 and not yet implemented. Ratification is
      not implementation — the criteria above and below carry that
- [x] [ADR 0018](adr/0018-register-checker-boundary.md) is **implemented**, not
      merely accepted — the rules its test moves are in the register, the rules
      that stay carry a recorded reason in the ADR, and SUP-001's lockfile
      ecosystems are register facts, so a Go, Rust or Java repo no longer passes
      it with no lockfile at all. Three passes: `ecosystems:` and `tools:` at
      contract 3, DOC-001's ceiling and extension id at contract 5, and at
      **contract 6** the item this criterion was left open for — the mandated
      tool names and their per-locus evidence. They needed a model, and the
      model is `stacks:`, keyed by predicate, each stack carrying `gates:` keyed
      by role. `tool`, `invocation`, `config` (with a `section` inside the file,
      because `pyproject.toml` existing says nothing about ruff), `pre_commit`,
      `editor_extension` and `strict_key` are all register facts now, as is the
      `suppression:` idiom set. `tests/test_stacks.py` is the evidence the move
      is real rather than cosmetic: every case edits **only** `controls.yaml`
      and asserts the verdict changes with it — a repository wired end to end
      for `flake8` fails today and passes once the register says `flake8`. The
      validator also rejects a stack naming no predicate, and a control
      declaring a locus its gate cannot express
- [x] ADR 0017 is **implemented**, not merely accepted — the register can
      declare a verification block partially implemented, with an expiry date
      and a named unverified property; GOV-001 carries that declaration instead
      of an unqualified `PASS`; and a declaration past its expiry fails the way
      GOV-003's `review_by` does. GOV-001's declaration expires 2026-11-30 and
      names what it cannot see: whether the workflow is a *required status
      check*. A run containing any partial block cannot exit `0`
- [x] ADR 0014 is **implemented**, not merely accepted — the repository is
      public as of 2026-08-17, confirmed by the rulesets API returning `[]` where
      it returned `403 Upgrade to GitHub Pro or make this repository public`
- [x] The default-branch ruleset exists and secret scanning push protection is
      enabled, so CI-001 and SEC-001 hold *in fact* — ruleset
      `default-branch-protection` (id `20937135`, `active`, no bypass actors)
      created 2026-08-17, `main` now reports `"protected": true`, and a direct
      push to `main` was observed being refused

The second criterion stops at the platform state being *correct*. Whether the
checker can *verify* it is Phase 3's `kind: remote` work and belongs to Phase 3's
exit criteria — requiring it here would make Phase 1.5 unclosable by its own
terms, which is the error this plan already made once by putting the devcontainer
in Phase 2.

The § D criterion is the real gate this time. Phase 1's suite passed 48 checks
while GOV-002 could not fail, a trailing comma could abort the run, and a
non-git directory reported clean — it exercised the paths the author had in mind
rather than the paths an adversary would take, which is the same critique this
repo levels at its predecessor.
