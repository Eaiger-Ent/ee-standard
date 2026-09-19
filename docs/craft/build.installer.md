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

- **Who installs the six ESLint plugins.** The Python profile has no such
  question — ruff ships every rule it selects — but a flat config importing
  `@eslint-react` from a repository that does not depend on it is a
  configuration that errors on the first run, and LNT-001 requires the linter to
  be reached through the lockfile (ADR 0020). Whether the installer adds them to
  the manifest, or refuses until somebody else has, is the writing slice's, and
  it is the first thing that slice should answer.
- **What the chooser does when the tool is not installed at all.** The fallback
  above presents the bench's figures; it does not say whether the installer may
  proceed to write against a tool it has never been able to read.

## What this document still owes

Named so that a reader can tell a gap from an omission. Every row is work rather
than an open question — S4 closed the design questions, and
`design.profiles.md` § What this document still owes is empty because of it.

| Owed | Which box in [`todo.md`](todo.md) |
| --- | --- |
| ~~How the stack is inferred, and what a repository with two of them gets~~ — **done**, § How the stack is inferred. It corrected the contract's pin shape on the way | Infer the stack from the repository |
| ~~What the chooser shows: each level's rules, and what S3 measured each costs to satisfy~~ — **done**, § What the chooser shows. It owes the writing slice one question: who installs the six ESLint plugins | Present each applicable profile with what it enables |
| The shape of the explicit yes, and what is shown before it | Require an explicit confirmation |
| What is written, per locus, and the stamp line at each | Write the pinned configuration; record what was written |
| The residue: its file, its default, its wording, and the unenforced label | Emit the judgment-only residue |
| A second run over the installer's own output changing nothing, and what "nothing" covers when a gate has opened since | Make a second run change nothing |
| Packaging, versioning and publication, and where the register sits in it | Version and publish it |
