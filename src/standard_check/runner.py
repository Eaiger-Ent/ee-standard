"""Executing verify blocks and aggregating verdicts.

Verdict vocabulary per docs/02-skill-family.md: PASS, FAIL, SKIPPED (predicate),
SKIPPED (no credentials), UNCLASSIFIED. The two skip reasons are distinct on
purpose, and neither is ever counted as a pass.
"""

from __future__ import annotations

import shlex
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum

from standard_check.asserts import ASSERTS
from standard_check.asserts_file import CONTROL_ARG, AssertFn
from standard_check.asserts_remote import REMOTE_ASSERTS
from standard_check.predicates import compile_predicate
from standard_check.register import Control, MetaControl, Register, VerifyBlock
from standard_check.remote import GitHub, NoCredentials, Unreadable, Unresolvable
from standard_check.remote import resolve as resolve_remote
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


# Exit codes, per ADR 0016. `2` is left to argparse for usage errors and to the
# CLI for a target that is not a repository — collapsing those into either of
# the verdict codes would be a fresh ambiguity.
EXIT_OK = 0
EXIT_VIOLATION = 1
EXIT_INCOMPLETE = 3

# Verdicts that mean "this run gathered no evidence either way". A predicate
# skip is deliberately absent: not-applicable is a legitimate pass, and
# conflating it with unverified would make the code meaningless in the common
# case (a repo with no Terraform genuinely satisfies IAC-001's applicability).
_UNVERIFIED = (Verdict.SKIPPED_NO_CREDENTIALS, Verdict.UNCLASSIFIED)


def exit_code(
    verdicts: list[Verdict], *, require_complete: bool = False, partial: bool = False
) -> int:
    """The run's exit status, given every control and meta-control verdict.

    `partial` is ADR 0017 composing with ADR 0016: a control that declared part
    of itself unimplemented was not fully verified, however clean the verdict it
    could compute. Without this a partial control would leave exit 0, which is
    the overstatement the annotation exists to prevent.
    """
    if any(verdict is Verdict.FAIL for verdict in verdicts):
        return EXIT_VIOLATION
    if partial or any(verdict in _UNVERIFIED for verdict in verdicts):
        return EXIT_VIOLATION if require_complete else EXIT_INCOMPLETE
    return EXIT_OK


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
        # Cannot verify is not the same as violates (ADR 0016). A missing binary
        # says nothing about the repository, so reporting FAIL would assert a
        # violation this run has no evidence for.
        return BlockResult(
            block,
            Verdict.UNCLASSIFIED,
            f"tool not installed: {argv[0]} — cannot verify",
        )
    except subprocess.TimeoutExpired:
        return BlockResult(block, Verdict.FAIL, f"timed out after 300s: {block.run}")
    if completed.returncode == 0:
        return BlockResult(block, Verdict.PASS, "exit 0")
    tail = (completed.stdout + completed.stderr).strip().splitlines()[-3:]
    detail = " | ".join(line.strip() for line in tail) or f"exit {completed.returncode}"
    return BlockResult(block, Verdict.FAIL, f"exit {completed.returncode}: {detail}")


#: What a remote block is run against: a resolved repository-and-token, the
#: statement that no token was offered, or `None` meaning "work it out from this
#: repository and this environment". The CLI resolves once and passes the result
#: down so that a run's remote blocks cannot disagree about which repository
#: they are describing.
RemoteTarget = GitHub | NoCredentials | Unresolvable | None


def _run_remote_block(
    block: VerifyBlock, register: Register, repo: Repo, remote: RemoteTarget
) -> BlockResult:
    """Ask the platform, and report honestly when it does not answer.

    Three outcomes, and only the third is about the repository (ADR 0021):
    nobody asked (SKIPPED — no credentials), somebody asked and got no usable
    answer (UNCLASSIFIED), or the platform answered (PASS or FAIL). The first
    two both deny the run a `0` exit, so neither can be read as a pass; they are
    distinguished because one needs a token supplied and the other needs one
    fixed.
    """
    assert block.assert_name is not None
    try:
        target = resolve_remote(repo) if remote is None else remote
        if isinstance(target, NoCredentials):
            return BlockResult(block, Verdict.SKIPPED_NO_CREDENTIALS, target.message)
        if isinstance(target, Unresolvable):
            return BlockResult(block, Verdict.UNCLASSIFIED, target.message)
        result = REMOTE_ASSERTS[block.assert_name](target, register, block.args)
    except Unreadable as exc:
        return BlockResult(block, Verdict.UNCLASSIFIED, str(exc))
    except Exception as exc:  # an assert must never abort the rest of the audit
        return BlockResult(
            block, Verdict.UNCLASSIFIED, f"could not evaluate: {type(exc).__name__}: {exc}"
        )
    return BlockResult(block, Verdict.PASS if result.passed else Verdict.FAIL, result.message)


