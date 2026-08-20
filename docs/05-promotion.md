# Promotion to ee-skills

The route from a skill authored here to a skill installable from the EE
marketplace, written against what the `ee-skills` repository **actually
contains**, not what its documentation says.

## The route

```text
  author locally, in this repo
            │
            ▼
  /skill-submit-new  (new)   or   /skill-submit-amend  (update)
            │                     one issue per SKILL, not per plugin
            ▼
  GitHub issue on EqualExperts/ee-skills-incubator
            │
            ▼
  maintainer review → each skill lands flat at incubator skills/<skill>/
            │           and skills/promote-config.json groups them into a plugin
            ▼
  maintainer promotes to EqualExperts/ee-skills plugins/<plugin>/skills/<skill>/
            │
            ▼
  marketplace.json + readme-meta.json → installable
```

Three properties of this route shape the build plan:

**Submission is an issue, not a pull request.** Both `skill-submit-new` and
`skill-submit-amend` open a GitHub issue against `EqualExperts/ee-skills-incubator`
for maintainer review. You do not push a branch, and you cannot self-merge. The
practical consequence: **the skills must be complete and working locally before
submission**, because there is no iterate-in-review loop under your control.
That is why the build plan tests everything against a real consumer repo before
promotion is attempted at all.

**Promotion is a maintainer action.** Whatever the incubator-to-marketplace step
is mechanically, it is not yours to run. Budget calendar time for it.

**The unit of submission is a skill, not a plugin.** `/skill-submit-new` takes a
skill name, reads one `SKILL.md`, and opens one issue. A plugin shipping nine
skills is nine issues. This is the correction that matters most to Phase 6's
shape, and § What the incubator actually holds sets out what follows from it.

## What the incubator actually holds

Read from `EqualExperts/ee-skills-incubator` on 2026-08-20, because the shape of
the destination decides how much of this repository's tree can go as it stands.

**Grouping is a config file, not a directory.** `adr-toolkit` ships eight skills
and `skills/adr-toolkit` **404s** — the eight sit flat as `skills/adr-create`,
`skills/adr-new` and so on, and `skills/promote-config.json` is the only thing
that says they are one plugin:

```json
"adr-toolkit": {
  "skills": ["adr-create", "adr-new", "adr-refine", "adr-check",
             "adr-review", "adr-approve", "adr-status", "adr-consistency"],
  "description": "Full ADR lifecycle: create, refine, check, review, approve, status, consistency."
}
```

So a multi-skill plugin is ordinary rather than exotic — `git-summary-plugin`
declares ten. What is *not* ordinary is getting one out of `/skill-submit-new`,
which writes `"<name>": { "skills": ["<name>"] }`: a single-skill entry, once per
issue. The consolidated entry naming all of `ee-standard`'s skills has to be
written deliberately and asked for in the issues, or nine plugins arrive where
one was intended.

**Three layouts coexist there.** This is worth knowing before assuming the
incubator will accept the tree as-is:

| Shape | Example | What it looks like |
| --- | --- | --- |
| Flat skill | `skills/domain-model/` | `SKILL.md` and its supporting files; grouping only in `promote-config.json` |
| Plugin metadata beside flat skills | `skills/corpus/`, `skills/issue-workflow/` | `.claude-plugin/`, `LICENSE`, `README.md` and **no** skills — those sit flat alongside, as `skills/corpus-query/` |
| Self-contained plugin | `skills/git-summary-plugin/` | `.claude-plugin/`, `LICENSE`, `README.md` and every skill nested inside |

Three shapes in one directory is a repository mid-convention, not a rule to
follow confidently. Ask which one is wanted rather than picking; the answer
costs a sentence in an issue and the wrong guess costs a resubmission.

**The marketplace layout, by contrast, is settled — and is the one built here.**
`ee-skills/plugins/adr-toolkit/` holds exactly `.claude-plugin/`, `LICENSE`,
`README.md` and `skills/`, with one directory per skill inside. That is
`plugins/ee-standard/` in this repository, field for field, with `LICENSE` the
one piece still missing. Nothing about the local tree needs rearranging for the
destination; what needs deciding is only how it is handed over.

