"""Executing verify blocks and aggregating verdicts.

Verdict vocabulary per docs/02-skill-family.md: PASS, FAIL, SKIPPED (predicate),
SKIPPED (no credentials), UNCLASSIFIED. The two skip reasons are distinct on
purpose, and neither is ever counted as a pass.
"""

from __future__ import annotations

import datetime
import shlex
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum

from register_check.asserts import ASSERTS
from register_check.asserts_file import CONTROL_ARG, AssertFn
from register_check.asserts_remote import PUBLIC_REMOTE_ASSERTS, REMOTE_ASSERTS
from register_check.platform_limits import PlatformLimit, limit_for, read_limits
from register_check.predicates import compile_predicate
from register_check.register import Control, MetaControl, Register, VerifyBlock
from register_check.remote import GitHub, NoCredentials, Unreadable, Unresolvable
from register_check.remote import resolve as resolve_remote
from register_check.repo import NotAGitRepository, Repo


class Verdict(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIPPED_PREDICATE = "SKIPPED (predicate)"
    SKIPPED_NO_CREDENTIALS = "SKIPPED (no credentials)"
    UNCLASSIFIED = "UNCLASSIFIED"
    #: A remote block the repository's GitHub plan does not let it satisfy,
    #: recorded in `deployment-decisions.yaml` (ADR 0047). Never a pass: it
    #: sits beside UNCLASSIFIED in severity because both mean the control
    #: does not hold and the run gathered no evidence that it does.
    UNAVAILABLE_PLAN = "UNAVAILABLE (plan)"

    def __str__(self) -> str:
        return self.value


# Aggregation order: the control's verdict is the worst of its blocks'.
_SEVERITY = (
    Verdict.PASS,
    Verdict.SKIPPED_PREDICATE,
    Verdict.SKIPPED_NO_CREDENTIALS,
    Verdict.UNAVAILABLE_PLAN,
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
_UNVERIFIED = (
    Verdict.SKIPPED_NO_CREDENTIALS,
    Verdict.UNCLASSIFIED,
    # A recorded plan limit denies the run a `0` exactly as an unreadable
    # answer does, and `--require-complete` promotes it to `1`. ADR 0047
    # rule 4: the flag means *fail if anything could not be verified*, and
    # this is the case it was written for. A repository in this state does
    # not turn the flag on, and that is the visible cost rather than a hole.
    Verdict.UNAVAILABLE_PLAN,
)


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
    if argv and argv[0] == "register-check":
        argv = [sys.executable, "-m", "register_check", *argv[1:]]
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
    block: VerifyBlock,
    register: Register,
    repo: Repo,
    remote: RemoteTarget,
    control_id: str | None = None,
    limits: tuple[PlatformLimit, ...] = (),
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
        # A block that answers without a credential must not be short-circuited
        # for want of one. A release checksum manifest is public, and reporting
        # SKIPPED (no credentials) over it would be the checker declining to
        # answer a question it could have answered (ADR 0041).
        if block.assert_name in PUBLIC_REMOTE_ASSERTS:
            result = REMOTE_ASSERTS[block.assert_name](None, register, block.args)
            return BlockResult(
                block, Verdict.PASS if result.passed else Verdict.FAIL, result.message
            )
        target = resolve_remote(repo) if remote is None else remote
        if isinstance(target, NoCredentials):
            return BlockResult(block, Verdict.SKIPPED_NO_CREDENTIALS, target.message)
        if isinstance(target, Unresolvable):
            return BlockResult(block, Verdict.UNCLASSIFIED, target.message)
        result = REMOTE_ASSERTS[block.assert_name](target, register, block.args)
    except Unreadable as exc:
        return _unreadable_or_unavailable(block, exc, control_id, limits)
    except Exception as exc:  # an assert must never abort the rest of the audit
        return BlockResult(
            block, Verdict.UNCLASSIFIED, f"could not evaluate: {type(exc).__name__}: {exc}"
        )
    if result.passed:
        return BlockResult(block, Verdict.PASS, result.message)
    return _waived_or_failed(block, result.message, control_id, limits)


#: The one status a recorded platform limit may cover. GitHub answers it with
#: *"Upgrade to GitHub Pro or make this repository public to enable this
#: feature."*, which is the evidence ADR 0047 asks an operator to record. A 401,
#: a 404, a timeout and a name that will not resolve are all things a correct
#: repository can hit on a bad afternoon, and a record must never swallow them.
_PLAN_REFUSAL = 403


def _unmatched_record(
    limits: tuple[PlatformLimit, ...], control_id: str | None, block: VerifyBlock
) -> str:
    """What to add when a repository recorded limits and none covers this block.

    ADR 0047 rule 5 says a limitation nobody sees is an exemption, and every run
    prints the ones that apply. The inverse was silent: an adopter who wrote a
    record the checker did not match got a report **identical** to having
    written nothing, and no way to tell which had happened.

    That is not hypothetical. The first live repository to record one produced
    the same output three times — once from a typo in the filename, once from a
    checker defect (revision 2 above), and once correctly — and the report
    distinguished none of them.

    So say what was on record. Naming the pairs it *does* carry is what makes a
    mistyped control id or assert name visible, which is the failure this
    sentence exists to catch; the file's absence stays silent, because having no
    limits is the ordinary case and not a mistake.
    """
    if not limits:
        return ""
    recorded = ", ".join(f"{limit.control}/{limit.assert_name}" for limit in limits)
    return (
        f" — deployment-decisions.yaml records a platform limit for {recorded}, which "
        f"does not name {control_id or '?'}/{block.assert_name or '?'}, so nothing here "
        "is covered by it"
    )


def _unreadable_or_unavailable(
    block: VerifyBlock,
    exc: Unreadable,
    control_id: str | None,
    limits: tuple[PlatformLimit, ...],
) -> BlockResult:
    """A block the platform refused, and whether a record explains the refusal.

    ADR 0047 revision 2. The ADR was written believing a plan limit arrives as a
    **failure** — that the effective-rules endpoint answers `[]` on a repository
    whose plan has no rulesets. A live Free private repository answers `403`
    instead, which is `Unreadable`, which never reached `_waived_or_failed`. So
    the mechanism was inert for the one case it was built for: an adopter could
    write a correct entry and still read `UNCLASSIFIED` for ever.

    Only a `403` is covered, and only when an entry names this exact block.
    Widening it to every `Unreadable` would let a dated record absorb an expired
    token or a broken network — the checker reporting a billing fact it had not
    established, which is the misuse the ADR's § What this cannot verify names.

    **An expired entry reports `UNCLASSIFIED`, not `FAIL`.** Rule 3 says an
    expired record stops covering, and it does; but this path never received an
    answer, and failing a control on the strength of not having looked is the
    thing ADR 0021 forbids everywhere else in this file. Not covering means
    reverting to what the run actually knows, which is that the question is
    unsettled. Both exit non-zero, and `--require-complete` promotes both to 1.
    """
    if exc.status != _PLAN_REFUSAL:
        return BlockResult(block, Verdict.UNCLASSIFIED, str(exc))
    limit = limit_for(limits, control_id or "", block.assert_name or "")
    if limit is None:
        return BlockResult(
            block, Verdict.UNCLASSIFIED, str(exc) + _unmatched_record(limits, control_id, block)
        )
    if limit.expired(datetime.date.today()):
        return BlockResult(
            block,
            Verdict.UNCLASSIFIED,
            f"{exc} — a platform limit was recorded for this block but expired on "
            f"{limit.review_by}. Re-check the plan and set a new review date, or remove "
            f"the entry; an expired record is not a waiver.",
        )
    return BlockResult(
        block,
        Verdict.UNAVAILABLE_PLAN,
        f"{limit.plan}: {limit.lacks} — the platform refused the request (403) and "
        f"deployment-decisions.yaml records why, review by {limit.review_by}. The "
        f"control does not hold; this is a dated record of why, not a pass.",
    )


def _waived_or_failed(
    block: VerifyBlock,
    message: str,
    control_id: str | None,
    limits: tuple[PlatformLimit, ...],
) -> BlockResult:
    """A failing remote block the repository recorded as unbuyable (ADR 0047).

    Only a **failure** is reachable here, and only a `kind: remote` one. A block
    that passed is not waived, and a file block never reaches this function —
    a plan cannot stop a repository containing a file, so CI-001's recorded
    ruleset must still match the register.

    An **expired** entry fails rather than reverting to the waiver. A plan is a
    commercial state that changes on a renewal date, and an entry with no live
    expiry is a permanent exemption wearing a record's clothes.
    """
    limit = limit_for(limits, control_id or "", block.assert_name or "")
    if limit is None:
        return BlockResult(
            block, Verdict.FAIL, message + _unmatched_record(limits, control_id, block)
        )
    if limit.expired(datetime.date.today()):
        return BlockResult(
            block,
            Verdict.FAIL,
            f"{message} — a platform limit was recorded for this block but expired on "
            f"{limit.review_by}. Re-check the plan and set a new review date, or remove "
            f"the entry; an expired record is not a waiver.",
        )
    return BlockResult(
        block,
        Verdict.UNAVAILABLE_PLAN,
        f"{limit.plan}: {limit.lacks} — recorded in deployment-decisions.yaml, "
        f"review by {limit.review_by}. The control does not hold; this is a dated "
        f"record of why, not a pass.",
    )


def run_block(
    block: VerifyBlock,
    register: Register,
    repo: Repo,
    control: Control | MetaControl | None = None,
    remote: RemoteTarget = None,
    limits: tuple[PlatformLimit, ...] = (),
) -> BlockResult:
    if block.kind == "command":
        return _run_command_block(block, repo)
    if block.kind == "remote":
        # The control's id reaches the waiver from here rather than from the
        # block's own `args:`, for the same reason `provenance_stamp_present`
        # takes it from the runner: a control naming itself in its own entry is
        # a second copy of its id in the file that exists to prevent them.
        return _run_remote_block(
            block,
            register,
            repo,
            remote,
            control.id if control is not None else None,
            limits,
        )
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
    control: Control,
    register: Register,
    repo: Repo,
    remote: RemoteTarget = None,
    limits: tuple[PlatformLimit, ...] | None = None,
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
    # Read once per control rather than per block. A malformed record raises,
    # which is deliberate: reading it as "no limits" would turn a recorded,
    # dated waiver into a silent failure and the report would look ordinary.
    recorded = read_limits(repo) if limits is None else limits
    blocks = tuple(
        run_block(block, register, repo, control, remote, recorded) for block in applicable
    )
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
    """Entry point for `register-check assert <name>`.

    A debugging entry point, not the register's mechanism: the register declares
    an assertion as `kind: file` with an `assert:` name, and the schema rejects
    the `register-check assert …` form outright.
    """
    if name not in ASSERTS:
        return False, (
            f"unknown assert name '{name}' — known asserts: " + ", ".join(sorted(ASSERTS))
        )
    return guarded(ASSERTS[name], repo, register, {})
