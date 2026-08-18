"""The mandated tools are register facts, not checker facts.

ADR 0018's boundary test asks: *could a reasonable Equal Experts repository need
this to differ without the checker changing?* Which linter is mandated, where
its configuration lives, which editor extension serves it, how CI invokes it and
what counts as swallowing a failure all answer yes. They lived in dictionaries
inside `asserts_command`, so "the standard mandates ruff" was a decision no
reviewer could find and no `review_by` date could ever have surfaced.

The tests here are the evidence that the move is real rather than cosmetic: each
changes only `controls.yaml` and asserts the verdict changes with it. An assert
that still held the rule privately would pass them all while ignoring the
register — so every case edits the register and none edits the checker.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest
import yaml

from conftest import MINIMAL_REGISTER, a_register, make_repo, write_register
from standard_check.asserts_command import (
    linter_wired_at_all_loci,
    no_failure_suppression,
    typecheck_strict_and_blocking,
)
from standard_check.register import Register, load_register
from standard_check.repo import Repo

_WORKFLOW = (
    "on: [push, pull_request]\njobs:\n  job:\n    runs-on: ubuntu-latest\n    steps:\n"
    "      - run: {command}\n"
)


def _python_repo(root: Path, tool: str = "ruff", extension: str = "charliermarsh.ruff") -> Repo:
    """A Python repo wired for whichever linter is named."""
    return make_repo(
        root,
        {
            "pyproject.toml": f"[project]\nname = 'x'\n[tool.{tool}]\nline-length = 100\n",
            ".devcontainer/devcontainer.json": (
                '{"customizations": {"vscode": {"extensions": ["' + extension + '"]}}}\n'
            ),
            ".pre-commit-config.yaml": (
                f"repos:\n  - repo: local\n    hooks:\n      - id: {tool}\n"
                f"        entry: uv run {tool}\n"
            ),
            ".github/workflows/ci.yml": _WORKFLOW.format(command=f"uv run {tool} check"),
        },
    )


def _register_with(tmp_path: Path, mutate: Any) -> Register:
    """This repository's register with one edit applied, reloaded from disk."""
    document = yaml.safe_load(Path("controls.yaml").read_text(encoding="utf-8"))
    mutate(document)
    root = tmp_path / "register"
    root.mkdir(parents=True, exist_ok=True)
    (root / "controls.yaml").write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    # `rationale_adr` paths are checked relative to the register, so bring them.
    for control in document["controls"] + document.get("meta_controls", []):
        adr = control.get("rationale_adr")
        if adr:
            target = root / adr
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("# ADR\n", encoding="utf-8")
    register, errors = load_register(root / "controls.yaml")
    assert register is not None, errors
    return register


def test_mandating_a_different_linter_changes_the_verdict(tmp_path: Path) -> None:
    """The decisive test. Only the register moves; the checker is untouched.

    A repository wired end to end for `flake8` fails against the register as it
    stands, and passes once the register says `flake8` — which is exactly what
    "the mandated tool is a register fact" has to mean.
    """
    flake8_repo = _python_repo(tmp_path / "flake8", tool="flake8", extension="ms-python.flake8")

    against_ruff = linter_wired_at_all_loci(flake8_repo, a_register(), {"role": "lint"})
    assert not against_ruff.passed
    assert "ruff" in against_ruff.message

    def mandate_flake8(document: dict[str, Any]) -> None:
        gate = document["stacks"]["python"]["gates"]["lint"]
        gate["tool"] = "flake8"
        gate["invocation"] = "flake8 check"
        gate["pre_commit"] = "flake8"
        gate["editor_extension"] = "ms-python.flake8"
        gate["config"] = [{"file": "pyproject.toml", "section": "tool.flake8"}]

    against_flake8 = linter_wired_at_all_loci(
        flake8_repo, _register_with(tmp_path, mandate_flake8), {"role": "lint"}
    )
    assert against_flake8.passed, against_flake8.message


