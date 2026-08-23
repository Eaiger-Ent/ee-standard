"""Every ADR declares a revision, and a revision above 1 is accounted for.

[ADR 0025](../docs/adr/0025-an-amendment-is-a-recorded-revision.md) decided
that an amendment to an Accepted ADR is recorded as a numbered revision. Seven
ADRs were already amended when it was written and not one said so in its
header: ADR 0005 carried a byte-identical header to its pre-amendment self
while a paragraph in the middle of § Decision reversed the variance value it
recorded, and ADR 0016 asserted a bound that had not held for six days.

What is checked here is the **form**, and the two halves checking each other:
the declared revision count must equal the rows in § Revision History, and a
count above 1 must be matched by an amendment marker in the body. That makes
the common failure — editing the body and forgetting the record, or the
reverse — a build failure rather than something an audit finds later.

What is deliberately **not** checked:

- Whether a row's summary is *accurate*. Nothing can read the body prose and
  confirm the one-line summary describes it. ADR 0025 § Consequences records
  this as the residual risk rather than implying it is covered.
- Whether the ratifier had authority to ratify. On this repository the author
  and the approver are the same person; the column's worth is that an adopter
  with real separation has somewhere to record it.
- Whether the table agrees with git. Git holds commits, not decisions, and ADR
  0025 § Alternatives Considered rejects git as the record for that reason.

The enforcement lives in a test rather than a register control because the rule
governs a document this repository authors about its own decisions, not a
property of a conformant Equal Experts repository — the same reason
`test_provenance_stamps.py` holds the stamp format. Putting it in
`controls.yaml` would make every adopter inherit an authoring convention, which
ADR 0022 requirement 6 rules out.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from conftest import REPO_ROOT

ADR_DIR = REPO_ROOT / "docs" / "adr"
ARCHIVE_DIR = ADR_DIR / "archive"

# ADR 0026: the two statuses that mean "no longer in force". `Draft` and
# `Proposed` are live work, not history, and stay in the active directory.
TERMINAL = {"Superseded", "Deprecated"}

REVISION = re.compile(r"^\*\*Revision:\*\* (\d+)$", re.M)
STATUS = re.compile(r"^\*\*Status:\*\* (\w+)$", re.M)
DATE = re.compile(r"^\*\*Date:\*\* (\d{4}-\d{2}-\d{2})$", re.M)
SUPERSEDED_BY = re.compile(r"^\*\*Superseded by:\*\* \S", re.M)
ROW = re.compile(r"^\| (\d+) \| (\d{4}-\d{2}-\d{2}) \| (.+?) \| (.+?) \|$", re.M)
# Anchored to the heading, not a substring: ADR 0025 names the section in its
# own prose, and a loose `in` matched that mention.
HISTORY_HEADING = re.compile(r"^## Revision History$", re.M)

# The four spellings the seven pre-0025 amendments used, plus the one ADR 0025
# settles on. A revision above 1 must be visible in the body under one of them.
AMENDMENT_MARKER = re.compile(
    r"\*\*(Amended|Extended)\b|^#{2,3} Applied\b|^Ratified on \d{4}-\d{2}-\d{2}", re.M
)


def adr_files() -> list[Path]:
    """Both directories. An archived ADR is frozen, not exempt: it still has to
    declare a revision, and it is the one kind of ADR that must name a
    replacement."""
    return sorted(
        [*ADR_DIR.glob("[0-9][0-9][0-9][0-9]-*.md"), *ARCHIVE_DIR.glob("[0-9][0-9][0-9][0-9]-*.md")]
    )


def _ids(paths: list[Path]) -> list[str]:
    return [("archive/" if p.parent.name == "archive" else "") + p.name[:4] for p in paths]


ADRS = adr_files()


def test_the_corpus_was_found() -> None:
    """A glob that matches nothing would pass every test below vacuously."""
    assert len(ADRS) >= 25, f"found only {len(ADRS)} ADRs in {ADR_DIR}"


@pytest.mark.parametrize("adr", ADRS, ids=_ids(ADRS))
def test_every_adr_declares_a_revision(adr: Path) -> None:
    """`**Revision:** 1` is a positive assertion, not padding.

    An absent field is ambiguous between "never amended" and "amended by
    someone who did not know the convention", and reading an absence as an
    answer is the failure ADR 0021 was written about.
    """
    match = REVISION.search(adr.read_text())
    assert match is not None, (
        f"{adr.name} has no `**Revision:**` header field. Add `**Revision:** 1` "
        "below `**Date:**` if it has never been amended (ADR 0025 § Decision)."
    )
    assert int(match.group(1)) >= 1, f"{adr.name} declares revision 0"


@pytest.mark.parametrize("adr", ADRS, ids=_ids(ADRS))
def test_revision_count_matches_the_history_table(adr: Path) -> None:
    """The count and the table check each other; neither is trusted alone."""
    text = adr.read_text()
    revision = int(REVISION.search(text).group(1))  # type: ignore[union-attr]
    has_table = HISTORY_HEADING.search(text) is not None

    if revision == 1:
        assert not has_table, (
            f"{adr.name} declares revision 1 but carries a § Revision History. "
            "Where there is no history the header already says everything the "
            "table would (ADR 0025 § The history table appears only where "
            "there is history)."
        )
        return

    assert has_table, (
        f"{adr.name} declares revision {revision} but has no § Revision "
        "History. An amendment must say what it changed and who ratified it."
    )
    rows = ROW.findall(HISTORY_HEADING.split(text, 1)[1])
    assert len(rows) == revision, (
        f"{adr.name} declares revision {revision} but § Revision History has "
        f"{len(rows)} rows. Editing one without the other is the failure this "
        "check exists to catch."
    )
    assert [int(r[0]) for r in rows] == list(range(1, revision + 1)), (
        f"{adr.name}: revision numbers must run 1..{revision} in order, "
        f"got {[r[0] for r in rows]}"
    )
    dates = [r[1] for r in rows]
    assert dates == sorted(dates), f"{adr.name}: revision dates go backwards: {dates}"
    assert dates[0] == DATE.search(text).group(1), (  # type: ignore[union-attr]
        f"{adr.name}: revision 1 is dated {dates[0]} but `**Date:**` says "
        f"{DATE.search(text).group(1)}. Revision 1 is the original decision."  # type: ignore[union-attr]
    )
    for number, _, summary, ratifier in rows:
        assert len(summary.strip()) >= 20, (
            f"{adr.name} revision {number}: the summary is too short to be one. "
            "A reader must learn what changed without opening the diff."
        )
        assert ratifier.strip() and ratifier.strip() != "-", (
            f"{adr.name} revision {number}: no ratifier. An in-place edit to an "
            "Accepted decision is a governance act, not a typo fix."
        )


@pytest.mark.parametrize("adr", ADRS, ids=_ids(ADRS))
def test_an_amended_adr_carries_the_amendment_in_its_body(adr: Path) -> None:
    """A table claiming an amendment the body does not make is a worse lie
    than no table, because it is the half a reader trusts."""
    text = adr.read_text()
    revision = int(REVISION.search(text).group(1))  # type: ignore[union-attr]
    if revision == 1:
        return
    body = HISTORY_HEADING.split(text, 1)[0]
    assert AMENDMENT_MARKER.search(body), (
        f"{adr.name} declares revision {revision} but its body carries no "
        "amendment. The revision history summarises changes made in the ADR; "
        "it does not replace them."
    )


@pytest.mark.parametrize("adr", ADRS, ids=_ids(ADRS))
def test_a_superseded_adr_names_its_replacement(adr: Path) -> None:
    """ADR 0015 was Superseded for six days with the replacement named only in
    prose, which `/adr-consistency` reported as its one CRITICAL finding."""
    text = adr.read_text()
    status = STATUS.search(text)
    assert status is not None, f"{adr.name} has no `**Status:**` field"
    assert status.group(1) in {
        "Draft",
        "Proposed",
        "Accepted",
        "Superseded",
        "Deprecated",
    }, f"{adr.name} has status {status.group(1)!r}, which is not in the enum"
    if status.group(1) == "Superseded":
        assert SUPERSEDED_BY.search(text), (
            f"{adr.name} is Superseded but names no `**Superseded by:**`. "
            "A replacement in prose is not a field a reader can find."
        )


@pytest.mark.parametrize("adr", ADRS, ids=_ids(ADRS))
def test_status_and_location_agree(adr: Path) -> None:
    """Checked in both directions, which is what makes the archive safe.

    ADR 0026 § Alternatives Considered concedes Option 1's objection: a
    directory that says "not active" is a second encoding of what
    `**Status:**` already says, and two encodings of one fact drift. They
    cannot drift if neither is trusted alone.
    """
    status = STATUS.search(adr.read_text()).group(1)  # type: ignore[union-attr]
    archived = adr.parent.name == "archive"

    if status in TERMINAL:
        assert archived, (
            f"{adr.name} is {status} but sits in the active directory. Move it "
            f"to docs/adr/archive/ (ADR 0026). It keeps its number."
        )
    else:
        assert not archived, (
            f"{adr.name} is {status} but sits in docs/adr/archive/, which holds "
            f"only {' and '.join(sorted(TERMINAL))} ADRs. An ADR still in force "
            "belongs in the active directory."
        )


@pytest.mark.parametrize("adr", ADRS, ids=_ids(ADRS))
def test_a_replacement_reference_resolves(adr: Path) -> None:
    """A `**Superseded by:**` naming a file that is not there is worse than
    none: it reads as an answer. Archiving rewrites paths, so this is the
    check most likely to catch a botched move."""
    text = adr.read_text()
    match = re.search(r"^\*\*Superseded by:\*\* \[[^\]]+\]\(([^)]+)\)", text, re.M)
    if match is None:
        return
    target = (adr.parent / match.group(1)).resolve()
    assert target.is_file(), (
        f"{adr.name} is superseded by {match.group(1)}, which does not resolve "
        f"from {adr.parent}. Archiving moves files; it does not move links."
    )


def test_no_live_control_cites_an_archived_adr() -> None:
    """A control's stated reasoning may not be a decision the corpus has
    marked as no longer current.

    The schema already requires `rationale_adr` to resolve, so archiving one
    fails as "file does not exist". That diagnoses the symptom; ADR 0026
    § A live control's `rationale_adr` names the rule.
    """
    import yaml

    register = yaml.safe_load((REPO_ROOT / "controls.yaml").read_text())
    archived = {p.name for p in ARCHIVE_DIR.glob("*.md")}
    offenders = [
        (control["id"], control["rationale_adr"])
        for control in register["controls"]
        if Path(control["rationale_adr"]).name in archived
        or "/archive/" in control["rationale_adr"]
    ]
    assert not offenders, (
        "these controls cite an archived ADR as their reasoning: "
        + ", ".join(f"{cid} -> {path}" for cid, path in offenders)
        + ". Repoint rationale_adr at the superseding ADR in the same change."
    )