**`/skill-submit-new` will not find these skills.** It resolves
`<name>/SKILL.md` in the project Claude skills directory or the user-level one.
This repository has no `.claude/skills/` at all, and the skills live at
`plugins/ee-standard/skills/<name>/`. Something has to bridge that at submission
time — a copy, a symlink, or an amendment to the submission skill that teaches
it the plugin layout. **This is undecided**, and it is recorded here rather than
settled because the third option is a fifth submission and that is not a
decision to make silently.

## Corrections to `CONTRIBUTING.md`

Three statements in `ee-skills/CONTRIBUTING.md` do not match the repository.
These are worth a documentation PR (Lane B — a direct PR is permitted for doc
fixes) and are recorded here so this plan is not built on them.

| `CONTRIBUTING.md` says | Actually |
| --- | --- |
| Run `/submit-amendment`; it "opens a PR against the incubator on branch `amend/<skill>--<author>-<YYYYMMDD>`" | The skill is `/skill-submit-amend`, and it opens a **GitHub issue**. No such branch is created. |
| "A maintainer runs `scripts/promote.py` here" | `scripts/` contains `check_duplicated_files.py`, `check_plugin_license.py`, `render_readme.py`, `sync-contrib-bundle.py`. There is no `promote.py` anywhere in the repo. |
| "Preflight P1–P6 … `plugins/skill-review/skills/skill-review/scripts/preflight-check.sh`" | The script implements **P1–P11**, and there is no `skill-review` plugin. It ships as nine byte-identical copies under `skills/skill-scripts/scripts/`. |

The first is the one that matters operationally — planning for a PR you can push
commits to, and finding an issue you cannot, changes how much must be finished
before you submit.

## Gates a submission must pass

Verified against the current `preflight-check.sh` rather than the documented
list:

| Check | Requirement |
| --- | --- |
| P1 | `SKILL.md` ≤ 500 lines |
| P2 | `description` ≤ 250 characters |
| P3 | `name` field present and matching the directory |
| P4 | Invocation documented |
| P5 | `argument-hint` present where arguments are taken |
| P6 | Supporting files referenced correctly |
| P7 | `dependencies` declared in JSON |
| P8 | Skill-directory paths use `${CLAUDE_SKILL_DIR}` |
| P9 | Sub-skill invocation correct |
| P10 | No duplicate directory |
| P11 | Argument flags documented |

Plus the repository CI gates: `markdownlint-cli2`, `claude plugin validate .`,
`scripts/render_readme.py --check`, `scripts/check_plugin_license.py`,
`scripts/check_duplicated_files.py`.

P1 and P2 bind hardest on this family. `standard-adopt` is a dispatcher across
six gates and could trivially exceed 500 lines if per-control detail is inlined
— which is the second reason, after drift, that detail belongs in the register
and in `templates/` files the skill reads.

## What ships with the plugin

The directory layout these sit in is the marketplace's, verified against
`ee-skills/plugins/adr-toolkit` and already matched by `plugins/ee-standard/` —
see § What the incubator actually holds rather than a second description here.

| Artefact | Requirement |
| --- | --- |
| `LICENSE` | A copy of the repo-root Apache-2.0 file. `check_plugin_license.py` fails without it. |
| `.claude-plugin/plugin.json` | Name, version, `dependencies`. |
| `.claude-plugin/deploys.json` | The deployment contract sidecar — see [`02-skill-family.md`](02-skill-family.md). |
| `marketplace.json` entry | Category from `categories.json`. |
| `readme-meta.json` entry | `readme_summary`, `internal`. A sidecar because `claude plugin validate` rejects unknown keys in `marketplace.json`. |
| README Plugins section | Generated. Never hand-edited between the `BEGIN`/`END` markers — change the source and run `render_readme.py`. |

**Path hygiene:** hooks and scripts use `${CLAUDE_PLUGIN_ROOT}` and
`${CLAUDE_SKILL_DIR}`. A plugin is copied into its own install cache and cannot
reference files in another plugin — a hardcoded path works in development and
breaks on install. P8 covers the skill-directory case; the plugin-root case is
documented but **not** enforced by CI, so it needs review attention.

**Duplication:** if a file must exist in more than one plugin, every copy stays
byte-identical and changes in the same commit, with the group registered in
`scripts/duplicated-files.json`. `check_duplicated_files.py` fails on drift. This
is worth noting for its own sake: the marketplace has already independently
arrived at *"one definition, many references, drift is a build failure"* — the
same principle the control register applies to controls. The precedent is
established; this plan extends it rather than importing something foreign.

