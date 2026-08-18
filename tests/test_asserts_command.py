"""Command assertions over workflow and configuration fixtures."""

from __future__ import annotations

from pathlib import Path

from conftest import a_register, make_repo
from standard_check.asserts_command import (
    actions_pinned_to_sha,
    ci_installs_frozen,
    markdown_gate_wired_at_all_loci,
    no_failure_suppression,
    no_static_cloud_keys,
    typecheck_strict_and_blocking,
)
from standard_check.asserts_command import (
    tests_run_and_block as check_tests_run_and_block,  # aliased: pytest would collect the name
)
from standard_check.repo import Repo

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
    # `on:` is part of the fixture because a workflow that runs on nothing gates
    # nothing — see test_workflow_dispatch_only_is_not_a_gate.
    return (
        "on: [push, pull_request]\njobs:\n  job:\n    runs-on: ubuntu-latest\n    steps:\n"
        + "".join(steps)
    )


def test_no_static_cloud_keys(tmp_path: Path) -> None:
    clean = make_repo(
        tmp_path / "a", {".github/workflows/ci.yml": _workflow("echo hello")}
    )
    assert no_static_cloud_keys(clean, a_register(), {}).passed
    dirty = make_repo(
        tmp_path / "b",
        {
            ".github/workflows/ci.yml": _workflow(
                "aws configure set aws_access_key_id ${{ secrets.AWS_ACCESS_KEY_ID }}"
            )
        },
    )
    result = no_static_cloud_keys(dirty, a_register(), {})
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
    assert ci_installs_frozen(frozen, a_register(), {}).passed
    resolving = make_repo(
        tmp_path / "b",
        {
            "pyproject.toml": "[project]\n",
            ".github/workflows/ci.yml": _workflow("uv sync", "uv run pytest"),
        },
    )
    result = ci_installs_frozen(resolving, a_register(), {})
    assert not result.passed
    assert "uv sync --frozen" in result.message
    unpinned_tool = make_repo(
        tmp_path / "c",
        {".github/workflows/ci.yml": _workflow("npm install -g markdownlint-cli2")},
    )
    assert not ci_installs_frozen(unpinned_tool, a_register(), {}).passed
    pinned_tool = make_repo(
        tmp_path / "d",
        {".github/workflows/ci.yml": _workflow("npm install -g markdownlint-cli2@0.23.2")},
    )
    assert ci_installs_frozen(pinned_tool, a_register(), {}).passed


def test_missing_python_install_fails_frozen_check(tmp_path: Path) -> None:
    repo = make_repo(
        tmp_path / "r",
        {
            "pyproject.toml": "[project]\n",
            ".github/workflows/ci.yml": _workflow("echo no install here"),
        },
    )
    result = ci_installs_frozen(repo, a_register(), {})
    assert not result.passed
    assert "frozen" in result.message


def test_actions_pinned_to_sha(tmp_path: Path) -> None:
    pinned = make_repo(
        tmp_path / "a",
        {".github/workflows/ci.yml": _workflow("echo hi", uses=f"actions/checkout@{_SHA}")},
    )
    assert actions_pinned_to_sha(pinned, a_register(), {}).passed
    tagged = make_repo(
        tmp_path / "b",
        {".github/workflows/ci.yml": _workflow("echo hi", uses="actions/checkout@v6")},
    )
    result = actions_pinned_to_sha(tagged, a_register(), {})
    assert not result.passed
    assert "actions/checkout@v6" in result.message
    local = make_repo(
        tmp_path / "c",
        {".github/workflows/ci.yml": _workflow("echo hi", uses="./.github/actions/mine")},
    )
    assert actions_pinned_to_sha(local, a_register(), {}).passed


def test_no_failure_suppression(tmp_path: Path) -> None:
    clean = make_repo(tmp_path / "a", {".github/workflows/ci.yml": _workflow("pytest")})
    assert no_failure_suppression(clean, a_register(), {}).passed
    or_true = make_repo(
        tmp_path / "b", {".github/workflows/ci.yml": _workflow("pytest || true")}
    )
    assert not no_failure_suppression(or_true, a_register(), {}).passed
    continue_on_error = make_repo(
        tmp_path / "c",
        {".github/workflows/ci.yml": _workflow("pytest", suppressed=True)},
    )
    assert not no_failure_suppression(continue_on_error, a_register(), {}).passed


