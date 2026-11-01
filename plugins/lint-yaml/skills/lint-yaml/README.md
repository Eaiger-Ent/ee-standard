# lint-yaml

## What it does

Installs a pinned yamllint in your project and wires it up in three places. A Claude Code
PostToolUse hook reports YAML issues in real time, a pre-commit hook blocks commits on
violations, and a GitHub Actions CI step lints every push. You start it with `/lint-yaml`. It
writes `.yamllint.yml`, `.claude/hooks/yaml-lint.py`, the hook entry in
`.claude/settings.json`, a `.pre-commit-config.yaml` entry and a CI step, then runs a
smoke test.

## Audience

Contributors to any repo that contains YAML files (GitHub Actions workflows, config,
OpenAPI specs) and wants automated style enforcement locally and in CI.

## Getting started

Prerequisites: Claude Code installed; a git repo; `uv` available — every locus
runs a pinned `yamllint` through it.

Trigger the skill in a Claude Code session:

```text
/lint-yaml
```

The skill installs `yamllint`, drops a `.yamllint.yml` config, and wires all three hooks.
A smoke-test runs at the end to surface any pre-existing violations.

## Usage

Run once per project to set up. Running it again is safe. If `.yamllint.yml` already
exists, the skill asks whether to overwrite it or stop. A hook copy that is out of date
is replaced. Hooks and CI steps that are already present are skipped with a message.

To run linting manually, use the same invocation the hooks run — `uv run yamllint` in a
project with a `pyproject.toml`, otherwise the pinned `uvx` form:

```bash
uv run yamllint -c .yamllint.yml .
uvx --from yamllint==1.38.0 yamllint -c .yamllint.yml .
```

The Claude Code hook fires automatically on every Write or Edit tool call to a `.yml` or
`.yaml` file, so violations are caught before they accumulate.

## Approach

- **Why one invocation at every locus?** A bare `pip install yamllint` pins nothing. A
  pre-commit hook pinned by its own `rev:` keeps a second copy of the version, which
  drifts from the first. The hook, pre-commit and CI all run one configured command, so
  the version has one owner: the project's lockfile, or the `uvx` pin when there is none.
- **Why state `key-duplicates` and `truthy` at `error`?** yamllint's `default` config sets
  `truthy` to `warning`, and yamllint exits 0 over warnings, so an inherited floor rule is
  a check that cannot fail. These two are the floor the control register's YML-001
  requires.
- **Why compare the deployed hook against the canonical script?** A deployed copy is a
  snapshot. Checking only that it mentions the linter reports an outdated copy as present.
  So the skill compares the whole file, except the `LINT_INVOCATION` line each deployment
  rewrites.
- **Why does the registered hook command fail open?** It resolves to the current worktree
  root. Without the guard, a worktree that lacks `.claude/hooks/yaml-lint.py` would fail
  every Write or Edit.

## References

- yamllint documentation: <https://yamllint.readthedocs.io/en/stable/>
- yamllint rules (`truthy`, `key-duplicates`): <https://yamllint.readthedocs.io/en/stable/rules.html>
- uv tools (`uvx`): <https://docs.astral.sh/uv/guides/tools/>
- pre-commit `repo: local` hooks: <https://pre-commit.com/#repository-local-hooks>

## Key files

- `SKILL.md` — the setup procedure
- `local-config.md` — how a repository pins the invocation the skill writes
- `scripts/yaml-lint-hook.py` — the canonical PostToolUse hook copied into the project
- `scripts/config-state.sh`, `scripts/precommit-state.sh` — pre-flight state probes

## Contributing

Raise issues or pull requests at
<https://github.com/EqualExperts/ee-skills-incubator>.
