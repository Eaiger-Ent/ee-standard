"""Assertions over platform state: what GitHub enforces, not what a file records.

These are the `kind: remote` blocks. They differ from every other assert in one
way that shapes the module: the thing they read can decline to answer. A file
assert that cannot read a file has learned something about the repository; a
remote assert that cannot read the platform has learned nothing about it, and
must say so rather than guess (ADR 0016, ADR 0021).

That is why these raise `remote.Unreadable` instead of returning `_fail`. A
`False` here would assert a violation the run never observed — the same
substitution `ruleset_recorded_matches_register` refuses in the other direction
when it declines to let a recorded ruleset stand in for an enforced one.

The requirements themselves are the register's, and the code that reads a set of
branch rules against them is `rulesets.py`'s — shared with the file block beside
these, so "protected" has one definition rather than two.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from standard_check.asserts_file import AssertResult
from standard_check.remote import GitHub, Unreadable
from standard_check.rulesets import by_rule_type, required_checks, requirement_problems

if TYPE_CHECKING:
    from standard_check.register import Register


def _ok(message: str) -> AssertResult:
    return AssertResult(True, message)


def _fail(message: str) -> AssertResult:
    return AssertResult(False, message)


def github_push_protection_enabled(
    github: GitHub,
    register: Register,
    args: Mapping[str, object],
) -> AssertResult:
    """Secret scanning push protection is on, so a credential is refused at the push.

    SEC-001's other three blocks all act on a credential that is already
    somewhere: `gitleaks` reads what git carries, and `.gitignore` acts before
    it is a git object. This one is the only block about the boundary itself —
    whether GitHub will refuse a push that carries a recognised secret — and no
    file can answer it.

    `security_and_analysis` being absent is `Unreadable`, not a failure. GitHub
    omits it for a caller without administration access, so a token that cannot
    see the setting would otherwise report push protection *off* on a repository
    where it is on — a false violation produced by not having looked.
    """
    repository = github.get(f"/repos/{github.slug}")
    if not isinstance(repository, dict):
        raise Unreadable(f"/repos/{github.slug} did not return a repository object")
    analysis = repository.get("security_and_analysis")
    if not isinstance(analysis, dict):
        raise Unreadable(
            f"{github.slug} reports no 'security_and_analysis' — the token cannot see "
            "the setting, which says nothing about whether push protection is enabled"
        )
    setting = analysis.get("secret_scanning_push_protection")
    status = setting.get("status") if isinstance(setting, dict) else None
    if status == "enabled":
        return _ok(f"{github.slug}: secret scanning push protection is enabled")
    if status is None:
        raise Unreadable(
            f"{github.slug} reports no 'secret_scanning_push_protection' status — the "
            "capability is not exposed to this token, and its absence is not evidence "
            "that pushes are unprotected"
        )
    return _fail(
        f"{github.slug}: secret scanning push protection is {status!r}, not 'enabled' — a "
        "credential that reaches a commit will reach the remote, and the two local blocks "
        "on this control are the only thing standing in its way"
    )


def default_branch_ruleset_satisfies(
    github: GitHub,
    register: Register,
    args: Mapping[str, object],
) -> AssertResult:
    """The rules GitHub actually applies to the default branch meet the register.

    Read from `/repos/{slug}/rules/branches/{branch}`, which reports the rules
    **in effect** on that branch rather than the rulesets that exist. That
    endpoint answers three things the recorded artefact has to state for itself:
    a ruleset in `evaluate` or `disabled` mode contributes nothing here, a
    ruleset whose conditions do not match the branch contributes nothing here,
    and a payload the API rejected was never applied at all. So a rule appearing
    in this response is a rule being enforced, which is the whole of what this
    block was written to establish.

    The branch is the repository's own `default_branch` rather than a name in
    the register: a ruleset targeting `~DEFAULT_BRANCH` protects whatever that
    is, and asking about a hard-coded `main` would stop being the same question
    the day a repository renamed it.
    """
    repository = github.get(f"/repos/{github.slug}")
    if not isinstance(repository, dict):
        raise Unreadable(f"/repos/{github.slug} did not return a repository object")
    branch = repository.get("default_branch")
    if not isinstance(branch, str) or not branch:
        raise Unreadable(f"{github.slug} reports no default branch, so there is none to ask about")

    rules: Any = github.get(f"/repos/{github.slug}/rules/branches/{branch}")
    if not isinstance(rules, list):
        raise Unreadable(
            f"the effective rules for {github.slug}@{branch} did not come back as a list"
        )
    problems = requirement_problems(by_rule_type(rules), args)
    if problems:
        return _fail(
            f"{github.slug}@{branch} is not protected as the register requires: "
            + "; ".join(problems)
        )
    checks = ", ".join(required_checks(args)) or "none named"
    return _ok(
        f"{github.slug}@{branch} is protected as the register requires, and GitHub reports "
        f"it in effect — a merge waits for {checks}"
    )


#: The closed set of `kind: remote` assert names, and their implementations. The
#: schema validates remote blocks against these keys, so a typo is a schema
#: error rather than a check that silently never runs.
REMOTE_ASSERTS = {
    "github_push_protection_enabled": github_push_protection_enabled,
    "default_branch_ruleset_satisfies": default_branch_ruleset_satisfies,
}
