"""CLAUDE.md instructs from decisions that are still in force, and stays reviewable.

CLAUDE.md is loaded into every session, so two things are true of it that are
true of no other document here: an error in it is acted on rather than read, and
every byte of it is paid for on every invocation.

**The first-order risk is not size, it is staleness.** CLAUDE.md restates around
thirty ADRs — far more than any control does — and a restatement is a second
copy that can drift from the decision it summarises. `tests/test_adr_revisions.py`
already fails a live control whose `rationale_adr` cites an archived ADR,
*"because a control's stated reasoning may not be a decision the corpus has
retired"*. That argument applies verbatim to the file the agent reads first, and
was not applied to it: an ADR could be superseded and moved to `docs/adr/archive/`
while CLAUDE.md went on teaching the retired decision, with nothing failing.

**The second-order risk is size**, and it is deliberately a *review trigger*
rather than a quality bar. The skill-preflight precedent cuts both ways: P1's
line ceiling found that `gate-quality` had two sections pasted into every skill
it governed, and the fix was ADR 0036 rather than trimming the longest file — a
ceiling can find real duplication. But a SKILL.md is an artefact and CLAUDE.md is
the agent's operating context, so a cap tight enough to force cutting operational
detail makes the agent worse at the job. The threshold below is set well above
today's size: it is there to prompt somebody to look, not to hold a line.

What does **not** belong in CLAUDE.md is a fact that changes no behaviour. The
test to apply when adding one: *if this number were different, would an agent do
anything differently?* A count of the ADRs on disk failed that test, was carried
for months, and rotted — which is how it was noticed.
"""

from __future__ import annotations

import re

import pytest

from conftest import REPO_ROOT

CLAUDE_MD = REPO_ROOT / "CLAUDE.md"
ARCHIVE = REPO_ROOT / "docs/adr/archive"

#: An ADR as CLAUDE.md names it. Two forms, because the prune replaced most of
#: the full-path links with bare numbers in a routing table — which is the point
#: of the prune (a pointer, not a restatement) and must not become a way for a
#: citation to escape the check below.
_ADR_LINK = re.compile(r"docs/adr/(\d{4})-[a-z0-9-]+\.md")
_ADR_NUMBER = re.compile(r"\bADRs? ((?:\d{4}(?:,\s*)?)+)")

#: A real ceiling, not a review trigger. The first version of this test set
#: 1,500 — chosen before Anthropic's guidance was read, and calibrated to *do
#: not grow much further* when the file was already 1,038 lines and 87% Exclude-
#: column content. That number certified the anti-pattern as acceptable.
#:
#: 300 is roughly half again over the pruned file, which leaves room for the
#: gotchas and commands this repository keeps discovering without leaving room
#: for a phase history to grow back.
#: `docs/17-adopter-onboarding-review.md` § R has the measurements.
_CEILING_LINES = 300


def _cited_adrs() -> list[str]:
    """Every ADR number CLAUDE.md instructs from, by either spelling."""
    text = CLAUDE_MD.read_text(encoding="utf-8")
    numbers = set(_ADR_LINK.findall(text))
    for group in _ADR_NUMBER.findall(text):
        numbers.update(re.findall(r"\d{4}", group))
    return sorted(numbers)


def test_claude_md_cites_some_adrs() -> None:
    """A regex that matches nothing passes every test below it."""
    found = _cited_adrs()
    assert len(found) >= 15, (
        f"only {len(found)} ADR citations found in CLAUDE.md — either the routing "
        "table has lost most of its rows, or the patterns have gone stale and the "
        "checks below are passing over nothing"
    )


@pytest.mark.parametrize("number", _cited_adrs())
def test_every_adr_claude_md_instructs_from_is_still_in_force(number: str) -> None:
    """A retired decision must not go on being taught as current.

    Archiving rewrites inbound links in the same change (`docs/adr/` § the
    archive rule). CLAUDE.md is the inbound reference most likely to be
    forgotten, because after the prune it cites by number rather than by path —
    a bare `ADR 0031` breaks no link when the file moves.
    """
    if list((REPO_ROOT / "docs/adr").glob(f"{number}-*.md")):
        return
    archived = list(ARCHIVE.glob(f"{number}-*.md"))
    assert not archived, (
        f"CLAUDE.md instructs from ADR {number}, which has been archived. A superseded "
        "or deprecated decision must not stay in the file every session reads first — "
        "rewrite the passage to the decision that replaced it."
    )
    pytest.fail(f"CLAUDE.md cites ADR {number}, which does not exist")


def test_claude_md_stays_short_enough_to_be_read() -> None:
    """A ceiling, because the cost of exceeding it is silent.

    Anthropic's guidance is blunt about the failure mode: *"Bloated CLAUDE.md
    files cause Claude to ignore your actual instructions."* Nothing warns when
    that starts happening, which is why it needs a number rather than a habit.
    """
    lines = len(CLAUDE_MD.read_text(encoding="utf-8").splitlines())
    assert lines <= _CEILING_LINES, (
        f"CLAUDE.md is {lines} lines, over the {_CEILING_LINES}-line ceiling. Ask of "
        "each passage: would removing this cause a session to make a mistake? A "
        "restatement of an ADR is a second copy — cite it instead. A fact that "
        "changes no behaviour does not belong in a file loaded every session. Raise "
        "the ceiling only with a reason recorded beside it."
    )
