# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A control register for Equal Experts repositories: `controls.yaml` defines what
"conformant" means, a family of Claude skills deploys the gates, and a checker
(`standard-check`, in `src/standard_check/`) audits them.

Current status: Phases 0, **0.5, 1 and 1.5 are all complete** as of 2026-08-18,
with no re-opened criteria outstanding. **Phase 2 is 11/12** and **Phase 3 is in
progress**; the register is at contract 20. `docs/04-build-plan.md` is the only
list of outstanding work and `uv run python scripts/plan_progress.py` is its
derived view — never keep a second copy of that status here. The slice-by-slice
record, and the evidence behind every criterion either phase ticks, lives in
`docs/10-phase-2-review.md` — including § Where Phase 2 finished, the closing
audit run over the register rather than over the ledger, and § What the second
review found — and in `docs/11-phase-3-review.md`, including what each slice
deliberately left open.

The one Phase 2 criterion still open is that the devcontainer template *builds*:
this container has no Docker, so nothing here has run `devcontainer build`, and
the commands for an operator are in `docs/08-adopting.md` § 2.0.

Read `docs/09-phase-1.5-review.md` before touching `src/standard_check/`:
it records what each assert was wrong about and why, and Phase 2 copies that
assert layer into six gate skills. Do not treat a ticked box in an earlier phase
as settled without checking it — **seven** boxes have been re-opened after being
ticked, four of them on 2026-08-18 by the review recorded as
`docs/09-phase-1.5-review.md` § H, which found GOV-001 passing a workflow that
ran on neither push nor pull_request, a tool compared only at filenames the
checker itself named, and ADR 0018 recorded as implemented with one of its
ratified moves never made.

Per [ADR 0027](docs/adr/0027-the-interpreter-is-a-pinned-tool.md) (**Accepted**
and implemented 2026-08-23, register contract 20), the interpreter the gates run
on is a pinned tool, and `.python-version` is its authority. `tools:` gained a
third `source` — `toolchain` — because both existing values would be false: the
value does not live in the register to be repeated (`literal`) and no package
manager produced the file (`lockfile`). **A support floor is not a pin.**
`requires-python` stays a floor and stays a support claim; narrowing it to force
the environment would tell an adopter that `standard-check` does not work on a
newer interpreter. `[tool.ruff] target-version` is deliberately absent — ruff
derives it from `requires-python`, and writing it out was a third copy that had
already drifted. The gap was invisible because there was no second copy to spot:
the devcontainer ran 3.13.15 and CI ran 3.14.7 from the same three files.

Per [ADR 0028](docs/adr/0028-the-support-floor-is-what-we-run.md) (**Accepted**
and implemented 2026-08-24) the pin and the support floor are both **3.14**:
`.python-version` reads 3.14 and `requires-python` reads `>=3.14`, so ruff's
derived target is 3.14 too — it moved with the floor and nobody edited it, which
is what deleting the written-out `target-version` bought. The floor was raised
because nobody had ever decided it; `>=3.13` was the number the container
happened to have. **An adopter on 3.13 can no longer install `standard-check`**,
and that is the accepted cost, cheap to reverse.

The devcontainer's python feature stays **3.13** and is now below the floor,
deliberately: it bootstraps `pip install uv` and answers
`#!/usr/bin/env python3`, it runs no gate, and `requires-python` claims nothing
about it — the decoupling ADR 0027 § Consequences predicted.

`.github/workflows/support-floor.yml` verifies the floor when it differs from
the pin, and today it does not, so the job reads both files and **skips itself**
rather than running the suite twice on one interpreter. It is kept because the
two diverge again the moment either moves — pinning ahead of the floor is the
ordinary case. It is **not** a gate and must never enter CI-001's
`required_checks:`. It is also the only place `UV_PYTHON` is set, which is the
one thing that outranks `.python-version`.

`kind: remote` reads platform API state (`src/standard_check/remote.py`,
`asserts_remote.py`, `rulesets.py`), reasoned in
[ADR 0021](docs/adr/0021-how-remote-verification-authenticates.md). It has
four outcomes, and only two are about the repository: **no token** is
`SKIPPED (no credentials)`; a token that was **rejected, under-scoped or shown
an answer that does not settle the control** is `UNCLASSIFIED`; only an actual
answer is `PASS`/`FAIL`. GitHub omits `security_and_analysis` for a caller
without admin, so reading its absence as "push protection is off" would report a
violation produced by not having looked — the asserts raise instead. The mirror
holds too: an effective-rules response of `[]` **is** an answer, and fails.
Tests must never depend on ambient auth — `tests/conftest.py` strips
`GITHUB_TOKEN`/`GH_TOKEN` autouse.

