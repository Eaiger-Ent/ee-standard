# ADR 0058: A Gate Declares Its Deployment Contract in Its Own Skill Directory

**Status:** Accepted
**Date:** 2026-10-25
**Revision:** 1

## Background

**The problem.** An adopter who installs `control-register` from
`EqualExperts/ee-skills` is told the wrong deployment contract for
`gate-secrets`. The number lives in `.claude-plugin/deploys.json`. The incubator
never updates that folder after a plugin's first promotion. The gate the adopter
installs writes contract 7, and the file beside it says 6.

That breaks staleness for every adopter on that route, silently. A gate stamps
the contract it reads ([ADR 0038](0038-the-stamp-records-the-deployment-contract.md)),
so `gate-secrets` writes a contract-7 deployment and labels it 6. The installed
number and the stamp then agree forever, whatever the gate's output does next.
`register-check deployments` reports *current* over a deployment it has no way
to judge.

**The cause is a rule in another repository, and the rule is not wrong for its
owner.** On an amendment, the incubator's `scripts/promote.py` syncs a native
bundle with `skip_names=_NATIVE_PRESERVE | _INCUBATOR_ONLY` (line 1217).
`_NATIVE_PRESERVE` is `{".claude-plugin", "data", "LICENSE", "README.md"}`,
which the script calls "managed in ee-skills". Part of that is true:
`plugin.json`'s `version` is assigned and bumped by the marketplace, and copying
the incubator's `0.1.0` over it would move the published version backwards. But
the rule protects the whole folder, so `deploys.json` is held back with it.

**It has already happened once.** `gate-secrets` moved to contract 7 in this
repository's #122 (2026-08-31). Submission 15 (incubator#1177) carried that change and merged
upstream as incubator#1183, closing as `implemented`. The release it produced,
`control-register@0.1.15` (ee-skills `94c9536`), changed one file:
`plugin.json`'s version line. `docs/promotion/published.json` records the
difference as `owed-upstream`. That record is what found it. Nothing in the
promotion pipeline would have.

**Who is affected.** An adopter installing from this repository's own
marketplace ([ADR 0044](0044-the-adopter-installs-from-the-public-marketplace.md))
reads `plugins/control-register/` as committed here and gets contract 7. The
fault is confined to the `ee-skills` copy. That copy is the one Equal Experts
teams are pointed at.

## Alternatives Considered

### Option 1: Ask the incubator to narrow `_NATIVE_PRESERVE` — Rejected

Protect only `plugin.json`, or only its `version`, and sync the rest of
`.claude-plugin/`. This is a reasonable change for the incubator to make, and it
can still be raised. It is rejected as *our* answer because it puts a
control-register mechanism behind a rule in another organisation's script, which
this repository cannot test and its owner may have reasons to keep. Every other
native bundle's manifest folder would change behaviour too. We would be asking
for a policy change to fix a file we chose to put in that folder.

### Option 2: Apply `deploys.json` to `ee-skills` by hand on each contract bump — Rejected

This is the process that has already failed. A contract bump would become an act
in another organisation's repository, outside the submission that made it, with
nothing to say it was missed. It was missed for almost eight weeks.

### Option 3: One `deploys.json` at the plugin root — Rejected

Move the file up one level, out of `.claude-plugin/`. It would ship:
`templates/` and `reference/` reach `ee-skills` through the same bundle-root
sweep (`78220a9` carried `templates/` files). It is also the smallest code
change, one path constant. It is rejected for two reasons:

- **It rides on the sweep's routing rules.** That path has a preserve list and a
  rule that moves loose root files under `skills/<bundle>/` once a bundle has a
  root `SKILL.md` (`promote.py` line 297). Either could catch it later.
- **It keeps a per-gate fact in a shared file.** A contract bump to
  `gate-quality` edits a file `gate-secrets` reads. One contract per gate is the
  shape `02-skill-family.md` § The `deploys` sidecar argues for. A shared file
  undercuts it at the level of the diff.

### Option 4: One `deploys.json` in each gate's skill directory — Chosen

`skills/gate-secrets/deploys.json` and so on. Shipping a skill directory is what
promotion exists to do. `copy_skill_dir` replaces the directory wholesale
(rmtree, then copytree) and drops only `dependencies.json`, so the file
published is the file submitted. A contract bump lands in the same directory,
the same diff and the same submission as the change to what the gate writes.
ADR 0038's property, *the writer and the declaration are the same artefact*,
becomes literal: the gate reads a file in its own directory.

## Decision

**We choose Option 4: each gate declares its deployment contract in a
`deploys.json` inside its own skill directory, and nothing reads
`.claude-plugin/deploys.json`.**

| | Before | After |
| --- | --- | --- |
| Where | `.claude-plugin/deploys.json`, one file for six gates | `skills/<gate>/deploys.json`, one per gate |
| Shape | `{schemaVersion: 2, gates: {<gate>: {contractVersion, controls, artifacts}}}` | `{schemaVersion: 3, contractVersion, controls, artifacts}`; the directory names the gate |
| A gate reads | `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/deploys.json`, `gates.<gate>.contractVersion` | `${CLAUDE_SKILL_DIR}/deploys.json`, `contractVersion` |
| `register-check deployments` reads | the one sidecar | every `skills/*/deploys.json` under the plugin root |
| On an incubator amendment | never updated | copied with the skill |

