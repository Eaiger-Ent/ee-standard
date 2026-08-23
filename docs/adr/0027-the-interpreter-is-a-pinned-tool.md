# ADR 0027: The Interpreter Is a Pinned Tool, and a Toolchain File Is Its Authority

**Status:** Accepted
**Date:** 2026-08-23
**Revision:** 1

## Background

Every tool this register pins is recorded under `tools:` with an authority for
its version, and `tool_versions_match_register` holds each locus to it
([ADR 0018](0018-register-checker-boundary.md),
[ADR 0020](0020-a-locus-reaches-the-pinned-artefact.md)). The Python interpreter
was not one of them. It is the tool every other Python tool runs *inside*, and
it was the only one no locus pinned and nothing compared.

What each locus actually resolved, measured rather than read off a file:

```text
devcontainer   Python 3.13.15   the python feature's `version: "3.13"`
ci             Python 3.14.7    nothing pinned; uv chose
```

The CI figure is from run 32635719603 on 2026-08-23, the most recent conformance
run on `main`:

```text
Downloading cpython-3.14.7-linux-x86_64-gnu (34.2MiB)
Using CPython 3.14.7
platform linux -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0
```

`standard-check.yml` has no `setup-python` step and no `.python-version` to
read. It installs uv and runs `uv sync --frozen`, and uv resolves an interpreter
against the only constraint in the repository — `requires-python = ">=3.13"` in
`pyproject.toml`. That is a floor, so the answer depends on what the machine
already has:

```text
here      3.13.15 is installed and satisfies the floor   uv uses it
runner    no installed interpreter satisfies the floor   uv downloads the newest that does
```

Neither locus is misconfigured. The same three files produce two different
interpreters because a floor selects nothing, and a floor was the only
constraint written down. So the gate that decides conformance ran on an
interpreter no file in the repository names, and would silently move to 3.15
the week it ships.

The cost is not hypothetical. `ruff`'s `target-version = "py313"` lints for the
syntax and deprecations of 3.13 while CI executes 3.14, so the linter's model of
the language and the interpreter running the tests disagree by a minor version.
A 3.14 behaviour change reaches `main` through a green run, and the
devcontainer — where it would be diagnosed — cannot reproduce it.

This is the duplication this repository exists to prevent, in its least visible
form. There was no second copy of the version to spot: there was **no** copy,
and two loci filled the gap independently.

## The two facts a single "3.13" was standing for

`3.13` appeared in three places, and they do not mean the same thing.

| Where | What it constrains |
| --- | --- |
| `requires-python = ">=3.13"` | Which interpreters this **package** claims to work on |
| the devcontainer python feature | Which interpreter **bootstraps** the container |
| whatever uv resolved | Which interpreter **runs the gates and the tests** |

Only the third is a locus property that must be identical everywhere. The first
is a support claim published in wheel metadata: narrowing it to `==3.13.*` to
force the environment would tell an adopter installing `standard-check` that it
does not work on 3.14, which is false and would be a lie told to make a local
gate deterministic. The second is bootstrap — `setup.sh` runs
`pip install uv==0.12.5` with the system interpreter, and `.claude/hooks/md-lint.py`
is `#!/usr/bin/env python3`; neither cares which minor answers, and neither runs
a gate.

Conflating them is what made the gap invisible. The register needs a name for
the third fact alone.

## Alternatives Considered

### Option 1: Narrow `requires-python` to a single minor

Write `requires-python = "==3.13.*"` and let uv resolve from it.

**Pros:** One line, no new file, and it does pin: measured, `uv venv` with
`==3.13.*` and no other constraint selects 3.13.15 rather than downloading
3.14.7.
**Cons:** It overloads package metadata with environment selection. The field is
published in the wheel and read by every installer, so this repository's choice
of development interpreter would become a declared incompatibility for every
adopter — and adopters are the point of the artefact. It also fails in the
direction that matters: the day the environment moves to 3.14, support for 3.13
would have to be dropped in the same commit, for no reason connected to the
code.

### Option 2: Pin the interpreter at each locus and reconcile the copies

Record `python` as a `source: literal` tool with
`pinned_at: [.devcontainer/devcontainer.json, .github/workflows/standard-check.yml]`,
add a `setup-python` step to CI, and let `tool_versions_match_register` compare
them.

**Pros:** Uses the machinery that already exists, and is exactly how `uv` and
`gitleaks` are handled.
**Cons:** It reconciles duplication rather than removing it, which ADR 0018 says
to prefer only when nothing else is available — and here something else is.
It also does not fit the assert it would rely on: that comparison finds a
version by matching the tool's name next to a version-shaped token on one line,
and the interpreter is spelled `"version": "3.13"` under a feature key on the
line above, and `python-version: "3.13"` in an action's `with:`. Each new
spelling is a regex in the checker for a value the register already holds, which
is the boundary ADR 0018 draws.

