#!/usr/bin/env -S uv run python
"""PostToolUse hook: auto-fix Markdown with markdownlint-cli2, block on the rest."""

import json
import shlex
import subprocess
import sys
from pathlib import Path

# The invocation this skill was configured with — `invocation` in
# .claude/skill-config.yaml, see local-config.md. Step 3a rewrites this one line
# at deploy time; the string below is the default, which is what a repository
# that configures nothing gets.
#
# Kept as a single string rather than a tuple so the substitution is a
# whole-line replacement. A configured value is a command line, not a token:
# "node_modules/.bin/markdownlint-cli2" is one word and the default is three.
LINT_INVOCATION = "npx --no-install markdownlint-cli2"

LINT = shlex.split(LINT_INVOCATION)


def repo_root() -> Path | None:
    """Nearest ancestor of the cwd containing .git, or None when there is no repository.

    Resolved from the working directory — the registered command cds to the git
    toplevel before invoking the hook — and deliberately not from the edited file,
    whose own nearest .git may be a different repository, or none at all.
    """
    start = Path.cwd().resolve()
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def main() -> int:
    payload = json.load(sys.stdin)
    file_arg = str(payload.get("tool_input", {}).get("file_path", ""))
    target = Path(file_arg)

    if target.suffix != ".md" or not target.exists():
        return 0

    # Repo-scope guard (#409, #664). A PostToolUse hook is handed every Write/Edit the
    # session makes, including files this repository has no authority over: Claude's
    # auto-memory under ~/.claude/projects/*/memory/, a dotfile in $HOME, a file in a
    # different checkout. Linting one of those applies this repository's rules and its
    # markdownlint config to a foreign file, the --fix pass rewrites it in place, and a
    # non-zero exit blocks the session over a file the session cannot correct here.
    root = repo_root()
    if root is None:
        return 0
    try:
        if not target.resolve().is_relative_to(root):
            return 0
    except OSError:
        return 0

    # Run from the repository root so the lockfile-pinned install resolves
    # regardless of where the edited file lives. This matters for both spellings:
    # `npx` searches upwards for node_modules, and a relative invocation such as
    # `node_modules/.bin/markdownlint-cli2` resolves against the cwd.

    # Auto-fix what markdownlint can repair on its own.
    subprocess.run(
        [*LINT, "--fix", str(target)],
        capture_output=True,
        cwd=root,
        check=False,
    )

    # Re-check for anything that couldn't be auto-fixed.
    result = subprocess.run(
        [*LINT, str(target)],
        capture_output=True,
        text=True,
        cwd=root,
        check=False,
    )
    findings = (result.stdout + result.stderr).strip()

    if result.returncode != 0:
        print(
            f"\n\n⚠ STOP: markdownlint [{target.name}] has unfixable errors — "
            f"do not proceed until resolved.\n"
            f"Fix each issue listed below by editing {target}, then re-save:\n\n"
            f"{findings}\n"
        )
        return 1

    print(f"markdownlint [{target.name}]: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
