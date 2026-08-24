"""The Conformance step's exit-code contract, exercised rather than read.

ADR 0016 gives the checker three exit codes and `--require-complete` promotes
"could not verify" to a failure. Which of those the CI step *tolerates* is a
decision that lives in a shell fragment inside a YAML string, where nothing was
checking it — and it has been rewritten three times: tolerate `3` (2026-08-17),
re-bounded twice, then flipped (2026-08-24) with one case left.

That case is the reason these tests exist. A pull request from a fork receives
no repository secret, so SEC-001's remote block cannot answer and the run
reports `UNCLASSIFIED` for a control that holds; failing there would fail a
contributor for a credential this repository deliberately does not give them. A
carve-out nobody exercises is a carve-out that quietly becomes general, which is
the shape of every tolerance this repository has had to re-bound.

The step is run with `uv` stubbed, so what is measured is the branch the script
takes and the code it returns — not what the checker would say.
"""

from __future__ import annotations

import shutil
import subprocess

import pytest
import yaml

from conftest import REPO_ROOT

WORKFLOW = REPO_ROOT / ".github/workflows/standard-check.yml"


def _conformance_step() -> dict[str, object]:
    doc = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = doc["jobs"]["standard-check"]["steps"]
    step = next((s for s in steps if s.get("name") == "Conformance"), None)
    assert step is not None, "no Conformance step in the Standard workflow"
    assert isinstance(step, dict)
    return step


def _run(from_a_fork: str, checker_exit: int) -> int:
    """The step's script, with `uv` replaced by something that exits as told."""
    script = str(_conformance_step()["run"])
    stub = f"uv() {{ return {checker_exit}; }}\n"
    return subprocess.run(
        ["bash", "-c", stub + script],
        env={"PATH": "/usr/bin:/bin", "FROM_A_FORK": from_a_fork},
        capture_output=True,
        check=False,
    ).returncode


needs_bash = pytest.mark.skipif(shutil.which("bash") is None, reason="bash is not installed")


def test_the_step_passes_require_complete_when_the_run_is_not_from_a_fork() -> None:
    """The flip itself, read from the file rather than assumed."""
    assert "--require-complete" in str(_conformance_step()["run"])


def test_the_fork_flag_is_read_from_the_environment_not_interpolated() -> None:
    """An expression expanded into shell is a shape worth not copying around.

    The value is a boolean GitHub computes and could not carry an injection, but
    this file is one other repositories read, and the habit is the point.
    """
    step = _conformance_step()
    env = step.get("env")
    assert isinstance(env, dict)
    assert env["FROM_A_FORK"] == "${{ github.event.pull_request.head.repo.fork }}"
    assert "${{" not in str(step["run"])


@needs_bash
@pytest.mark.parametrize(
    "checker_exit,expected",
    [(0, 0), (1, 1), (3, 3)],
    ids=["clean", "violation", "incomplete"],
)
def test_an_ordinary_run_tolerates_nothing(checker_exit: int, expected: int) -> None:
    """Not from a fork: whatever the checker returns, the job returns.

    `--require-complete` means the checker itself never returns 3 here — it
    returns 1 instead — so the third case is the belt this script no longer
    needs and must not quietly grow back.
    """
    assert _run("", checker_exit) == expected


@needs_bash
@pytest.mark.parametrize(
    "checker_exit,expected",
    [(0, 0), (1, 1), (3, 0)],
    ids=["clean", "violation", "incomplete-is-tolerated"],
)
def test_a_fork_run_tolerates_three_and_only_three(checker_exit: int, expected: int) -> None:
    """The whole carve-out, in three rows.

    A verified violation still fails a fork pull request. Only "could not
    verify" is tolerated, and only because the credential that would settle it
    is one a fork deliberately does not receive.
    """
    assert _run("true", checker_exit) == expected
