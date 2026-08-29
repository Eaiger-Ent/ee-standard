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
            │                     one pull request per SKILL, not per plugin
            ▼
  the incubator gates, run locally, before anything is pushed
            │
            ▼
  branch + pull request on EqualExperts/ee-skills-incubator
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

**The transport changed on 2026-08-28, and this section was rewritten the same
day.** Everything below was measured against the installed marketplace checkout
at `~/.claude/plugins/marketplaces/ee-skills/` (`0ff6b28`), and
[`15-phase-6-review.md`](15-phase-6-review.md) § The transport changed records
what it replaced and how a re-verification earlier that morning missed it.

Three properties of this route shape the build plan:

**Submission is a branch and a pull request, not an issue.** Both
`skill-submit-new` and `skill-submit-amend` build a branch —
`new/<skill>--<author>-<YYYYMMDD>` and `amend/<skill>--<author>-<YYYYMMDD>` — in
a reusable incubator checkout, run the incubator's own gates on it, and only
then push and open a pull request against `EqualExperts/ee-skills-incubator`.
The submission travels as commits: *"Nothing is serialised into text: the commit
is the submission, and a commit is its own file manifest"* (#608, #611, #615).
You still cannot self-merge, and promotion is still someone else's action — but
the branch is yours, `submit-branch.sh` is idempotent (*"PR already open for
$BRANCH — branch updated, no new PR created"*), so **there is now an
iterate-in-review loop under your control.**

That removes the argument this document used to make for finishing everything
first, and the rule survives on a better one: **the gates run before the push**
(#637). `test-local.sh` Gates 1–4 — plugin validation, smoke test, trigger
fidelity, and a rubric evaluation that calls the API — are run on the committed
branch, and a submission that fails one never reaches a pull request at all. So
an unfinished skill is not something you fix in review; it is something that
does not get filed. Testing against a real consumer repo before promotion is
attempted was never contingent on the transport anyway.

**Promotion is a maintainer action.** Whatever the incubator-to-marketplace step
is mechanically, it is not yours to run. Budget calendar time for it.

**The unit of submission is a skill, not a plugin.** `/skill-submit-new` takes a
skill name, reads one `SKILL.md`, and opens one pull request. A plugin shipping
nine skills is nine pull requests. This is the correction that matters most to
Phase 6's shape, it is the one of the three that the transport change did **not**
alter, and § What the incubator actually holds sets out what follows from it.

### What a submission now needs from the machine it runs on

None of this was in the plan before 2026-08-28, because none of it was true of a
tool that posted an issue body. Each was read from the installed
`skill-submit-new` and `skill-submit-amend` and, where it is a fact about this
container, measured here:

| Requirement | State on this machine |
| --- | --- |
| `gh` authenticated with push access to `EqualExperts/ee-skills-incubator`, or able to fork it | **Push access yes, ambient `gh` no.** The scripts invoke `gh` themselves, and this container's `GITHUB_TOKEN` is scoped to `Eaiger-Ent`: plain `gh api repos/EqualExperts/ee-skills-incubator` returns 404. `EE_SKILLS_GITHUB_TOKEN` has `push` and `admin`, so a submission must be run with it in the environment as `GH_TOKEN` — the `gh-ee-skills` wrapper cannot help, because it scopes a single invocation and the invocations are inside someone else's script |
| `claude` and `uv` on `PATH` | Both present |
| An Anthropic credential — `ANTHROPIC_API_KEY` or `CLAUDE_CODE_OAUTH_TOKEN` — for Gate 4 | Neither is exported in an ordinary shell here. `CLAUDE_CODE_OAUTH_TOKEN` is in `.devcontainer/.env`, so this is a `set -a; . .devcontainer/.env; set +a` away rather than a gap. Without it the scripts **stop**: the gates are refused rather than degraded, because Gate 4 skipping without failing would push an ungated submission under a "gates passed" banner |
| `tests/<skill>/triggers.yaml` and `tests/<skill>/prompt.txt` | **Drafted 2026-08-29** in [`promotion/fixtures/`](promotion/fixtures/README.md), one directory per skill, with the Q4 rationale beside them. The tool still builds the files it commits from its own Q1–Q4, so these are answers to review rather than files it reads — which turns nine live Q&A sessions into nine readings. `tests/test_submission_fixtures.py` derives the set from the plugin in both directions and holds each file to the tool's own validation |
| `SKILL_SUBMIT_CHECKOUT` — where the incubator checkout lives | Unset, so it defaults to `~/.cache/ee-skills-incubator`. It must have no uncommitted changes; the script refuses rather than resetting work it finds |

#### The drafted answers

The tool asks four questions per skill and commits two files built from the
answers. [`promotion/fixtures/`](promotion/fixtures/README.md) holds a drafted
answer to each, one directory per skill — `triggers.yaml`, `prompt.txt`, and
`rationale.txt` for Q4, which is typed into a question box and never rendered.

**Nothing reads them**, and that is the point of writing them down: the tool
resolves its fixtures from its own Q&A into temp files, so without a draft the
answers are composed live, nine times, at the one moment there is no undo. A
test derives the set from the plugin in both directions, so a tenth skill added
without answers fails the build rather than being noticed with eight
submissions already open.

Two things the drafting found, both about `prompt.txt`. **The smoke test runs
it for real** — `claude -p "$(cat prompt.txt)"` under
`--permission-mode bypassPermissions`, ten-second deadline — but in a **fresh
empty temp repository** holding only a shim of the skill under test, so nothing
in a real repository is at risk, and with no `controls.yaml` there every gate
stops at its own pre-flight, which is the most inert thing this family can be
asked to do. The gate's only assertion is that the reply is not
`Unknown command`. And **`register-adopt` gets no natural-language entries**: it
is the one skill still carrying `disable-model-invocation: true`, and Q2 is
skipped entirely for such a skill.

#### The submitting shell

Three of the five rows above are environment, and together they are one command.
Run every `/skill-submit-new` and `/skill-submit-amend` from a shell prepared
this way — **verified on 2026-08-29**, which is what the last line is for:

```bash
set -a; . .devcontainer/.env; set +a   # CLAUDE_CODE_OAUTH_TOKEN, for Gate 4
unset GITHUB_TOKEN                     # scoped to Eaiger-Ent; it shadows the next line
export GH_TOKEN="$EE_SKILLS_GITHUB_TOKEN"

gh api repos/EqualExperts/ee-skills-incubator --jq .permissions.push   # true, or stop
```

`unset` rather than a prefix, because `gh` honours one of `GH_TOKEN`/`GITHUB_TOKEN`
at a time and the scripts invoke `gh` themselves — this is the whole reason the
`gh-ee-skills` wrapper cannot serve here, since it scopes a single invocation and
the invocations are somebody else's. The last line is not ceremony: it is the
one check that distinguishes *can push* from *cannot see*, which is the
distinction the next paragraph is about.

**Step 1a reads a 404 as good news, and on this machine a 404 is ambiguous.**
Before doing anything else, `skill-submit-new` runs
`gh api repos/EqualExperts/ee-skills-incubator/contents/skills/<name>` and treats
failure as *the skill is new — continue*. A token that cannot see the repository
at all returns exactly that, so with the ambient `GITHUB_TOKEN` the check passes
for every name, including one already there. It is the failure this repository
refuses everywhere else — SEC-001 raising rather than reading an omitted
`security_and_analysis` as "off", ADR 0043 giving a missing plugin inventory a
third state instead of reading it as agreement — and it is submission 6 below.

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
rejected: eight of them, by hand, at the one moment the content has to be right.
The transport has changed since — a branch can be amended where an issue body
could not — but the decision does not move with it: the copies would be nine
files diverging from the plugin between submissions, which is the drift this
repository exists to prevent rather than a review-loop problem.

`tests/test_skill_links.py` derives the link set from the plugin in both
directions, so a ninth skill added without a link fails the build rather than
being discovered as "not found" while eight submissions are being written.

## Corrections to `CONTRIBUTING.md`

Three statements in `ee-skills/CONTRIBUTING.md` do not match the repository.
These are worth a documentation PR (Lane B — a direct PR is permitted for doc
fixes) and are recorded here so this plan is not built on them.

| `CONTRIBUTING.md` says | Actually |
| --- | --- |
| Run `/submit-amendment`; it "opens a PR against the incubator on branch `amend/<skill>--<author>-<YYYYMMDD>`" | **Only the name is wrong now:** the skill is `/skill-submit-amend`. Since 2026-08-28 it does open a pull request, on exactly that branch — `submit-branch.sh` builds `amend/${NAME}--${AUTHOR}-$(date -u +%Y%m%d)`. This row was two errors and is one. |
| "A maintainer runs `scripts/promote.py` here" | `scripts/` contains `check_duplicated_files.py`, `check_plugin_license.py`, `render_readme.py`, `sync-contrib-bundle.py`. There is no `promote.py` anywhere in the repo. |
| "Preflight P1–P6 … `plugins/skill-review/skills/skill-review/scripts/preflight-check.sh`" | The script implements **P1–P11**, and there is no `skill-review` plugin. It ships as nine byte-identical copies under `plugins/<plugin>/skills/skill-scripts/scripts/`. |
| "SKILL.md files are governed by the preflight P1–P6 checks" (a second line, further down) | The same error twice in one document, and the second instance is easy to miss when fixing the first. |

The first used to be the one that mattered operationally, for a reason that has
inverted: planning for a PR you can push commits to and finding an issue you
cannot is no longer the risk, because the tool now does what the sentence says.
`CONTRIBUTING.md` was describing the transport correctly the whole time and this
document recorded it as wrong — accurately, when it was written, which is the
argument for dating a measurement rather than stating a fact.

**All four re-verified on 2026-08-25** against an installed checkout at
`~/.claude/plugins/marketplaces/ee-skills/` (`2ce0e19`), five days after they
were first read, again on 2026-08-28 at `d83e1c6`, **and re-measured the same
evening at `0ff6b28`**, which is the run that found the transport change and
shrank the first row. The measurements behind rows 2 to 4 at `0ff6b28`:
`scripts/` holds those four files and no `promote.py`; `preflight-check.sh`
implements P1 to P11 and ships as nine copies of one md5 under
`plugins/<plugin>/skills/skill-scripts/scripts/`, with no `skill-review` plugin
among the forty-nine; and the second `P1–P6` line is still there. None of the
four has been fixed, so submission 3 still has something to say — and it is the
submission that goes first, so its evidence is the one worth being freshest.

Two things worth knowing before looking for them, neither an error:
`skill-submit-new` is not a plugin of its own — it ships inside
`ee-skills-contribute`, where `skill-submit-amend` is both a top-level plugin
**and** a skill inside `ee-skills-contribute`, two byte-identical copies that
moved together in the same hour. Both open pull requests.

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

**And, from 2026-08-28, four gates that run before the push rather than after
it.** `submit-branch.sh` runs the incubator's `test-local.sh` Gates 1–4 on the
committed branch — plugin validation, smoke test, trigger fidelity, and a rubric
evaluation — and pushes only if all four pass, because `gh pr create` is what
starts CI and gating afterwards would spend a full CI run, the paid rubric call
among it, on a tree no gate had seen (#637). Two of the four are new information
for this family: Gate 3 reads the `triggers.yaml` that does not exist yet for
any of the nine, and Gate 4 needs an Anthropic credential on the machine. The
gates are **refused rather than degraded** when they cannot run in full, which is
the same shape as this repository's own `UNCLASSIFIED`.

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

*"Worth re-running before submitting"* was the plan's answer and it is not one.
The reason has changed with the transport and has not weakened: the incubator's
own gates now run on the committed branch **before** it is pushed, so a
`FAIL` here is not something a reviewer sees and asks about — it is a submission
that is never filed, discovered by a script at the moment the operator expected
a pull-request URL. `tests/test_preflight.py` now runs the marketplace's script over
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

## The `promote-config.json` entry

The one thing nine pull requests have to agree about, and the one the tool
writes wrongly by default. `apply-promote-entry.py` applies
`"<name>": {"skills": ["<name>"], "description": …}` on each branch, so the
default outcome of submission 1 is **nine single-skill plugins**. The entry
below is what each branch must carry instead — one key under `plugins`, naming
all nine skills. (`skills/promote-config.json` has three top-level keys —
`plugins`, `incubatorOnly` and `removed`; this belongs under the first.)

```json
"control-register": {
  "skills": [
    "register-adopt",
    "gate-secrets",
    "gate-quality",
    "gate-supply-chain",
    "gate-build",
    "gate-iac",
    "gate-repo",
    "register-install",
    "register-variance"
  ],
  "description": "Deploys and verifies the Equal Experts control standard. The register in controls.yaml defines what conformant means; the gate skills write the artefacts, and register-check audits them."
}
```

It is written out here rather than left as an ellipsis because it is the text an
operator pastes onto nine branches, and because the failure it prevents is
silent: nine correct submissions, each individually gated and merged, arriving
as nine plugins nobody asked for. **It is not a second copy.**
`tests/test_promote_entry.py` derives both fields from the plugin — the skill
list from `plugins/control-register/skills/`, the description from
`.claude-plugin/plugin.json` — so a tenth skill, or a description reworded in
the plugin and not here, fails the build. The order is the dispatcher first,
then the six gates it dispatches, then the two skills that are on nobody's
route; the test compares the set, because ordering is presentation and a rule
about it would fail a build over a preference.

## Submission order

The family is one plugin, and it is **not** one submission: `/skill-submit-new`
is per skill, so submission 1 is one pull request per skill in the family, each
carrying the **same** `promote-config.json` entry — the consolidated one below,
not the single-skill entry the tool generates. The two changes to *existing*
plugins are separate again and should not be bundled with any of it:

| Submission | Target | Why separate |
| --- | --- | --- |
| 1. `control-register` | **Raised 2026-08-29 as [incubator#657](https://github.com/EqualExperts/ee-skills-incubator/pull/657) — one pull request, not nine** | The new plugin, plus the `governance` category. Every pull request must carry the same `promote-config.json` entry — § The `promote-config.json` entry below — or the skills are promoted as separate single-skill plugins, which is what the tool's generated entry says by default. Nine of them, and `apply-promote-entry.py` writes the generated one on each branch, so the entry is corrected on the branch rather than asked for in prose. |
| 2. `skill-update` widening | **Withdrawn 2026-08-29 — it shipped.** | Measured against the installed skill before writing it: `skill-update` already has Step 2.7 *"Is a deployment owed?"*, a `DEPLOYMENT_STATE`, a *Deployment owed* output block, and the rule **"Never emit Already done over an owed deployment"** — stating this submission's own argument almost verbatim. Nothing to raise. Kept in the table because a submission that vanishes is indistinguishable from one nobody noticed. |
| 3. `CONTRIBUTING.md` corrections | Direct PR (Lane B) | Documentation fix, explicitly permitted as a direct PR. Useful to land first — it is small, independent, and establishes contact before the large submission arrives. |
| 4. `lint-md` amendment | `/skill-submit-amend` against `ee-skills-incubator` | Raised 2026-08-18 as [issue #530](https://github.com/EqualExperts/ee-skills-incubator/issues/530), which is **closed**, and mostly answered across `lint-md@1.0.7` and `1.0.8`. **Measured against the installed 1.0.8 on 2026-08-28, one of its four rows is closed and two changed shape, and re-measured against 1.0.9 the same evening with all three still standing** — the defaults in `local-config.md` are byte-for-byte the ones 1.0.8 shipped, and `SKILL.md` still mentions no `ee-control` header anywhere. Closed: the guard that skipped Step 2b on a `grep -q "node_modules"` matching this repository's own *comment* now parses the YAML and compares the `ignores` list. Changed shape: the two disputed **values** are inputs rather than arguments, because 1.0.8 ships `local-config.md`, which is [ADR 0042](adr/0042-a-deploying-skill-reads-local-configuration.md) implemented upstream — but a key that can be set is not a default that is right, and what this amendment argues is the defaults. So three rows stand: `invocation` still defaults to `npx --no-install` ([ADR 0020](adr/0020-a-locus-reaches-the-pinned-artefact.md)) and `ignores` still defaults to a list containing `.claude/**` ([ADR 0019](adr/0019-exemptions-cannot-hide-tracked-files.md)), which local configuration fixes here and nowhere else; and the overwrite prompt still does not recognise an `ee-control:` header, so accepting it drops a provenance stamp. Two more are already filed as [#627](https://github.com/EqualExperts/ee-skills-incubator/issues/627) and belong to it: `local-config.md` says `invocation` reaches the PostToolUse hook and Step 3a is a plain `cp` of a script with the value hardcoded, and that script's shebang resolves from `PATH`. This is now a **new** amendment against a closed issue rather than a follow-up on an open one, which is what makes carrying ADR 0019's and ADR 0020's measurements — rather than their conclusions — the whole of its case. |
| 5. `skill-submit-new` layout amendment | `/skill-submit-amend` against `ee-skills-incubator` | Teaches the tool to resolve `plugins/<plugin>/skills/<skill>/`, which `preflight-check.sh` in the same marketplace already does — one of the two tools has learned about plugin layouts and the other has not. Re-read at `0ff6b28`: the resolution rule is unchanged by the transport change, so [ADR 0033](adr/0033-the-submission-tool-reaches-the-skills-by-symlink.md)'s symlinks still carry submissions 1 to 4 and this is still the general fix for the next repository rather than the one this one waits on. Deliberately last, so it is never on the critical path. |
| 6. `skill-submit-new` reads a 404 as an answer | `/skill-submit-amend` against `ee-skills-incubator` | Added 2026-08-28. Step 1a asks the API whether `skills/<name>` already exists and treats **any** failure as *it does not*, so a token that cannot see a private repository — this container's ambient one — clears every name. The fix is small (distinguish 404 from 401/403, and stop rather than continue on the latter), the argument is one this repository has made four times about its own asserts, and it is worth raising **before** submission 1 rather than after, because submission 1 is what would run into it nine times. Bundled with 5 or separate is the maintainer's call; both touch one skill. |
| 7. `lint-md` where an adopter can reach it | **Closed 2026-08-29** as [ee-skills#551](https://github.com/EqualExperts/ee-skills/issues/551) — a known limitation, already planned for | Added 2026-08-29 with [ADR 0044](adr/0044-the-adopter-installs-from-the-public-marketplace.md). `ee-skills` is private, `lint-md` owns the whole DOC-001 lifecycle, and an adopter outside Equal Experts therefore satisfies one control by hand. The ask is that `lint-md` be reachable to them — published to a public marketplace, or mirrored. **Nothing here waits on the answer**, which is the point of raising it as its own submission rather than as a precondition: ADR 0044 decided what this repository does while the answer is no, and a yes makes part 2 of it unnecessary without touching part 1. |

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

**Promotion adds a route and does not replace one**
([ADR 0044](adr/0044-the-adopter-installs-from-the-public-marketplace.md)).
`ee-skills` is private, so an `ee-skills` install serves people inside Equal
Experts; [`08-adopting.md`](08-adopting.md) § 0.0 goes on naming the public
`Eaiger-Ent/ee-standard` marketplace, before promotion and after it, and
`tests/test_adopter_guide.py` fails a guide that names a second address. Read
every criterion below with that in mind: *installable from the marketplace*
means the plugin installs cleanly from the published copy, not that the
published copy is the one an outside adopter is sent to.

**One thing Phase 4 deliberately did not prove**, and it is the reason a
criterion survives it: the consumer installed `control-register` from this
repository's own `.claude-plugin/marketplace.json`, not from `ee-skills`. Installing *as
published* is Phase 6's last criterion rather than something Phase 4 covered, and
it cannot be tested before the promotion it tests. Saying so is the point —
"the gate has been passed" is the sentence under which a bounded deviation
becomes an unrecorded one.

### What is ready, and what it is waiting on

Everything below was done, so that when the gate opened the submission would be
a submission rather than a week of preparation. Stated as a table because "the
submission is prepared" is the sort of claim that hides the one row that is not
— and on 2026-08-28 the transport change put two rows in it that are not.

| Piece | State |
| --- | --- |
| Plugin layout matches the marketplace's | Done — `plugins/control-register/`, field for field |
| `LICENSE` in the plugin | Done 2026-08-25, byte-identical to the root's, held by a test |
| Preflight P1–P11 on all nine skills | Done — re-run 2026-08-28 against the marketplace's own script, one `FAIL` found and fixed, and held from here by `tests/test_preflight.py` rather than by remembering to re-run it |
| The names the `promote-config.json` entry will use | Done — [ADR 0031](adr/0031-the-plugin-is-named-for-the-register.md), and the rename landed 2026-08-25 |
| How the tool reaches the skills | Done — [ADR 0033](adr/0033-the-submission-tool-reaches-the-skills-by-symlink.md) |
| The consolidated `promote-config.json` entry | Done 2026-08-28 — written out in § The `promote-config.json` entry and derived from the plugin by `tests/test_promote_entry.py`, rather than left as an ellipsis nine branches would each have to guess |
| The `governance` category entry | Drafted above; lands in the same PR as the submission, in the destination repository |
| `tests/<skill>/triggers.yaml` and `prompt.txt`, nine sets | **Not done, and not stageable here.** The tool builds them from its own Q1–Q4 and will not commit a branch until the operator has confirmed each pair. It is the largest remaining piece of submission 1, it is interactive, and until 2026-08-28 nothing in this plan knew it existed |
| A machine that can actually push the branch | **Done 2026-08-29** — § The submitting shell, three lines, verified by asking the API for `permissions.push` and getting `true`. It was not obvious: `submit-branch.sh` invokes `gh` directly, the ambient `GITHUB_TOKEN` here cannot see `EqualExperts/ee-skills-incubator`, and `gh` honours one token variable at a time, so the fix is to `unset` rather than to prefix |
| `marketplace.json` and `readme-meta.json` entries | Not stageable here — both live in `ee-skills`, and are written when the plugin is promoted |
| Submission 3 (`CONTRIBUTING.md` corrections) | Ready, and **independent of the gate** — it is a documentation PR about the destination, not a submission of this plugin |
| Submissions 1, 2, 4, 5 | **Unblocked 2026-08-26**, when Phase 4 closed. Submission 4 is three rows smaller than it was — see its entry above |
| Submission 6 (`skill-submit-new` reads a 404 as an answer) | Found 2026-08-28, measured rather than reasoned about; ready to raise, and worth raising before submission 1 rather than after |
| Submission 7 (`lint-md` where an adopter can reach it) | Ready 2026-08-29. It is the one submission whose answer changes nothing here either way, which is why it is last and why no criterion is written against it |

Submission 3 was for a long time the one row that could go today, and it is
still the one that goes first — but the reason has strengthened rather than
lapsed. It was listed as ready rather than sent because the argument for landing
it first, establishing contact before the large submission arrives, is worth
little when the large submission is still weeks away. Phase 4 closing removed
that objection: submission 1 is now next in the order rather than next quarter,
so the small independent PR is doing the job it was put first to do.

## What was raised, and when

All of it went out on 2026-08-29, in the order this document sets.

| Submission | Where it went |
| --- | --- |
| 3. `CONTRIBUTING.md` corrections | [ee-skills#550](https://github.com/EqualExperts/ee-skills/pull/550) — Lane B direct PR |
| 5 + 6. `skill-submit-new` | [incubator#655](https://github.com/EqualExperts/ee-skills-incubator/pull/655) — **one PR, forced**: `/skill-submit-amend` builds `amend/<skill>--<author>-<date>`, so two amendments to one skill on one day is one branch |
| 4. `lint-md` | [incubator#656](https://github.com/EqualExperts/ee-skills-incubator/pull/656) — **two rows, not three**; see below |
| 7. `lint-md` reachability | [ee-skills#551](https://github.com/EqualExperts/ee-skills/issues/551) — **answered and closed the same day**: *"This is a current feature of the repository and is planned to be fixed in the future. Closing as a known feature."* |
| 1. `control-register` | [incubator#657](https://github.com/EqualExperts/ee-skills-incubator/pull/657) — **one PR, not nine** |
| 2. `skill-update` widening | Not raised. It shipped upstream; see its row above |

**Submission 1 is one pull request because nine would have been worse.** Nine
branches each adding the same `"control-register"` key to `promote-config.json`
is eight textual conflicts on an identical addition, and an entry naming eight
skills that do not exist until the last one merges. `check-promote-registration.py`
takes a *list* of changed skill directories and reported all nine registered.
The PR says so and offers to split them.

**Submission 4 lost a row to measurement.** It was going to argue that
`invocation` should default to `node_modules/.bin/markdownlint-cli2`, on the
premise — stated in `local-config.md` itself, and in
[ADR 0020](adr/0020-a-locus-reaches-the-pinned-artefact.md) here — that
`npx --no-install` falls through to `PATH`. **That does not reproduce on npm
11.17.0.** With a real `markdownlint-cli2` first on `PATH`, no `package.json`
and no `node_modules`, `npx --no-install markdownlint-cli2 --version` exits `1`
against the registry rather than running it. The row was withdrawn rather than
argued, and the measurement sent as information instead.
[`15-phase-6-review.md`](15-phase-6-review.md) § The fifth slice records what
that means for ADR 0020, whose decision survives and whose stated mechanism does
not.

Every one of these is an act with a person on the other end of it, in another
organisation's repository, and none was raised without being asked for.

**And every one of them is now a branch pushed to that repository rather than an
issue filed against it**, which raises what "asked for" has to cover: a
submission that goes wrong leaves a branch and an open pull request in someone
else's repository, not a comment. Nothing about the rule changes; what changes is
that a mistaken submission is now something a maintainer has to clean up.
