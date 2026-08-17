"""The checker must always produce a verdict, and never a green report it did not earn.

Two failure directions are covered here, both found by review after Phase 1's
suite passed 48 checks over them:

- an assert that raises must degrade to a verdict, not abort the run;
- a target the checker cannot evaluate must be an error, not a page of skips.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import make_repo, write_register
from standard_check.cli import main
from standard_check.register import VerifyBlock
from standard_check.repo import Repo, strip_jsonc
from standard_check.runner import Verdict, run_block, run_command_assert

_HOOK = "repos:\n  - repo: local\n    hooks:\n      - id: gitleaks\n"


def _file_block(name: str, **args: object) -> VerifyBlock:
    return VerifyBlock(kind="file", assert_name=name, args=dict(args))


# --- an assert that cannot read its input still returns a verdict -------------


def test_tracked_but_deleted_file_is_a_verdict(tmp_path: Path) -> None:
    """git ls-files still lists it, so repo.exists() is true and the read fails."""
    repo = make_repo(tmp_path / "r", {".pre-commit-config.yaml": _HOOK})
    (repo.root / ".pre-commit-config.yaml").unlink()
    result = run_block(_file_block("precommit_hook_present", id="gitleaks"), repo)
    assert result.verdict is Verdict.FAIL
    assert ".pre-commit-config.yaml" in result.message


@pytest.mark.parametrize(
    ("label", "filename", "content", "assert_name", "args", "expected"),
    [
        # A section present but empty parses to None, which used to be iterated.
        ("null-repos", ".pre-commit-config.yaml", "repos:\n", "precommit_hook_present",
         {"id": "gitleaks"}, Verdict.FAIL),
        ("not-a-mapping", ".pre-commit-config.yaml", "[]\n", "precommit_hook_present",
         {"id": "gitleaks"}, Verdict.FAIL),
        ("unparseable", ".pre-commit-config.yaml", "{{ not yaml\n", "precommit_hook_present",
         {"id": "gitleaks"}, Verdict.FAIL),
        # These two are legitimately satisfied — the point is that they resolve
        # rather than raising on a None section.
        ("null-updates", ".github/dependabot.yml", "version: 2\nupdates:\n",
         "dependency_update_config_covers_all_ecosystems", {}, Verdict.PASS),
        ("null-features", ".devcontainer/devcontainer.json", '{"features": null}',
         "devcontainer_lock_covers_all_features", {}, Verdict.PASS),
    ],
)
def test_degenerate_config_shapes_are_verdicts(
    tmp_path: Path,
    label: str,
    filename: str,
    content: str,
    assert_name: str,
    args: dict[str, object],
    expected: Verdict,
) -> None:
    """A file that parses to None, to a non-mapping, or not at all still yields a verdict."""
    repo = make_repo(tmp_path / label, {filename: content})
    result = run_block(_file_block(assert_name, **args), repo)
    assert result.verdict is expected
    assert result.message


def test_malformed_pyproject_is_a_verdict(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "r", {"pyproject.toml": "[project\nbroken = "})
    passed, message = run_command_assert("typecheck-strict-and-blocking", repo)
    assert not passed
    assert message  # a reason, not a traceback


def test_unparseable_workflow_is_a_verdict(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "r", {".github/workflows/ci.yml": "jobs: [unclosed\n"})
    passed, _message = run_command_assert("actions-pinned-to-sha", repo)
    assert not passed


def test_npm_install_ci_test_does_not_crash(tmp_path: Path) -> None:
    """`npm install-ci-test` is a real command; the regex matches but 'install' is not a word."""
    workflow = (
        "jobs:\n  j:\n    runs-on: ubuntu-latest\n    steps:\n      - run: npm install-ci-test\n"
    )
    repo = make_repo(tmp_path / "r", {".github/workflows/ci.yml": workflow})
    passed, message = run_command_assert("ci-installs-frozen", repo)
    assert isinstance(passed, bool)
    assert "ValueError" not in message


def test_one_broken_file_does_not_abort_the_whole_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Every control still gets a verdict even when one assert's input is poison."""
    write_register(tmp_path)
    make_repo(tmp_path, {".pre-commit-config.yaml": "repos:\n"})
    code = main(["--repo", str(tmp_path)])
    out = capsys.readouterr().out
    assert code == 1
    assert "SEC-001" in out
    assert "Summary:" in out  # the report was rendered rather than aborted


# --- JSONC with trailing commas is legal and must parse ----------------------


def test_strip_jsonc_removes_trailing_commas() -> None:
    text = '{\n  "a": [1, 2,],\n  // comment\n  "b": {"c": true,},\n}'
    assert json.loads(strip_jsonc(text)) == {"a": [1, 2], "b": {"c": True}}


def test_strip_jsonc_preserves_commas_inside_strings() -> None:
    assert json.loads(strip_jsonc('{"a": "x,}", "b": 1}')) == {"a": "x,}", "b": 1}


def test_tsconfig_with_trailing_comma_is_read_not_fatal(tmp_path: Path) -> None:
    repo = make_repo(
        tmp_path / "r",
        {"tsconfig.json": '{\n  "compilerOptions": {\n    "strict": true,\n  },\n}\n'},
    )
    passed, message = run_command_assert("typecheck-strict-and-blocking", repo)
    # strict is set, so the only complaint may be the missing CI step — never a crash.
    assert "JSONDecodeError" not in message
    assert "compilerOptions.strict is not true" not in message
    assert isinstance(passed, bool)


# --- a target the checker cannot evaluate is an error, not a clean report -----


def test_non_git_directory_is_an_error_not_a_green_report(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A directory full of violations must never report as all-skipped, exit 0."""
    write_register(tmp_path)
    (tmp_path / "Dockerfile").write_text("FROM alpine\nUSER root\n", encoding="utf-8")
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text(
        "jobs:\n  j:\n    steps:\n      - run: echo ${{ secrets.AWS_SECRET_ACCESS_KEY }}\n",
        encoding="utf-8",
    )
    code = main(["--repo", str(tmp_path)])
    captured = capsys.readouterr()
    assert code == 2
    assert "not a git repository" in captured.err
    assert "SKIPPED (predicate)" not in captured.out


def test_missing_repo_path_is_an_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["--repo", str(tmp_path / "nope")])
    assert code == 2
    assert "nope" in capsys.readouterr().err


def test_repo_helper_reports_non_git_directories(tmp_path: Path) -> None:
    assert Repo(tmp_path).is_git_repo() is False
    assert make_repo(tmp_path / "r", {"a.txt": "x"}).is_git_repo() is True
