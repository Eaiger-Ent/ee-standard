# lint-yaml — Output Templates

## Success

```text
lint-yaml setup complete
  Config:      .yamllint.yml (floor at error: key-duplicates, truthy; line-length 200; comments enforced)
  Claude hook: .claude/hooks/yaml-lint.py — written; PostToolUse entry added to .claude/settings.json
  Invocation:  uv run yamllint (every locus)
  Pre-commit:  .pre-commit-config.yaml — yamllint hook added (repo: local)
  CI:          .github/workflows/ci.yml — Lint YAML step added
  Smoke-test:  0 violations
```

## Success with violations

```text
lint-yaml setup complete
  Config:      .yamllint.yml
  Claude hook: .claude/hooks/yaml-lint.py — already up to date; PostToolUse entry already present
  Invocation:  uvx --from yamllint==1.38.0 yamllint (every locus)
  Pre-commit:  .pre-commit-config.yaml — yamllint hook added (repo: local)
  CI:          .github/workflows/lint.yml — created
  Smoke-test:  7 violations in 2 files (pre-existing — not auto-fixed)
               Run `<YAMLLINT_INVOCATION> .` to see the full list.
```

## Aborted — already configured

```text
lint-yaml aborted — .yamllint.yml already exists; user chose not to overwrite.
  Action: No changes made.
```

## Install failed

```text
lint-yaml failed — yamllint install returned non-zero.
  Error: <exact uv error output, or UV_MISSING>
  Action: Fix the install error and re-run /lint-yaml.
```

## Hook write failed

```text
lint-yaml failed — .claude/hooks/yaml-lint.py could not be written.
  Error: <WRITE_FAILED or INVOCATION_NOT_WRITTEN, with the stop message Step 2.5a names>
  Action: Check .claude/hooks/ is writable and re-run /lint-yaml.
```

## Pre-commit YAML invalid

```text
lint-yaml failed — .pre-commit-config.yaml is malformed after edit.
  Error: <parse error from yaml.safe_load>
  Action: Repair .pre-commit-config.yaml manually and re-run /lint-yaml.
```
