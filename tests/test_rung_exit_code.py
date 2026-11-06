"""ADR 0061: a rung below `blocking` never sets the exit code.

Until this ADR the checker never read `rung`, so a failing `warn` control
exited 1 and a `warn` partial exited 3 — which CI's `--require-complete` turns
into 1. Every control was `blocking`, so nothing showed it. AGT-001 is the
first control that is not, and as ADR 0023 wrote it, it would have failed the
required check on every pull request.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from conftest import make_repo, minimal_register, write_register
from register_check.cli import main

HOOK = {".pre-commit-config.yaml": "repos:\n  - repo: local\n    hooks:\n      - id: gitleaks\n"}


def _with_control(rung: str, **overrides: Any) -> dict[str, Any]:
    """The minimal register, whose one blocking control passes, plus a second
    control at `rung` that fails unless `overrides` say otherwise."""
    document = minimal_register()
    control: dict[str, Any] = dict(
        document["controls"][0],
        id="AGT-001",
        title="A control below blocking",
        tier=2,
        rung=rung,
        verify=[
            {
                "kind": "file",
                "assert": "precommit_hook_present",
                "args": {"id": "not-installed"},
            }
        ],
    )
    control.update(overrides)
    document["controls"].append(control)
    return document


def _run(tmp_path: Path, document: dict[str, Any], *flags: str) -> int:
    write_register(tmp_path, document)
    if not (tmp_path / ".git").exists():
        make_repo(tmp_path, HOOK)
    return main(["--repo", str(tmp_path), *flags])


@pytest.mark.parametrize("rung", ["warn", "advisory"])
def test_a_failure_below_blocking_does_not_exit_one(
    rung: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _run(tmp_path, _with_control(rung)) == 0
    out = capsys.readouterr().out
    # Reported, not silenced: the verdict, the rung on its line, and the
    # summary line naming it.
    assert f"FAIL                      A control below blocking [{rung}]" in out
    assert "1 failed" in out
    assert "Below blocking: 1 did not hold (AGT-001)" in out


@pytest.mark.parametrize("rung", ["warn", "advisory"])
def test_a_partial_below_blocking_is_not_promoted_by_require_complete(
    rung: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The case that would have turned this repository's required check red."""
    document = _with_control(
        rung,
        verify=[
            {
                "kind": "file",
                "assert": "precommit_hook_present",
                "args": {"id": "gitleaks"},
                "partial": {"unverified": "the runtime half", "expires": "2099-01-01"},
            }
        ],
    )
    assert _run(tmp_path, document) == 0
    assert _run(tmp_path, document, "--require-complete") == 0
    assert "partial: the runtime half (expires 2099-01-01)" in capsys.readouterr().out


def test_an_unverified_block_below_blocking_sets_nothing(tmp_path: Path) -> None:
    document = _with_control(
        "warn", verify=[{"kind": "command", "run": "definitely-not-installed --check"}]
    )
    assert _run(tmp_path, document) == 0
    assert _run(tmp_path, document, "--require-complete") == 0


@pytest.mark.parametrize("rung", ["blocking", "blocking (baselined)"])
def test_a_failure_at_a_blocking_rung_still_exits_one(rung: str, tmp_path: Path) -> None:
    """The control: the change narrows which controls count, and no further."""
    overrides: dict[str, Any] = {}
    if rung == "blocking (baselined)":
        overrides["baseline"] = ".baseline.json"
    assert _run(tmp_path, _with_control(rung, **overrides)) == 1


def test_an_expired_partial_below_blocking_still_fails_through_gov_003(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The expiry is what stops a `warn` partial from becoming permanent, and
    GOV-003 is a meta-control, which sets the exit code at every rung."""
    document = _with_control(
        "warn",
        verify=[
            {
                "kind": "file",
                "assert": "precommit_hook_present",
                "args": {"id": "gitleaks"},
                "partial": {"unverified": "the runtime half", "expires": "2020-01-01"},
            }
        ],
    )
    assert _run(tmp_path, document) == 1
    out = capsys.readouterr().out
    assert "GOV-003" in out
    assert "AGT-001" in out


def test_warn_is_reported_before_the_blocking_results(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A `warn` result sets no exit code, so the report is the only place it is
    surfaced. It goes above the tier sections a reader scans for failures."""
    _run(tmp_path, _with_control("warn"))
    out = capsys.readouterr().out
    assert out.index("Warn — reported, does not set the exit code") < out.index("Tier 1")
    assert out.index("AGT-001") < out.index("Tier 1")


def test_advisory_keeps_its_place_in_the_tier_order(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _run(tmp_path, _with_control("advisory"))
    out = capsys.readouterr().out
    assert "Warn —" not in out
    assert out.index("Tier 2") < out.index("AGT-001")
