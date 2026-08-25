"""Phase 3: what remote verification reports, and what it refuses to report.

The three refusals are the point of these tests. A remote block that cannot
reach the platform has learned nothing about the repository, and the register's
whole argument is that a check which cannot answer must say so rather than pick
a side (ADR 0016, ADR 0021). Every test here is about which of PASS, FAIL,
SKIPPED (no credentials) and UNCLASSIFIED a given non-answer earns.
"""

from __future__ import annotations

import datetime
import email.message
import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import pytest

from conftest import (
    FakeGitHub,
    a_register,
    make_repo,
    minimal_register,
    register_with,
    write_register,
)
from register_check import remote as remote_module
from register_check.asserts_remote import (
    REMOTE_ASSERTS,
    default_branch_ruleset_satisfies,
    github_push_protection_enabled,
    platform_token_expires_within,
    platform_token_is_not_classic,
)
from register_check.remote import (
    CI_VARIABLE,
    OAUTH_SCOPES_HEADER,
    TOKEN_EXPIRY_HEADER,
    GitHub,
    NoCredentials,
    Unreadable,
    Unresolvable,
)
from register_check.repo import Repo
from register_check.runner import Verdict, run_control

# The register's own CI-001 arguments. Held here so a test that changes what
# "protected" means has to say so out loud rather than drift quietly.
RULESET_ARGS: dict[str, Any] = {
    "require_pull_request": True,
    "require_status_checks": True,
    "allow_force_push": False,
    "required_checks": ["register-check", "lint-md"],
    "require_branches_up_to_date": True,
}


def satisfying_rules(
    contexts: list[str] | None = None, strict: bool = True
) -> list[dict[str, Any]]:
    """The effective-rules response of a branch protected as the register requires."""
    if contexts is None:
        contexts = list(RULESET_ARGS["required_checks"])
    return [
        {"type": "pull_request", "parameters": {"required_approving_review_count": 0}},
        {
            "type": "required_status_checks",
            "parameters": {
                "strict_required_status_checks_policy": strict,
                "required_status_checks": [{"context": name} for name in contexts],
            },
        },
        {"type": "non_fast_forward"},
        {"type": "deletion"},
    ]


def protected_repo(
    *, push_protection: str | None = "enabled", branch: str = "main", **rules: Any
) -> FakeGitHub:
    analysis: dict[str, Any] | None = (
        None
        if push_protection is None
        else {"secret_scanning_push_protection": {"status": push_protection}}
    )
    return FakeGitHub(
        {
            "/repos/acme/widget": {"default_branch": branch, "security_and_analysis": analysis},
            f"/repos/acme/widget/rules/branches/{branch}": rules.get(
                "effective", satisfying_rules()
            ),
        }
    )


# --- resolving the target ---------------------------------------------------


def test_no_token_is_no_credentials_not_a_guess(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, {"a.txt": "x"})
    outcome = remote_module.resolve(repo, environ={})
    assert isinstance(outcome, NoCredentials)
    assert "no GitHub token" in outcome.message


@pytest.mark.parametrize("variable", remote_module.TOKEN_VARIABLES)
def test_either_token_spelling_is_accepted(tmp_path: Path, variable: str) -> None:
    """`gh` exports one name and GitHub Actions injects the other."""
    repo = make_repo(tmp_path, {"a.txt": "x"})
    subprocess.run(
        ["git", "-C", str(tmp_path), "remote", "add", "origin", "https://github.com/acme/widget"],
        check=True,
    )
    outcome = remote_module.resolve(repo, environ={variable: "secret"})
    assert isinstance(outcome, GitHub)
    assert (outcome.slug, outcome.token) == ("acme/widget", "secret")


def test_a_token_with_no_repository_to_ask_about_is_not_a_credentials_skip(
    tmp_path: Path,
) -> None:
    """Credentials were offered. The remedy is a repository, not a token."""
    repo = make_repo(tmp_path, {"a.txt": "x"})
    outcome = remote_module.resolve(repo, environ={"GITHUB_TOKEN": "secret"})
    assert isinstance(outcome, Unresolvable)
    assert "--github-repo" in outcome.message


