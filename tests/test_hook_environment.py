"""The suite runs safely from a git hook, which may export `GIT_DIR`.

`tests/conftest.py` `pytest_configure` records why: a pre-push hook run from a
worktree pointed every `git` in the suite at the real repository.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import REPO_ROOT, make_repo

_INNER = "REGISTER_CHECK_TEST_INNER_RUN"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def test_an_inherited_git_dir_reaches_no_repository(tmp_path: Path) -> None:
    """Runs the suite's own `make_repo` under a `GIT_DIR` naming a decoy.

    In a subprocess, because the fix acts as pytest starts. Setting the
    variable inside this process would come too late to test it.
    """
    decoy = make_repo(tmp_path / "decoy", {"README": "decoy\n"}).root
    head = _git(decoy, "rev-parse", "HEAD")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            f"{__file__}::test_make_repo_builds_its_own_repository",
        ],
        cwd=REPO_ROOT,
        env={**os.environ, "GIT_DIR": str(decoy / ".git"), _INNER: "1"},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert _git(decoy, "rev-parse", "HEAD") == head, "a fixture commit reached the decoy"
    assert _git(decoy, "config", "--get", "core.bare") == "false"


@pytest.mark.skipif(_INNER not in os.environ, reason="run only by the test above")
def test_make_repo_builds_its_own_repository(tmp_path: Path) -> None:
    root = make_repo(tmp_path / "fixture", {"f": "x\n"}).root
    assert (root / ".git").is_dir()
    assert _git(root, "log", "--format=%s") == "fixture"
