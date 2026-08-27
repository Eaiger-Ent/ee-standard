"""What this repository has deliberately not deployed, and why.

[ADR 0042](../docs/adr/0042-a-deploying-skill-reads-local-configuration.md)
revision 2. Phase 5 asks that a deployment behind because nobody redeployed is
distinguishable from one behind because the release would revert a narrowing
this register holds — *"the first is a chore; the second is a decision, and
reporting them the same way trains everyone to ignore both."*

The distinction is only worth having if the record cannot quietly stop being
true, so most of this file is about the three ways it can: an entry that has
expired, one the repository has already moved past, and one naming a skill
nothing here stamps. Each fails; none of them is a deployment anyone owes.
"""

from __future__ import annotations

import datetime
from pathlib import Path

import pytest

from conftest import REPO_ROOT, make_repo
from register_check.cli import main
from register_check.deployments import (
    DECISIONS,
    BadDecisions,
    Declination,
    decision_problems,
    read_decisions,
)
from register_check.repo import Repo

TODAY = datetime.date(2026, 8, 27)


def _repo(tmp_path: Path, text: str | None) -> Repo:
    files = {"README.md": "# x\n"}
    if text is not None:
        files[DECISIONS] = text
    return make_repo(tmp_path, files)


# --- reading the record ----------------------------------------------------


def test_this_repository_records_the_lint_md_declination() -> None:
    """The live entry, read from the file this repository actually ships."""
    declined = read_decisions(Repo(REPO_ROOT))
    assert [d.skill for d in declined] == ["lint-md"]
    assert declined[0].version == "1.0.7"
    assert declined[0].adr is not None and "0042" in declined[0].adr
    assert declined[0].review_by > TODAY


def test_an_absent_file_is_no_declinations(tmp_path: Path) -> None:
    """The ordinary case: a repository that has declined nothing."""
    assert read_decisions(_repo(tmp_path, None)) == ()


def test_a_malformed_file_raises_rather_than_reading_as_empty(tmp_path: Path) -> None:
    """The failure that would be invisible.

    Reading an unparseable record as "no declinations" reports every declined
    deployment as a chore nobody got to — the exact opposite of what the record
    says — and the report would look entirely ordinary while doing it.
    """
    with pytest.raises(BadDecisions):
        read_decisions(_repo(tmp_path, "declined: [\n"))


@pytest.mark.parametrize(
    ("text", "because"),
    [
        ("declined: not-a-list\n", "'declined' must be a list"),
        ("- a\n- b\n", "must be a mapping"),
        ("declined:\n  - skill: x\n", "is missing"),
        ('declined:\n  - {skill: x, version: "1", reason: y, review_by: soon}\n', "ISO date"),
    ],
)
def test_a_record_that_cannot_be_acted_on_is_refused(
    tmp_path: Path, text: str, because: str
) -> None:
    with pytest.raises(BadDecisions) as caught:
        read_decisions(_repo(tmp_path, text))
    assert because in str(caught.value)


# --- the three ways a record stops being true ------------------------------


def _declination(**over: object) -> Declination:
    fields: dict[str, object] = {
        "skill": "lint-md",
        "version": "1.0.7",
        "reason": "it would revert a narrowing",
        "review_by": datetime.date(2026, 11, 27),
    }
    fields.update(over)
    return Declination(**fields)  # type: ignore[arg-type]


def test_a_current_declination_is_no_problem() -> None:
    assert decision_problems((_declination(),), {"lint-md": "1.0.6"}, TODAY) == []


def test_an_expired_declination_is_a_problem() -> None:
    """The reason `variance: justified` was removed at register contract 3.

    A declination with no live expiry is a permanent exemption wearing a
    reason. GOV-003 fails a control past its review date, and a declination is
    the stronger claim of the two — it says a release should not be taken.
    """
    problems = decision_problems(
        (_declination(review_by=datetime.date(2026, 1, 1)),), {"lint-md": "1.0.6"}, TODAY
    )
    assert len(problems) == 1
    assert "that date has passed" in problems[0]


