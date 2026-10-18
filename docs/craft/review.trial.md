# Craft — the trial

Stage **S6** of [`plan.md`](plan.md). Install on a new repository at its start,
run for a stated period, and revise against what the team reports rather than
against what the plan predicted.

**Status: installed 2026-09-20; reviewed 2026-10-17, thirteen days after the
fortnight ended** — § The review, 2026-10-17, with the owner's account of
2026-10-18. The profile revision it decided is still owed. This
document begins with the agreement, which was recorded before anything was
installed, because `plan.md` § S6 asks for the period to be agreed *before*
installing and an agreement recorded afterwards is a description of what
happened rather than a commitment anyone was held to. The install record follows
it and nothing above it has been edited since.

## What was agreed

| | |
| --- | --- |
| The repository | `anonymise-transcripts` — private, owned by this workstream's author, outside the `Eaiger-Ent` organisation |
| Its state at agreement | **One commit, zero files.** `Initial commit`, empty |
| The stack | Not yet declared. The first real commit decides it |
| The sequence | The owner's skeleton first, then the control register, then Craft |
| The period | **Two weeks from the Craft install**, not from this agreement |
| What is reviewed | S3's criteria as they hold in use, and what the person working in it reports |

**The repository is named and its owner is not.** This repository is public and
that one is private; the name is what makes the record checkable by anyone who
has access, and the handle would add nothing but reach.

## The sequence, and why this order

**The skeleton is the owner's.** A project's shape is not Craft's to invent, and
a profile that met a repository this workstream had built for it would be
measuring its own assumptions — which is the objection S3's rewrite already made
once.

**The control register comes before Craft.** A Craft profile writes rule
selection into the configuration LNT-001's gate wires at editor, pre-commit and
CI. Installed with no gate, the selection is a file that is read when somebody
runs the linter by hand, which is not the thing the two weeks are supposed to
measure. So the register is deployed first and the profile is felt the way the
design assumes it is felt: at a commit that does not complete.

**Two weeks starts at the Craft install.** Long enough for the profile to be met
in ordinary work several times over; short enough that what somebody felt is
still remembered rather than reconstructed when they are asked.

## What has already been observed, before installing anything

Two things, and both are evidence rather than preamble.

**`craft-install` would refuse this repository, correctly.** Neither predicate
holds on an empty repository — no `pyproject.toml`, no `package.json` declaring
react — so no profile applies, and the skill's rule is to name the condition that
was false rather than to report that nothing happened. The first thing the
installer meets in the wild is the case where it does nothing, which is a case
`docs/craft/build.installer.md` § How the stack is inferred wrote a table row for
and had never run.

**The trial crosses an access boundary this workstream has not crossed before.**
Every install so far has been into a scaffold in this container. This one is a
repository the standard's own tooling cannot reach: the ambient token is scoped
to `Eaiger-Ent`, so it can neither read nor push there. Three consequences,
recorded now because each will shape what the trial can say:

- **Every push is the owner's.** Work is prepared in a local clone and pushed by
  somebody with access, so nothing here is a claim about what CI did unless the
  owner reports it.
- **CI-001 is platform state.** `gate-repo` applies a default-branch ruleset
  through the GitHub API, and that call has to be made by an account with admin
  on the repository. It is the one part of the adoption this container cannot
  perform at all.
- **What the trial reports is second-hand.** That is the ordinary condition of a
  trial with a team in it, and it is worth naming before the report arrives
  rather than when it disagrees with a measurement taken here.

## What the owner needs to do first

The repository needs a stack before Craft has anything to install. Minimally, a
first real commit carrying:

- **`pyproject.toml`** with `[project]`, a `name`, a `version` and a
  `requires-python`. That file existing *is* the `python` predicate — the control
  register's, reused rather than re-spelled.
- **A source directory and a test directory**, however small. TYP-001's coverage
  key and the profile's source scope both read the layout, and a repository with
  nothing in `src/` is one where the scope cannot be seen to work.
- **A lockfile**, once there are dependencies. LNT-001 and TYP-001 require their
  tools to be reached through it, so `uv lock` is what makes the gates
  installable rather than aspirational.

