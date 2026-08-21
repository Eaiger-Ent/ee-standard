# Phase 2 review — the gates

The evidence for Phase 2's criteria, so that
[`04-build-plan.md`](04-build-plan.md) can stay a list of outstanding work.
A criterion there is one checkable sentence; the reasoning for a tick is here.

**Scope of this record.** Two slices so far.

The first covered the plugin skeleton, the assert entry point gates verify
through, and `gate-secrets` — the reference implementation the plan puts first
*"as the reference implementation… whatever shape works for it works for the
rest"*.

The second is `gate-quality`, recorded in § The second gate below. It is the
first gate that owns more than one control, so it is where "grouped by the
artefact they write" stops being a sentence in a design document and becomes a
shape three controls have to share. The other four gates, `standard-adopt` and
the devcontainer template are still outstanding, and the criteria that name them
are still open.

## What closed, and how

### `gate-secrets` deploys onto a repo with none of its config

The subject cannot be this repository. It wired `gitleaks` by hand in Phase 0.5,
long before there was a gate to write it, so "a repo with none of its config" is
a state it has not been in since. The subject is a throwaway repository —
`tests/test_gate_secrets_deploy.py` builds it: one source file, one CI workflow
that gates on `push` and `pull_request`, and nothing whatever about secrets.

Before deploying, run against that repository with this register:

```text
SEC-001  FAIL
  ✓ command: gitleaks detect --no-banner --redact — exit 0
  ✗ file: secrets_gate_wired_at_all_loci — pre-commit locus — no hook runs
    'gitleaks'; ci locus — no gating step runs 'gitleaks'
  ✗ file: provenance_stamp_present — no tracked file carries a provenance stamp
    naming 'gate-secrets'
  - remote: github_push_protection_enabled — requires credentials (Phase 3)
exit=1
```

After rendering the skill's own templates with the register's values and writing
them where Steps 2 and 3 say:

```text
SEC-001  SKIPPED (no credentials)
  ✓ command: gitleaks detect --no-banner --redact — exit 0
  ✓ file: secrets_gate_wired_at_all_loci — pre-commit and ci loci both reach
    gitleaks through 'gitleaks'
  ✓ file: provenance_stamp_present — gate-secrets stamped 2 artefacts
    (.github/workflows/ci.yml, .pre-commit-config.yaml), each naming a control
    the register defines
  - remote: github_push_protection_enabled — requires credentials (Phase 3)
exit=3
```

**Exit 3, and not 0, is the result the criterion wanted.** The criterion says
*PASS for its local loci*, and that is exactly what this says: two local blocks
verified, one remote block not verified and not claimed. A `0` here would assert
that GitHub push protection is on, which this run has no evidence for
([ADR 0016](adr/0016-exit-codes-for-unverifiable-controls.md)).

**And it was watched failing.** Phase 2's own note — *"a verify step that has
never been observed failing is not known to work"* — is applied by deleting each
artefact in turn from the deployed repository and re-running: the CI steps, the
pre-commit hook, both stamps, and finally by adding a `.gitleaksignore` entry
that hides a tracked source file. Each is a `FAIL` naming what went.

**What this does not establish.** The artefacts come from the skill's shipped
templates — one copy of the content — and the test proves those artefacts are
accepted where a repository had none. It does not prove that a model follows the
prose in `SKILL.md`, and no test can. That distinction is why the criterion is
worded around what `standard-check` reports rather than around the skill running
to completion.

### Gates and checker share one assert implementation

The criterion asks for this to be *"verified by there being one copy, not by
comparing two"*. Three things make that so:

1. The one copy is `standard_check.asserts` — a single namespace merging
   `asserts_file` and `asserts_command`, which the register's closed assert set
   is validated against.
2. The only way a skill reaches it is `standard-check run --control <ID>`, added
   here. It runs the control's own verify blocks through `run_control`, the same
   function the full audit calls. A gate cannot pass itself where the auditor
   would fail it, because it is the auditor that answers.
3. `test_the_gate_verifies_through_the_checker_and_not_otherwise` fails a skill
   that deploys a control it does not name on that command line. A future gate
   that read its own files back would pass every other structural check and be
   caught by this one.

The narrowing is a narrowing and nothing more, which is the part worth testing:
an unknown id exits `2` rather than verifying an empty set and exiting `0` — a
gate reporting success over a typo would be § A's defect with a typo for a
cause. `--tier` and `--control` both narrow and neither widens. A narrowed run
carries no meta-controls, because a gate verifying artefacts it just wrote has
no business reporting on whether some other control is past its review date.

## What Phase 2 found, in the register and in the checker

### SEC-001 was checked at one of the three loci it declares

