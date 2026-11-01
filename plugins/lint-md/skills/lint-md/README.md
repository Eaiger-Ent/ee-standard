# lint-md

Installs markdownlint-cli2 in your project and wires it up in three places: a Claude Code
PostToolUse hook that auto-fixes and reports Markdown style issues in real time, a pre-commit
hook that blocks commits on unresolved violations, and a GitHub Actions CI step.

## What it does

You start it with `/lint-md`. It installs `markdownlint-cli2` as an exact-pinned dev
dependency, then writes `.markdownlint.yaml` and `.markdownlint-cli2.yaml`. It also writes
`.claude/hooks/md-lint.py` and registers it in `.claude/settings.json`, adds a
`.pre-commit-config.yaml` hook and a workflow step. It finishes by linting every Markdown file
once to show what already fails. If the repo still uses pymarkdownlnt, the skill moves it
over to markdownlint-cli2.

## Audience

Contributors to any repo that contains Markdown documentation and wants automated style
enforcement enforced locally and in CI.

## Getting started

Prerequisites: Claude Code installed; a git repo; Node.js with `npm` available; `uv`
available — the skill runs its PyYAML helpers with `uv run --script`, so they work whatever
`python3` the machine has.

Trigger the skill in a Claude Code session:

```text
/lint-md
```

The skill installs `markdownlint-cli2` as an exact-pinned dev dependency (recorded in
`package.json` and `package-lock.json`) and wires all three hooks. A smoke-test runs at
the end to surface any pre-existing violations.

## Usage

Run once per project to set up. Subsequent invocations are idempotent — already-present
hooks and config are skipped with a message.

To re-run linting manually:

```bash
npx --no-install markdownlint-cli2 "**/*.md"
```

To auto-fix without running the full skill:

```bash
npx --no-install markdownlint-cli2 --fix "**/*.md"
```

The Claude Code hook fires automatically on every Write or Edit tool call, so violations
are caught before they accumulate.

## Local configuration

The command above is the default. A repository may pin what this skill writes in
`.claude/skill-config.yaml`, and the skill reads it before Step 1:

```yaml
lint-md:
  invocation: node_modules/.bin/markdownlint-cli2
  ignores: []
```

`invocation` replaces `npx --no-install markdownlint-cli2` at every locus — the pre-commit
hook, the CI step, the DevContainer check and every verification command. `ignores`
replaces the default ignore list in `.markdownlint-cli2.yaml`, verbatim rather than
merged, so `ignores: []` means ignore nothing.

An absent file, an absent key or an absent value takes the default, so a repository that
has never set this gets exactly what it got before.

## Approach

- **Why pin the version in `package-lock.json` and nowhere else?** The hook, pre-commit
  and CI all run one configured command, so the lockfile is the only place the version
  lives. A pre-commit hook pinned by its own `rev:` would hold a second copy that drifts.
  So the hook is a `repo: local` entry, and the skill replaces an older `rev:`-pinned block
  when it finds one.
- **Why write `ignores` verbatim rather than merging it with the default?** A repository
  that sets `ignores: []` means "ignore nothing". Merging would quietly bring the default
  list back.
- **Why compare the deployed hook against the canonical script?** A deployed copy is a
  snapshot. Checking only that it mentions the linter reports an outdated copy as present
  (#842). So the skill compares the whole file, except the `LINT_INVOCATION` line each
  deployment rewrites.
- **Why does the registered hook command fail open?** It resolves to the current worktree
  root. Without the guard, a worktree that lacks `.claude/hooks/md-lint.py` would fail
  every Write or Edit.

## References

- markdownlint-cli2: <https://github.com/DavidAnson/markdownlint-cli2>
- markdownlint rules: <https://github.com/DavidAnson/markdownlint/blob/main/doc/Rules.md>
- pre-commit `repo: local` hooks: <https://pre-commit.com/#repository-local-hooks>
- `npm ci`: <https://docs.npmjs.com/cli/commands/npm-ci>

## Contributing

Raise issues or pull requests at
<https://github.com/EqualExperts/ee-skills-incubator>.
