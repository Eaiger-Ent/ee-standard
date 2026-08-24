"""The meta-controls: GOV-001, GOV-002, GOV-003.

These check the register and its enforcement, not the code. Without them the
register rots quietly (docs/00-concepts.md § Meta-controls).
"""

from __future__ import annotations

import datetime
import re

from standard_check.asserts_command import WorkflowStep, _suppression_match, _workflow_steps
from standard_check.register import Control, MetaControl, Register
from standard_check.remote import GitHub, NoCredentials, Unreadable, Unresolvable
from standard_check.repo import Repo, git
from standard_check.rulesets import by_rule_type, enforced_contexts
from standard_check.runner import Verdict, applies

# A step runs the whole register if it *invokes* the checker without a
# subcommand that narrows it. Matched as an invocation — the command word at the
# start of a command, optionally behind `uv run` — not as a line shape.
#
# The previous pattern required the line to be exactly the invocation, which
# made every control's verdict depend on shell punctuation: adding error
# handling to the CI step (`… && status=0 || status=$?`) silently flipped
# GOV-001 from "everything reachable" to "SUP-002 and DEV-001 unreachable",
# without either control changing. A reachability test that a cosmetic
# reformat can invert is not measuring reachability.
#
# The leading alternation is what keeps `pip install standard-check` out: an
# invocation starts a command, so it follows a line start or a separator, never
# another word. This is the "match invocations, not substrings" criterion
# applied to the full-run case; the per-control case is still a substring test
# and is fixed with the `kind:` taxonomy.
_FULL_RUN = re.compile(
    r"(?:^\s*|[;&|(]\s*)(?:uv\s+run\s+)?standard-check"
    r"(?![-\w])(?!\s+(?:assert|meta|explain|schema)\b)",
    re.MULTILINE,
)


def _invocation(word: str) -> re.Pattern[str]:
    """A pattern matching `word` invoked as a command, not merely mentioned.

    An invocation starts a command, so it follows a line start or a separator —
    never another word. This is what distinguishes running a tool from
    installing it, naming it in an echo, or matching it inside a longer name.
    """
    return re.compile(rf"(?:^\s*|[;&|(]\s*)(?:\S+\s+run\s+)?{re.escape(word)}(?![-\w])", re.M)


def _reaches(control: Control, run: str, register: Register) -> bool:
    """Whether this CI step verifies `control`.

    A control is reached by a step that runs one of its external tools, or that
    runs one of its assertions by name. Before contract 3 this was a substring
    test over the first word of each `kind: command` block — which, because
    every in-process assertion was declared as `standard-check assert …`, meant
    six controls collapsed to the single token `standard-check`, and the two
    verified only by file asserts (SUP-002, DEV-001) had no token at all and
    were unreachable by construction.
    """
    if _suppression_match(register, run):
        return False
    for block in control.verify:
        if block.kind == "command" and block.run and _invocation(block.run.split()[0]).search(run):
            return True
        # `standard-check assert <name>` — the debugging entry point, but a
        # legitimate way for CI to reach one assertion deliberately.
        if (
            block.kind == "file"
            and block.assert_name
            and re.search(rf"standard-check\s+assert\s+{re.escape(block.assert_name)}\b", run)
        ):
            return True
    return False


