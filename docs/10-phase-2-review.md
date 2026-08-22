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
shape three controls have to share.

The third settles one of the decisions the second slice recorded as outstanding
— § The pin's existence — because every gate after `gate-quality` inherits the
answer, and a decision inherited by four gates is cheaper to make once than to
unpick four times.

The fourth is `gate-supply-chain`, in § The third gate below, and it is the
first whose controls were **already passing** before it existed.

The fifth is `gate-build`, in § The fourth gate, which closes two more of the
four unread loci that slice found and replaces three near-copies of one assert
with one that reads the control's own `locus:` list.

The sixth is `gate-iac`, in § The fifth gate, which closes the last of those
four — and, in the course of doing so, found two ways a CI step could be
credited as a locus without gating anything.

The seventh is `gate-repo`, in § The sixth gate, and it completes the family.

The eighth is the shipped devcontainer template, in § The template.

The ninth is `standard-adopt`, in § The front door, which is the last piece of
the phase.

**Ten criteria of eleven are closed.** § Where Phase 2 finished holds the audit
that closed them and the one that is still open — the devcontainer template
building, which needs an operator with Docker and stays open until its output is
recorded here.

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
| Every artefact written, and only TST-001's stamp kept | LNT-001 **and** TYP-001 FAIL — *no stamp names LNT-001*; TST-001 still passes, so the failure is about the record and not the file |

The last four are the ones worth reading twice. Each leaves every artefact in
place: a suppressed step, a coverage list that quietly excludes, a deployment
nothing records, and a deployment recorded for one control out of three. All
four are gates that look deployed and are not.

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

**And it was measured rather than assumed.** ADR 0020 was written from npm's
evidence, and `uv run` is a different mechanism, so the claim was probed:
deleting the artefact makes `uv run` reinstall the pin, and makes it *fail* when
it cannot — it never reaches an impostor on `PATH`. That is the criterion
*delete the artefact and watch the locus fail*, demonstrated in a second
ecosystem. One residual is recorded rather than glossed: `uv run` does fall
through to `PATH` when the tool is absent from the project altogether, which is
a different and smaller condition than `npx --no-install`'s, and is the decision
the next slice inherits. The full measurement is in
[ADR 0020](adr/0020-a-locus-reaches-the-pinned-artefact.md) § Applied to the
quality gates.

**`deployed_by` on three controls, and a stamp block on each.** The first
draft of this slice gave the three controls one shared block, on the reasoning
that `provenance_stamp_present` matched stamps by *skill*, so three copies would
evaluate the same files three times. That reasoning was correct and the
conclusion was wrong: matching by skill is what made the copies redundant, and
matching by skill is itself the defect. A stamp naming TST-001 satisfied
LNT-001's read-back, so a gate that wrote every artefact and recorded only the
CI steps passed all three with the editor locus unstamped.

The assert now reads back the stamp of the control it is evaluating, the id
arrives from the runner rather than from `args:`, and each control carries its
own block. The reasoning is recorded in
[ADR 0018](adr/0018-register-checker-boundary.md) § Applied — fifth pass,
because it puts a rule *in* the checker and that direction owes a reason too.

A test holds the sidecar to the register as well: a control the register assigns
to a gate must appear under that gate.

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
13, and `gate-quality`'s read 12. That is staleness, and staleness is reported
and never enforced
(`00-concepts.md` § Notify, never redeploy) — `provenance_stamp_present` fails a
stamp *ahead* of the register, never one behind. Nothing about SEC-001 changed
at contract 12 or 13, and rewriting those stamps by hand would record a
redeployment that did not happen. Left as it is, deliberately, and it is the
first live instance of the state Phase 5's sweep exists to report.

Contract 13 is the more interesting case, because it *did* change what
`gate-quality` writes — the gate now creates the pin as well as the wiring — and
`gate-quality`'s `contractVersion` in `deploys.json` moved from 1 to 2 to say
so. This repository still needs no redeployment: `uv.lock` already pins ruff and
mypy, so the gate re-run would add nothing. A contract bump recommending a
redeployment that would change no file is exactly the noise a per-gate contract
was introduced to bound, and it is bounded here to one gate rather than two.

## The pin's existence — register contract 13

The third slice, and the smallest: one assert, four register fields, one new
step in a gate that already shipped.

### What was open

[ADR 0020](adr/0020-a-locus-reaches-the-pinned-artefact.md) made every locus
invoke the artefact its lockfile owns, and measured four conditions. Three came
out the way the ADR wanted. The fourth, case C, did not:

```text
C  ruff removed from the project entirely
   uv run ruff --version          exit 0   9.9.9-impostor     (PATH answered)
```

Every artefact is in place, the invocation still reads `uv run ruff check`, and
what answers is whatever is on `PATH`. No spelling of `invocation` closes it,
because an invocation cannot assert the existence of the thing it invokes. The
ADR said so and recorded the question here rather than as a footnote: *must a
stack's gate tools be present in a lockfile the repository commits?*

Answered yes. It is a new assert rather than a register edit, and every gate
after `gate-quality` inherits it — which is why it is settled before the four
gates that would otherwise each inherit an open question.

### What the register gained

Four fields, all of them answering *yes* to
[ADR 0018](adr/0018-register-checker-boundary.md)'s test.

| Field | What it settles | Why it is not the checker's |
| --- | --- | --- |
| `stacks.<stack>.ecosystem` | Whose lockfile pins this stack's gate tools | A stack and an ecosystem are different things, and a repository could reasonably run its linter from a package manager other than the one its application uses |
| `ecosystems.<name>.lock_entry` | What a package looks like inside that lockfile | The same argument as `frozen_install` beside it: a lockfile format the checker has not heard of is a pin nothing verifies, and the failure is silent |
| `ecosystems.<name>.add_dev_dependency` | How a gate creates a pin that is missing, keyed by the lockfile present | `uv add --dev` and `poetry add --group dev` are both python. Which is right is a fact about the repository |
| `stacks.<stack>.gates.<role>.package` | The name the tool is pinned under, where it differs | `tsc` is a binary the `typescript` package ships. Searching a correctly-pinned lockfile for `tsc` finds nothing |

### The half that is easy to miss

An assert that fails a control for an unpinned tool makes `gate-quality`
incapable of satisfying a control it deploys — the gate wires a linter and never
adds it as a dependency. That surfaced as a test failure rather than as a
thought, which is the useful direction: `test_after_deploying_every_locus_verifies`
went red the moment the assert was wired, on a fixture repository whose
`uv.lock` pins neither tool.

So the slice is two changes, not one. `add_dev_dependency` is the register's
answer, and `gate-quality`'s Step 2 gained a first half that runs it. A gate
that can report a problem and not fix it is a gate that deploys a control it
cannot satisfy, and the schema now refuses the shape: an ecosystem a stack names
must declare `add_dev_dependency` for every lockfile it lists.

### Watched failing

The assert fails when the pin is gone, on a fully deployed repository —
`test_removing_the_pin_is_caught`:

