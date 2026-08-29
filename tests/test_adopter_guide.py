"""A control that asks the platform something owes an adopter the credential it needs.

`04-build-plan.md` § A standing requirement says every phase writes down the
adopter steps it introduces, and its own test for that is *"could someone who
has never seen this repository do it, and know that they had?"* — which no test
can answer. What a test can hold is the narrower property that made the
requirement necessary: a step is missing from the guide most often because
nobody noticed it had been introduced.

So this file derives the list from the register rather than keeping one. Every
control carrying a `kind: remote` block asks GitHub a question, and every such
question needs a token with some particular access — which is the one thing an
adopter cannot work out from their own repository, cannot discover by running
the checker (it reports `SKIPPED (no credentials)` and stops), and will not
guess right, because the scopes differ per control and the surprising one is
that reading a *setting* needs administration access.

A control gaining a remote block therefore fails here until § 4.1's table says
what it reads and what that needs. GOV-001's remote half is not a verify block —
the runner hands a meta-control the resolved platform target — so it is named
here rather than derived, and named for that reason rather than as an oversight.
"""

from __future__ import annotations

import re

import pytest

from conftest import REPO_ROOT, a_register

GUIDE = REPO_ROOT / "docs/08-adopting.md"
GUIDE_TEXT = GUIDE.read_text(encoding="utf-8")

#: § 4.1's table of what each remote check reads and what it needs to read it.
SCOPES_SECTION = "**The scopes are not the same for each control**"

#: The one remote check that is not a verify block, and so cannot be derived.
#: A meta-control receives the resolved platform target from the runner
#: (register contract 26), which is what lets it read the enforced checks.
UNDERIVABLE = {"GOV-001"}


def _remote_controls() -> set[str]:
    return {
        control.id
        for control in a_register().controls
        for block in control.verify
        if block.kind == "remote"
    }


def _scopes_table() -> str:
    body = GUIDE_TEXT.split(SCOPES_SECTION, 1)[1]
    return body.split("\n\n**", 1)[0]


def test_the_guide_has_the_section_the_table_lives_in() -> None:
    """Checked separately so a rename fails here rather than emptying the tests below."""
    assert SCOPES_SECTION in GUIDE_TEXT, f"{GUIDE.name} § 4.1 no longer introduces its table"


@pytest.mark.parametrize("control_id", sorted(_remote_controls() | UNDERIVABLE))
def test_every_remote_check_tells_an_adopter_what_credential_it_needs(control_id: str) -> None:
    """The scopes differ per control, and the surprising one is not guessable.

    SEC-001 reads a *setting* and needs repository administration access to see
    it at all — GitHub omits the object rather than reporting the setting off.
    An adopter who assumes one token answers everything gets `UNCLASSIFIED` on a
    repository where the control holds, with nothing saying which token to fix.
    """
    assert control_id in _scopes_table(), (
        f"{control_id} asks the platform something and § 4.1's table does not say "
        "what token can answer it"
    )


def test_the_guide_says_how_to_confirm_a_required_check_and_how_to_credential_ci() -> None:
    """The two sections Phase 3's adopter criterion names, by what they must contain.

    Not by heading text, which is decoration — by the three things an adopter
    cannot get anywhere else: that a recorded ruleset is not an enforced one,
    that the credential goes behind a branch policy rather than in a plain
    repository secret, and that `--require-complete` comes *after* the
    credential rather than before it.
    """
    text = " ".join(GUIDE_TEXT.split())
    assert "rules/branches" in text, "no way given to read what GitHub actually enforces"
    assert "deployment environment" in text.lower()
    assert "--require-complete" in text
    assert "token, confirm the remote blocks answer, then the flag" in text


def test_the_guide_says_which_exit_code_to_expect_conditionally() -> None:
    """`3` was flatly "the expected result" for as long as remote verification did not exist.

    It stopped being true on 2026-08-22, and the sentence outlived it in two
    shipped files until Phase 3's tenth slice. The guide is the third place it
    could stand, and the one an adopter reads first — so what is held here is
    the conditional framing rather than the absence of one wording, because the
    claim can be made wrong in more ways than it can be spelled.
    """
    text = " ".join(GUIDE_TEXT.split())
    assert "Whether `3` is the expected result now depends on your environment" in text
    assert "not reachable today" not in text


_FENCED_YAML = re.compile(r"```yaml\n(.*?)```", re.DOTALL)


def test_no_yaml_example_hands_ci_a_secret_without_a_branch_policy() -> None:
    """The guide must not show an adopter the arrangement this repository takes.

    `tests/test_posture.py` holds `plugins/` to this; the guide is the other
    place the shape could travel, and the more likely one — a reader copies the
    example, not the plugin. A workflow fragment reaching a stored secret needs
    the `environment:` line in the same fragment, because that is where the
    branch policy a pull request cannot edit is attached.
    """
    for block in _FENCED_YAML.findall(GUIDE_TEXT):
        reached = {
            name
            for name in re.findall(r"secrets\.([A-Za-z_][A-Za-z0-9_-]*)", block)
            if name != "GITHUB_TOKEN"
        }
        if not reached:
            continue
        assert "environment:" in block, (
            f"this example reaches {', '.join(sorted(reached))} with no environment gate:\n{block}"
        )


