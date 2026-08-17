# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A control register for Equal Experts repositories: `controls.yaml` defines what
"conformant" means, a family of Claude skills deploys the gates, and a checker
(`standard-check`, in `src/standard_check/`) audits them.

Current status: Phases 0, 0.5 and 1 are built — the register has its ADRs, the
devcontainer is verified, and `standard-check` exists as a plain Python
executable. **Phase 1.5 (remediation) is next and gates Phase 2**: a review
found the checker aborts without a verdict in some cases and reports green for
things it never examined in others, and Phase 2 would copy that assert layer
into six gate skills. Read `docs/04-build-plan.md` § Phase 1.5 before touching
`src/standard_check/` — four earlier exit criteria are re-opened there, so do
not treat a ticked box in an earlier phase as settled without checking it.
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

- Full conformance run: `uv run standard-check` (also: `schema`, `--tier 1`,
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
- **Verification kinds**: `command` (exit code), `file` (shape assertion),
  `remote` (platform API state).
- **Variance**: `forbidden` or `narrowing-only`. Deployed artefacts may tighten
  a narrowing-only control but never loosen it; loosening requires updating the
  control's entry in the register first (as was done for DOC-001's 250-char
  line ceiling).

## Rules for editing `controls.yaml`

- Bump `meta.register_contract` only when a control's `rung`, `verify`, or
  `variance` changes — skills read it to detect stale deployments.
- Every control must cite an external, resolving standard URL; verify URLs
  before committing them.
- An unknown `assert` name is a schema error, not a skipped check (Phase 1 exit
  criterion — keep the closed set in sync with the checker when it exists).
- Meta-controls (GOV-001/002/003) check the register itself, not the code.

## Deployed artefacts and skills

Files deployed by ee-skills plugins (e.g. `.markdownlint.yaml`) carry an
`ee-control:` provenance header naming the control, the deploying skill and
version, and the register version. Keep the header when editing such files, and
respect the control's variance direction. `lint-md` owns the whole DOC-001
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
| `docs/05-promotion.md` | The route to the `ee-skills` marketplace |
| `docs/06-devcontainer-setup.md` | Operator guide for this repo's own container |
| `docs/07-inherited-conventions.md` | What the predecessor repo knew, sorted by whether it transfers — including what must **not** be copied |
| `docs/adr/` | One ADR per control, plus the open decisions at `Status: Proposed` |

`README.md` § "The register at a glance" lists the thirteen Tier-1 controls, with
the three meta-controls described below the table.