Per [ADR 0022](docs/adr/0022-a-platform-token-ci-carries.md) (**Accepted**
2026-08-23), **a platform token in CI is governed rather than forbidden**, and
its absence is what still blocks the `--require-complete` flip: the Actions
`GITHUB_TOKEN` cannot read `security_and_analysis`, so SEC-001's remote block is
`UNCLASSIFIED` in CI while passing locally.

**Requirements 1 and 2 of that ADR § What the register must gain land before any
token** — this is the one ordering it rules out absolutely. SEC-002 cannot see a
platform token today, because `no-static-cloud-keys` reads `cloud_credentials:`
and every name in it is a cloud provider key, so a `GH_ADMIN_TOKEN` secret would
leave SEC-002 green over a standing administrative credential.

This repository takes **Option 1** — a fine-grained token scoped to this
repository, `Administration: read`, held as an ordinary repository secret —
because the six accounts that could read it are organisation owners who already
hold admin here, and classic PATs are not in use. **An adopter takes Option 3**,
the deployment-environment gate, because its contributors are not organisation
owners. That is a posture difference rather than an exception, and **it must
never reach `controls.yaml` or anything under `plugins/`**, which is what an
adopter installs (ADR 0022 requirement 6). Note also that a `pull_request` run
receives repository secrets unless the pull request comes from a fork, and that
a guard written in a workflow file is a guard the pull request is editing.

Per [ADR 0014](docs/adr/0014-satisfying-remote-locus-controls.md) (**Accepted**
and implemented 2026-08-17), this repository **is public**: write nothing that
assumes privacy, and treat anything committed as publishable. CI-001 and SEC-001
stay Tier 1 — do not re-tier a control to make a report green.

Per [ADR 0016](docs/adr/0016-exit-codes-for-unverifiable-controls.md) and
[ADR 0017](docs/adr/0017-partial-verification-is-reported.md) (both **Accepted**
2026-08-17, neither implemented), the checker's verdict vocabulary is settled:
exit `3` means no violation was found but something could not be verified, `1`
means a verified violation, `0` means every applicable control was verified, and
`--require-complete` promotes `3` to `1`. A control whose tool is absent is
`UNCLASSIFIED`, not `FAIL`. A verification block declares its own partial
implementation **in the register**, with an expiry — never in the checker.

## Commands

- Full conformance run: `uv run standard-check` (also: `schema`, `run --tier 1`,
  `meta GOV-001`, `assert <name>`, `explain <ID>`). CI runs it in
  `.github/workflows/standard-check.yml`.
- Quality gates: `uv run ruff check .`, `uv run mypy`, `uv run pytest` — all
  configured in `pyproject.toml`, the single definition every locus reads.
- Build-plan progress: `uv run python scripts/plan_progress.py` — a derived view
  of the exit criteria in `docs/04-build-plan.md`, which stays the single source.
  It stores nothing and infers no gating; it exits non-zero if a criterion is
  marked re-opened while still ticked. Never maintain a second list of this work.
- Lint markdown: `markdownlint-cli2 "**/*.md"` — also runs via a PostToolUse
  auto-fix hook on every file you write, a pre-commit hook, and
  `.github/workflows/lint.yml`.
- Run all pre-commit hooks: `uv run pre-commit run --all-files`
- Verify container auth/tools: `.devcontainer/check-auth.sh`
- `gh` for repos in the Eaiger-Ent org (ambient `GITHUB_TOKEN`); `gh-ee-skills`
  for repos in the EqualExperts org (ee-skills, ee-skills-incubator) — the
  wrapper scopes `EE_SKILLS_GITHUB_TOKEN` to a single invocation.

All development happens inside the devcontainer (`docs/06-devcontainer-setup.md`
is the operator guide). Host secrets arrive via `.devcontainer/fetch-secrets.sh`
(macOS Keychain → `.devcontainer/.env`, from which `.devcontainer/.env.docker`
is derived for `--env-file`; both are gitignored and must stay so — SEC-001
depends on those lines).

## The core invariant

