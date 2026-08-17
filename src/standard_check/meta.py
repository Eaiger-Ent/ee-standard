"""The meta-controls: GOV-001, GOV-002, GOV-003.

These check the register and its enforcement, not the code. Without them the
register rots quietly (docs/00-concepts.md § Meta-controls).
"""

from __future__ import annotations

import datetime
import re

from standard_check.asserts_command import _SUPPRESSION, _workflow_steps
from standard_check.register import Register
from standard_check.repo import Repo, git
from standard_check.runner import Verdict, applies

_BARE_INVOCATION = re.compile(
    r"^\s*(?:uv run\s+)?standard-check(?:\s+--tier\s+\d+)?\s*$", re.MULTILINE
)


def gov_001(register: Register, repo: Repo) -> tuple[Verdict, str]:
    """Every blocking control is reachable from a CI step that can fail."""
    clean_steps = [
        step for step in _workflow_steps(repo) if step.run and not step.suppressed
    ]
    full_run = any(
        _BARE_INVOCATION.search(step.run) and not _SUPPRESSION.search(step.run)
        for step in clean_steps
    )
    unreachable = []
    for control in register.controls:
        if control.rung != "blocking" or "ci" not in control.locus:
            continue
        if not applies(control, register, repo)[0]:
            continue
        if full_run:
            continue
        commands = [
            block.run.split()[0]
            for block in control.verify
            if block.kind == "command" and block.run
        ]
        reached = any(
            any(command in step.run for command in commands) and not _SUPPRESSION.search(step.run)
            for step in clean_steps
        )
        if not reached:
            unreachable.append(control.id)
    if unreachable:
        return Verdict.FAIL, (
            "blocking controls with no reachable CI step: " + ", ".join(unreachable)
        )
    return (
        Verdict.PASS,
        "every applicable blocking control is reachable from a CI step that can fail",
    )


def _entries(text: str) -> int:
    return sum(
        1 for line in text.splitlines() if line.strip() and not line.strip().startswith("#")
    )


def _rev_parse(repo: Repo, rev: str) -> str | None:
    result = git(repo.root, "rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}")
    return result.stdout.strip() or None if result.returncode == 0 else None


def _reference_commit(repo: Repo) -> tuple[str | None, str]:
    """The commit whose baselines the working tree must not exceed.

    GOV-002 compares against *the previous commit on the default branch*. Which
    commit that is depends on where the checker is running:

    - on a branch, it is the merge-base with the default branch, so a pull
      request is measured against what it forked from;
    - on the default branch itself, it is the parent commit, so a merge that
      grew a baseline is caught.

    Resolving to HEAD in either case is what made this control unable to fail:
    once a growth is committed — which in CI it always is — HEAD *is* the grown
    state, so current always equalled previous.
    """
    head = _rev_parse(repo, "HEAD")
    if head is None:
        return None, "HEAD does not resolve to a commit"
    for name in ("origin/HEAD", "origin/main", "main", "master"):
        tip = _rev_parse(repo, name)
        if tip is None or tip == head:
            continue
        base = git(repo.root, "merge-base", name, "HEAD")
        if base.returncode == 0 and base.stdout.strip():
            return base.stdout.strip(), f"the merge-base with {name}"
    parent = _rev_parse(repo, "HEAD~1")
    if parent is not None:
        return parent, "the previous commit"
    return head, "HEAD (the repository has no earlier commit)"


def _entries_at(repo: Repo, commit: str, rel: str) -> int:
    """Entry count for `rel` at `commit`; absent there counts as zero."""
    result = git(repo.root, "show", f"{commit}:{rel}")
    return _entries(result.stdout) if result.returncode == 0 else 0


def _entries_now(repo: Repo, rel: str) -> int:
    path = repo.root / rel
    if not path.is_file():
        return 0
    return _entries(path.read_text(encoding="utf-8"))


def gov_002(register: Register, repo: Repo) -> tuple[Verdict, str]:
    """No baseline grew. A baseline that may grow is an exemption list."""
    baselines = [c for c in register.controls if c.baseline is not None]
    if not baselines:
        return Verdict.PASS, "no control carries a baseline — nothing that could grow"
    reference, description = _reference_commit(repo)
    if reference is None:
        # Cannot verify is not the same as passes, and not the same as violates
        # either (ADR 0016). Without a comparison point this run has no evidence
        # about growth in any direction, and UNCLASSIFIED keeps the exit code
        # off 0 without asserting a violation.
        return Verdict.UNCLASSIFIED, f"cannot determine a comparison point: {description}"
    grown = []
    for control in baselines:
        assert control.baseline is not None
        current = _entries_now(repo, control.baseline)
        previous = _entries_at(repo, reference, control.baseline)
        if current > previous:
            grown.append(f"{control.id} ({control.baseline}: {previous} → {current})")
    if grown:
        return Verdict.FAIL, f"baselines grew against {description}: " + "; ".join(grown)
    return (
        Verdict.PASS,
        f"no baseline grew ({len(baselines)} checked against {description})",
    )


def gov_003(register: Register, _repo: Repo) -> tuple[Verdict, str]:
    """No control is past its review_by date."""
    today = datetime.date.today()
    expired = [
        f"{control.id} (review_by {control.review_by.isoformat()})"
        for control in register.controls
        if control.review_by < today
    ]
    if expired:
        return Verdict.FAIL, "controls past their review date: " + ", ".join(expired)
    return Verdict.PASS, "no control is past its review date"


META_CHECKS = {
    "GOV-001": gov_001,
    "GOV-002": gov_002,
    "GOV-003": gov_003,
}
