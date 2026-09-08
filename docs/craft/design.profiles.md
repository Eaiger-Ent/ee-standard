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

**Corrected by § Naming, versioning, and what a re-run does**: *reports it* is
too permissive. A loosening of a `narrowing-only` control is a violation rather
than a disclosure, so the installer refuses the write instead of narrating it.
The paragraph stands as written because a correction is worth more than a
deletion, and the floor it argues for is unchanged.

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

## The Craft register's schema

[ADR 0053](../adr/0053-the-craft-mapping-is-register-data.md) put the enforceable
mapping in data, in a register of its own, and left the schema to this stage. It
also left one question open in terms: whether that register is generated from
`assess.rules.md`, replaces it, or is written fresh — *the two must not both be
maintained as sources*. Both halves are settled here.

The schema has four jobs. It has to say what a property binds to, which level
that binding sits at, what evidence switches it on, and where the citation
points — and it has to make the two mistakes S3 measured impossible to spell
rather than merely discouraged.

### One instrument per property, and alternatives recorded as alternatives

S3's first hand-forward: *a property that cites two instruments is a double
report waiting to happen.* The measured case is C4's —
`react-hooks/static-components` and `@eslint-react/no-nested-component-definitions`
are one property under two names, they both fired on one defect, and **no
name-keyed conflict configuration could ever have separated them** because the
names do not match.

So a property has exactly one `instrument`. Anything else that could carry it
goes in `alternatives`, which is documentation and is never emitted:

```yaml
react.no-nested-component-definitions:
  instrument:
    tool: eslint
    rule: react-hooks/static-components
  alternatives:
    - rule: "@eslint-react/no-nested-component-definitions"
      why: >
        One property under two names. C4 measured the double report and demoted
        this one; `react-hooks` owns the overlap per C1.
```

The `why` is not decoration. An alternative with no reason is a rule somebody
will re-enable, and the reason is the thing that stops them.

### An instrument is a closed set or a linter, and never a range

S3's second hand-forward said the register has to choose between a range
citation and a linter citation, and that the two findings pulled in opposite
directions. They do — and the strictness slice showed the choice is not between
those two at all, because **a range is the worst of both**.

| Spelling | What went wrong, measured |
| --- | --- |
| Range — `DTZ001`–`DTZ012` | **Rots.** Missed `DTZ901`, which asserts the same property. Same for `PTH100`–`PTH210` missing `PTH211`, and `N801`–`N818` missing `N999` |
| Range read widely — `D2xx`, `D4xx` | **Over-reaches into contradiction.** Brings in `D203` against `D211` and `D212` against `D213`; ruff warns and silently drops one of each |
| Linter — `PL` under `preview = true` | **Over-reaches into cost.** C8: a linter selector picks up preview rules wholesale, where exact codes pick up none |

So the schema admits exactly two spellings and no third:

```yaml
python.timezone-aware-datetimes:
  instrument:
    tool: ruff
    linter: flake8-datetimez        # an OPEN set: whatever this linter holds
    coextensive: >
      All ten of its rules assert the property and any rule it adds would too —
      it exists for exactly this. Verified preview-free at 0.16.5.

python.docstring-form:
  instrument:
    tool: ruff
    codes: [D205, D401]             # a CLOSED set: these, and nothing else
```

**The test for `linter:` is coextensiveness, and it is a real test rather than a
preference:** *would every rule this linter could contain be an assertion of
this property?* Read against the pinned taxonomy, the two answers are not close:

| Linter | Rules | Preview | Coextensive with the property? |
| --- | --- | --- | --- |
| `flake8-datetimez` | 10 | 0 | **Yes.** Every rule is a naive-datetime call |
| `flake8-use-pathlib` | 35 | 0 | **Yes** |
| `pep8-naming` | 16 | 0 | **Yes** |
| `flake8-comprehensions` | 19 | 0 | **Yes** |
| `pydocstyle` | 48 | 2 | **No.** It carries *both sides* of two conventions — a property cannot assert `D203` and `D211` |