The control declares `locus: [pre-commit, ci, remote]`.
`precommit_hook_present` read the hook, the remote block honestly defers to
Phase 3, and **nothing at all read the ci locus**. A repository could delete its
secret-scanning job and keep SEC-001 green.

This is § A's defect and the shape § H found in GOV-001 — a control declared at
three loci and checked at one. `secrets_gate_wired_at_all_loci` subsumes the
hook check and adds the job, reusing `_hook_mentions` and `_ci_run_mentions` so
that the rule rejecting a `workflow_dispatch`-only workflow is inherited rather
than restated.

It also applies [ADR 0019](adr/0019-exemptions-cannot-hide-tracked-files.md) to
the one exemption list this gate has. SEC-001 is `variance: forbidden` with
`baseline: null`: a `.gitleaksignore` entry whose fingerprint names a file git
tracks hides authored content from a control that admits no tolerated
violations, and an entry naming nothing tracked scopes the scanner instead. Both
directions are tested, because a blanket "no exemptions" rule breaks the second
— which is the mistake ADR 0019 was written after making.

### A stamp nothing reads back is a claim, not a record

`provenance_stamp_present` is the criterion *every gate writes a provenance
stamp its own verify step reads back*, made mechanical. What it checks is
**soundness, not currency**: a stamp behind the register is staleness, which
[`00-concepts.md`](00-concepts.md) § Notify, never redeploy says is reported and
never enforced, so failing a build over one would be enforcing redeployment. A
stamp naming a control the register does not define, or claiming a contract the
register has not reached, is a defect and fails.

Which gate deploys a control is now recorded once. `deployed_by` names it, the
assert's `skill` argument reads it back, and the **schema rejects a register
where the two disagree** — two fields in one entry saying who deploys a control,
free to drift apart, would be theme T-2 inside the one file that exists to
prevent it.

The stamp pattern itself moved to `standard_check.provenance`. It had two
definitions: the checker had none and the test had a regex, so the format the
test accepted and the format anything else accepted were free to differ. The
test now also requires *every* marker in a file to parse, not merely the first —
a partly-owned file carries one stamp per section, and a malformed second one
was hiding behind a well-formed first.

### The register recorded a value only a bot could read

`gate-secrets` installs the scanner from a pinned release, and needs to know
which repository the release comes from. The register carried that nowhere: it
existed only inside `# renovate: datasource=github-releases depName=gitleaks/gitleaks`,
an annotation written for a bot.

This is the deploy-from-nothing exercise doing its job — the gap was invisible
until something had to read the register without already knowing the answer.
`tools.<tool>.release_repo` records it as a field, validated as `owner/name` and
rejected on a lockfile-sourced tool that has no release to download. A fork or
an internal mirror is a reasonable thing for a repository to differ on without
the checker changing, so it answers *yes* to
[ADR 0018](adr/0018-register-checker-boundary.md)'s test.

It folds into contract 11 rather than opening a twelfth: contract 11 has not
landed anywhere, so nothing could be stale against it.

### This repository's own SEC-001 artefacts were unstamped

Both were hand-wired in Phase 0.5. They are now stamped, and each stamp says
**adopted rather than deployed from nothing** — they were written before there
was a gate to write them, and a stamp claiming otherwise would be the
overstatement § F found in `CLAUDE.md`. The pre-commit hook's content is
byte-identical to what `templates/precommit-hook.yaml` renders.

`.pre-commit-config.yaml` now carries two stamps, one per control that owns a
hook in it. That is the documented shape — a file a skill owns *in part* carries
the stamp above the section it owns — and it is why the well-formedness test had
to stop reading only the first stamp in a file.

## Preflight P1–P11

Run against `plugins/ee-standard/skills/gate-secrets` with
`preflight-check.sh`, which ships in `ee-skills` and cannot run in this
repository's CI. Re-run on 2026-08-20 against `skill-preflight@0.1.15` after
`/skill-update` moved it three versions — same result, and the check script is
byte-identical to 0.1.12's, so the version jump was in the skill around it:

```text
P1 line count           PASS  305 / 500
P2 description length   PASS  211 / 250
P3 name field           PASS  gate-secrets
P4 invocation           PASS  side-effect verbs present; disable-model-invocation=true
P5 argument-hint        PASS
P6 supporting files     PASS  all sibling files referenced from SKILL.md
P7 dependencies.json    PASS  not required
P8 ${CLAUDE_SKILL_DIR}  PASS  every path ref resolves
P9 sub-skill invocation PASS  none
P10 duplicate directory PASS  one location
P11 argument flags      PASS
overall: PASS, 0 failures
```