## The `governance` category

None of `development`, `productivity`, `workflow`, or `contributor-tooling` fits.
`workflow` is nearest but is explicitly for coordinating cross-issue processes.
`contributor-tooling` is for contributing to `ee-skills` itself.

`categories.json` states the resolution directly: *"If your plugin doesn't fit any
category cleanly, add a new entry to `categories.json` in the same PR rather than
forcing a poor fit"* — with the caveat *"Keep categories broad — five or six is
the practical ceiling."* Adding one makes five. Within budget, and a category
added at six would deserve more scepticism than this one does.

Proposed entry:

```json
{
  "key": "governance",
  "label": "Governance",
  "description": "Skills that define, deploy, or audit engineering standards across repositories — control registers, conformance checking, drift detection, and the deployment of shared CI and pre-commit configuration.",
  "examples": ["ee-standard"],
  "not_for": "Single-tool setup helpers (use `development`) or one-off environment checks (use `productivity`)."
}
```

Two consequences to handle in the same PR:

1. `categories.json` is **duplicated** into
   `plugins/ee-skills-contribute/data/categories.json`, and CI fails on drift.
   Both copies change together.
2. `render_readme.py` must be re-run so the README's Categories and Plugins
   sections regenerate.

## Submission order

The family is one plugin, and it is **not** one submission: `/skill-submit-new`
is per skill, so submission 1 is one issue per skill in the family, asking in
each for the shared `promote-config.json` entry. The two changes to *existing*
plugins are separate again and should not be bundled with any of it:

| Submission | Target | Why separate |
| --- | --- | --- |
| 1. `ee-standard` | `/skill-submit-new`, once per skill | The new plugin, plus the `governance` category. Every issue must name the same `promote-config.json` entry — `"ee-standard": {"skills": [ … ]}` — or the skills are promoted as separate single-skill plugins, which is what the tool's generated entry says by default. |
| 2. `skill-update` widening | `/skill-submit-amend` against `ee-skills-manage` | Changes an existing, widely installed skill. Reviewers assessing a new plugin and reviewers assessing a behaviour change to a shipped one are asking different questions. |
| 3. `CONTRIBUTING.md` corrections | Direct PR (Lane B) | Documentation fix, explicitly permitted as a direct PR. Useful to land first — it is small, independent, and establishes contact before the large submission arrives. |
| 4. `lint-md` amendment | `/skill-submit-amend` against `ee-skills-incubator` | Raised 2026-08-18 as [issue #530](https://github.com/EqualExperts/ee-skills-incubator/issues/530), and **mostly shipped in `lint-md@1.0.7`** on 2026-08-20: the CI template now pins `actions/checkout` to a SHA, the tool installs as an exact-pinned dev dependency with `npm ci` at the other loci, and the pre-commit hook is `repo: local` with no `rev:` copy. Two rows remain open, and both are this repository's own ADRs rather than the original report: a locus must reach the artefact the lockfile pins, where 1.0.7 still writes `npx --no-install` ([ADR 0020](adr/0020-a-locus-reaches-the-pinned-artefact.md)); and an exemption may not hide a tracked file, where a fresh deployment still writes `.claude/**` into `ignores` ([ADR 0019](adr/0019-exemptions-cannot-hide-tracked-files.md)). This is a follow-up on an open issue, not a fresh submission. |

Submission 4 was identified by this repository deploying `lint-md` and then
having to hand-edit every artefact it wrote — recorded in
[`09-phase-1.5-review.md`](09-phase-1.5-review.md) § F, including what 1.0.7
subsequently shipped. It is listed here because a submission tracked in a build
plan and absent from the promotion order is a submission that gets forgotten at
promotion time — and one that is *partly* shipped is the easiest of all to close
prematurely, because most of the report is answered.

Submission 2 is not optional dressing. Without it, `skill-update` computes the
owed-deployment report and then prints *"Already done"* underneath it whenever
every plugin happens to be current — the exact case where the new report matters
most. Ship it, or the staleness mechanism is contradicted by the summary line
sitting below it.

## Before submitting anything

The gate is the consumer repo, not the checklist. `ee-standard` must have been
deployed onto a repository that did not author it, by someone following only the
published instructions, with `standard-check` passing afterwards.

A conformance tool that has only ever been run against the repository that
defines conformance has not been tested. It has been demonstrated.