That is the whole of the finding: the four linters `standard` spells as linters
pass the test, and the one the strict level would have spelled as a range fails
it. `python.docstring-form` is `codes:`, and the contradiction never arises.

**`coextensive:` is required whenever `linter:` is used**, and its absence is a
schema error rather than a default. A linter citation is a standing bet that the
tool will only ever add rules asserting your property; a bet nobody wrote down is
one nobody will re-check.

### The rest of the fields

```yaml
meta:
  craft_contract: 1

levels: [standard, strict]          # ordered; each a superset of the one below

sources:                            # ADR 0054: cite every source, copy none
  ruff:
    title: ruff's rule taxonomy
    url: https://docs.astral.sh/ruff/rules/
    licence: MIT

properties:
  python.no-any:
    asserts: "`Any` does not appear in a public signature"
    bucket: 1
    sources: [typescript]           # keys into `sources:` above
    instrument: {tool: ruff, codes: [ANN401]}
    level: standard
  python.no-any-anywhere:
    asserts: "`Any` does not appear at all"
    bucket: 1
    sources: [typescript]
    instrument: {tool: mypy, setting: disallow_any_explicit, value: true}
    level: strict

  python.line-length:
    settings: {line-length: 88}     # C6's numbers live with their property
    level: standard

  any.api-response-shape:
    gated_on: openapi-document      # ADR 0052's evidence gate
    level: standard
```

Four things about that shape are decisions rather than notation.

**`level` sits on the binding, not on the property.** The strictness slice found
the same appetite for `Any` landing two levels apart across the stacks because
of what each toolchain's defaults ship. Keying the level to the binding is what
lets a property say *`standard` in React and `strict` in Python* without minting
two identities, and it is the schema change that finding asked for.

**`sources:` is in the register, not only in `survey.sources.md`.** ADR 0054
requires every rule to cite its source, and a citation key that resolves only
into prose is not a citation anything can emit. The installer has to be able to
hand a team the source behind a rule, which means the source register is data
too.

**No file location appears anywhere.** [ADR
0055](../adr/0055-craft-writes-into-a-gated-section.md) settled that the surface
comes from `controls.yaml`'s `stacks:`, so a `file:` key here would be the second
copy that ADR exists to prevent. The Craft register names the **tool and the
keys**; the control register names **where they go**.

**No tool version appears either**, for the reason § What pins the tool version
gives: the lockfile is the pin. What the register does carry is the taxonomy
version a binding was *read against*, as provenance — which is a different
question and goes stale visibly.

### What may live in Craft's Python, and why each is allowed

ADR 0053 permits the checker-class of rule — properties of the format, not of
any repository — and **requires each to carry its reason where it is written**.
Four, on ADR 0018's test: *could a reasonable Equal Experts repository need this
to differ without changing the code?*

| Rule | Why it is format, not data |
| --- | --- |
| The identity grammar — lowercase, dotted, one of three scopes | `plan.md`'s naming standard is a property of Craft's vocabulary. A repository wanting `Python.FunctionLength` is not a repository with a different need |
| Levels are ordered and nested | The relation *is* the model ADR 0052 chose. A register that could declare them unordered would be declaring a different model |
| The instrument shapes are a closed set — `codes`, `linter`, `rule`, `setting` | A fifth shape is a change to what an instrument means, which no repository varies |
| `linter:` requires `coextensive:` | The measured rule above. A repository that wanted to omit it would be a repository wanting the `D203`/`D211` failure |

And what may **not**: which linter is coextensive, which codes a property binds,
which level a binding sits at, every threshold, and every evidence artefact.
Those are the ordinary case ADR 0053 sent to data.

### `assess.rules.md` becomes a stage record, and stops being a source

ADR 0053's open question, answered: **the register replaces it.** Not generated
from it — a markdown table is not a schema, and a parser over one is a second
copy with a regex in the middle. Not written alongside it either, which that ADR
forbids outright.

