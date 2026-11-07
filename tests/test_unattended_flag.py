"""`--yes` answers the proceed question, and may never answer the others.

An adoption is re-run — after a failure, after a token arrives, after a control
is added — and each re-run asked the same two questions and got the same two
answers. A confirmation always answered the same way is not consent; it is a
keystroke, and it teaches the reader to press through the questions that do
matter.

So `--yes` exists, and the whole of its value depends on what it refuses to
answer. `gate-repo`'s calls change what everyone with access can push, and are
in force the moment they return. A takeover question rewrites a file a person
wrote by hand. A removal deletes on the skill's guess. None of those is
"proceed", and none may be suppressed.

`tests/test_gate_repo_confirmation.py` holds the shape of gate-repo's questions.
This file holds the boundary around them.
"""

from __future__ import annotations

import re

import pytest

from conftest import REPO_ROOT

PLUGINS = REPO_ROOT / "plugins"
SKILLS = PLUGINS / "control-register" / "skills"
REFERENCE = REPO_ROOT / "plugins" / "control-register" / "reference" / "unattended.md"

#: The skills a person re-runs, and the only ones that may take the flag.
_ACCEPTS = ("register-adopt", "register-install")

#: Every other skill in the plugin. A gate that grows the flag is the defect
#: this file exists to catch: none of a gate's questions is a proceed question.
_REFUSES = (
    "gate-build",
    "gate-iac",
    "gate-quality",
    "gate-repo",
    "gate-secrets",
    "gate-supply-chain",
    "register-variance",
    # Not a gate, and held to the same rule for a sharper reason: the only
    # question `craft-install` asks is the consent. A flag that answered it
    # would be a flag that installs a rule selection nobody looked at, into the
    # configuration a merge gate reads.
    "craft-install",
)


def _skill(name: str) -> str:
    for plugin in sorted(PLUGINS.iterdir()):
        candidate = plugin / "skills" / name / "SKILL.md"
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8")
    raise AssertionError(f"{name} is in no plugin")


def test_the_shared_rule_has_one_home() -> None:
    """ADR 0036: prose several skills must follow is shipped once."""
    assert REFERENCE.is_file(), f"{REFERENCE.relative_to(REPO_ROOT)} is missing"


@pytest.mark.parametrize("name", _ACCEPTS)
def test_a_rerun_skill_declares_the_flag_and_reads_the_rule(name: str) -> None:
    text = _skill(name)

    hint = re.search(r"^argument-hint: \"(.*)\"$", text, re.M)
    assert hint is not None, f"{name} has no argument-hint"
    assert "--yes" in hint.group(1), (
        f"{name} accepts --yes but its argument-hint does not offer it, so the "
        "one place a user sees the flag never mentions it."
    )

    assert "reference/unattended.md" in text, (
        f"{name} implements --yes without reading the shared rule. The rule is what "
        "says which questions it may not answer, and a copy of that in each skill "
        "is what ADR 0036 exists to prevent."
    )


@pytest.mark.parametrize("name", _REFUSES)
def test_no_gate_takes_the_flag(name: str) -> None:
    """A gate's questions are takeover, removal and platform state — never proceed."""
    text = _skill(name)
    assert "--yes" not in text, (
        f"{name} mentions --yes. No question a gate asks is a proceed question: it "
        "asks before taking over a file it did not write, before removing anything, "
        "and — in gate-repo — before every call that changes platform state. A flag "
        "that answers one of those is a defect, not a convenience."
    )


def test_the_rule_names_what_the_flag_may_not_answer() -> None:
    """The reference is only worth reading if it draws the line explicitly."""
    rule = REFERENCE.read_text(encoding="utf-8")
    for required in ("gate-repo", "Adopt and stamp", "Remove"):
        assert required in rule, (
            f"the shared rule does not mention {required!r}, so a skill following it "
            "would not know that question is excluded."
        )


def test_the_front_door_does_not_pass_the_flag_to_the_gates() -> None:
    """`register-adopt` passes `--repo` and `--register` to every gate. Not this."""
    # Prose wraps, so compare on collapsed whitespace rather than on a line.
    text = " ".join(_skill("register-adopt").split())
    assert "The gates never receive it" in text, (
        "register-adopt passes --repo and --register through to every gate, so it "
        "must say plainly that --yes is not passed with them. Without that sentence "
        "the natural reading is that every flag travels together."
    )


# --- ADR 0062: the gates take --plan and --answers instead -------------------

_GATES = tuple(n for n in _REFUSES if n.startswith("gate-"))
_PRE_ANSWERED = REPO_ROOT / "plugins" / "control-register" / "reference" / "pre-answered.md"


@pytest.mark.parametrize("name", _GATES)
def test_every_gate_offers_plan_and_answers(name: str) -> None:
    """register-adopt can only list a gate's questions if the gate can report
    them, and can only pass the answers back if the gate reads them."""
    text = _skill(name)
    hint = re.search(r"^argument-hint: \"(.*)\"$", text, re.M)
    assert hint is not None
    assert "--plan" in hint.group(1) and "--answers <path>" in hint.group(1), name
    assert "reference/pre-answered.md" in text, (
        f"{name} takes --plan and --answers without reading the rule that says "
        "what they mean, which is the copy ADR 0036 exists to prevent"
    )


@pytest.mark.parametrize("name", _GATES)
def test_every_takeover_and_removal_question_says_it_is_answerable(name: str) -> None:
    """A question site with no marker is one the plan will never list, so the
    adopter is asked it mid-run: the state ADR 0062 was written to end."""
    text = _skill(name)
    for options, kind in (
        ("Adopt and stamp / Leave and abort", "takeover"),
        ("Remove / Keep", "removal"),
    ):
        for match in re.finditer(re.escape(options), text):
            window = text[max(0, match.start() - 400) : match.end() + 400]
            assert f"*Answerable from the plan: `{kind}`" in window, (
                f"{name}: a {kind} question is not marked answerable from the plan"
            )


def test_the_plan_rule_keeps_the_unlisted_question() -> None:
    """The one sentence the whole rule depends on."""
    rule = " ".join(_PRE_ANSWERED.read_text(encoding="utf-8").split())
    assert "A question the plan did not show is still asked." in rule
    assert "An entry is never stretched." in rule
    assert "`body_sha256`" in rule


def test_yes_never_answers_a_plan_with_a_platform_call() -> None:
    rule = " ".join(REFERENCE.read_text(encoding="utf-8").split())
    assert "`--yes` does not answer a plan that lists one of these calls" in rule
    adopt = " ".join(_skill("register-adopt").split())
    assert "With `--yes` and a plan that lists a platform call:** ask anyway" in adopt
