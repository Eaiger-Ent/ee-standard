"""`gate-repo` confirms before **every** remote mutation, not before the first one.

The Phase 3 criterion this file closes is one word wider than the test that
already stood in `test_gate_repo_deploy.py`. That one holds the wording of the
question before `POST /rulesets`. This one holds the property that the question
exists *for each call*, which is a different thing: a gate that asks once and
then makes three calls has an approval for one of them and an assumption about
the other two.

Two of the three reduce protection rather than adding it. A `PUT` replaces a
ruleset entire, so anything the live one carries and the record does not is
dropped by the call; a `DELETE` takes classic branch protection away. Neither is
covered by an answer given about creating a ruleset, and both were reachable
from the skill before this file existed — the `PUT` named in one line of prose
inside the create question's own step, the `DELETE` not written down at all.

**No test can prove a model asks first.** What is machine-checkable is the shape
of the instruction it follows, and this file checks it structurally rather than
by phrase: it enumerates every call in the skill that uses a method other than
`GET`, and requires each one to be preceded by its own question and to appear in
the skill's own table of them. A fourth mutation added later fails here until it
has both — which is the point, because the failure mode is not a wrong
confirmation but a missing one, and a missing one is invisible in a diff that
adds a plausible-looking `gh api` line.
"""

from __future__ import annotations

import re

import pytest

from conftest import REPO_ROOT

SKILL = REPO_ROOT / "plugins/control-register/skills/gate-repo"
SKILL_TEXT = (SKILL / "SKILL.md").read_text(encoding="utf-8")

# The section that must list every mutating call. Named here because the test
# fails if a call exists outside it, and the message has to say where to add it.
TABLE_HEADING = "## Every call that changes platform state, and what confirms it"

_FENCE = re.compile(r"```bash\n(.*?)```", re.DOTALL)
_METHOD = re.compile(r"gh api\s+(?:--method|-X)\s+([A-Z]+)\s+\"([^\"]+)\"")
_ANY_GH_API = re.compile(r"gh api\b[^\n|]*")
_TABLE_ROW = re.compile(r"^\| `([A-Z]+) (/\S+)` \|", re.MULTILINE)

#: `$OWNER` in a command and `{owner}` in the table are the same repository.
_PLACEHOLDERS = {
    "$OWNER": "{owner}",
    "$NAME": "{name}",
    "$ID": "{id}",
    "$DEFAULT": "{branch}",
}


def _normalise(path: str) -> str:
    """One spelling for a route written as a shell string and as documentation."""
    for shell, documented in _PLACEHOLDERS.items():
        path = path.replace(shell, documented)
    return "/" + path.lstrip("/")


def _mutations() -> list[tuple[int, str, str]]:
    """Every non-`GET` call in the skill's fenced blocks, with where it appears.

    The offset is what makes "its own question" checkable: a confirmation counts
    for a call only if it stands between that call and the one before it.
    """
    found = []
    for fence in _FENCE.finditer(SKILL_TEXT):
        for call in _METHOD.finditer(fence.group(1)):
            found.append(
                (fence.start() + call.start(), call.group(1), _normalise(call.group(2)))
            )
    return sorted(found)


def _documented() -> list[tuple[str, str]]:
    section = SKILL_TEXT.split(TABLE_HEADING, 1)[1]
    return [(m.group(1), m.group(2)) for m in _TABLE_ROW.finditer(section.split("\n## ", 1)[0])]


def test_the_skill_lists_every_call_that_changes_platform_state() -> None:
    """The table and the commands are the same set, checked both ways.

    A row with no call is a promise the skill does not keep; a call with no row
    is an effect the reader was never told about. Neither direction is the more
    likely mistake, so neither is the one to check.
    """
    assert TABLE_HEADING in SKILL_TEXT, "the skill must enumerate its own mutations"
    called = {(method, path) for _, method, path in _mutations()}
    documented = set(_documented())
    assert called == documented, (
        f"only in the commands: {sorted(called - documented)}; "
        f"only in the table: {sorted(documented - called)}"
    )
    assert len(called) == 3, called


