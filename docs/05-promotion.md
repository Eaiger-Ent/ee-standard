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
issue. The consolidated entry naming all of `control-register`'s skills has to be
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
`plugins/control-register/` in this repository, field for field — **including
`LICENSE`, added 2026-08-25**, which `check_plugin_license.py` fails a plugin
for lacking. It is byte-identical to the repository root's, held so by
`tests/test_skill_links.py`, because each plugin is copied into its own install
cache and a single root licence does not follow it. Nothing about the local tree
needs rearranging for the destination; what needs deciding is only how it is
handed over.

**`/skill-submit-new` will not find these skills on its own.** It resolves
`<name>/SKILL.md` in the project Claude skills directory or the user-level one,
and the skills live at `plugins/control-register/skills/<name>/`. **Settled on
2026-08-25 by [ADR 0033](adr/0033-the-submission-tool-reaches-the-skills-by-symlink.md):**
each skill is exposed at `.claude/skills/<name>` as a tracked symlink into the
plugin, so there is one definition and a second reference rather than a copy —
and the amendment that would teach the tool about plugin layouts is submission 5
rather than a blocker on submissions 1 to 4. A copy made at submission time was
rejected: eight of them, by hand, at the one moment the content has to be right
and there is no iterate-in-review loop to fix it in.

`tests/test_skill_links.py` derives the link set from the plugin in both
directions, so a ninth skill added without a link fails the build rather than
being discovered as "not found" while eight issues are being written.

## Corrections to `CONTRIBUTING.md`

Three statements in `ee-skills/CONTRIBUTING.md` do not match the repository.
These are worth a documentation PR (Lane B — a direct PR is permitted for doc
fixes) and are recorded here so this plan is not built on them.

| `CONTRIBUTING.md` says | Actually |
| --- | --- |
| Run `/submit-amendment`; it "opens a PR against the incubator on branch `amend/<skill>--<author>-<YYYYMMDD>`" | The skill is `/skill-submit-amend`, and it opens a **GitHub issue**. No such branch is created. |
| "A maintainer runs `scripts/promote.py` here" | `scripts/` contains `check_duplicated_files.py`, `check_plugin_license.py`, `render_readme.py`, `sync-contrib-bundle.py`. There is no `promote.py` anywhere in the repo. |
| "Preflight P1–P6 … `plugins/skill-review/skills/skill-review/scripts/preflight-check.sh`" | The script implements **P1–P11**, and there is no `skill-review` plugin. It ships as nine byte-identical copies under `plugins/<plugin>/skills/skill-scripts/scripts/`. |
| "SKILL.md files are governed by the preflight P1–P6 checks" (a second line, further down) | The same error twice in one document, and the second instance is easy to miss when fixing the first. |

The first is the one that matters operationally — planning for a PR you can push
commits to, and finding an issue you cannot, changes how much must be finished
before you submit.

**All four re-verified on 2026-08-25** against an installed checkout at
`~/.claude/plugins/marketplaces/ee-skills/` (`2ce0e19`), five days after they
were first read, **and again on 2026-08-28** against the same checkout at
`d83e1c6`. None has been fixed, so submission 3 still has something to say — and
it is the submission that goes first, so its evidence is the one worth being
freshest. Also observed then, and not an error so much as a thing worth knowing
before looking for it: `skill-submit-new` is not a plugin of its own — it ships
inside `ee-skills-contribute`, where `skill-submit-amend` is a top-level plugin.
Both open issues.

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

**Run on 2026-08-25 against all eight skills** — the six gates, `register-adopt`
and `register-install` — using the marketplace's own script from an installed
checkout rather than a description of it. Every skill returned `PASS` on P1
through P11 with no check below `PASS`.

**Re-run on 2026-08-28 against all nine**, `register-variance` having joined the
family in Phase 5, and the second run is why the first was not enough. Two
things had moved in three days:

- `gate-supply-chain` **failed P2**, at 285 characters against a ceiling of 250.
  SUP-004 landed on 2026-08-27
  ([ADR 0041](adr/0041-a-pinned-digest-is-checked-against-what-was-published.md))
  and the description grew a clause to name it. That is a `FAIL`, which is a
  submission blocker, and it sat there for a day with nothing here reporting it.
