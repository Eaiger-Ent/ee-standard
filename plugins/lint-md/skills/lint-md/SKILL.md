---
name: lint-md
description: >
  Set up markdownlint-cli2: installs linter, writes config, wires PostToolUse
  hook, pre-commit hook, and CI step. Migrates from pymarkdownlnt. Triggers:
  'lint markdown', 'set up markdown linting', 'add markdownlint', '/lint-md'.
argument-hint: "[path]"
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
---

# /lint-md — Markdown Linting Setup

You are running the **lint-md** skill. Install `markdownlint-cli2`, drop a config file,
wire a PostToolUse Claude Code hook for real-time auto-fix, a pre-commit hook, and a
GitHub Actions CI step. Migrate from `pymarkdownlnt` if it is already present.

**Do not use when:**

- `.markdownlint.yaml` already exists and the user does not want to overwrite it.
- The project uses `remark` — adding a second linter creates conflicts.
- You only need to run the linter once; call `<CLI2_INVOCATION> "**/*.md"` directly.

---

## Pre-flight — detect current state

Run all checks before making any changes. Any file this skill writes (config, hook script,
pre-commit block, workflow step) that is found zero-byte or truncated — e.g. from an
interrupted prior run — is treated as absent and overwritten in the relevant Step without
prompting, since there is no existing content to lose.

1. **Detect existing markdownlint config:**

   ```bash
   bash "${CLAUDE_SKILL_DIR}/scripts/md-config-state.sh"
   ```

   - `EXISTS_MARKDOWNLINT` or `EXISTS_MARKDOWNLINT_JSON`: ask the user via **AskUserQuestion**:
     "`.markdownlint.yaml` already exists. Overwrite and reconfigure, or abort?"
     Options: Overwrite / Abort. If Abort, stop here and emit the **Aborted** template.
     **First read the file's opening comments.** If a line begins `ee-control:` the file
     is a deployed artefact carrying a provenance record — which control owns it, which
     skill wrote it and at what version. Say so in the question and quote the line, so
     the person choosing Overwrite knows a record is being discarded and not just a rule
     set. Overwrite still overwrites; this only stops it happening unknowingly.
   - `EXISTS_MARKDOWNLINT_EMPTY`: per the general empty-file rule above — treat as `ABSENT`.

2. **Detect legacy pymarkdownlnt setup:**

   ```bash
   test -f .pymarkdown.json && echo "LEGACY_FOUND" || echo "ABSENT"
   ```

   Store as `LEGACY_STATE`. If `LEGACY_FOUND`, note that a migration step will run after
   the main setup to clean up the old tooling.

3. **Check remaining tool/file state** — run each command below and store the result:

   | State var | Command |
   | --- | --- |
   | `CLI2_INVOCATION`, `CLI2_IGNORES` | read `${CLAUDE_SKILL_DIR}/local-config.md` and follow it — the repository may pin what this skill writes, and an absent file means every default |
   | `CLI2_STATE` | `<CLI2_INVOCATION> --version 2>/dev/null && echo INSTALLED \|\| echo NEEDS_INSTALL` |
   | `DEVCONTAINER_STATE` | `test -f .devcontainer/setup.sh && echo EXISTS \|\| echo ABSENT` |
   | `PRECOMMIT_STATE` | `test -f .pre-commit-config.yaml && echo EXISTS \|\| echo ABSENT` |
   | workflow list (Step 5) | `ls .github/workflows/ 2>/dev/null \|\| echo NONE` |
   | `HOOK_STATE` | `test -f .claude/hooks/md-lint.py && echo EXISTS \|\| echo ABSENT` |
   | `CLI2_IGNORES_STATE` | `test -f .markdownlint-cli2.yaml && echo EXISTS \|\| echo ABSENT` |

---

## Step 1 — Install markdownlint-cli2

**If `CLI2_STATE` is `INSTALLED`:** skip the npm install; proceed to Step 1b.

**If `CLI2_STATE` is `NEEDS_INSTALL`:** install as an exact-pinned dev dependency, so the
version is recorded in `package.json` and `package-lock.json` — the lockfile is the single
authority every other locus resolves through. If the project has no `package.json` yet,
create one first:

```bash
test -f package.json || npm init -y
npm install --save-dev --save-exact markdownlint-cli2
```

Verify:

```bash
<CLI2_INVOCATION> --version
```

If the install fails (non-zero exit or `command not found`), stop and show the user the
exact error output. Do not proceed.

### Step 1b — DevContainer setup.sh

If `DEVCONTAINER_STATE` is `EXISTS`: read `.devcontainer/setup.sh` and check whether
the lockfile install is already present:

