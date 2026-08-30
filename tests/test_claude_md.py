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

#: An ADR path as CLAUDE.md spells it, in a link or in prose.
_ADR_LINK = re.compile(r"docs/adr/(\d{4}-[a-z0-9-]+\.md)")

#: Generous on purpose — see the module docstring. Today's file is ~1,040 lines;
#: this fires when it has grown by roughly half again, which is the point at
#: which somebody should ask what has accumulated rather than the point at which
#: the file is wrong.
_REVIEW_THRESHOLD_LINES = 1500


def _cited_adrs() -> list[str]:
    return sorted(set(_ADR_LINK.findall(CLAUDE_MD.read_text(encoding="utf-8"))))


def test_claude_md_cites_some_adrs() -> None:
    """A regex that matches nothing passes every test below it."""
    assert len(_cited_adrs()) >= 20, (
        f"only {len(_cited_adrs())} ADR citations found in CLAUDE.md — the pattern has "
        "gone stale, and the checks below are passing over nothing"
    )


@pytest.mark.parametrize("name", _cited_adrs())
def test_every_adr_claude_md_instructs_from_is_still_in_force(name: str) -> None:
    """A retired decision must not go on being taught as current.

    Archiving rewrites inbound links in the same change (`docs/adr/` § the
    archive rule). CLAUDE.md is the inbound link most likely to be forgotten,
    because it cites by prose as often as by path.
    """
    live = REPO_ROOT / "docs/adr" / name
    if live.is_file():
        return
    archived = ARCHIVE / name
    assert not archived.is_file(), (
        f"CLAUDE.md instructs from {name}, which has been archived. A superseded or "
        "deprecated decision must not stay in the file every session reads first — "
        "rewrite the passage to the decision that replaced it."
    )
    pytest.fail(f"CLAUDE.md cites docs/adr/{name}, which does not exist")


def test_claude_md_is_still_worth_reading_in_full() -> None:
    """A size review trigger, not a quality bar — see the module docstring."""
    lines = len(CLAUDE_MD.read_text(encoding="utf-8").splitlines())
    assert lines <= _REVIEW_THRESHOLD_LINES, (
        f"CLAUDE.md is {lines} lines, over the {_REVIEW_THRESHOLD_LINES}-line review "
        "threshold. This is a prompt to look at what has accumulated, not a claim that "
        "the file is wrong. Ask of each passage: does an agent act differently for "
        "knowing this? A fact that changes no behaviour — a count, a date with nothing "
        "hanging on it — is the first thing to remove. Raise the threshold "
        "deliberately if the answer is that it all earns its place."
    )