def test_the_override_wins_over_the_origin_remote(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, {"a.txt": "x"})
    subprocess.run(
        ["git", "-C", str(tmp_path), "remote", "add", "origin", "https://github.com/acme/fork"],
        check=True,
    )
    outcome = remote_module.resolve(repo, "acme/upstream", environ={"GITHUB_TOKEN": "secret"})
    assert isinstance(outcome, GitHub)
    assert outcome.slug == "acme/upstream"


def test_a_malformed_override_is_refused_rather_than_sent(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, {"a.txt": "x"})
    outcome = remote_module.resolve(repo, "https://evil.example/x", environ={"GITHUB_TOKEN": "s"})
    assert isinstance(outcome, Unresolvable)


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/acme/widget.git",
        "https://github.com/acme/widget",
        "git@github.com:acme/widget.git",
    ],
)
def test_the_slug_is_read_from_every_remote_url_spelling(tmp_path: Path, url: str) -> None:
    repo = make_repo(tmp_path, {"a.txt": "x"})
    subprocess.run(["git", "-C", str(tmp_path), "remote", "add", "origin", url], check=True)
    assert repo.github_slug() == "acme/widget"


# --- what an HTTP status earns ----------------------------------------------


@pytest.mark.parametrize("code", [401, 403, 404, 500])
def test_every_http_failure_is_unreadable_never_a_violation(
    monkeypatch: pytest.MonkeyPatch, code: int
) -> None:
    """A status is a fact about the request, never about the repository.

    401 and 403 in particular are UNCLASSIFIED rather than SKIPPED (no
    credentials): a token that was presented and rejected needs fixing, and a
    token that was never supplied needs supplying. Collapsing the two tells the
    operator to do the wrong thing.
    """

    def raising(*_: Any, **__: Any) -> Any:
        raise urllib.error.HTTPError("https://api.github.com/x", code, "no", {}, None)  # type: ignore[arg-type]

    monkeypatch.setattr(urllib.request, "urlopen", raising)
    with pytest.raises(Unreadable):
        GitHub("acme/widget", "t").get("/repos/acme/widget")


def test_a_network_failure_is_unreadable(monkeypatch: pytest.MonkeyPatch) -> None:
    def raising(*_: Any, **__: Any) -> Any:
        raise urllib.error.URLError("name resolution failed")

    monkeypatch.setattr(urllib.request, "urlopen", raising)
    with pytest.raises(Unreadable, match="could not reach"):
        GitHub("acme/widget", "t").get("/repos/acme/widget")


def test_the_token_is_sent_as_a_bearer_header(monkeypatch: pytest.MonkeyPatch) -> None:
    """And nowhere else — never in the URL, which proxies and logs retain."""
    seen: dict[str, Any] = {}

    class Response:
        headers = email.message.Message()

        def read(self) -> bytes:
            return json.dumps({"ok": True}).encode()

        def __enter__(self) -> Response:
            return self

        def __exit__(self, *_: Any) -> None:
            return None

    def capturing(request: Any, **__: Any) -> Any:
        seen["url"] = request.full_url
        seen["auth"] = request.get_header("Authorization")
        return Response()

    monkeypatch.setattr(urllib.request, "urlopen", capturing)
    GitHub("acme/widget", "s3cret").get("/repos/acme/widget")
    assert seen["auth"] == "Bearer s3cret"
    assert "s3cret" not in seen["url"]


# --- push protection --------------------------------------------------------


def test_push_protection_enabled_passes() -> None:
    result = github_push_protection_enabled(protected_repo(), a_register(), {})
    assert result.passed


def test_push_protection_disabled_fails() -> None:
    result = github_push_protection_enabled(
        protected_repo(push_protection="disabled"), a_register(), {}
    )
    assert not result.passed
    assert "not 'enabled'" in result.message


def test_a_setting_the_token_cannot_see_is_not_a_setting_that_is_off() -> None:
    """GitHub omits `security_and_analysis` from a non-administrator's answer.

    Reading that absence as "push protection is off" would report a violation on
    a repository where it is on, produced entirely by not having looked.
    """
    with pytest.raises(Unreadable, match="says nothing about"):
        github_push_protection_enabled(protected_repo(push_protection=None), a_register(), {})


# --- the branch ruleset -----------------------------------------------------


