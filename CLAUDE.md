# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A control register for Equal Experts repositories: `controls.yaml` defines what
"conformant" means, a family of Claude skills deploys the gates, and a checker
(`standard-check`, not yet built) audits them. There is no application code yet
— the repo is currently the register plus design docs plus its own devcontainer.

Current status: Phase 0 (register) and Phase 0.5 (this repo's devcontainer) are
complete. Phase 1 — building `standard-check` as a plain Python executable, in
the order given in `docs/04-build-plan.md` § Phase 1 — is next. `kind: remote`
verification is deliberately deferred to Phase 3; do not stub it earlier.

## Commands

- Lint markdown (the only gate wired so far): `markdownlint-cli2 "**/*.md"` —
  also runs via a PostToolUse auto-fix hook on every file you write, a
  pre-commit hook, and `.github/workflows/lint.yml`.
- Run all pre-commit hooks: `pre-commit run --all-files`
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

Read `docs/00-concepts.md` first; `docs/04-build-plan.md` has the phase exit
criteria that define "done" for any implementation work; `README.md` § "The
register at a glance" lists all sixteen controls.