**And one thing to leave out.** Do not add a `ruff.toml` or a `.ruff.toml`
beside the `pyproject.toml`, and do not write a `[tool.ruff.lint] select` by
hand. Both make the installer stop: ruff reads the *nearest* configuration file
where the register lists the checker's search order, so a sibling `ruff.toml`
silently replaces the section a profile writes. That refusal exists because the
first trial run, on a scaffold, installed a profile that applied to `src/` and
not to `tests/` and reported success —
[`build.installer.md`](build.installer.md) § The first run of the installer.

**This is also the trial's first prediction.** If the skeleton arrives with one
of those files in it, the installer should refuse and say why. Whether it does is
a result, and it is written down here before the skeleton exists so that it
cannot be rewritten afterwards.

## The install, 2026-09-20

Installed through `craft-install` rather than by hand, which is the only way the
skill gets tested by this stage. The clock the agreement set starts here: the
review is due **2026-10-04**.

| | |
| --- | --- |
| Stack inferred | `python`, from `pyproject.toml` at the root |
| Stack refused | `react` — `package.json` declares no react (it exists for `markdownlint-cli2` alone) and there is no `tsconfig.json`. Both conditions were false, and both were named |
| Profile | `python/strict@1` |
| Where the choice came from | An answer given at the install. `.claude/skill-config.yaml` did not exist, so nothing was pinned and nothing was inferred |
| Config files later in the search order | None. No `ruff.toml` and no `.ruff.toml` beside the `pyproject.toml`, so the audited configuration and the running configuration are the same file |

### The repository at the moment of install

Seven commits, the last of them the same day. Fourteen tracked Python files,
1,219 lines: 555 under `src/`, 600 under `tests/`, and the rest repository
tooling. Small enough that every finding below is on code somebody wrote this
month, which is the condition ADR 0052 says the profile is for.

### What was written

| File | What | Rules |
| --- | --- | --- |
| `pyproject.toml` | Marked spans in `[tool.ruff]`, `[tool.ruff.lint]`, `[tool.ruff.lint.flake8-type-checking]`, `[tool.ruff.lint.mccabe]`, `[tool.ruff.lint.pylint]` and the existing `[tool.mypy]` | 168 selected, plus the four below |
| `src/ruff.toml` | New. `extend = "../pyproject.toml"` and the source-scoped selections | `S101`, `D100`–`D107` |
| `craft/unenforced.md` | The residue for `python/strict`, copied whole | 51 properties with no instrument here |
| `CLAUDE.md` | New, with a marked span pointing at the residue | — |
| `.claude/skill-config.yaml` | New. `python/strict: 1`, `residue: craft/unenforced.md` | — |

No dependencies were added: ruff ships every rule the profile selects, and the
control register already requires ruff. Every span in `pyproject.toml` is
byte-identical to the rendered artefact, checked rather than asserted.

### The cost, read from the version that will run it

`plan.md` § S5 and the skill both say to read fix availability from the
repository's own tool where that is possible. It was, and the figures moved:

| | Manifest, at ruff 0.16.5 | This repository, at ruff 0.16.8 |
| --- | --- | --- |
| `python/standard` | 141 rules, 69 declare a fix, 72 hand-work | 145 rules, 73 declare a fix, 72 hand-work |
| `python/strict` | 168 rules, 77 declare a fix, 91 hand-work | 172 rules, 81 declare a fix, 91 hand-work |

Four rules in each level, all of them fix-declaring, arrived under selectors the
profile already names — three patch releases were enough. The hand-work column
is unchanged, which is the column a team feels. **The manifest's numbers are
version-stamped for exactly this reason, and on the first real install they were
already stale.** The instruction to read fresh is what saved the presentation
from being wrong, not the manifest.

### Verification, by running the tools

`uv run ruff check .` resolves the configuration and reports **38 findings** on
1,219 lines. Findings are the install working; a configuration error would have
been the install failing.

| Where | Findings |
| --- | --- |
| `src/` | 24 |
| `tests/` | 6, all `INP001` |
| `.claude/hooks/` | 8 |