`assess.rules.md` keeps its 182 rows and becomes what `survey.sources.md` and
`review.bench.md` already are: **the record of a stage**, dated, describing how
the classification was reached and what it found. Its counts stay true of
2026-09-06 and stop being true of the register the moment either moves, which is
what a stage record is for. `survey.sources.md` goes the same way for the same
reason, since its rows become the `sources:` block above.

The freeze needs one check rather than a promise. **Every identity in
`assess.rules.md` must exist in the Craft register** — a superset test, cheap to
write, and it fails exactly when somebody adds a property to the prose and
forgets the data. It does not check the reverse, because the register is allowed
to grow past the stage that started it. S5 owns it.

### What this section does not settle

- **The Craft register's own validation.** ADR 0053 says `register-check` has no
  business reading this file and that what validates it is the implementing
  work's to build. This names the schema, not the checker.
- **Whether `craft_contract` gates anything.** `controls.yaml`'s
  `register_contract` exists because skills read it to detect a stale
  deployment. Whether Craft needs the same mechanism depends on the installer,
  which is S5's.
- **The migration.** Nothing here writes the 182 rows. Turning the prose into
  data is work, and it belongs with the installer that reads it.

## The evidence gates

ADR 0052 removed the archetype axis by grouping the 42 stack-neutral properties
by the artefact they read, switching each group on when that artefact is
present, so that a repository declares nothing. It named one consequence as
binding: **the installer must report which groups it switched on and which
artefact switched them**, because a gate nobody can see is the invisible
suppression that ADR rejected the declared archetype for.

This section says what the groups are, what gates each, and where the record
goes. It also reports that the model fits fewer of the rows than the ADR assumed
— which is a finding about the other rows rather than about the model.

### The 42 rows do not all group by an artefact

Read against `assess.rules.md`'s stack-neutral section, keyed on what each row's
Instrument column actually names:

| Group | Rows | Gated by an artefact? |
| --- | --- | --- |
| `spectral` over an OpenAPI document | 11 | **Yes** — the ADR's own example |
| An infrastructure analyser over Terraform | 4 | **Yes** |
| `commitlint` over commit messages | 3 | **No.** Every repository has commits |
| A GitHub ruleset or repository setting | 5 | **No.** Platform state, not a file |
| Already a control — SEC-001/002, CI-001, SUP-002 | 4 | n/a, and excluded from the shares |
| Bucket 3, no instrument at all | 10 | Nothing to gate |
| Bucket 2, no instrument yet | 5 | Nothing to gate |

**Fifteen of the forty-two gate on an artefact the way ADR 0052 describes.** The
model is right about those and it was never wrong — it was stated over the whole
`any.` scope when the evidence supports it over two groups. The other four
groups need answers of their own, and three of them turn out to be answers about
scope rather than about gating.

**ADR 0052 has since been amended to say so** — revision 3, 2026-09-07, which
narrows its Decision to the groups that read an artefact and removes a count of
`spectral` rows that was wrong when written. The decision it records is
unchanged, and this section is the reading that found it.

### The gate is a register predicate, not a new mechanism

`controls.yaml` already carries the thing this needs:

```yaml
predicates:
  always: true
  python: pyproject.toml exists
  typescript: tsconfig.json exists
  container: any Dockerfile exists
  terraform: any *.tf file exists
  github-actions: .github/workflows/ exists
  devcontainer: .devcontainer/devcontainer.json exists
```

That is a named set of *does this artefact exist* tests, read by
`_applicable_gates` to decide which controls apply to a repository. IAC-001's
`applies_to: [terraform]` is the infrastructure group's gate already written,
already read, and already true of the same repository at the same moment.

**So a Craft group names a predicate rather than describing one.**

```yaml
any.https-everywhere:
  gated_on: terraform          # resolves in controls.yaml
```

Predicates resolve from `controls.yaml` first and from the Craft register's own
`predicates:` block second, and **a name defined in both is a schema error**.
That is the same move the schema slice made with `coextensive:` — duplication
made illegal rather than discouraged, because two definitions of *is there
Terraform here* would eventually disagree about a repository and nobody would
know which one the profile used.