### Option 3: A toolchain file every locus reads

Commit `.python-version` naming the minor, and let uv resolve from it at every
locus. Record the file in the register as the interpreter's authority.

**Pros:** It removes the duplication instead of reconciling it — the same
property that makes `source: lockfile` the preferred option for every other
tool. There is one value, in one tracked file, and no locus repeats it, so there
is nothing to keep in step and nothing for a rename to drop out of comparison.
Measured, it selects rather than filters: with 3.13.15 installed and satisfying
the floor, `.python-version` naming 3.14 makes `uv sync` download and use
3.14.7, and naming 3.13 uses 3.13.15. CI needs no new step, because the
mechanism is the one uv already runs.
**Cons:** It is not a lockfile — no package manager produced it and none
maintains it — so the register needs a third `source` value rather than reusing
one that would be false. `UV_PYTHON` in the environment overrides it (measured:
`UV_PYTHON=3.14` with `.python-version` naming 3.13 yields 3.14.7), so the file
is authoritative over configuration but not over a caller who sets out to
bypass it.

## Decision

We will treat the interpreter that runs the gates as a pinned tool, and record
its authority in the register as a **toolchain file**.

`tools.python` takes `source: toolchain`, naming `.python-version`. The value
lives in that file; every locus reaches the interpreter through `uv`, which
reads it; and no locus repeats it. The third source value exists because the
first two are both false here — `literal` would mean the version lives in the
register and each locus repeats it, and `lockfile` would mean a package manager
owns it. A toolchain file is the third thing: an authority a human writes and
every locus reads.

`tool_versions_match_register` treats it the way it already treats a lockfile —
there is no version at any locus to compare, so what must hold is that the file
exists and is tracked. A `source: toolchain` tool therefore rejects `version:`,
`pinned_at:`, `release_repo:` and `lockfile:`, and requires `toolchain:` and
`invocation:`, for the reasons ADR 0020 gives for the lockfile pair: an
authority no invocation resolves to is not an authority.

**`requires-python` stays a floor, and keeps its own meaning.** It is the
package's support claim, not the environment's selection, and the two are now
recorded separately. `[tool.ruff] target-version` is deleted in the same change:
ruff infers the target from `requires-python` when the key is absent — measured,
`unresolved_target_version = 3.13` with no key present — so the explicit `py313`
was a third copy of the support floor, free to drift from it. Deriving it is
strictly better than comparing it, and it is now derived.

This also fixes the linter/interpreter disagreement in the right direction.
Ruff targets the **oldest** interpreter the package supports, because that is
what the code must run on; the environment runs whichever the toolchain file
names. Those are allowed to differ, and after this change the difference is
stated rather than accidental.

Option 3 was chosen over Option 1 because environment selection does not belong
in published package metadata, and over Option 2 because a property that holds
by construction beats one reconciled after the fact — the same argument ADR 0020
made for `invocation`.

## Consequences

**Positive outcomes:**

- The interpreter is named in the repository, once. Every locus resolves the
  same minor, and CI no longer picks one by what a runner image happens to lack.
- Moving minor version becomes a one-line change with a verdict attached, rather
  than an edit to two files that nothing compares.
- `ruff`'s target follows the support floor automatically, so the two cannot
  drift.
- SUP-001's `enforces` already reads *every tool this register pins resolves to
  the version recorded under `tools:`, at every locus that installs it*. The
  interpreter was outside that sentence while being inside its scope; it is now
  inside both.

**Trade-offs and risks:**

- `UV_PYTHON` overrides the file. This is not closed by the decision, and is not
  closable from inside the repository — an environment variable set on a runner
  outranks a committed file. It is a narrower hole than the one it replaces: it
  requires someone to set it deliberately, where the previous behaviour needed
  only a different base image.
- The devcontainer's python feature stays, and stays unpinned by the register.
  It bootstraps `pip install uv` and answers `#!/usr/bin/env python3`; it does
  not run a gate. Recording it as a pin would assert an equality that is not
  required and would break the first time the project interpreter moves ahead of
  the image's.
- Renovate covers `custom.regex` only, so `.python-version` needs a manager of
  its own or it fossilises — the same gap `docs/09-phase-1.5-review.md` § G
  records for the literals. One is added in the same change.
- A third `source` value is a third branch in the validator, and every gate
  skill that reads `tools:` must handle it. Today none installs an interpreter,
  so none does anything with it; a future one that does has a field to read
  rather than a filename to guess.

## Applied — the first move, and what it made visible

