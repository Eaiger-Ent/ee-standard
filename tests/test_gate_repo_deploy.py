"""`gate-repo` deploys onto a repo with none of its config, and it verifies — partly.

The sixth and last gate, and the only one that changes something outside the
repository. Its control's only locus is `remote`, which made it the one gate
with no file to write, no stamp to leave, and nothing observable until Phase 3
implements `kind: remote`. A gate that cannot be watched working is what this
project's review record keeps re-opening criteria over.

So the ruleset is **recorded** before it is applied, and this file is about the
record. Everything below verifies *intent*: that the repository writes down the
ruleset the register requires, that a weakened record fails, and that the record
is stamped. None of it verifies platform state, and the tests say so where it
matters — the remote block reports `SKIPPED (no credentials)` throughout, which
is why every deployed run here exits `3` rather than `0`.

`test_the_recorded_ruleset_is_valid_json_once_the_comments_are_stripped` is the
one that keeps the two halves connected: the record is JSONC so it can carry a
stamp, and GitHub's API takes strict JSON, so the file the gate writes has to
survive the filter the gate applies to it.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

import pytest

from conftest import REPO_ROOT, make_repo
from standard_check.cli import main
from standard_check.register import Register, load_register

SKILL = REPO_ROOT / "plugins/ee-standard/skills/gate-repo"
REGISTER_PATH = REPO_ROOT / "controls.yaml"
SKILL_VERSION = "0.1.0"
RULESET_PATH = ".github/rulesets/default-branch.json"

def _register() -> Register:
    register, errors = load_register(REGISTER_PATH)
    assert register is not None, errors
    return register


def _ci_args() -> dict[str, object]:
    """CI-001's `ruleset_recorded_matches_register` block, `args:`.

    Every value the skill substitutes comes from here, so a test that hard-coded
    one would be testing a second copy of the register rather than the register.
    """
    control = next(c for c in _register().controls if c.id == "CI-001")
    block = next(b for b in control.verify if b.assert_name == "ruleset_recorded_matches_register")
    return dict(block.args)


def _required_checks() -> list[str]:
    checks = _ci_args()["required_checks"]
    assert isinstance(checks, list), "the register's `required_checks:` must be a list"
    return [str(entry) for entry in checks]


def _gating_workflow() -> str:
    """A workflow producing exactly the checks the register requires.

    From register contract 19 a required check must be produced by a job in a
    gating workflow, so an adopter with no such workflow has nothing a ruleset
    could require. Built from `required_checks` rather than written out: the job
    ids *are* the contexts, and that identity is the thing being tested.
    """
    jobs = "".join(
        f"  {check}:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo {check}\n"
        for check in _required_checks()
    )
    return "name: CI\n\non:\n  push:\n    branches: [main]\n  pull_request:\n\njobs:\n" + jobs


# A repository an adopter might bring: some source, a workflow that gates, and
# no branch protection recorded anywhere.
_ADOPTER = {
    "src/app.py": 'def main() -> None:\n    print("hello")\n',
    ".github/workflows/ci.yml": _gating_workflow(),
}


def _render(template: str, register: Register) -> str:
    args = _ci_args()
    contexts = ", ".join(f'{{ "context": "{check}" }}' for check in _required_checks())
    text = template
    for placeholder, value in {
        "{{RULESET_NAME}}": "default-branch-protection",
        "{{REQUIRED_CHECKS}}": contexts,
        "{{REQUIRE_BRANCHES_UP_TO_DATE}}": json.dumps(args["require_branches_up_to_date"]),
        "{{SKILL_VERSION}}": SKILL_VERSION,
        "{{REGISTER_VERSION}}": register.version,
        "{{REGISTER_CONTRACT}}": str(register.register_contract),
    }.items():
        text = text.replace(placeholder, value)
    assert "{{" not in text, f"a placeholder was not filled: {text}"
    return text


def _body(template: str) -> str:
    """The template's payload, after the marker that separates it from prose."""
    return template.split("// --- .github/rulesets/default-branch.json ---\n", 1)[1]


def _deploy(root: Path, register: Register) -> None:
    """Write the record, as Step 1 of the skill describes.

    Step 2 — the API call — is not simulated and could not usefully be. What it
    changes is platform state, which is exactly what nothing here may stand in
    for.
    """
    target = root / RULESET_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        _render(_body((SKILL / "templates/default-branch.json").read_text()), register),
        encoding="utf-8",
    )


