# Phase 8 — what four weeks of use found, and how each closed

The evidence for each tick in
[`04-build-plan.md`](04-build-plan.md) § Phase 8. The findings themselves are in
[`craft/review.trial.md`](craft/review.trial.md) § The control register, in the
same four weeks, written before any of them was worked on; this records what
was done about each and how it was shown to hold.

## LNT-001 finds an ESLint flat config that is not valid YAML

**Closed 2026-10-19.**

**The defect.** `stacks.typescript.gates.lint.config` names `eslint.config.*`
and `.eslintrc*` with no section, and `_read_section`'s own docstring says a
location with no section is *configured by existing*. The code parsed the file
first and treated a failed parse as absence. No reader in the checker parses
JavaScript, so a flat config fell through to the YAML reader:

| Config | As YAML | LNT-001 said |
| --- | --- | --- |
| `export default [];` | a plain string | configured |
| `export default [js.configs.recommended, { rules: { semi: "error" } }];` | a parse error at the `{` | **no eslint configuration** |

Since ESLint 9 a flat config is the only format ESLint reads, so every real
TypeScript repository hit the second row, and the verdict depended on whether
its config happened to be valid YAML.

**The fix.** For a location with no section, existence decides before any parse
is attempted. A parsed document is still returned to a caller that reads one;
a file that does not parse returns an empty mapping rather than nothing.

**One consequence, stated rather than discovered later.** An unparseable
section-less file — a broken `ruff.toml` — now counts as configured. That is
what the docstring always said, and ruff refusing its own configuration fails
every locus that runs it, which is where that failure belongs.

**How it was shown to hold.**

- `tests/test_stacks.py::test_an_eslint_config_counts_by_existing_whatever_it_contains`
  runs the real register over a TypeScript repository wired at every locus,
  with four config shapes. Before the fix the object-literal and CommonJS
  shapes failed with *no eslint configuration* and the trivial and JSON ones
  passed — the defect exactly. After it, all four pass.
- The trial repository, at the commit the review assessed:
  `register-check run --control LNT-001` read FAIL before and **PASS** after,
  with nothing in that repository changed.

**What it does not reach yet.** An adopter runs the checker at the ref their
register pins — the trial repository pins `v0.8.4` — so the fix reaches them at
the next release and not before.

## LNT-001's title and its verification agree about formatting

**Closed 2026-10-19, by correcting the title.**

**The mismatch.** LNT-001 was titled *Lint and format violations block the
merge*. Its `enforces:` text, its verify blocks and ADR 0009 are all about the
linter, and none mentions formatting. What the register does govern is narrower
than the title and real: from contract 21 the editor locus requires
`[python].editor.defaultFormatter` to be the pinned tool's extension
(`editor_binding`). Nothing at a locus that can block a merge — no hook, no CI
step — runs a format check. The trial repository's `CONTRIBUTING.md` had
already said so in its own words.

**What was done.** The title now reads *Lint violations block the merge*, with
a comment in `controls.yaml` saying what it read and why it changed.
`controls.published.yaml` is re-derived. No `meta.register_contract` bump: the
rule in `CLAUDE.md` names `rung`, `verify`, `variance` and `applies_to`, and a
title is none of them — what any repository has to do is unchanged.

**What was found on the way, and fixed with it.** Craft's
`python.consistent-formatting` was counted as **bound** in both Python profiles,
its instrument `ruff format` with no codes, on the reading that the property
*is met by running it*. Nothing runs it at a locus that can fail, so both
profiles reported a property as enforced that no build could fail on. It is now
`unenforced` with `ruff format --check` as its candidate, and appears in the
residue. `python/standard@4` and `python/strict@4` record the move as `neither`:
nothing a repository runs changed, only what the record claims.