The pin landed at 3.13, the version the devcontainer already had, so that the
mechanism could be verified without also changing what ran. Moving it is the
first exercise of the decision, and it separated the three facts in practice
rather than on paper:

| | Before | After |
| --- | --- | --- |
| `.python-version` — what runs the gates | 3.13 | **3.14** |
| `requires-python` — what the package supports | `>=3.13` | `>=3.13`, unchanged |
| ruff's target — what the linter models | 3.13, derived | 3.13, derived |
| the devcontainer feature — what bootstraps | 3.13 | 3.13, unchanged |

Three of the four do not move, and each for its own reason. The support claim is
not this repository's environment. Ruff follows the support claim, so it is
still right to lint for 3.13 — the code must run there. And the feature is
bootstrap: it installs the `python3` that runs `pip install uv` in `setup.sh`
and answers `#!/usr/bin/env python3`, neither of which is a gate.

**That last one is the case this ADR predicted.** § Consequences recorded that
pinning the feature "would break the first time the project interpreter moves
ahead of the image's". This is that time, and nothing broke: uv resolves 3.14
inside a container whose system interpreter is 3.13, and the register does not
compare them because it never claimed they were equal.

### The claim the move left untested

Moving the environment to 3.14 meant nothing ran on 3.13 any more, while
`requires-python` went on saying 3.13 works — and adopters install
`standard-check` as a dependency, so somebody is on that floor. A property
declared and verified nowhere is the shape this repository exists to catch, and
the move would have created one.

`.github/workflows/support-floor.yml` is the answer: it reads the floor out of
`requires-python` and runs the test suite on it. It is not a gate, and it is
deliberately absent from CI-001's `required_checks:` — a support claim failing
is a thing to know about, not a reason a conformant change cannot merge. The
response is to widen the floor or fix the code, never to make the job required.

It is also the only place `UV_PYTHON` appears, which is the residual risk named
in § Consequences. The floor is a different interpreter from the pinned one by
definition, so the job that tests it has to override the pin — and the override
being used on purpose, in one reviewed file, is the difference between a known
escape hatch and an unmonitored one.

Measured, both ends pass:

```text
uv run pytest                       619 passed, 2 skipped   (3.14.7, the pin)
UV_PYTHON=3.13 uv run --frozen pytest   619 passed, 2 skipped   (3.13.15, the floor)
```

### What the floor job found on its first run

It failed, and not over the interpreter. `support-floor.yml` installs uv and
nothing else, because its subject is Python — and two tests asserting SEC-001
reaches `PASS` got `UNCLASSIFIED` instead, because `gitleaks` was not on that
runner's `PATH`. The checker was right: an absent tool is `UNCLASSIFIED`
(ADR 0016). The tests were asserting something about a binary without saying so.

They had passed everywhere they had ever run — this devcontainer installs
gitleaks in `setup.sh`, and the conformance job installs it before the test
step — so the dependency was invisible for as long as every environment happened
to satisfy it. It is the same hidden input `tests/conftest.py` already strips for
ambient authentication, one input over, and it took an environment that
deliberately had less in it to surface.

`requires_tool(name)` in `conftest.py` is the fix: skip, with the tool named,
rather than fail for a reason unrelated to the test's subject. Skipping rather
than tolerating `UNCLASSIFIED` is deliberate — a test that accepted that verdict
would keep passing in the devcontainer if the tool disappeared, which is
silence reading as agreement.

```text
with gitleaks on PATH      619 passed, 2 skipped
with gitleaks removed      617 passed, 4 skipped
```

## Related ADRs

- [ADR 0018: Draw the Boundary Between Register and Checker](0018-register-checker-boundary.md)
  — the test this applies: which interpreter a repository runs is a fact a
  repository may reasonably differ on without the checker changing.
- [ADR 0020: Invoke a Pinned Tool by the Path Its Lockfile Owns](0020-a-locus-reaches-the-pinned-artefact.md)
  — the same shape one level down, and the source of the `invocation`
  requirement carried here.
- [ADR 0003: Frozen Dependency Resolution](0003-frozen-dependency-resolution.md)
  — SUP-001's rationale, the control this verification lands in.
- [ADR 0007: Pinned Devcontainer Features](0007-pinned-devcontainer-features.md)
  — why the feature is pinned as a feature, and why that pin is not this one.

## References

- [uv — Python version files](https://docs.astral.sh/uv/concepts/python-versions/)
  — `.python-version`, its discovery order, and `UV_PYTHON`.
- [ruff — `target-version`](https://docs.astral.sh/ruff/settings/#target-version)
  — inference from `requires-python` when the key is absent.
- [Python packaging — `requires-python`](https://packaging.python.org/en/latest/specifications/pyproject-toml/#requires-python)
  — the field as a support claim published in package metadata.
