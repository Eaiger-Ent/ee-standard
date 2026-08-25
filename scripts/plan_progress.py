#!/usr/bin/env -S uv run python
"""Derived progress view over the build plan's exit criteria.

`docs/04-build-plan.md` is the single source of truth for what "done" means
(CLAUDE.md § Documents). This script computes a view of it and stores nothing:
there is no second copy of the criteria, so there is nothing to drift.

It deliberately reports only what the plan states, and infers no ordering,
gating or priority — the plan says which phase gates which, and re-encoding that
here would be the duplication the register exists to prevent (theme T-2).

Deliberately **not** a `register-check` subcommand: the checker audits any repo
against `controls.yaml`, and a repo being audited has no build plan of ours.
Keeping this in `scripts/` means consumers never ship a command that reads a
file they do not have.

Usage: uv run python scripts/plan_progress.py [--plan PATH]
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

PHASE = re.compile(r"^## Phase (?P<id>\S+) — (?P<title>.+)$")
ITEM = re.compile(r"^- \[(?P<mark>[ x])\] (?P<text>.*)$")
CONTINUATION = re.compile(r"^ {6}(?P<text>\S.*)$")

REOPENED_MARKER = "**re-opened**"
BAR_WIDTH = 20
SUMMARY_WIDTH = 88


@dataclass(frozen=True)
class Criterion:
    """One exit criterion, with its continuation lines joined."""

    text: str
    done: bool

    @property
    def reopened(self) -> bool:
        return REOPENED_MARKER in self.text

    def one_line(self, width: int = SUMMARY_WIDTH) -> str:
        flat = " ".join(self.text.split())
        return flat if len(flat) <= width else flat[: width - 3] + "..."


@dataclass
class Phase:
    id: str
    title: str
    criteria: list[Criterion] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.criteria)

    @property
    def done(self) -> int:
        return sum(1 for c in self.criteria if c.done)

    @property
    def reopened(self) -> int:
        return sum(1 for c in self.criteria if c.reopened)


def parse(text: str) -> list[Phase]:
    """Collect every checkbox criterion, grouped by the phase heading above it."""
    phases: list[Phase] = []
    current: Phase | None = None
    pending: list[str] = []
    pending_done = False
    collecting = False

    def commit() -> None:
        nonlocal collecting
        if collecting and current is not None:
            current.criteria.append(Criterion(" ".join(pending), pending_done))
        collecting = False

    for line in text.splitlines():
        if match := PHASE.match(line):
            commit()
            current = Phase(id=match["id"], title=match["title"].strip())
            phases.append(current)
            continue
        if line.startswith("## "):
            # Any other top-level section ends the current phase.
            commit()
            current = None
            continue
        if current is None:
            continue
        if match := ITEM.match(line):
            commit()
            pending = [match["text"]]
            pending_done = match["mark"] == "x"
            collecting = True
            continue
        if collecting:
            if match := CONTINUATION.match(line):
                pending.append(match["text"])
                continue
            commit()
    commit()
    return phases


def bar(done: int, total: int, width: int = BAR_WIDTH) -> str:
    if total == 0:
        return " " * width
    filled = round(width * done / total)
    return "#" * filled + "-" * (width - filled)


def render(phases: list[Phase], source: Path) -> str:
    scored = [p for p in phases if p.total]
    lines = [f"Build plan progress — {source}", ""]
    if not scored:
        return "\n".join([*lines, "  no exit criteria found", ""])

    labels = {p.id: f"Phase {p.id}" for p in scored}
    label_width = max(len(v) for v in labels.values())
    title_width = max(len(p.title) for p in scored)

    for phase in scored:
        pct = 100 * phase.done // phase.total
        note = f"  ({phase.reopened} re-opened)" if phase.reopened else ""
        lines.append(
            f"  {labels[phase.id]:<{label_width}}  {phase.title:<{title_width}}  "
            f"{phase.done:>2}/{phase.total:<2}  [{bar(phase.done, phase.total)}] "
            f"{pct:>3}%{note}"
        )

    done = sum(p.done for p in scored)
    total = sum(p.total for p in scored)
    lines += ["", f"  {'Total':<{label_width}}  {'':<{title_width}}  {done:>2}/{total:<2}  "
              f"[{bar(done, total)}] {100 * done // total:>3}%"]

    reopened = [(p, c) for p in scored for c in p.criteria if c.reopened]
    if reopened:
        lines += ["", f"Re-opened criteria ({len(reopened)}) — ticked once, no longer met:"]
        lines += [f"  Phase {p.id:<4} {c.one_line()}" for p, c in reopened]

    return "\n".join([*lines, ""])


def main(argv: list[str] | None = None) -> int:
    default = Path(__file__).resolve().parent.parent / "docs" / "04-build-plan.md"
    parser = argparse.ArgumentParser(
        description="Report progress against the build plan's exit criteria."
    )
    parser.add_argument("--plan", type=Path, default=default, help=f"default: {default}")
    args = parser.parse_args(argv)
    plan: Path = args.plan
    try:
        text = plan.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"cannot read the build plan: {exc}", file=sys.stderr)
        return 2
    phases = parse(text)
    # A re-opened criterion that is still ticked is a contradiction in the
    # ledger, and the whole point of recording re-openings is that they are
    # visible — so say so loudly rather than rendering a tidy report over it.
    contradictions = [c for p in phases for c in p.criteria if c.reopened and c.done]
    print(render(phases, plan))
    if contradictions:
        print(
            f"error: {len(contradictions)} criterion/criteria marked re-opened while "
            "still ticked:",
            file=sys.stderr,
        )
        for criterion in contradictions:
            print(f"  {criterion.one_line()}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