The largest families are `INP001` (6), `D102` (5) and `EM102` (5); two are
fixable with `--fix` and fifteen more only with `--unsafe-fixes`, which is the
gap between *declares a fix* and *is cheap* showing up on the first run.

**The nested scope works, and this is the first evidence from outside a
scaffold.** Every one of the twelve docstring findings is in `src/` and none is
in `tests/`; `S101` fired nowhere, because `src/` has no bare asserts and the
tests where asserts belong are outside its scope. That is the defect S5 found on
its own scaffold —
[`build.installer.md`](build.installer.md) § The first run of the installer —
behaving correctly on a repository it did not build.

`uv run register-check` reports two failures, **CI-001 and TYP-001, and Craft
caused neither.** That was established rather than assumed: the Craft changes
were stashed, the two controls re-run, and both failed identically without them.

- **CI-001** has no recorded ruleset and no `gate-repo` stamp, because the
  agreement already recorded that this container cannot make that API call. The
  remote block adds something the agreement did not anticipate: GitHub answers
  `403 — Upgrade to GitHub Pro or make this repository public`. For a private
  repository on this plan the control cannot pass at all, which ADR 0047 says is
  recorded in `deployment-decisions.yaml` and never fixed with a bigger token.
- **TYP-001** fails on `.claude/hooks/yaml-lint.py`, a tracked Python file
  outside `[tool.mypy] files`. It is the owner's to close, and it is the same
  file the section below is about.

## What the install found

Four things, none of them derivable from reading the skill.

**A span written inside an existing table needs a stated position.** The skill
says to write the span *inside* the table and says nothing about where. Writing
it at the end of the table is the obvious reading and it is wrong: the comment
block explaining `[tool.mypy]` sits above that header and therefore inside
`[tool.ruff]`, so the span landed underneath somebody else's explanation of a
different section. The file still parsed, which is the problem — nothing would
have caught it. Immediately after the header line is the position that is always
right, and the skill should say so.

**The gate's own comment now describes a file it no longer matches.**
`gate-quality` wrote `An empty section is a real configuration: ruff's defaults,
stated in a place a reviewer can find and a later commit can tighten` above
`[tool.ruff]`. That commit has now happened, by a different skill, and the
comment above the section says the section is empty. Neither skill owns the
other's prose and neither is wrong; the artefact is. It is the first case of two
stamped writers sharing one table, and it will recur at every Craft install into
a register-conformant repository.

**The residue has nowhere to be pointed from in a repository with no assistant
context file.** Step 5 says to add a marked span to *the* assistant context
file. This repository had none. A `CLAUDE.md` was created carrying the span and
nothing else, which is a defensible answer and is not the skill's answer,
because the skill does not have one. Naming the file to create, or saying to
report instead of creating, is a one-line fix to a step that currently depends
on the installer's judgment.

**The profile lints repository tooling as though it were product code.** Eight
of the thirty-eight findings are in `.claude/hooks/yaml-lint.py`: a pre-commit
hook that shells out to `os.path`, annotated loosely, written to be read once.
Nothing is wrong with the findings. The question the trial raises is whether a
profile whose source-scoped half is careful about `src/` versus `tests/` should
be silent about a third category — scripts the repository runs on itself — and
the answer is not this document's to give before the fortnight is up.

## The prediction did not fire

The document predicted that a skeleton arriving with a hand-written
`[tool.ruff.lint] select` or a sibling `ruff.toml` would make the installer
refuse. The skeleton arrived with neither, so the refusal was never reached.
That is **untested, not confirmed**, and the prediction stands for the next
install rather than being quietly counted as a pass.

## The review, 2026-10-17

**Thirteen days late, and that cuts both ways.** Four weeks of use is more
evidence than two, and none of it is lost: the history is the record. What is
lost is the condition the agreement set the fortnight for — that what somebody
felt is *still remembered rather than reconstructed*. Everything below was read
from the repository. The owner's own account came a day later and is § The
owner's account, 2026-10-18; no finding above it was edited to fit it.

### How it was assessed