```text
LNT-001  FAIL
   ✓ file: linter-wired-at-all-loci — ruff wired at every declared locus from one configuration
   ✗ file: stack_tool_pinned_in_lockfile — python: ruff is not pinned in uv.lock,
     so uv run ruff check resolves from PATH
```

The two blocks disagreeing is the point. The wiring is untouched and still
passes; the pin is gone and fails. A repository can satisfy either half without
the other, and only the pair means *the version that runs is the version that
was reviewed*.

Six more cases are held in `tests/test_lockfile_pin.py`: no lockfile at all, a
lockfile git does not track, a stack whose predicate is unsatisfied, a binary
lockfile that cannot confirm a pin and does not pretend to, `package`
overriding `tool`, and the register-moves-alone test that renames the mandated
linter in `controls.yaml` and watches the same repository fail.

### The patterns that nobody had run

`lock_entry` is declared for all six ecosystems and exercised by two, because
this repository has a python stack and a typescript one. The other four would
have shipped as regular expressions nobody had ever run — the shape that let a
`go.mod` repository past SUP-001 for three contracts (§ H3 in
[`09-phase-1.5-review.md`](09-phase-1.5-review.md)).

So each of the six is tested twice: once against a real fragment of its own
lockfile, and once against a package that is not in that fragment. The second
half is what makes the first mean something — a pattern loose enough to match
any text would pass the positive test while verifying nothing.

### What is deliberately not covered

TST-001 gains no pin check. Its test command is not a stack gate role, so there
is no `stacks:` entry to read one from, and inventing a role for it would put a
rule in the checker that the register could not state. The residual is smaller
than case C was — a test command that resolves from `PATH` runs *some* test
runner, where an unpinned linter enforces *some* rule set — but it is a
residual, stated rather than closed.

DOC-001 gains none either, and for a different reason: `node_modules/.bin/` exits
127 when the artefact is absent, so there is nothing to fall through to. Case C
is specific to a resolver that searches.

## The third gate — `gate-supply-chain`, register contract 14

SUP-001, SUP-002 and SUP-003: what a build resolves, how it stays current, and
what it is allowed to fetch.

### It found a locus nothing had ever read

The first two gates deployed things a bare repository plainly lacked. This one
started from three controls that were **green**, in this repository, on the day
it was written — and one of them was green for the wrong reason.

SUP-003 declares `locus: [pre-commit, ci]`. Its one verify block was
`actions-pinned-to-sha`, which walks the workflow files and checks every `uses:`
is a 40-character SHA. That is a claim about the *property*. It is not the claim
the control's `locus:` makes, which is that something enforces the property
before a commit lands and before a merge does. This repository had **no
pre-commit hook for SUP-003 of any kind**, and reported PASS.

Exactly the shape contract 11 fixed in SEC-001, and § H found in GOV-001. Found
again here because a gate has to *write* each locus it claims, which is a
question nobody asks while only auditing.

A survey while fixing it found three more of the same: BLD-001, DEV-001 and
IAC-001 all declare `pre-commit` and verify only their property. They belong to
gates not yet built, and each will wire and verify its own locus as this one
did. Recorded here rather than fixed silently, because four controls is a
pattern and not an oversight.

### The gate is the checker, and that is the point

SUP-003 has no third-party tool that could serve its pre-commit locus. No action
linter shares this register's notion of an owner-exempt action —
`actions-pinned-to-sha` reads the repository's own owner from the remote and
exempts what it published. A second implementation would eventually disagree
with the first, and the disagreement would surface as a commit blocked at one
locus and waved through at another.

So the hook runs `standard-check run --control SUP-003`. One assert, one
implementation, at both loci — the same argument that made a gate verify itself
through `standard-check run --control <ID>` rather than by reading its own files
back. `tools.standard-check` records how a locus reaches it, because a bare name
resolves from `PATH` (ADR 0020) and for this tool what answered would be
auditing the repository.

**Running the checker is not the same as auditing with it.** The first
implementation of `supply_chain_gate_wired_at_all_loci` credited this
repository's pre-commit locus immediately — and the hook it credited was
`standard-check schema`, which validates the register and reads not one control.
A SUP-003 gate that could never have failed SUP-003. `schema`, `meta`, `assert`
and `explain` are now excluded by name, and `test_a_non_auditing_subcommand_is_not_this_locus`
holds it.

The same distinction cuts the other way and has to. A gating step running the
checker with **no** `--control` audits every applicable control, so it reaches
SUP-003 and a second step would be the same check twice. This repository's
workflow is exactly that case: it carries a SUP-003 stamp and no SUP-003 step,
and the skill checks for it before writing one.

### What the register gained

| Field | What it settles | Why it is not the checker's |
| --- | --- | --- |
| `ecosystems.<name>.frozen_install_command` | What a gate *writes* to install from the lockfile, keyed by the lockfile present | `uv sync --frozen` and `poetry install --sync` are both python. The same argument as `add_dev_dependency` at contract 13 |
| `tools.standard-check` | How a locus reaches the checker | An adopter installs it as a dependency and reaches it however their package manager does |
| `SUP-00x.deployed_by` | Which gate owns these artefacts | The same statement contract 12 made for the quality controls |

**The pair that cannot drift.** `frozen_install` is what the checker credits;
`frozen_install_command` is what the gate writes. The schema requires every
command to match one of its own ecosystem's patterns, so a register cannot be
written in which the gate deploys a step the control then refuses. That rule
found its first case immediately: `test_h3_the_frozen_idiom_comes_from_the_register`
mutates `frozen_install` to nonsense, and the register now refuses to load until
the command moves with it — which is the coupling working, stated in the test.

**A lockfile the register recognised and no install it accepted.** `bun.lockb`
was listed among node's lockfiles from contract 8 with no `frozen_install`
pattern that installs from it. A bun repository could satisfy SUP-001 by no
spelling at all. Found by the new schema rule rather than by a bun repository,
which is the cheaper way to find it.

### Watched failing

Fourteen cases in `tests/test_gate_supply_chain_deploy.py`, on a fixture
repository whose one action reference is **already SHA-pinned** — chosen so that
`actions-pinned-to-sha` is green from the first line and every failure below is
about a locus rather than about the property:

```text
SUP-003  FAIL
   ✓ file: actions-pinned-to-sha — every third-party action reference is pinned by SHA
   ✗ file: supply_chain_gate_wired_at_all_loci — pre-commit locus — no hook runs
     'uv run standard-check' for SUP-003
```

And the reverse, on the deployed repository with one reference reverted to a
tag: the property fails and the loci still pass. The two halves are separable,
which is what makes the locus check worth having rather than a restatement.

Also held: the install step replaced, `dependabot.yml` deleted, the hook
deleted, the hook auditing a *different* control, the hook running a
non-auditing subcommand, the stamps stripped, and one control's stamp stripped
while the other two keep theirs.

### What this repository had to change about itself

Four artefacts, all *adopted rather than deployed* — hand-written in Phase 0.5,
stamped now that the gate that owns them exists — and one genuinely new:

| Artefact | Control | State |
| --- | --- | --- |
| `.github/workflows/standard-check.yml` — frozen install | SUP-001 | Adopted, stamped |
| `.github/dependabot.yml` | SUP-002 | Adopted, stamped |
| `.github/workflows/standard-check.yml` — the full audit | SUP-003 | Adopted, stamped; no step added |
| `.pre-commit-config.yaml` — `standard-check-supply-chain` | SUP-003 | **New.** The locus that had never existed |

`.github/dependabot.yml` is the eighth stamped file in this repository and the
only one whose stamp sits at the top rather than at a section: every line of it
belongs to one control, which is exactly the condition that makes a whole-file
stamp right rather than a claim over hooks it does not own.

### Preflight P1–P11 — `gate-supply-chain`

`preflight-check.sh` from `ee-skills`, the same script the marketplace runs.

```text
{"skill": "gate-supply-chain", "overall": "PASS", "fails": 0}
  P1_line_count  363 / 500      P7_dependencies_json   none required
  P2_description_len            P8_skill_dir_paths     all resolve
  P3_name_field                 P9_subskill_invocation none
  P4_invocation  side-effect verbs; disable-model-invocation=true
  P5_arguments_hint             P10_no_duplicate_dir
  P6_supporting_files           P11_argument_flags
```

P2 failed first time at 286 characters against a 250 limit, and the fix is
worth recording rather than smoothing over: the description had been written to
list all three controls and what each does. The limit is a real constraint on
what a description can be — a trigger, not a summary — and the rewritten one
says what the gate is for in three clauses and keeps the trigger phrases.

## The fourth gate — `gate-build`, register contract 15

BLD-001 and DEV-001: a container that does not end as root, and a devcontainer
whose image and features are pinned.

### The same finding, in the two controls beside it

The third slice found SUP-003 declaring `locus: [pre-commit, ci]` with nothing
reading either, and listed three more controls with the same defect. Two of them
are this gate's. Both verified only their *property* — the final `USER`, the
declared container user, the lock file's coverage — read out of the files on
disk, and a repository with no pre-commit hook of any kind reported PASS on
both.

So the fixture in `tests/test_gate_build_deploy.py` is a devcontainer that is
**already correct**: non-root user, digest-pinned image, complete lock file.
Every failure in that file is about a locus or a stamp, which is the whole of
what contract 15 added.

### One assert instead of four

Contract 14 shipped `supply_chain_gate_wired_at_all_loci`, which knew two loci
by name. BLD-001, DEV-001 and IAC-001 would each have grown another copy — and
three copies of one check was already one too many, which is the shape this
repository exists to prevent, reproduced inside the tool meant to prevent it.

`gate_wired_at_declared_loci` reads the **control's own** `locus:` list from the
register and checks each member. SUP-003 migrated to it in the same commit, so
the count went from one-and-growing to one. `remote` is skipped deliberately and
*named* as skipped in the message — verifying platform state is Phase 3's, and a
locus quietly dropped is the silence this assert exists to remove.

The one thing it still knows by name is this checker's own console script,
recorded as `_SELF`. A gate whose tool *is* the auditor has to be judged by which
subcommand it runs, and no other tool does — which is a property of the checker
rather than of any repository (ADR 0018).

### The tool this gate deliberately does not install

BLD-001's container half runs `hadolint`. The obvious move was a
`tools.hadolint` entry, and the schema refused it: `pinned_at` is required to be
non-empty under `source: literal`, because *an empty list is indistinguishable
from a tool nobody pins*. This repository has no Dockerfile, so it installs
hadolint at no locus, and any site listed would be a site
`tool_versions_match_register` then fails as absent.

Working around that would have meant either installing an unused binary here or
weakening a rule that exists for a good reason. Neither is the answer. The
answer is that `standard-check run --control BLD-001` runs the `hadolint` block
through the same path the audit uses, so a repository with a Dockerfile needs no
second wiring — and an absent linter reports `UNCLASSIFIED — cannot verify`
(ADR 0016) rather than passing. What closes it is a `tools.hadolint` entry in
**that repository's** register, naming the loci it installs the linter at, which
is `08-adopting.md` § 3.5 doing exactly the work it was written for.

The skill says so and says what not to do about it: *do not install a tool the
register does not pin*. `test_hadolint_is_not_installed_by_this_gate` holds it.

### `.devcontainer/setup.sh` gets an owner, and its regions get theirs

The second slice recorded this as a decision it could not defer: the scanner
install in `setup.sh` was a third site repeating SEC-001's version, listed in
`pinned_at`, claimed by no gate — *"today it is nobody's, which is how a locus
gets forgotten"*. The `uv` install two lines above it was in the same state and
had not even been noticed.

Settled: `gate-build` owns the **file** and each gate writes and stamps its own
**region** inside it, exactly as four gates write their own hooks into one
`.pre-commit-config.yaml`. `gate-secrets` gained a step for the scanner install,
`gate-supply-chain` one for the package manager, and both bumped their
`contractVersion`. `gate-build` writes no stamp there at all, because neither of
its controls has a locus in that file and a stamp naming a control whose locus
the file is not is a claim rather than a record.

`.devcontainer/setup.sh` is the ninth stamped file in this repository and the
only one whose every stamp belongs to a gate other than the one that owns it.

### Watched failing

Twelve cases, including both halves failing independently:

```text
BLD-001  FAIL
   ✓ file: devcontainer_user_is_non_root — states a non-root user (remoteUser: vscode)
   ✗ file: gate_wired_at_declared_loci — pre-commit locus — nothing runs
     'uv run standard-check' for BLD-001
```

and its mirror, with the user reverted to `root` on a fully deployed repository:
the property fails and `gate_wired_at_declared_loci` still passes.

