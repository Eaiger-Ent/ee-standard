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
# A fourth, added 2026-08-28: the invocation is the register's pinned one,
# `tools.markdownlint-cli2.invocation`, the same string the pre-commit hook and
# the CI step reach the tool through. It was `npx --no-install` until then —
# which ADR 0020 measured falling through to PATH when the local install is
# missing, so a lockfile is an authority in name only. Every locus now spells it
# the same way, which is `docs/00-concepts.md` § Locus: pin once, reference many.
#
# This is the one divergence the skill will re-introduce. 1.0.8's
# local-config.md says `invocation` reaches "every locus ... the PostToolUse
# hook", but Step 3a is a plain `cp` of a script with npx hardcoded, so the
# configured value in .claude/skill-config.yaml never arrives here — filed as
# EqualExperts/ee-skills-incubator#627. Until that ships, this line is a
# hand-edit rather than configuration; Step 3a's skip branch leaves an existing
# hook alone, so a re-run will not revert it.
# See docs/00-concepts.md § The provenance stamp.
"""Lint (and auto-fix) a markdown file after Claude writes it."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

MARKDOWNLINT = ["node_modules/.bin/markdownlint-cli2"]


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
