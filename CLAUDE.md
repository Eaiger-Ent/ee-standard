# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A control register for Equal Experts repositories: `controls.yaml` defines what
"conformant" means, a family of Claude skills deploys the gates, and a checker
(`standard-check`, in `src/standard_check/`) audits them.

Current status: Phases 0, **0.5, 1 and 1.5 are all complete** as of 2026-08-18,
with no re-opened criteria outstanding. **Phase 2 is next.**
Read `docs/09-phase-1.5-review.md` before touching `src/standard_check/`:
it records what each assert was wrong about and why, and Phase 2 copies that
assert layer into six gate skills. Do not treat a ticked box in an earlier phase
as settled without checking it — **seven** boxes have been re-opened after being
ticked, four of them on 2026-08-18 by the review recorded as
`docs/09-phase-1.5-review.md` § H, which found GOV-001 passing a workflow that
ran on neither push nor pull_request, a tool compared only at filenames the
checker itself named, and ADR 0018 recorded as implemented with one of its
ratified moves never made.
`kind: remote` verification stays deferred to Phase 3; do not stub it earlier —
remote verify blocks report `SKIPPED (no credentials)`.

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
(macOS Keychain → `.devcontainer/.env`, which is gitignored and must stay so —
SEC-001 depends on that line).

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
mandated tool names and their per-locus evidence live in `stacks:`, lockfile
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
  miscategorisation decided its verdict.
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
format, and `tests/test_provenance_stamps.py` checks every stamp parses and
names a real control. Five files carry one: `.markdownlint.yaml`,
`.markdownlint-cli2.yaml`, `.github/workflows/lint.yml`,
`.claude/hooks/md-lint.py`, and — at the hook it owns rather than at the top of
the file — `.pre-commit-config.yaml`. Keep the header when editing such files,
note the edit in it, and respect the control's variance direction: no ignore
path may be added to a `narrowing-only` control with `baseline: null`, which is
all of them. `lint-md` owns the whole DOC-001
lifecycle — this repo does not write its own markdown gate, and `lint-md`'s
shape (pre-flight → install → write config → wire every locus → migrate →
verify) is the template every future gate skill copies (`docs/02-skill-family.md`).

Enforcement is never Claude: gates are pinned binaries reading pinned configs;
a skill may install or explain a gate but cannot be one.

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
| `docs/adr/` | One ADR per control, plus the open decisions at `Status: Proposed` |

`README.md` § "The register at a glance" lists the thirteen Tier-1 controls, with
the three meta-controls described below the table.