**The OpenAPI predicate does not exist and belongs in the Craft register**, not
in `controls.yaml`. No control gates on it, and adding a predicate to the control
register purely for Craft's benefit is the direction ADR 0053 sent Craft data
away from:

```yaml
predicates:
  openapi-document: any file with a top-level `openapi` key exists
```

**Keyed on the document's own declaration, not on its name.** `openapi.yaml`,
`api/spec.yaml` and `docs/openapi/v1.json` are all real conventions and a glob
over them would both miss and over-match — a `spectral` run finds nothing in a
file that does not declare itself, and finds plenty in one that does whatever it
is called. This is ADR 0052's own requirement applied literally: the gate reads
the same fact the rule needs to run at all, so the two cannot disagree.

### The commit group has no artefact, and its gate is a cost

Three rows — `any.conventional-commits`, `any.commit-subject-length`,
`any.commit-references-work-item` — are instrumented by `commitlint`, and every
repository has commit messages for it to read. There is no artefact whose
absence makes the property inapplicable, so **there is nothing here to gate on
and the group is simply on**.

What there is instead is a cost the register has a word for. `commitlint` is a
Node package, so a Python repository with no `package.json` acquires a Node
toolchain and a second lockfile to check its commit messages — which is a real
objection a Python team would be right to make, and it is not a gate, because
gating on `package.json` would mean a Python repository never gets commit
conventions for a reason that has nothing to do with commit conventions.

**No Python-ecosystem instrument for this group is registered.** That is survey
work, and the schema slice already settled how it arrives: `sources:` is register
data now, so a new source is added there and `survey.sources.md` stays the record
of the original sweep rather than a document anybody edits. Until one is
registered the group is Node-only, and an installer that would drag a toolchain
into a repository to satisfy it should say so and let the team decline —
which is a report, not a gate.

### The platform group is not a profile's to write

Five rows name a GitHub ruleset or a repository setting: `any.branch-naming`,
`any.linear-merged-history`, `any.signed-commits`, `any.semver-release-tags` and
`any.delete-merged-branches`. None of them is configuration in a file a profile
writes, and reading CI-001 against them splits them three ways — none of which
ends in a Craft profile:

- **`linear-merged-history` and `signed-commits`** are default-branch
  properties, and could be added to the ruleset `gate-repo` records:
  `_ruleset_problems` checks that the recording *falls short* of nothing the
  register requires, so an extra rule is a narrowing it permits. But that file
  carries `gate-repo`'s provenance stamp, and a second writer to a gate's own
  recorded artefact is a worse version of the problem ADR 0055 solved for
  `pyproject.toml` — there the control asserted three keys; here the file *is*
  the control's deployment.
- **`branch-naming` and `semver-release-tags`** cannot go in that file at all.
  `ruleset_recorded_matches_register` fails a ruleset whose conditions target
  anything but `~DEFAULT_BRANCH`, and these two target feature branches and
  tags. They need a ruleset of their own, which is a second ruleset for a
  repository to reconcile.
- **`delete-merged-branches`** is a repository setting rather than a ruleset rule
  — a different API call again.

All three are platform state applied through the GitHub API after an explicit
confirmation, which is what `gate-repo` does and what a profile writing
configuration files does not. **So the platform group is out of scope for a
Craft profile**, and those five properties are the clearest candidates in the
register for ADR 0051's crossing route: become controls, deployed by the gate
that already owns that surface. `any.dependency-vulnerability-scanning` is
already named there by that ADR, and this is four more of the same shape.

### The fifteen rows with nothing to gate

Ten bucket-3 properties have no instrument by their own classification —
`any.authorise-separately-from-authenticate`, `any.validate-at-boundaries`,
`any.threat-modelling` and seven others — and five bucket-2 rows have none yet.
They are not gated because there is nothing to switch on. They are the
judgment-only residue `plan.md` § S5 says the installer hands back as prose an
assistant loads, **labelled unenforced**, and the label is the whole of what
makes them honest.

### What the installer records, and where

ADR 0052 requires the record and ADR 0055 settled its shape. The stamp carries,
per group: the predicate consulted, what it matched, and the resulting state.

