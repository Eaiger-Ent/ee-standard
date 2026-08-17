"""Executing verify blocks and aggregating verdicts.

Verdict vocabulary per docs/02-skill-family.md: PASS, FAIL, SKIPPED (predicate),
SKIPPED (no credentials), UNCLASSIFIED. The two skip reasons are distinct on
purpose, and neither is ever counted as a pass.
"""

from __future__ import annotations

import shlex
import subprocess
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import Enum

from standard_check.asserts_command import COMMAND_ASSERTS
from standard_check.asserts_file import FILE_ASSERTS, AssertResult
from standard_check.predicates import compile_predicate
from standard_check.register import Control, MetaControl, Register, VerifyBlock
from standard_check.repo import NotAGitRepository, Repo


class Verdict(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIPPED_PREDICATE = "SKIPPED (predicate)"
    SKIPPED_NO_CREDENTIALS = "SKIPPED (no credentials)"
    UNCLASSIFIED = "UNCLASSIFIED"

    def __str__(self) -> str:
        return self.value


# Aggregation order: the control's verdict is the worst of its blocks'.
_SEVERITY = (
    Verdict.PASS,
    Verdict.SKIPPED_PREDICATE,
    Verdict.SKIPPED_NO_CREDENTIALS,
    Verdict.UNCLASSIFIED,
    Verdict.FAIL,
)


def worst(verdicts: list[Verdict]) -> Verdict:
    return max(verdicts, key=_SEVERITY.index)


@dataclass(frozen=True)
class BlockResult:
    block: VerifyBlock
    verdict: Verdict
    message: str


@dataclass(frozen=True)
class ControlResult:
    control: Control | MetaControl
    verdict: Verdict
    blocks: tuple[BlockResult, ...]
    note: str = ""


def _run_command_block(block: VerifyBlock, repo: Repo) -> BlockResult:
    assert block.run is not None
    argv = shlex.split(block.run)
    # Self-referential commands run through this same interpreter so the
    # register's command strings work identically in CI and under test.
    if argv and argv[0] == "standard-check":
        argv = [sys.executable, "-m", "standard_check", *argv[1:]]
    try:
        completed = subprocess.run(
            argv, cwd=repo.root, capture_output=True, text=True, timeout=300, check=False
        )
    except FileNotFoundError:
        return BlockResult(block, Verdict.FAIL, f"command not found: {argv[0]}")
    except subprocess.TimeoutExpired:
        return BlockResult(block, Verdict.FAIL, f"timed out after 300s: {block.run}")
    if completed.returncode == 0:
        return BlockResult(block, Verdict.PASS, "exit 0")
    tail = (completed.stdout + completed.stderr).strip().splitlines()[-3:]
    detail = " | ".join(line.strip() for line in tail) or f"exit {completed.returncode}"
    return BlockResult(block, Verdict.FAIL, f"exit {completed.returncode}: {detail}")


def run_block(block: VerifyBlock, repo: Repo) -> BlockResult:
    if block.kind == "command":
        return _run_command_block(block, repo)
    if block.kind == "remote":
        # Remote verification is Phase 3: it needs credentials, network and a
        # live repository. Skipping is the honest verdict — never a pass.
        return BlockResult(
            block,
            Verdict.SKIPPED_NO_CREDENTIALS,
            "remote verification requires credentials (Phase 3)",
        )
    assert block.assert_name is not None
    passed, message = guarded(FILE_ASSERTS[block.assert_name], repo, block.args)
    return BlockResult(block, Verdict.PASS if passed else Verdict.FAIL, message)


def applies(control: Control, register: Register, repo: Repo) -> tuple[bool, str]:
    """Whether any of the control's predicates is satisfied by the repo."""
    for name in control.applies_to:
        if compile_predicate(register.predicates[name])(repo):
            return True, name
    return False, ", ".join(control.applies_to)


def run_control(control: Control, register: Register, repo: Repo) -> ControlResult:
    satisfied, detail = applies(control, register, repo)
    if not satisfied:
        return ControlResult(
            control, Verdict.SKIPPED_PREDICATE, (), note=f"predicate not satisfied: {detail}"
        )
    blocks = tuple(run_block(block, repo) for block in control.verify)
    return ControlResult(control, worst([b.verdict for b in blocks]), blocks)


def guarded(
    fn: Callable[[Repo, Mapping[str, object]], AssertResult],
    repo: Repo,
    args: Mapping[str, object],
) -> tuple[bool, str]:
    """Run an assert so that it always yields a verdict.

    Asserts run in-process, so an unhandled exception would abort the whole
    audit before any verdict is rendered — losing every other control's result
    to one unreadable file. A raising assert is a failure of that control, and
    the message names what could not be read.
    """
    try:
        result = fn(repo, args)
    except NotAGitRepository:
        raise  # the target itself is unevaluable; the CLI reports this, not a verdict
    except Exception as exc:
        return False, f"could not evaluate: {type(exc).__name__}: {exc}"
    return result.passed, result.message


def run_command_assert(name: str, repo: Repo) -> tuple[bool, str]:
    """Entry point for `standard-check assert <name>`."""
    if name not in COMMAND_ASSERTS:
        return False, (
            f"unknown assert name '{name}' — known command asserts: "
            + ", ".join(sorted(COMMAND_ASSERTS))
        )
    return guarded(COMMAND_ASSERTS[name], repo, {})