def test_a_branch_protected_as_the_register_requires_passes() -> None:
    result = default_branch_ruleset_satisfies(protected_repo(), a_register(), RULESET_ARGS)
    assert result.passed, result.message
    assert "register-check, lint-md" in result.message


def test_the_default_branch_is_the_repositorys_own_not_a_hard_coded_name() -> None:
    """A ruleset targeting ~DEFAULT_BRANCH protects whatever that branch is."""
    result = default_branch_ruleset_satisfies(
        protected_repo(branch="trunk"), a_register(), RULESET_ARGS
    )
    assert result.passed
    assert "@trunk" in result.message


def test_no_effective_rules_at_all_fails() -> None:
    """The endpoint returning `[]` is an answer: nothing protects the branch.

    Distinct from every refusal above — the platform spoke, and what it said was
    that a ruleset exists nowhere or is not active. That is a violation, and
    reporting it as unverified would be the mirror of the error the refusals
    avoid.
    """
    result = default_branch_ruleset_satisfies(
        protected_repo(effective=[]), a_register(), RULESET_ARGS
    )
    assert not result.passed
    assert "no 'pull_request' rule" in result.message
    assert "no 'non_fast_forward' rule" in result.message


def test_a_status_check_rule_naming_no_context_fails() -> None:
    """Contract 19's defect, asked of the platform instead of the file."""
    result = default_branch_ruleset_satisfies(
        protected_repo(effective=satisfying_rules(contexts=[])), a_register(), RULESET_ARGS
    )
    assert not result.passed
    assert "no check at all" in result.message


def test_a_missing_required_check_fails() -> None:
    result = default_branch_ruleset_satisfies(
        protected_repo(effective=satisfying_rules(contexts=["register-check"])),
        a_register(),
        RULESET_ARGS,
    )
    assert not result.passed
    assert "lint-md" in result.message


def test_a_non_strict_policy_fails() -> None:
    result = default_branch_ruleset_satisfies(
        protected_repo(effective=satisfying_rules(strict=False)), a_register(), RULESET_ARGS
    )
    assert not result.passed
    assert "strict_required_status_checks_policy" in result.message


# --- the runner's mapping ---------------------------------------------------


def _remote_control(tmp_path: Path, assert_name: str) -> tuple[Any, Repo]:
    document = minimal_register(
        locus=["remote"],
        verify=[{"kind": "remote", "assert": assert_name}],
    )
    write_register(tmp_path, document)
    repo = make_repo(tmp_path, {})
    register, errors = _load(tmp_path)
    assert register is not None, errors
    return register, repo


def _load(tmp_path: Path) -> Any:
    from register_check.register import load_register

    return load_register(tmp_path / "controls.yaml")


def test_no_credentials_skips_and_an_unreadable_platform_does_not(tmp_path: Path) -> None:
    register, repo = _remote_control(tmp_path, "github_push_protection_enabled")
    control = register.controls[0]

    skipped = run_control(control, register, repo, NoCredentials("no token"))
    assert skipped.verdict is Verdict.SKIPPED_NO_CREDENTIALS

    unresolved = run_control(control, register, repo, Unresolvable("which repository?"))
    assert unresolved.verdict is Verdict.UNCLASSIFIED

    unreadable = run_control(
        control,
        register,
        repo,
        FakeGitHub({"/repos/acme/widget": Unreadable("403")}),
    )
    assert unreadable.verdict is Verdict.UNCLASSIFIED


def test_the_platform_answering_yields_pass_or_fail(tmp_path: Path) -> None:
    register, repo = _remote_control(tmp_path, "github_push_protection_enabled")
    control = register.controls[0]
    assert run_control(control, register, repo, protected_repo()).verdict is Verdict.PASS
    off = run_control(control, register, repo, protected_repo(push_protection="disabled"))
    assert off.verdict is Verdict.FAIL


def test_a_raising_assert_does_not_abort_the_audit(tmp_path: Path) -> None:
    """One unanswerable control must not cost every other control its verdict."""
    register, repo = _remote_control(tmp_path, "github_push_protection_enabled")
    exploding = FakeGitHub({"/repos/acme/widget": ValueError("boom")})
    result = run_control(register.controls[0], register, repo, exploding)
    assert result.verdict is Verdict.UNCLASSIFIED
    assert "ValueError" in result.blocks[0].message