Three rules come with it.

**No gate's `contractVersion` moves.** Relocating the declaration changes nothing
any gate writes, so every stamp in every adopting repository stays exactly as
valid as it was. This is what makes the change invisible to adopters'
repositories. It is a plugin-layout change, not a deployment.

**The old location is not a fallback.** `.claude-plugin/` is never synced on
amendment, so the `ee-skills` copy will keep a contract-6
`.claude-plugin/deploys.json` indefinitely. Reading it whenever no per-gate file
is found would bring back the exact fault this ADR removes. A plugin root with
no `skills/*/deploys.json` gets the refusal a missing sidecar gets today
(`NoPlugin`, exit `2`), and the message names this ADR. If it carries the old
file, the message says that the plugin predates the move.

**The leftover file is recorded, not chased.** In `docs/promotion/published.json`,
`.claude-plugin/deploys.json` becomes a `by-design` difference: deleted here,
preserved there by `promote.py`, and read by nothing. Removing it from `ee-skills`
is a hand change we may ask for, not a condition of this decision.

## Consequences

**What moves together.** The path is named in the checker (`deployments.py`'s
`_SIDECAR`, `find_plugin` and `load_gates`; `provenance.py`; `cli.py`'s help;
`asserts_file.py`'s docstring), in every gate's substitution table and in
`register-adopt`, in `tests/test_plugin.py`, `tests/test_deployments.py` and
`tests/conftest.py`, and in `02-skill-family.md`, `00-concepts.md`,
`08-adopting.md` and `14-file-map.md`. `tests/test_plugin.py` holds the files to
the register in the same direction it does now, per file. The phase reviews keep
the old path, because they record what was true then.

**ADR 0038 is amended, in the change that implements this one.** Its decision is
unchanged. Two of its sentences become false once the file moves: § Background's
*"declares a `contractVersion` in `.claude-plugin/deploys.json`"*, and
§ Decision's *"`gates.<gate>.contractVersion` from the plugin's `deploys.json`"*.
They become *"in its own `skills/<gate>/deploys.json`
([ADR 0058](0058-a-gate-declares-its-contract-in-its-own-directory.md))"* and
*"`contractVersion` from the `deploys.json` in the gate's own directory"*, at
Revision 2. That is the case [ADR 0024](0024-variance-vocabulary-is-direction-only.md)
reserves for amendment. Amending now would make 0038 false in the other
direction. [ADR 0042](0042-a-deploying-skill-reads-local-configuration.md) names
the old path in its list of what a declination record is not, and takes the same
one-line correction.

**One sentence upstream becomes inaccurate, and nothing breaks.**
`ee-skills-manage`'s `skill-update`, Step 2.7, says a deploying plugin declares
its gates "in its own `.claude-plugin/deploys.json`". It reads nothing itself.
It runs `register-check deployments` and reports what that prints, so its
behaviour is unaffected. The sentence is worth correcting upstream. Fixing it is
not a dependency of this decision.

**The Phase 6 criterion's `deploys.json` half closes through an ordinary
submission.** The per-gate files reach the incubator as one amendment and ship
on its next promotion. `scripts/record_published.py --check` then shows whether
they arrived. The README half is not affected by this ADR and is asked for in
incubator#1185.

**The cost** is six small files where there was one, and a `schemaVersion` the
checker must refuse in its old form rather than read. The report's order does not
change, because it comes from the register's tier and rung, not the file
(`tests/test_deployments.py`).

## Related ADRs

- [ADR 0038](0038-the-stamp-records-the-deployment-contract.md): the decision
  this keeps true; amended, not superseded, when this is implemented
- [ADR 0018](0018-register-checker-boundary.md): the deployment contract is a
  plugin fact rather than a register one, which is why it moves within the
  plugin and not into `controls.yaml`
- [ADR 0044](0044-the-adopter-installs-from-the-public-marketplace.md): the route
  this fault does not affect
- [ADR 0024](0024-variance-vocabulary-is-direction-only.md) and
  [ADR 0025](0025-an-amendment-is-a-recorded-revision.md): why 0038 is amended
  rather than superseded, and how the amendment is recorded

## References

- `EqualExperts/ee-skills-incubator` `scripts/promote.py`: `_NATIVE_PRESERVE`
  (line 152), the amend sync (line 1217), `copy_skill_dir` (line 125)
- incubator#1177 and incubator#1183: submission 15, merged and not published
- [`docs/promotion/published.json`](../promotion/published.json): the record
  that found it
- [`04-build-plan.md`](../04-build-plan.md) § Phase 6, *Nothing in
  `control-register` is owed to the published copy*
- [`02-skill-family.md`](../02-skill-family.md) § The `deploys` sidecar