def test_tests_run_and_block(tmp_path: Path) -> None:
    good = make_repo(
        tmp_path / "a", {".github/workflows/ci.yml": _workflow("uv run pytest")}
    )
    assert check_tests_run_and_block(good, a_register(), {}).passed
    none = make_repo(tmp_path / "b", {".github/workflows/ci.yml": _workflow("echo build")})
    assert not check_tests_run_and_block(none, a_register(), {}).passed
    absorbed = make_repo(
        tmp_path / "c",
        {".github/workflows/ci.yml": _workflow("uv run pytest", suppressed=True)},
    )
    result = check_tests_run_and_block(absorbed, a_register(), {})
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
    assert typecheck_strict_and_blocking(strict, a_register(), {"role": "typecheck"}).passed
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
    result = typecheck_strict_and_blocking(lax, a_register(), {"role": "typecheck"})
    assert not result.passed
    assert "strict" in result.message


# DOC-001's args as the register carries them. The assert takes the ceiling, the
# tool name and the extension id from here rather than holding them, so a repo
# may tighten or re-tool without the checker changing (ADR 0018).
_DOC_ARGS = {
    "max_line_length": 250,
    "tool": "markdownlint-cli2",
    "editor_extension": "DavidAnson.vscode-markdownlint",
}


def _markdown_repo(root: Path, **overrides: str) -> Repo:
    """A repo wired for DOC-001 at all three loci, with the ceiling in force."""
    files = {
        ".markdownlint.yaml": "default: true\nMD013:\n  line_length: 250\n",
        ".devcontainer/devcontainer.json": (
            '{"customizations": {"vscode": {"extensions": '
            '["DavidAnson.vscode-markdownlint"]}}}\n'
        ),
        ".pre-commit-config.yaml": (
            "repos:\n  - repo: local\n    hooks:\n      - id: markdownlint-cli2\n"
            "        entry: npx --no-install markdownlint-cli2\n"
        ),
        ".github/workflows/lint.yml": _workflow('npx --no-install markdownlint-cli2 "**/*.md"'),
    }
    files.update(overrides)
    return make_repo(root, {k: v for k, v in files.items() if v})


def test_markdown_gate_wired_at_all_loci(tmp_path: Path) -> None:
    repo = _markdown_repo(tmp_path / "ok")
    result = markdown_gate_wired_at_all_loci(repo, a_register(), _DOC_ARGS)
    assert result.passed, result.message
    assert "250" in result.message


def test_markdown_ceiling_may_not_be_loosened(tmp_path: Path) -> None:
    """`line_length: 100000` plus a 1600-character line used to pass (§ A).

    DOC-001 is `narrowing-only`, so a repo may cap lines below the register's
    250 and may never raise the cap above it.
    """
    loosened = _markdown_repo(
        tmp_path / "loose",
        **{".markdownlint.yaml": "default: true\nMD013:\n  line_length: 100000\n"},
    )
    result = markdown_gate_wired_at_all_loci(loosened, a_register(), _DOC_ARGS)
    assert not result.passed
    assert "100000" in result.message and "250" in result.message

    tightened = _markdown_repo(
        tmp_path / "tight",
        **{".markdownlint.yaml": "default: true\nMD013:\n  line_length: 100\n"},
    )
    assert markdown_gate_wired_at_all_loci(tightened, a_register(), _DOC_ARGS).passed


def test_markdown_ceiling_switched_off_is_no_ceiling(tmp_path: Path) -> None:
    for config in ("default: true\nMD013: false\n", "default: false\nMD024: {}\n"):
        repo = _markdown_repo(tmp_path / str(abs(hash(config))), **{".markdownlint.yaml": config})
        result = markdown_gate_wired_at_all_loci(repo, a_register(), _DOC_ARGS)
        assert not result.passed, config
        assert "MD013" in result.message


def test_markdown_gate_missing_at_each_locus_is_caught(tmp_path: Path) -> None:
    """Deleting the CI step, the hook or the extension each used to pass (§ A)."""
    cases = {
        ".github/workflows/lint.yml": "ci locus",
        ".pre-commit-config.yaml": "pre-commit locus",
        ".devcontainer/devcontainer.json": "editor locus",
    }
    for path, expected in cases.items():
        repo = _markdown_repo(tmp_path / expected.replace(" ", "-"), **{path: ""})
        result = markdown_gate_wired_at_all_loci(repo, a_register(), _DOC_ARGS)
        assert not result.passed, path
        assert expected in result.message


def test_markdown_gate_reads_the_cli2_config_shape(tmp_path: Path) -> None:
    """A `.markdownlint-cli2.*` file wraps its rules in a `config:` key."""
    repo = _markdown_repo(
        tmp_path / "cli2",
        **{
            ".markdownlint.yaml": "",
            ".markdownlint-cli2.yaml": (
                "ignores:\n  - '**/node_modules/**'\nconfig:\n  MD013:\n    line_length: 120\n"
            ),
        },
    )
    result = markdown_gate_wired_at_all_loci(repo, a_register(), _DOC_ARGS)
    assert result.passed, result.message
    assert "120" in result.message
