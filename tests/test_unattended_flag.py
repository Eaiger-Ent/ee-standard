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

SKILLS = REPO_ROOT / "plugins" / "control-register" / "skills"
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
)


def _skill(name: str) -> str:
    return (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")


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
