"""The meta-controls: GOV-001, GOV-002, GOV-003.

Meta-controls return a `Verdict`, not a bool, so that "could not verify" is
expressible (ADR 0016). These tests compare against the enum member rather than
its truthiness: every `Verdict` is truthy, so `assert verdict` would pass for
FAIL and UNCLASSIFIED alike — the false green this repository exists to prevent.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from conftest import FakeGitHub, make_repo, minimal_register, write_register
from register_check.meta import gov_001, gov_002, gov_003
from register_check.register import Register, load_register
from register_check.remote import NoCredentials, Unreadable, Unresolvable
from register_check.repo import Repo
from register_check.runner import Verdict


def _load(root: Path, document: dict[str, Any]) -> tuple[Register, Repo]:
    path = write_register(root, document)
    register, errors = load_register(path)
    assert errors == [], errors
    assert register is not None
    return register, Repo(root)


# Every fixture below declares `on:`. A step in a workflow that runs on neither
# push nor pull_request cannot fail a merge, so from § H1 it is evidence for no
# control — and these tests are about *which* step reaches a control, so without
# a trigger they would all fail for the same unrelated reason.
_ON = "on: [push, pull_request]\n"

_WORKFLOW_FULL_RUN = (
    _ON + "jobs:\n  check:\n    runs-on: ubuntu-latest\n    steps:\n"
    "      - run: uv run register-check\n"
)

_WORKFLOW_SUPPRESSED = _WORKFLOW_FULL_RUN + "        continue-on-error: true\n"


def test_gov_001_passes_when_checker_runs_in_ci(tmp_path: Path) -> None:
    register, repo = _load(tmp_path, minimal_register())
    make_repo(tmp_path, {".github/workflows/check.yml": _WORKFLOW_FULL_RUN})
    verdict, _message = gov_001(register, repo)
    assert verdict is Verdict.PASS


def test_gov_001_fails_with_no_reachable_step(tmp_path: Path) -> None:
    register, repo = _load(tmp_path, minimal_register())
    make_repo(tmp_path, {".github/workflows/check.yml": "jobs: {}\n"})
    verdict, message = gov_001(register, repo)
    assert verdict is Verdict.FAIL
    assert "SEC-001" in message


def test_gov_001_ignores_suppressed_steps(tmp_path: Path) -> None:
    register, repo = _load(tmp_path, minimal_register())
    workflow = (
        _ON + "jobs:\n  check:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - run: uv run register-check\n"
        "        continue-on-error: true\n"
    )
    make_repo(tmp_path, {".github/workflows/check.yml": workflow})
    verdict, _message = gov_001(register, repo)
    assert verdict is Verdict.FAIL


def test_gov_001_full_run_survives_shell_punctuation(tmp_path: Path) -> None:
    """A step that handles the exit code still runs the whole register.

    The old pattern required the CI line to be *exactly* the invocation, so
    wrapping it in error handling flipped GOV-001 from "everything reachable" to
    "SUP-002 and DEV-001 unreachable" without either control changing. A
    reachability test a cosmetic reformat can invert is not measuring
    reachability.
    """
    register, repo = _load(tmp_path, minimal_register())
    workflow = (
        _ON + "jobs:\n  check:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - run: |\n"
        "          uv run register-check && status=0 || status=$?\n"
        '          if [ "$status" -ne 0 ] && [ "$status" -ne 3 ]; then\n'
        '            exit "$status"\n'
        "          fi\n"
    )
    make_repo(tmp_path, {".github/workflows/check.yml": workflow})
    verdict, _message = gov_001(register, repo)
    assert verdict is Verdict.PASS


def test_gov_001_does_not_count_installing_the_checker_as_running_it(
    tmp_path: Path,
) -> None:
    """`pip install register-check` is not evidence that anything is checked.

    An invocation starts a command; it never follows another word. Substring
    matching made installing the tool mark every control reachable at once —
    § A row 4 of the build plan.
    """
    register, repo = _load(tmp_path, minimal_register())
    workflow = (
        _ON + "jobs:\n  check:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - run: pip install register-check\n"
    )
    make_repo(tmp_path, {".github/workflows/check.yml": workflow})
    verdict, message = gov_001(register, repo)
    assert verdict is Verdict.FAIL
    assert "SEC-001" in message


def test_gov_001_reaches_a_control_verified_only_by_file_asserts(tmp_path: Path) -> None:
    """SUP-002 and DEV-001's case: no `kind: command` block at all.

    Before contract 3, reachability was a substring test over the first word of
    each command block, so a control with only file asserts had no token and was
    unreachable *by construction* — it could pass only via the full-run
    short-circuit, never on its own evidence.
    """
    register, repo = _load(tmp_path, minimal_register())
    workflow = (
        _ON + "jobs:\n  check:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - run: uv run register-check assert precommit_hook_present\n"
    )
    make_repo(tmp_path, {".github/workflows/check.yml": workflow})
    verdict, message = gov_001(register, repo)
    assert verdict is Verdict.PASS, message


def test_gov_001_rejects_a_workflow_that_gates_no_merge(tmp_path: Path) -> None:
    """§ H1. A step a human has to click cannot fail a merge.

    Pointing `on:` at `workflow_dispatch` and changing nothing else used to
    leave this control reporting every blocking control reachable — in the same
    run where TST-001 read the same workflow and failed it for exactly this. The
    verdict has to distinguish the two repairs: this control was wired to a
    trigger that gates nothing, which is not the same as never wired.
    """
    register, repo = _load(tmp_path, minimal_register())
    workflow = (
        "on:\n  workflow_dispatch:\n"
        "jobs:\n  check:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - run: uv run register-check\n"
    )
    make_repo(tmp_path, {".github/workflows/check.yml": workflow})
    verdict, message = gov_001(register, repo)
    assert verdict is Verdict.FAIL
    assert "SEC-001" in message
    assert "gates no merge" in message


def test_gov_001_accepts_a_workflow_that_gates_only_pull_requests(tmp_path: Path) -> None:
    """The mirror of the test above: `pull_request` alone is a merge gate."""
    register, repo = _load(tmp_path, minimal_register())
    workflow = (
        "on:\n  pull_request:\n"
        "jobs:\n  check:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - run: uv run register-check\n"
    )
    make_repo(tmp_path, {".github/workflows/check.yml": workflow})
    verdict, message = gov_001(register, repo)
    assert verdict is Verdict.PASS, message


def test_gov_001_does_not_accept_a_different_assert_as_evidence(tmp_path: Path) -> None:
    """Reaching *an* assertion is not reaching *this* control's assertion."""
    register, repo = _load(tmp_path, minimal_register())
    workflow = (
        _ON + "jobs:\n  check:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - run: uv run register-check assert actions-pinned-to-sha\n"
    )
    make_repo(tmp_path, {".github/workflows/check.yml": workflow})
    verdict, message = gov_001(register, repo)
    assert verdict is Verdict.FAIL
    assert "SEC-001" in message


