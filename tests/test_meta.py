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

from conftest import make_repo, minimal_register, write_register
from standard_check.meta import gov_001, gov_002, gov_003
from standard_check.register import Register, load_register
from standard_check.repo import Repo
from standard_check.runner import Verdict


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
    "      - run: uv run standard-check\n"
)


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
        "      - run: uv run standard-check\n"
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
        "          uv run standard-check && status=0 || status=$?\n"
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
    """`pip install standard-check` is not evidence that anything is checked.

    An invocation starts a command; it never follows another word. Substring
    matching made installing the tool mark every control reachable at once —
    § A row 4 of the build plan.
    """
    register, repo = _load(tmp_path, minimal_register())
    workflow = (
        _ON + "jobs:\n  check:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - run: pip install standard-check\n"
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
        "      - run: uv run standard-check assert precommit_hook_present\n"
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
        "      - run: uv run standard-check\n"
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
        "      - run: uv run standard-check\n"
    )
    make_repo(tmp_path, {".github/workflows/check.yml": workflow})
    verdict, message = gov_001(register, repo)
    assert verdict is Verdict.PASS, message


def test_gov_001_does_not_accept_a_different_assert_as_evidence(tmp_path: Path) -> None:
    """Reaching *an* assertion is not reaching *this* control's assertion."""
    register, repo = _load(tmp_path, minimal_register())
    workflow = (
        _ON + "jobs:\n  check:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - run: uv run standard-check assert actions-pinned-to-sha\n"
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