def test_no_call_slips_past_the_table_by_omitting_its_method() -> None:
    """`gh api` with a body and no `--method` is a POST, and reads like a GET.

    This is the way a mutation gets added without anyone meaning to: `--input`
    or `-f` on a call that names no method makes `gh` POST it. The enumeration
    above would not see it, so it is checked separately rather than trusted to
    the same regex.
    """
    for fence in _FENCE.finditer(SKILL_TEXT):
        for call in _ANY_GH_API.finditer(fence.group(1)):
            text = call.group(0)
            if _METHOD.search(text):
                continue
            assert "--input" not in text and not re.search(r"\s-f\s|--field", text), (
                f"this call sends a body with no method, so `gh` POSTs it: {text.strip()}"
            )


def test_each_mutation_has_a_question_of_its_own_before_it() -> None:
    """The criterion, structurally: a confirmation between each call and the last.

    "Before it" is not enough on its own — one question at the top of the file
    is before all three. What is required is a question in the span since the
    previous mutation, so that approving one call cannot stand in for the next.
    """
    mutations = _mutations()
    assert mutations, "no mutating call found — the regex, not the skill, is what changed"
    start = SKILL_TEXT.index(TABLE_HEADING)
    for offset, method, path in mutations:
        span = SKILL_TEXT[start:offset]
        question = [line for line in span.splitlines() if line.startswith(">") and "?" in line]
        assert question, f"{method} {path} has no question of its own since the call before it"
        assert "Options:" in span or "**On " in span, (
            f"{method} {path} has a question with no answers offered"
        )
        start = offset


@pytest.mark.parametrize(
    ("phrase", "why"),
    [
        (
            "This creates an active ruleset on",
            "the create question names what comes into force",
        ),
        (
            "This replaces ruleset",
            "the update question names the ruleset it overwrites",
        ),
        (
            "A `PUT` replaces the ruleset entire",
            "the update question says the call can drop what it does not carry",
        ),
        (
            "If the diff is empty, ask anyway",
            "a call whose effect is invisible is not one to make silently",
        ),
        (
            "This removes classic branch protection from",
            "the delete question names what stops being required",
        ),
        (
            "It affects every collaborator, not only you",
            "the blast radius is other people, and is stated as such",
        ),
    ],
)
def test_each_question_names_its_own_blast_radius(phrase: str, why: str) -> None:
    """Structure is not enough: three questions with one wording is one question.

    Each of these is the sentence that makes its own call recognisable to the
    person answering. A confirmation that describes a different call than the
    one about to be made is worse than none, because it is answered.
    """
    assert phrase in " ".join(SKILL_TEXT.split()), why


def test_no_confirmation_is_waivable_by_an_earlier_approval() -> None:
    """Including `register-adopt`'s plan.

    That is the approval most likely to be read as covering these, because it is
    the one a person actually gave a few minutes earlier.
    """
    text = " ".join(SKILL_TEXT.split())
    assert "No confirmation here is waivable by an earlier approval" in text
    assert "never ask them as one question with one answer" in text
    adopt = " ".join(
        (REPO_ROOT / "plugins/control-register/skills/register-adopt/SKILL.md").read_text(
            encoding="utf-8"
        ).split()
    )
    assert "This confirmation does not cover `gate-repo`" in adopt
    assert "once for each call that changes platform state, not once for the gate" in adopt


def test_the_delete_is_asked_after_the_ruleset_is_known_active() -> None:
    """Removing the classic rule before the ruleset is enforcing is an unprotected window.

    The union of a classic rule and a ruleset is what is enforced, so the delete
    is only safe once the ruleset is confirmed active — which is a read, and the
    reason the question sits in a later step rather than beside Step 2's.
    """
    text = " ".join(SKILL_TEXT.split())
    assert "Do not remove it in the same breath as creating the ruleset" in text
    assert "confirm the ruleset is active first" in text
    delete = next(o for o, method, _ in _mutations() if method == "DELETE")
    apply_calls = [o for o, method, _ in _mutations() if method in {"POST", "PUT"}]
    assert all(o < delete for o in apply_calls), "the delete must come after both apply calls"