A register entry in `controls.yaml` **is** the control, not documentation of
one. Every other artefact — CI workflow, pre-commit config, gate skill,
devcontainer, checker — derives from the register rather than restating it.
Never introduce a second copy of a rule (in prose, CI, or config) that could
drift from the register; that duplication ("theme T-2") is the failure this repo
exists to prevent.

**Python counts as a second copy.** Per
[ADR 0018](docs/adr/0018-register-checker-boundary.md) (**Accepted** 2026-08-17,
**implemented** over contracts 3, 5, 6 and 8), before writing a rule into
`src/standard_check/` ask: *could a reasonable Equal Experts repository need this
to differ without changing the checker?* If yes, it belongs in `controls.yaml` —
mandated tool names and their per-locus evidence live in `stacks:` — including which files a stack's gates must cover and where each
tool's allow-list lives — lockfile
ecosystems, test-command spellings and frozen-install idioms in `ecosystems:`,
tool versions **and the loci that repeat them** in `tools:`,
failure-suppression idioms in `suppression:`, the credential names SEC-002
forbids in `cloud_credentials:`, and anything specific to
one control in its verify block's `args:`. If no, the checker may hold it, but
the reason must be recorded in ADR 0018 — the predicate grammar, the ID pattern, semver
strictness, `rationale_adr` existence and the Tier-1 baseline rule are
properties of the register format, not of any repository. An unreasoned rule in
the checker is the failure, not an exception to it.

## Vocabulary you need before editing anything

Defined in `docs/00-concepts.md`; the schema is `docs/01-register-schema.md`.

- **Rung** (enforcement ladder): `advisory` → `warn` → `blocking` →
  `blocking (baselined)`. Promotion is only by explicit recorded decision.
- **Locus**: where a control runs — `editor`, `pre-commit`, `ci`, `remote`.
  Discipline is *pin once, reference many*: same tool version, same config, at
  every locus.
- **Predicates**: a control whose `applies_to` predicate the repo doesn't
  satisfy is SKIPPED, not failed. Predicates are evaluated against files, never
  self-declared.
- **Baseline**: shrink-only tolerated-violation list (GOV-002 fails if one
  grows). All Tier-1 controls carry `baseline: null` by design.
- **Verification kinds**: `command` (an external tool; exit code is the verdict),
  `file` (an in-process assertion over repository files), `remote` (platform API
  state). The kind names what performs the verification, not which module
  implements it — declaring an in-process assertion as `kind: command` is a
  schema error, because GOV-001 reads `kind: command` blocks and the
  miscategorisation decided its verdict. **One exception, bounded by the
  validator**: a meta-control verifies itself with
  `run: standard-check meta GOV-NNN`, which runs in-process. The shape is forced
  — a meta-control returns a three-valued `Verdict` and a `kind: file` assert
  returns a boolean — and it decides nothing, since GOV-001 never reads
  `meta_controls`. A control using that spelling, or a meta-control naming
  another's id, is rejected (`docs/01-register-schema.md` § The one exception).
- **Partial**: any verify block may declare itself not fully implemented, naming
  the unverified property and an expiry date. GOV-003 fails an expired one, and
  a partial block denies the run a `0` exit.
- **Variance**: `forbidden` or `narrowing-only`. Deployed artefacts may tighten
  a narrowing-only control but never loosen it; loosening requires updating the
  control's entry in the register first (as was done for DOC-001's 250-char
  line ceiling).

## Rules for editing `controls.yaml`

- Bump `meta.register_contract` when a control's `rung`, `verify`, `variance` or
  `applies_to` changes, or when the register gains a field a skill reading it
  must understand — skills read it to detect stale deployments.
- Every control must cite an external, resolving standard URL; verify URLs
  before committing them.
- An unknown `assert` name is a schema error, not a skipped check (Phase 1 exit
  criterion — keep the closed set in sync with the checker when it exists).
- Meta-controls (GOV-001/002/003) check the register itself, not the code.

## Deployed artefacts and skills

