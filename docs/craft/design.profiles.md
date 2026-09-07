# Craft — the design

Stage **S4** of [`plan.md`](plan.md). What gets built, decided before it is
built.

**Four of this stage's decisions were taken ahead of it**, on 2026-09-06, and are
Accepted ADRs — a fifth,
[0055](../adr/0055-craft-writes-into-a-gated-section.md), was produced by this
document's first section rather than ahead of it: [0051](../adr/0051-a-craft-rule-becomes-a-control-by-being-installed.md)
on the craft/register boundary, [0052](../adr/0052-a-profile-is-a-stack-and-a-strictness.md)
on the profile model, [0053](../adr/0053-the-craft-mapping-is-register-data.md) on
where the mapping lives, and [0054](../adr/0054-craft-cites-its-sources-and-copies-none.md)
on attribution. This document is the design that reads them, not a summary of
them — each is cited where it binds and restated nowhere.

**Written in slices, like `review.bench.md` before it.** Each section lands with
the work that produced it, and [§ What this document still
owes](#what-this-document-still-owes) is the list of what has not been written.
A design document that reads as finished while half of it is missing is worse
than one that says which half.

Started **2026-09-07**.

## What the ADRs taken ahead of this stage left it

| ADR settled | S4 owes |
| --- | --- |
| A profile is a **stack** and a **strictness**; no archetype axis, no age axis (0052) | What the strictness **levels are**, how a profile is named, how it is versioned |
| The `any.` groups gate on the artefact they read (0052) | Which artefact gates which group, and where the installer records what it switched on |
| A profile is pinned by the consumer, and reports what moved (0052) | What "what moved" means when a rule is *removed* from a level |
| The mapping is data, in a Craft register of its own (0053) | That register's schema, and whether it is generated from `assess.rules.md`, replaces it, or is written fresh |
| A craft rule becomes a control by being installed as one (0051) | Nothing here yet; S5's installer is what mints the entry |
| Cite every source, copy none (0054) | Nothing here yet; the citation lives in the register schema above |

S3 also handed forward six things, in `review.bench.md` § What S3 hands forward.
Two of them are answered below and the other four are named where they land.

## The config surface

**What a profile writes, per stack, and into which file.** This is the section
S3 could not write: its bench put a `ruff.toml` beside the scaffold's
`pyproject.toml` because the bench varies the instrument while holding the
subject still, and said in terms that *which surface the installed profile writes
is S4's question and this file does not answer it*. This answers it.

It also closes two of S3's six hand-forwards — the profile pinning no tool
version, and the Python profile configuring no type checker. Both turn out to
have answers already sitting in `controls.yaml`, which is the finding worth
having.

### The control register already names most of it

`controls.yaml`'s `stacks:` block declares, per stack, the lint tool, the type
checker, the invocation for each, and **the ordered list of files where each
tool's configuration may live**. It is not a Craft artefact and it long predates
this workstream; it is what LNT-001 and TYP-001 read to find out whether a
repository has configured the tools they gate.

That makes the config surface a question this workstream mostly does not get to
answer. Craft chooses **what goes in** the configuration. Where the
configuration lives was decided when the control register was written, and a
Craft document that listed the files again would be the second copy this
repository exists to prevent — the failure `CLAUDE.md` calls theme T-2, arriving
by the most ordinary route available: someone writing down something true.

**So the rule for this section is:** every file named below is quoted from
`stacks:`, and none is chosen here. Where Craft has a choice it is a choice
*within* what the register already permits, and the paragraph says so.

### Python

| | The register says | The profile writes |
| --- | --- | --- |
| Lint | `ruff`, `uv run ruff check`; config at `pyproject.toml` §`tool.ruff`, then `ruff.toml`, then `.ruff.toml` | `pyproject.toml` §`tool.ruff.lint` — the **first** location, for the reason below |
| Type check | `mypy`, `uv run mypy`; config at `pyproject.toml` §`tool.mypy`, then `mypy.ini`, `.mypy.ini`, `setup.cfg` | `pyproject.toml` §`tool.mypy` — one key, and § The type checker says which |

**Why the first location and not the one the bench used.** The list in `stacks:`
is a *search order*: `register_check.asserts_command._configured` returns the
first location that actually configures the tool and stops. Ruff's own
precedence runs the other way — a `ruff.toml` in a directory **overrides**
`[tool.ruff]` in the `pyproject.toml` beside it rather than merging with it.
Verified rather than read:

```bash
# pyproject.toml selects E501 at line-length 20; ruff.toml selects F401.
$ uv run ruff check m.py
F401 [*] `os` imported but unused
```

`E501` never fires and the line length is ignored. So a profile that writes a
`ruff.toml` into a repository whose `pyproject.toml` already carries
`[tool.ruff]` leaves LNT-001 auditing a section ruff is no longer applying —
the checker reads the first location, ruff obeys the last. **Nothing warns.**
Writing the location the register searches first keeps the audited
configuration and the running configuration the same file, which is what
ADR 0009's *one configuration* is for.

**The residue this leaves.** S3's `S101` scoping needs a second ruff
configuration — a nested `src/ruff.toml`, because ruff has no per-path
`select` and `per-file-ignores` is the exemption the register's resolution
rejected. A nested file does not break ADR 0009: all three loci still run
`uv run ruff check` and resolve the same two files the same way, so the *one
configuration* every locus reads is intact. What it does break is the audit's
view of it — `_configured` sees the root file alone. Whether that matters to
LNT-001's four asserts is a question for the implementing work, and it is
recorded here rather than assumed away.

### React

| | The register says | The profile writes |
| --- | --- | --- |
| Lint | `eslint`, `node_modules/.bin/eslint`; config at `eslint.config.*`, then `.eslintrc*` | `eslint.config.js` — flat config, the only shape the profile's plugins support |
| Type check | `tsc`, `node_modules/.bin/tsc`; config at `tsconfig.json` §`compilerOptions`, coverage at `include` | `tsconfig.json` §`compilerOptions` — nothing, and § The type checker says why |

**The register's stack key is `typescript`; Craft's scope is `react.`** They are
not the same word and they are not a disagreement. ADR 0052's axis names the
stack a *profile* targets; `stacks:` names the stack a *control* applies to, and
LNT-001 applies to TypeScript whether or not React is in it. A React profile
writes into the TypeScript stack's declared surface. Anyone reading the two
files together needs that sentence, which is why it is here rather than left as
a coincidence of vocabulary.

**One ceiling the surface carries.** S3 measured that `eslint-plugin-jsx-a11y`
6.10.2's peer range holds the whole profile at ESLint 9 — `review.bench.md`
§ The scaffolds. That is not a config-surface decision and it is not settled
here; it is named because the surface is where it will be felt, and dropping the
accessibility group to reach a supported ESLint is a real option with a measured
price.

### The type checker, which S3 said the profile was missing

S3's C6 could not settle `python.no-any`'s strict variant and recorded the prior
question: **the candidate configuration configures no type checker at all**,
while the register cites mypy for two rows. It handed that to S4 as *a strictness
axis cannot be defined before the tool that would carry it.*

The tool was already there. TYP-001 gates mypy for Python and `tsc` for
TypeScript, and `stacks:` names `strict_key: strict` for both — so a conformant
repository of either stack **already runs its type checker in strict mode**
before Craft arrives. Reading the three register rows against that:

| Row | Instrument | Already required by TYP-001 |
| --- | --- | --- |
| `python.annotate-public-api` | mypy `disallow_untyped_defs` | **Yes.** `--strict` enables it, one of the thirteen flags it turns on |
| `react.strict-type-checking` | the `tsconfig` strict family | **Yes.** That is `strict_key: strict`, read from `compilerOptions` |
| `python.no-any` | mypy `disallow_any_explicit` | **No.** Not in `--strict`; verified against the pinned mypy |

```bash
$ uv run mypy --help   # --strict enables the following flags: …
--disallow-any-generics, --disallow-subclassing-any, --disallow-untyped-calls,
--disallow-untyped-defs, --disallow-incomplete-defs, --check-untyped-defs,
--disallow-untyped-decorators, --warn-redundant-casts, --warn-unused-ignores,
--warn-return-any, --no-implicit-reexport, --strict-equality, --extra-checks
```

**So Craft's entire type-checking contribution, across both stacks, is one mypy
key.** Two of the three rows are conformance the repository already owes, and
writing them into a Craft profile would be Craft claiming credit for gates the
register already runs — the same exclusion `assess.rules.md` applies to the four
rows carrying a control ID.

That reframes what S3 asked. The Python profile was not missing a type checker;
it was missing the one key TYP-001's strict mode does not give, which is exactly
the strict-profile variant C6 deferred. **The strictness axis now has somewhere
concrete to live for Python:** `[tool.mypy]` keys above `strict`. Whether
`disallow_any_explicit` is what a level should turn on is the strictness
section's, not this one's — C5 measured that its narrow cousin `ANN401` already
fires on a legitimate `repr` helper, and the wide key would flag every
`dict[str, Any]` a JSON boundary needs.

**The boundary question this raised, and how it was answered.** Writing into
`[tool.mypy]` at all is a boundary question — that section is TYP-001's gated
configuration, and a Craft profile editing it is a craft rule touching a
control's surface without crossing ADR 0051's route. It turned out not to be
about mypy: a craft rule installed into *any* mandated tool blocks a merge under
a control's name while appearing in neither register, which is already true of
every ruff selector this profile writes. `[tool.mypy]` is only where it became
visible, because that section has a control reading its contents.
[ADR 0055](../adr/0055-craft-writes-into-a-gated-section.md) settles it:
**Craft may write into a gated section, may never write a key that control
asserts, and records every key it writes.** `disallow_any_explicit` is not a key
TYP-001 asserts, so a Python strictness level may set it.

### What pins the tool version

S3's third hand-forward: *the profile pins no tool version in anything it
materialises*, and *an installed profile whose posture is a pinned binary
reading a pinned config cannot ship a rule selection without the version it was
selected against.*

The premise is right and the remedy it implies is wrong, and `controls.yaml`
shows why. Nothing in `stacks:` names a version either. Ruff's version comes
from the `uv.lock` that `uv run ruff check` resolves; ESLint's from
`package-lock.json`; and SUP-001 is the control that makes the lockfile
authoritative by requiring a frozen install. **The lockfile is the pin**, and a
version written into `ruff.toml` would be a second copy of it — the same mistake
`CLAUDE.md` records for `.python-version`, `requires-python` and
`[tool.ruff] target-version`, which is why that key is deliberately absent here
too. S3's own C1 confirmed ruff still derives the floor without it.

**Two different things wear the word *version* here, and separating them
dissolves the problem:**

- **The version that runs** is the lockfile's, pinned by SUP-001, and the
  profile must not restate it.
- **The version a selection was made against** is provenance — the answer to
  *was this rule set chosen against the ruff we are running?* That is real, it
  is what S3 was reaching for, and it belongs with the profile's own record
  rather than in the tool's configuration file.

The second has a shape this repository already uses: a **provenance stamp**, per
[ADR 0038](../adr/0038-the-stamp-records-the-deployment-contract.md), which
every gate skill writes and which `register-check deployments` reads to say
whether a deployment is current. A profile is not a gate and this is not that
stamp — but *a record of what a deployment was made against, which goes stale
visibly rather than silently* is exactly the mechanism, and the Craft register
schema is where it lands.
Recorded as owed, with the shape named.

### Does it introduce a new format

**No, and the check is mechanical.** Every file the two tables above name is a
file `controls.yaml` already names, in a format that already exists:

| File | Format | Named by |
| --- | --- | --- |
| `pyproject.toml` §`tool.ruff.lint` | TOML | `stacks.python.gates.lint.config[0]` |
| `pyproject.toml` §`tool.mypy` | TOML | `stacks.python.gates.typecheck.config[0]` |
| `eslint.config.js` | flat config, JavaScript | `stacks.typescript.gates.lint.config[0]` |
| `tsconfig.json` §`compilerOptions` | JSON | `stacks.typescript.gates.typecheck.config[0]` |

The Craft register of ADR 0053 is a new file, and it is not a new *surface*: no
repository's tools read it, the installer does, and what the installer writes is
the four rows above. `plan.md` § S4 asks for "real tool configuration —
generated and pinned. Not a new format, and not a second copy of one." The
generated half holds. The pinned half is the lockfile's, per the section above.

## The strictness levels

ADR 0052 made strictness one of two axes and left what the levels are to this
stage. With archetype gone and codebase age gone, **every question of the form
*should this repository get more or fewer rules* resolves here**, which is that
ADR's own warning about how much weight this section carries.

### The register already drew the line, and this names it

`assess.rules.md`'s **Default** column is a two-valued proposal per row — `on`,
`off`, or `n/a` where nothing can be switched. That is a level boundary already
present in the data, proposed by S2 and measured by S3, and inventing a
different one here would be a second opinion about rows somebody has already
read twice.

| | `on` | `off` | `n/a` |
| --- | --- | --- | --- |
| Python | 42 | 16 | 12 |
| React | 51 | 5 | 10 |
| Stack-neutral | 11 | 17 | 14 |

**So: two levels per stack, nested.** `standard` is the `on` rows. `strict` is
`standard` plus the `off` rows that have an instrument to turn on. A level is a
superset of the one below it, which is what makes *upgrade* and *downgrade*
mean anything.

**`standard` is exactly what S3 benched.** 65 selectors resolving to 141 ruff
rules, 87 ESLint rules named on over two preset bases — every number in
`review.bench.md` describes this level and no other. That is the reason to make
it the base rather than a convenience: it is the only rule set anything has
been run against.

### What `strict` adds, per stack

**Python, eleven properties with a real instrument.** The other five `off` rows
are bucket 2 with nothing to enable — `python.no-duplication` needs a clone
detector, `python.shallow-inheritance` and `python.class-dependency-count` need
a check nobody has written — and one, `python.return-count`, is the register's
`incompatible` row and is never selected at any level.

| Property | Instrument |
| --- | --- |
| `python.no-import-inside-function` | `PLC0415` |
| `python.exception-message-not-a-literal` | `EM101`, `EM102` |
| `python.exception-type-carries-its-message` | `TRY003` |
| `python.no-redundant-assign-before-return` | `RET504` |
| `python.typing-only-imports` | `TC001`–`TC003` |
| `python.no-bind-all-interfaces` | `S104` |
| `python.docstring-presence` | `D100`–`D107` |
| `python.docstring-form` | `D205`, `D401`, `D2xx`, `D4xx` |
| `python.no-untracked-todo` | `TD001`–`TD007`, `FIX001`–`FIX004` |
| `python.nesting-depth` | `PLR1702` — preview |
| `python.class-size` | `PLR0904` — preview |

Plus the one key ADR 0055 cleared: mypy `disallow_any_explicit`, which
`assess.rules.md` marks as this property's strict variant in terms.

**React, one property.** `react.effect-dependencies-exhaustive`, instrumented by
`react-hooks/exhaustive-effect-dependencies`, which the plugin ships `off` and
`react.dev` does not document. The remaining four `off` rows have no instrument
that can simply be enabled: three are bucket 2 with nothing asserting them, and
`react.naming-form` cites `@typescript-eslint/naming-convention`, which needs a
written selector list rather than a flip and is therefore a rule somebody has to
author before a level can contain it.

### Three things fall out, and none of them is comfortable

**1. The Python strict level contains two contradicting pairs, and ruff resolves
them by choosing for you.** Expanding `python.docstring-form`'s citation the
widest way it can be read — `D2xx` and `D4xx` whole — takes the strict addition
from 32 rules to 68, and brings in `D203` against `D211` and `D212` against
`D213`:

```console
$ uv run ruff format --check --config ruff.toml m.py
warning: `incorrect-blank-line-before-class` (D203) and `no-blank-line-before-class`
  (D211) are incompatible. Ignoring `incorrect-blank-line-before-class`.
warning: `multi-line-summary-first-line` (D212) and `multi-line-summary-second-line`
  (D213) are incompatible. Ignoring `multi-line-summary-second-line`.
```

These are the same shape as `python.return-count`, which C3 recorded as the
register's only `incompatible` pair — and C3 could not have found these, because
it ran over `standard` and no `D` code is in it. **Ruff does not fail on them;
it warns and silently drops one**, so a profile shipping the widest reading
ships a docstring convention nobody chose.

**The narrow reading has no conflict at all.** `D205` and `D401` as exact codes
bring in neither pair. So the contradiction is not in the property — it is in
the citation, and it is S3's second hand-forward arriving with a consequence
attached: *a range citation rots and a linter citation over-reaches, and the
register has to choose.* `python.docstring-form` is where choosing wrong costs
something visible.

**2. Nothing has run `strict`.** C1 to C9 measured `standard`. The strict level
has not been assembled, has not been run, has had no contradiction pass and no
probe. That is not a gap this document can close by writing more of itself, and
it has a consequence with teeth: **ADR 0051's third precondition is that S3 has
measured the property**, so no rule that exists only at `strict` is eligible to
become a control, however obviously good it looks. A second bench is owed before
`strict` ships, and `review.bench.md`'s scripts are parameterised on the
selection rather than on the level, so it is a smaller job than the first.

**3. The axis is asymmetric to the point of being suspect.** Python's strict
level adds up to 68 rules; React's adds one. Worse, the two stacks disagree
about where the same property sits:

| Property | Python | React |
| --- | --- | --- |
| `Any` is not used explicitly | mypy `disallow_any_explicit` — **strict only** | `@typescript-eslint/no-explicit-any` — **`standard`**, because `recommended` ships it |
| Unsafe `any` flows are not followed | not asserted | `@typescript-eslint/no-unsafe-*` — **`standard`** |

The same appetite for `Any` lands two levels apart, and the reason is not a
judgement anyone made about Python or React. It is that `typescript-eslint`'s
`recommended` preset happens to carry the rule and mypy's `--strict` happens not
to. **As the register stands, the strictness axis partly measures what each
ecosystem's defaults ship rather than what a team wants**, which is the tool
source speaking as though it were a stack source — `survey.sources.md` finding
9, arriving in the profile model.

This does not refute ADR 0052; two axes are still the model, and nothing here
argues for a third. It says the axis needs a definition that is about the
property rather than about the preset, and that `strict` should mean *the same
appetite in both stacks* even where the two toolchains reach it from different
defaults. Writing that definition is what the Craft register schema has to
support, and it is the strongest argument yet for ADR 0053's register carrying a
level per binding rather than a level per rule.

### No level below `standard`

**There are two levels and the lower one is the floor.** A third, looser level
was considered and is not proposed, for a reason the last slice made concrete:
Craft's rules live in `[tool.ruff.lint] select`, which is LNT-001's gated
configuration at `variance: narrowing-only`. Removing selectors is a change to
that configuration in the loosening direction, so a level *below* the benched
base would ship a loosening as a supported option.

That does not make a downgrade impossible — a repository can move from `strict`
to `standard`, and that is the same loosening. What the model says is that
**Craft never performs one silently**: the installer reports a level change that
removes rules as what it is, and the justification is the repository's. This is
the question ADR 0055 named as unanswered in its consequences, and it is
answered for level changes specifically rather than in general — a hand-edited
`select` list is still outside anything Craft can see.

`react.explicit-return-types`' scope is the one dial that looks like a third
level and is not. C6 set it to `src/**/*.ts` and not `*.tsx` because the
unscoped rule fired on all three of C5's components. Widening it is available
and it belongs to `strict` if it belongs anywhere, not to a level of its own.

### What this section does not settle

- **Profile naming and versioning.** `standard` and `strict` are level names
  within a stack; what a whole profile is called and how it is versioned is the
  next slice's, with ADR 0052's pinning paragraph as the constraint.
- **Whether `strict` ships at all.** It is unbenched, and finding 2 says what
  that costs. Shipping one level is a defensible outcome of the second bench.
- **The 17 stack-neutral `off` rows.** They gate on evidence rather than on a
  level (ADR 0052), so they are the evidence-gate slice's and not this one's.

## What this document still owes

Named now so that a reader can tell a gap from an omission, and so that a later
slice cannot quietly drop one.

Two rows have left this table since it was first written — the `[tool.mypy]`
question, answered by ADR 0055, and the strictness levels — and one has joined
it, because § The strictness levels found that nothing has run the level it
proposes.

| Owed | Which box in `todo.md` |
| --- | --- |
| Profile naming and versioning, and what a consumer pins — the levels themselves are settled above | Specify the profile: its axes, its naming, its versioning |
| A second bench, over `strict`. Until it runs, no strict-only rule can ever become a control — ADR 0051's third precondition | Raised by § The strictness levels |
| What happens when a profile changes under a repository that installed it — including whether **removing** a rule from a level is a loosening under LNT-001's `variance: narrowing-only` | Specify what happens when a profile changes |
| The Craft register's schema, and its answer to ADR 0053's unresolved question about `assess.rules.md` | Write `design.profiles.md` |
| Which artefact gates each `any.` group, and where the installer records what it switched on | ADR 0052's evidence-gate consequence |
| S3's remaining hand-forwards: one instrument per property, and the range-versus-linter citation the register has to choose between | `review.bench.md` § What S3 hands forward, items 1 and 2 |

`plan.md`'s exit criterion for S4 is *every ADR it names is Accepted*. All five
are — the four taken ahead of the stage, and ADR 0055, which this document's
first section produced. That does not finish S4: the deliverable is this
document, and it is two sections long.