def test_a_config_location_added_to_the_register_is_honoured(tmp_path: Path) -> None:
    """`section` distinguishes a file existing from the tool being configured."""
    repo = make_repo(
        tmp_path / "r",
        {
            "pyproject.toml": "[project]\nname = 'x'\n",  # present, but no [tool.ruff]
            ".devcontainer/devcontainer.json": (
                '{"customizations": {"vscode": {"extensions": ["charliermarsh.ruff"]}}}\n'
            ),
            ".pre-commit-config.yaml": (
                "repos:\n  - repo: local\n    hooks:\n      - id: ruff\n        entry: ruff\n"
            ),
            ".github/workflows/ci.yml": _WORKFLOW.format(command="ruff check ."),
            "house-ruff.toml": "line-length = 100\n",
        },
    )
    unconfigured = linter_wired_at_all_loci(repo, a_register(), {"role": "lint"})
    assert not unconfigured.passed
    assert "no ruff configuration" in unconfigured.message

    def add_location(document: dict[str, Any]) -> None:
        document["stacks"]["python"]["gates"]["lint"]["config"].append({"file": "house-ruff.toml"})

    assert linter_wired_at_all_loci(
        repo, _register_with(tmp_path, add_location), {"role": "lint"}
    ).passed


def test_strict_key_comes_from_the_register(tmp_path: Path) -> None:
    """A type checker whose strictness flag is spelled differently."""
    repo = make_repo(
        tmp_path / "r",
        {
            "pyproject.toml": "[project]\nname = 'x'\n[tool.mypy]\nvery_strict = true\n",
            ".pre-commit-config.yaml": (
                "repos:\n  - repo: local\n    hooks:\n      - id: mypy\n        entry: mypy\n"
            ),
            ".github/workflows/ci.yml": _WORKFLOW.format(command="mypy"),
        },
    )
    result = typecheck_strict_and_blocking(repo, a_register(), {"role": "typecheck"})
    assert not result.passed
    assert "strict mode is not set" in result.message

    def rename_key(document: dict[str, Any]) -> None:
        document["stacks"]["python"]["gates"]["typecheck"]["strict_key"] = "very_strict"

    assert typecheck_strict_and_blocking(
        repo, _register_with(tmp_path, rename_key), {"role": "typecheck"}
    ).passed


def test_suppression_idioms_come_from_the_register(tmp_path: Path) -> None:
    """A house idiom the checker never heard of is a suppression it never caught."""
    repo = make_repo(
        tmp_path / "r",
        {".github/workflows/ci.yml": _WORKFLOW.format(command="pytest ; echo swallowed")},
    )
    assert no_failure_suppression(repo, a_register(), {}).passed

    def add_idiom(document: dict[str, Any]) -> None:
        document["suppression"].append(r";\s*echo swallowed\b")

    result = no_failure_suppression(repo, _register_with(tmp_path, add_idiom), {})
    assert not result.passed
    assert "swallowed" in result.message


def test_a_stack_must_name_a_predicate(tmp_path: Path) -> None:
    """A stack nothing can detect never applies — T-3 inside the register."""
    document = copy.deepcopy(MINIMAL_REGISTER)
    document["stacks"] = {
        "kotlin": {
            "gates": {
                "lint": {
                    "tool": "ktlint",
                    "invocation": "ktlint",
                    "config": [{"file": ".editorconfig"}],
                }
            }
        }
    }
    path = write_register(tmp_path / "r", document)
    register, errors = load_register(path)
    assert register is None
    assert any("stacks.kotlin" in e.field and "no predicate" in e.message for e in errors), errors


def test_a_declared_locus_must_be_expressible_by_its_gate(tmp_path: Path) -> None:
    """Caught once at schema time, not argued about at every run.

    A control claiming an `editor` locus whose gate names no extension would
    otherwise either fail every repository or be quietly skipped, and which of
    those happened would depend on how the assert was written.
    """

    def drop_extension(document: dict[str, Any]) -> None:
        del document["stacks"]["python"]["gates"]["lint"]["editor_extension"]

    document = yaml.safe_load(Path("controls.yaml").read_text(encoding="utf-8"))
    drop_extension(document)
    root = tmp_path / "broken"
    root.mkdir(parents=True)
    (root / "controls.yaml").write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    for control in document["controls"]:
        target = root / control["rationale_adr"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# ADR\n", encoding="utf-8")
    register, errors = load_register(root / "controls.yaml")
    assert register is None
    assert any(
        e.field == "stacks.python.gates.lint.editor_extension" and "LNT-001" in e.message
        for e in errors
    ), errors


@pytest.mark.parametrize("role", ["lint", "typecheck"])
def test_a_stack_absent_from_the_repo_is_not_a_failure(tmp_path: Path, role: str) -> None:
    """No tsconfig.json means no typescript gate to check, not a violation."""
    empty = make_repo(tmp_path / f"empty-{role}", {"README.md": "# x\n"})
    for assert_fn in (linter_wired_at_all_loci, typecheck_strict_and_blocking):
        result = assert_fn(empty, a_register(), {"role": role})
        assert result.passed, result.message
