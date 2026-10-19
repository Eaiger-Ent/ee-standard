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
