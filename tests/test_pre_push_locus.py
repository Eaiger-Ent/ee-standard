"""The `pre-push` locus: a hook's stage decides which moment it serves.

ADR 0039. Two of the register's loci live in `.pre-commit-config.yaml`, and
until contract 31 nothing asked which stage a hook ran at — harmless while
`pre-commit` was the only local locus, and not harmless once a second one
exists. These tests hold the separation in both directions, because a checker
that read every hook as a pre-commit hook would credit the wrong moment and one
that read `stages:` as required would fail a repository that is genuinely wired.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from conftest import REPO_ROOT, a_register, make_repo, register_with
from register_check.asserts_command import gate_wired_at_declared_loci
from register_check.asserts_command import (
    tests_run_and_block as check_tests_run_and_block,  # aliased: pytest would collect it
)
from register_check.asserts_file import CONTROL_ARG
from register_check.register import LOCI

_GATING = (
    "on: [push, pull_request]\njobs:\n  job:\n    runs-on: ubuntu-latest\n"
    "    steps:\n      - run: uv run pytest\n"
)


def _config(*hooks: str, default_stages: str | None = None) -> str:
    head = f"default_stages: [{default_stages}]\n" if default_stages else ""
    return head + "repos:\n  - repo: local\n    hooks:\n" + "".join(hooks)


def _hook(hook_id: str, entry: str, stages: str | None = None) -> str:
    text = f"      - id: {hook_id}\n        entry: {entry}\n        language: system\n"
    if stages:
        text += f"        stages: [{stages}]\n"
    return text


def _tst_001(repo: Any) -> Any:
    return check_tests_run_and_block(repo, a_register(), {CONTROL_ARG: "TST-001"})


def test_pre_push_is_a_locus_the_register_knows() -> None:
    """The vocabulary itself, so the value cannot be removed without a failure."""
    assert LOCI == ("editor", "pre-commit", "pre-push", "ci", "remote")


def test_a_hook_staged_for_a_push_does_not_serve_the_commit_locus(tmp_path: Path) -> None:
    """The reason stages are read at all.

    SUP-003 declares `[pre-commit, ci]`. A hook that runs only before a push
    satisfies neither claim it makes about commits, and before contract 31 the
    checker would have credited it, because it read every hook in the file.
    """
    repo = make_repo(
        tmp_path,
        {
            ".pre-commit-config.yaml": _config(
                _hook("sup", "uv run register-check run --control SUP-003", stages="pre-push")
            ),
            ".github/workflows/ci.yml": (
                "on: [push, pull_request]\njobs:\n  job:\n    runs-on: ubuntu-latest\n"
                "    steps:\n      - run: uv run register-check\n"
            ),
        },
    )
    result = gate_wired_at_declared_loci(
        repo, a_register(), {"tool": "register-check", CONTROL_ARG: "SUP-003"}
    )
    assert not result.passed
    assert "pre-commit locus" in result.message


def test_a_hook_that_names_no_stage_serves_both(tmp_path: Path) -> None:
    """pre-commit's own rule, not a convenience.

    An absent `stages` runs at every stage the repository has installed. Reading
    the absence as `pre-commit` would fail a locus that is in fact wired, which
    is the opposite error and just as wrong.
    """
    repo = make_repo(
        tmp_path,
        {
            ".pre-commit-config.yaml": _config(_hook("tests", "uv run pytest")),
            ".github/workflows/ci.yml": _GATING,
        },
    )
    assert _tst_001(repo).passed


def test_default_stages_narrows_a_hook_that_names_none(tmp_path: Path) -> None:
    """The file-level key this repository uses to keep the two moments apart.

    With `default_stages: [pre-commit]` a hook that says nothing is a
    pre-commit hook, so TST-001's `pre-push` locus is not served by it — which
    is what makes the register's `locus:` list a description of what happens
    rather than of where a line sits.
    """
    repo = make_repo(
        tmp_path,
        {
            ".pre-commit-config.yaml": _config(
                _hook("tests", "uv run pytest"), default_stages="pre-commit"
            ),
            ".github/workflows/ci.yml": _GATING,
        },
    )
    result = _tst_001(repo)
    assert not result.passed
    assert "pre-push locus — no hook runs the test command" in result.message


def test_both_of_the_declared_loci_are_reported_when_neither_is_wired(tmp_path: Path) -> None:
    """Every locus, not the first that fails.

    A repository that has wired neither should be told both, or fixing one
    reveals the other and the second report reads as a fresh regression.
    """
    repo = make_repo(tmp_path, {".pre-commit-config.yaml": _config()})
    result = _tst_001(repo)
    assert not result.passed
    assert "pre-push locus" in result.message and "no CI step" in result.message


def test_a_hook_whose_exit_code_is_absorbed_is_not_a_gate(tmp_path: Path) -> None:
    """The same question the ci locus is asked, asked of the hook.

    `|| true` on a hook entry runs the suite and gates on nothing, exactly as
    `continue-on-error` does to a step. The idioms come from the register's
    `suppression:`, so both loci refuse the same list.
    """
    repo = make_repo(
        tmp_path,
        {
            ".pre-commit-config.yaml": _config(
                _hook("tests", "uv run pytest || true", stages="pre-push")
            ),
            ".github/workflows/ci.yml": _GATING,
        },
    )
    result = _tst_001(repo)
    assert not result.passed
    assert "absorbed" in result.message


def test_the_locus_comes_from_the_register_and_not_from_this_module(tmp_path: Path) -> None:
    """Only the register moves, and the verdict moves with it.

    A repository wired at `ci` alone passes TST-001 when the register asks for
    `ci` alone, and the same repository fails the moment the register declares
    the second locus. An assert holding the loci privately would pass both.
    """
    repo = make_repo(
        tmp_path,
        {
            ".pre-commit-config.yaml": _config(default_stages="pre-commit"),
            ".github/workflows/ci.yml": _GATING,
        },
    )

    def ci_only(document: dict[str, Any]) -> None:
        for control in document["controls"]:
            if control["id"] == "TST-001":
                control["locus"] = ["ci"]

    narrowed = register_with(tmp_path / "reg", ci_only)
    assert check_tests_run_and_block(repo, narrowed, {CONTROL_ARG: "TST-001"}).passed
    assert not _tst_001(repo).passed


def test_this_repository_wires_the_locus_it_declares() -> None:
    """The deployed artefacts, read rather than assumed.

    `register-check` already fails if these are missing; what this adds is the
    two facts no control can check — that `setup.sh` installs the second hook
    type, and that `check-auth.sh` reports it missing. `.git/hooks/` is
    untracked, so that boundary is a test's to hold or nobody's.
    """
    config = (REPO_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    assert "default_stages: [pre-commit]" in config
    assert config.count("stages: [pre-push]") == 3

    for script in (
        REPO_ROOT / ".devcontainer/setup.sh",
        REPO_ROOT / "plugins/control-register/templates/devcontainer/setup.sh",
    ):
        text = script.read_text(encoding="utf-8")
        assert "pre-commit install --hook-type pre-commit --hook-type pre-push" in text
        assert "pre-commit install\n" not in text, script

    auth = (REPO_ROOT / ".devcontainer/check-auth.sh").read_text(encoding="utf-8")
    assert "for hook_type in pre-commit pre-push" in auth
