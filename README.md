# ee-standard

A control register for Equal Experts repositories, the skills that deploy it, and
the checker that audits it.

## The problem

A retrospective on `generate-ee-slides` found tooling that was individually good
and collectively leaky. The failures were not missing tools — every gate that
mattered was, at some point, installed. The failures were **missing relationships
between** tools:

| Theme | Pattern |
| --- | --- |
| T-1 | A stated standard that nothing enforces |
| T-2 | One definition copied, then diverged |
| T-3 | Declared but unreachable |
| T-4 | Failures absorbed rather than surfaced |
| T-5 | The credential boundary least defended |

T-3 is the sharpest: a lint workflow existed, was believed in, and was not a
required status check. Nothing about the repository on disk revealed this.

## The approach

One file, `controls.yaml`, is the single source of truth for what conformant
means. Everything else derives from it rather than restating it — CI workflow,
pre-commit config, gate skills, devcontainer, checker.

A register entry is not documentation of a control. It **is** the control.

Three properties follow:

- **Deployment is a skill.** Getting a gate into a repo is a Claude-assisted,
  reviewable act. Modelled directly on the existing `lint-md` plugin.
- **Enforcement is not.** The gate itself is a pinned binary reading a pinned
  config. CI has no Claude in it. A plugin can install, explain, and propose
  fixes for a gate; it cannot *be* the gate.
- **Drift is computable.** Every deployed artefact carries a provenance stamp, so
  never-deployed, deployed-and-current, and deployed-and-stale are distinguishable
  states rather than matters of memory.

## Documents

Two starting points, depending on who you are.

**Adopting the standard for your own repository** →
[`docs/08-adopting.md`](docs/08-adopting.md). It leads with the steps no tool can
take for you — repository visibility, branch rulesets, push protection, and the
dependency-update bots — because those are the ones discovered late and paid for
twice. Every step carries the evidence that shows it worked.

**Working on this repository** → [`docs/06-devcontainer-setup.md`](docs/06-devcontainer-setup.md).

| Document | What it covers |
| --- | --- |
| [`docs/08-adopting.md`](docs/08-adopting.md) | **Start here if you are adopting.** The platform state, the gates, and reading a verdict. |
| [`docs/00-concepts.md`](docs/00-concepts.md) | The vocabulary. Read first. |
| [`docs/01-register-schema.md`](docs/01-register-schema.md) | Field-by-field spec for `controls.yaml`. |
| [`docs/02-skill-family.md`](docs/02-skill-family.md) | The plugin: dispatcher, gates, checker, staleness. |
| [`docs/03-devcontainer.md`](docs/03-devcontainer.md) | The clean devcontainer, what it ships, and who owns each step. |
| [`docs/04-build-plan.md`](docs/04-build-plan.md) | Seven phases with checkable exit criteria. |
| [`docs/05-promotion.md`](docs/05-promotion.md) | The route to the `ee-skills` marketplace. |
| [`docs/06-devcontainer-setup.md`](docs/06-devcontainer-setup.md) | **Start here if you are working on this repo.** Standing up its container, and the macOS values it needs. |
| [`docs/07-inherited-conventions.md`](docs/07-inherited-conventions.md) | What the predecessor repo already knew, and which half of it transfers. |
| [`docs/09-phase-1.5-review.md`](docs/09-phase-1.5-review.md) | Record of the Phase 1.5 review — the findings `§ A`–`§ H` the code cites, and the evidence behind each tick. |
| [`controls.yaml`](controls.yaml) | The register itself. |

## The register at a glance

Fifteen Tier-1 controls — birth conditions, true from the first commit, never
baselined:

| ID | Property |
| --- | --- |
| SEC-001 | A commit containing a secret cannot reach the remote |
| SEC-002 | No long-lived cloud credential exists in CI |
| SEC-003 | CI carries no platform credential the register does not name |
| SUP-001 | Dependencies resolve from a frozen lockfile |
| SUP-002 | Dependency updates arrive as reviewable proposals |
| SUP-003 | CI actions are pinned to an immutable SHA |
| SUP-004 | A pinned release digest is the one the project published |
| BLD-001 | The container's final user is not root |
| DEV-001 | The devcontainer's image and features are pinned |
| CI-001 | The default branch requires review and passing checks |
| LNT-001 | Lint blocks at editor, pre-commit and CI alike |
| TYP-001 | Type checking is strict and blocking |
| TST-001 | A failing test fails the build |
| IAC-001 | Infrastructure is scanned before it is applied |
| DOC-001 | Markdown conforms to one shared ruleset |

Plus three meta-controls that check the register rather than the code: **GOV-001**
every blocking control is reachable from a CI step that can fail; **GOV-002** no
baseline grew; **GOV-003** nothing is past its review date.

Every control cites an external, resolving standard. Every URL in the register
was verified before it was committed.

## Status

Phase 0 complete — the register exists, with a rationale ADR per control in
[`docs/adr/`](docs/adr/).

Phase 0.5 complete — this repo's own devcontainer, digest-pinned and verified.
Operator guide: [`docs/06-devcontainer-setup.md`](docs/06-devcontainer-setup.md).

Phase 1 built — `register-check` exists (`uv run register-check`) and this repo
satisfies every control the checker can verify.

Phase 1.5, remediation, is complete as of 2026-08-18 — 26 exit criteria, seven of
which were ticked and later found false before closing properly. It existed
because Phase 2 copies the assert layer into six gate skills, so a defect left
in the checker becomes six. The findings, the five decisions they needed, and the
evidence behind every tick are in
[`docs/09-phase-1.5-review.md`](docs/09-phase-1.5-review.md).

Phase 2, the gates, is 11 criteria of 12 — the whole `gate-*` family plus
`register-adopt` ship in [`plugins/control-register/`](plugins/control-register/), and the
one open criterion needs an operator with Docker
([`docs/10-phase-2-review.md`](docs/10-phase-2-review.md)).

**Phase 3 is in progress.** `kind: remote` is implemented as of 2026-08-22, so
the two controls that verify GitHub's own state — a protected default branch and
secret scanning push protection — are checked rather than skipped. Give the
checker a `GITHUB_TOKEN` and they answer; without one they report
`SKIPPED (no credentials)`, which is never a pass
([`docs/11-phase-3-review.md`](docs/11-phase-3-review.md)).

The outstanding work is [`docs/04-build-plan.md`](docs/04-build-plan.md).

## Relationship to existing ee-skills plugins

This composes with prior art rather than replacing it:

| Plugin | Relationship |
| --- | --- |
| `lint-md` | Owns DOC-001 outright. Also the reference shape every gate copies. |
| `devcontainer-check` | Checks the environment. This repo checks the configuration. |
| `ee-skills-manage` | `skill-update` gains the owed-deployment report. |

`project-init` was in this table, deferred to for the choice of image. The
shipped devcontainer template now produces a configured `.devcontainer/`, and
`project-init` replaces its digest pin with a floating tag, so the standard no
longer composes with it
([ADR 0037](docs/adr/0037-the-template-is-the-whole-devcontainer-step.md)).