def test_a_declination_the_repository_moved_past_is_a_problem() -> None:
    """The record describes a decision that no longer applies.

    Deployed at 1.0.7 while declining 1.0.7 means the declination was taken
    back and the entry never removed — and an entry nobody removes is how the
    file stops being read.
    """
    problems = decision_problems((_declination(),), {"lint-md": "1.0.7"}, TODAY)
    assert len(problems) == 1 and "already deployed at 1.0.7" in problems[0]


def test_a_declination_naming_a_skill_nothing_stamps_is_a_problem() -> None:
    problems = decision_problems((_declination(skill="ghost"),), {"lint-md": "1.0.6"}, TODAY)
    assert len(problems) == 1 and "does not exist" in problems[0]


def test_a_version_that_does_not_parse_never_claims_to_be_superseded() -> None:
    """The comparison declines rather than guessing.

    `_version_key` is not a semver implementation and does not need to be: the
    only question is whether the repository has moved past the declined
    release, and a version it cannot read simply never answers yes.
    """
    assert decision_problems(
        (_declination(version="2026-Q3"),), {"lint-md": "1.0.6"}, TODAY
    ) == []


# --- the command -----------------------------------------------------------


def _run(root: Path, capsys: pytest.CaptureFixture[str]) -> tuple[int, str, str]:
    code = main(
        [
            "--repo", str(root),
            "--register", str(REPO_ROOT / "controls.yaml"),
            "deployments",
            "--plugin", str(REPO_ROOT / "plugins/control-register"),
            "--decisions", str(root / DECISIONS),
        ]
    )
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_the_command_reports_this_repository_s_declination(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main(
        ["--repo", str(REPO_ROOT), "--register", str(REPO_ROOT / "controls.yaml"), "deployments"]
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "Deliberately not deployed:" in out
    assert "lint-md@1.0.7" in out and "DECLINED until" in out
    # The property that makes it a record rather than an opt-out, said in the
    # report rather than only in the ADR.
    assert "covers the version it names and no later one" in out


def test_a_stale_record_fails_where_a_stale_deployment_does_not(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The asymmetry this command turns on.

    Staleness of a *deployment* is a recommendation and exits 0 — that is
    `docs/00-concepts.md` § Notify, never redeploy. Staleness of the *record* is
    a claim that has stopped being true, and exits 1.
    """
    root = tmp_path / "repo"
    make_repo(
        root,
        {
            "README.md": "# x\n",
            DECISIONS: (
                "declined:\n"
                "  - skill: lint-md\n"
                '    version: "1.0.7"\n'
                "    reason: it would revert a narrowing\n"
                "    review_by: 2025-01-01\n"
            ),
        },
    )
    code, out, _ = _run(root, capsys)
    assert code == 1
    assert "stopped describing reality" in out


def test_a_malformed_record_exits_two_rather_than_reporting(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "repo"
    make_repo(root, {"README.md": "# x\n", DECISIONS: "declined: [\n"})
    code, out, err = _run(root, capsys)
    assert code == 2
    assert out == "" and "not valid YAML" in err


def test_the_register_does_not_carry_the_declination() -> None:
    """ADR 0022 requirement 6, applied to this record.

    A declination is this repository's posture. `tests/test_posture.py` holds
    the same boundary for the platform-token choice; this holds it for the one
    Phase 5 introduced, because the file sits beside `controls.yaml` and the
    obvious wrong move is to put it inside.
    """
    register = (REPO_ROOT / "controls.yaml").read_text(encoding="utf-8")
    assert "declined:" not in register
    for path in (REPO_ROOT / "plugins").rglob("*"):
        if path.is_file() and path.suffix in {".yaml", ".yml", ".json", ".md"}:
            assert "deployment-decisions" not in path.read_text(encoding="utf-8"), path


def test_the_file_lives_beside_the_register() -> None:
    """The location, asserted so it cannot drift into a tool's directory."""
    assert DECISIONS == "deployment-decisions.yaml"
    assert (REPO_ROOT / DECISIONS).is_file()
