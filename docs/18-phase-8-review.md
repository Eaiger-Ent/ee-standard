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