def test_gov_003_fails_an_expired_partial_declaration(tmp_path: Path) -> None:
    """ADR 0017's expiry is enforced by the same mechanism as `review_by`.

    An expiry nothing enforces is what lets "partial" become permanent, which is
    the one objection the ADR raised against its own decision.
    """
    document = minimal_register(
        verify=[
            {
                "kind": "file",
                "assert": "precommit_hook_present",
                "args": {"id": "gitleaks"},
                "partial": {"unverified": "the remote half", "expires": "2001-01-01"},
            }
        ]
    )
    register, repo = _load(tmp_path, document)
    make_repo(tmp_path, {})
    verdict, message = gov_003(register, repo)
    assert verdict is Verdict.FAIL
    assert "partial declaration expired" in message
    assert "the remote half" in message


def _commit(root: Path, message: str) -> None:
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-q",
            "-m",
            message,
        ],
        check=True,
    )


def test_gov_002_fails_when_a_baseline_grows(tmp_path: Path) -> None:
    document = minimal_register(tier=2, baseline="baselines/sec.txt")
    register, repo = _load(tmp_path, document)
    make_repo(tmp_path, {"baselines/sec.txt": "one\n"})
    baseline = tmp_path / "baselines/sec.txt"
    verdict, _message = gov_002(register, repo)
    assert verdict is Verdict.PASS
    baseline.write_text("one\ntwo\n", encoding="utf-8")
    verdict, message = gov_002(register, repo)
    assert verdict is Verdict.FAIL
    assert "1 → 2" in message
    # Shrinking is always fine.
    baseline.write_text("", encoding="utf-8")
    _commit(tmp_path, "shrink")
    verdict, _message = gov_002(register, repo)
    assert verdict is Verdict.PASS


def test_gov_002_fails_when_growth_is_committed(tmp_path: Path) -> None:
    """The CI case: growth is always committed by the time the checker sees it."""
    document = minimal_register(tier=2, baseline="baselines/sec.txt")
    register, repo = _load(tmp_path, document)
    make_repo(tmp_path, {"baselines/sec.txt": "one\n"})
    (tmp_path / "baselines/sec.txt").write_text("one\ntwo\n", encoding="utf-8")
    _commit(tmp_path, "grow the baseline")
    verdict, message = gov_002(register, repo)
    assert verdict is Verdict.FAIL
    assert "1 → 2" in message


