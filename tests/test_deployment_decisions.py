"""What this repository has deliberately not deployed, and why.

[ADR 0042](../docs/adr/0042-a-deploying-skill-reads-local-configuration.md)
revision 2. Phase 5 asks that a deployment behind because nobody redeployed is
distinguishable from one behind because the release would revert a narrowing
this register holds — *"the first is a chore; the second is a decision, and
reporting them the same way trains everyone to ignore both."*

The distinction is only worth having if the record cannot quietly stop being
true, so most of this file is about the four ways it can: an entry that has
expired, one the repository has already moved past, one naming a skill nothing
here stamps, and — from
[ADR 0043](../docs/adr/0043-a-declination-is-reconciled-against-the-installed-skill.md)
— one whose skill is **installed** at a later release than it names. Each
fails; none of them is a deployment anyone owes.

The fourth is the one that had been stated and not applied: the report printed
*"a declination covers the version it names and no later one"* underneath an
entry while comparing that entry against nothing of the sort. Its tests carry
the weight of the third state as well — a run that cannot see an inventory must
say so rather than report agreement, because CI has no plugins installed and a
rule that read absence as coverage would be right only where nobody could check.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path

import pytest

from conftest import REPO_ROOT, make_repo
from register_check.cli import main
from register_check.deployments import (
    DECISIONS,
    BadDecisions,
    Declination,
    Inventory,
    decision_problems,
    read_decisions,
    read_inventory,
    unreconciled,
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

    **What may not ship is the decision, not the mechanism.** An earlier version
    of this test banned the *filename* from everything under `plugins/`, and the
    sweep template broke it by telling an adopter where to record a declination
    of their own — which is the mechanism working rather than posture leaking.
    A rule that fires on the shipped instructions is a rule aimed at the wrong
    thing.
    """
    register = (REPO_ROOT / "controls.yaml").read_text(encoding="utf-8")
    assert "declined:" not in register
    ours = read_decisions(Repo(REPO_ROOT))
    assert ours, "this test is vacuous unless something is declined"
    for path in (REPO_ROOT / "plugins").rglob("*"):
        if not path.is_file() or path.suffix not in {".yaml", ".yml", ".json", ".md"}:
            continue
        text = path.read_text(encoding="utf-8")
        for entry in ours:
            assert f"{entry.skill}@{entry.version}" not in text, path
            assert entry.reason[:40] not in text, path


def test_the_file_lives_beside_the_register() -> None:
    """The location, asserted so it cannot drift into a tool's directory."""
    assert DECISIONS == "deployment-decisions.yaml"
    assert (REPO_ROOT / DECISIONS).is_file()


# --- ADR 0043: reconciled against what is installed ---------------------------

DECLINED_AT = (
    Declination(
        skill="lint-md",
        version="1.0.7",
        reason="writes what this register forbids",
        review_by=datetime.date(2026, 11, 27),
    ),
)

#: Stamped at the version being declined, so the *deployment* comparison stays
#: silent and every assertion below is about the inventory alone.
STAMPED = {"lint-md": "1.0.6"}


def _problems(installed: Inventory) -> list[str]:
    return decision_problems(DECLINED_AT, STAMPED, TODAY, installed)


def _inventory_file(tmp_path: Path, plugins: dict[str, list[dict[str, str]]]) -> Path:
    target = tmp_path / "installed_plugins.json"
    target.write_text(json.dumps({"version": 2, "plugins": plugins}), encoding="utf-8")
    return target


def test_a_later_installed_release_re_opens_the_record() -> None:
    """The state this repository was in, and the report that did not say so.

    `lint-md` was updated to 1.0.8 while the record named 1.0.7, and the command
    exited 0 with the entry printed as live. Nothing about the record had
    changed; what it was about had moved out from under it.
    """
    problems = _problems(Inventory({"lint-md": "1.0.8"}))
    assert len(problems) == 1
    assert "installed at 1.0.8" in problems[0]
    assert "renewed against the new release or deleted" in problems[0]


def test_the_release_it_names_is_still_covered() -> None:
    """Strictly later, not later-or-equal.

    A record naming the installed version is the ordinary state a declination is
    written in — it is *this* release we are declining — so equality must be
    silence. `_both_parse_and_stamp_is_newer` uses `>=` for the stamp because
    that question is the opposite one: whether the repository moved past it.
    """
    assert _problems(Inventory({"lint-md": "1.0.7"})) == []


def test_an_older_installed_release_is_not_a_problem() -> None:
    """Nobody has taken the release yet, which is not a fault in the record."""
    assert _problems(Inventory({"lint-md": "1.0.6"})) == []


def test_a_two_digit_component_compares_as_a_number() -> None:
    """1.0.10 is later than 1.0.9, which a string comparison gets backwards."""
    assert _problems(Inventory({"lint-md": "1.0.10"})) != []
    assert _problems(Inventory({"lint-md": "1.0.70"})) != []


def test_an_unparseable_installed_version_never_reports_superseded() -> None:
    """Both sides must parse, for `_both_parse_and_stamp_is_newer`'s reason.

    A version that sorted below everything would be *above* nothing, but the
    mirror bug is the dangerous one: an empty key comparing high would report a
    live declination as superseded and tell somebody to delete it.
    """
    assert _problems(Inventory({"lint-md": "main-4f21a9c"})) == []


