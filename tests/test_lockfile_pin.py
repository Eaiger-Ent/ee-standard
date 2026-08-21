"""The pin a locus reaches is verified to exist — ADR 0020 case C.

ADR 0020 made every locus invoke the artefact its lockfile owns, and measured
the one condition that form cannot cover: `uv run <tool>` falls through to
`PATH` when the tool is absent from the project altogether. An invocation cannot
assert the existence of the thing it invokes, so `stack_tool_pinned_in_lockfile`
does, and register contract 13 gives it the two facts it reads —
`stacks.<stack>.ecosystem` and `ecosystems.<name>.lock_entry`.

Two things are proved here. First, that the assert fails when the pin is gone,
which is the whole of case C: an assert never observed failing is not known to
work. Second, that **every** `lock_entry` pattern in the register matches a real
lockfile of its ecosystem. Six ecosystems are declared and two are exercised by
this repository's own stacks; the other four would otherwise ship as regular
expressions nobody had ever run — the vacuous-pass shape that put a `go.mod`
repository past SUP-001 for three contracts (§ H3).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

from conftest import a_register, make_repo, register_with
from standard_check.asserts_file import stack_tool_pinned_in_lockfile, substitute_package
from standard_check.repo import Repo

_PYPROJECT = """
[project]
name = "probe"
version = "0.1.0"

[tool.ruff]
line-length = 100

[tool.mypy]
strict = true
files = ["src"]
"""

_UV_LOCK_WITH = """
version = 1
requires-python = ">=3.12"

[[package]]
name = "mypy"
version = "1.18.2"

[[package]]
name = "ruff"
version = "0.14.1"
"""

_UV_LOCK_WITHOUT_RUFF = """
version = 1
requires-python = ">=3.12"