- Six gates now report **`WARN` on P4** — side-effect verbs with no
  `disable-model-invocation: true`. That is
  [ADR 0035](adr/0035-a-dispatched-skill-is-reachable.md) working as ratified
  rather than a regression: a callee carrying the flag cannot be dispatched at
  all, and `register-adopt` dispatches every one of them. A `WARN` does not
  block. It is recorded here so nobody reading *"no check below `PASS`"* above
  reads the change as a defect.

*"Worth re-running before submitting"* was the plan's answer and it is not one:
a submission is the single moment there is no iterate-in-review loop to fix
anything in, which is the same argument this document makes about finishing the
skills first. `tests/test_preflight.py` now runs the marketplace's script over
every skill in the plugin. It runs **their** script rather than reimplementing
P1–P11 here — a local copy of the 250-character ceiling would be a second source
of truth for someone else's rule, free to drift from the one a submission is
judged against — and where the machine has no marketplace checkout it skips and
says so, which is the state ADR 0043 gives the plugin inventory for the same
reason. CI has none; `git push` runs the suite
([ADR 0039](adr/0039-a-push-is-a-locus.md)) in the container where the skills
are edited, which is the locus that matters for this one.

P1 and P2 bind hardest on this family. `register-adopt` is a dispatcher across
six gates and could trivially exceed 500 lines if per-control detail is inlined
— which is the second reason, after drift, that detail belongs in the register
and in `templates/` files the skill reads.

## What ships with the plugin