def _stripped(root: Path) -> Any:
    """The recorded ruleset as GitHub would receive it — the gate's own filter.

    `grep -v '^[[:space:]]*//'` is what Step 2 pipes the file through, so this
    is the payload and not a convenience view of it.
    """
    text = (root / RULESET_PATH).read_text(encoding="utf-8")
    body = "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("//")
    )
    parsed = json.loads(body)
    assert isinstance(parsed, dict)
    return parsed


def _replace_rules(root: Path, rules: object) -> None:
    """Write the record back with different rules, keeping its stamp.

    Serialised as strict JSON with the stamp restored as the file's one comment,
    because a rewrite that dropped it would fail `provenance_stamp_present` and
    the test would then pass for the wrong reason.
    """
    path = root / RULESET_PATH
    stamp = next(
        line for line in path.read_text(encoding="utf-8").splitlines() if "ee-control:" in line
    )
    document = _stripped(root)
    document["rules"] = rules
    body = json.dumps(document, indent=2)
    path.write_text("{\n" + stamp + body[1:], encoding="utf-8")
    make_repo(root, {})


def _verdict(root: Path, capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    code = main(
        ["--repo", str(root), "--register", str(REGISTER_PATH), "run", "--control", "CI-001"]
    )
    return code, capsys.readouterr().out


@pytest.fixture
def deployed(tmp_path: Path) -> Path:
    make_repo(tmp_path, _ADOPTER)
    _deploy(tmp_path, _register())
    make_repo(tmp_path, {})  # re-add and commit what the deployment wrote
    return tmp_path


def _rewrite(root: Path, edit: object) -> None:
    path = root / RULESET_PATH
    path.write_text(edit(path.read_text(encoding="utf-8")), encoding="utf-8")  # type: ignore[operator]
    make_repo(root, {})


def test_before_deploying_the_record_is_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The starting state. Exit 1, not 3 — a missing record is a verified failure."""
    make_repo(tmp_path, _ADOPTER)
    code, out = _verdict(tmp_path, capsys)
    assert code == 1
    assert "is not tracked" in out
    assert "no tracked file carries a provenance stamp" in out


def test_after_deploying_the_record_verifies_and_the_platform_does_not(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The criterion, and the two halves said separately.

    Exit `3`, never `0`. What is verified is that the repository records the
    ruleset the register requires. What is not verified — by anything, yet — is
    that GitHub is enforcing it, and reporting this as a clean pass would claim
    a locus no code has touched.
    """
    code, out = _verdict(deployed, capsys)
    assert code == 3, out
    assert "✓ file: ruleset_recorded_matches_register" in out
    assert "intent only" in out
    assert "✓ file: provenance_stamp_present" in out
    assert "SKIPPED (no credentials)" in out
    assert "incomplete" in out


def test_the_recorded_ruleset_is_valid_json_once_the_comments_are_stripped(
    deployed: Path,
) -> None:
    """The record is JSONC so it can carry a stamp; the API takes strict JSON.

    The gate's own Step 2 pipes the file through `grep -v '^[[:space:]]*//'`
    before POSTing. If a comment ever appeared at the end of a line rather than
    on one of its own, that filter would leave it behind and the API call would
    fail at deploy time rather than here.
    """
    text = (deployed / RULESET_PATH).read_text(encoding="utf-8")
    stripped = subprocess.run(
        ["grep", "-v", "^[[:space:]]*//"],
        input=text,
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    document = json.loads(stripped)
    assert document["enforcement"] == "active"
    assert document["conditions"]["ref_name"]["include"] == ["~DEFAULT_BRANCH"]
    assert {rule["type"] for rule in document["rules"]} == {
        "pull_request",
        "required_status_checks",
        "non_fast_forward",
    }


def test_the_recorded_stamp_records_the_register_it_came_from(deployed: Path) -> None:
    register = _register()
    text = (deployed / RULESET_PATH).read_text(encoding="utf-8")
    stamp = re.search(
        r"ee-control: (\S+)\s+ee-skill: (\S+)\s+register: v(\S+)\s+register-contract: (\d+)", text
    )
    assert stamp is not None
    assert stamp.groups() == (
        "CI-001",
        f"gate-repo@{SKILL_VERSION}",
        register.version,
        str(register.register_contract),
    )


@pytest.mark.parametrize(
    ("rule", "expected"),
    [
        ("pull_request", "written to directly"),
        ("required_status_checks", "merge unchecked"),
        ("non_fast_forward", "history on the default branch can be rewritten"),
    ],
)
def test_removing_any_required_rule_is_caught(
    deployed: Path, capsys: pytest.CaptureFixture[str], rule: str, expected: str
) -> None:
    """Each of the register's three requirements, watched failing on its own.

    CI-001 is `variance: forbidden` with `baseline: null`. There is no tolerated
    list, so a record that drops one requirement is not a narrowing — it is the
    control not being met.
    """
    _rewrite(deployed, lambda text: text.replace(f'"type": "{rule}"', '"type": "creation"'))
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "CI-001   FAIL" in out
    assert expected in out


def test_an_evaluate_only_ruleset_is_not_a_gate(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """GitHub accepts `evaluate`, and it blocks nothing.

    A ruleset that reports what would have happened is a control declared and
    unreachable — theme T-3, in the one domain where the checker cannot yet see
    the platform to catch it any other way.
    """
    _rewrite(
        deployed,
        lambda text: text.replace('"enforcement": "active"', '"enforcement": "evaluate"'),
    )
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "not 'active'" in out
    assert "blocks nothing" in out


def test_a_ruleset_naming_the_branch_is_caught(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`main` stops protecting the default branch the day the default moves."""
    _rewrite(deployed, lambda text: text.replace('"~DEFAULT_BRANCH"', '"refs/heads/main"'))
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "~DEFAULT_BRANCH" in out
    assert "the day the default moves" in out


def test_an_untracked_record_is_not_a_record(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A ruleset git does not carry is not one anybody can review.

    And it is the worst case rather than a minor one: the remote block cannot be
    reached without credentials either, so an untracked record would mean
    *nothing at all* about this control had been verified.
    """
    root = tmp_path / "untracked"
    make_repo(root, {**_ADOPTER, ".gitignore": ".github/rulesets/\n"})
    _deploy(root, _register())
    code, out = _verdict(root, capsys)
    assert code == 1
    assert "is not tracked" in out


def test_removing_the_stamp_is_caught(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _rewrite(
        deployed,
        lambda text: "\n".join(
            line for line in text.splitlines() if "ee-control:" not in line
        )
        + "\n",
    )
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "provenance stamp" in out


def test_the_register_states_the_requirements_once(deployed: Path) -> None:
    """The recorded file and the remote check read the same `args:`.

    Two blocks would be two definitions of "protected", free to drift from each
    other — and the drift would be invisible until Phase 3 made the second one
    executable, which is the worst moment to discover it.
    """
    control = next(c for c in _register().controls if c.id == "CI-001")
    recorded = next(
        b for b in control.verify if b.assert_name == "ruleset_recorded_matches_register"
    )
    remote = next(b for b in control.verify if b.assert_name == "default_branch_ruleset_satisfies")
    requirements = {k: v for k, v in recorded.args.items() if k != "path"}
    assert requirements == dict(remote.args)
    assert requirements == {
        "require_pull_request": True,
        "require_status_checks": True,
        "allow_force_push": False,
        "required_checks": ["standard-check", "lint-md"],
        "require_branches_up_to_date": True,
    }


def test_the_skill_confirms_before_it_calls() -> None:
    """The one property no fixture can hold, stated where it can be checked.

    This gate changes state outside the repository, and the ruleset is in force
    the moment the call returns. No test can prove a model asks first — what can
    be held is that the skill says to, in terms that name the blast radius, and
    that it does not treat an earlier plan approval as covering it.
    """
    text = " ".join((SKILL / "SKILL.md").read_text(encoding="utf-8").split())
    assert "Ask via AskUserQuestion before the API call, every time" in text
    assert "This confirmation is not waivable by an earlier approval" in text
    assert "It affects every collaborator, not only you" in text
    # And the failure path: a weaker ruleset is never the retry.
    assert "do not retry with a weaker ruleset" in text


# --- What a recorded rule *does*, from register contract 19 ------------------


@pytest.mark.parametrize("rule", ["pull_request", "required_status_checks"])
def test_a_rule_without_parameters_is_a_payload_the_api_rejects(
    deployed: Path, capsys: pytest.CaptureFixture[str], rule: str
) -> None:
    """The defect this contract was written for, watched failing.

    Until contract 19 the template wrote every rule as a bare `{ "type": ... }`,
    and GitHub's REST schema requires `parameters` on both of these. The apply
    call returned 422, so `gate-repo` could not deploy the one control it exists
    for — and the assert read rule *names*, so the record looked complete.
    """
    document = _stripped(deployed)
    for entry in document["rules"]:
        if entry["type"] == rule:
            entry.pop("parameters")
    _replace_rules(deployed, document["rules"])
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "no 'parameters' object" in out
    assert "422" in out


def test_parameters_on_a_rule_that_takes_none_is_caught(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The same property in the other direction: the API rejects these too."""
    document = _stripped(deployed)
    for entry in document["rules"]:
        if entry["type"] == "non_fast_forward":
            entry["parameters"] = {"anything": True}
    _replace_rules(deployed, document["rules"])
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "does not accept" in out


def test_a_status_check_rule_naming_no_check_is_not_a_gate(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A rule requiring zero checks lets a pull request merge with CI red.

    This is what the recorded ruleset said before contract 19, and
    `require_status_checks: true` was satisfied by it — the contract-14 shape,
    where a verdict turns on a rule being present rather than on what it does.
    """
    document = _stripped(deployed)
    for entry in document["rules"]:
        if entry["type"] == "required_status_checks":
            entry["parameters"]["required_status_checks"] = []
    _replace_rules(deployed, document["rules"])
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "does not require" in out
    assert "no check at all" in out


def test_dropping_one_required_check_is_caught(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Requiring some of them is not requiring them."""
    kept, dropped = _required_checks()[0], _required_checks()[1]
    document = _stripped(deployed)
    for entry in document["rules"]:
        if entry["type"] == "required_status_checks":
            entry["parameters"]["required_status_checks"] = [{"context": kept}]
    _replace_rules(deployed, document["rules"])
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert dropped in out


def test_a_required_check_no_gating_job_produces_is_caught(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The cross-check that keeps `required_checks` from drifting from the workflows.

    A renamed job leaves the register naming a context nothing reports, and
    GitHub waits forever for it — every merge blocked rather than one gated. It
    fails here instead, where the two can still be reconciled.
    """
    workflow = deployed / ".github/workflows/ci.yml"
    workflow.write_text(
        workflow.read_text(encoding="utf-8").replace(
            f"  {_required_checks()[0]}:", "  renamed-job:"
        ),
        encoding="utf-8",
    )
    make_repo(deployed, {})
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "produced by no job in a gating workflow" in out


def test_a_required_check_from_a_suppressed_job_is_caught(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A required check that always passes is theme T-3 wearing a ruleset.

    GOV-001 catches a suppressed *step*; this is the same failure one level up,
    arriving through the rule that is supposed to make the check matter.
    """
    workflow = deployed / ".github/workflows/ci.yml"
    check = _required_checks()[0]
    workflow.write_text(
        workflow.read_text(encoding="utf-8").replace(
            f"  {check}:\n    runs-on: ubuntu-latest\n",
            f"  {check}:\n    runs-on: ubuntu-latest\n    continue-on-error: true\n",
        ),
        encoding="utf-8",
    )
    make_repo(deployed, {})
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "cannot fail" in out


def test_a_non_strict_policy_disagreeing_with_the_register_is_caught(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """With it off, a check that passed against stale code counts."""
    document = _stripped(deployed)
    for entry in document["rules"]:
        if entry["type"] == "required_status_checks":
            entry["parameters"]["strict_required_status_checks_policy"] = False
    _replace_rules(deployed, document["rules"])
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "strict_required_status_checks_policy" in out


def test_the_recorded_payload_matches_what_this_repository_has_on_the_platform() -> None:
    """This repository's own record, against a response nobody transcribed twice.

    The live ruleset is not fetched here — a test that needed credentials would
    report SKIPPED on every machine that matters. What is held instead is the
    property the first transcription broke: the record names the checks, and
    they are the ones the register requires.
    """
    document = json.loads(
        "\n".join(
            line
            for line in (REPO_ROOT / RULESET_PATH).read_text(encoding="utf-8").splitlines()
            if not line.lstrip().startswith("//")
        )
    )
    rule = next(r for r in document["rules"] if r["type"] == "required_status_checks")
    contexts = [entry["context"] for entry in rule["parameters"]["required_status_checks"]]
    assert contexts == _required_checks()