Also held: the partial lock file (Phase 0.5's re-opened criterion, as a test),
the floating image tag under a complete lock file, one control's stamp stripped
while the other keeps its own — one command enforcing two controls needs two
stamps — and the no-op path where an existing full audit reaches both controls
and the gate correctly adds nothing.

### Preflight P1–P11 — `gate-build`

```text
{"skill": "gate-build", "overall": "PASS", "fails": 0}
```

P6 failed first time — `ci-steps.yaml` shipped in `templates/` and was
referenced by no line of `SKILL.md`, because the ci locus had been described in
prose rather than pointed at its template. A shipped file nothing references is
a file nothing keeps current, which is precisely what P6 is for.

## The fifth gate — `gate-iac`, register contract 16

IAC-001, the last of the four unread loci — and the slice that found what the
other three had been reading.

### The gate that cannot be exercised here

This repository has no `*.tf`, so IAC-001 reports `SKIPPED (predicate)` and
always will. Every test in `tests/test_gate_iac_deploy.py` runs against a
throwaway repository with Terraform in it, because a gate whose tests all ran
against a repository the control skips would be a gate nothing had run.

The same fact shapes the gate itself. This register pins neither `checkov` nor
`tflint`, so the deployed control reports `UNCLASSIFIED — cannot verify` on both
analyser blocks. The skill does **not** close that by installing them: an
unpinned install leaves the version unrecorded, which is the condition
`tool_versions_match_register` exists to fail. `UNCLASSIFIED` is the honest
verdict and it is not a pass — `test_after_deploying_the_wiring_verifies`
asserts the exit code is **not** `0` and calls that correct.

### One hook, two analysers

IAC-001's verify blocks are `checkov --directory . --compact --quiet` and
`tflint --recursive`. The hook runs the *control*, and the control runs both.

Two hooks each invoking one analyser would be two statements of what "analysed"
means — a `--recursive` dropped at one locus and kept at another, discovered by
a finding CI caught and pre-commit did not. The template names neither analyser,
and two tests hold it: one checks the hook's `entry` names the control rather
than the tools, the other that neither `run:` string appears anywhere under
`plugins/`.

### What this slice found in the other four gates

Building the "suppressed step" test for IAC-001 turned up two defects in a check
every gate uses, both of them the same shape as the ones contracts 11 and 14
fixed: a locus read by something that could not tell enforcement from mention.

**A suppressed step counted as a locus.** `continue-on-error: true` means the
job succeeds whatever the gate reports. The tool runs; the merge is not gated on
it. SEC-001 and SUP-003 carry no `no-failure-suppression` block of their own, so
nothing else caught it — *declared and unreachable* one level in from the
`workflow_dispatch` case § D found.

**Installing a tool counted as running it.** This was the worse of the two, and
it was `gate-secrets`' own shipped template that exposed it. The ci-locus check
was a substring search over a step's whole `run:` text, and the install step
mentions `gitleaks` six times — in a URL, in a tarball name, and as an argument
to `tar`, `install` and `rm`. Measured:

```text
workflow with the secret-scan step deleted, install step kept
  SEC-001  ✓ file: secrets_gate_wired_at_all_loci — pre-commit and ci loci
           both reach gitleaks through 'gitleaks'
```

The scanner was installed and never run, and the control was green. Contract 11
added that ci check precisely to stop a deleted scan step passing; it did not
stop this one.

Both are closed by one change: a tool is run by a step when it is the
**command**, not when its name appears in one. `_commands()` splits a `run:`
block on shell separators, strips prefix words (`sudo`, `env`, a `VAR=`
assignment), and the invocation is matched at position 0. `_ci_run_mentions` and
the generic locus assert both go through it.

One existing test moved with the tightening rather than around it:
`test_mandating_a_different_linter_changes_the_verdict` had a fixture running
`uv run flake8 check` against a register naming `flake8 check`. The substring
search accepted it; the command match does not, and it should not — that is ADR
0020's point stated the other way round, so the register mutation now names the
invocation the repository actually makes.

### Watched failing

Twelve cases, including the predicate itself: a repository with no Terraform is
`SKIPPED (predicate)` and exits `0`, which is the state this repository is
permanently in. Then, on the Terraform fixture: both loci failing before
deployment, each artefact deleted in turn, the CI step suppressed, the stamps
stripped, and the no-op path where an existing full audit reaches the control.

### Preflight P1–P11 — `gate-iac`

```text
{"skill": "gate-iac", "overall": "PASS", "fails": 0}
```

Zero failures first time — the first gate for which that is true, and only
because P2's 250-character description limit and P6's referenced-files rule had
already been paid for by `gate-supply-chain` and `gate-build`.

## The sixth gate — `gate-repo`, register contract 17

CI-001, and the last gate. It is the only one whose effect is not a file.

### The gate with nothing to verify

Every other gate writes artefacts a checker can read. CI-001's only locus is
`remote`, so `gate-repo` had no file to write, no stamp to leave and nothing at
all observable until Phase 3 implements `kind: remote`. Its whole verify block
would have reported `SKIPPED (no credentials)` — a gate whose correctness rested
entirely on a phase that has not happened.

That is the shape this review record keeps re-opening criteria over, so the
ruleset is **recorded before it is applied**:
`.github/rulesets/default-branch.json`, derived from CI-001's `args:` at deploy
time, stamped like any other artefact, and read back by
`ruleset_recorded_matches_register`.

**And the record must not be mistaken for the enforcement.** GitHub does not
read a path in a repository to decide what protects its default branch; only the
API call does. A recorded ruleset the platform has never been told about
protects nothing, which is the reads-as-solved half-state DEV-001 exists to
catch, one domain over. So the assert says *intent only* in its own message, and
the `remote` block is unchanged — still `SKIPPED (no credentials)`, still the
verdict that would say the branch is protected. Every deployed run in
`tests/test_gate_repo_deploy.py` exits `3`, never `0`, and the test that asserts
it says why.

### One statement of "protected", read twice

The recorded file and the remote check take the **same** `args:` —
`require_pull_request`, `require_status_checks`, `allow_force_push`. Two blocks
would be two definitions, free to drift, and the drift would be invisible until
Phase 3 made the second one executable. That is the worst moment to discover it,
so `test_the_register_states_the_requirements_once` compares them.

One mapping is stated rather than inferred: `allow_force_push: false` becomes
GitHub's `non_fast_forward` rule. The register says what is *allowed* and GitHub
names what is *blocked*, and reading one as the other is how a control ends up
inverted.

### Three things GitHub accepts and the checker does not

Each is a ruleset that exists and protects less than it appears to:

| Recorded | Why it fails |
| --- | --- |
| `enforcement: evaluate` | Reports what would have happened and blocks nothing — declared and unreachable |
| `include: ["refs/heads/main"]` | Stops protecting the default branch the day the default moves, silently |
| The file untracked | Nobody can review it, and the remote block cannot be reached without credentials either — so *nothing* about the control would have been verified |

### JSONC, and the filter that has to survive it

The record carries a `//` stamp, so it is JSONC, as `.devcontainer/devcontainer.json`
is and for the same reason: a file that cannot carry a comment cannot carry its
own provenance. GitHub's API takes strict JSON, so Step 2 pipes the file through
`grep -v '^[[:space:]]*//'` on the way out.

That is a filter on a payload rather than a second copy of the ruleset — but it
only works while every comment sits on a line of its own.
`test_the_recorded_ruleset_is_valid_json_once_the_comments_are_stripped` runs
the gate's own filter over the gate's own template and parses the result, so a
trailing comment fails here rather than at the API call.

### The confirmation no test can hold

This gate calls an API whose effect is immediate and shared. No test can prove a
model asks first. What can be held is that the skill says to, in terms that name
the blast radius — *it affects every collaborator, not only you* — that it does
not treat `standard-adopt`'s plan approval as covering a call that is not a
file, and that a failed call is never retried with a weaker ruleset. Those four
sentences are asserted in `test_the_skill_confirms_before_it_calls`, which is a
weaker guarantee than the others in this repository and is labelled as one.

### What this repository recorded

Adopted, not deployed. The ruleset was created by hand on 2026-08-17 and
`GET /rulesets/20937135` returns four rules, not three: `pull_request`,
`required_status_checks`, `non_fast_forward` and `deletion`. The record
transcribes all four.

`deletion` is not one of CI-001's requirements, and keeping it is deliberate. An
extra rule adds a restriction; what the control forbids is removing a required
one. A record that disagreed with what is enforced would be worse than one
carrying more than the register asks for — and it is the disagreement, not the
extra rule, that this file exists to make visible.

Stated as a limit rather than left implicit: the assert checks that the required
rules are **present**, not that no others are. CI-001 is `variance: forbidden`,
and a stricter reading would fail this repository for protecting its branch more
than the register asks. If that reading is wanted, it is a register change.

### Preflight P1–P11 — `gate-repo`

```text
{"skill": "gate-repo", "overall": "PASS", "fails": 0}
```

## The template — `plugins/ee-standard/templates/devcontainer/`

The eighth slice, and the first that is not code.

### Where it lives, and why that was a decision

`03-devcontainer.md` named two candidate homes and settled on neither: a public
template repository, or a directory inside the plugin. The plugin won, and the
argument is the one that document already made — `project-init`'s stated
precondition is that `.devcontainer/devcontainer.json` exists, its guidance when
it does not is *"clone the template repo"*, and **that repo is private**. Anyone
whose access lapses loses the ability to start a project.

A directory in the plugin is obtainable by anyone who can install the plugin,
needs no org-admin action, and cannot drift from the register into a second
repository nobody is auditing.

### What it pins, resolved rather than copied

The base image digest was **resolved from the registry while writing this**,
not carried across from this repository's own devcontainer:

```text
GET https://mcr.microsoft.com/v2/devcontainers/base/manifests/trixie
docker-content-digest: sha256:025b74bb5f7ac53edd77e01aa7188c359aab100e23a2f6220bde50bbb9fd31dd
```

It matches what this repository pins, which is the answer the copy would have
given — and the point is that it was checked rather than assumed. The feature
digest did **not**: `ghcr.io/devcontainers/features/github-cli:1` now resolves
to `1.1.1` where this repository's lock file holds `1.1.0`. A tag had moved
since Phase 0.5, and copying the lock file would have shipped a stale pin as a
fresh one.

### The criterion that needed a test rather than a review

> The template pins no tool version by hand. Every tool it installs is either
> sourced from a lockfile the consumer repo already commits, or from a single
> toolchain file — never a literal inside `setup.sh`.

[ADR 0020](adr/0020-a-locus-reaches-the-pinned-artefact.md) singled this one out
in advance as a criterion a template could meet **in letter**: it is about the
*source* of a version, and a template with a resolution hole satisfies it. So it
is a grep, not a reading — `_VERSION_LITERAL` in
`tests/test_devcontainer_template.py` enumerates the shapes a real setup script
uses, and `setup.sh` must contain none of them.

And the grep is itself tested. `test_the_grep_would_catch_a_pin_if_one_appeared`
feeds it five lines lifted from real scripts — `pip install --quiet uv==0.12.5`,
`GITLEAKS_VERSION=8.30.1`, a version in a URL path, a bare `sha256sum -c` digest,
`npm install -g markdownlint-cli2@0.18.1` — and requires each to fail. Two of
those five slipped through the first pattern, which is the whole argument for
writing that test: a pattern loose enough to match nothing passes the positive
test while verifying nothing at all.

A second test covers what the grep cannot. A script can pin nothing and still
install something unpinned — `pip install uv`, `npm install -g` — which is worse,
because the version is then whatever the registry served that day. Every install
in the template is required to be frozen and guarded by a lockfile's presence.

### The two lines that travel with the directory

`fetch-secrets.sh` writes real credentials into `.devcontainer/.env`. The
template ships its own `.gitignore` naming that file and its derived
`.env.docker`, rather than telling an adopter to add them — a `.gitignore` you
have to remember is one added after the first commit, which is one commit too
late.

Asserted twice, and deliberately: once on the file's contents, and once by
`git ls-files` on a real copy with real-looking files in place.
`.gitignore` semantics are subtle enough — a nested path, a leading slash, a
negation — that reading the file is not the same as checking the behaviour.

### What is verified, and what is not

`test_the_copied_template_passes_the_controls_that_judge_it` copies the template
into a throwaway repository and runs BLD-001 and DEV-001 against it. All three
property blocks pass from the first line. The locus and stamp blocks fail, and
the test asserts that too — a fresh copy has not run `gate-build`, which is the
next step the README gives, and hiding that would be claiming a deployment that
had not happened.

**The build is not verified here and cannot be.** This devcontainer has no
Docker, so a test claiming a successful build would claim something nothing ran.
The exit criterion has two halves and only one of them is closed; the other
needs an operator with Docker, and the commands are in `08-adopting.md` § 2.0:

```bash
grep -rl '{{' .devcontainer          # expect no output
devcontainer build --workspace-folder .
standard-check run --control BLD-001 --control DEV-001
```

Recorded as open rather than ticked. A criterion closed on a build nobody ran is
the over-tick this document exists to catch.

## The front door — `standard-adopt`

The ninth slice, and the last. It writes no gate configuration: every artefact is
written by the gate that owns the control, which is what keeps one control's
config in one place. What it owns is the *plan*, the *order*, and the
*verification*.

### The fourth plan row nobody had noticed

The plan has to name every control in the register — one absent from the plan
reads as one that does not apply. Three rows were obvious: **deploy**, **dispatch
elsewhere** (DOC-001 is `lint-md`'s, in another plugin) and **manual**.

Writing the test found a fourth. **SEC-002 fits none of them.** It has no
`deployed_by`, so it would have been planned as *manual* — telling a reader they
owe an act they do not. It is satisfied by a workflow **not** referencing a
static credential: there is nothing to write, and `gate-secrets` verifies it and
writes nothing for it. `02-skill-family.md` had recorded that as correct rather
than as a gap, in a sentence nobody had needed until there was a planner.

So the skill has a **checked, not deployed** row, derived from `deploys.json`
listing a control under a gate while the control names no `deployed_by`. A
control satisfied by an absence has to be distinguishable from one nobody has
got to yet.

### The dispatch order is load-bearing in its first two positions

Not alphabetical, and not the order the gates were built:

1. `gate-build` — owns `.devcontainer/` and creates `setup.sh`, which two later
   gates write their own regions into.
2. `gate-supply-chain` — writes the frozen install every other gate's CI steps
   run after. A lint step written before it lints against nothing.
3. `gate-secrets`, then `gate-quality`, then `gate-iac` — the rest of the
   file-writing gates, in an order that is preference rather than dependency.
4. `gate-repo` last, because its effect is not a file and cannot be reviewed
   before it takes effect.

`test_the_dispatch_order_is_the_one_the_skill_states` reads the order out of
`SKILL.md` rather than restating it, so a reordering there fails the test that
exercises it instead of drifting from it silently.

### What the end-to-end test reaches that no gate's test could

Each gate's own test deploys it alone into a clean repository. Here all six run
in sequence into one repository, and **four of them write into the same
`.pre-commit-config.yaml`**. That is where "grouped by the artefact they write"
is either true or discovered not to be: if any gate replaced the file rather than
appending to it, the later ones would silently drop the earlier ones' hooks.
`test_four_gates_share_one_pre_commit_config_without_overwriting_each_other`
asserts all five hook ids survive.

Two other things only exist at this level:

**The verify step failing.** The criterion's operative clause is *"with the
verify step genuinely able to fail"*. A deployed config is broken — `|| true` on
the lint step — and the run is checked. It fails **two** controls at once,
because both verify through `no-failure-suppression` over the whole workflow.

**A gate breaking another gate's control.** The frozen install
`gate-supply-chain` wrote is removed, and SUP-001 fails while everything else
passes. That is exactly what a per-gate verify cannot see, and it is why Step 5
runs the whole register rather than the controls just deployed.

### What is proved, and what is not

Stated here as plainly as it is in the test's own docstring, because this is the
criterion most easily over-ticked.

**Proved:** the pipeline works. Six gates compose, their artefacts do not
overwrite each other, the order matters in the way the skill says, every deployed
control carries its own stamp at the current contract, and the whole-register
verify catches a break.

**Not proved:** that a model follows the prose. `SKILL.md` is instructions, and
instructions are followed or they are not. No test can establish it, and the
limit is the same one every gate's tests carry.

The criterion is ticked on the first and the second is recorded rather than
glossed — which is the distinction seven re-opened boxes in this project exist to
teach.

### Preflight P1–P11 — `standard-adopt`

```text
{"skill": "standard-adopt", "overall": "PASS", "fails": 0}
```

One test moved to accommodate it. `test_the_templates_stamp_what_they_write`
required every skill to ship templates, which is right for a gate and wrong for
a dispatcher: `standard-adopt` ships none **because** it writes no artefacts. The
test now skips a skill with no templates only after checking it is not a gate —
a gate with no templates would be one whose deployment has no reviewable source.

## Where Phase 2 finished

Ten of eleven criteria. What follows is the audit that closed it, run over the
register rather than over the ledger — because a ledger is a claim and the
register is the thing.

### Every control, and what reads each locus it declares

| Control | Gate | Own stamp | Loci read by |
| --- | --- | --- | --- |
| SEC-001 | `gate-secrets` | yes | `secrets_gate_wired_at_all_loci`; remote deferred |
| SEC-002 | — | no | `no-static-cloud-keys` — see below |
| SUP-001 | `gate-supply-chain` | yes | `ci-installs-frozen`, over gating steps |
| SUP-002 | `gate-supply-chain` | yes | `dependency_update_config_covers_all_ecosystems` — see below |
| SUP-003 | `gate-supply-chain` | yes | `gate_wired_at_declared_loci` |
| BLD-001 | `gate-build` | yes | `gate_wired_at_declared_loci` |
| DEV-001 | `gate-build` | yes | `gate_wired_at_declared_loci` |
| CI-001 | `gate-repo` | yes | `ruleset_recorded_matches_register`; remote deferred |
| LNT-001 | `gate-quality` | yes | `linter-wired-at-all-loci` |
| TYP-001 | `gate-quality` | yes | `typecheck-strict-and-blocking` |
| TST-001 | `gate-quality` | yes | `tests-run-and-block` |
| IAC-001 | `gate-iac` | yes | `gate_wired_at_declared_loci` |
| DOC-001 | `lint-md` | no | `markdown_gate_wired_at_all_loci` |

**Two rows have no locus-wiring assert, and neither is an oversight.** Saying so
here rather than leaving the blank, because a blank in a table like this is
exactly the silence three of this phase's slices were spent removing.

**SEC-002 has nothing to wire.** *CI authenticates without a long-lived cloud
credential* is satisfied by a workflow **not** referencing one.
`no-static-cloud-keys` reads every workflow file, which is the whole of the `ci`
locus for a control whose content is an absence. There is no gate to install, no
artefact to write, and so no stamp — which is why it is `standard-adopt`'s
*checked, not deployed* row rather than a gap.

**SUP-002's `ci` locus is read, and measured.** Its assert reads a config file
rather than a workflow step, so the question is fair: what fails in CI when that
config is wrong? Measured by deleting `.github/dependabot.yml` from a copy of
this repository —

```text
SUP-002  FAIL
   ✗ file: dependency_update_config_covers_all_ecosystems — renovate.json enables
     custom managers only, so it proposes no package-ecosystem updates, and
     there is no .github/dependabot.yml to cover them
```

— and that failure reaches CI through the conformance step, which is the same
route SUP-001's `tool_versions_match_register` takes. The locus is read.

**DOC-001 carries no stamp block of its own**, and that is `lint-md`'s to add.
The deployment here is stale by design (`lint-md@1.0.6` against 1.0.7) and
`CLAUDE.md` records why re-running it is not the fix.

### What the audit found that Phase 3 owns

One thing, recorded rather than fixed: **SUP-002 verifies the configuration and
not the bot**. A `dependabot.yml` is inert until Dependabot is enabled on the
repository, and a `renovate.json` until the app is installed and its onboarding
pull request left open. Both are platform acts, both are already flagged as a
human's in `08-adopting.md` § 1.1 and in `gate-supply-chain`'s own output — and
neither is *verified*, because verifying platform state is Phase 3's.

Whether SUP-002 should therefore declare a `remote` locus is a register change
this phase deliberately did not make: adding one would create a fourth
`kind: remote` block, and Phase 3 is where those are implemented rather than
stubbed.

### The one criterion left open

The devcontainer template **builds**. This container has no Docker, so nothing
here has run `devcontainer build`, and the criterion says so rather than
resting on the copy's controls passing. The commands are in `08-adopting.md`
§ 2.0, and this section is where the output goes when an operator runs them.

A criterion closed on a build nobody ran is the over-tick this document exists
to catch — seven times, so far.

## What the second review found

A second review on 2026-08-21, run over the artefacts rather than over this
document, after Phase 2's own closing audit had already run. It found four
things. One was a Tier-1 control resting on prose and is fixed at register
contract 18. One is a shipped gate that cannot do the thing it exists to do, and
is **open**. Two were documentation that had drifted behind the code and are
fixed.

Recording the count plainly: the closing audit above ran over the register and
missed all four, because three of them are not in the register and the fourth is
in a shipped skill's prose. An audit is scoped by what it reads.

### 1 — SEC-001's only preventive block was a comment (fixed, contract 18)

SEC-001 had four verify blocks and every one of them read state that already
existed. `gitleaks detect` reads what git carries. `secrets_gate_wired_at_all_loci`
reads the workflow and the hook. `provenance_stamp_present` reads a stamp.
`github_push_protection_enabled` reads what reached the remote. All four act
after a credential is a git object.

`fetch-secrets.sh` writes real tokens into `.devcontainer/.env` and
`.devcontainer/.env.docker` on **every container start**, on the host, outside
anything git sees until someone types `git add -A`. The only thing standing
between that and a commit is an ignore rule — and the ignore rule's own comment
read *SEC-001 depends on these lines*, which is a claim about a control rather
than a check performed by one. `grep -rn gitignore src/` returned nothing.

The shipped devcontainer template carried the same comment, one better and one
worse: better because it travels to every adopting repository, worse because it
said out loud what the consequence was — *deleting it does not fail a build; it
fails quietly, later, in someone else's clone*.

**Closed** by `secret_files_are_gitignored`, and the `paths:` are the register's
because which files hold fetched credentials is a fact about a repository
(ADR 0018). Three failures, told apart because the remedies differ:

| State | Why it is not a pass | Remedy |
| --- | --- | --- |
| Not ignored | The next `git add -A` commits it | Add the rule |
| Ignored by a rule git does not track | Works on one machine; the file is unignored in every clone | Commit a rule that travels |
| Already tracked | An ignore rule added now removes nothing from history | Rotate the credential; the history is a separate problem |

The third is why the assert reports tracking as its own case rather than folding
it into "not ignored": a checker that recommended an ignore rule for a file git
already carries would be recommending the wrong thing, confidently.

The second is why it reads `check-ignore -v` for the *source* of the match
rather than taking exit `0` as the answer. `.git/info/exclude` and an
uncommitted `.gitignore` both exit `0`, and both protect exactly one clone.

**Watched failing**, all three, in `tests/test_asserts_file.py`, and end to end
in `tests/test_gate_secrets_deploy.py` — where deleting the deployed rule, moving
it to `.git/info/exclude`, and force-adding a credential file each fail SEC-001.
`tests/test_standard_adopt.py` holds the last of it: after `standard-adopt` runs,
the rule satisfying SEC-001 is the *template's own* `.devcontainer/.gitignore`,
and deleting it fails the control. The template's comment is now true in the
other direction.

An existing test caught its own staleness on the way: `test_removing_the_stamps_is_caught`
stripped stamps from the two files it knew about, and a third now carried one,
so `provenance_stamp_present` correctly passed. The assert was right and the
test had gone stale — which is the direction round that this document exists to
notice.

`.gitignore` is now the eleventh stamped file, and the only one whose stamped
region runs nothing, installs nothing and declares nothing. It only prevents.

### 2 — `gate-repo` would POST a ruleset GitHub rejects (**closed at contract 19**)

The most serious of the four. Recorded here as it was found, and closed the next
day in its own slice — § What contract 19 changed has what the fix did and what
it turned up on the way.

Running the skill's own comment filter over the recorded artefact gives the
literal payload it would send:

```json
[{"type":"pull_request"},{"type":"required_status_checks"},{"type":"non_fast_forward"},{"type":"deletion"}]
```

GitHub's REST schema makes `parameters` **required** on a `required_status_checks`
rule, carrying `required_status_checks` (the list of check contexts) and
`strict_required_status_checks_policy`. So `/gate-repo`'s apply step returns 422
for every adopter — and the skill correctly forbids retrying with anything
weaker, so the gate dead-ends with CI-001 undeployed. The shipped template at
`skills/gate-repo/templates/default-branch.json` has the same shape.

Set the API aside and it is worse rather than better. A `required_status_checks`
rule naming no context requires no check. CI-001's `enforces` reads *at least one
passing status check*, and `_ruleset_problems` tests only that a rule of that
**type** is present — so a ruleset requiring nothing satisfies
`require_status_checks: true`. This is the same shape as the four loci nothing
read (§ It found a locus nothing had ever read): the verdict is decided by the
presence of a thing rather than by what the thing does.

The record is also not the transcription it says it is. Its header states it is
what `GET /repos/Eaiger-Ent/ee-standard/rulesets/20937135` returns, transcribed.
The live ruleset returns:

```json
"required_status_checks":[{"context":"standard-check"},{"context":"lint-md"}]
```

Both contexts are dropped, along with every `pull_request` parameter. The
platform enforces the property; the record of it does not say so. So this
repository is *safe* and its record is *wrong*, which is the more dangerous way
round — nothing fails, and the file a reader would trust is the one that is
incomplete.

The same `args:` feed the Phase 3 `default_branch_ruleset_satisfies`, so the
blind spot is inherited before it is implemented. It also sits next to something
now closable: GOV-001's partial says *whether the CI workflow is a required
status check … is not verified*, and a recorded ruleset carrying its contexts
would answer exactly that, from a file, today.

**What the fix looks like**, recorded before it was made: the required contexts
become CI-001 `args:` — which checks a repository requires is precisely the kind
of fact ADR 0018 puts in the register — both the record and the template render
`parameters`, `_ruleset_problems` fails a status-check rule naming no context,
`.github/rulesets/default-branch.json` is re-transcribed from the API, and the
contract bumps. That is what contract 19 did, plus two things this paragraph did
not anticipate.

### 3 and 4 — documentation behind the code (fixed)

Neither changes a verdict, and both are the kind of drift that makes a reader
trust the wrong file.

`plugins/ee-standard/README.md` — the plugin's own front page — still listed
`gate-supply-chain`, `gate-build` and `gate-iac` as *Phase 2* meaning unbuilt,
and `gate-repo` as *Phase 3*. All six had shipped. The two genuinely unbuilt
rows now name the phase that owns each rather than sharing a number with the
finished ones.

`08-adopting.md` § 3 said *All six gates are built* and then, in the next
sentence, *until Phase 2 ships them, wire the gates by copying this repository's
own artefacts*. § 2.0 carried the same residue. Phase 3's preamble in the build
plan said *Build `gate-repo`*, which happened at contract 17.

Two `§` citations pointed at the wrong document: `.github/workflows/lint.yml`
cited `04-build-plan.md § F` and `renovate.json` cited `§ G`, and both sections
live in `09-phase-1.5-review.md`. `lint.yml`'s comment also still said the tool
is invoked through `npx`, which ADR 0020 changed to `node_modules/.bin` — a
stamped artefact describing its own previous shape.

### What was checked and found sound

Recorded because a review that lists only findings reads as though nothing else
was looked at.

The full suite passes, `ruff` and `mypy` are clean, `standard-check` exits `3`
and `--require-complete` exits `1`. The ten pre-existing stamps parse and name
real controls. `deploys.json`'s per-gate controls agree with every `deployed_by`,
including SEC-002, which is listed under `gate-secrets` and deliberately has no
`deployed_by` — it is verified from the workflows and has no artefact of its own.
The workflow's tolerance of exit `3` is bounded in a comment and held by a Phase
3 criterion. The required status check contexts on the platform — `standard-check`
and `lint-md` — match the job ids in both workflows.

One thing was found and deliberately not treated as a defect: the shipped
template's `fetch-secrets.sh` is macOS-only and hard-fails without a Claude
OAuth token in the Keychain, so `devcontainer up` cannot succeed on Linux or
Windows. The repository's owner ruled this acceptable for now. It is recorded
here rather than fixed, and it is not what blocks the open build criterion —
`devcontainer build` does not run `initializeCommand`.

## What contract 19 changed

The fix for § 2, and the two things it turned up that the fix's own sketch had
not anticipated.

### `pull_request` was broken too, not only `required_status_checks`

The review found one rule missing its `parameters`. GitHub's schema requires
them on **two**: `pull_request` needs `required_approving_review_count`,
`dismiss_stale_reviews_on_push`, `dismissal_restriction`,
`require_code_owner_review`, `require_last_push_approval` and
`required_review_thread_resolution`. So the apply call had two reasons to fail
rather than one, and a fix that addressed only the reported rule would have
moved the 422 without removing it.

`non_fast_forward` and `deletion` take no parameters at all, and the API rejects
a payload supplying them. Both directions are checked, because a record the API
rejects is not a record of anything — which is the property that failed here,
stated once rather than as a list of rules to remember.

### A required check must be one the repository produces

`required_checks:` is the register's, and on its own that is a second copy of
the workflows' job ids sitting in `controls.yaml`, free to drift from the jobs
that produce them — theme T-2, in the file that exists to prevent T-2. That was
not acceptable, and the answer is not to move the list somewhere else: which
checks a repository requires is genuinely a repository's own decision
(ADR 0018), so it belongs in the register.

What makes it safe is that the assert holds it to the workflows. A named context
must be produced by a job in a **gating** workflow, and that job must not carry
`continue-on-error`. Two failures fall out, and both are real:

- A **renamed job** leaves the register naming a context nothing reports.
  GitHub waits forever for a check that never arrives, so the ruleset blocks
  every merge rather than gating one. It fails here instead, while the two can
  still be reconciled.
- A **suppressed job** produces a check that always succeeds. Requiring it
  requires nothing — theme T-3 arriving through the rule that is supposed to
  make the check matter, which is the same shape contract 16 found in CI steps
  and this one finds one level out.

A repository whose required check comes from outside its own workflows — a SaaS
status check, say — would fail this cross-check today. That case has not
appeared, and a register field invented for it before it exists is a field
nobody has tested. Recorded here as the decision it is.

### The record was re-transcribed, and now matches

`.github/rulesets/default-branch.json` was rewritten from
`GET /repos/Eaiger-Ent/ee-standard/rulesets/20937135` and compared field by
field against that response. It matches exactly, including
`require_extra_approval_for_unattributed_changes`, a field GitHub added and the
first transcription never had. `required_approving_review_count` is `0`, which
is what the platform holds: CI-001 requires a pull request and does not require
an approval on one. Transcribed rather than tightened — a record that says more
than the platform does is as wrong as one that says less, and this file's whole
job is to be true.

### GOV-001's partial narrowed rather than dropped

The review said closing this would *likely let GOV-001 drop its partial*. On
doing the work, that was too strong, and the reason is worth keeping.

Two questions were hiding inside *is the workflow a required status check*.
Whether the **repository** says the job is required is now answerable from a
file, and GOV-001 answers it: every blocking control must be reachable from a
step in a job the recorded ruleset requires. A gating, unsuppressed job that no
ruleset waits for can go red while the merge button stays green, and every
earlier version of this control passed that repository.

Whether **GitHub** enforces that ruleset is not answerable from any file, and
nothing here may stand in for it. So the partial stays and says the smaller
thing. Dropping it would have let the first question stand in for the second,
which is the substitution `ruleset_recorded_matches_register` refuses in its own
message and would have been a strange thing for the register to do beside it.

GOV-001 finds the required checks by looking for whichever control carries a
`ruleset_recorded_matches_register` block, not by knowing CI-001 by name — a
register may call that control something else, and a meta-control that knew an
id would be a rule about one repository's register living in the checker.

Watched failing: a register whose required check names a different job fails
GOV-001 with both the control and the required list in the message, and a
register naming no required check at all gets the old verdict with the
limitation stated in it rather than implied.

### What this cost, and what it did not

Nine new tests in `tests/test_gate_repo_deploy.py` and three in
`tests/test_meta.py`, each watching one failure mode. The assert moved from
`asserts_file` to `asserts_command`, which is where the workflow parsing lives
and where the other asserts that read workflows already were — `asserts_command`
imports `asserts_file`, so reading workflows from the latter would have been a
cycle. The split between those two modules is by *what an assert reads*, not by
`kind:`, and this move makes that more true rather than less.

`standard-adopt`'s fixture gained `_ADOPTER_CHECKS`, one statement of what the
adopter's job is called, read by both the deployment and the audit. That is
`08-adopting.md` § 3.7 — *your register records your own files* — in miniature,
and it is the first place in this repository where the adopter's register had to
differ from ours in something other than `tools:`.

## Decisions the next slice needs

Recorded here rather than settled silently, in the shape § H used.

| Decision | Why it cannot be deferred past the second gate |
| --- | --- |
| ~~`deploys.json` carries one `contractVersion` for the whole plugin~~ — **settled** by the second gate, see § `deploys.json` carries one contract per gate | Phase 5's criteria are *a version bump produces no recommendation, a contract bump does*. A per-plugin contract makes the second one fire for gates that did not change, and that is discovered as noise rather than as a bug |
| A repo-root `LICENSE`, copied into the plugin | `check_plugin_license.py` fails without it and `pyproject.toml` already declares Apache-2.0. Phase 6 holds the criterion; the plugin directory exists from now on without one |
| ~~**`gate-repo`'s ruleset payload omits `parameters`**~~ — **settled** at register contract 19, see § What contract 19 changed | Every adopter who runs `/gate-repo` hit it, and CI-001 is the control the whole Phase 3 remote story is built on |
| Whether a required status check produced **outside** the repository's own workflows needs a register field. The cross-check that keeps `required_checks` from drifting from the job ids would fail such a check today | Not urgent: no adopter has one yet, and a field invented before the case exists is a field nobody has tested. It becomes urgent the first time a repository requires a SaaS check |
| Whether SUP-002 should declare a `remote` locus. It verifies the *configuration*; whether the bot is **enabled** is platform state nothing checks — see § What the audit found that Phase 3 owns | Adding one creates a fourth `kind: remote` block, and Phase 3 is where those are implemented rather than stubbed. Deciding it earlier would mean stubbing exactly the part that must not be stubbed |
| ~~Whether `gate-secrets` should own `.devcontainer/setup.sh`'s scanner install~~ — **settled** at register contract 15: `gate-build` owns the file, each gate stamps its own region, see § `.devcontainer/setup.sh` gets an owner | It is a third site repeating the version, listed in `pinned_at`, and no gate currently claims it. Today it is nobody's, which is how a locus gets forgotten |
| ~~Whether a stack's gate tools must be **present** in a lockfile the repository commits~~ — **settled yes** at register contract 13, see § The pin's existence | It is about the pin's *existence* rather than the invocation, so it is a new assert rather than a register edit, and every gate after this one inherits whichever answer is given |
