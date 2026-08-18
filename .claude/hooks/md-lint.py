#!/usr/bin/env python3
# ee-control: DOC-001  ee-skill: lint-md@1.0.6  register: v0.5.0  register-contract: 5
#
# Deployed artefact — DOC-001's editor locus, as a PostToolUse hook. Hand-edited
# since deployment: it invokes markdownlint-cli2 through npx from the repository
# root so package-lock.json owns the version, it skips Claude's own memory
# files, and it conforms to this repository's ruff and mypy rules rather than
# sitting behind an exclusion. See docs/00-concepts.md § The provenance stamp.
"""Lint (and auto-fix) a markdown file after Claude writes it."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

MARKDOWNLINT = ["npx", "--no-install", "markdownlint-cli2"]


def main() -> int:
    payload = json.load(sys.stdin)
    target = payload.get("tool_input", {}).get("file_path", "")
    if not target.endswith(".md"):
        return 0
    path = Path(target)
    if not path.exists():
        return 0

    # Claude's auto-memory files (~/.claude/projects/*/memory/*.md) are managed
    # by Claude's memory system, not by this repo's markdown conventions.
    memory_root = Path.home() / ".claude" / "projects"
    if path.is_relative_to(memory_root) and "memory" in path.parts:
        return 0

    # DOC-001's tool resolves from package-lock.json, so npx must run with the
    # repository root as cwd — the hook fires on files anywhere, including
    # outside it.
    repo_root = Path(__file__).resolve().parents[2]

    # Auto-fix what markdownlint can repair on its own, then re-check for what
    # it cannot.
    subprocess.run([*MARKDOWNLINT, "--fix", str(path)], capture_output=True, cwd=repo_root)
    result = subprocess.run(
        [*MARKDOWNLINT, str(path)], capture_output=True, text=True, cwd=repo_root
    )
    output = (result.stdout + result.stderr).strip()

    if result.returncode != 0:
        print(
            f"\n\n⚠ STOP: markdownlint [{path.name}] has unfixable errors — "
            f"do not proceed until resolved.\n"
            f"Fix each issue listed below by editing {path}, then re-save:\n\n{output}\n"
        )
        return 1
    print(f"markdownlint [{path.name}]: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
