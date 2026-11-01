---
name: lint-yaml
description: >
  Set up yamllint linting in the current project: installs yamllint, drops a config
  file, wires a PostToolUse Claude Code hook, a pre-commit hook, and a GitHub Actions CI
  step. Triggers: 'lint yaml', 'set up yaml linting', 'add yamllint', '/lint-yaml'.
argument-hint: "[path]"
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
---

# /lint-yaml — YAML Linting Setup

You are running the **lint-yaml** skill. Install `yamllint`, drop a config file, wire a
PostToolUse Claude Code hook, a pre-commit hook, and add a GitHub Actions CI step to the
current project.

**Project-relative:** every bare path below — `.yamllint.yml`, `.claude/hooks/yaml-lint.py`,
`.claude/settings.json`, `.pre-commit-config.yaml`, `.github/workflows/` — is a file this skill
creates or edits in the project you are configuring. Only `${CLAUDE_SKILL_DIR}/...` paths refer
to the skill's own shipped files. Run the skill from the target project's root.

**Do not use when:**

- `.yamllint.yml` already exists — the project is already configured (re-run is safe but
  will overwrite the config; warn the user before proceeding).
- You only need to run the linter, not set it up; just call `yamllint .` directly.

---

## Pre-flight — detect current state

Run these checks before making any changes.

1. Check for existing config:

   ```bash
   bash "${CLAUDE_SKILL_DIR}/scripts/config-state.sh"
   ```

   - `EXISTS_EMPTY`: stop — "ERROR: `.yamllint.yml` exists but is 0 bytes — the previous setup was incomplete. Delete it and re-run `/lint-yaml`."
   - `EXISTS_NONEMPTY`: ask the user via **AskUserQuestion**: "`.yamllint.yml` already exists. Overwrite and reconfigure, or abort?" — options: Overwrite / Abort. If Abort, stop here.

2. Detect package manager:

   ```bash
   test -f pyproject.toml && echo "uv" || echo "uvx"
   ```

   Store as `PKG_MANAGER` for Step 1. `uv` means the project's own lockfile pins
   `yamllint`; `uvx` means nothing does, so the version is written at every locus.

3. Check for pre-commit config:

   ```bash
   test -f .pre-commit-config.yaml && echo "EXISTS" || echo "ABSENT"
   ```

   Store as `PRECOMMIT_STATE`.

4. List existing GitHub Actions workflow files:

   ```bash
   ls .github/workflows/ 2>/dev/null || echo "NONE"
   ```

   Store the list for Step 4. If the directory exists but is empty (command exits 0 with no output), treat as NONE — proceed to Step 4b to create a new workflow.

5. Read local configuration:

   Read `${CLAUDE_SKILL_DIR}/local-config.md` and follow it — the repository may pin what
   this skill writes, and an absent file means every default. Store the invocation it
   yields as `YAMLLINT_INVOCATION`. It is the one command every locus runs: the hook
   (Step 2.5a), the pre-commit hook (Step 3) and the CI step (Step 4). If the file sets
   none, the default is resolved in Step 1.

---

## Step 1 — Install yamllint

Every locus must run the **same pinned** `yamllint`. A bare `pip install yamllint` pins
nothing, and a hook pinned by its own `rev:` keeps a second copy of the version that
drifts from the first. So the version has one owner:

If `PKG_MANAGER` is `uv`, the project's lockfile owns it:

```bash
uv add --dev yamllint
```

The default `YAMLLINT_INVOCATION` is `uv run yamllint`.

If `PKG_MANAGER` is `uvx`, no lockfile can own it, so resolve a version and write it at
every locus:

```bash
uv --version || echo "UV_MISSING"
bash "${CLAUDE_SKILL_DIR}/scripts/detect-version.sh"
```

