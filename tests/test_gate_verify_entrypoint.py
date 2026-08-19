"""`standard-check run --control <ID>` — the one entry point a gate verifies through.

Phase 2's criterion is *"gates and checker share one assert implementation —
verified by there being one copy, not by comparing two"*. The mechanism is this
subcommand: a `gate-*` skill's Verify step runs the control it just deployed
through `run_control`, the same function the full audit calls, against the same
register. There is no second path for a gate to take, so there is nothing for a
gate and the auditor to disagree about.

What is tested here is that the narrowing is a narrowing and nothing more: the
same verdicts, the same exit codes, no control silently dropped, and — the case
that matters — an unknown id reported as a usage error rather than as an empty
green run. A gate that misspelled its own control would otherwise be told it
succeeded having verified nothing, which is § A's defect with a typo for a
cause.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

from conftest import make_repo, minimal_register, write_register
from standard_check.cli import main

_HOOKS = "repos:\n  - repo: local\n    hooks:\n      - id: gitleaks\n"


def _two_control_register() -> dict[str, Any]:
    """The minimal register plus a second, deliberately failing, control."""
    document = minimal_register()
    document["controls"].append(
        dict(
            document["controls"][0],
            id="LNT-001",
            title="A control this repo violates",
            verify=[
                {"kind": "file", "assert": "precommit_hook_present", "args": {"id": "ruff"}}
            ],
        )
    )
    return document


def test_one_control_runs_and_the_others_do_not(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_register(tmp_path, _two_control_register())
    make_repo(tmp_path, {".pre-commit-config.yaml": _HOOKS})

    assert main(["--repo", str(tmp_path), "run", "--control", "SEC-001"]) == 0
    out = capsys.readouterr().out
    assert "SEC-001" in out
    # The failing control is genuinely absent, not merely quiet: were it still
    # evaluated, its FAIL would have made the exit 1 above.
    assert "LNT-001" not in out


def test_the_narrowed_verdict_is_the_verdict_the_full_run_gives(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A gate must not be able to pass itself where the auditor would fail it."""
    write_register(tmp_path, _two_control_register())
    make_repo(tmp_path, {".pre-commit-config.yaml": _HOOKS})

    assert main(["--repo", str(tmp_path)]) == 1
    full = capsys.readouterr().out
    assert main(["--repo", str(tmp_path), "run", "--control", "LNT-001"]) == 1
    narrowed = capsys.readouterr().out

    for report in (full, narrowed):
        assert re.search(r"^  LNT-001\s+FAIL\b", report, re.MULTILINE), report
    # ...and for the same stated reason, not merely with the same word.
    assert "ruff" in narrowed


def test_repeating_the_flag_selects_several_controls(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_register(tmp_path, _two_control_register())
    make_repo(tmp_path, {".pre-commit-config.yaml": _HOOKS})

    assert (
        main(
            ["--repo", str(tmp_path), "run", "--control", "SEC-001", "--control", "LNT-001"]
        )
        == 1
    )
    out = capsys.readouterr().out
    assert "SEC-001" in out and "LNT-001" in out


def test_an_unknown_id_is_a_usage_error_not_an_empty_pass(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The failure this flag would otherwise introduce.

    `--control SEC-01` selects nothing. With no id check, nothing is what gets
    verified, and a run that verified nothing exits 0 — a gate reporting success
    over a typo. Exit 2 is the usage-error code, distinct from both verdicts.
    """
    write_register(tmp_path)
    make_repo(tmp_path, {".pre-commit-config.yaml": _HOOKS})

    assert main(["--repo", str(tmp_path), "run", "--control", "SEC-01"]) == 2
    assert "no control SEC-01" in capsys.readouterr().err


def test_a_control_outside_the_selected_tier_is_unknown_to_the_flag(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--tier` narrows first, so `--control` cannot smuggle a control back in.

    Reporting "no control X in the selected set" rather than running it keeps
    the two flags composable in one direction only: both narrow, neither widens.
    """
    document = _two_control_register()
    document["controls"][1]["tier"] = 2
    write_register(tmp_path, document)
    make_repo(tmp_path, {".pre-commit-config.yaml": _HOOKS})

    assert (
        main(["--repo", str(tmp_path), "run", "--tier", "1", "--control", "LNT-001"]) == 2
    )
    assert "no control LNT-001 in the selected set" in capsys.readouterr().err


def test_a_narrowed_run_carries_no_meta_controls(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Meta-controls audit the register, not a deployment.

    A gate verifying the artefacts it just wrote has no business reporting on
    whether some other control is past its review date — and an empty `Meta`
    heading over no results reads as meta-controls that passed silently.
    """
    write_register(tmp_path)
    make_repo(tmp_path, {".pre-commit-config.yaml": _HOOKS})

    assert main(["--repo", str(tmp_path), "run", "--control", "SEC-001"]) == 0
    out = capsys.readouterr().out
    assert "GOV-003" not in out
    assert "\nMeta\n" not in out
    assert "meta-controls: 0/0 passed" in out


def test_remote_blocks_still_deny_the_narrowed_run_a_clean_exit(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """SEC-001's own shape: two local loci that pass, one remote that cannot.

    This is what a `gate-secrets` verify step sees until Phase 3. The local
    blocks tick, the remote one reports `SKIPPED (no credentials)`, and the run
    exits 3 — incomplete. Exiting 0 here would let the gate claim the remote
    locus it has not touched (ADR 0016).
    """
    document = minimal_register(
        locus=["pre-commit", "ci", "remote"],
        verify=[
            {"kind": "file", "assert": "precommit_hook_present", "args": {"id": "gitleaks"}},
            {"kind": "remote", "assert": "github_push_protection_enabled"},
        ],
    )
    write_register(tmp_path, document)
    make_repo(tmp_path, {".pre-commit-config.yaml": _HOOKS})

    assert main(["--repo", str(tmp_path), "run", "--control", "SEC-001"]) == 3
    out = capsys.readouterr().out
    assert "✓ file: precommit_hook_present" in out
    assert "SKIPPED (no credentials)" in out
    assert (
        main(["--repo", str(tmp_path), "--require-complete", "run", "--control", "SEC-001"])
        == 1
    )
