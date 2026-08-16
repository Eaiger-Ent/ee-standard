"""Predicate grammar and evaluation against repository files."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import make_repo
from standard_check.predicates import PredicateSyntaxError, compile_predicate


def test_boolean_predicates() -> None:
    repo = None  # never touched
    assert compile_predicate(True)(repo)  # type: ignore[arg-type]
    assert not compile_predicate(False)(repo)  # type: ignore[arg-type]


def test_file_exists(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "r", {"pyproject.toml": "[project]\n"})
    assert compile_predicate("pyproject.toml exists")(repo)
    assert not compile_predicate("tsconfig.json exists")(repo)


def test_directory_exists(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "r", {".github/workflows/ci.yml": "jobs: {}\n"})
    assert compile_predicate(".github/workflows/ exists")(repo)
    assert not compile_predicate(".circleci/ exists")(repo)


def test_any_glob_exists_with_optional_file_noun(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "r", {"infra/main.tf": "{}\n"})
    assert compile_predicate("any *.tf file exists")(repo)
    assert compile_predicate("any *.tf exists")(repo)
    assert not compile_predicate("any Dockerfile exists")(repo)


def test_unknown_expression_raises() -> None:
    with pytest.raises(PredicateSyntaxError):
        compile_predicate("the repo feels conformant")