def run_block(
    block: VerifyBlock,
    register: Register,
    repo: Repo,
    control: Control | MetaControl | None = None,
    remote: RemoteTarget = None,
) -> BlockResult:
    if block.kind == "command":
        return _run_command_block(block, repo)
    if block.kind == "remote":
        return _run_remote_block(block, register, repo, remote)
    assert block.assert_name is not None
    args = dict(block.args)
    if control is not None:
        args[CONTROL_ARG] = control.id
    passed, message = guarded(ASSERTS[block.assert_name], repo, register, args)
    return BlockResult(block, Verdict.PASS if passed else Verdict.FAIL, message)


def applies(control: Control, register: Register, repo: Repo) -> tuple[bool, str]:
    """Whether any of the control's predicates is satisfied by the repo."""
    for name in control.applies_to:
        if compile_predicate(register.predicates[name])(repo):
            return True, name
    return False, ", ".join(control.applies_to)


def _block_applies(block: VerifyBlock, register: Register, repo: Repo) -> bool:
    """Whether this block's own predicates hold, if it declares any.

    A control may verify one property by different mechanisms for different
    repository shapes: BLD-001 reads a Dockerfile with hadolint and a
    devcontainer with a file assert. Running either against the shape it was not
    written for reports on something that is not there — `hadolint` against a
    repository with no Dockerfile is not a finding, it is a category error.
    """
    return not block.applies_to or any(
        compile_predicate(register.predicates[name])(repo) for name in block.applies_to
    )


def run_control(
    control: Control, register: Register, repo: Repo, remote: RemoteTarget = None
) -> ControlResult:
    satisfied, detail = applies(control, register, repo)
    if not satisfied:
        return ControlResult(
            control, Verdict.SKIPPED_PREDICATE, (), note=f"predicate not satisfied: {detail}"
        )
    applicable = [b for b in control.verify if _block_applies(b, register, repo)]
    if not applicable:
        # Every block narrowed itself out. The control applies but nothing
        # verified it, so it has not passed — reporting PASS here would be a
        # green tick over an empty check, which is the § A defect exactly.
        return ControlResult(
            control,
            Verdict.SKIPPED_PREDICATE,
            (),
            note=(
                "the control applies, but every verification block is narrowed to a "
                "repository shape this repo does not have"
            ),
        )
    blocks = tuple(run_block(block, register, repo, control, remote) for block in applicable)
    return ControlResult(control, worst([b.verdict for b in blocks]), blocks)


def guarded(
    fn: AssertFn,
    repo: Repo,
    register: Register,
    args: Mapping[str, object],
) -> tuple[bool, str]:
    """Run an assert so that it always yields a verdict.

    Asserts run in-process, so an unhandled exception would abort the whole
    audit before any verdict is rendered — losing every other control's result
    to one unreadable file. A raising assert is a failure of that control, and
    the message names what could not be read.
    """
    try:
        result = fn(repo, register, args)
    except NotAGitRepository:
        raise  # the target itself is unevaluable; the CLI reports this, not a verdict
    except Exception as exc:
        return False, f"could not evaluate: {type(exc).__name__}: {exc}"
    return result.passed, result.message


def run_command_assert(name: str, register: Register, repo: Repo) -> tuple[bool, str]:
    """Entry point for `standard-check assert <name>`.

    A debugging entry point, not the register's mechanism: the register declares
    an assertion as `kind: file` with an `assert:` name, and the schema rejects
    the `standard-check assert …` form outright.
    """
    if name not in ASSERTS:
        return False, (
            f"unknown assert name '{name}' — known asserts: " + ", ".join(sorted(ASSERTS))
        )
    return guarded(ASSERTS[name], repo, register, {})