# --- the closed set ---------------------------------------------------------


def test_the_register_declares_only_implemented_remote_asserts() -> None:
    """No remote block may name an assert nothing implements.

    The schema enforces this, but the point here is the other direction: Phase 3
    is not finished while a `kind: remote` block in the shipped register has no
    implementation behind it.
    """
    from register_check.register import load_register

    register, _ = load_register(Path(__file__).resolve().parent.parent / "controls.yaml")
    assert register is not None
    declared = {
        block.assert_name
        for control in register.controls
        for block in control.verify
        if block.kind == "remote"
    }
    assert declared, "the register declares no remote blocks — this phase has nothing to verify"
    assert declared <= set(REMOTE_ASSERTS)


# --- one reading, two readers -----------------------------------------------


def test_the_recorded_ruleset_and_the_platform_are_judged_by_one_function() -> None:
    """The artefact `gate-repo` records passes the *remote* reading of it.

    `test_gate_repo_deploy.py` already guards the register against carrying two
    different `args:`. This guards the checker against carrying two different
    readings of them: the recorded `rules:` array is handed to the remote assert
    exactly as the platform would report it, and must earn the same verdict the
    file assert gives it. Two readings could otherwise disagree with nothing
    comparing them — theme T-2, arriving in the checker instead of the register.
    """
    from register_check.register import load_register
    from register_check.repo import load_jsonc

    root = Path(__file__).resolve().parent.parent
    register, _ = load_register(root / "controls.yaml")
    assert register is not None
    control = next(c for c in register.controls if c.id == "CI-001")
    block = next(b for b in control.verify if b.assert_name == "default_branch_ruleset_satisfies")

    recorded = load_jsonc(root / ".github/rulesets/default-branch.json")
    assert isinstance(recorded, dict)
    as_the_platform_reports_it = FakeGitHub(
        {
            "/repos/acme/widget": {"default_branch": "main", "security_and_analysis": {}},
            "/repos/acme/widget/rules/branches/main": recorded["rules"],
        }
    )
    result = default_branch_ruleset_satisfies(
        as_the_platform_reports_it, a_register(), block.args
    )
    assert result.passed, result.message


def test_there_is_no_second_copy_of_the_rule_vocabulary() -> None:
    """Both asserts read GitHub's rule spellings from `rulesets.py`, not their own."""
    import register_check.asserts_command as file_side
    import register_check.asserts_remote as remote_side
    from register_check import rulesets

    for module in (file_side, remote_side):
        assert (
            getattr(module, "requirement_problems", None) is rulesets.requirement_problems
        ), f"{module.__name__} does not read requirements through rulesets.py"
    for module in (file_side, remote_side):
        assert not hasattr(module, "_RULE_TYPES"), (
            f"{module.__name__} has its own rule-type map — one reading, two readers"
        )


# --- SEC-003's remote block: the expiry of the credential CI carries ---------