A clone at `084cb1e` (PR #159), under this repository's ignored `temp/`, so
nothing was pushed anywhere and nothing in that repository was changed.

| What was run | Against |
| --- | --- |
| `uv run register-check`, the adopter's own pin (`v0.8.4`) over its own fetched register (contract 35) | `HEAD` |
| `register-check deployments --plugin plugins/control-register` | `HEAD` |
| `ruff check` and `mypy`, at `HEAD`'s tool versions and with each commit's own configuration | Every one of the 150 first-parent commits on `main` |
| `pytest`, `vitest`, `eslint`, `tsc`, `lint-imports`, `python -m tests.check`, `ruff format --check` | `HEAD` |
| Suppressions counted (`noqa`, `type: ignore`, `test-check: allow`) | Five dates, a week apart |
| The owner's own documents: `docs/test-review.md`, ADR 005, `CONTRIBUTING.md`, `CLAUDE.md` | `HEAD` |

**Three things could not be seen from here.** CI's run history, because the
ambient token cannot read the repository (404, as the
agreement predicted). Whether hooks were installed on the owner's machine,
because `.git/hooks/` does not travel with a clone. And SEC-001's push
protection setting, for the same token reason. All three were answered on
2026-10-18 — the hooks by the owner's account, CI and the platform by a
read-only script the owner ran with their own credentials — in § What CI
recorded.

### The repository it became

| | At install, 2026-09-20 | At review, 2026-10-17 |
| --- | --- | --- |
| Commits | 7 | 334 — 181 non-merge, 159 pull requests |
| Python | 1,290 lines | 51,191 lines, 190 files under mypy |
| TypeScript and React | none | 9,018 lines under `frontend/`, from 2026-10-10 |
| Tests | — | 2,051 pytest passing (18 skipped), 102 vitest |
| Co-authored by Claude | — | 176 of 181 non-merge commits |

**The team is one person and an assistant**, and every result below should be
read that way. The profile was felt by an agent told in `CLAUDE.md` to run
`/simplify` and `/code-review` before every commit and to merge on green
without asking — not by several people meeting a commit that will not complete.

### What held

**The profile was never loosened.** Every marked span in `pyproject.toml` and
`src/ruff.toml` is as `craft-install` wrote it. The configuration changed after
install in exactly one direction: `tests/ruff.toml` (2026-10-17) adds PT008,
PT017 and three banned APIs, outside the managed spans and labelled as not
Craft's.

**`main` was never red on lint or types.** All 150 first-parent commits pass
`ruff check` with no findings and `mypy` with no errors. The replay uses
`HEAD`'s tool versions, so it is an approximation of what each commit's CI saw
and not a record of it. CI's own record, read a day later, agrees: 148 runs on
`main`, every one green (§ What CI recorded).

**Suppressions grew with the code, not faster than it, and each says why.**

| Date | Python lines | `noqa` | `type: ignore` | `test-check: allow` |
| --- | --- | --- | --- | --- |
| 2026-09-20 | 1,290 | 0 | 0 | — |
| 2026-09-27 | 15,216 | 7 | 0 | — |
| 2026-10-04 | 23,225 | 11 | 0 | — |
| 2026-10-11 | 35,322 | 14 | 4 | — |
| 2026-10-17 | 51,191 | 28 | 4 | 16 |

About one per two thousand lines. Every `noqa` in `src/` carries a reason after
the code; the five in `tests/` do not. `RUF100` keeps them honest, and none is
blanket.

**The residue was read, and used.** `docs/test-review.md` reviewed all 86 test
files against a rubric whose standards it names as `craft/unenforced.md`. That
is the residue doing what ADR 0053 says it is for, by the reader it was written
for.

### Rules fought

The 28 suppressions, by what they argue with:

| Rule | Times | What it was fighting |
| --- | --- | --- |
| `PLR0913` | 8 | Pipeline stages and driver entry points that take every place a run writes. Half the friction is the size family |
| `C901` | 4 | Dispatchers over `match`, each suppression saying *a case a command* or *a case a notice*. McCabe counts each case as a branch, so a flat dispatcher reads as complex code |
| `PLR0915` | 2 | The same two dispatchers |
| `ARG002` | 5 | Test doubles implementing a protocol method whose argument they ignore |
| `PLC0415` | 3 | An optional extra (`[web]`, imported only when asked for) and one import cycle. The rule cannot see either reason |
| `TC001`, `TC003` | 3 | pydantic, which reads annotations at runtime |
| `BLE001` | 2 | The boundary where a failure is shown on the page rather than raised |
| `S105` | 1 | A false positive: an OAuth endpoint URL in a constant named `TOKEN` |
| `PTH207` | 1 | Genuine: `Path.glob` cannot take a pattern with its own folders |
| `TID251` | 1 | The one sanctioned sleep, in `tests/waiting.py` |

**One is the profile's to fix.** `python/strict` sets
`runtime-evaluated-decorators` for `dataclasses.dataclass` and says nothing about
pydantic, so a repository using pydantic meets the typing-only-import rules on
every model module. `runtime-evaluated-base-classes = ["pydantic.BaseModel"]`
clears one of the three here, measured; the other two are a type used in a
model defined elsewhere, which the setting cannot reach. The same omission
appears on the mypy side: `disallow_any_explicit` refuses every pydantic model
unless `pydantic.mypy` is loaded, and the owner had to work that out and add
the plugin.

### S3's criteria, as they held in use

| S3 criterion | In use |
| --- | --- |
| The configuration assembles and runs | **Held.** 150 commits, no configuration error at any of them |
| No two selected rules contradict | **Held.** No suppression is one selected rule giving way to another |
| A false positive is the whole of the friction | **Held, with one class.** `S105` once; the pydantic `TC00x` cases are a false positive the profile can configure away and does not |
| Cost per finding, not count | **The size rules are the cost.** `PLR0913`, `C901` and `PLR0915` are 14 of 28 suppressions. The `C901`-on-dispatchers case is the strongest argument in the set, and it is about McCabe rather than about the threshold |

### What the owner built that the profile did not

ADR 005 (2026-10-17) records a review that found *the same few mistakes again
and again, none of which any gate here caught*: assertions that could never
fail, refusals checked only by an exit, a test reaching Google, loops that could
hang, doubles standing in for the code under test. *Most of the suite is now
written with Claude, quickly, and a mistake a reviewer has to spot by eye will
come back.* The owner's answer, against the residue's own words:

| The owner added | Residue property | What the residue says |
| --- | --- | --- |
| `pytest-randomly` in every run | `python.test-independence` | *A check could hold this, and none is written* — *a randomised-order run detects violations empirically; nothing prevents them* |
| `pytest-timeout`, `pytest-socket` | `python.no-flaky-tests` | The same bucket — *repeated runs detect it; nothing prevents it* |
| `patched-under-test`, and `unittest.mock` banned in `tests/` | `python.no-mocking-domain-logic` | **Judgment only.** The owner found a heuristic instrument for a property the profile classes as having none |
| `constant-assert`, `no-assertion`, `bare-refusal`, `loop-assert` | `python.test-code-quality` | Satisfied *by configuration* — the lint profile applies to `tests/`. It did, and these defects passed it |
| `PT008`, `PT017` | — | Ruff rules the profile could have selected and did not |

**This is the largest finding about the profile.** It is strict about
production code and lets a fast, assistant-written suite carry tautologies that
pass every gate. Two of the residue's classifications are contradicted by an
instrument now running in a repository. The candidates for a profile revision
are in § What this document owes; none is decided here.

### React arrived, and Craft did not notice

`tsconfig.json` and a `package.json` declaring `react` both landed on
2026-10-10, in `c597c09`. From that commit `craft-install`'s React row holds on
both its conditions, and 9,018 lines of TypeScript have been written since with
no React profile. Nothing reported that: `.claude/skill-config.yaml` pins
`python/strict` alone, and Craft has no equivalent of
`register-check deployments` to say that a stack has arrived which no installed
profile covers. The owner hand-wrote an `eslint.config.mjs` instead.

### The two questions the install left open

**A repository with no assistant context file** — answered in use. The
`CLAUDE.md` that `craft-install` created to hold one span became the
repository's whole assistant file: its decisions, its commit routine, its ADR
pointers. Creating one was the right default, and the skill should say so
rather than leave it to the installer's judgment.

**Repository tooling** — answered by the owner, in two ways that both avoided
the question. Vendored code (`.claude/hooks/yaml-lint.py`, compared against the
`lint-yaml` skill's copy line by line) was excluded from ruff. The owner's own
tooling — `tests/check.py`, `tests/hook.py` — was put under `tests/` *so mypy's
`files` and ruff's test rules already cover it*. No third category was needed
for first-party tooling. Vendored code is a different question, and it is the
register's rather than Craft's: the next section's TYP-001.

### The control register, in the same four weeks

The trial put the register first so that the profile would be felt at a gate.
It was. The register's own verdict is a different matter.

```text
Summary: 8 passed, 3 failed, 1 skipped (predicate), 3 unclassified
```

| Control | Verdict | What it is |
| --- | --- | --- |
| LNT-001 | FAIL | **The checker's defect, not the adopter's.** The TypeScript half reports *no eslint configuration* over a tracked `eslint.config.mjs`. `_load_config` reads any extension it does not know as YAML; JavaScript does not parse, so the file counts as absent. It depends on content: reproduced here, `export default [];` passes and a config with an object literal fails. No test in this repository runs LNT-001 against an ESLint config at all |
| TYP-001 | FAIL | `.claude/hooks/yaml-lint.py` is outside `[tool.mypy] files`. **Recorded at install on 2026-09-20 and still failing 27 days later.** Adding it is not a fix: strict mypy finds two errors in it, and it is vendored, so editing it breaks the comparison against its upstream. TYP-001 carries `baseline: null` and has no way to say *vendored* |
| CI-001 | FAIL | Never deployed. The agreement said this container could not make the ruleset call; that is true of the apply and not of the record, which `gate-repo` writes locally. Nor was ADR 0047's `platform_limits:` entry written, so the run cannot even say *unavailable (plan)* |
| SEC-001, SEC-003, GOV-001 | UNCLASSIFIED | The token cannot see the repository. Read with the owner's credentials, `security_and_analysis` is absent rather than `disabled` — the plan does not offer push protection here, which ADR 0047 reads as unreadable and records under `platform_limits:` |

**The finding that matters most is why two FAILs could stand for weeks.** The
adopter's CI runs the tools and runs `register-check` for named controls — the
shape every gate skill writes. Nothing at any locus computes the register's
verdict on LNT-001, TYP-001 or TST-001: their file asserts are read only in a
full run, a full run exits `3` locally by design, and in CI it would fail on
CI-001 regardless. So the build was green at every commit while the register
said FAIL, and nobody was told. The gates are enforced; **conformance to the
register is not, anywhere**, in a repository adopted exactly as the skills
describe.

Three smaller things, each confirmed:

- **LNT-001's title promises formatting.** *Lint and format violations block the
  merge* — and nothing in the register, the gate or the checker runs
  `ruff format --check`. The adopter wrote it into `CONTRIBUTING.md` in its own
  words: *`uv run ruff format` too, though no hook or CI checks formatting*.
  `HEAD` happens to be formatted.
- **The TypeScript half was deployed by hand**, and `deployments` reports
  `gate-quality` as CURRENT. The stamp is truthful about what the gate wrote. It
  says nothing about a stack that arrived afterwards and was wired around it.
- **A skill fix did not reach the deployment.** `gate-quality` stopped writing
  *an empty section is a real configuration* on 2026-09-25 without moving its
  contract, correctly by its own rule. The adopter still carries the sentence
  above a `[tool.ruff]` that is no longer empty, and no report will ever say so.

**And one thing that went well, and is easy to miss.** The owner extended the
register's conventions to tools no control names — yamllint, import-linter, the
test checker — and each hook and step says so in the same words: *no register
control names it, so no stamp*. Every one runs the lockfile's binary, as
ADR 0020 asks. The conventions were learned, not just installed.

### Verdict

**Craft's Python profile worked, for production code.** It assembled, was never
loosened, and cost about one suppression per two thousand lines, half of them
the function-size rules. It **did not work for tests**,
which the owner had to fix with a checker of their own, or for the stack that
arrived three weeks in. The register's gates held at every commit. Its
**verdict** was never read anywhere that could fail a build, which is how a
checker defect and a known gap stood unseen for weeks.

### The owner's account, 2026-10-18

Given after reading the above, and recorded as given:

> There were no issues, the checks could be seen working, the only area which
> you've caught was that the test coverage and test standards needed more
> strict rules — adding these to the ee-standard seems sensible.

**It agrees with the record, and it narrows it.** *The checks could be seen
working* is the thing the history cannot show — that the hooks were installed
and fired on the owner's machine, which `.git/hooks/` does not carry. *No
issues* means the friction § Rules fought counted was not felt as friction: the
size rules, the dispatchers and the pydantic cases were each met, suppressed
with a reason, and moved past. What was felt is the gap § What the owner built
that the profile did not describes, and the owner names **coverage** as part of
it, which that section did not: the suite's 94% branch coverage was measured in
the owner's review and enforced nowhere.

**So the profile revision is decided, and it is the tests.** The other
candidates were not felt, and they are carried rather than taken (§ What this
document owes).

### What CI recorded, read 2026-10-18

`temp/s6-evidence.sh`, GET requests only, run by the owner where their own `gh`
could see the repository. The output was read here and is not committed: it is
a fact about a private repository, and this one is public.

| Question | Answer |
| --- | --- |
| Runs on `main` | **148, all green.** No commit on `main` ever failed CI, which matches the replay |
| Runs on pull-request branches | 350 green, 12 red |
| What the red ones were | 10 are Dependabot proposals the gates refused — a test failing on a React bump, a frozen install failing on TypeScript 7, generated pages going stale on three bumps. **That is the gates working**: none of those bumps merged as proposed. The other 2 are PR #40's |
| Pull requests merged red | **1 of 150.** PR #40, `fix/adjacent-name-parts`, merged 2026-09-28 with its check failed. Both failed runs name no failing step and kept no log: **the account needed credit adding**, so the job was never started. No gate ran and none failed. The merge commit's own run on `main`, once credit was added, was green |
| Rulesets, branch protection | **403** — *Upgrade to GitHub Pro or make this repository public.* Nothing on the platform can require a check. ADR 0047's case exactly |
| Push protection | `security_and_analysis` is `null`: the plan does not offer it on a private repository |

**One red merge in 150 is the cost of CI-001 being unavailable, measured** —
and the red was not a gate. A private repository on this plan spends Actions
minutes, and when they ran out CI did not run at all. A required check would
have held the merge until it could; without one, a check that never started
looked like any other red, and the merge went ahead. Every other merge was green
because somebody, or an assistant told to, looked before merging. PR #40
predates the `CLAUDE.md` instruction to merge only on green (2026-10-10), and no
merge since then has been red.

**This is a failure mode the register does not name.** ADR 0047 records what a
plan *lacks*. A plan that meters CI can also stop the gates running in the
middle of ordinary work, and the only defence is the required check the same
plan withholds.

## The revision, 2026-10-18

**`python/strict@2` and `python/standard@2`**, published from the register by
`scripts/craft_publish.py`. What the owner's account decided, against what the
register can install today:

| Decided | Taken | How |
| --- | --- | --- |
| Tests that cannot fail are refused | **Yes, at strict** | `python.tests-can-fail` binds `PT017`, `B015` and `PLW0129` |
| `PT008` | **No** | It governs how a double is written — `return_value=` rather than a lambda — not whether the test can fail. The trial repository took it alongside banning `unittest.mock` outright, which is that repository's opinion and not one the register holds |
| `python.no-mocking-domain-logic` out of *judgment only* | **Yes** | Bucket 3 to bucket 2, citing the owner's `patched-under-test` as the instrument that shows a heuristic can hold it |
| `pytest-randomly`, `pytest-timeout`, `pytest-socket` | **Named, not installed** | `candidate:` on `python.test-independence` and `python.no-flaky-tests`, so the residue says what would assert them |
| A branch-coverage floor | **Named, not installed** | A new property, `python.branch-coverage-floor`, with coverage.py's `fail_under` as its candidate |

**The last two need what contract 2 does not have.** A profile can select ruff
codes, set ruff options and set one mypy key. A pytest plugin is a dependency
plus an `addopts` entry, and a coverage floor is a number that is the
repository's rather than the profile's — 94% was right here and is not a
default. Both are an instrument shape and an installer question, which is a
`craft_contract` change. It is the next slice rather than this one, so that the
part of the revision the current schema can carry is not held behind the part
that needs a new one.

### What was measured

S3's four criteria, applied to the three codes added:

| S3 criterion | Measured |
| --- | --- |
| Assembles and runs | The region renders and the publish check is clean. `HEAD` of the trial repository passes all three, so taking `@2` there costs nothing |
| No contradiction | None of the three shares a property or a remedy with a selected rule |
| False positives, probed | One test per code written broken and one written correctly. Each code fired on its broken case and nothing fired on the correct ones — including an `except` that calls `pytest.fail` rather than asserting, which is the case `PT017` could plausibly mistake |
| Cost | All three declare no fix: `python/strict` goes from 168 rules and 90 hand-work to 171 and 93, read from ruff 0.16.9 |

**Observed as well as probed, for one of the three.** Before the owner's own
guard landed, `PT017` fired once in the trial repository, on
`tests/test_progress.py`, a test that would have passed with nothing raised.
`B015` and `PLW0129` fired nowhere in its history. They are taken on the probe
and on what they are — a comparison with no `assert`, an `assert` on a string —
because a suite written quickly by an assistant is where both appear, and
neither has a correct use in a test.

## What this document owes

| Owed | When |
| --- | --- |
| ~~The install record: what was inferred, what was presented, what was chosen, what was written~~ — § The install, 2026-09-20 | Done |
| ~~The repository's size and shape at install, so the finding counts mean something~~ — § The repository at the moment of install | Done |
| ~~The span's position~~ — `craft-install` Step 4 now names *immediately after the header line*, 2026-09-25 | Done |
| ~~The comment that describes a table it no longer matches~~ — `gate-quality` Step 2 now writes no comment describing the section, and `craft-install` reports one it finds rather than editing it, 2026-09-25 | Done |
| ~~The other two things § What the install found raises — the missing assistant context file and repository tooling — answered or carried~~ — § The two questions the install left open. `craft-install` naming `CLAUDE.md` as the file to create is carried below | Done |
| ~~What the two weeks produced — findings met, rules fought, anything switched off~~ — § What held and § Rules fought. Nothing was switched off | Done |
| ~~S3's criteria as they hold in use, or the gap recorded~~ — § S3's criteria, as they held in use. They held; the gap is tests, recorded in § What the owner built that the profile did not | Done |
| ~~The owner's own account~~ — § The owner's account, 2026-10-18 | Done |
| ~~The profile revision: stricter test rules and a coverage floor~~ — § The revision, 2026-10-18. `python/strict@2` binds `python.tests-can-fail`; the guards and the floor are named in the residue | Done |
| **An instrument shape for a pytest plugin and a coverage floor**, so `python.test-independence`, `python.no-flaky-tests` and `python.branch-coverage-floor` can bind. A `craft_contract` change, and the installer has to ask for the floor's number | The next slice |
| **Carried, not felt:** `runtime-evaluated-base-classes` for pydantic, and `pydantic.mypy` named wherever `disallow_any_explicit` is; whether `C901` should give way to a dispatcher over `match`; a root `src =` written with any nested scope, because ruff resolves first-party imports from the nearest config and the owner had to add `src = [".", "src"]` by hand when `tests/ruff.toml` arrived | Not scheduled |
| **`craft-install` names `CLAUDE.md`** as the assistant context file to create when none exists | With the profile revision |
| **A stack arriving after install is reported.** The React row has held since 2026-10-10 with no profile installed and nothing saying so | `todo.md` |
| **The register's findings** — LNT-001's ESLint config defect, TYP-001 and vendored code, no locus computing the register's verdict, LNT-001's title and formatting, a stack arriving after a gate ran | [`04-build-plan.md`](../04-build-plan.md) § Phase 8, which is the register's list and not this workstream's |
| **The adopter's own two** — `gate-repo`'s record and stamp, and ADR 0047's `platform_limits:` entry for CI-001 and SEC-001 | The owner's, in that repository. Nothing here can push there |