**What was deliberately not done.** Wiring `ruff format --check` at pre-commit
and in CI would make the old title true, and it changes what LNT-001 enforces
for every adopter: a field in `stacks:`, an assert that reads it, a
`gate-quality` step, a contract bump and a checker release. That is a decision
about the standard, which an ADR records and a second reader accepts, not a
correction. It is also not free here: `ruff format --check .` reports 47 files in
this repository that it would reformat. Recorded, not scheduled.

## `deployments` says when a stack has arrived since a gate ran

**Closed 2026-10-19.**

**The gap.** A stamp records what a gate wrote and at which contract. It does
not record which stacks the gate found. So when React and TypeScript arrived in
the trial repository three weeks after `gate-quality` ran, every stamp stayed
current and the report read `gate-quality CURRENT`. The TypeScript half had been
wired by hand, and nothing said the gate was owed a run.

**What `deployments` now does.** For each gate that has deployed, it takes the
roles the gate wires from the register — a control the gate deploys whose verify
block names `role:` — and, for every stack whose predicate holds now, looks up
that stack's hook for the role in `stacks:` (`pre_commit`). Then it asks whether
that hook in `.pre-commit-config.yaml` is headed by the gate's stamp: the
unbroken run of comment lines directly above `- id:`, where every gate writes
it. A blank line ends the run, so a hand-written hook below a gate's is not
credited to the gate by sitting near it.

A stack whose hook is missing, or carries no stamp from the gate, is listed
under the gate with the instruction to run it again. The gate keeps its state —
no stamp is behind, so `STALE` would be false — and it counts as owed in the
summary. The exit code is unchanged: staleness is reported, never enforced.

**How it was shown to hold.**

- Six tests in `tests/test_deployments.py`, from one fixture that differs only
  in the pre-commit file and whether `tsconfig.json` exists: hand-wired hooks
  reported and owed; stamped hooks not reported; absent hooks reported; no
  TypeScript, nothing owed; a stamp separated by a blank line not credited; the
  rendered report naming the stack and the instruction.
- Mutation-tested on its three rules — the blank line, the predicate, the
  owed count — and each mutation fails the test written for it.
- The trial repository, read with the change: `gate-quality CURRENT`, then
  *typescript: the eslint hook carries no gate-quality stamp* and the same for
  `tsc`, and *2 owed a deployment* where it had said 1. This repository's own
  report is unchanged: it is Python-only, and its hooks are stamped.

**Only the pre-commit locus is read**, and that is deliberate rather than
unfinished. It is the one locus where a stamp sits beside the thing it governs,
and one locus is enough to tell a stack the gate wired from one it did not.

## TYP-001 and a vendored file it may not edit

**Closed 2026-10-19, by the register saying why it cannot be met another way.**
The criterion offered two ways out — the control can be met, or the register
says why it cannot — and the decisions already in force answer it.

**The case.** The trial repository tracks `.claude/hooks/yaml-lint.py`, a hook
the `lint-yaml` skill copies in and later compares line by line against its own.
It sits outside `[tool.mypy] files`, so TYP-001 failed from the day of install.
Adding it to `files` is not a fix: strict mypy reports two errors in it, and
editing a vendored copy breaks the skill's comparison.

**Why there is no exemption.** An exclusion that hides a tracked file is what
[ADR 0019](adr/0019-exemptions-cannot-hide-tracked-files.md) forbids, and
TYP-001's own text allows *no per-file opt-out beyond the recorded baseline*,
where the baseline is `null`. A `vendored:` list, or honouring
`linguist-vendored` in `.gitattributes`, would be that opt-out under another
name. Making one would mean superseding ADR 0019, for a case with two honest
routes already open.

**What was done.** TYP-001 carries a comment saying a vendored file has no
exemption and why, and `08-adopting.md` § 3.2 point 2 gives the two routes: get
the file fixed upstream so it passes strict mode, or stop tracking it and have
its installer write it at setup. Until then TYP-001 fails, and the failure is
accurate.