Files deployed by ee-skills plugins carry an `ee-control:` provenance header
naming the control, the deploying skill and version, the register version **and
the register contract** — `docs/00-concepts.md` § The provenance stamp has the
format, one parser lives at `src/standard_check/provenance.py` (never write a
second), and `tests/test_provenance_stamps.py` checks every stamp parses and
names a real control. Eleven files carry one: `.markdownlint.yaml`,
`.markdownlint-cli2.yaml`, `.github/workflows/lint.yml`,
`.claude/hooks/md-lint.py`, `.github/workflows/standard-check.yml`,
`.devcontainer/devcontainer.json`, `.github/dependabot.yml` — the one file whose
stamp sits at the top, because every line of it belongs to SUP-002 —
`.devcontainer/setup.sh`, whose every stamp belongs to a gate other than the
`gate-build` that owns the file, `.github/rulesets/default-branch.json` — the
one artefact that enforces nothing by existing, being a record of what the
platform is asked to enforce — and, with one stamp per hook it owns rather than
one at the top of the file, `.pre-commit-config.yaml`, and — from contract 18,
stamped per region for the same reason — `.gitignore`, whose two credential
lines are the only stamped artefact that runs nothing and installs nothing.
A control whose artefacts a gate writes names it in
`deployed_by`, and `provenance_stamp_present` reads back a stamp naming **that
control** — not merely one naming its gate, which credited a gate's three
controls for any stamp it had written anywhere. The control's id reaches the
assert from the runner, and the schema rejects a register that writes it into
`args:` itself, or one where `deployed_by` and the stamp block disagree. Keep the header when editing such
files, note the edit in it, and respect the control's variance direction.

A stamp *behind* the register is staleness, which is never enforced and — until
Phase 5's sweep exists — is not reported either: `gate-secrets`' and
`gate-quality`'s older stamps read contracts 11 and 12 against a register at 19,
deliberately, because nothing they wrote here needs rewriting and doing it by
hand would record a redeployment that did not happen. Nothing in the checker says
so, and that is Phase 5's job rather than a defect. A stamp *ahead* of the
register is a defect, and fails. An exemption
in a deployed config is judged by what it hides
([ADR 0019](docs/adr/0019-exemptions-cannot-hide-tracked-files.md)): excluding a
path git does not track scopes the tool, excluding a path git tracks weakens the
control, and no `narrowing-only` control with `baseline: null` — which is all of
them — admits the second. `markdown_gate_wired_at_all_loci` checks it, so it is
a build failure rather than something to remember. `lint-md` owns the whole DOC-001
lifecycle — this repo does not write its own markdown gate, and `lint-md`'s
shape (pre-flight → install → write config → wire every locus → migrate →
verify) is the template every future gate skill copies (`docs/02-skill-family.md`).

