"""Verdict aggregation, skip rendering, and exit-code semantics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from conftest import make_repo, minimal_register, write_register
from standard_check.cli import main
from standard_check.register import Register, load_register
from standard_check.repo import Repo
from standard_check.runner import Verdict, run_control, worst


def _register_at(root: Path, document: dict[str, Any]) -> tuple[Register, Repo]:
    path = write_register(root, document)
    register, errors = load_register(path)
    assert errors == []
    assert register is not None
    return register, Repo(root)


def test_worst_orders_fail_above_skips() -> None:
    assert worst([Verdict.PASS, Verdict.FAIL]) is Verdict.FAIL
    assert worst([Verdict.PASS, Verdict.SKIPPED_NO_CREDENTIALS]) is Verdict.SKIPPED_NO_CREDENTIALS
    assert worst([Verdict.PASS]) is Verdict.PASS


def test_unsatisfied_predicate_skips_not_fails(tmp_path: Path) -> None:
    document = minimal_register(applies_to=["python"])  # no pyproject.toml in fixture
    register, repo = _register_at(tmp_path, document)
    make_repo(tmp_path, {})
    result = run_control(register.controls[0], register, repo)
    assert result.verdict is Verdict.SKIPPED_PREDICATE
    assert result.blocks == ()


def test_remote_block_skips_without_credentials(tmp_path: Path) -> None:
    document = minimal_register(
        locus=["remote"],
        verify=[{"kind": "remote", "assert": "github_push_protection_enabled"}],
    )
    register, repo = _register_at(tmp_path, document)
    make_repo(tmp_path, {})
    result = run_control(register.controls[0], register, repo)
    assert result.verdict is Verdict.SKIPPED_NO_CREDENTIALS


def test_file_assert_failure_fails_the_control(tmp_path: Path) -> None:
    register, repo = _register_at(tmp_path, minimal_register())
    make_repo(tmp_path, {})  # no .pre-commit-config.yaml
    result = run_control(register.controls[0], register, repo)
    assert result.verdict is Verdict.FAIL


def test_run_exit_codes_and_distinct_skip_rendering(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    document = minimal_register()
    document["controls"].append(
        dict(
            document["controls"][0],
            id="CI-001",
            title="Remote-only control",
            locus=["remote"],
            verify=[{"kind": "remote", "assert": "github_push_protection_enabled"}],
        )
    )
    document["controls"].append(
        dict(
            document["controls"][0],
            id="IAC-001",
            title="Predicate-skipped control",
            applies_to=["python"],
        )
    )
    write_register(tmp_path, document)
    make_repo(
        tmp_path,
        {".pre-commit-config.yaml": "repos:\n  - repo: local\n    hooks:\n      - id: gitleaks\n"},
    )
    code = main(["--repo", str(tmp_path)])
    out = capsys.readouterr().out
    # Local control passes, remote skip and predicate skip render distinctly,
    # and neither skip is counted as a pass. The no-credentials skip makes the
    # run incomplete, so it exits 3 rather than 0 (ADR 0016) — this is the
    # Phase 1 criterion that was re-opened for having left the code at 0.
    assert code == 3
    assert "SKIPPED (no credentials)" in out
    assert "SKIPPED (predicate)" in out
    assert "1 passed" in out
    assert "1 skipped (predicate)" in out
    assert "1 skipped (no credentials)" in out
    assert "incomplete" in out
    # ...and --require-complete turns that incompleteness into a hard failure.
    assert main(["--repo", str(tmp_path), "--require-complete"]) == 1


def test_predicate_skip_alone_still_exits_zero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Not-applicable is a legitimate pass, even under --require-complete.

    A repo with no Terraform genuinely satisfies IAC-001's applicability.
    Conflating that with "could not verify" would make exit 3 meaningless in the
    common case, so a predicate skip never contributes to incompleteness.
    """
    document = minimal_register()
    document["controls"].append(
        dict(
            document["controls"][0],
            id="IAC-001",
            title="Predicate-skipped control",
            applies_to=["python"],
        )
    )
    write_register(tmp_path, document)
    make_repo(
        tmp_path,
        {".pre-commit-config.yaml": "repos:\n  - repo: local\n    hooks:\n      - id: gitleaks\n"},
    )
    assert main(["--repo", str(tmp_path)]) == 0
    assert main(["--repo", str(tmp_path), "--require-complete"]) == 0
    assert "1 skipped (predicate)" in capsys.readouterr().out


def test_absent_tool_is_unclassified_not_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """"Cannot verify" must be distinguishable from "violates".

    A missing binary says nothing about the repository. Reporting FAIL asserts a
    violation the run has no evidence for — and makes a broken container look
    identical to a non-conformant repo.
    """
    document = minimal_register(
        verify=[{"kind": "command", "run": "definitely-not-installed --check"}]
    )
    write_register(tmp_path, document)
    make_repo(tmp_path, {})
    code = main(["--repo", str(tmp_path)])
    out = capsys.readouterr().out
    assert code == 3
    assert "UNCLASSIFIED" in out
    assert "tool not installed: definitely-not-installed" in out
    assert "0 failed" in out
    assert "1 unclassified" in out
    assert main(["--repo", str(tmp_path), "--require-complete"]) == 1


def test_run_exits_nonzero_on_failure(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write_register(tmp_path, minimal_register())
    make_repo(tmp_path, {})  # hook missing → FAIL
    code = main(["--repo", str(tmp_path)])
    assert code == 1
    assert "FAIL" in capsys.readouterr().out


def test_schema_command_reports_errors_naming_fields(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_register(tmp_path, minimal_register(rung="mandatory"))
    code = main(["--repo", str(tmp_path), "schema"])
    err = capsys.readouterr().err
    assert code == 1
    assert "(SEC-001).rung" in err


def test_assert_command_unknown_name(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["assert", "no-such-assert"])
    assert code == 1
    assert "unknown assert name" in capsys.readouterr().out
