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

import datetime
import re
from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any

from register_check.asserts_file import AssertResult
from register_check.remote import (
    CREDENTIAL_PROBE_PATH,
    OAUTH_SCOPES_HEADER,
    TOKEN_EXPIRY_HEADER,
    GitHub,
    Unreadable,
    fetch_text,
    runs_in_github_actions,
)
from register_check.rulesets import by_rule_type, required_checks, requirement_problems

if TYPE_CHECKING:
    from register_check.register import Register


def _ok(message: str) -> AssertResult:
    return AssertResult(True, message)


def _fail(message: str) -> AssertResult:
    return AssertResult(False, message)


# `2026-11-14 15:37:26 UTC`, the one shape GitHub sends. Parsed strictly rather
# than leniently: an expiry this cannot place in time is not an expiry it can
# compare, and guessing at a format would decide a control on a misreading.
_EXPIRY = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) UTC$")


def _register_maximum(register: Register) -> int:
    """The longest lifetime any credential in the register may have.

    The register's number, not the checker's (ADR 0018). A register naming no
    platform credential has no maximum to compare against, and a comparison
    against a number nobody wrote is the invented default this repository keeps
    catching.
    """
    if not register.platform_credentials:
        raise Unreadable(
            "the register names no platform credential, so there is no maximum lifetime "
            "to compare this token against — add a `platform_credentials:` entry"
        )
    return max(credential.max_lifetime_hours for credential in register.platform_credentials)


def platform_token_expires_within(
    github: GitHub,
    register: Register,
    _args: Mapping[str, object],
) -> AssertResult:
    """The credential CI carries expires inside the register's maximum.

    ADR 0022 requirement 3. Without it, "we will use a short-expiry token" is a
    promise rather than a property — the decaying policy ADR 0002 rejected a
    static cloud key for, applied to the platform instead of the cloud.

    **Two absences that look alike and are not.** A response carrying no expiry
    header means the credential does not expire *if the instrument is one that
    would have said so* — a classic token with no expiration date set. For a
    fine-grained or installation token the header is how expiry is reported at
    all, so its absence is GitHub declining to answer, and reporting a violation
    from it would be the substitution `github_push_protection_enabled` refuses
    one function above.

    **And this is a `locus: [ci]` control.** The token in a developer's shell is
    not the token CI carries, so answering from it would settle a question about
    a different credential. Outside GitHub Actions the block declines rather
    than passing or failing.
    """
    if not runs_in_github_actions():
        raise Unreadable(
            "this run is not a GitHub Actions job, so the token in the environment is not "
            "the credential CI carries — SEC-003's ci locus is answered by the run that "
            "carries it, and a developer's own token settles nothing about it"
        )
    maximum = _register_maximum(register)
    headers = github.headers(CREDENTIAL_PROBE_PATH)
    reported = headers.get(TOKEN_EXPIRY_HEADER, "").strip()
    if not reported:
        if OAUTH_SCOPES_HEADER in headers:
            return _fail(
                "the token CI carries is a classic personal access token with no expiry "
                f"date set, so it never expires — the register permits at most {maximum}h"
            )
        raise Unreadable(
            f"GitHub returned no {TOKEN_EXPIRY_HEADER} header for this token, and it is "
            "not the instrument whose silence means 'never expires' — what CI carries "
            "was not read, and nothing here claims it was"
        )
    match = _EXPIRY.match(reported)
    if match is None:
        raise Unreadable(
            f"{TOKEN_EXPIRY_HEADER} read {reported!r}, which is not the "
            "'YYYY-MM-DD HH:MM:SS UTC' shape this can place in time"
        )
    expires = datetime.datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S").replace(
        tzinfo=datetime.UTC
    )
    remaining = expires - datetime.datetime.now(tz=datetime.UTC)
    hours = remaining.total_seconds() / 3600
    if hours > maximum:
        return _fail(
            f"the token CI carries expires {expires.isoformat()}, which is {hours:.0f}h "
            f"away — the register permits at most {maximum}h"
        )
    return _ok(
        f"the token CI carries expires {expires.isoformat()}, inside the {maximum}h the "
        "register permits"
    )


