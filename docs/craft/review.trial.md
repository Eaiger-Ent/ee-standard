# Craft — the trial

Stage **S6** of [`plan.md`](plan.md). Install on a new repository at its start,
run for a stated period, and revise against what the team reports rather than
against what the plan predicted.

**Status: installed 2026-09-20; the fortnight runs to 2026-10-04.** This
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

## What this document owes

| Owed | When |
| --- | --- |
| ~~The install record: what was inferred, what was presented, what was chosen, what was written~~ — § The install, 2026-09-20 | Done |
| ~~The repository's size and shape at install, so the finding counts mean something~~ — § The repository at the moment of install | Done |
| ~~The span's position~~ — `craft-install` Step 4 now names *immediately after the header line*, 2026-09-25 | Done |
| ~~The comment that describes a table it no longer matches~~ — `gate-quality` Step 2 now writes no comment describing the section, and `craft-install` reports one it finds rather than editing it, 2026-09-25 | Done |
| The other two things § What the install found raises — the missing assistant context file and repository tooling — answered or carried | At the review |
| What the two weeks produced — findings met, rules fought, anything switched off | At the review |
| S3's criteria as they hold in use, or the gap recorded | At the review |
| A profile revision, or the reason there is none | At the review |
