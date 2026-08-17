"""The meta-controls: GOV-001, GOV-002, GOV-003."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from conftest import make_repo, minimal_register, write_register
from standard_check.meta import gov_001, gov_002, gov_003
from standard_check.register import Register, load_register
from standard_check.repo import Repo


def _load(root: Path, document: dict[str, Any]) -> tuple[Register, Repo]:
    path = write_register(root, document)
    register, errors = load_register(path)
    assert errors == [], errors
    assert register is not None
    return register, Repo(root)


_WORKFLOW_FULL_RUN = (
    "jobs:\n  check:\n    runs-on: ubuntu-latest\n    steps:\n"
    "      - run: uv run standard-check\n"
)


def test_gov_001_passes_when_checker_runs_in_ci(tmp_path: Path) -> None:
    register, repo = _load(tmp_path, minimal_register())
    make_repo(tmp_path, {".github/workflows/check.yml": _WORKFLOW_FULL_RUN})
    passed, _message = gov_001(register, repo)
    assert passed


def test_gov_001_fails_with_no_reachable_step(tmp_path: Path) -> None:
    register, repo = _load(tmp_path, minimal_register())
    make_repo(tmp_path, {".github/workflows/check.yml": "jobs: {}\n"})
    passed, message = gov_001(register, repo)
    assert not passed
    assert "SEC-001" in message


def test_gov_001_ignores_suppressed_steps(tmp_path: Path) -> None:
    register, repo = _load(tmp_path, minimal_register())
    workflow = (
        "jobs:\n  check:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - run: uv run standard-check\n"
        "        continue-on-error: true\n"
    )
    make_repo(tmp_path, {".github/workflows/check.yml": workflow})
    passed, _message = gov_001(register, repo)
    assert not passed


def _commit(root: Path, message: str) -> None:
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
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
            "-m",
            message,
        ],
        check=True,
    )


def test_gov_002_fails_when_a_baseline_grows(tmp_path: Path) -> None:
    document = minimal_register(tier=2, baseline="baselines/sec.txt")
    register, repo = _load(tmp_path, document)
    make_repo(tmp_path, {"baselines/sec.txt": "one\n"})
    baseline = tmp_path / "baselines/sec.txt"
    passed, _message = gov_002(register, repo)
    assert passed
    baseline.write_text("one\ntwo\n", encoding="utf-8")
    passed, message = gov_002(register, repo)
    assert not passed
    assert "1 → 2" in message
    # Shrinking is always fine.
    baseline.write_text("", encoding="utf-8")
    _commit(tmp_path, "shrink")
    passed, _message = gov_002(register, repo)
    assert passed


def test_gov_002_fails_when_growth_is_committed(tmp_path: Path) -> None:
    """The CI case: growth is always committed by the time the checker sees it."""
    document = minimal_register(tier=2, baseline="baselines/sec.txt")
    register, repo = _load(tmp_path, document)
    make_repo(tmp_path, {"baselines/sec.txt": "one\n"})
    (tmp_path / "baselines/sec.txt").write_text("one\ntwo\n", encoding="utf-8")
    _commit(tmp_path, "grow the baseline")
    passed, message = gov_002(register, repo)
    assert not passed
    assert "1 → 2" in message


def test_gov_002_fails_when_growth_is_on_a_branch(tmp_path: Path) -> None:
    """The pull-request case: compare against the merge-base, not the branch tip."""
    document = minimal_register(tier=2, baseline="baselines/sec.txt")
    register, repo = _load(tmp_path, document)
    make_repo(tmp_path, {"baselines/sec.txt": "one\n"})
    subprocess.run(["git", "-C", str(tmp_path), "checkout", "-q", "-b", "feature"], check=True)
    (tmp_path / "baselines/sec.txt").write_text("one\ntwo\nthree\n", encoding="utf-8")
    _commit(tmp_path, "grow on a branch")
    passed, message = gov_002(register, repo)
    assert not passed
    assert "1 → 3" in message


def test_gov_002_passes_when_a_committed_change_shrinks(tmp_path: Path) -> None:
    document = minimal_register(tier=2, baseline="baselines/sec.txt")
    register, repo = _load(tmp_path, document)
    make_repo(tmp_path, {"baselines/sec.txt": "one\ntwo\n"})
    (tmp_path / "baselines/sec.txt").write_text("one\n", encoding="utf-8")
    _commit(tmp_path, "shrink the baseline")
    passed, _message = gov_002(register, repo)
    assert passed


def test_gov_003_fails_past_review_date(tmp_path: Path) -> None:
    register, repo = _load(tmp_path, minimal_register(review_by="2001-01-01"))
    make_repo(tmp_path, {})
    passed, message = gov_003(register, repo)
    assert not passed
    assert "SEC-001" in message


def test_gov_003_passes_before_review_date(tmp_path: Path) -> None:
    register, repo = _load(tmp_path, minimal_register())
    make_repo(tmp_path, {})
    passed, _message = gov_003(register, repo)
    assert passed