```text
# ee-craft: python/standard@1  gates: terraform=no(0 *.tf) openapi-document=yes(api/openapi.yaml) commit=on
```

Two properties of that line are the point of it.

**It names the artefact, not just the answer.** *The API group is off* is not
reviewable; *the API group is off because no file declares a top-level `openapi`
key* is, and it tells a reader exactly what to add to change it.

**It goes stale visibly rather than silently.** ADR 0052 names the transition it
worries about: writing a first OpenAPI document enables eleven rules on a
codebase never checked against them, and it *will* feel like a regression at the
worst moment. The stamp is what makes that legible — it records the answer as of
the install, so a reader can see that the profile was installed before the
document existed, and a re-run is what turns the group on. Nothing switches on
under a repository that is not looking, which is the same guarantee ADR 0052
gives for the profile version.

### What this section does not settle

- **How the fifteen ungated rows are worded as prose.** The residue is S5's
  deliverable, and *labelled unenforced* is a requirement rather than a wording.
- ~~**Whether the five platform properties become controls.**~~ Closed by
  § Where the register lives, and what checks it: **they do not, here.** They are
  recorded in `any.yaml` with `out_of_scope: profile` and the reason in place of
  an instrument. ADR 0051's route stays open and nobody walks it now.
- **The Node-toolchain question for the commit group.** It needs a registered
  Python-ecosystem instrument, and registering one is survey work.

## Naming, versioning, and what a re-run does

The last design question. ADR 0052 settled that a profile is versioned and
pinned by the consumer in the shape `.claude/skill-config.yaml` already uses,
that an installed repository keeps the version it pinned until someone re-runs
the installer, and that the installer reports what moved. What it did not settle
is what a version *is*, and this section found that the obvious answer is wrong
in a way worth writing down.

### A profile is named by its two axes and nothing else

`python/standard`, `python/strict`, `react/standard`, `react/strict`. Stack and
level, per ADR 0052, with the levels § The strictness levels named. There is no
third component because there is no third axis, and a name with room in it for
one is an invitation.

### The version is a counter, because semver would point the wrong way

The obvious answer is semver, and it is wrong here. Semver's major position
means *this will break you*, and for a lint profile the change that breaks a
consumer is the one semver would call minor:

| Change | What it does to a consumer's build | Semver would say | What the register cares about |
| --- | --- | --- | --- |
| A rule is added | **Fails on code that passed yesterday** | minor — a compatible addition | narrowing, which `narrowing-only` permits |
| A rule is removed | Passes more than it did | major — a removal | **loosening**, which is the governance event |

**The two notions of significance point in opposite directions**, and one number
cannot carry both without misleading somebody. A consumer reading `2.0.0` would
brace for a build full of findings and get a quieter one; a reviewer reading
`1.3.0` would relax at the version that just removed a rule.

So a profile version is a **monotonic integer** — `python/standard@7` — and the
direction of each change is recorded separately and explicitly, in the
vocabulary this repository already has:

```yaml
python/standard:
  version: 7
  changes:
    - version: 7
      moved: narrowing        # narrowing | loosening | neither
      what: "python.no-import-inside-function added — PLC0415"
```

**`narrowing`, `loosening` and `neither` are `register-variance`'s three
answers**, not three new words, and its rule comes with them unchanged: *a mixed
delta is a loosening*. A version that adds two rules and drops one is a
loosening, and the profile does not get to average them out any more than a
repository does.

The counter is what makes *what moved between the pinned version and the current
one* answerable as ADR 0052 requires: the installer reads the entries between
the two numbers and reports them, rather than inferring severity from a position
in a version string.

### What a consumer pins

Per ADR 0042, keyed by the skill name, read verbatim, and reported as coming
from the file:

```yaml
# .claude/skill-config.yaml
craft-install:
  profile: python/standard
  version: 7
```