def platform_token_is_not_classic(
    github: GitHub,
    _register: Register,
    _args: Mapping[str, object],
) -> AssertResult:
    """The credential CI carries is not a classic personal access token.

    ADR 0022 requirement 4, and the check that makes the `pull_request` exposure
    tolerable rather than merely bounded. A classic token grants its readers
    access to **every repository its owner can reach**; a fine-grained one
    grants what it was scoped to and nothing else. The difference is the whole
    argument for carrying a platform token at all, and "we use fine-grained
    tokens only" is a convention until something reads the instrument.

    `X-OAuth-Scopes` is returned for a classic token and for no other kind, so
    its **presence** identifies the instrument — including for a classic token
    with no scopes at all, where the header comes back empty. Reading the value
    rather than the presence would pass exactly that token.

    Note the limit honestly, as the requirement does: this identifies the *kind*
    of credential, not its scope. No API lets a fine-grained token enumerate its
    own permissions, so "scoped to this repository, `Administration: read` only"
    stays a human act recorded at issue time.
    """
    if not runs_in_github_actions():
        raise Unreadable(
            "this run is not a GitHub Actions job, so the token in the environment is not "
            "the credential CI carries — SEC-003's ci locus is answered by the run that "
            "carries it, and a developer's own token settles nothing about it"
        )
    headers = github.headers(CREDENTIAL_PROBE_PATH)
    if OAUTH_SCOPES_HEADER in headers:
        scopes = headers[OAUTH_SCOPES_HEADER].strip() or "none"
        return _fail(
            "the token CI carries is a classic personal access token (it returned "
            f"{OAUTH_SCOPES_HEADER}, scopes: {scopes}) — a classic token grants its readers "
            "access to every repository its owner can reach, which is what a fine-grained "
            "token is carried instead of"
        )
    return _ok(
        f"the token CI carries returned no {OAUTH_SCOPES_HEADER}, so it is not a classic "
        "personal access token — it is fine-grained or platform-minted"
    )


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
def release_checksums_match_register(
    _target: Any,
    register: Register,
    _args: Mapping[str, object],
) -> AssertResult:
    """Every pinned digest equals the one the project published for that release.

    SUP-004 (ADR 0041). Renovate's uv bump moved the version at all four sites
    the register names and left all three digests at the previous release's
    values, and every check passed. This is the check that would not have.

    **It presents no credential and must not**, which is why it ignores the
    target the runner resolves: a release manifest is public, and a check that
    can answer without a token reporting SKIPPED for want of one would be
    declining to answer a question it could have answered.

    A tool that publishes no manifest **passes**, saying so. Whether a project
    publishes checksums is a fact about that project, and failing a repository
    for someone else's release process would make the conformance run
    unpassable for a reason nobody in it could fix.
    """
    checked: list[str] = []
    silent: list[str] = []
    problems: list[str] = []
    for name, tool in sorted(register.tools.items()):
        if tool.checksums is None:
            if tool.sha256 is not None:
                silent.append(name)
            continue
        if tool.version is None:  # pragma: no cover — the schema requires one
            continue
        url = tool.checksums.manifest_url(tool.release_repo or "", tool.version)
        published = _published_digests(url)
        for asset, pinned in tool.checksums.digests(tool.version, tool.sha256).items():
            actual = published.get(asset)
            if actual is None:
                problems.append(
                    f"{name}: the release publishes no digest for '{asset}' — the register "
                    "names an asset this release does not have"
                )
            elif actual != pinned:
                problems.append(
                    f"{name}: {asset} is pinned at {pinned[:12]}… and the release published "
                    f"{actual[:12]}… — the pin names a different artefact"
                )
            else:
                checked.append(f"{name}/{asset}")
    if problems:
        return _fail("; ".join(problems))
    note = f"; {len(silent)} tool(s) publish no manifest and were not compared" if silent else ""
    return _ok(f"{len(checked)} pinned digest(s) match what the project published{note}")


def _published_digests(url: str) -> dict[str, str]:
    """A `sha256sum`-style manifest, as asset name to digest.

    Both spellings, because both pinned tools use one: gitleaks writes
    `<digest>  <file>` and uv writes `<digest> *<file>`, the second being
    `sha256sum`'s binary marker. Reading only one would have covered one tool.
    """
    found: dict[str, str] = {}
    for line in fetch_text(url).splitlines():
        parts = line.split()
        if len(parts) != 2 or not _DIGEST.fullmatch(parts[0]):
            continue
        found[parts[1].lstrip("*")] = parts[0]
    return found


_DIGEST = re.compile(r"[0-9a-f]{64}")

#: Remote asserts that answer without a credential, so the runner must not
#: short-circuit them to SKIPPED (no credentials). A release manifest is public;
#: everything else here reads a repository's own platform state and cannot be.
PUBLIC_REMOTE_ASSERTS = frozenset({"release_checksums_match_register"})

#: The signature every remote assert shares. `GitHub | None` rather than
#: `GitHub`, because a public assert is handed `None`: it reads something the
#: platform serves to anyone, so there is no credential to give it.
RemoteAssertFn = Callable[[Any, "Register", Mapping[str, object]], AssertResult]

REMOTE_ASSERTS: dict[str, RemoteAssertFn] = {
    "release_checksums_match_register": release_checksums_match_register,
    "github_push_protection_enabled": github_push_protection_enabled,
    "default_branch_ruleset_satisfies": default_branch_ruleset_satisfies,
    "platform_token_expires_within": platform_token_expires_within,
    "platform_token_is_not_classic": platform_token_is_not_classic,
}