The criterion says *every* SKILL.md, and five gate skills plus three
`standard-*` skills do not exist yet, so it stays open. What this run
establishes is that the shape the rest will copy passes today.

`tests/test_plugin.py` holds the checks only this repository can make — that the
sidecar names controls the register defines, that the templates' stamps parse
once the register fills them, and that **no value the register pins appears
anywhere under `plugins/`**. The last is the rule that stops a gate becoming a
second register, and it is a grep rather than a convention.

## The second gate

`gate-quality` deploys LNT-001, TYP-001 and TST-001. Three controls and one
skill because they share two files: three skills writing the same
`.pre-commit-config.yaml` and the same workflow in turn would each rewrite what
the last one wrote.

### It deploys onto a repo with none of its config

Same shape as `gate-secrets`' criterion, same reason this repository cannot be
the subject: it has run a linter, a type checker and a test suite since Phase
0.5. `tests/test_gate_quality_deploy.py` builds the subject — Python source, a
devcontainer, a CI workflow that gates on `push` and `pull_request` and installs
from a lockfile, and no quality gate of any kind.

Before deploying, all three fail, and they name the loci rather than the files:

```text
LNT-001  FAIL  editor locus — no editor configuration installs <extension>;
               pre-commit locus — no <tool> hook;
               ci locus — no gating step runs <invocation>
TYP-001  FAIL  … and: no tracked file carries a provenance stamp naming
               'gate-quality'
TST-001  FAIL  no CI step runs the test command
```

After deploying from the shipped templates, `standard-check run --control
LNT-001 --control TYP-001 --control TST-001` exits `0` — not `3`. That
difference from `gate-secrets` is the point rather than an accident: all three
controls verify from files and none declares a `remote` locus, so there is
nothing Phase 3 is holding back and nothing to round up.

### Every artefact broken in turn, and watched failing

A verify step that has never been observed failing is not known to work. Nine
breakages, each producing the verdict that names it. Run twice, against two
subjects, because they answer different questions: against the throwaway
repository in `tests/test_gate_quality_deploy.py`, where six of them are kept as
tests so a regression is caught rather than remembered; and against a scratch
copy of **this** repository, which is the deployment an adopter would read as
the worked example. The messages quoted below are that second run's — a real
repository's filenames rather than a fixture's:

| What was broken | Verdict |
| --- | --- |
| Editor extension removed from `devcontainer.json` | LNT-001 FAIL — *editor locus — no editor configuration installs charliermarsh.ruff* |
| The lint hook removed from `.pre-commit-config.yaml` | LNT-001 FAIL — *pre-commit locus* |
| The Lint step removed from the workflow | LNT-001 FAIL — *ci locus* |
| The Type check step removed | TYP-001 FAIL — *ci locus — no gating step runs uv run mypy* |
| Strictness switched off in the config | TYP-001 FAIL — *mypy strict mode is not set* |
| The Tests step removed | TST-001 FAIL — *no CI step runs the test command* |
| `\|\| true` appended to the Lint step | LNT-001 **and** TST-001 FAIL — both verify through `no-failure-suppression` |
| A root dropped from the coverage allow-list | TYP-001 FAIL — *tool.mypy.files does not cover 1 tracked python file (scripts/plan_progress.py)* |
| Every `gate-quality` stamp removed, artefacts left in place | LNT-001 FAIL — *no tracked file carries a provenance stamp naming 'gate-quality'* |

The last three are the ones worth reading twice. Each leaves every artefact in
place: a suppressed step, a coverage list that quietly excludes, and a
deployment nothing records are all gates that look deployed and are not.

### What the second gate needed from the register

**`invocation` had to name the artefact, not the tool.** `stacks:` recorded
`ruff check` and `mypy` — bare names. The checker only ever *matched* them
against a CI step, and this repository's steps say `uv run …`, so the substring
matched and nothing was wrong. A gate is different: it **writes** that string at
every locus, and a bare name deploys a hook and a CI step that resolve from
`PATH`. That is exactly the fall-through ADR 0020 measured for `npx
--no-install` (§ H6), arriving by a different route — a value that was only ever
read is now also written, and the two uses have different requirements.

Contract 12 sets all four invocations to the form that reaches the pinned
artefact: `uv run …` for the Python stack, `node_modules/.bin/…` for the
TypeScript one, which is the spelling DOC-001 already uses. Two test fixtures
that had encoded the bare form moved with it.

**`deployed_by` on three controls, and one stamp block between them.**
`provenance_stamp_present` matches stamps by *skill*, not by control, so three
copies of the block would evaluate the same files and report the same verdict
three times. LNT-001 carries it — the one control with an artefact at every
locus this gate writes to — and all three carry `deployed_by`. A test holds the
sidecar to the register in that direction: a control the register assigns to a
gate must appear under that gate.