**Absent file, absent key, absent value is not a default here**, which is the one
place Craft departs from ADR 0042's part 3. That part says an absent value gets
today's behaviour, and for `lint-md` there is a sensible default to fall back on.
There is no sensible default level: a profile is a decision about how much a team
wants to be told, and guessing it is the declared-archetype failure ADR 0052
rejected wearing different clothes. With no pin, the installer infers the stack,
presents the levels with what each costs, and takes an explicit yes — which is
what `plan.md` § S5 already requires of it.

### `craft_contract` is needed, and it is not the profile version

The schema slice proposed `meta.craft_contract` and left whether it gates
anything to here. It does, for the same reason `controls.yaml` carries
`register_contract`: **the installer is versioned and pinned by a consumer**, so
a repository can hold an installer from six months ago and read a register
written last week. A field that installer does not understand is one it will
either ignore or mis-apply, and ignoring a field silently is how a rule stops
being installed without anybody noticing.

**The two numbers move for different reasons and must not be one number.**

| | Moves when | Read by |
| --- | --- | --- |
| `craft_contract` | The **schema** changes — a new field, a new instrument shape | The installer, to refuse a register it cannot read |
| A profile's `version` | The **rules** change — a binding added, a threshold moved | The installer, to report what moved to a consumer |

Conflating them would make every rule change look like a format change, which
is the failure `register_contract` avoids by moving only when a skill reading
the register must understand something new.

### What a re-run does, and the three things it compares

ADR 0052 guarantees that nothing changes under a repository that is not looking.
A re-run is the moment of looking, and there are three deltas to report — not
one, which is the part worth designing rather than discovering:

1. **The pinned version against the current one.** The `changes` entries
   between them, each with its direction. This is ADR 0052's requirement.
2. **The stamp against the file as it stands.** ADR 0055 rule 2's stamp records
   what Craft wrote; comparing it to what is there now detects **hand edits made
   since**. A re-run that silently overwrote a team's deliberate change would be
   worse than one that refused, and without the stamp it could not tell the
   difference.
3. **The evidence gates now against the gates at install.** This is ADR 0052's
   named worst moment — writing a first OpenAPI document turns on a group of
   rules against code never checked against them. The gate line in the stamp is
   what makes it a reported change rather than a surprise.

### The installer never writes a loosening, and an earlier sentence was wrong

§ The strictness levels said a downgrade from `strict` to `standard` stays
possible and *the installer reports it as the loosening it is*. **That is too
permissive and this section corrects it.**

Craft's rules live in LNT-001's gated configuration, and LNT-001 is
`variance: narrowing-only`. A change that removes selectors is a loosening of a
narrowing-only control, which is a **violation** — `register-variance` exits `1`
on it and `register-check` fails on the next run. An installer that performed
that write would be knowingly leaving a repository non-conformant, and reporting
it honestly on the way out does not make it defensible.

**So the installer will not write it.** A team that wants a lower level makes
that change themselves and answers for it in the way the register already
provides for — which is the same shape as ADR 0055's rule 1, where Craft cannot
weaken a control, applied to the level mechanism rather than to a key.

What the installer does instead is say so: *`python/strict@4` is pinned;
`python/standard` would remove nineteen rules, which is a loosening of LNT-001
and not mine to write.* That is a more useful sentence than a silent success,
and it is the only one that leaves the repository conformant.

The floor from § The strictness levels is unchanged and this is why it exists:
with `standard` as the lowest level, the only downgrade available is one the
installer refuses, so the ordinary case never reaches this rule at all.

### What this section does not settle

- ~~**Where the profile's `changes` entries live.**~~ Closed by § Where the
  register lives, and what checks it: `profiles:` in `craft/meta.yaml`, keyed by
  `<stack>/<level>`, because a profile spans the per-scope files and entries
  kept per-file would split one profile's history across two.
- **Whether an installer may refuse to run at all** on a repository whose stamp
  shows hand edits, or only report them. That is an installer behaviour and S5's.

## Where the register lives, and what checks it