**Do not re-run `/lint-md` here.** The stamps read `lint-md@1.0.6` and the
installed skill is 1.0.7, so the deployment is stale — which is reported and
never enforced. 1.0.7 shipped most of the amend at
[#530](https://github.com/EqualExperts/ee-skills-incubator/issues/530) but still
writes `npx --no-install` at every locus, which ADR 0020 measured falling
through to `PATH`, and still writes `.claude/**` into `ignores`, which ADR 0019
forbids. Its presence checks mean a re-run would skip four of the five artefacts
today rather than revert them — but that is idempotency rather than agreement,
one of the four greps matches only a comment, and the fifth
(`.markdownlint.yaml`) prompts to overwrite rather than skipping. Refresh the
deployment only once those two rows ship
(`docs/09-phase-1.5-review.md` § F, Update 2026-08-20).

Enforcement is never Claude: gates are pinned binaries reading pinned configs;
a skill may install or explain a gate but cannot be one.

Which model an agent or sub-agent runs on is decided by
[ADR 0023](docs/adr/0023-smallest-model-a-task-can-be-trusted-to.md)
(**Accepted** 2026-08-23, **not implemented**): three classes, a floor per
class, and `CLAUDE_CODE_SUBAGENT_MODEL` forbidden because it outranks every one
of them. Do not restate the floors here — the register's `agent_models:` block
is the source once it lands, and `.claude/agents/*.md` frontmatter is the only
copy the harness reads.

## Documents

Read `docs/00-concepts.md` first for the vocabulary, then:

| Document | What it is for |
| --- | --- |
| `docs/00-concepts.md` | The vocabulary every other document assumes |
| `docs/01-register-schema.md` | Field-by-field specification of `controls.yaml` |
| `docs/02-skill-family.md` | How the standard reaches a repo, and stays current |
| `docs/03-devcontainer.md` | What the shipped devcontainer template must be |
| `docs/04-build-plan.md` | The phase exit criteria that define "done" for any implementation work, and the only list of outstanding work |
| `docs/08-adopting.md` | What a repository that did not author the standard must do to satisfy it. **Every phase owes this file the adopter-facing steps it introduces** — see `04-build-plan.md` § A standing requirement |
| `docs/05-promotion.md` | The route to the `ee-skills` marketplace |
| `docs/06-devcontainer-setup.md` | Operator guide for this repo's own container |
| `docs/07-inherited-conventions.md` | What the predecessor repo knew, sorted by whether it transfers — including what must **not** be copied |
| `docs/09-phase-1.5-review.md` | Record of the Phase 1.5 review, and of § H, the review of the closed phase that re-opened four of its criteria. **`§ A`–`§ H` anywhere in this repo — asserts, tests, ADRs — refer to this file**, not to the build plan |
| `docs/10-phase-2-review.md` | Record of Phase 2 slice by slice, and the evidence behind every criterion it ticks |
| `docs/11-phase-3-review.md` | Record of Phase 3 slice by slice, including what each slice deliberately left open |
| `docs/adr/` | One ADR per control, plus the cross-cutting decisions (0014 onward). All **27** in this directory are `Accepted` — the count is of files here, not of ADR numbers, which reach 0028 because 0015 is archived. There are no open decisions |
| `docs/adr/archive/` | ADRs no longer in force — `Superseded` or `Deprecated` only. Today: 0015 alone. `ls docs/adr/` is therefore the list of decisions in force |

`README.md` § "The register at a glance" lists the thirteen Tier-1 controls, with
the three meta-controls described below the table.

**An ADR is written once and stands on its own** ([ADR 0026](docs/adr/0026-an-adr-stands-on-its-own.md)).
Editing an accepted one is the exception, permitted only where the decision is
unchanged **and** the record has become factually false — ADR 0016 asserting a
bound that had stopped holding is the model case. Anything that changes *what
was decided* is a new ADR that supersedes, however small it looks; when in
doubt, supersede. Recording implementation (`## Applied — pass N`) is not
amendment and needs no revision. Do not read the seven amended ADRs as a norm:
they are this repo amending its own process in one week.

Where that exception does apply, the ADR is **amended in place** rather than
superseded ([ADR 0024](docs/adr/0024-variance-vocabulary-is-direction-only.md)) —
superseding would restate a correct decision to change one clause, which is the
second copy this repo exists to prevent. Per
[ADR 0025](docs/adr/0025-an-amendment-is-a-recorded-revision.md) an amendment is
a **numbered revision**: every ADR carries `**Revision:** N`, and one above 1
carries a `## Revision History` table giving each revision's date, a one-line
summary and its ratifier. `grep -L '\*\*Revision:\*\* 1' docs/adr/*.md` lists
the amended ones. `tests/test_adr_revisions.py` holds the form — the count must
equal the rows and a count above 1 must be matched by an amendment in the body,
so the two halves fail each other. It is a test rather than a control because it
governs how this repository records its own decisions, not what a conformant
repository contains (ADR 0022 requirement 6). It does **not** check that a
summary is accurate; that is recorded as the residual risk, not covered.
`adr-toolkit@0.1.11` models no revision or approver at all, so `/adr-check` and
`/adr-consistency` neither check these fields nor object to them.

An ADR reaching a terminal status moves to `docs/adr/archive/` **keeping its
number**, which is never reused — only its path changes. The same test checks
status and location agree **in both directions**, so the directory cannot
disagree with the header; it also fails a live control whose `rationale_adr`
cites an archived ADR, because a control's stated reasoning may not be a
decision the corpus has retired. Archiving breaks inbound links: rewrite them in
the same change. Note the cost — `adr-toolkit` globs `docs/adr/*.md`, so an
archived ADR leaves the corpus `/adr-consistency` scans.

Gate skills live in `plugins/ee-standard/skills/` — `gate-secrets`,
`gate-quality`, `gate-supply-chain`, `gate-build`, `gate-iac` and `gate-repo`,
the whole family, plus `standard-adopt`, the dispatcher that ships no templates
because it writes no artefacts of its own. A gate verifies itself with
`standard-check run --control <ID>` and never by reading its own files back —
that command runs the control's verify blocks through the same `run_control` the
full audit calls, which is what makes "one assert implementation" true rather
than intended. A gate holds **no** pinned version of its own; templates carry
placeholders and `tests/test_plugin.py` fails if any value the register pins
appears anywhere under `plugins/`. `.claude-plugin/deploys.json` carries one
`contractVersion` **per gate**, not per plugin — a shared number would
recommend redeploying every gate whenever any one of them changed, which is the
noise Phase 5's first two criteria exist to prevent.
