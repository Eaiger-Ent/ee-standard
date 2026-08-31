"""A plan limit is recorded, never tolerated (ADR 0047).

The mechanism that lets a Tier-1 control not hold, which makes its guardrails
the point rather than a detail. Every rule from the ADR that can be tested is
tested here, and the two that cannot are stated in `platform_limits.py`'s
docstring rather than pretended away.

The failure it exists to prevent is not the two controls — it is the other
thirteen. A conformance run that can never be green is one people stop reading,
so a permanently red gate degrades every control that does hold.
"""

from __future__ import annotations

import datetime
from pathlib import Path

import pytest

from conftest import a_register, make_repo
from register_check.platform_limits import (
    BadPlatformLimits,
    limit_for,
    read_limits,
)
from register_check.register import Control, Register, VerifyBlock
from register_check.repo import Repo
from register_check.runner import Verdict, _waived_or_failed, exit_code

FUTURE = (datetime.date.today() + datetime.timedelta(days=90)).isoformat()
PAST = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()


def _record(review_by: str) -> str:
    return (
        "platform_limits:\n"
        "  - control: CI-001\n"
        "    assert: default_branch_ruleset_satisfies\n"
        "    plan: github-free-private\n"
        "    lacks: rulesets are GitHub Team and Enterprise only\n"
        f"    review_by: {review_by}\n"
    )


def test_an_absent_file_is_no_limits_rather_than_an_error(tmp_path: Path) -> None:
    assert read_limits(make_repo(tmp_path, {"a.txt": "x"})) == ()


def test_a_malformed_record_raises_rather_than_reading_as_none(tmp_path: Path) -> None:
    """Silence here would turn a dated waiver into a silent failure.

    The same rule `read_decisions` follows, and for the same reason: a report
    that looks ordinary while saying the opposite of what the repository wrote
    down is worse than one that stops.
    """
    repo = make_repo(tmp_path, {"deployment-decisions.yaml": "platform_limits: 3\n"})
    with pytest.raises(BadPlatformLimits):
        read_limits(repo)


@pytest.mark.parametrize(
    "field", ["control", "assert", "plan", "lacks", "review_by"]
)
def test_every_field_is_required(tmp_path: Path, field: str) -> None:
    """No field here is decoration. `lacks` is what the report prints, and
    `review_by` is what stops the entry being permanent."""
    # `control:` carries the list marker, so strip that before matching —
    # otherwise the line survives and the test passes over an intact record.
    lines = [
        ln
        for ln in _record(FUTURE).splitlines()
        if not ln.strip().lstrip("- ").startswith(f"{field}:")
    ]
    text = "\n".join(lines) + "\n"
    if field == "control":
        text = text.replace("    assert:", "  - assert:", 1)  # keep it a list item
    repo = make_repo(tmp_path, {"deployment-decisions.yaml": text})
    with pytest.raises(BadPlatformLimits, match=field):
        read_limits(repo)


def test_a_live_entry_is_read(tmp_path: Path) -> None:
    limits = read_limits(make_repo(tmp_path, {"deployment-decisions.yaml": _record(FUTURE)}))
    assert len(limits) == 1
    assert limits[0].control == "CI-001"
    assert not limits[0].expired(datetime.date.today())


def test_it_matches_on_the_pair_not_the_control(tmp_path: Path) -> None:
    """A control's *other* blocks are not waived by a limit on one of them.

    ADR 0047 rule 2. CI-001's `ruleset_recorded_matches_register` must still
    pass, so the adopter records the ruleset they would enforce and the day the
    plan changes it is one API call rather than a fresh decision.
    """
    limits = read_limits(make_repo(tmp_path, {"deployment-decisions.yaml": _record(FUTURE)}))
    assert limit_for(limits, "CI-001", "default_branch_ruleset_satisfies") is not None
    assert limit_for(limits, "CI-001", "ruleset_recorded_matches_register") is None
    assert limit_for(limits, "SEC-001", "default_branch_ruleset_satisfies") is None


def test_an_expired_entry_reports_expired_rather_than_covering(tmp_path: Path) -> None:
    """Rule 3. A plan is a commercial state that changes on a renewal date."""
    limits = read_limits(make_repo(tmp_path, {"deployment-decisions.yaml": _record(PAST)}))
    assert limits[0].expired(datetime.date.today())


def _remote_block(
    register: Register, control_id: str, assert_name: str
) -> tuple[VerifyBlock, Control]:
    control = next(c for c in register.controls if c.id == control_id)
    return next(b for b in control.verify if b.assert_name == assert_name), control


def test_a_recorded_limit_downgrades_a_failing_block(tmp_path: Path) -> None:
    """Rule 1, at the function that decides it.

    Tested here rather than through a live run because the waiver is only
    reachable from a genuine remote **failure**, and a test that needed an
    unprotected repository on GitHub to exist would be measuring somebody
    else's configuration.
    """
    register = a_register()
    block, control = _remote_block(register, "CI-001", "default_branch_ruleset_satisfies")
    limits = read_limits(make_repo(tmp_path, {"deployment-decisions.yaml": _record(FUTURE)}))
    result = _waived_or_failed(block, "the branch is not protected", control.id, limits)
    assert result.verdict is Verdict.UNAVAILABLE_PLAN
    assert "github-free-private" in result.message
    assert "does not hold" in result.message, (
        "the message reads as a pass — it must say the control does not hold"
    )


def test_an_expired_limit_fails_rather_than_covering(tmp_path: Path) -> None:
    """Rule 3, at the same function. An expired record is not a waiver."""
    register = a_register()
    block, control = _remote_block(register, "CI-001", "default_branch_ruleset_satisfies")
    limits = read_limits(make_repo(tmp_path, {"deployment-decisions.yaml": _record(PAST)}))
    result = _waived_or_failed(block, "the branch is not protected", control.id, limits)
    assert result.verdict is Verdict.FAIL
    assert "expired" in result.message


def test_an_unrecorded_block_still_fails(tmp_path: Path) -> None:
    """The default. A repository with no record gets the verdict it earned."""
    register = a_register()
    block, control = _remote_block(register, "CI-001", "default_branch_ruleset_satisfies")
    result = _waived_or_failed(block, "the branch is not protected", control.id, ())
    assert result.verdict is Verdict.FAIL


def test_the_waived_verdict_still_denies_a_zero_exit() -> None:
    """Rule 1 again, at the exit code. A run carrying one exits 3 at best."""
    assert exit_code([Verdict.PASS, Verdict.UNAVAILABLE_PLAN]) == 3


def test_require_complete_promotes_it_to_a_failure() -> None:
    """Rule 4. The flag means *fail if anything could not be verified*, and this
    is the case it was written for — a repository in this state does not turn it
    on, and that is the visible cost rather than a hole in it."""
    assert exit_code([Verdict.UNAVAILABLE_PLAN], require_complete=True) == 1


def test_this_repository_records_none() -> None:
    """The mechanism must be quiet where it is not needed.

    This repository is public and ruleset-protected. An entry here would be the
    misuse the ADR warns about — waiving a capability the platform does offer.
    """
    from conftest import REPO_ROOT

    assert read_limits(Repo(REPO_ROOT)) == ()