```bash
grep -qE "npm ci|markdownlint-cli2" .devcontainer/setup.sh && echo "PRESENT" || echo "ABSENT"
```

If `ABSENT`: insert a new line after any existing `npm install` block. `npm ci` reads
`package-lock.json` and cannot re-resolve, so new containers get exactly the pinned version:

```bash
npm ci
```

Tell the user: "Added `npm ci` to `.devcontainer/setup.sh` — new containers will install the locked markdownlint-cli2."

If `DEVCONTAINER_STATE` is `ABSENT`: tell the user:

```text
No .devcontainer/setup.sh found. To pre-install in future containers, add to your setup script:
  npm ci
```

---

## Step 2 — Write .markdownlint.yaml

**Write** `.markdownlint.yaml`:

```yaml
default: true
MD013:
  line_length: 250
  code_blocks: false
  tables: false
MD024:
  siblings_only: true
MD050:
  style: asterisk
MD060:
  style: compact
```

After writing, verify the file is non-empty:

```bash
test -s .markdownlint.yaml && echo "OK" || echo "WRITE_FAILED"
```

If `WRITE_FAILED`, stop: "`.markdownlint.yaml` was not written correctly — please re-run `/lint-md`."

Rule rationale (tell the user after writing):

- `MD013` (line-length) — capped at 250 chars; code blocks and tables exempt.
- `MD024` (no-duplicate-heading) — `siblings_only: true` permits repeated headings under different parent sections.
- `MD060` (table-column-style) — `compact` enforces `| --- | --- |` separator style.
- `MD050` (strong-style) — pinned to `asterisk` instead of the default `consistent`, which
  only matches whichever style a file happens to use first and misses bare dunder identifiers
  (`__init__.py`, `__tests__`) that markdown-it parses as strong emphasis whenever correctly
  flanked. Wrap them in backticks. Exception: structured-data `.md` files (e.g. YAML-parsed
  pipeline-registry docs) — add an ignore entry to `.markdownlint-cli2.yaml` instead (Step 2b),
  since backticks there are real command-substitution syntax.

---

## Step 2b — Write .markdownlint-cli2.yaml (scan ignores)

`<CLI2_INVOCATION> "**/*.md"` scans every `.md` file, including `node_modules/` and `.claude/`
caches. Without an ignore config, the smoke-test and CI step will report thousands of violations
from third-party files.

`CLI2_IGNORES` is what to write — the repository's list if it set one, else the
default. **Write it verbatim**; do not merge it with the default, because a
repository that sets `ignores: []` means *ignore nothing*.

**If `CLI2_IGNORES_STATE` is `EXISTS`:** read `.markdownlint-cli2.yaml` and compare its
`ignores` list with `CLI2_IGNORES`. The script **parses the YAML rather than grepping it**
and prints the list as a JSON array:

```bash
uv run --script "${CLAUDE_SKILL_DIR}/scripts/read-cli2-ignores.py"
```

- If the two lists match: tell the user "`.markdownlint-cli2.yaml` already has the wanted
  `ignores` — skipped." and proceed to Step 3.
- Otherwise: use **Edit** to make the `ignores` list `CLI2_IGNORES`, and say which entries
  were added and which removed.

**If `CLI2_IGNORES_STATE` is `ABSENT`:** **Write** `.markdownlint-cli2.yaml` with
`gitignore: true` and `ignores` set to `CLI2_IGNORES` verbatim. The default list is
in `local-config.md` and is not repeated here — one copy, so the two cannot drift.

After writing, verify the file is non-empty:

```bash
test -s .markdownlint-cli2.yaml && echo "OK" || echo "WRITE_FAILED"
```

If `WRITE_FAILED`, stop: "`.markdownlint-cli2.yaml` was not written — please re-run `/lint-md`."

---

## Step 3 — Install PostToolUse Claude Code hook

This wires `markdownlint-cli2 --fix` to run automatically whenever Claude writes or edits
a Markdown file — silently repairing auto-fixable issues and surfacing unfixable ones.

### Step 3a — Write the hook script

Create the hooks directory if it does not exist:

```bash
mkdir -p .claude/hooks
```