If `UV_MISSING`, stop: "`uv` is required to run a pinned `yamllint` without a Python
lockfile — install it (<https://docs.astral.sh/uv/>) and re-run `/lint-yaml`." Store the
version as `YAMLLINT_VERSION`. The default `YAMLLINT_INVOCATION` is
`uvx --from yamllint==<YAMLLINT_VERSION> yamllint`.

A `YAMLLINT_INVOCATION` from `local-config.md` replaces the default in either case.

Verify:

```bash
<YAMLLINT_INVOCATION> --version
```

If the install fails (non-zero exit or `command not found`), stop and show the user the exact
error output. Do not proceed.

---

## Step 2 — Drop the config file

**Write** `.yamllint.yml`:

```yaml
extends: default

# Not linted: what the repository does not author (a virtualenv, node_modules).
# Never list a tracked file here — hiding authored YAML is a weakening, not a scope.
ignore-from-file: .gitignore

rules:
  line-length:
    max: 200
  # The correctness floor, stated at error rather than inherited: `default` sets `truthy`
  # to warning, and yamllint exits 0 over warnings — a check that cannot fail.
  key-duplicates:
    level: error
  truthy:
    allowed-values: ['true', 'false']
    check-keys: false
    level: error
  comments:
    min-spaces-from-content: 1
```

After writing, verify the file is non-empty:

```bash
test -s .yamllint.yml && echo "OK" || echo "WRITE_FAILED"
```

If `WRITE_FAILED`, stop: "`.yamllint.yml` was not written correctly — please re-run `/lint-yaml`."

Rule rationale (tell the user after writing):

- `key-duplicates` at `error` — YAML requires unique keys, and most parsers keep the
  last duplicate and drop the rest silently, so a pasted key replaces a value with no
  error anywhere else.
- `truthy` at `error` — restricts truthy values to `true`/`false`, so `NO` or `on` is
  never read as a boolean; `check-keys: false` keeps a GitHub Actions `on:` key legal.
- `line-length.max: 200` — accommodates long GitHub Actions expressions, URLs and
  one-line strings, which a wrap would make harder to read, not easier.
- `comments` — enforces a single space between code and inline comments for readability.
- `ignore-from-file: .gitignore` — `yamllint .` otherwise walks into untracked trees.

These first two are the floor the control register's YML-001 requires. A repository
may add or tighten rules; it should never disable these or lower them below `error`.

---

## Step 2.5 — Install PostToolUse Claude Code hook

### Step 2.5a — Write the hook script

Create the hooks directory if it does not exist:

```bash
mkdir -p .claude/hooks
```

Check for an existing hook:

```bash
test -f .claude/hooks/yaml-lint.py && echo "EXISTS" || echo "ABSENT"
```

If `EXISTS`, ask whether that copy is still the script it was copied from. "It mentions
the linter" is not that question: a fix to the canonical script leaves an older copy
running, and a test that only looks for the linter's name reports it as present (#842).

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/yaml-check-hook-freshness.py" \
  "${CLAUDE_SKILL_DIR}/scripts/yaml-lint-hook.py" .claude/hooks/yaml-lint.py
```

The comparison ignores the `LINT_INVOCATION` line, which a deployed copy is expected to
differ by — it is rewritten below.

- `FRESH` — the copy already matches. Skip the `cp` below, but still run the
  `LINT_INVOCATION` write and its verification: the comparison ignores that line, so it
  cannot tell a changed `YAMLLINT_INVOCATION` from an unchanged one. Tell the user the
  hook was already up to date.
- `STALE` — the copy is an older version of this script. Continue; the `cp` below replaces
  it. Tell the user which file was overwritten, so a local edit to it is not lost silently.
- `ABSENT` — no copy yet. Continue as a first install.

Copy the hook script from the skill's scripts directory:

```bash
cp "${CLAUDE_SKILL_DIR}/scripts/yaml-lint-hook.py" .claude/hooks/yaml-lint.py
```

**Then write `YAMLLINT_INVOCATION` into it.** The copied script carries the default
invocation, and a copy is not a deployment: the value the repository configured is named
in `local-config.md` and this is where it lands. Use **Edit** to replace the whole
`LINT_INVOCATION` line:

```python
LINT_INVOCATION = "<YAMLLINT_INVOCATION>"
```

If `YAMLLINT_INVOCATION` is the default the line is already correct — say
"skipped, already the default" rather than rewriting it. Verify the value landed, so a
failed Edit is not reported as a deployment:

```bash
grep -q '^LINT_INVOCATION = "<YAMLLINT_INVOCATION>"$' .claude/hooks/yaml-lint.py \
  && echo "OK" || echo "INVOCATION_NOT_WRITTEN"
```

If `INVOCATION_NOT_WRITTEN`, stop: "`.claude/hooks/yaml-lint.py` still carries the default
invocation — the configured value was not applied. Re-run `/lint-yaml`."

Verify the write succeeded:

```bash
test -s .claude/hooks/yaml-lint.py && echo "OK" || echo "WRITE_FAILED"
```

If `WRITE_FAILED`, stop: "`.claude/hooks/yaml-lint.py` was not written — please re-run `/lint-yaml`."

### Step 2.5b — Register in .claude/settings.json

Read `.claude/settings.json` if it exists, or treat it as `{}`.

Check whether a `PostToolUse` entry for `yaml-lint.py` already exists:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/yaml-check-hook-registered.py" yaml-lint.py
```

If `ABSENT`, merge the new entry into the settings:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/yaml-wire-settings-hook.py" yaml-lint.py
```

The command registered anchors on the repository root so the hook runs correctly regardless
of the shell's working directory, and guards on the hook file being present there so it
fails **open**:

```json
"command": "bash -c 'root=$(git rev-parse --show-toplevel 2>/dev/null) && cd \"$root\" && [ -f .claude/hooks/yaml-lint.py ] || exit 0; uv run python .claude/hooks/yaml-lint.py'"
```

Without the `[ -f … ] || exit 0` guard the hook fails *closed*: `--show-toplevel` resolves to
the current **worktree** root, and a worktree that does not hold `.claude/hooks/yaml-lint.py`
makes `uv run` exit non-zero on every `Write`/`Edit` (#865, #872).

Verify the file is valid JSON after writing:

```bash
uv run --script "${CLAUDE_SKILL_DIR}/scripts/yaml-validate-config.py" .claude/settings.json
```

If the output starts `INVALID`, show the user the parse error it names and restore the
original content.

---

## Step 3 — Wire pre-commit hook

The hook is a `repo: local` entry running `YAMLLINT_INVOCATION`, the same command as every
other locus, so the version resolves from wherever Step 1 pinned it — there is no `rev:`
copy to keep in step.

The hook block:

```yaml
  - repo: local
    hooks:
      - id: yamllint
        name: yamllint
        entry: <YAMLLINT_INVOCATION>
        language: system
        types: [yaml]
```

**If `.pre-commit-config.yaml` exists:** Read it first. Validate it is non-empty and parseable:

```bash
uv run --script "${CLAUDE_SKILL_DIR}/scripts/yaml-validate-config.py" .pre-commit-config.yaml
```

If the output starts `INVALID`, stop: "ERROR: `.pre-commit-config.yaml` is empty or malformed — repair it manually and re-run `/lint-yaml`."

Check what is already present:

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/precommit-state.sh"
```

If `LEGACY_PINNED` (an `adrienverge/yamllint` block with a `rev:` pin, written by a
previous version of this skill): use **Edit** to replace that repo block with the
`repo: local` block above — leaving it would keep a second, hand-kept copy of the version.

If `PRESENT`: tell the user "yamllint hook already in `.pre-commit-config.yaml` — skipped"
and proceed to Step 4.

If `ABSENT`: use **Edit** to append the block after the last existing repo entry.

**If `.pre-commit-config.yaml` does not exist:** **Write** it from scratch:

```yaml
repos:
  - repo: local
    hooks:
      - id: yamllint
        name: yamllint
        entry: <YAMLLINT_INVOCATION>
        language: system
        types: [yaml]
```

After writing, validate it is parseable:

```bash
uv run --script "${CLAUDE_SKILL_DIR}/scripts/yaml-validate-config.py" .pre-commit-config.yaml
```

If the output starts `INVALID`, show the user the parse error it names and stop.

---

## Step 4 — Add GitHub Actions CI step

Select a target workflow:

- Prefer `ci.yml`, `lint.yml`, `build.yml` — in that order — from the list found in Pre-flight.
- If none of those exist but another workflow file is present, use the first one listed.
- If no workflow files exist at all, create `.github/workflows/lint.yml` (Step 4b).

The step runs `YAMLLINT_INVOCATION`, so CI lints with the version every other locus uses.
Both forms need `uv` on the runner.

**Step 4a — Add step to existing workflow:** Read the file. Check if the step already exists:

```bash
grep -q "yamllint" <workflow-file> && echo "PRESENT" || echo "ABSENT"
```

If `PRESENT`, check it does not install `yamllint` by `pip install yamllint` (a previous
version of this skill wrote that, and it pins nothing). If it does, replace the step with
the one below and say so; otherwise tell the user "Lint YAML step already in
`<workflow-file>` — skipped" and proceed to Step 5.

If `ABSENT`: check whether the job already installs `uv`:

```bash
grep -qE "astral-sh/setup-uv|install uv" <workflow-file> && echo "HAS_UV" || echo "NO_UV"
```

Locate the `steps:` block and append after the last `- name:` entry — with `NO_UV`, both
steps; with `HAS_UV`, the second only:

```yaml
      - uses: astral-sh/setup-uv@1c37ad07a6a961277cf70c0d37d6f313000f5884 # v10.3.0
      - name: Lint YAML
        run: <YAMLLINT_INVOCATION> .
```

Use **Edit** with the exact last `- name:` block text as `old_string`, appending the new step
after it. If the Edit fails (old_string not unique), re-read the file and retry with a longer
anchor string.

**Step 4b — Create new workflow:** **Write** `.github/workflows/lint.yml`:

```yaml
name: Lint

on:
  push:
    branches: [main]
  pull_request:

jobs:
  lint-yaml:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803 # v6
      - uses: astral-sh/setup-uv@1c37ad07a6a961277cf70c0d37d6f313000f5884 # v10.3.0
      - name: Lint YAML
        run: <YAMLLINT_INVOCATION> .
```

Both actions are pinned to a commit SHA with the tag as a trailing comment: a git tag is
mutable, so `@v6` alone is an unpinned third-party dependency in a workflow with repository
access.

---

## Step 5 — Smoke-test

Run yamllint against the scan path (default: `.`; use the argument if provided):

If a non-default path was given, verify it exists first:

```bash
test -e <path> && echo "EXISTS" || echo "PATH_MISSING"
```

If `PATH_MISSING`, stop: "ERROR: path `<path>` not found — verify the argument and re-run `/lint-yaml`."

```bash
<YAMLLINT_INVOCATION> <path> 2>&1 | tail -30
```

Count violations:

```bash
<YAMLLINT_INVOCATION> <path> 2>&1 | grep -c "^\s" || true
```

If yamllint exits cleanly with no output (empty directory or no YAML files at path), emit:
"No YAML files found at `<path>` — smoke-test found 0 violations."

If violations exist, report them as pre-existing — do not auto-fix.

---

## Completion states

| State | Trigger condition |
| --- | --- |
| **Success** | Config written, Claude Code hook wired, pre-commit hook wired, CI step added, smoke-test ran |
| **Success with violations** | Setup complete; smoke-test found pre-existing violations |
| **Aborted — already configured** | `.yamllint.yml` exists and user chose Abort |
| **Install failed** | `yamllint` install returned non-zero, or `uv` is missing without a Python lockfile |
| **Hook write failed** | `.claude/hooks/yaml-lint.py` could not be written |
| **Pre-commit YAML invalid** | `.pre-commit-config.yaml` is malformed after edit |

**Before emitting any completion output:** Read `${CLAUDE_SKILL_DIR}/output-templates.md` — use the matching template verbatim.

---

## Inputs

| Input | Required | Default | Notes |
| --- | --- | --- | --- |
| path | optional | `.` | Directory or glob to scan; passed as skill argument |

**Missing required input:** none — the skill runs against `.` by default.

---

## Calibration

- **Strong:** `${CLAUDE_SKILL_DIR}/examples.md` §Strong — all four artefacts written; smoke-test runs cleanly; output matches the template.
- **Weak:** `${CLAUDE_SKILL_DIR}/examples.md` §Weak — config written but pre-commit or CI step missing; smoke-test skipped.

## Standards and co-update partners

The single canonical authority for the shared Python-linter integration pattern (pre-commit hook format + GitHub Actions CI step) is `lint-md`
(<https://github.com/EqualExperts/ee-skills-incubator/blob/main/skills/lint-md/SKILL.md>)
— a separate plugin, so it is cited as an incubator URL rather than a `${CLAUDE_SKILL_DIR}`
path, which does not resolve across independently-installed plugins.

Co-update partner: `lint-md` — update both skills when hook block format, CI step format, or PostToolUse hook command template changes. When the hook script in Step 2.5 changes, update `.claude/hooks/yaml-lint.py` in the same PR.

User-facing documentation: `${CLAUDE_SKILL_DIR}/README.md`.