def test_gov_002_fails_when_growth_is_on_a_branch(tmp_path: Path) -> None:
    """The pull-request case: compare against the merge-base, not the branch tip."""
    document = minimal_register(tier=2, baseline="baselines/sec.txt")
    register, repo = _load(tmp_path, document)
    make_repo(tmp_path, {"baselines/sec.txt": "one\n"})
    subprocess.run(["git", "-C", str(tmp_path), "checkout", "-q", "-b", "feature"], check=True)
    (tmp_path / "baselines/sec.txt").write_text("one\ntwo\nthree\n", encoding="utf-8")
    _commit(tmp_path, "grow on a branch")
    verdict, message = gov_002(register, repo)
    assert verdict is Verdict.FAIL
    assert "1 → 3" in message


def test_gov_002_passes_when_a_committed_change_shrinks(tmp_path: Path) -> None:
    document = minimal_register(tier=2, baseline="baselines/sec.txt")
    register, repo = _load(tmp_path, document)
    make_repo(tmp_path, {"baselines/sec.txt": "one\ntwo\n"})
    (tmp_path / "baselines/sec.txt").write_text("one\n", encoding="utf-8")
    _commit(tmp_path, "shrink the baseline")
    verdict, _message = gov_002(register, repo)
    assert verdict is Verdict.PASS


def test_gov_002_is_unclassified_with_no_comparison_point(tmp_path: Path) -> None:
    """No commits means no evidence about growth — in either direction.

    Failing closed here would assert a violation the run never observed; passing
    would be the false green. UNCLASSIFIED is the third answer (ADR 0016), and it
    keeps the exit code off 0 without claiming the baseline grew.
    """
    document = minimal_register(tier=2, baseline="baselines/sec.txt")
    register, repo = _load(tmp_path, document)
    make_repo(tmp_path, {"baselines/sec.txt": "one\n"}, commit=False)
    verdict, message = gov_002(register, repo)
    assert verdict is Verdict.UNCLASSIFIED
    assert "cannot determine a comparison point" in message


def test_gov_003_fails_past_review_date(tmp_path: Path) -> None:
    register, repo = _load(tmp_path, minimal_register(review_by="2001-01-01"))
    make_repo(tmp_path, {})
    verdict, message = gov_003(register, repo)
    assert verdict is Verdict.FAIL
    assert "SEC-001" in message


def test_gov_003_passes_before_review_date(tmp_path: Path) -> None:
    register, repo = _load(tmp_path, minimal_register())
    make_repo(tmp_path, {})
    verdict, _message = gov_003(register, repo)
    assert verdict is Verdict.PASS


# --- GOV-001 reads the required checks, from register contract 19 -----------


def _with_required_checks(checks: list[str]) -> dict[str, Any]:
    """A minimal register whose first control also records a ruleset.

    GOV-001 finds the required checks by looking for whichever control carries a
    `ruleset_recorded_matches_register` block, rather than by knowing CI-001 by
    name — a register is free to call that control something else.
    """
    document = minimal_register()
    document["controls"][0]["verify"].append(
        {
            "kind": "file",
            "assert": "ruleset_recorded_matches_register",
            "args": {
                "path": ".github/rulesets/default-branch.json",
                "require_pull_request": True,
                "require_status_checks": True,
                "allow_force_push": False,
                "required_checks": checks,
                "require_branches_up_to_date": True,
            },
        }
    )
    return document


def _enforcing(*contexts: str, slug: str = "acme/widget") -> FakeGitHub:
    """A platform enforcing exactly these status checks on the default branch."""
    return FakeGitHub(
        {
            f"/repos/{slug}": {"default_branch": "main"},
            f"/repos/{slug}/rules/branches/main": [
                {
                    "type": "required_status_checks",
                    "parameters": {
                        "required_status_checks": [{"context": c} for c in contexts]
                    },
                }
            ],
        },
        slug=slug,
    )


def test_gov_001_passes_when_the_platform_enforces_the_reaching_job(tmp_path: Path) -> None:
    """The whole chain, from contract 26: control → step → job → enforced check."""
    register, repo = _load(tmp_path, _with_required_checks(["check"]))
    make_repo(tmp_path, {".github/workflows/check.yml": _WORKFLOW_FULL_RUN})
    verdict, message = gov_001(register, repo, _enforcing("check"))
    assert verdict is Verdict.PASS
    assert "GitHub enforces those checks" in message


