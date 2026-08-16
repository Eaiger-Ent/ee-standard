"""Shared fixtures: throwaway git repositories and minimal valid registers."""

from __future__ import annotations

import copy
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

from standard_check.repo import Repo

REPO_ROOT = Path(__file__).resolve().parent.parent


def make_repo(root: Path, files: dict[str, str], commit: bool = True) -> Repo:
    """A throwaway git repository holding `files`."""
    root.mkdir(parents=True, exist_ok=True)
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    if commit:
        subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "-c",
                "user.name=test",
                "-c",
                "user.email=test@example.com",
                "commit",
                "-q",
                "--allow-empty",
                "-m",
                "fixture",
            ],
            check=True,
        )
    return Repo(root)


@pytest.fixture
def real_repo() -> Repo:
    return Repo(REPO_ROOT)


MINIMAL_CONTROL: dict[str, Any] = {
    "id": "SEC-001",
    "title": "A commit containing a secret cannot reach the remote",
    "enforces": "gitleaks runs as a pre-commit hook.",
    "standard": {"name": "OWASP", "url": "https://example.com/standard"},
    "tier": 1,
    "rung": "blocking",
    "locus": ["pre-commit", "ci"],
    "applies_to": ["always"],
    "verify": [{"kind": "file", "assert": "precommit_hook_present", "args": {"id": "gitleaks"}}],
    "owner": "platform-engineering",
    "variance": "forbidden",
    "baseline": None,
    "review_by": "2999-01-01",
    "rationale_adr": "docs/adr/0001-test.md",
}

MINIMAL_REGISTER: dict[str, Any] = {
    "version": "0.1.0",
    "meta": {"owner": "platform-engineering", "register_contract": 1},
    "predicates": {"always": True, "python": "pyproject.toml exists"},
    "controls": [MINIMAL_CONTROL],
    "meta_controls": [
        {
            "id": "GOV-003",
            "title": "No control is past its review date",
            "enforces": "No review_by is earlier than today.",
            "rationale": "Expiry forces the re-decision.",
            "verify": [{"kind": "command", "run": "standard-check meta GOV-003"}],
        }
    ],
}


def write_register(root: Path, register: dict[str, Any] | None = None) -> Path:
    """Write a register (default: the minimal valid one) plus its ADR file."""
    document = copy.deepcopy(register if register is not None else MINIMAL_REGISTER)
    root.mkdir(parents=True, exist_ok=True)
    adr = root / "docs/adr/0001-test.md"
    adr.parent.mkdir(parents=True, exist_ok=True)
    adr.write_text("# ADR 0001: Test\n", encoding="utf-8")
    path = root / "controls.yaml"
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    return path


def minimal_register(**overrides: Any) -> dict[str, Any]:
    """A deep copy of the minimal register with control-level overrides applied."""
    document = copy.deepcopy(MINIMAL_REGISTER)
    document["controls"][0].update(overrides)
    return document