def _in_actions(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(CI_VARIABLE, "true")


def _expiring_in(hours: float) -> FakeGitHub:
    when = datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(hours=hours)
    return FakeGitHub({}, headers={TOKEN_EXPIRY_HEADER: when.strftime("%Y-%m-%d %H:%M:%S UTC")})


def _registers_maximum() -> int:
    """The ceiling the register permits, read rather than repeated.

    A test asserting `24h` was a second copy of a register value, and it broke
    the day this repository named a standing credential — which is the register
    moving, exactly as it is supposed to.
    """
    return max(c.max_lifetime_hours for c in a_register().platform_credentials)


def test_a_token_expiring_inside_the_registers_maximum_passes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _in_actions(monkeypatch)
    result = platform_token_expires_within(_expiring_in(_registers_maximum() / 2), a_register(), {})
    assert result.passed
    assert f"{_registers_maximum()}h" in result.message


def test_a_token_outliving_the_registers_maximum_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The case the requirement exists for: a standing credential in CI."""
    _in_actions(monkeypatch)
    result = platform_token_expires_within(_expiring_in(_registers_maximum() * 2), a_register(), {})
    assert not result.passed
    assert f"{_registers_maximum()}h" in result.message


def test_the_maximum_moves_with_the_register(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Widen the register and the same token passes — the assert holds no number."""
    _in_actions(monkeypatch)
    beyond = _registers_maximum() * 2
    token = _expiring_in(beyond)
    assert not platform_token_expires_within(token, a_register(), {}).passed

    def permit_longer(document: dict[str, Any]) -> None:
        document["platform_credentials"].append(
            {
                "name": "ANOTHER_STANDING_TOKEN",
                "triggers": ["push"],
                "max_lifetime_hours": beyond * 2,
            }
        )

    assert platform_token_expires_within(token, register_with(tmp_path, permit_longer), {}).passed


def test_a_classic_token_with_no_expiry_set_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """An absent header **is** the answer when the instrument would have said."""
    _in_actions(monkeypatch)
    classic = FakeGitHub({}, headers={OAUTH_SCOPES_HEADER: "repo, workflow"})
    result = platform_token_expires_within(classic, a_register(), {})
    assert not result.passed
    assert "never expires" in result.message


def test_an_absent_header_on_another_instrument_is_not_a_violation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """And is not the answer when it is GitHub declining to give one.

    The same shape `github_push_protection_enabled` refuses: a fine-grained or
    installation token reports its expiry *through* this header, so reading its
    absence as "never expires" would report a violation produced by not having
    looked.
    """
    _in_actions(monkeypatch)
    with pytest.raises(Unreadable) as raised:
        platform_token_expires_within(FakeGitHub({}, headers={}), a_register(), {})
    assert "was not read" in str(raised.value)


def test_an_expiry_that_cannot_be_placed_in_time_is_unreadable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _in_actions(monkeypatch)
    odd = FakeGitHub({}, headers={TOKEN_EXPIRY_HEADER: "next Tuesday"})
    with pytest.raises(Unreadable):
        platform_token_expires_within(odd, a_register(), {})


def test_outside_actions_the_block_declines_rather_than_answering() -> None:
    """SEC-003's locus is `ci`, and a developer's token is a different credential."""
    with pytest.raises(Unreadable) as raised:
        platform_token_expires_within(_expiring_in(1), a_register(), {})
    assert "not a GitHub Actions job" in str(raised.value)


def test_a_register_naming_no_platform_credential_has_no_maximum(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """No number in the register means no comparison, not a default in the checker."""
    _in_actions(monkeypatch)

    def forget_them(document: dict[str, Any]) -> None:
        del document["platform_credentials"]

    with pytest.raises(Unreadable) as raised:
        platform_token_expires_within(_expiring_in(1), register_with(tmp_path, forget_them), {})
    assert "no maximum lifetime" in str(raised.value)


# --- SEC-003's second remote block: what the credential *is* -----------------


def test_a_classic_token_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    _in_actions(monkeypatch)
    classic = FakeGitHub({}, headers={OAUTH_SCOPES_HEADER: "repo, workflow"})
    result = platform_token_is_not_classic(classic, a_register(), {})
    assert not result.passed
    assert "repo, workflow" in result.message


def test_a_scopeless_classic_token_is_refused_too(monkeypatch: pytest.MonkeyPatch) -> None:
    """Presence identifies the instrument; the value does not.

    A classic token with no scopes returns the header empty, and a check reading
    the value rather than the presence would pass the one credential that
    reaches everything its owner can.
    """
    _in_actions(monkeypatch)
    scopeless = FakeGitHub({}, headers={OAUTH_SCOPES_HEADER: ""})
    result = platform_token_is_not_classic(scopeless, a_register(), {})
    assert not result.passed
    assert "none" in result.message


def test_a_token_that_is_not_classic_passes(monkeypatch: pytest.MonkeyPatch) -> None:
    _in_actions(monkeypatch)
    fine_grained = FakeGitHub({}, headers={TOKEN_EXPIRY_HEADER: "2026-11-14 15:37:26 UTC"})
    assert platform_token_is_not_classic(fine_grained, a_register(), {}).passed


def test_the_instrument_is_not_read_outside_actions() -> None:
    """Same reason as the expiry block: a developer's token is a different credential."""
    with pytest.raises(Unreadable) as raised:
        platform_token_is_not_classic(FakeGitHub({}, headers={}), a_register(), {})
    assert "not a GitHub Actions job" in str(raised.value)