def gov_001(
    register: Register,
    repo: Repo,
    remote: GitHub | NoCredentials | Unresolvable | None = None,
) -> tuple[Verdict, str]:
    """Every blocking control is reachable from a CI step that can fail.

    "Can fail" has two halves, and this control was ticked on one of them. A step
    whose failure is swallowed cannot fail, and a step in a workflow that runs on
    neither push nor pull_request cannot fail *a merge* — it runs when a human
    clicks it, which is theme T-3 in the control written to catch T-3 (§ H1).
    Pointing `on:` at `workflow_dispatch` and changing nothing else used to leave
    this reporting every blocking control reachable, in the same run where
    TST-001 read the same file correctly and failed.
    """
    runnable = [step for step in _workflow_steps(repo) if step.run and not step.suppressed]
    clean_steps = [step for step in runnable if step.gating]
    ungated = [step for step in runnable if not step.gating]
    # The jobs a ruleset makes a merge wait for, from CI-001's `args:` — the one
    # statement of them, read rather than restated. Register contract 19 put
    # them there; before it, "reachable from a step that can fail" was the whole
    # of this control and *reachable from a step anything waits for* was the
    # partial beside it.
    required_jobs = _required_jobs(register)

    def full_run(steps: list[WorkflowStep]) -> bool:
        return any(
            _FULL_RUN.search(step.run) and not _suppression_match(register, step.run)
            for step in steps
        )

    def in_a_required_job(steps: list[WorkflowStep]) -> bool:
        return not required_jobs or any(step.job in required_jobs for step in steps)

    runs_everything = full_run(clean_steps)
    runs_everything_ungated = full_run(ungated)
    unreachable = []
    ungated_only = []
    unrequired = []
    for control in register.controls:
        if control.rung != "blocking" or "ci" not in control.locus:
            continue
        if not applies(control, register, repo)[0]:
            continue
        # A step reaches a control either by naming it or by running the whole
        # register — and the full-run case still has to survive the suppression
        # check, or a swallowed `standard-check` would be credited with reaching
        # everything.
        reaching = [
            step
            for step in clean_steps
            if (_FULL_RUN.search(step.run) and not _suppression_match(register, step.run))
            or _reaches(control, step.run, register)
        ]
        if runs_everything or reaching:
            # Reachable. The remaining question is whether anything waits for
            # the job it is reachable from: a gating job no ruleset requires
            # can go red and the merge button stays green, which is the same
            # T-3 shape one level out from the step.
            if not in_a_required_job(reaching):
                unrequired.append(control.id)
            continue
        if runs_everything_ungated:
            ungated_only.append(control.id)
            continue
        # Named apart from the absent case: "you wired it to the wrong trigger"
        # and "you never wired it" are different repairs, and a message that
        # says only the second sends the reader looking for a step that is there.
        if any(_reaches(control, step.run, register) for step in ungated):
            ungated_only.append(control.id)
        else:
            unreachable.append(control.id)
    problems = []
    if unreachable:
        problems.append("blocking controls with no reachable CI step: " + ", ".join(unreachable))
    if ungated_only:
        problems.append(
            "blocking controls reached only from a workflow that runs on neither push nor "
            "pull_request, so it gates no merge: " + ", ".join(ungated_only)
        )
    if unrequired:
        problems.append(
            "blocking controls reached only from a job no recorded ruleset requires, so the "
            "job can fail and the merge button stays green: "
            + ", ".join(unrequired)
            + f" (required checks: {', '.join(sorted(required_jobs))})"
        )
    if problems:
        return Verdict.FAIL, "; ".join(problems)
    if not required_jobs:
        return (
            Verdict.PASS,
            "every applicable blocking control is reachable from a CI step that can fail a "
            "merge; no ruleset in this register names a required check, so whether anything "
            "waits for that step is not answered here",
        )
    # The half no file can answer, from register contract 26. Everything above
    # reads what the repository *records*: the step, the job, and the register's
    # own list of required checks. A recorded ruleset GitHub was never told
    # about protects nothing, so a control credited to a job on that list is
    # credited to a job that may block no merge at all — theme T-3 one level out
    # from the step, and the reason this control carried a `partial:` until the
    # remote locus existed to close it.
    return _platform_requires(remote, required_jobs)