def test_gov_001_fails_a_required_check_the_platform_does_not_enforce(tmp_path: Path) -> None:
    """The workflow exists, the register requires it, and GitHub does not.

    Phase 3's criterion in one sentence, and the case a file could never
    answer: a ruleset recorded in the repository and never applied at the
    platform protects nothing, so a control credited to that job is reached
    from a step nothing waits for.
    """
    register, repo = _load(tmp_path, _with_required_checks(["check"]))
    make_repo(tmp_path, {".github/workflows/check.yml": _WORKFLOW_FULL_RUN})
    verdict, message = gov_001(register, repo, _enforcing("some-other-job"))
    assert verdict is Verdict.FAIL
    assert "the register requires check and GitHub does not" in message


def test_gov_001_fails_when_the_platform_enforces_nothing_at_all(tmp_path: Path) -> None:
    register, repo = _load(tmp_path, _with_required_checks(["check"]))
    make_repo(tmp_path, {".github/workflows/check.yml": _WORKFLOW_FULL_RUN})
    verdict, message = gov_001(register, repo, _enforcing())
    assert verdict is Verdict.FAIL
    assert "no check at all" in message


def test_gov_001_without_credentials_keeps_what_it_did_verify(tmp_path: Path) -> None:
    """A bare skip would throw away the half that was answered.

    The file-level chain is read whether or not a token exists, so the verdict
    says so — and still denies the run a `0`, because the half that decides
    whether any of it blocks a merge was not read (ADR 0016).
    """
    register, repo = _load(tmp_path, _with_required_checks(["check"]))
    make_repo(tmp_path, {".github/workflows/check.yml": _WORKFLOW_FULL_RUN})
    verdict, message = gov_001(register, repo, NoCredentials("no token"))
    assert verdict is Verdict.SKIPPED_NO_CREDENTIALS
    assert "in a job the register requires" in message
    assert "no token was offered" in message


def test_gov_001_is_unclassified_when_the_platform_declines_to_answer(tmp_path: Path) -> None:
    """Somebody asked and got nothing back — a different fact from nobody asking."""
    register, repo = _load(tmp_path, _with_required_checks(["check"]))
    make_repo(tmp_path, {".github/workflows/check.yml": _WORKFLOW_FULL_RUN})
    refusing = FakeGitHub({"/repos/acme/widget": Unreadable("the token was rejected (401)")})
    verdict, message = gov_001(register, repo, refusing)
    assert verdict is Verdict.UNCLASSIFIED
    assert "could not be read" in message

    verdict, message = gov_001(register, repo, Unresolvable("no repository to ask about"))
    assert verdict is Verdict.UNCLASSIFIED
    assert "no repository to ask about" in message


def test_gov_001_does_not_ask_the_platform_when_the_files_already_fail(tmp_path: Path) -> None:
    """A local repair is a local repair, and the network says nothing about it.

    The exploding target would raise if it were touched; the verdict is FAIL
    from what the files say, which is also the cheaper answer.
    """
    register, repo = _load(tmp_path, _with_required_checks(["check"]))
    make_repo(tmp_path, {".github/workflows/check.yml": _WORKFLOW_SUPPRESSED})
    exploding = FakeGitHub({"/repos/acme/widget": Unreadable("must not be asked")})
    verdict, _message = gov_001(register, repo, exploding)
    assert verdict is Verdict.FAIL


def test_gov_001_fails_when_nothing_waits_for_the_reaching_job(tmp_path: Path) -> None:
    """Reachable, gating, unsuppressed — and no ruleset requires it.

    The job runs on a pull request and can fail, so every earlier version of
    this control passed. Nothing waits for it, so it can go red and the merge
    button stays green: theme T-3 one level out from the step, which is the
    level GOV-001 could not see before the ruleset recorded its contexts.
    """
    register, repo = _load(tmp_path, _with_required_checks(["some-other-job"]))
    make_repo(tmp_path, {".github/workflows/check.yml": _WORKFLOW_FULL_RUN})
    verdict, message = gov_001(register, repo)
    assert verdict is Verdict.FAIL
    assert "no recorded ruleset requires" in message
    assert "some-other-job" in message


def test_gov_001_says_so_when_no_control_names_a_required_check(tmp_path: Path) -> None:
    """A register with no recorded ruleset gets the old answer, and is told."""
    register, repo = _load(tmp_path, minimal_register())
    make_repo(tmp_path, {".github/workflows/check.yml": _WORKFLOW_FULL_RUN})
    verdict, message = gov_001(register, repo)
    assert verdict is Verdict.PASS
    assert "is not answered here" in message
