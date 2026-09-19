# Craft — the installer

Stage **S5** of [`plan.md`](plan.md). The chooser and the installer: the skill
that infers a repository's stack, presents the profiles with what each costs,
takes an explicit yes, and writes the pinned configuration at every locus the
control register declares.

**Written in slices, like [`design.profiles.md`](design.profiles.md) before it.**
Each section lands with the work that produced it, and [§ What this document
still owes](#what-this-document-still-owes) is the list of what has not been
written. S4 is the design this reads; nothing it settled is restated here, and
every section below cites where its premise came from.

Started **2026-09-19**.

## The configuration contract

**What the skill is called, what a repository may tell it, and what happens when
that file is absent, partial or wrong.** [ADR
0042](../adr/0042-a-deploying-skill-reads-local-configuration.md) is the
contract this joins; `design.profiles.md` § What a consumer pins settled that
Craft's pin lives in it and that an absent pin is not a default. What that
section left — and what a skill cannot be built without — is the rest of the
file's behaviour: which keys exist, which deliberately do not, and which of
*absent*, *partial* and *malformed* is an error.

### The skill is `craft-install`, and the key is its name

ADR 0042 part 2 keys the file by skill name, so the name is the contract's first
term rather than a later detail. `craft-install` is the parallel to
`register-install`, which installs the checker the same way: a verb that says
what the run does to the repository it is pointed at.

[ADR 0031](../adr/0031-the-plugin-is-named-for-the-register.md) does not reach it. That
naming rule governs the control-register family — the checker, the `register-*`
skills, the gates that keep their names — and Craft is deliberately a different
question, with a naming standard of its own in [`plan.md`](plan.md) § The naming
standard for this workstream. That table gains one row for skills with this
slice; the row is the standard, and this paragraph is not a second copy of it.

**Which plugin ships it is not settled here** and does not need to be: the key is
the skill's name, not its publisher, and a skill that moved between plugins would
keep both.

### Two values, and the three that were considered and refused

```yaml
# .claude/skill-config.yaml
craft-install:
  profile: python/standard    # <stack>/<level>, ADR 0052's two axes
  version: 7                  # the profile version installed, a counter
  residue: CLAUDE.md          # optional; where the unenforced prose is written
```

**The shape above is superseded by [§ One pin per stack](#one-pin-per-stack-and--two-values-was-too-narrow),
and is kept because the correction only reads against it.** A single `profile`
and `version` cannot express a repository with both stacks in it, which is the
ordinary shape here. What that section does not change is anything below: the
keys are the same keys, and the reasons they exist or do not are the reasons
they exist or do not.

`profile` and `version` are ADR 0052's, and `design.profiles.md` § What a
consumer pins and § The version is a counter are why each has the shape it has.
`residue` is this slice's addition, and the reason is that **the file an
assistant loads is a property of the repository, not of the profile**: one team
loads `CLAUDE.md`, another an `AGENTS.md`, another a directory of context files,
and the judgment-only residue is worth nothing written somewhere nothing reads.
Its default is the residue slice's to settle, not this one's.

Three more keys were considered. Each is refused, and the refusals are more
informative than the acceptances:

| Refused key | Why it is not in the contract |
| --- | --- |
| A per-rule `ignore:` or `exclude:` | Removing selectors from LNT-001's gated configuration is a **loosening of a narrowing-only control**, and `design.profiles.md` § The installer never writes a loosening is why the installer refuses that write. A key whose only use is to request a write the skill declines is worse than no key: it invites the request, then answers no. A team wanting fewer rules edits the configuration itself and answers for it through the variance machinery the register already has |
| A `config_path:` — which file to write | `controls.yaml`'s `stacks:` block names the tool and the ordered config locations per stack, so **Craft chooses what goes into a configuration and not where it lives** (`design.profiles.md` § The config surface). A key here would be a second statement of the register's answer, free to drift from it, which is theme T-2 by the most ordinary route available |
| A tool version or invocation | The lockfile is the version pin (§ What pins the tool version) and `tools.<tool>.invocation` is the register's (ADR 0020). Neither is Craft's to take as input |

### Absent, partial and malformed are three different things

ADR 0042 part 3 says absent file, absent key and absent value all get today's
behaviour. Craft departs from it for *absent* — there is no sensible default
level, and guessing one is the declared-archetype failure ADR 0052 rejected
wearing different clothes — and that departure is already recorded. What it left
is the middle case, which a skill meets on real repositories and a design
document can miss: a pin that exists and is incomplete.

| The file says | The installer does | Why |
| --- | --- | --- |
| No file, or no `craft-install:` key | Infers the stack, presents the levels with what each rule costs, takes an explicit yes | `design.profiles.md` § What a consumer pins. An absent pin is a decision not yet taken, and the skill's job is to take it with somebody |
| `profile`, no `version` | Treats it as a **first install of that profile** — installs the current version and writes the number | The version's only job is to answer *what moved since*. With no number there is nothing to compare, and inferring the version the team meant would fabricate exactly the fact a re-run reports |
| ~~`version`, no `profile`~~ | ~~Fails~~ | **Unspellable** under the corrected shape: the version is the value of the profile that names it. Struck rather than deleted, because the reason it was a failure is the reason the mapping is keyed the way it is — a version is a position in one profile's history, and without the profile it names nothing |
| Two levels of one stack — `python/standard` beside `python/strict` | Fails, writes nothing | Two answers to how much this team wants to be told about its Python. Choosing between them is the installer guessing at a level, which is the one thing it never does |
| A `profile` the register does not define | Fails, writes nothing | A typo must not quietly become an interactive prompt: the run would install a profile other than the one written down, and the file would still say the wrong thing afterwards |
| A `version` ahead of the register's current one | Fails, writes nothing | The same shape as a provenance stamp ahead of the register, which this repository treats as a defect rather than as staleness. It means the installer is older than the pin, and installing would move the repository **down** a profile — the loosening the installer never writes |
| A `version` behind the current one | Proceeds, and reports the `changes` entries between the two with their directions | The ordinary case, and ADR 0052's requirement |
| Unparseable YAML, or a value of the wrong type | Fails, writes nothing | ADR 0042's own rule for a malformed file, taken as written. Silently falling back to the interactive path would report the opposite of the truth — that nobody had chosen — about a repository where somebody had |

**Failing means writing nothing**, not writing what it could and reporting the
rest. A half-installed profile is the state nothing in the design can describe:
the stamp would claim a profile the configuration does not hold, and the next
run would read that claim as the truth.

### The pin, the stamp and the register are three records, and none is a copy

`design.profiles.md` § What a re-run does names three comparisons. Building them
means naming what is being compared, and the answer is three records that look
alike enough to be mistaken for the duplication this repository exists to
prevent:

| Record | Where | What it asserts | Written by |
| --- | --- | --- | --- |
| The **pin** | `.claude/skill-config.yaml` | Which profile this team chose, at which version | `craft-install`, on an explicit yes |
| The **stamp** | The header of each gated configuration file (ADR 0055 rule 2) | What was written into *this file*, and which evidence gates were open when | `craft-install`, in the same run |
| The **register** | `craft/` | What the profile is **now** | Craft, as rules change |

They are not three copies of one fact, because **they are expected to differ and
the differences are the report**. The pin is intent; the stamp is what happened;
the register is the present. It is the shape this repository already relies on
twice — `.pre-commit-config.yaml` states intent where `.git/hooks/pre-commit` is
whether anything runs, and `controls.yaml` is the register where a provenance
stamp is what was deployed against it.

The doctrine that comes with that shape comes with this one, and it resolves the
pairs the design left implicit:

- **Stamp behind pin**: the install did not complete, or somebody edited the pin
  by hand. Staleness, reported and offered a re-run.
- **Stamp ahead of pin**: the pin was lowered by hand after an install. The
  installer will not write down to it — writing down is the loosening it refuses
  — so it reports the pair and leaves both as they are.
- **Pin behind the register**: the ordinary delta. The `changes` entries between
  the two numbers, each with its direction.
- **Pin ahead of the register**: the defect row above.

### `craft_contract` is the register's number, not the team's

`meta.craft_contract` is 1, and the installer declares the highest value it
understands. A register above that is refused **whole** — not read as far as the
unknown field and installed for the rest — because a field the installer does
not understand is one it will ignore or misapply, and ignoring one silently is
how a rule stops being installed without anybody noticing.

**A consumer does not pin it**, and this is the one number in the picture that
does not appear in the file above. A repository has an opinion about which rules
it runs; it has no opinion about the schema those rules are written in, and a key
that let it express one would let a team ask for a format. The two numbers move
for different reasons — `design.profiles.md` § `craft_contract` is needed — and
only one of them is a choice.

### The installer writes the pin, and only its own key

ADR 0042 describes `.claude/skill-config.yaml` as written once, by hand. For
`lint-md` that is exact: the file is input, and the skill only reads it. Craft's
pin is input *and* the record of a choice made interactively, so somebody has to
write it after the choice, and the alternatives are worse:

- **Leave it to the team.** A choice nobody wrote down is re-asked on every run.
  Worse, it makes ADR 0052's guarantee unverifiable: *nothing changes under a
  repository that is not looking* needs something to compare against, and with no
  pin there is nothing.
- **Write it into the stamp only.** The stamp is in the gated configuration file,
  which is exactly the file a re-run needs to check the stamp *against*. A record
  that is only ever read from the artefact it describes cannot detect a hand edit
  to that artefact.

So `craft-install` writes `craft-install:` — its own key, with the values it was
given or chosen — and nothing else in that file. Another skill's key is not
Craft's to touch, and records that are not values the skill reads back are not
the file's at all: ADR 0042 excluded `deployment-decisions.yaml` from it for that
reason, and the exclusion binds the skill that would benefit from breaking it.

On every later run, a value that came from the file is reported as coming from
the file (ADR 0042 part 4). *`profile: python/strict` (from
`.claude/skill-config.yaml`)* and *`profile: python/strict` (chosen just now)*
are different facts, and the person approving the write has to be able to tell
them apart.

### What this section does not settle

- **The `residue` key's default**, and whether there is one. The residue slice's,
  with the wording.
- **Whether the installer may refuse to run at all** on a repository whose stamp
  shows hand edits, or only report them. Handed here by `design.profiles.md`
  § What a re-run does, and it belongs with the re-run behaviour rather than with
  the file format.
- **Whether the Craft register travels inside the installer or is read from a
  pinned ref.** `craft_contract`'s refusal can only fire in the second case, and
  which case it is, is the packaging slice's.

## How the stack is inferred

**What makes a repository Python, what makes one React, and what the installer
does when the answer is both, neither or half.** ADR 0052 ruled archetype out as
an axis and left the stack as the only thing to infer. [`plan.md`](plan.md) § S5
says *infer the stack from the repository*, singular, and the first thing this
slice found is that the singular is wrong — a Python service with a React
frontend is the ordinary Equal Experts shape rather than an edge case.

### Craft must agree with the control register about the stack

`controls.yaml` already answers half the question, and not as a convenience:

```yaml
predicates:
  python: "pyproject.toml exists"
  typescript: "tsconfig.json exists"
```

Craft reuses `python` as it stands and does not re-spell it. A second definition
of *is this a Python repository* is already illegal — the Craft register's
predicates share a namespace with the control register's, and
`tests/test_craft_register.py` fails a name defined in both — but the reason it
would be wrong here is stronger than the schema rule.

**A profile writes into a control's gated configuration** (ADR 0055). The ruff
selection goes into the file `stacks.python.gates.lint.config` names, which is
the file LNT-001 reads, at the loci LNT-001 wires. So a Craft that answered
*python* where the control register answers *not python* would write a
configuration **no control reads and no locus runs**: a file that looks like an
installed profile, enforces nothing, and reports success. Agreement with the
register is not tidiness; it is the difference between a profile and a document.

### `react` is not `typescript`, and a React profile needs both to be true

| Craft stack | Applies when | Has a locus when | What the profile writes into |
| --- | --- | --- | --- |
| `python` | `python` — `pyproject.toml exists` | The same predicate | `[tool.ruff.lint]` and `[tool.mypy]`, in the first location `stacks.python` names |
| `react` | `react` — `package.json` declares react | `typescript` — `tsconfig.json exists` | The flat config `stacks.typescript.gates.lint.config` names |

For Python the two questions have one answer and the distinction is invisible.
For React they come apart, and both halves fail in a way somebody would
otherwise have to discover:

- **React with no `tsconfig.json`** — a JavaScript-only React repository. The
  control register's `typescript` predicate is false, so LNT-001 does not apply,
  no locus is wired, and a flat config written here would be a file nothing runs.
  The rules are right and there is nowhere to put them.
- **`tsconfig.json` with no react** — Angular, Vue, a Node service. There *is* a
  gated linter, so the write would succeed, and `craft/react.yaml`'s bindings
  would be wrong for the repository: 29 `jsx-a11y` rules, 24 `@eslint-react`
  and 17 `react-hooks` against code with no JSX in it. `plan.md` § Scope put
  Angular out, and this is what installing anyway would look like.

The two predicates ask different questions — *which rules apply* and *where they
can be enforced* — and a stack name that merged them would answer one of them by
accident. Only 11 of `craft/react.yaml`'s 93 rule bindings are
`@typescript-eslint`'s, which is also the measure of how little of that file
would survive being installed on TypeScript alone.

### The predicate grammar cannot say *react is a dependency*

The control register's grammar is closed on purpose — `true`/`false`,
`<path> exists`, `<dir>/ exists`, `any <glob> exists`, and an expression outside
it is a schema error rather than a skipped check. None of those shapes can ask
what a manifest **declares**. Three ways out, and two of them are worse:

| Route | Why not |
| --- | --- |
| Extend the control register's grammar | A production added to the control checker for a consumer with no control behind it — nothing in `controls.yaml` gates on React — and ADR 0018 asks the opposite question before a rule enters that code |
| Take a path proxy: `any *.tsx file exists` | It fails in exactly the case the profile is for. ADR 0052 targets **new** repositories, where the dependency is declared before the first component is written: a repository one commit old has react in `package.json` and no `.tsx` at all. It over-matches, too — Preact and Solid use the same extension |
| **Define it in the Craft register, keyed on what the manifest declares** | `openapi-document`'s precedent exactly: keyed on the document's own declaration rather than on a filename, because a glob both misses and over-matches where the manifest does neither |

So `craft/meta.yaml` gains its second predicate, and it is the second thing the
installer must evaluate for itself:

```yaml
react:
  asks: package.json declares react in dependencies, devDependencies or peerDependencies
```

`peerDependencies` is in the list because a component library declares react
there and nowhere else, and its code is React code by every rule in the file.

**The two registers share a predicate namespace and not an evaluator.** The
control register's are compiled by a closed grammar; Craft's are a sentence the
installer implements. That is a real cost of the second register ADR 0053 chose,
and it is paid where it can be seen: the whole of it is the `asks:` lines under
`predicates:` in `craft/meta.yaml`, two of them today.

### What the installer does, per repository

| What is there | Profiles offered |
| --- | --- |
| `pyproject.toml`; `package.json` declaring react; `tsconfig.json` | `python/*` and `react/*`, chosen separately, one pin per stack |
| `pyproject.toml` only | `python/*` |
| react and `tsconfig.json`, no `pyproject.toml` | `react/*` |
| `tsconfig.json`, no react | **None.** Craft has no TypeScript profile and does not install the React one here |
| react, no `tsconfig.json` | **None.** The rules apply and nothing gates them |
| Neither stack | **None** |

The rule behind the last three rows: **an empty answer names the predicate that
produced it.** *No profile applies* is not reviewable; *no profile applies
because `package.json` declares no react and there is no `pyproject.toml`* is,
and it tells a reader exactly what would change the answer. It is the same
property § What the installer records asks of the gate line in the stamp, applied
to the case where nothing is written at all.

### One pin per stack, and § Two values was too narrow

That section's contract carried a single `profile` and a single `version`, which
is `design.profiles.md` § What a consumer pins as it stands and cannot express
the repository above. **This section corrects it.** The pin is a mapping, keyed
by profile name and valued by the version installed:

```yaml
# .claude/skill-config.yaml
craft-install:
  profiles:
    python/standard: 7
    react/standard: 4
  residue: CLAUDE.md
```

Three consequences, and each of them moves a row in § Absent, partial and
malformed:

- **A version with no profile becomes unspellable.** The version is the value of
  the profile that names it, so the row describing that failure is struck rather
  than answered.
- **Two levels of one stack is spellable, and fails.** `python/standard: 7`
  beside `python/strict: 2` are two answers to how much a team wants to be told
  about its Python, and choosing between them would be the installer guessing at
  a level — the one thing § What a consumer pins says it never does.
- **A profile key with an empty value** is the first-install case that table
  already describes, unchanged.

The version stays a bare number rather than a mapping with room in it. Anything
more about an install — when, by which skill version, against which gates — is
the **stamp's**, and the stamp is in the file the install wrote. The pin is
intent, and intent is one number per profile.

### What this section does not settle

- **Monorepos.** `pyproject.toml exists` is root-relative, so `api/pyproject.toml`
  makes a repository Python to nobody. Craft inherits that answer rather than
  correcting it, for the reason the first subsection gives: a Craft that was
  cleverer than the control register about where a stack lives would install
  profiles at loci the register does not wire. Whether either register learns
  about subdirectories is the control register's question first.
- **Whether a `typescript` scope is ever minted.** Eleven bindings would
  transfer; `plan.md`'s naming standard asks a scope to be earned, and eleven is
  not a stack. Nothing mints one here.

## What the chooser shows, and where the numbers come from

**Before anybody says yes, they are told what the profile turns on and what it
will cost them.** `plan.md` § S5 requires both, and the second half is why S3
measured cost at all. This section is where the numbers come from, and the
answer is that they are **resolved from the register** rather than typed into a
document: [`scripts/craft_select.py`](../../scripts/craft_select.py) reads
`craft/*.yaml`, expands every instrument against the installed tool, and prints
what a profile binds and what each rule declares about fixing itself.

```bash
uv run python scripts/craft_select.py                      # every profile
uv run python scripts/craft_select.py --profile python/strict --per-rule
uv run python scripts/craft_select.py --against-bench      # the register against S3
```

### The register resolves to exactly what S3 benched

`--against-bench` reports **0 disagreements**, across both stacks and both
levels: every selector the bench's hand-written configuration carries, the
register resolves to, and nothing the register binds is missing from it.

That check was owed and nothing was performing it. ADR 0053 made the register
the source and `assess.rules.md` a stage record, and
`tests/test_craft_register.py`'s superset test holds the register to that
**document** — it says no row was lost in the migration. Nothing held the
register to the **configuration somebody actually ran**, which is the thing S3's
exit criterion was about. Two descriptions of one decision, written by two
passes from the same rows, are worth exactly as much as their agreement.

Two things surfaced on the way there, and both are the kind of detail that only
a run finds:

- **A ruff selector is not a textual prefix.** `N` is pep8-naming, and
  `"NPY001".startswith("N")` is true — the first version of the comparison
  reported four NumPy rules as benched-but-missing. The selector resolves
  against the linter prefixes the catalogue itself declares, which is the same
  correction the register already made when it replaced ranges with `linter:`.
- **One rule in ruff 0.16.5 has no code.** `pytest-fixture-autouse`, in preview
  since that release, reports `"code": null`. A catalogue keyed on it carries a
  `None` that every comparison then trips over. A rule with no code cannot be
  selected, so it is not in the catalogue.

### What a person is shown is not the rule list

A 141-line dump is a receipt, not a decision aid. What the chooser shows per
applicable profile is what somebody can hold in their head while saying yes:

| Shown | `python/standard` today |
| --- | --- |
| Properties bound, by tool | 40 — 39 ruff, 1 `ruff format` |
| Rules, and the tool version they were read from | 141, ruff 0.16.5 |
| What declares a fix, in the tool's own three words | always 17, sometimes 52, none 72 |
| The hand-work share | **72 of 141 (51%) declare no fix** |
| Thresholds and tool settings that come with it | 2 |
| Preview rules, which a release may move | none at `standard`; `PLR0904` and `PLR1702` at `strict` |
| The residue this profile does not enforce | 22 `python.` properties with no instrument, and 42 `any.` rows |

**These are C7's numbers, re-derived from the other end.**
`review.bench.md` § What each rule costs read 141 rules and 72 hand-work from
the benched configuration; this reads the register and gets 141 and 72. The
agreement is the check rather than a coincidence.

`--per-rule` exists for the person who wants the receipt, and the chooser does
not show it unasked.

### Named is not enabled, and the chooser says which it is showing

`craft/react.yaml` names **88** rules at `standard`. The configuration S3
benched resolved to **132**, and the gap is not a discrepancy: two presets are
part of the profile *by the register's own resolution* —
`react.no-legacy-proptypes` and `react.jsx-runtime-assumed` are `satisfied_by`
taking `@eslint-react`'s `recommended` as the base, and `jsx-a11y`'s
`recommended` carries five rules the register counts as inherited rather than
keyed.

So there are two true answers to *what does this turn on*, and a chooser that
shows one of them without saying which has misled somebody either way: a team
that consents to 88 rules and meets 132 was told the wrong number, and a team
told 132 cannot find 44 of them in the register. **It shows both**, labelled —
the rules the register names, and the rules the resolved configuration will
enable.

### Cost is read from the tool that will run, and it is a floor

C7 read cost from ruff's `fix_availability` and each ESLint plugin's
`meta.fixable`, and `review.strict.md` then ran `--fix` over the violation
cases and found the declarations overstated — the `react-hooks` family declares
the most fixes in either stack and applies the fewest. **What a tool declares is
a floor on cheapness rather than an estimate of it**, so the chooser says
*declares a fix*, never *is cheap*, and the wording is not a nicety: a team that
reads "auto-fixable" and meets a finding that survives its own fix has been told
something untrue by the tool that installed it.

The reading is per version, for the same reason C7 is a command rather than a
table: a number read from ruff 0.16.5 is a number about ruff 0.16.5, and
`design.profiles.md` § What pins the tool version puts the version in the
adopter's lockfile rather than in anything Craft writes.

### What cannot be read is reported unread, and the React half cannot be read yet

Python's cost is readable before anything is written: ruff is one binary and
its taxonomy answers without a run. React's is not — it needs the six plugins
resolved from a `node_modules`, and a repository at its first install has not
got one. The script reports that as `UNREAD` with the reason rather than as
zero, which is the posture `register-check deployments` already takes: *a run
that cannot look says so*.

For the chooser this is not enough, because the yes has to be informed. It shows
the figures **`review.bench.md` measured, labelled with the versions they were
read at**, and re-reads from the installed tree once the dependencies are there
— reporting any difference rather than leaving the presented numbers standing.
A labelled approximation somebody can check beats both alternatives: silence,
and a number presented as current that was read on another machine in September.

### What this section does not settle

- ~~**Who installs the six ESLint plugins.**~~ Answered by § What the installer
  writes: through the command `ecosystems.<name>.add_dev_dependency` already
  names, chosen by lockfile, with no version picked by Craft — and nothing is
  written if they cannot be added.
- **What the chooser does when the tool is not installed at all.** The fallback
  above presents the bench's figures; it does not say whether the installer may
  proceed to write against a tool it has never been able to read.

## What the installer writes, and how it shares a file

**The Python half is built** — [`scripts/craft_render.py`](../../scripts/craft_render.py)
turns a profile into the exact lines an installer places, and
`tests/test_craft_render.py` holds that rendering to the register. The React
flat config is owed, and the box in [`todo.md`](todo.md) stays open until it
exists. What this section settles is the part both stacks share: **how a writer
puts its lines into a file it does not own.**

```bash
uv run python scripts/craft_render.py --profile python/strict
uv run python scripts/craft_render.py --profile python/strict --file src
```

### The installer writes at no loci at all

`plan.md` § S5 says *writes the pinned configuration at every locus the profile
declares*, and a profile declares none. LNT-001 declares three — editor,
pre-commit and CI — and `gate-quality` is what wires them; ADR 0009 is why all
three read **one** configuration. So Craft writes one file's worth of lines and
reaches every locus by construction, which is a stronger guarantee than writing
three times and is not the installer's doing at all.

### The second writer is not `gate-quality`

ADR 0055 records, as a trade-off, that *`pyproject.toml` acquires a second
writer* and that `gate-quality` writes the same file. **It does not.**
`gate-quality`'s templates are the loci artefacts — `.pre-commit-config.yaml`,
the CI steps, the editor settings — and LNT-001's provenance stamp lives in
`.pre-commit-config.yaml` beside the hook. Nothing automated writes
`[tool.ruff]` today; in this repository that section is hand-written, comments
and all.

That changes what the discipline is for. It is not two skills coordinating a
file, which could be solved by either of them knowing about the other. It is
**Craft writing into a file a person wrote**, and the person is not going to
read Craft's documentation first.

### A contribution is a span of lines, not a table

Two writers to one TOML document cannot each own a table header. A second
`[tool.mypy]` is not a merge, it is an invalid file — and TYP-001 requires that
table to exist already, since `typecheck-strict-and-blocking` reads `strict` and
the coverage key inside it. So the renderer emits `(table, lines)` pairs and
never a header, and the installer places each span:

```toml
[tool.ruff.lint]
# >>> ee-craft python/strict@1
# ee-craft: python/strict@1  gates: none (no any. property binds an instrument)  craft-contract: 1
select = [
  "ANN001", "ANN201", "ANN204", "ANN205", "ANN206", # python.annotate-public-api
  ...
]
# <<< ee-craft
```

Three things follow, and each is a rule rather than a style:

- **Every line Craft writes is inside a marked span**, so *what did the profile
  turn on here* is answerable by reading the file, which is the question ADR
  0055 rule 2 exists for.
- **The header is written only where the table is absent.** In a new repository
  Craft writes `[tool.ruff.lint]` itself; in one that has it, Craft writes
  between the existing header and whatever follows.
- **The stamp goes once per file**, at the first span, and every other span
  names the profile in its own marker. Six copies of one stamp would make the
  file harder to read without making it more true.

### A write is a union, and a key somebody else owns is a refusal

Craft rewrites what is inside its markers, wholly, on every run. It never edits
a line outside them, and the reason is the register's rather than politeness:
removing a selector is a **loosening** of a `narrowing-only` control, which
`design.profiles.md` § The installer never writes a loosening already refuses.

That leaves one case with no comfortable answer. A repository whose
`[tool.ruff.lint]` already carries `select = ["E501"]` cannot receive Craft's
span as written — two `select` keys in one table is the same invalid document as
two headers. Two ways out, and the second is worse:

| | |
| --- | --- |
| **Refuse, and report the union it would have written** | The team pastes once, or deletes their line and re-runs. Authorship stays legible: every value inside the markers is the profile's, and nothing inside them was somebody else's decision |
| Absorb — move their values inside the markers, commented as kept | It deletes a line the team wrote and re-publishes their decision under Craft's name, and the next re-run rewrites the span carrying a stranger's selectors inside it. A merge nobody asked for, remembered forever |

**Refuse, and report.** The cost is real and it is paid by exactly the
repositories ADR 0052 says are not the target: a new repository has no
`[tool.ruff.lint]` to collide with, and the installer writes the whole span.

### The nested configuration passes all four of LNT-001's asserts

`design.profiles.md` § The config surface left this to the implementing work:
two properties are scoped to the package source, ruff has no per-path `select`,
and the only expression the tool allows is a nested configuration — so an
installed profile writes a second file, and `register_check`'s `_configured`
reads the first location only. Whether that breaks LNT-001 was recorded rather
than assumed.

**It breaks none of them**, and the four are worth naming one at a time:

| Assert | Why the nested file does not reach it |
| --- | --- |
| `linter-wired-at-all-loci` | Reads the loci, which run `uv run ruff check` and resolve both files the same way |
| `stack_tool_pinned_in_lockfile` | Reads the lockfile |
| `no-failure-suppression` | Reads the CI invocation |
| `provenance_stamp_present` | Reads `gate-quality`'s stamp, which is in `.pre-commit-config.yaml` |

**What it does cost is the audit's view.** `_configured` returns the root
location and stops, so a later edit to `src/ruff.toml` — removing `S101`, or the
docstring rules — is invisible to `register-variance` and to every LNT-001 run.
The thing that would notice is Craft's own re-run, comparing the stamp against
the file as it stands. That is the second of the three comparisons
§ What a re-run does names, and this is the case that makes it load-bearing
rather than tidy.

Verified rather than reasoned: the rendered configuration plus the nested file,
run over a five-line module and a two-line test, reports `S101` and the `D1xx`
rules in `src/` and neither in `tests/`.

### The six ESLint plugins, which the register already knows how to add

§ What the chooser shows handed this here as the first thing to answer. A flat
config importing `@eslint-react` from a repository that does not depend on it
errors on its first run, and ADR 0020 requires the locus to reach the lockfile's
binary rather than something on `PATH`.

**The answer needed no new data.** `controls.yaml`'s `ecosystems:` block already
carries `add_dev_dependency`, keyed by lockfile — `npm install --save-dev
{package}`, `pnpm add --save-dev {package}`, and the other two — and
`lock_entry` is the pattern that confirms a package landed there. So the
installer detects the lockfile, uses the command the register names, and
**chooses no version and names no package manager**: the resolver picks the
version and the lockfile records it, which is where
`design.profiles.md` § What pins the tool version already put that decision.

Two rules come with it:

- **The chooser names the six before the yes**, so the consent covers adding
  them. Six dependencies is a supply-chain change, and a team that agreed to a
  lint profile did not thereby agree to whatever the installer felt was needed.
- **If they cannot be added, nothing is written.** A configuration referring to
  plugins the repository does not have is a gate that fails for the wrong
  reason, which is worse than no profile at all.

The asymmetry is worth stating plainly: **Craft's React profile brings six
dependencies no control mandates, and its Python profile brings none**, because
ruff ships every rule it selects inside the binary LNT-001 already requires.

### Two things the tool had to be asked, rather than remembered

- **Where a setting lives is ruff's to say.** `max-complexity` is `mccabe`'s and
  `max-statements` is `pylint`'s; written into the wrong table both parse and
  **neither applies**, so the failure mode is a threshold that silently does
  nothing. The renderer reads `ruff config --output-format json`, which
  enumerates every option by the path a file spells, and fails loudly on a name
  it finds in two places. A table of those paths inside Craft would be the
  checker-side dictionary ADR 0018 was written about, stale the first release
  that moves an option.
- **`preview = true` against a linter selector is wholesale.** C8 measured the
  cost of the switch as nothing *for a selection spelled in exact codes*, and
  `standard` is not spelled only in codes — four of its instruments are
  `linter:` selectors, which is the correction the register made when it
  replaced ranges. `strict` needs `preview = true` for `PLR0904` and `PLR1702`,
  so the same switch would enable whatever preview rules those four linters
  hold. They hold none at ruff 0.16.5. That is a fact about a version rather
  than a property of the design, so the renderer checks it at render time and
  refuses to write the switch if it ever stops being true.

### What this section does not settle

- **The React flat config.** The renderer is Python-only, and the box stays
  open. The shape is the same — spans inside a file — but the file is
  JavaScript rather than data, which makes *what is inside the markers* a
  different problem.
- **Whether the installer may refuse to run at all** on a repository whose stamp
  shows hand edits inside a span. Still open from § What a re-run does, and now
  with a second case attached to it: the nested file nothing else audits.

## The React config is one file, and rendering it found what reading could not

The writing box is closed. `craft_render.py --profile react/standard` emits the
whole `eslint.config.mjs`, and the two levels it renders resolve to **exactly
the configuration S3 benched** — checked by resolution rather than by reading,
which is the section's last subsection.

### Written whole, because a flat config is a module

The Python surface takes spans inside a file somebody else may own. This one
cannot: a flat config is imports, constants and an exported array, and no span
of it means anything on its own. So Craft writes the file or writes nothing,
and the refusal is the same shape as the Python one rather than a weaker
version of it — **if a config exists that Craft did not write, the installer
reports what it would have written and stops.**

The file is `eslint.config.mjs`, and the extension is a decision. A new
repository's `package.json` may not say `"type": "module"`, and the config this
profile needs is ESM — `.mjs` is the spelling that does not depend on a field
Craft would otherwise have to write into somebody's manifest. It also walks
into ESLint's lookup order, which is the ruff trap in another ecosystem: a
`.mjs` written beside an existing `eslint.config.js` **loses**, silently, the
way a `ruff.toml` beside `[tool.ruff]` wins silently. The refusal above is what
keeps that from being discovered by a team whose rules never fired.

### Three things the migration had lost, and a renderer found all three

`craft/react.yaml` was migrated from `assess.rules.md` and checked by a superset
test that reads identities out of a table. Every row was there. **Rendering it
into a configuration is what showed that the rows were not enough**, and the
three gaps are worth naming because each would have shipped a defect:

| What was missing | What would have shipped |
| --- | --- |
| The `testing-library` rules were scoped to tests in the bench and to nothing in the register | Eleven test-hygiene rules applied to production code — `prefer-screen-queries` on a component is the kind of finding that teaches a team to switch the profile off |
| The two presets the profile takes as a base were prose in two `satisfied_by` rows and data nowhere | `react.no-legacy-proptypes` and `react.jsx-runtime-assumed` silently unbound, and 34 accessibility rules reduced to the 29 the register names |
| Six of the seven `@eslint-react` rules C1 stood down were not recorded; one was | Six defects reported twice each, by two plugins, in the state C1 and C4 spent a bench resolving |

**Reading a register tells you it is consistent. Rendering it tells you it is
complete.** The superset test could not have found any of these, because each is
a fact about what the configuration *does* rather than about which properties
exist — and `assess.rules.md`, the document it holds the register to, does not
carry them either.

All three are now register data: `bases:` in `craft/react.yaml`, `scope: tests`
on five properties, and six new `alternatives:` entries beside the one that was
already there. The `react/*` alternatives stay without an `off` line, and the
rule that decides is derivable rather than a judgement in the renderer: **a
losing rule is stood down only where its namespace is a base**, because a preset
that is not applied has nothing to stand down.

### `craft_contract` moves to 2, and the profile version to 2 with it

Three fields no earlier reader knew: `bases:`, the `namespace:`/`package:` pair
on the six plugin sources, and `scope: tests`. The first is why the number had
to move at all — **an installer that did not understand `bases:` would write a
configuration missing two presets** and unbind two properties without reporting
anything, which is precisely the case § `craft_contract` is the register's
number says the field exists to refuse.

The React profile versions move to **2, `moved: neither`**. Nothing about the
profile changed: the scoping, the bases and the stand-downs are what S3 ran and
what `review.bench.md` records. This is the register catching up with the bench,
and calling it a narrowing would claim the profile got stricter when what
happened is that it stopped being wrong.

### The three scopes are fixed globs, and the installer reports them

```js
const SOURCE = ['src/**/*.ts', 'src/**/*.tsx']
const MODULES = ['src/**/*.ts']
const TESTS = ['**/*.test.ts', '**/*.test.tsx', '**/*.spec.ts', '**/*.spec.tsx', '**/__tests__/**']
```

`MODULES` is `craft/react.yaml`'s `scope: modules` — C6 set it to *not a `.tsx`
file*, which is the closest a file pattern gets to *not a component*. `TESTS` is
the new one, and it is **a default the installer reports rather than a
configuration key**: a new repository has no tests to infer a convention from,
which is the repository ADR 0052 says the profile is for, and a team that keeps
its tests somewhere else can see from the report why theirs are unlinted. If
that turns out to be wrong in use, S6 is where it will show.

### Verified against the bench by resolution, not by reading

The text of a generated config proves nothing — two files can differ in every
line and resolve to the same rules, or agree line for line and resolve
differently once a preset moves. So the check is ESLint's own
`--print-config`, over the three file kinds C1 resolved, against the
configuration `scripts/craft_profile.py` benched:

```bash
uv run python scripts/craft_scaffold.py && (cd temp/craft-bench/react && npm install)
uv run python scripts/craft_profile.py && uv run python scripts/craft_profile.py --level strict
uv run python scripts/craft_render.py --profile react/standard > temp/craft-bench/react/eslint.config.mjs
# then, per file: npx eslint --config <each> --print-config <file>
```

| File kind | Enabled rules, rendered | Enabled rules, benched | Difference |
| --- | --- | --- | --- |
| `src/components/Basket.tsx` | 120 | 120 | none, either direction |
| `src/lib/money.ts` | 121 | 121 | none |
| `src/components/Basket.test.tsx` | 131 | 131 | none |
| `Basket.tsx` at `strict` | 121 | 121 | none, and the one option identical |

And a run rather than a resolution: a deliberately wrong component — an effect
setting state, a missing dependency, an `any`, an unlabelled image, a
click handler on a `div`, an index key — reports **eight findings, each once**.
That last word is the check on the stand-downs: before them, three of those
eight arrived twice.

### What this section does not settle

- **Who runs `npm install`.** § What the installer writes settles that the
  installer adds the six plugins through the command `ecosystems:` names; it
  does not settle whether the installer may then run the ecosystem's install to
  make the config loadable, or leave a repository whose config references
  plugins the lockfile has and the tree does not.
- **The scaffold's `tsconfig.json`.** The type-checked rules need a project
  service, and the profile assumes a `tsconfig.json` that TYP-001 already
  requires. What an installer does when `include` does not cover the files the
  profile lints is unexamined.

## The residue is a document of its own, and it is lint-clean

`plan.md` § S5's last write: *hand back the judgment-only residue as prose an
assistant loads, labelled unenforced*. `craft_render.py --file residue` is that,
and three decisions shaped it.

```bash
uv run python scripts/craft_render.py --profile python/standard,react/standard --file residue
```

### Seventy-one properties, in four states, and only three are handed over

A property with no instrument is not one kind of thing, and the schema already
knows it — § The Craft register's schema records **three ways of having no
instrument**, and `candidate:` is a fourth state beside them. The document
treats them differently because a reader can act on some and not others:

| State | In the document | Why |
| --- | --- | --- |
| `unenforced`, bucket 3 — **32** | Listed, with what it asserts | Judgment only. Nothing can decide them but a person, which is what the profile is silent about |
| `unenforced`, bucket 2 — **33** | Listed | A check could hold them and none is written. The list a later profile version is drawn from |
| `unenforced` bucket 1, and `candidate:` — **6** | Listed, with the instrument named | Either measured and demoted — the reason is the reason not to re-enable it — or unmeasured, with ADR 0051's third precondition unmet |
| `satisfied_by` and `out_of_scope` — **12** | **Counted, by name, nothing more** | They hold already. One is a choice the profile made; the rest are a control's or `gate-repo`'s |

The fourth row is the one worth arguing about, and the argument is the same one
ADR 0055 makes about credit. Handing a reader *`react.strict-type-checking`:
`tsconfig` enables the strict family* as something to watch would be asking them
to re-check what TYP-001 gates on every run — and a residue that padded itself
with other people's work would be less honest, not more thorough.

### The label is the document, not a heading in it

Everything here is unenforced, so the file says so in its first sentence and
never again pretends otherwise: *nothing here fails a build, no tool reports on
it, and none of it is a rule*. `plan.md` § What this workstream will not do ends
on *ship a rule that claims enforcement it does not have*, and a residue written
in the imperative — **always** validate at boundaries — is exactly that rule,
one file away from the configuration that does block a merge.

So each entry is what the property asserts and why nothing checks it, and where
the register's reason says only `Bucket 3.` the document omits it rather than
padding: the section heading has already said it.

### It has to pass the gate the register requires

**Craft writes Markdown into a repository whose Markdown DOC-001 lints.** The
first render failed `markdownlint` three ways — a code span with spaces in it,
because one candidate's `tool:` is *commitlint with
@commitlint/config-conventional, or commitizen*; `__init__` read as emphasis,
because the register's prose was written for YAML and not for Markdown; and a
trailing blank line, because `print` adds one to a document that already ends in
a newline.

An installer of this standard that wrote a file failing this standard would be
the plainest defect available to it, so `tests/test_craft_render.py` runs the
repository's own pinned `markdownlint-cli2` over the rendered residue. The
register's own prose was corrected where it caused one of the three, which is
the register learning that its text has a second audience.

### What this section does not settle

- **Where the file goes, and what points at it.** `residue:` in
  `.claude/skill-config.yaml` names the file an assistant loads; whether Craft
  writes the list into that file or writes it beside and leaves a marked span
  pointing at it is the installer's, not the renderer's. The span discipline
  from § What the installer writes is what makes the second possible.
- **Whether an assistant reads it at all.** Craft can write a file; it cannot
  make a harness load one, and saying so is part of the label.

## What this document still owes

Named so that a reader can tell a gap from an omission. Every row is work rather
than an open question — S4 closed the design questions, and
`design.profiles.md` § What this document still owes is empty because of it.

| Owed | Which box in [`todo.md`](todo.md) |
| --- | --- |
| ~~How the stack is inferred, and what a repository with two of them gets~~ — **done**, § How the stack is inferred. It corrected the contract's pin shape on the way | Infer the stack from the repository |
| ~~What the chooser shows: each level's rules, and what S3 measured each costs to satisfy~~ — **done**, § What the chooser shows. It owes the writing slice one question: who installs the six ESLint plugins | Present each applicable profile with what it enables |
| The shape of the explicit yes, and what is shown before it | Require an explicit confirmation |
| ~~What is written, and the stamp at each span~~ — **done**, § What the installer writes and § The React config is one file. Both stacks render from the register | Write the pinned configuration; record what was written |
| ~~The residue: its wording, and the unenforced label~~ — **done**, § The residue is a document of its own. Its file and the pointer to it are the installer's, and stay owed | Emit the judgment-only residue |
| A second run over the installer's own output changing nothing, and what "nothing" covers when a gate has opened since | Make a second run change nothing |
| Packaging, versioning and publication, and where the register sits in it | Version and publish it |