def _platform_requires(
    remote: GitHub | NoCredentials | Unresolvable | None,
    required_jobs: frozenset[str],
) -> tuple[Verdict, str]:
    """Whether GitHub makes a merge wait for the jobs GOV-001 credited.

    The refusals are ADR 0021's, unchanged in meaning because they mean the same
    thing here: nobody asked, somebody asked and got no answer, or an answer.
    What differs is that a meta-control carries the verdict itself rather than a
    block carrying it, so the file half's result has to survive into the
    message — a bare "SKIPPED (no credentials)" would throw away the part that
    *was* verified.
    """
    reached = (
        "reached from a step that can fail, in a job the register requires "
        f"({', '.join(sorted(required_jobs))})"
    )
    if remote is None or isinstance(remote, NoCredentials):
        return (
            Verdict.SKIPPED_NO_CREDENTIALS,
            f"every applicable blocking control is {reached} — but whether GitHub enforces "
            "that is unread: no token was offered, and a recorded ruleset the platform was "
            "never told about protects nothing",
        )
    if isinstance(remote, Unresolvable):
        return (
            Verdict.UNCLASSIFIED,
            f"every applicable blocking control is {reached}; {remote.message}",
        )
    try:
        repository = remote.get(f"/repos/{remote.slug}")
        if not isinstance(repository, dict):
            raise Unreadable(f"/repos/{remote.slug} did not return a repository object")
        branch = repository.get("default_branch")
        if not isinstance(branch, str) or not branch:
            raise Unreadable(
                f"{remote.slug} reports no default branch, so there is none to ask about"
            )
        rules = remote.get(f"/repos/{remote.slug}/rules/branches/{branch}")
        if not isinstance(rules, list):
            raise Unreadable(
                f"the effective rules for {remote.slug}@{branch} did not come back as a list"
            )
    except Unreadable as exc:
        return (
            Verdict.UNCLASSIFIED,
            f"every applicable blocking control is {reached}; whether GitHub enforces that "
            f"could not be read: {exc}",
        )
    enforced = enforced_contexts(by_rule_type(rules))
    unenforced = sorted(job for job in required_jobs if job not in enforced)
    if unenforced:
        return (
            Verdict.FAIL,
            f"the register requires {', '.join(unenforced)} and GitHub does not: a merge to "
            f"{remote.slug}@{branch} waits for "
            + (", ".join(sorted(enforced)) if enforced else "no check at all")
            + " — every blocking control credited to those jobs is reached from a step "
            "nothing waits for",
        )
    return (
        Verdict.PASS,
        f"every applicable blocking control is {reached}, and GitHub enforces those checks on "
        f"{remote.slug}@{branch} — the whole chain from control to blocked merge is read",
    )


def _required_jobs(register: Register) -> frozenset[str]:
    """The status checks a recorded ruleset makes a merge wait for.

    Read from whichever control records a ruleset rather than from a name this
    module knows: it is CI-001 here, and a register is free to call it something
    else. An empty set means no control names a required check, and GOV-001 then
    answers only the half it always answered — said in the verdict rather than
    silently.
    """
    for control in register.controls:
        for block in control.verify:
            if block.assert_name != "ruleset_recorded_matches_register":
                continue
            checks = block.args.get("required_checks")
            if isinstance(checks, list):
                return frozenset(str(check) for check in checks)
    return frozenset()


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


def gov_002(
    register: Register,
    repo: Repo,
    _remote: GitHub | NoCredentials | Unresolvable | None = None,
) -> tuple[Verdict, str]:
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


def gov_003(
    register: Register,
    _repo: Repo,
    _remote: GitHub | NoCredentials | Unresolvable | None = None,
) -> tuple[Verdict, str]:
    """No control is past its review_by date, and no partial declaration expired.

    Both are the same mechanism: an expiry that turns silence into a build
    failure. ADR 0017 gives a partial declaration an expiry precisely so that
    "partial" cannot become permanent, and enforcing it here is what makes that
    promise real rather than decorative.
    """
    today = datetime.date.today()
    expired = [
        f"{control.id} (review_by {control.review_by.isoformat()})"
        for control in register.controls
        if control.review_by < today
    ]
    declared: list[Control | MetaControl] = [*register.controls, *register.meta_controls]
    expired += [
        f"{control.id} (partial declaration expired {block.partial.expires.isoformat()}: "
        f"{block.partial.unverified})"
        for control in declared
        for block in control.verify
        if block.partial is not None and block.partial.expires < today
    ]
    if expired:
        return Verdict.FAIL, "past their review date: " + ", ".join(expired)
    return Verdict.PASS, "no control is past its review date, and no partial declaration expired"


META_CHECKS = {
    "GOV-001": gov_001,
    "GOV-002": gov_002,
    "GOV-003": gov_003,
}
