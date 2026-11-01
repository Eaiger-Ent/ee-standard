# lint-md — Output Templates

## Success

```text
✅ lint-md setup complete
  Config:      .markdownlint.yaml (MD013: 250 chars, MD024: siblings_only, MD050: asterisk, MD060: compact)
               .markdownlint-cli2.yaml (ignores: <CLI2_IGNORES>)
  Hook:        .claude/hooks/md-lint.py — PostToolUse auto-fix wired
  Pre-commit:  .pre-commit-config.yaml — local `<CLI2_INVOCATION>` hook added
  CI:          .github/workflows/ci.yml — Lint Markdown step added
  Smoke-test:  0 violations
  Config from: invocation: node_modules/.bin/markdownlint-cli2 (.claude/skill-config.yaml)
```

Omit the `Config from:` line when every value came from a default. List one entry per
value that `.claude/skill-config.yaml` pinned — see `local-config.md`.

## Success with violations

```text
⚠️ lint-md setup complete
  Config:      .markdownlint.yaml (MD013: 250 chars, MD024: siblings_only, MD050: asterisk, MD060: compact)
               .markdownlint-cli2.yaml (ignores: <CLI2_IGNORES>)
  Hook:        .claude/hooks/md-lint.py — PostToolUse auto-fix wired
  Pre-commit:  .pre-commit-config.yaml — local `<CLI2_INVOCATION>` hook added
  CI:          .github/workflows/lint.yml — created
  Smoke-test:  12 violations in 3 files (pre-existing — not auto-fixed)
               Run `<CLI2_INVOCATION> "**/*.md"` to see the full list.
```

## Success with migration

```text
✅ lint-md setup complete (migrated from pymarkdownlnt)
  Removed:     .pymarkdown.json
  Config:      .markdownlint.yaml (MD013: 250 chars, MD024: siblings_only, MD050: asterisk, MD060: compact)
               .markdownlint-cli2.yaml (ignores: <CLI2_IGNORES>)
  Hook:        .claude/hooks/md-lint.py — PostToolUse auto-fix wired
  Pre-commit:  .pre-commit-config.yaml — pymarkdown hook replaced with local `<CLI2_INVOCATION>` hook
  CI:          .github/workflows/ci.yml — pymarkdown step replaced with markdownlint-cli2
  Smoke-test:  0 violations
  Next steps:  Run `uv sync` or `pip install -r requirements.txt` to remove pymarkdownlnt
               from your environment.
```

## Aborted — already configured

```text
⚠️ lint-md aborted — .markdownlint.yaml already exists; user chose not to overwrite.
  Action: No changes made.
```

## Install failed

```text
❌ lint-md failed — markdownlint-cli2 install returned non-zero.
  Error: <exact npm error output>
  Action: Fix the install error and re-run /lint-md.
```

## Pre-commit YAML invalid

```text
❌ lint-md failed — .pre-commit-config.yaml is malformed after edit.
  Error: <parse error from yaml.safe_load>
  Action: Repair .pre-commit-config.yaml manually and re-run /lint-md.
```