If `HOOK_STATE` is `EXISTS`, ask whether that copy is still the script it was copied
from. "It mentions the linter" is not that question: a fix to the canonical script leaves
an older copy running, and a name test still reports it as present (#842).

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check-hook-freshness.py" "${CLAUDE_SKILL_DIR}/scripts/md-lint-hook.py" .claude/hooks/md-lint.py
```

The comparison ignores the `LINT_INVOCATION` line, which the deployed copy is rewritten below to differ by.

- `FRESH` — already matches. Skip the `cp` below, but still run the `LINT_INVOCATION`
  write and its verification: that line is ignored above, so a changed `CLI2_INVOCATION`
  looks identical. Tell the user the hook was already up to date.
- `STALE` — an older version of this script; the `cp` below replaces it. Name the file
  overwritten, so a local edit to it is not lost silently.
- `ABSENT` — no copy yet. Continue as a first install.

Copy the hook script from the skill's scripts directory:

```bash
cp "${CLAUDE_SKILL_DIR}/scripts/md-lint-hook.py" .claude/hooks/md-lint.py
```

**Then write `CLI2_INVOCATION` into it.** The copied script carries the default
invocation, and a copy is not a deployment: every other locus takes the
configured value, and this one is named in `local-config.md` alongside them. Use
**Edit** to replace the whole `LINT_INVOCATION` line:

```python
LINT_INVOCATION = "<CLI2_INVOCATION>"
```

If `CLI2_INVOCATION` is the default the line is already correct — say
"skipped, already the default" rather than rewriting it. Verify the value landed,
so a failed Edit is not reported as a deployment:

```bash
grep -q "^LINT_INVOCATION = \"<CLI2_INVOCATION>\"$" .claude/hooks/md-lint.py \
  && echo "OK" || echo "INVOCATION_NOT_WRITTEN"
```

If `INVOCATION_NOT_WRITTEN`, stop: "`.claude/hooks/md-lint.py` still carries the
default invocation — the configured value was not applied. Re-run `/lint-md`."

Verify the file was written:

```bash
test -s .claude/hooks/md-lint.py && echo "OK" || echo "WRITE_FAILED"
```

If `WRITE_FAILED`, stop: "`.claude/hooks/md-lint.py` was not written — please re-run `/lint-md`."

### Step 3b — Register in .claude/settings.json

Read `.claude/settings.json` if it exists, or treat it as `{}`.

Check whether a `PostToolUse` entry for `md-lint.py` already exists:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check-hook-registered.py" md-lint.py
```

If `ABSENT`, merge the new entry into the settings:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/wire-settings-hook.py" md-lint.py
```

Verify the file is valid JSON after writing:

```bash
uv run --script "${CLAUDE_SKILL_DIR}/scripts/validate-config.py" .claude/settings.json
```

If the output starts `INVALID`, show the user the parse error it names and restore the
original content.

---

## Step 4 — Wire pre-commit hook

The hook is a `repo: local` entry running the same `npx` command as every other locus, so
the version resolves from `package-lock.json` — there is no `rev:` copy to keep in step.

The hook block:

```yaml
  - repo: local
    hooks:
      - id: markdownlint-cli2
        name: markdownlint-cli2
        entry: <CLI2_INVOCATION>
        language: system
        types: [markdown]
```

**If `.pre-commit-config.yaml` exists:** read it first and validate it is parseable:

```bash
uv run --script "${CLAUDE_SKILL_DIR}/scripts/validate-config.py" .pre-commit-config.yaml
```

If the output starts `INVALID`, stop: "ERROR: `.pre-commit-config.yaml` is empty or
malformed — repair it manually and re-run `/lint-md`."

Check what is already present:

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/md-precommit-state.sh"
```

If `LEGACY_PINNED` (an older `repo: https://github.com/DavidAnson/markdownlint-cli2` block
with a `rev:` pin, written by a previous version of this skill): use **Edit** to replace
that repo block with the `repo: local` block above — leaving it would keep a second,
hand-kept copy of the version that drifts from the lockfile.

If `PRESENT`: tell the user "markdownlint-cli2 hook already in `.pre-commit-config.yaml` —
skipped" and proceed to Step 5.

If `ABSENT`: use **Edit** to append the block after the last existing repo entry.

**If `.pre-commit-config.yaml` does not exist:** **Write** it from scratch:

```yaml
repos:
  - repo: local
    hooks:
      - id: markdownlint-cli2
        name: markdownlint-cli2
        entry: <CLI2_INVOCATION>
        language: system
        types: [markdown]
```

After writing, validate it is parseable:

```bash
uv run --script "${CLAUDE_SKILL_DIR}/scripts/validate-config.py" .pre-commit-config.yaml
```

If the output starts `INVALID`, show the parse error it names and stop.

---

## Step 5 — Add GitHub Actions CI step

Select a target workflow:

- Prefer `ci.yml`, `lint.yml`, `build.yml` — in that order — from the list found in Pre-flight.
- If none of those exist but another workflow file is present, use the first one listed.
- If no workflow files exist at all, create `.github/workflows/lint.yml` (Step 5b).

**Step 5a — Add step to existing workflow:** Read the file. Check if the step already exists:

```bash
grep -q "markdownlint-cli2" <workflow-file> && echo "PRESENT" || echo "ABSENT"
```

If `PRESENT`: tell the user "markdownlint-cli2 step already in `<workflow-file>` — skipped"
and proceed to Step 6.

Otherwise: append after the last `- name:` entry:

```yaml
      - name: Lint Markdown
        run: |
          npm ci
          <CLI2_INVOCATION> "**/*.md"
```

**Step 5b — Create new workflow:** **Write** `.github/workflows/lint.yml`:

```yaml
name: Lint

on:
  push:
    branches: [main]
  pull_request:

jobs:
  lint-md:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803 # v6
      - name: Lint Markdown
        run: |
          npm ci
          <CLI2_INVOCATION> "**/*.md"
```

The `actions/checkout` pin is a commit SHA with the tag as a trailing comment: a git tag is
mutable, so `@v6` alone is an unpinned third-party dependency in a workflow with repository
access.

---

## Step 6 — Smoke-test

Run markdownlint-cli2 against the scan path (default: `"**/*.md"`; use the argument if
provided, appended as a glob):

If a non-default path was given, verify it exists first:

```bash
test -e <path> && echo "EXISTS" || echo "PATH_MISSING"
```

If `PATH_MISSING`, stop: "ERROR: path `<path>` not found — verify the argument and re-run `/lint-md`."

```bash
<CLI2_INVOCATION> "**/*.md" 2>&1 | tail -30
```

Count violations:

```bash
<CLI2_INVOCATION> "**/*.md" 2>&1 | grep -c " error " || true
```

If violations exist, report them as pre-existing — do not auto-fix at this stage (the hook
will handle future writes).

---

## Migration — remove pymarkdownlnt (if LEGACY_STATE is LEGACY_FOUND)

If `LEGACY_STATE` is `LEGACY_FOUND`, read `${CLAUDE_SKILL_DIR}/migration.md` and run
its five removal steps (config file, pre-commit block, workflow step, package
manifest, confirmation) before reporting completion. If `LEGACY_STATE` is anything
else, skip this section entirely.

---

## Completion states

| State | Trigger condition |
| --- | --- |
| ✅ **Success** | Config written, hook installed, pre-commit wired, CI step added, smoke-test ran |
| ⚠️ **Success with violations** | Setup complete; smoke-test found pre-existing violations |
| ✅ **Success with migration** | As above; pymarkdownlnt also removed |
| ⚠️ **Aborted — already configured** | `.markdownlint.yaml` exists and user chose Abort |
| ❌ **Install failed** | `markdownlint-cli2` install returned non-zero |
| ❌ **Pre-commit YAML invalid** | `.pre-commit-config.yaml` is malformed after edit |

**Verdict field:** `lint-md:` — possible values: `success` | `success-with-violations` | `success-with-migration` | `aborted` | `install-failed` | `pre-commit-yaml-invalid`

**Before emitting any completion output:** Read `${CLAUDE_SKILL_DIR}/output-templates.md` — use the matching template verbatim.

---

## Inputs

No required inputs — every input is optional and falls back to its default.

| Input | Required | Default | Notes |
| --- | --- | --- | --- |
| path | optional | `"**/*.md"` | Glob or directory to scan; passed as skill argument |

---

## Idempotency

Re-running on an already fully configured project (every pre-flight check returns
`PRESENT`/`INSTALLED`/`EXISTS`) is a safe no-op: each step's skip branch fires, no files are
rewritten, and the **Success** template is emitted with `— skipped` noted next to each
already-present artefact.

## Calibration

- **Strong:** `${CLAUDE_SKILL_DIR}/examples.md` §Strong — all seven artefacts present; smoke-test clean; output matches the template.
- **Weak:** `${CLAUDE_SKILL_DIR}/examples.md` §Weak — config written but hook, pre-commit, or CI step missing.

## Standards and co-update partners

`lint-md` is the canonical source for the shared Node-linter integration pattern used by
this skill family. Co-update partner: `lint-yaml`
(<https://github.com/EqualExperts/ee-skills-incubator/blob/main/skills/lint-yaml/SKILL.md>)
— a separate plugin, so it is cited as an incubator URL rather than a `${CLAUDE_SKILL_DIR}`
path, which does not resolve across independently-installed plugins. Shares the same
pre-commit and CI step structure; update both when hook block format or CI step format
changes. When the hook script in Step 3 changes, update `.claude/hooks/md-lint.py` in the
same PR.

User-facing documentation: `${CLAUDE_SKILL_DIR}/README.md`.
