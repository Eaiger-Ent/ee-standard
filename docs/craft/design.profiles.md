# Craft — the design

Stage **S4** of [`plan.md`](plan.md). What gets built, decided before it is
built.

**Four of this stage's decisions were taken ahead of it**, on 2026-09-06, and are
Accepted ADRs: [0051](../adr/0051-a-craft-rule-becomes-a-control-by-being-installed.md)
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

## What the four ADRs left to this stage

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

**What this does not decide.** Whether a Craft profile may write into
`[tool.mypy]` at all is a boundary question: that section is TYP-001's gated
configuration, and a Craft profile editing it is a craft rule touching a
control's surface without crossing ADR 0051's route. The register's
`variance: narrowing-only` says adding a key is permitted; it does not say
whether Craft is the thing that should add it. Recorded as owed.

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

## What this document still owes

Named now so that a reader can tell a gap from an omission, and so that a later
slice cannot quietly drop one.

| Owed | Which box in `todo.md` |
| --- | --- |
| The strictness levels: how many, what each turns on, and what names them | Specify the profile: its axes, its naming, its versioning |
| How a profile is versioned, and what a consumer pins | The same box, and ADR 0052's pinning paragraph |
| What happens when a profile changes under a repository that installed it — including whether **removing** a rule from a level is a loosening under LNT-001's `variance: narrowing-only` | Specify what happens when a profile changes |
| The Craft register's schema, and its answer to ADR 0053's unresolved question about `assess.rules.md` | Write `design.profiles.md` |
| Which artefact gates each `any.` group, and where the installer records what it switched on | ADR 0052's evidence-gate consequence |
| Whether a Craft profile may write into `[tool.mypy]`, which is TYP-001's gated surface | Raised by § The type checker above |
| S3's remaining hand-forwards: one instrument per property, and the range-versus-linter citation the register has to choose between | `review.bench.md` § What S3 hands forward, items 1 and 2 |

`plan.md`'s exit criterion for S4 is *every ADR it names is Accepted*. The four
above are, which does not finish the stage: this document is the deliverable, and
it is one section long.
