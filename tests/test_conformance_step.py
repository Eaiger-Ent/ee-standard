"""The Conformance step's exit-code contract, exercised rather than read.

ADR 0016 gives the checker three exit codes and `--require-complete` promotes
"could not verify" to a failure. Which of those the CI step *tolerates* is a
decision that lives in a shell fragment inside a YAML string, where nothing was
checking it — and it has been rewritten three times: tolerate `3` (2026-08-17),
re-bounded twice, then flipped (2026-08-24) with one case left — and a
second case found on 2026-09-07.

That case is the reason these tests exist. Two run shapes receive no repository
secret — a pull request from a fork, and anything Dependabot opens, whose
secrets GitHub keeps in a store of its own — so SEC-001's remote block cannot
answer and the run reports `UNCLASSIFIED` for a control that holds; failing
there would fail a contributor, or a dependency update, for a credential this
repository deliberately does not give them. A carve-out nobody exercises is a
carve-out that quietly becomes general, which is the shape of every tolerance
this repository has had to re-bound.

Dependabot was added on 2026-09-07, after a bump sat unmergeable on exactly the
verdict the fork branch exists to tolerate. The bound was right about the
platform and short by one instance of it, which is why the flag below names the
condition rather than either instance.

The step is run with `uv` stubbed, so what is measured is the branch the script
takes and the code it returns — not what the checker would say.
"""

from __future__ import annotations

import shutil
import subprocess

import pytest
import yaml

from conftest import REPO_ROOT

WORKFLOW = REPO_ROOT / ".github/workflows/register-check.yml"


def _conformance_step() -> dict[str, object]:
    doc = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = doc["jobs"]["register-check"]["steps"]
    step = next((s for s in steps if s.get("name") == "Conformance"), None)
    assert step is not None, "no Conformance step in the Conformance workflow"
    assert isinstance(step, dict)
    return step


def _run(no_repository_secret: str, checker_exit: int) -> int:
    """The step's script, with `uv` replaced by something that exits as told."""
    script = str(_conformance_step()["run"])
    stub = f"uv() {{ return {checker_exit}; }}\n"
    return subprocess.run(
        ["bash", "-c", stub + script],
        env={"PATH": "/usr/bin:/bin", "NO_REPOSITORY_SECRET": no_repository_secret},
        capture_output=True,
        check=False,
    ).returncode


needs_bash = pytest.mark.skipif(shutil.which("bash") is None, reason="bash is not installed")


def test_the_step_passes_require_complete_when_the_run_carries_the_secret() -> None:
    """The flip itself, read from the file rather than assumed."""
    assert "--require-complete" in str(_conformance_step()["run"])


def test_the_flag_is_read_from_the_environment_not_interpolated() -> None:
    """An expression expanded into shell is a shape worth not copying around.

    The value is a boolean GitHub computes and could not carry an injection, but
    this file is one other repositories read, and the habit is the point.
    """
    step = _conformance_step()
    env = step.get("env")
    assert isinstance(env, dict)
    assert "${{" not in str(step["run"])
    assert env["NO_REPOSITORY_SECRET"].startswith("${{")


def test_the_flag_names_both_runs_the_platform_denies_a_secret() -> None:
    """Both disjuncts, and both keyed on the pull request rather than the secret.

    Keying on `secrets.PLATFORM_READ_TOKEN` being empty would read the same on
    the happy path and let a revoked or misspelled secret silently downgrade
    every run to the tolerant branch — a carve-out becoming general by way of a
    typo. `user.login` rather than `github.actor` because a human re-running a
    Dependabot check is still a run Dependabot's pull request triggered.
    """
    env = _conformance_step()["env"]
    assert isinstance(env, dict)
    flag = env["NO_REPOSITORY_SECRET"]
    assert "github.event.pull_request.head.repo.fork" in flag
    assert "github.event.pull_request.user.login == 'dependabot[bot]'" in flag
    assert "secrets." not in flag


@needs_bash
@pytest.mark.parametrize(
    "checker_exit,expected",
    [(0, 0), (1, 1), (3, 3)],
    ids=["clean", "violation", "incomplete"],
)
def test_an_ordinary_run_tolerates_nothing(checker_exit: int, expected: int) -> None:
    """A run that carries the secret: whatever the checker returns, the job returns.

    `--require-complete` means the checker itself never returns 3 here — it
    returns 1 instead — so the third case is the belt this script no longer
    needs and must not quietly grow back.
    """
    assert _run("", checker_exit) == expected
    # A pull request that carries the secret evaluates the expression to
    # `false`; only a run with no pull request at all leaves it empty. Both
    # reach the same branch, and both are asserted so neither can drift.
    assert _run("false", checker_exit) == expected


@needs_bash
@pytest.mark.parametrize(
    "checker_exit,expected",
    [(0, 0), (1, 1), (3, 0)],
    ids=["clean", "violation", "incomplete-is-tolerated"],
)
def test_a_run_without_the_secret_tolerates_three_and_only_three(
    checker_exit: int, expected: int
) -> None:
    """The whole carve-out, in three rows.

    A verified violation still fails a fork pull request, and still fails a
    Dependabot one. Only "could not verify" is tolerated, and only because the
    credential that would settle it is one the platform deliberately does not
    hand to either.
    """
    assert _run("true", checker_exit) == expected
