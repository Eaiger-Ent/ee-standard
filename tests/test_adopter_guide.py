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
