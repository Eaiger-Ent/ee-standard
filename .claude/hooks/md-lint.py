#!/usr/bin/env -S uv run python
# ee-control: DOC-001  ee-skill: lint-md@1.0.9  register: v0.29.0  register-contract: 35
#
# Deployed artefact — DOC-001's editor locus, as a PostToolUse hook. Written by
# `lint-md` 1.0.9 on 2026-08-28: Step 3a copies the release's own script and
# then writes `invocation` from .claude/skill-config.yaml into it.
#
# It is a deployment rather than a reconciliation, and that is the news. Until
# 1.0.9 this file carried four deliberate divergences from the shipped script —
# the `-S uv run python` shebang, a skip for Claude's own memory files,
# conformance with this repository's ruff and mypy rules, and the register's
# pinned invocation in place of `npx --no-install`. All four are now upstream:
# 1.0.9 ships the shebang and the memory skip, its script passes `uv run ruff
# check` and `uv run mypy` here unedited, and Step 3a substitutes the invocation
# instead of hardcoding npx. That last one was
# EqualExperts/ee-skills-incubator#627, filed against 1.0.8 and fixed here.
#
# So there is nothing left hand-edited below, and the stamp means what it says:
# 1.0.9 wrote this file. Do not re-introduce a divergence without recording it
# here — the previous four were each a narrowing, and each was named.
# See docs/00-concepts.md § The provenance stamp.
"""PostToolUse hook: auto-fix Markdown files with markdownlint-cli2, block on the rest."""

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
LINT_INVOCATION = "node_modules/.bin/markdownlint-cli2"

LINT = shlex.split(LINT_INVOCATION)


def find_repo_root(start: Path) -> Path:
    """Nearest ancestor containing .git — where package-lock.json and node_modules live."""
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    return start


def main() -> int:
    payload = json.load(sys.stdin)
    file_arg = str(payload.get("tool_input", {}).get("file_path", ""))
    target = Path(file_arg)

    if target.suffix != ".md" or not target.exists():
        return 0

    # Claude's auto-memory files (~/.claude/projects/*/memory/*.md) are managed
    # by Claude's memory system, not this repo's markdown conventions.
    memory_root = Path.home() / ".claude" / "projects"
    if target.is_relative_to(memory_root) and "memory" in target.parts:
        return 0

    # Run from the repository root so the lockfile-pinned install resolves
    # regardless of where the edited file lives. This matters for both spellings:
    # `npx` searches upwards for node_modules, and a relative invocation such as
    # `node_modules/.bin/markdownlint-cli2` resolves against the cwd.
    repo_root = find_repo_root(target.resolve().parent)

    # Auto-fix what markdownlint can repair on its own.
    subprocess.run(
        [*LINT, "--fix", str(target)],
        capture_output=True,
        cwd=repo_root,
        check=False,
    )

    # Re-check for anything that couldn't be auto-fixed.
    result = subprocess.run(
        [*LINT, str(target)],
        capture_output=True,
        text=True,
        cwd=repo_root,
        check=False,
    )
    findings = (result.stdout + result.stderr).strip()

    if result.returncode != 0:
        print(
            f"\n\n⚠ STOP: markdownlint [{target.name}] has unfixable errors — "
            f"do not proceed until resolved.\n"
            f"Fix each issue listed below by editing {target}, then re-save:\n\n{findings}\n"
        )
        return 1

    print(f"markdownlint [{target.name}]: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
