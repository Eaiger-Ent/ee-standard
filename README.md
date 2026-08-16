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

| Document | What it covers |
| --- | --- |
| [`docs/00-concepts.md`](docs/00-concepts.md) | The vocabulary. Read first. |
| [`docs/01-register-schema.md`](docs/01-register-schema.md) | Field-by-field spec for `controls.yaml`. |
| [`docs/02-skill-family.md`](docs/02-skill-family.md) | The plugin: dispatcher, gates, checker, staleness. |
| [`docs/03-devcontainer.md`](docs/03-devcontainer.md) | The clean devcontainer, and how it composes with `project-init`. |
| [`docs/04-build-plan.md`](docs/04-build-plan.md) | Seven phases with checkable exit criteria. |
| [`docs/05-promotion.md`](docs/05-promotion.md) | The route to the `ee-skills` marketplace. |
| [`docs/06-devcontainer-setup.md`](docs/06-devcontainer-setup.md) | **Start here.** Standing up this repo's own container, and the macOS values it needs. |
| [`controls.yaml`](controls.yaml) | The register itself. |

## The register at a glance

Thirteen Tier-1 controls — birth conditions, true from the first commit, never
baselined:

| ID | Property |
| --- | --- |
| SEC-001 | A commit containing a secret cannot reach the remote |
| SEC-002 | No long-lived cloud credential exists in CI |
| SUP-001 | Dependencies resolve from a frozen lockfile |
| SUP-002 | Dependency updates arrive as reviewable proposals |
| SUP-003 | CI actions are pinned to an immutable SHA |
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

Phase 0 complete — the register exists.

Phase 0.5, this repo's own devcontainer, is next and comes before any code is
written: all development happens inside the container, and Phase 1 cannot meet
its own exit criteria without one. Follow
[`docs/06-devcontainer-setup.md`](docs/06-devcontainer-setup.md).

Then Phase 1, the checker. See
[`docs/04-build-plan.md`](docs/04-build-plan.md) for exit criteria.

## Relationship to existing ee-skills plugins

This composes with prior art rather than replacing it:

| Plugin | Relationship |
| --- | --- |
| `lint-md` | Owns DOC-001 outright. Also the reference shape every gate copies. |
| `project-init` | Configures the devcontainer. This repo insists the result is pinned. |
| `devcontainer-check` | Checks the environment. This repo checks the configuration. |
| `ee-skills-manage` | `skill-update` gains the owed-deployment report. |
