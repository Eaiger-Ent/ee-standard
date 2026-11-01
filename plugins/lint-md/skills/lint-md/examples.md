# lint-md — Calibration Examples

## §Strong

All seven artefacts produced; smoke-test runs cleanly:

- `package.json` lists `markdownlint-cli2` as an exact-pinned dev dependency and
  `package-lock.json` records the resolved version — the single authority every other
  locus resolves through via `<CLI2_INVOCATION>`

- `.markdownlint.yaml` written with `MD013` capped at 250 chars, `MD024` scoped to
  `siblings_only`, `MD050` set to `asterisk`, and `MD060` set to `compact`
- `.markdownlint-cli2.yaml` written with `ignores` set to `<CLI2_IGNORES>` verbatim
- `.claude/hooks/md-lint.py` written and registered in `.claude/settings.json` as a
  `PostToolUse` hook on `Write|Edit`
- `.pre-commit-config.yaml` has a `repo: local` markdownlint-cli2 hook running
  `<CLI2_INVOCATION>` (no `rev:` version copy)
- `.github/workflows/ci.yml` (or `lint.yml`) has `Lint Markdown` step using `npm ci` and
  `<CLI2_INVOCATION> "**/*.md"`
- `<CLI2_INVOCATION> "**/*.md"` exits 0 with 0 violations (or reports pre-existing
  violations scoped to project files only — not third-party dependencies)

Expected output matches the **Success** block in `output-templates.md`.

When migrating from `pymarkdownlnt`: all of the above, plus `.pymarkdown.json` removed,
pre-commit and CI steps updated, and pymarkdownlnt removed from `pyproject.toml` or
`requirements.txt`. Expected output matches **Success with migration**.

## §Weak

A weak run is missing ≥1 artefact:

- Config written but PostToolUse hook not installed (Step 3 skipped or failed silently)
- Hook installed but pre-commit entry missing (Step 4 skipped)
- Pre-commit hook added but CI step missing (Step 5 skipped)
- Linter installed but `.markdownlint.yaml` not written
- `.markdownlint-cli2.yaml` not written — smoke-test scans thousands of third-party files
- Smoke-test not run (Step 6 skipped)
- Migration detected but `.pymarkdown.json` not removed
- Version pinned by hand in a second locus (e.g. a pre-commit `rev:` or a version-suffixed
  install line) instead of resolving through `package-lock.json` — the pins drift apart

Any of these produces an incomplete setup that will not catch Markdown violations in CI,
on commit, or during Claude Code sessions.
