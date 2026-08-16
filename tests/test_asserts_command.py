"""Command assertions over workflow and configuration fixtures."""

from __future__ import annotations

from pathlib import Path

from conftest import make_repo
from standard_check.asserts_command import (
    actions_pinned_to_sha,
    ci_installs_frozen,
    no_failure_suppression,
    no_static_cloud_keys,
    typecheck_strict_and_blocking,
)
from standard_check.asserts_command import (
    tests_run_and_block as check_tests_run_and_block,  # aliased: pytest would collect the name
)

_SHA = "a" * 40


def _workflow(*runs: str, uses: str | None = None, suppressed: bool = False) -> str:
    steps = []
    if uses:
        steps.append(f"      - uses: {uses}\n")
    for run in runs:
        step = f"      - run: {run}\n"
        if suppressed:
            step += "        continue-on-error: true\n"
        steps.append(step)
    return "jobs:\n  job:\n    runs-on: ubuntu-latest\n    steps:\n" + "".join(steps)


def test_no_static_cloud_keys(tmp_path: Path) -> None:
    clean = make_repo(
        tmp_path / "a", {".github/workflows/ci.yml": _workflow("echo hello")}
    )
    assert no_static_cloud_keys(clean, {}).passed
    dirty = make_repo(
        tmp_path / "b",
        {
            ".github/workflows/ci.yml": _workflow(
                "aws configure set aws_access_key_id ${{ secrets.AWS_ACCESS_KEY_ID }}"
            )
        },
    )
    result = no_static_cloud_keys(dirty, {})
    assert not result.passed
    assert "AWS_ACCESS_KEY_ID" in result.message


def test_ci_installs_frozen(tmp_path: Path) -> None:
    frozen = make_repo(
        tmp_path / "a",
        {
            "pyproject.toml": "[project]\n",
            ".github/workflows/ci.yml": _workflow("uv sync --frozen", "uv run pytest"),
        },
    )
    assert ci_installs_frozen(frozen, {}).passed
    resolving = make_repo(
        tmp_path / "b",
        {
            "pyproject.toml": "[project]\n",
            ".github/workflows/ci.yml": _workflow("uv sync", "uv run pytest"),
        },
    )
    result = ci_installs_frozen(resolving, {})
    assert not result.passed
    assert "uv sync --frozen" in result.message
    unpinned_tool = make_repo(
        tmp_path / "c",
        {".github/workflows/ci.yml": _workflow("npm install -g markdownlint-cli2")},
    )
    assert not ci_installs_frozen(unpinned_tool, {}).passed
    pinned_tool = make_repo(
        tmp_path / "d",
        {".github/workflows/ci.yml": _workflow("npm install -g markdownlint-cli2@0.23.2")},
    )
    assert ci_installs_frozen(pinned_tool, {}).passed


def test_missing_python_install_fails_frozen_check(tmp_path: Path) -> None:
    repo = make_repo(
        tmp_path / "r",
        {
            "pyproject.toml": "[project]\n",
            ".github/workflows/ci.yml": _workflow("echo no install here"),
        },
    )
    result = ci_installs_frozen(repo, {})
    assert not result.passed
    assert "frozen" in result.message


def test_actions_pinned_to_sha(tmp_path: Path) -> None:
    pinned = make_repo(
        tmp_path / "a",
        {".github/workflows/ci.yml": _workflow("echo hi", uses=f"actions/checkout@{_SHA}")},
    )
    assert actions_pinned_to_sha(pinned, {}).passed
    tagged = make_repo(
        tmp_path / "b",
        {".github/workflows/ci.yml": _workflow("echo hi", uses="actions/checkout@v6")},
    )
    result = actions_pinned_to_sha(tagged, {})
    assert not result.passed
    assert "actions/checkout@v6" in result.message
    local = make_repo(
        tmp_path / "c",
        {".github/workflows/ci.yml": _workflow("echo hi", uses="./.github/actions/mine")},
    )
    assert actions_pinned_to_sha(local, {}).passed


def test_no_failure_suppression(tmp_path: Path) -> None:
    clean = make_repo(tmp_path / "a", {".github/workflows/ci.yml": _workflow("pytest")})
    assert no_failure_suppression(clean, {}).passed
    or_true = make_repo(
        tmp_path / "b", {".github/workflows/ci.yml": _workflow("pytest || true")}
    )
    assert not no_failure_suppression(or_true, {}).passed
    continue_on_error = make_repo(
        tmp_path / "c",
        {".github/workflows/ci.yml": _workflow("pytest", suppressed=True)},
    )
    assert not no_failure_suppression(continue_on_error, {}).passed


def test_tests_run_and_block(tmp_path: Path) -> None:
    good = make_repo(
        tmp_path / "a", {".github/workflows/ci.yml": _workflow("uv run pytest")}
    )
    assert check_tests_run_and_block(good, {}).passed
    none = make_repo(tmp_path / "b", {".github/workflows/ci.yml": _workflow("echo build")})
    assert not check_tests_run_and_block(none, {}).passed
    absorbed = make_repo(
        tmp_path / "c",
        {".github/workflows/ci.yml": _workflow("uv run pytest", suppressed=True)},
    )
    result = check_tests_run_and_block(absorbed, {})
    assert not result.passed
    assert "absorbed" in result.message


def test_typecheck_strict_and_blocking(tmp_path: Path) -> None:
    strict = make_repo(
        tmp_path / "a",
        {
            "pyproject.toml": "[project]\n[tool.mypy]\nstrict = true\n",
            ".pre-commit-config.yaml": (
                "repos:\n  - repo: local\n    hooks:\n"
                "      - id: mypy\n        entry: uv run mypy\n"
            ),
            ".github/workflows/ci.yml": _workflow("uv run mypy"),
        },
    )
    assert typecheck_strict_and_blocking(strict, {}).passed
    lax = make_repo(
        tmp_path / "b",
        {
            "pyproject.toml": "[project]\n[tool.mypy]\n",
            ".pre-commit-config.yaml": (
                "repos:\n  - repo: local\n    hooks:\n"
                "      - id: mypy\n        entry: uv run mypy\n"
            ),
            ".github/workflows/ci.yml": _workflow("uv run mypy"),
        },
    )
    result = typecheck_strict_and_blocking(lax, {})
    assert not result.passed
    assert "strict" in result.message