_FENCED_BASH = re.compile(r"```bash\n(.*?)```", re.DOTALL)

#: The directory the shipped template is copied out of. Its placeholders are
#: derived from it rather than listed here, so a fifth one fails this file.
TEMPLATE = REPO_ROOT / "plugins/control-register/templates/devcontainer"

_PLACEHOLDER = re.compile(r"\{\{[A-Z0-9_]+\}\}")


def test_no_example_reaches_the_checker_off_path() -> None:
    """§ 2.3 states the rule; until Phase 4's last criterion, the examples broke it.

    Two copy-and-paste blocks spelled `register-check run --control …` with no
    `uv run` in front, which is ADR 0020 case C offered to a reader as an
    instruction — a bare name resolves against `PATH`, so what answered would be
    some other copy auditing their repository. A rule stated in one section and
    contradicted in another is worse than an unstated one, because the reader
    following the commands never reaches the sentence.
    """
    for block in _FENCED_BASH.findall(GUIDE_TEXT):
        for line in block.splitlines():
            command = line.split("#", 1)[0].strip()
            assert not command.startswith("register-check "), (
                f"this example reaches the checker off PATH: {command}"
            )


def test_the_guide_names_every_placeholder_the_template_ships() -> None:
    """A placeholder nobody is told to substitute survives into a built container.

    Derived from the template rather than listed, because the failure mode is a
    placeholder being *added* and the guide not hearing about it: Phase 4 met
    the same shape from the other direction, with `{{UV_SHA256_AARCH64}}` named
    in § 2.0 and sourced nowhere, so the value the consumer repository carries
    came out of the operator's head rather than out of any instruction.
    """
    shipped = {
        placeholder
        for path in TEMPLATE.rglob("*")
        if path.is_file() and path.name != "README.md"
        for placeholder in _PLACEHOLDER.findall(path.read_text(encoding="utf-8"))
    }
    assert shipped, "the template ships no placeholders — this test is now vacuous"
    missing = sorted(p for p in shipped if p not in GUIDE_TEXT)
    assert not missing, f"the template ships {', '.join(missing)} and § 2.0 does not name them"


def test_the_guide_does_not_hard_code_a_release_tag() -> None:
    """Which tag is current is the one thing an adopter cannot check and the author never has to.

    § 0.1's fetch named `v0.4.0` while the register pinned the checker at
    `v0.5.0` — internally consistent, one release stale, and unfalsifiable from
    the reader's side. The number has one home, `tools.register-check.install.ref`,
    which is inside the file being fetched; so the guide resolves the tag instead
    of naming it, and this holds it to that.
    """
    pattern = r"raw\.githubusercontent\.com/Eaiger-Ent/ee-standard/([^/\s\"']+)/"
    urls = re.findall(pattern, GUIDE_TEXT)
    assert urls, "§ 0.1 no longer fetches the register — this test is now vacuous"
    hard_coded = sorted({ref for ref in urls if not ref.startswith("$")})
    assert not hard_coded, (
        f"§ 0.1 names {', '.join(hard_coded)} by hand; resolve the tag rather than writing one"
    )


def test_the_guide_installs_the_plugin_from_the_repository_the_register_names() -> None:
    """The published route stays the public one, and is not retyped as a second address.

    Per [ADR 0044](../docs/adr/0044-the-adopter-installs-from-the-public-marketplace.md)
    an adopter obtains the register, the checker and the plugin from one public
    repository, and Phase 6's promotion adds an `ee-skills` copy rather than
    replacing that instruction. The failure this catches is the promotion being
    written into the guide as a substitution — a one-line edit at the moment
    everyone is thinking about the destination rather than about who cannot
    reach it, and one nothing else here would notice, because installing from a
    private marketplace works perfectly for whoever makes the edit.

    Derived from `tools.register-check.install.repository` rather than compared
    against a literal: the address is a thing a fork or an internal mirror
    reasonably differs on (ADR 0032), so the guide must move with the register
    and not with this file.
    """
    install = a_register().tools["register-check"].install
    assert install is not None, "the register no longer says where the checker comes from"
    slug = install.repository.removeprefix("https://github.com/").removesuffix(".git")
    adds = re.findall(r"claude plugin marketplace add (\S+)", GUIDE_TEXT)
    assert adds, "§ 0.0 no longer adds a marketplace — this test is now vacuous"
    wrong = sorted({named for named in adds if named != slug})
    assert not wrong, (
        f"§ 0.0 installs from {', '.join(wrong)}; the register names {slug} (ADR 0044)"
    )