The directory layout these sit in is the marketplace's, verified against
`ee-skills/plugins/adr-toolkit` and already matched by `plugins/control-register/` —
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
  "examples": ["control-register"],
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
| 1. `control-register` | `/skill-submit-new`, once per skill | The new plugin, plus the `governance` category. Every issue must name the same `promote-config.json` entry — `"control-register": {"skills": [ … ]}` — or the skills are promoted as separate single-skill plugins, which is what the tool's generated entry says by default. |
| 2. `skill-update` widening | `/skill-submit-amend` against `ee-skills-manage` | Changes an existing, widely installed skill. Reviewers assessing a new plugin and reviewers assessing a behaviour change to a shipped one are asking different questions. |
| 3. `CONTRIBUTING.md` corrections | Direct PR (Lane B) | Documentation fix, explicitly permitted as a direct PR. Useful to land first — it is small, independent, and establishes contact before the large submission arrives. |
| 4. `lint-md` amendment | `/skill-submit-amend` against `ee-skills-incubator` | Raised 2026-08-18 as [issue #530](https://github.com/EqualExperts/ee-skills-incubator/issues/530), which is **closed**, and mostly answered across `lint-md@1.0.7` and `1.0.8`. **Measured against the installed 1.0.8 on 2026-08-28, one of its four rows is closed and two changed shape.** Closed: the guard that skipped Step 2b on a `grep -q "node_modules"` matching this repository's own *comment* now parses the YAML and compares the `ignores` list. Changed shape: the two disputed **values** are inputs rather than arguments, because 1.0.8 ships `local-config.md`, which is [ADR 0042](adr/0042-a-deploying-skill-reads-local-configuration.md) implemented upstream — but a key that can be set is not a default that is right, and what this amendment argues is the defaults. So three rows stand: `invocation` still defaults to `npx --no-install` ([ADR 0020](adr/0020-a-locus-reaches-the-pinned-artefact.md)) and `ignores` still defaults to a list containing `.claude/**` ([ADR 0019](adr/0019-exemptions-cannot-hide-tracked-files.md)), which local configuration fixes here and nowhere else; and the overwrite prompt still does not recognise an `ee-control:` header, so accepting it drops a provenance stamp. Two more are already filed as [#627](https://github.com/EqualExperts/ee-skills-incubator/issues/627) and belong to it: `local-config.md` says `invocation` reaches the PostToolUse hook and Step 3a is a plain `cp` of a script with the value hardcoded, and that script's shebang resolves from `PATH`. This is now a **new** amendment against a closed issue rather than a follow-up on an open one, which is what makes carrying ADR 0019's and ADR 0020's measurements — rather than their conclusions — the whole of its case. |
| 5. `skill-submit-new` layout amendment | `/skill-submit-amend` against `ee-skills-incubator` | Teaches the tool to resolve `plugins/<plugin>/skills/<skill>/`, which `preflight-check.sh` in the same marketplace already does — one of the two tools has learned about plugin layouts and the other has not. **Not a blocker**: [ADR 0033](adr/0033-the-submission-tool-reaches-the-skills-by-symlink.md) clears the path locally with symlinks, so this is the general fix for the next repository rather than the one this one waits on. Deliberately last, so it is never on the critical path. |

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

The gate is the consumer repo, not the checklist. `control-register` must have been
deployed onto a repository that did not author it, by someone following only the
published instructions, with `register-check` passing afterwards.

A conformance tool that has only ever been run against the repository that
defines conformance has not been tested. It has been demonstrated.

**That gate is Phase 4, and Phase 4 has run.** It needed a host with Docker,
which the container this repository is developed in does not have, and it got
one: `Eaiger-Ent/ee-standard-consumer` was adopted on a macOS host over
2026-08-25 and 2026-08-26, closing 6/6 and finding twenty-six things
([`12-phase-4-review.md`](12-phase-4-review.md)). The gate is open, and it was
worth having — four of the twenty-six were defects in artefacts every check here
reported healthy, including a front door that could dispatch nothing
([ADR 0035](adr/0035-a-dispatched-skill-is-reachable.md)) and a devcontainer
template that did not build.

**One thing it deliberately did not prove**, and it is the reason a criterion
survives it: the consumer installed `control-register` from this repository's own
`.claude-plugin/marketplace.json`, not from `ee-skills`. Installing *as
published* is Phase 6's last criterion rather than something Phase 4 covered, and
it cannot be tested before the promotion it tests. Saying so is the point —
"the gate has been passed" is the sentence under which a bounded deviation
becomes an unrecorded one.

### What is ready, and what it is waiting on

Everything below is done, so that when the gate opens the submission is a
submission rather than a week of preparation. Stated as a table because "the
submission is prepared" is the sort of claim that hides the one row that is not.

| Piece | State |
| --- | --- |
| Plugin layout matches the marketplace's | Done — `plugins/control-register/`, field for field |
| `LICENSE` in the plugin | Done 2026-08-25, byte-identical to the root's, held by a test |
| Preflight P1–P11 on all nine skills | Done — re-run 2026-08-28 against the marketplace's own script, one `FAIL` found and fixed, and held from here by `tests/test_preflight.py` rather than by remembering to re-run it |
| The names the `promote-config.json` entry will use | Done — [ADR 0031](adr/0031-the-plugin-is-named-for-the-register.md), and the rename landed 2026-08-25 |
| How the tool reaches the skills | Done — [ADR 0033](adr/0033-the-submission-tool-reaches-the-skills-by-symlink.md) |
| The `governance` category entry | Drafted above; lands in the same PR as the submission, in the destination repository |
| `marketplace.json` and `readme-meta.json` entries | Not stageable here — both live in `ee-skills`, and are written when the plugin is promoted |
| Submission 3 (`CONTRIBUTING.md` corrections) | Ready, and **independent of the gate** — it is a documentation PR about the destination, not a submission of this plugin |
| Submissions 1, 2, 4, 5 | **Unblocked 2026-08-26**, when Phase 4 closed. Submission 4 is three rows smaller than it was — see its entry above |

Submission 3 was for a long time the one row that could go today, and it is
still the one that goes first — but the reason has strengthened rather than
lapsed. It was listed as ready rather than sent because the argument for landing
it first, establishing contact before the large submission arrives, is worth
little when the large submission is still weeks away. Phase 4 closing removed
that objection: submission 1 is now next in the order rather than next quarter,
so the small independent PR is doing the job it was put first to do.

Every one of these is an act with a person on the other end of it, in another
organisation's repository, and none is raised without being asked for.
