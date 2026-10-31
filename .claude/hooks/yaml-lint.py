#!/usr/bin/env -S uv run python
"""PostToolUse hook: lint YAML files with yamllint and report what it finds."""

import json
import shlex
import subprocess
import sys
from pathlib import Path

# The invocation this skill was configured with — `invocation` in
# .claude/skill-config.yaml, see local-config.md. Step 2.5a rewrites this one line at
# deploy time; the string below is the default, which is what a repository that
# configures nothing gets. It is also the only line a deployed copy of this file may
# differ by, which is what scripts/check-hook-deployments.py compares modulo (#842).
#
# Kept as a single string rather than a list so the substitution is a whole-line
# replacement: a configured value is a command line, not a token.
LINT_INVOCATION = "uv run yamllint"

LINT = shlex.split(LINT_INVOCATION)

# What to call the thing in the hook's own output. A configured invocation need not be
# yamllint at all, and a line that says "yamllint" over the output of something else sends
# the reader to the wrong tool's documentation.
# The tool is the first token that names yamllint, not the first token: in `uv run yamllint`
# or `uvx --from yamllint==1.38.0 yamllint` the first token is the runner.
TOOL = next(
    (Path(token).name for token in LINT if Path(token).name == 'yamllint'),
    Path(LINT[0]).name if LINT else 'yaml-lint',
)


# Repo-scope guard (#664). A PostToolUse hook is handed every Write/Edit the session
# makes, including files this repository has no authority over: a dotfile in $HOME,
# Claude's auto-memory, a file in a different checkout. Linting one of those applies
# this repository's .yamllint.yml to a foreign file. So anything outside the
# repository is skipped.
#
# The repository is resolved from the working directory — the registered command cds
# to the git toplevel before invoking the hook — and deliberately not from the edited
# file, whose own nearest .git may be a different repository, or none at all.
def in_repo(target: Path) -> bool:
    start = Path.cwd().resolve()
    root = next((c for c in (start, *start.parents) if (c / '.git').exists()), None)
    if root is None:
        return False
    try:
        return target.resolve().is_relative_to(root)
    except OSError:
        return False


d = json.load(sys.stdin)
f = d.get('tool_input', {}).get('file_path', '')

if not (f.endswith('.yml') or f.endswith('.yaml')) or not Path(f).exists():
    sys.exit(0)

if not in_repo(Path(f)):
    sys.exit(0)

cfg = '.yamllint.yml'
args = ['-c', cfg] if Path(cfg).exists() else []
r = subprocess.run(LINT + args + [f], capture_output=True, text=True)
out = (r.stdout + r.stderr).strip()

if r.returncode != 0:
    print(f'{TOOL} [{Path(f).name}] — reported:\n{out}')
else:
    print(f'{TOOL} [{Path(f).name}]: OK')
