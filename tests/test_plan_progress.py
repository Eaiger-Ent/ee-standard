"""The derived build-plan progress view.

Exact-parse behaviour is asserted against a synthetic plan; the real plan is
checked only for invariants, so ticking a criterion never breaks a test.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import plan_progress  # noqa: E402  — path is set above

SYNTHETIC = """\
# Build plan

## Phase 0 — The register

### Exit criteria — phase 0

- [x] A done criterion
- [x] A done criterion whose text
      continues on a second line

## Phase 1 — The checker

Prose that mentions nothing.

- [ ] An open criterion
- [ ] An open criterion that was **re-opened** with a reason
      spread over two lines

## What is deliberately not in scope

| Excluded | Why |
| --- | --- |
| Something | Because |
"""


def test_parses_phases_and_marks() -> None:
    phases = plan_progress.parse(SYNTHETIC)
    assert [p.id for p in phases] == ["0", "1"]
    assert phases[0].title == "The register"
    assert (phases[0].done, phases[0].total) == (2, 2)
    assert (phases[1].done, phases[1].total) == (0, 2)


def test_joins_continuation_lines() -> None:
    phases = plan_progress.parse(SYNTHETIC)
    assert phases[0].criteria[1].text == "A done criterion whose text continues on a second line"


def test_detects_reopened() -> None:
    phases = plan_progress.parse(SYNTHETIC)
    assert phases[1].reopened == 1
    assert phases[1].criteria[1].reopened
    assert not phases[1].criteria[0].reopened


def test_non_phase_section_ends_collection() -> None:
    # The "not in scope" table must not be swept into Phase 1.
    phases = plan_progress.parse(SYNTHETIC)
    assert sum(p.total for p in phases) == 4


def test_one_line_truncates() -> None:
    long = plan_progress.Criterion(text="x" * 200, done=False)
    assert len(long.one_line(width=40)) == 40
    assert long.one_line(width=40).endswith("...")


def test_bar_is_full_when_complete() -> None:
    assert plan_progress.bar(3, 3, width=6) == "######"
    assert plan_progress.bar(0, 3, width=6) == "------"
    assert plan_progress.bar(0, 0, width=6).strip() == ""


def test_render_includes_totals_and_reopened_section() -> None:
    out = plan_progress.render(plan_progress.parse(SYNTHETIC), Path("plan.md"))
    assert "Phase 0" in out
    assert "Total" in out
    assert "Re-opened criteria (1)" in out


def test_real_plan_parses_and_is_self_consistent() -> None:
    plan = REPO_ROOT / "docs" / "04-build-plan.md"
    text = plan.read_text(encoding="utf-8")
    phases = plan_progress.parse(text)
    # Every checkbox line in the file is accounted for by exactly one phase.
    checkboxes = sum(1 for line in text.splitlines() if plan_progress.ITEM.match(line))
    assert sum(p.total for p in phases) == checkboxes
    assert checkboxes > 0
    assert len(phases) >= 9


def test_real_plan_has_no_reopened_and_ticked_criterion() -> None:
    """A re-opened criterion must be unticked — otherwise the ledger lies."""
    plan = REPO_ROOT / "docs" / "04-build-plan.md"
    phases = plan_progress.parse(plan.read_text(encoding="utf-8"))
    contradictions = [c.one_line() for p in phases for c in p.criteria if c.reopened and c.done]
    assert contradictions == []


def test_main_exits_zero_on_the_real_plan(capsys: object) -> None:
    assert plan_progress.main([]) == 0


def test_main_reports_unreadable_plan() -> None:
    assert plan_progress.main(["--plan", str(REPO_ROOT / "does-not-exist.md")]) == 2