**The upstream fix, measured.** `lint-yaml` 0.1.14, the newest release in the
ee-skills marketplace on this machine, ships `yaml-lint-hook.py` with the same
two errors. Both come from one function: `in_repo` has no annotations, and the
second error is a typed call into it. One line in that skill would let every
repository that vendors it put `.claude/hooks` under strict mypy. That is a
change to another repository and is recorded here as owed, not made.

## Some locus fails when the register's verdict is FAIL

**Closed 2026-10-19**, implementing
[ADR 0057](adr/0057-register-install-writes-the-conformance-step.md), accepted
the same day. Register contract 36.

**What the review got wrong about it, and what it found instead.** The finding
read as *no locus computes the register's verdict*, as if the design had no
answer. It has one: `08-adopting.md` § 4.1 and § 4.3 tell the adopter to add a
*Conformance* step running `uv run register-check`, the sweep template assumes
it is there, and checklist rows 8 and 10 depend on it. The trial repository did
not take that step, because no skill writes it, and nothing reported its
absence: GOV-001 counts a control as reached when a step runs its **tool**, so
`uv run mypy` reaching TYP-001 satisfied it while TYP-001's own verdict was
computed nowhere CI runs.

**Why it is a decision and not a fix.** Two things have to change, and each
belongs to an Accepted ADR. Which skill writes the step widens a skill that
ADR 0032 decided *owns nothing else*. And GOV-001 failing without the step is
a change to a meta-control's verify, which moves the register contract. ADR 0057
proposes `register-install` for the first — it runs on every adoption, where
`gate-repo` is the gate most often left unfinished — and the GOV-001 change for
the second.

**What was built.**

- **GOV-001** fails a repository with no gating step that runs the whole
  register, and one whose full run sits in a job no recorded ruleset requires.
- **`register-install`** writes that step from a template, as the last step of
  the job CI-001's `required_checks:` names, in the tolerant form `08-adopting.md`
  § 4.3 gives: a verified violation fails it, exit `3` passes and is printed.
  With no gating workflow yet it defers and says so, and `register-adopt` runs it
  again after the file-writing gates, before `gate-repo`, so the step is in the
  adoption's own commit.

**Two defects found by building it, both in GOV-001's reachability.** Fixing
them is what made the new requirement mean anything:

| What it did | What it does now |
| --- | --- |
| Credited `register-check run --control SUP-001` — and `run --tier 1`, and `deployments` — as a run of the whole register, because its pattern excluded only `assert`, `meta`, `explain` and `schema`. So every gate's named-control step made **every** blocking control reachable | Reads the subcommand: the bare checker, or `run` with no `--control` and no `--tier`, is a full run. Global options before the subcommand are skipped with their values |
| Never credited `run --control X` with reaching X — the full-run accident had covered for it | `run --control X` reaches X and nothing else |

Together they are why the trial repository read *every applicable blocking
control is reached* while its CI never asked the register for a verdict. With
both fixed and no step added, GOV-001 there reads FAIL and lists SEC-003,
LNT-001, TYP-001 and TST-001 as unreached — exactly the four no step in that CI
computes.

**How it was shown to hold.**

- Six tests in `tests/test_meta.py`, five new and one changed: a repository that never
  runs the whole register fails; each of the three spellings § 4.3 gives counts
  as a full run, including the exit-code capture; `run --control`, `meta`,
  `explain` and `schema` do not; a `--control` step reaches what it names, both
  through the helper and through the verdict. Mutation-tested on the
  requirement, on the narrowing rule and on the `--control` credit — the last
  survived the first pass, and the verdict-level test was written for it.
- On a copy of the trial repository with the shipped template placed as Step 5
  says: GOV-001's file half passes, and every other control's verdict is
  unchanged — TYP-001 still FAIL, which is what the step would now fail the
  required check on.
- ee-standard's own GOV-001 still passes: its CI already runs the whole
  register.

**What it does not reach yet.** An adopter meets both the step and GOV-001's
requirement at the next checker release and a re-run of `register-install`.
