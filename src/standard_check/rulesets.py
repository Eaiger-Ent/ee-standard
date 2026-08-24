"""How GitHub spells a protected branch — one reading, two readers.

CI-001 asks the same question twice. `ruleset_recorded_matches_register` asks it
of the artefact the repository records, which is *intent*;
`default_branch_ruleset_satisfies` asks it of the rules the platform reports as
effective, which is *enforcement*. The register states the requirement once and
both blocks read the same `args:` — and the code that turns those args into a
judgement about a set of rules lives here, once, for the same reason.

Two implementations of "protected" would be theme **T-2** arriving in the
checker rather than the register: the file half could go on passing while the
remote half read the same rules differently, and the disagreement would be
invisible because no test compares two copies of a rule to each other.

What is *not* shared is deliberate. The recorded artefact carries an
`enforcement` field, `conditions`, and a payload GitHub's API has to accept —
none of which the effective-rules endpoint returns, because a rule only appears
there when it is already active and already applies to the branch asked about.
The platform answers those three questions by responding at all.
"""

from __future__ import annotations

from collections.abc import Mapping

#: How a GitHub ruleset spells each requirement. The *rules* are the register's
#: — which requirements a protected branch must carry is `args:` — while the
#: shape of GitHub's own JSON is not something a repository can differ on, so it
#: stays here (ADR 0018).
RULE_TYPES = {
    "require_pull_request": "pull_request",
    "require_status_checks": "required_status_checks",
    "allow_force_push": "non_fast_forward",
}


def required_checks(args: Mapping[str, object]) -> list[str]:
    """The status-check contexts the register requires a merge to wait for."""
    raw = args.get("required_checks")
    return [str(entry) for entry in raw] if isinstance(raw, list) else []


def by_rule_type(rules: object) -> dict[str, Mapping[str, object]]:
    """Index a list of rule objects by `type`.

    Both sources hand over the same rule shape — `{"type": ..., "parameters":
    ...}` — the recorded artefact inside a `rules:` array and the platform as a
    bare array. Indexing them the same way is what lets one judgement read both.
    """
    return {
        str(rule.get("type")): rule
        for rule in (rules if isinstance(rules, list) else [])
        if isinstance(rule, dict)
    }


def enforced_contexts(by_type: Mapping[str, Mapping[str, object]]) -> set[str]:
    """The status-check contexts a set of rules actually makes a merge wait for.

    Two readers, one reading — the reason this module exists. CI-001's blocks
    ask whether the branch is protected as the register requires; GOV-001 asks
    whether the job it credited a blocking control to is one of the checks a
    merge waits for. Those are different questions about the same list, and a
    second extraction of it could drift from this one with nothing comparing
    them.
    """
    rule = by_type.get(RULE_TYPES["require_status_checks"])
    parameters = rule.get("parameters") if rule is not None else None
    entries = parameters.get("required_status_checks") if isinstance(parameters, dict) else None
    return {
        str(entry.get("context"))
        for entry in (entries if isinstance(entries, list) else [])
        if isinstance(entry, dict)
    }


def requirement_problems(
    by_type: Mapping[str, Mapping[str, object]],
    args: Mapping[str, object],
) -> list[str]:
    """Where a set of branch rules falls short of what the register requires.

    Reads what a rule *does*, not that a rule of that name is present — the
    defect register contract 19 closed. A `required_status_checks` rule naming
    no context requires no check, and would otherwise satisfy
    `require_status_checks: true` while gating nothing.
    """
    problems: list[str] = []
    if args.get("require_pull_request") is True and RULE_TYPES["require_pull_request"] not in (
        by_type
    ):
        problems.append("no 'pull_request' rule — the default branch can be written to directly")
    if args.get("require_status_checks") is True and RULE_TYPES["require_status_checks"] not in (
        by_type
    ):
        problems.append("no 'required_status_checks' rule — a pull request can merge unchecked")
    # `non_fast_forward` is the rule that *forbids* force-push, so the register's
    # `allow_force_push: false` requires it to be present. Stated rather than
    # inferred: the register says what is allowed and GitHub names what is
    # blocked, and reading one as the other is how a control ends up inverted.
    if args.get("allow_force_push") is False and RULE_TYPES["allow_force_push"] not in by_type:
        problems.append(
            "no 'non_fast_forward' rule — history on the default branch can be rewritten"
        )
    problems.extend(_status_check_problems(by_type, args))
    return problems


def _status_check_problems(
    by_type: Mapping[str, Mapping[str, object]],
    args: Mapping[str, object],
) -> list[str]:
    """What the status-check rule actually requires, rather than that it exists."""
    if args.get("require_status_checks") is not True:
        return []
    rule = by_type.get(RULE_TYPES["require_status_checks"])
    if rule is None:
        return []  # already reported as an absent rule
    required = required_checks(args)
    if not required:
        return [
            "the register requires status checks and names none in `required_checks` — a "
            "rule requiring zero checks lets a pull request merge with CI red, so there is "
            "nothing here for a ruleset to satisfy"
        ]
    parameters = rule.get("parameters")
    if not isinstance(parameters, dict):
        return []  # already reported as a payload the API rejects
    present = enforced_contexts(by_type)
    problems: list[str] = []
    missing = [check for check in required if check not in present]
    if missing:
        problems.append(
            "does not require " + ", ".join(missing) + " — a "
            "'required_status_checks' rule naming "
            + (f"only {', '.join(sorted(present))}" if present else "no check at all")
            + " does not gate what the register says it gates"
        )
    strict = parameters.get("strict_required_status_checks_policy")
    wanted = args.get("require_branches_up_to_date")
    if isinstance(wanted, bool) and strict is not wanted:
        problems.append(
            f"strict_required_status_checks_policy is {strict!r} where the register says "
            f"{wanted!r} — with it off, a check that passed against stale code counts"
        )
    return problems