[[package]]
name = "mypy"
version = "1.18.2"
"""


def _python_repo(root: Path, uv_lock: str) -> Repo:
    return make_repo(root, {"pyproject.toml": _PYPROJECT, "uv.lock": uv_lock})


def test_pinned_tool_passes(tmp_path: Path) -> None:
    repo = _python_repo(tmp_path / "pinned", _UV_LOCK_WITH)
    result = stack_tool_pinned_in_lockfile(repo, a_register(), {"role": "lint"})
    assert result.passed
    assert "ruff pinned in uv.lock" in result.message


def test_tool_removed_from_the_project_fails(tmp_path: Path) -> None:
    """Case C, made a verdict.

    The invocation is untouched and still reads `uv run ruff check`; what
    changed is that nothing pins ruff, so that invocation resolves from PATH.
    ADR 0020 measured this passing; here it fails, with the reason named.
    """
    repo = _python_repo(tmp_path / "unpinned", _UV_LOCK_WITHOUT_RUFF)
    result = stack_tool_pinned_in_lockfile(repo, a_register(), {"role": "lint"})
    assert not result.passed
    assert "ruff is not pinned in uv.lock" in result.message
    assert "resolves from PATH" in result.message


def test_typecheck_role_reads_the_same_register(tmp_path: Path) -> None:
    repo = _python_repo(tmp_path / "typecheck", _UV_LOCK_WITH)
    assert stack_tool_pinned_in_lockfile(repo, a_register(), {"role": "typecheck"}).passed


def test_no_lockfile_at_all_fails(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "nolock", {"pyproject.toml": _PYPROJECT})
    result = stack_tool_pinned_in_lockfile(repo, a_register(), {"role": "lint"})
    assert not result.passed
    assert "no tracked python lockfile" in result.message


def test_untracked_lockfile_is_not_a_pin(tmp_path: Path) -> None:
    """A lockfile git does not track pins nothing anyone else will resolve."""
    root = tmp_path / "untracked"
    repo = make_repo(root, {"pyproject.toml": _PYPROJECT, ".gitignore": "uv.lock\n"})
    (root / "uv.lock").write_text(_UV_LOCK_WITH, encoding="utf-8")
    result = stack_tool_pinned_in_lockfile(repo, a_register(), {"role": "lint"})
    assert not result.passed
    assert "no tracked python lockfile" in result.message


def test_stack_whose_predicate_is_unsatisfied_is_not_judged(tmp_path: Path) -> None:
    """A repository with no `pyproject.toml` has no python gate to pin."""
    repo = make_repo(tmp_path / "empty", {"README.md": "# probe\n"})
    result = stack_tool_pinned_in_lockfile(repo, a_register(), {"role": "lint"})
    assert result.passed
    assert "no stack with a lint gate is present" in result.message


def test_role_is_required(tmp_path: Path) -> None:
    repo = _python_repo(tmp_path / "norole", _UV_LOCK_WITH)
    result = stack_tool_pinned_in_lockfile(repo, a_register(), {})
    assert not result.passed
    assert "'role'" in result.message


def test_only_the_register_moves(tmp_path: Path) -> None:
    """Mandating a different linter is a register change, not a checker change.

    The repository pins ruff and nothing else. Renaming the mandated tool in
    `controls.yaml` has to make the same repository fail — an assert still
    holding "the linter is ruff" privately would pass this.
    """
    repo = _python_repo(tmp_path / "moved", _UV_LOCK_WITH)

    def mandate_pylint(document: dict[str, Any]) -> None:
        document["stacks"]["python"]["gates"]["lint"]["tool"] = "pylint"

    register = register_with(tmp_path, mandate_pylint)
    result = stack_tool_pinned_in_lockfile(repo, register, {"role": "lint"})
    assert not result.passed
    assert "pylint is not pinned" in result.message


def test_package_overrides_the_tool_name(tmp_path: Path) -> None:
    """`tsc` is shipped by `typescript`, and the register says so.

    Without the `package` field the lockfile would be searched for `tsc`, which
    a correctly-pinned repository does not contain — a control failing a repo
    that satisfies it.
    """
    repo = make_repo(
        tmp_path / "ts",
        {
            "tsconfig.json": '{"compilerOptions": {"strict": true}}\n',
            "package.json": '{"name": "probe"}\n',
            "package-lock.json": '{"packages": {"node_modules/typescript": {}}}\n',
        },
    )
    result = stack_tool_pinned_in_lockfile(repo, a_register(), {"role": "typecheck"})
    assert result.passed
    assert "tsc pinned in package-lock.json" in result.message


def test_binary_lockfile_is_reported_rather_than_passed(tmp_path: Path) -> None:
    """A lockfile that is not text cannot confirm a pin, and does not pretend to."""
    root = tmp_path / "bun"
    repo = make_repo(
        root,
        {
            "tsconfig.json": '{"compilerOptions": {"strict": true}}\n',
            "package.json": '{"name": "probe"}\n',
        },
    )
    (root / "bun.lockb").write_bytes(b"\x00\x01typescript\xff\xfe")
    import subprocess

    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    repo = Repo(root)
    result = stack_tool_pinned_in_lockfile(repo, a_register(), {"role": "typecheck"})
    assert not result.passed
    assert "could not be read as text" in result.message


# Every `lock_entry` pattern, against a real fragment of the lockfile it claims
# to read. `python` and `node` are exercised by this repository; the other four
# are not, and a pattern nobody has run is a pin nobody verifies.
_LOCKFILE_FRAGMENTS: dict[str, tuple[str, str]] = {
    "python": (
        "ruff",
        '[[package]]\nname = "ruff"\nversion = "0.14.1"\n',
    ),
    "node": (
        "eslint",
        '{"packages": {"node_modules/eslint": {"version": "9.0.0"}}}\n',
    ),
    "go": (
        "golang.org/x/tools",
        "golang.org/x/tools v0.24.0 h1:J1shsA93PJUEV\n",
    ),
    "rust": (
        "clippy",
        '[[package]]\nname = "clippy"\nversion = "0.1.80"\n',
    ),
    "java": (
        "spotbugs",
        "com.github.spotbugs:spotbugs:4.8.3=compileClasspath\n",
    ),
    "ruby": (
        "rubocop",
        "GEM\n  specs:\n    rubocop (1.66.1)\n",
    ),
}

_NODE_ALTERNATIVES = (
    "  /eslint@9.0.0:\n",
    'eslint@^9.0.0:\n  version "9.0.0"\n',
)

_JAVA_ALTERNATIVE = '<component group="com.github.spotbugs" name="spotbugs" version="4.8.3">\n'


@pytest.mark.parametrize("ecosystem", sorted(_LOCKFILE_FRAGMENTS))
def test_every_lock_entry_pattern_matches_its_own_lockfile(ecosystem: str) -> None:
    package, fragment = _LOCKFILE_FRAGMENTS[ecosystem]
    patterns = a_register().ecosystems[ecosystem].lock_entry
    assert patterns, f"{ecosystem} declares no lock_entry"
    assert any(
        re.search(substitute_package(pattern, package), fragment) for pattern in patterns
    ), f"no {ecosystem} lock_entry pattern matched its own lockfile"


@pytest.mark.parametrize("fragment", _NODE_ALTERNATIVES)
def test_node_patterns_cover_pnpm_and_yarn(fragment: str) -> None:
    patterns = a_register().ecosystems["node"].lock_entry
    assert any(re.search(substitute_package(p, "eslint"), fragment) for p in patterns)


def test_java_patterns_cover_verification_metadata() -> None:
    patterns = a_register().ecosystems["java"].lock_entry
    assert any(
        re.search(substitute_package(p, "spotbugs"), _JAVA_ALTERNATIVE) for p in patterns
    )


@pytest.mark.parametrize("ecosystem", sorted(_LOCKFILE_FRAGMENTS))
def test_lock_entry_patterns_do_not_match_a_package_that_is_absent(ecosystem: str) -> None:
    """The half that makes the other half mean something.

    A pattern loose enough to match any text would pass every test above while
    verifying nothing, which is the failure mode this whole assert exists to
    remove one level up.
    """
    _, fragment = _LOCKFILE_FRAGMENTS[ecosystem]
    patterns = a_register().ecosystems[ecosystem].lock_entry
    assert not any(
        re.search(substitute_package(pattern, "definitely-not-here"), fragment)
        for pattern in patterns
    )


def test_this_repository_pins_the_tools_it_mandates() -> None:
    """The real gate: uv.lock pins ruff and mypy, and the assert reads it."""
    repo = Repo(Path(__file__).resolve().parent.parent)
    register = a_register()
    for role in ("lint", "typecheck"):
        result = stack_tool_pinned_in_lockfile(repo, register, {"role": role})
        assert result.passed, f"{role}: {result.message}"
