"""The meta-controls: GOV-001, GOV-002, GOV-003.

These check the register and its enforcement, not the code. Without them the
register rots quietly (docs/00-concepts.md § Meta-controls).
"""

from __future__ import annotations

import datetime
import re
import subprocess

from standard_check.asserts_command import _SUPPRESSION, _workflow_steps
from standard_check.register import Register
from standard_check.repo import Repo
from standard_check.runner import applies

_BARE_INVOCATION = re.compile(
    r"^\s*(?:uv run\s+)?standard-check(?:\s+--tier\s+\d+)?\s*$", re.MULTILINE
)


def gov_001(register: Register, repo: Repo) -> tuple[bool, str]:
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
        return False, (
            "blocking controls with no reachable CI step: " + ", ".join(unreachable)
        )
    return True, "every applicable blocking control is reachable from a CI step that can fail"


def _entries(text: str) -> int:
    return sum(
        1 for line in text.splitlines() if line.strip() and not line.strip().startswith("#")
    )


def _previous_content(repo: Repo, rel: str) -> str | None:
    for ref in ("origin/main", "main", "HEAD"):
        result = subprocess.run(
            ["git", "-C", str(repo.root), "show", f"{ref}:{rel}"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout
        if "does not exist" in result.stderr or "exists on disk, but not in" in result.stderr:
            return None
    return None


def gov_002(register: Register, repo: Repo) -> tuple[bool, str]:
    """No baseline grew. A baseline that may grow is an exemption list."""
    grown = []
    baselines = [c for c in register.controls if c.baseline is not None]
    if not baselines:
        return True, "no control carries a baseline — nothing that could grow"
    for control in baselines:
        assert control.baseline is not None
        current = _entries(repo.read(control.baseline)) if repo.exists(control.baseline) else 0
        previous_text = _previous_content(repo, control.baseline)
        previous = _entries(previous_text) if previous_text is not None else 0
        if current > previous:
            grown.append(f"{control.id} ({control.baseline}: {previous} → {current})")
    if grown:
        return False, "baselines grew: " + "; ".join(grown)
    return True, f"no baseline grew ({len(baselines)} checked)"


def gov_003(register: Register, _repo: Repo) -> tuple[bool, str]:
    """No control is past its review_by date."""
    today = datetime.date.today()
    expired = [
        f"{control.id} (review_by {control.review_by.isoformat()})"
        for control in register.controls
        if control.review_by < today
    ]
    if expired:
        return False, "controls past their review date: " + ", ".join(expired)
    return True, "no control is past its review date"


META_CHECKS = {
    "GOV-001": gov_001,
    "GOV-002": gov_002,
    "GOV-003": gov_003,
}
