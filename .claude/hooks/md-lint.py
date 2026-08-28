#!/usr/bin/env -S uv run python
# ee-control: DOC-001  ee-skill: lint-md@1.0.8  register: v0.29.0  register-contract: 34
#
# Deployed artefact — DOC-001's editor locus, as a PostToolUse hook. The 1.0.8
# run on 2026-08-28 reconciled it and **skipped** it: Step 3a copies the
# release's own script verbatim, and that script is not what this file is. The
# stamp names 1.0.8 because that is the release this file was reconciled
# against, not because 1.0.8 wrote it — the divergences below are deliberate
# and each is a narrowing.
#
# Three of them. The shebang reads `-S uv run python` rather than the shipped
# `python3`, which in this container resolves to the base image's 3.13.5 and is
# below the floor (ADR 0028 revision 2, tests/test_toolchain_pin.py). It skips
# Claude's own memory files. And it conforms to this repository's ruff and mypy
# rules rather than sitting behind an exclusion.
#
# One divergence is NOT a narrowing and is owed upstream: the invocation. 1.0.8's
# local-config.md says `invocation` reaches "every locus ... the PostToolUse
# hook", but Step 3a is a plain copy of a script with npx hardcoded, so the
# configured value never arrives here. This file invokes npx too, from the
# repository root so package-lock.json still owns the version — the one locus
# where ADR 0020's row is open. See docs/00-concepts.md § The provenance stamp.
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