def test_a_version_that_does_not_compare_is_reported_rather_than_dropped() -> None:
    """Silence would be indistinguishable from having checked and agreed."""
    notes = unreconciled(DECLINED_AT, Inventory({"lint-md": "main-4f21a9c"}))
    assert len(notes) == 1
    assert "does not compare as a dotted version" in notes[0]


def test_a_missing_inventory_is_reported_rather_than_read_as_agreement() -> None:
    """The third state, and the reason ADR 0043 part 2 exists.

    CI has no plugins installed. A rule that read "not found" as "still covered"
    would be correct on a developer's machine and silently vacuous everywhere
    the repository is actually audited.
    """
    inventory = Inventory({}, "no plugin inventory at /nowhere")
    assert _problems(inventory) == []
    notes = unreconciled(DECLINED_AT, inventory)
    assert notes == ["lint-md@1.0.7: no plugin inventory at /nowhere"]


def test_a_skill_absent_from_a_readable_inventory_says_so() -> None:
    """Different from an unreadable one: here we looked, and it is not there."""
    notes = unreconciled(DECLINED_AT, Inventory({"adr-toolkit": "0.1.13"}))
    assert notes == ["lint-md@1.0.7: lint-md is not installed here"]


def test_the_marketplace_suffix_is_not_part_of_the_skill_name(tmp_path: Path) -> None:
    """`lint-md@ee-skills` is the plugin; `lint-md` is what a stamp names."""
    path = _inventory_file(tmp_path, {"lint-md@ee-skills": [{"version": "1.0.8"}]})
    assert read_inventory(path).version_of("lint-md") == "1.0.8"


def test_the_later_of_two_installed_scopes_wins(tmp_path: Path) -> None:
    """Covering the older of two installations covers the copy that will not run."""
    path = _inventory_file(
        tmp_path,
        {"lint-md@ee-skills": [{"version": "1.0.6"}, {"version": "1.0.8"}]},
    )
    assert read_inventory(path).version_of("lint-md") == "1.0.8"


def test_a_malformed_inventory_is_reported_rather_than_raised(tmp_path: Path) -> None:
    """Never raises. A home directory laid out unusually may not fail a report.

    `deployment-decisions.yaml` raises in the same situation and that asymmetry
    is deliberate: the record is this repository's own tracked file, where the
    inventory is the machine's, and the run has to work on a machine that has
    none.
    """
    target = tmp_path / "installed_plugins.json"
    target.write_text("{not json", encoding="utf-8")
    inventory = read_inventory(target)
    assert inventory.versions == {}
    assert inventory.unreadable is not None and "could not be read" in inventory.unreadable


def test_an_inventory_without_a_plugins_object_is_reported(tmp_path: Path) -> None:
    target = tmp_path / "installed_plugins.json"
    target.write_text(json.dumps({"version": 2}), encoding="utf-8")
    assert read_inventory(target).unreadable is not None


def test_the_command_fails_over_a_record_the_inventory_has_moved_past(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """End to end, and the exit code is the point.

    A stale *deployment* is a recommendation and exits 0; a stale *record* is a
    claim that has stopped being true. An entry the installed release has moved
    past is the second, and joins the expired entry in exiting 1.
    """
    root = tmp_path / "repo"
    make_repo(
        root,
        {
            "README.md": "# x\n",
            # Stamped at the declined release's predecessor, so the two rules
            # that would otherwise also fire — nothing stamps this skill, and
            # the repository has already deployed past it — both stay silent
            # and the exit code below is about the inventory alone.
            ".markdownlint.yaml": (
                "# ee-control: DOC-001  ee-skill: lint-md@1.0.6  "
                "register: v0.5.0  register-contract: 5\ndefault: true\n"
            ),
            DECISIONS: (
                "declined:\n"
                "  - skill: lint-md\n"
                '    version: "1.0.7"\n'
                "    reason: writes what this register forbids\n"
                "    review_by: 2026-11-27\n"
            ),
        },
    )
    inventory = _inventory_file(tmp_path, {"lint-md@ee-skills": [{"version": "1.0.8"}]})
    code = main(
        [
            "--repo", str(root),
            "--register", str(REPO_ROOT / "controls.yaml"),
            "deployments",
            "--plugin", str(REPO_ROOT / "plugins/control-register"),
            "--decisions", str(root / DECISIONS),
            "--installed", str(inventory),
        ]
    )
    out = capsys.readouterr().out
    assert code == 1
    assert "installed at 1.0.8" in out

    # Same commit, same record, a machine with no plugins: the question is
    # unanswered rather than answered in the repository's favour.
    code = main(
        [
            "--repo", str(root),
            "--register", str(REPO_ROOT / "controls.yaml"),
            "deployments",
            "--plugin", str(REPO_ROOT / "plugins/control-register"),
            "--decisions", str(root / DECISIONS),
            "--installed", str(tmp_path / "absent.json"),
        ]
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "Not reconciled against an installed release" in out