### The one value the register does not settle

The test command. `ecosystems.<name>.test_commands` records the spellings the
standard accepts; which one a repository uses is that repository's own fact, and
neither the register nor the skill can know it. So the gate **asks**, offering
exactly that set, and writes the answer — and says when it asks that the answer
must also reach the artefact the lockfile pins, which `pytest` does not and
`uv run pytest` does.

This is the difference between a value a skill invents and a value a skill
elicits. Inventing `pytest` would have put a rule in a skill; asking, from a set
the register bounds, puts the decision where it belongs and leaves the record in
the workflow for anyone to read.

### `deploys.json` carries one contract per gate

The first slice recorded this as a decision the second gate would force, and it
did. The sidecar is now keyed by gate — `schemaVersion: 2`, with
`contractVersion`, `controls` and `artifacts` under each — because a
plugin-wide number would have made `gate-quality`'s first release recommend
redeploying `gate-secrets`, which changed nothing. Phase 5's criteria are *a
version bump produces no recommendation, a contract bump does*; a contract that
fires for the wrong gate fails the second while appearing to pass it.

`skill-update` still reads one file at one path, so the widening in
[`05-promotion.md`](05-promotion.md) is unaffected — the gate a stamp names is
the key to compare against.

### This repository's own quality artefacts were unstamped

Six stamps, across the three files those artefacts already lived in, all saying
**adopted rather than deployed from nothing** — hand-wired in Phase 0.5, before
there was a gate to write them. `.devcontainer/devcontainer.json` is the seventh
stamped file in this repository and the only artefact any gate writes that is
neither a hook nor a CI step.

One difference from the template is recorded in its own stamp comment rather
than smoothed over: the lint hook carries `--force-exclude`, so it honours the
tool's own exclude list when pre-commit passes filenames. That is a narrowing,
and `variance: narrowing-only` permits it.

### Preflight P1–P11 — `gate-quality`

Run with the same `preflight-check.sh` from `skill-preflight@0.1.15`:

```text
P1 line count           PASS  384 / 500
P2 description length   PASS  226 / 250
P3 name field           PASS  gate-quality
P4 invocation           PASS  side-effect verbs present; disable-model-invocation=true
P5 argument-hint        PASS  no $ARGUMENTS usage
P6 supporting files     PASS  all sibling files referenced from SKILL.md
P7 dependencies.json    PASS  not required
P8 ${CLAUDE_SKILL_DIR}  PASS  every path ref resolves
P9 sub-skill invocation PASS  none
P10 duplicate directory PASS  one location
P11 argument flags      PASS
overall: PASS, 0 failures
```

Two skills of the nine now pass. The criterion says *every* SKILL.md, so it
stays open.

### What is now stale, on purpose

`gate-secrets`' two stamps read `register-contract: 11` against a register at
12. That is staleness, and staleness is reported and never enforced
(`00-concepts.md` § Notify, never redeploy) — `provenance_stamp_present` fails a
stamp *ahead* of the register, never one behind. Nothing about SEC-001 changed
at contract 12, and rewriting those stamps by hand would record a redeployment
that did not happen. Left as it is, deliberately, and it is the first live
instance of the state Phase 5's sweep exists to report.

## Decisions the next slice needs

Recorded here rather than settled silently, in the shape § H used.

| Decision | Why it cannot be deferred past the second gate |
| --- | --- |
| ~~`deploys.json` carries one `contractVersion` for the whole plugin~~ — **settled** by the second gate, see § `deploys.json` carries one contract per gate | Phase 5's criteria are *a version bump produces no recommendation, a contract bump does*. A per-plugin contract makes the second one fire for gates that did not change, and that is discovered as noise rather than as a bug |
| A repo-root `LICENSE`, copied into the plugin | `check_plugin_license.py` fails without it and `pyproject.toml` already declares Apache-2.0. Phase 6 holds the criterion; the plugin directory exists from now on without one |
| Whether `gate-secrets` should own `.devcontainer/setup.sh`'s scanner install | It is a third site repeating the version, listed in `pinned_at`, and no gate currently claims it. Today it is nobody's, which is how a locus gets forgotten |
| Whether an assert that reads a stamp back should know which control it is evaluating. `provenance_stamp_present` matches by skill, so a gate that stamped one of its three artefacts and forgot the others still passes | It decides how many stamp blocks a multi-control gate carries, and every gate after `gate-quality` owns more than one control. Changing the assert's signature is a checker change with a reason ADR 0018 would have to record |
