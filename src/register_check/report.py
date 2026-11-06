"""Report rendering, ordered by tier then rung."""

from __future__ import annotations

from collections import Counter

from register_check.register import Control, Register
from register_check.runner import ControlResult, Verdict, sets_exit_code

_RUNG_ORDER = {"blocking": 0, "blocking (baselined)": 1, "warn": 2, "advisory": 3}

_MARK = {
    Verdict.PASS: "✓",
    Verdict.FAIL: "✗",
    Verdict.SKIPPED_PREDICATE: "-",
    Verdict.SKIPPED_NO_CREDENTIALS: "-",
    Verdict.UNCLASSIFIED: "?",
    # Distinct from `?` on purpose: unreadable is *we could not tell*, and
    # this is *we know, and the plan does not sell it* (ADR 0047).
    Verdict.UNAVAILABLE_PLAN: "⊘",
}


#: Verdicts a control below `blocking` can return without being called out.
_HELD = (Verdict.PASS, Verdict.SKIPPED_PREDICATE)


def _rung(result: ControlResult) -> str:
    control = result.control
    assert isinstance(control, Control)
    return control.rung


def _control_lines(result: ControlResult) -> list[str]:
    control = result.control
    assert isinstance(control, Control)
    # A rung that sets no exit code is named on the line, so a FAIL beside it
    # is not read as one that failed the build.
    rung = "" if sets_exit_code(control) else f" [{control.rung}]"
    lines = [f"  {control.id:<8} {result.verdict!s:<25} {control.title}{rung}"]
    if result.verdict is Verdict.SKIPPED_PREDICATE:
        lines.append(f"           - {result.note}")
    elif result.verdict is not Verdict.PASS:
        lines.extend(
            f"           {_MARK[block.verdict]} {block.block.describe()} — {block.message}"
            for block in result.blocks
        )
    # ADR 0017: a verdict that does not cover everything the control claims
    # says so, whatever the verdict was. Printed even for PASS — especially
    # for PASS, since that is the verdict a partial block would otherwise
    # let overstate its evidence.
    lines.extend(
        f"           partial: {block.block.partial.unverified} "
        f"(expires {block.block.partial.expires.isoformat()})"
        for block in result.blocks
        if block.block.partial is not None
    )
    return lines


def _sort_key(result: ControlResult) -> tuple[int, int, str]:
    control = result.control
    assert isinstance(control, Control)
    return (control.tier, _RUNG_ORDER.get(control.rung, 9), control.id)


def render(
    register: Register,
    results: list[ControlResult],
    meta_results: list[tuple[str, str, Verdict, str]],
) -> str:
    lines = [
        f"control register conformance report — register v{register.version} "
        f"(contract {register.register_contract})",
        "",
    ]
    ordered = sorted(results, key=_sort_key)
    # ADR 0061: a `warn` control sets no exit code, so the report is the only
    # place it is surfaced. It goes first, before the results a reader scans
    # for what failed the build, under a heading that says it did not.
    warned = [r for r in ordered if _rung(r) == "warn"]
    if warned:
        lines.append("Warn — reported, does not set the exit code")
        for result in warned:
            lines.extend(_control_lines(result))
    tier: int | None = None
    for result in ordered:
        if _rung(result) == "warn":
            continue
        control = result.control
        assert isinstance(control, Control)
        if control.tier != tier:
            tier = control.tier
            lines.append(f"Tier {tier}")
        lines.extend(_control_lines(result))
    # A narrowed run (`--control`) audits one deployment, not the register, so
    # it carries no meta-controls. Printing an empty heading over nothing would
    # read as three meta-controls that passed silently.
    if meta_results:
        lines.append("Meta")
    meta_by_id = {meta.id: meta for meta in register.meta_controls}
    for meta_id, title, verdict, message in meta_results:
        lines.append(f"  {meta_id:<8} {verdict!s:<25} {title}")
        if verdict is not Verdict.PASS:
            lines.append(f"           {_MARK[verdict]} {message}")
        lines.extend(
            f"           partial: {block.partial.unverified} "
            f"(expires {block.partial.expires.isoformat()})"
            for block in meta_by_id[meta_id].verify
            if block.partial is not None
        )
    # Counts stay control-only so "N passed" keeps meaning what it always has;
    # meta-controls have their own line. The notes below read both, because a
    # meta-control that could not be verified makes the report incomplete too.
    counts = Counter(result.verdict for result in results)
    meta_passed = sum(1 for meta in meta_results if meta[2] is Verdict.PASS)
    all_verdicts = [result.verdict for result in results] + [meta[2] for meta in meta_results]
    lines += [
        "",
        "Summary: "
        f"{counts[Verdict.PASS]} passed, "
        f"{counts[Verdict.FAIL]} failed, "
        f"{counts[Verdict.SKIPPED_PREDICATE]} skipped (predicate), "
        f"{counts[Verdict.SKIPPED_NO_CREDENTIALS]} skipped (no credentials), "
        f"{counts[Verdict.UNCLASSIFIED]} unclassified, "
        # Printed even when zero, unlike a footnote. A repository running
        # with a recorded plan limit should see it in the same line it
        # reads for everything else (ADR 0047 rule 5).
        f"{counts[Verdict.UNAVAILABLE_PLAN]} unavailable (plan); "
        f"meta-controls: {meta_passed}/{len(meta_results)} passed",
    ]
    # The counts above include controls below `blocking`, so a run can exit 0
    # with "1 failed" in it. This line says which failures those are.
    unheld = [r for r in results if not sets_exit_code(r.control) and r.verdict not in _HELD]
    if unheld:
        lines.append(
            f"Below blocking: {len(unheld)} did not hold "
            f"({', '.join(r.control.id for r in unheld)}) — reported, not counted "
            "in the exit code (ADR 0061)."
        )
    # Two different reasons a run gathered no evidence, reported separately
    # because they are fixed differently: one needs credentials, the other needs
    # the tool installed. Neither is a claim that the control holds (ADR 0016).
    if Verdict.SKIPPED_NO_CREDENTIALS in all_verdicts:
        lines.append(
            "Note: remote checks were skipped without credentials — this report is "
            "incomplete, not a claim that those controls hold."
        )
    if Verdict.UNCLASSIFIED in all_verdicts:
        lines.append(
            "Note: some controls could not be verified — this report is incomplete, "
            "not a claim that those controls hold."
        )
    return "\n".join(lines)