[ADR 0053](../adr/0053-the-craft-mapping-is-register-data.md) put the mapping in
data and left this stage the schema; § The Craft register's schema answered what
a row looks like. Three things it did not answer are answered here: **which
files**, **where a profile's `changes` entries sit**, and **what validates any of
it**, given that ADR 0053 rules out the checker this repository already has.

### `craft/`, one file per scope

```text
ee-standard/
├─ controls.yaml          # the control register
└─ craft/
   ├─ meta.yaml           # craft_contract, levels, sources, profiles
   ├─ python.yaml
   ├─ react.yaml
   └─ any.yaml
```

**Not under `docs/`.** A register is data a machine reads, and ADR 0053's whole
finding is that the mapping stops being documentation the moment something
enforces it. A path that says `docs/` invites the next reader to treat a wrong
row as a typo rather than a defect, which is what `assess.rules.md` has been.

**Not in `controls.yaml`, and not a section of it.** The two registers assert
different kinds of thing, and ADR 0051 exists precisely because crossing from
one to the other is an event. A Craft property living in the control register
would have crossed by filing.

**One file per scope, rather than one file.** The naming standard already says a
property's identity carries its scope — `python.`, `react.`, `any.` — so the
file a row belongs in is *derivable from its own name*, and a row in the wrong
file is a schema error something can state rather than a matter of taste. That
is the same move the schema slice made twice: make the mistake unspellable
rather than discouraged. The cost is that a schema rule now has to hold in four
places instead of one, which is what the validation below is for.

`any.yaml` is a file and not a fallback. The forty-two stack-neutral rows are
the ones ADR 0052 gates on evidence, and keeping them together is what makes
*which gates did this repository switch on* a question about one file.

### A profile's `changes` entries go in `meta.yaml`

§ Naming, versioning, and what a re-run does left this as *a field, not a
decision*. The field is `profiles:` in `meta.yaml`, keyed by `<stack>/<level>`:

```yaml
craft_contract: 1

levels: [standard, strict]

profiles:
  python/standard:
    version: 7
    changes:
      - version: 7
        moved: narrowing          # narrowing | loosening | neither
        what: "python.no-import-inside-function added — PLC0415"
```

**It cannot go in the per-scope files**, and the reason is the one thing that
made this worth a paragraph: a profile spans them. `python/standard` binds every
`python.` row at that level **and** every `any.` row whose evidence gate is open,
so its version moves when either file moves. Entries kept per-file would split
one profile's history across two, and the installer's *what changed between the
pinned version and the current one* would have to reassemble it — a second copy
of a history, which is theme T-2 by the most ordinary route available.

### What checks it — a test, not a second checker

ADR 0053 says `register-check` must not. Two reasons, and the second is the one
that generalises: the checker is the **control** register's, so a Craft register
inside it would make Craft look like a control by inspection; and ADR 0018's
boundary lets the checker hold a rule only when the rule is a property of *the
register format*, which the Craft format is not.

**A `craft-check` CLI was considered and is not taken.** It would be symmetrical
with `register-check` and wrong for the same reason a symmetry usually is: a
second checker to keep current, a second thing in CI, and a second thing an
adopter would have to run — for a register **only this repository holds**. An
adopter never reads `craft/`; they read the profile the installer wrote. The
thing an adopter runs is the installer, and it validates what it loads.

So the register is checked by **`tests/test_craft_register.py`**, in this
repository's own pytest suite. It rides the existing gate, it fails a commit
rather than a build, and it has a precedent: `tests/test_posture.py` already
fails the build if a *document* stops saying something. A register is a smaller
ask than that.

What it asserts, one test per rule so a failure names the rule rather than the
file:

| Check | Why it is a test and not a convention |
| --- | --- |
| Every identity matches the naming standard's grammar, and **sits in the file its scope names** | The whole reason for four files |
| Exactly one `instrument` per property; anything else is under `alternatives` | S3's first hand-forward; C4 measured the double report |
| An instrument is a **closed set of codes or a `linter:`**, never a range | S3's second; a range rots and, read widely, contradicts |
| `linter:` carries a `coextensive:` reason, and its absence is an error | The schema slice's test, which `pydocstyle` fails and four linters pass |
| `level` is one of `meta.yaml`'s, and `strict` ⊇ `standard` per stack | ADR 0052 defines the levels as nested; a register that says otherwise is wrong, not merely unusual |
| `gated_on` names a predicate defined in **exactly one** of the two registers | The evidence-gate slice: a name defined in both is a schema error |
| Every source cited resolves to a key in `meta.yaml`'s `sources:` | ADR 0054: cite every source |
| **Every `assess.rules.md` row has a property here** | The superset test ADR 0053's open question was closed on |

The last row is the one that stops the migration losing anything, and it is the
reason `assess.rules.md` can become a stage record rather than a second source:
the test, not a promise, is what holds them together. It reads the identities out
of the markdown table — which is exactly as fragile as it sounds, and is the
point: when somebody edits that table and the test breaks, the register is what
they should have edited.

### The platform group: recorded, and nothing minted

§ The evidence gates left open *whether the five platform properties become
controls*. **S4's answer is that they do not, here.** They are out of a
profile's scope for the reason that section gives, and they are recorded in
`any.yaml` with no instrument and the reason in place of one:

```yaml
any.signed-commits:
  asserts: "Commits on the default branch are signed"
  bucket: 2
  out_of_scope: profile
  why: >
    Platform state applied through the GitHub API, not configuration in a file.
    `gate-repo` owns that surface and records its own ruleset with a provenance
    stamp; a profile writing into it would be a second writer to a gate's
    deployment. ADR 0051's crossing route is open and its three preconditions
    still bind — nothing here mints anything.
```

ADR 0051's route stays available and **nobody walks it now**. Minting five
controls to close a documentation row would be the tail wagging the dog: a
control is a thing this repository then owes a gate, a verify block and an
evidence trail for, and none of the five has a stated adopter need behind it.
Recording the verdict costs a field; taking the route costs a register entry
that somebody would have to keep true.

## What this document still owes

Named now so that a reader can tell a gap from an omission, and so that a later
slice cannot quietly drop one.

**Every slice has closed more than it opened, and opened something** — which is
what a design document doing its job looks like from the inside. No count of
that is kept here, because a tally of another list's rows is the shape ADR 0052
revision 3 removed.

What is left is **no longer design.** Both remaining entries are work: the
migration, and one source to register. Everything that was a decision has been
taken.

**Four of the six closed on 2026-09-08**, which is why the table below is
shorter than the one a reader of an earlier revision saw. They are struck rather
than deleted, because a silently removed row is indistinguishable from one that
was never owed.

| Owed | Which box in `todo.md` |
| --- | --- |
| ~~A second bench over `strict`~~ — **done**, [`review.strict.md`](review.strict.md). Every criterion answered, and the two rows it could not settle handed here and taken | Raised by § The strictness levels |
| ~~The Craft register's **validation**~~ — **`tests/test_craft_register.py`**, not a second checker. § Where the register lives, and what checks it | Write `design.profiles.md` |
| ~~Where a profile's `changes` entries live~~ — **`profiles:` in `craft/meta.yaml`**, same section | Raised by § Naming, versioning |
| ~~Whether the five platform properties take ADR 0051's route~~ — **they do not, here.** Recorded with `out_of_scope: profile` and a reason; the route stays open | Raised by § The evidence gates |
| The migration: turning `assess.rules.md`'s 182 rows into register data | Raised by § The Craft register's schema |
| A registered Python-ecosystem instrument for the commit group, so it is not Node-only | Raised by § The evidence gates; survey work under the schema slice's `sources:` |

`plan.md`'s exit criterion for S4 is *every ADR it names is Accepted*. All five
are — the four taken ahead of the stage, and ADR 0055, which this document's
first section produced. **No sixth ADR was needed**, and the box that stayed open
against that possibility can close: the two verdicts the bench handed S4 and the
four decisions above were all taken within the frame the five already set.

That does not finish S4 by itself: the deliverable is this document. It is six
sections long, **no design question is outstanding**, and what remains under the
heading above is work rather than a decision.
