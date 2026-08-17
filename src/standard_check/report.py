"""Report rendering, ordered by tier then rung."""

from __future__ import annotations

from collections import Counter

from standard_check.register import Control, Register
from standard_check.runner import ControlResult, Verdict

_RUNG_ORDER = {"blocking": 0, "blocking (baselined)": 1, "warn": 2, "advisory": 3}

_MARK = {
    Verdict.PASS: "✓",
    Verdict.FAIL: "✗",
    Verdict.SKIPPED_PREDICATE: "-",
    Verdict.SKIPPED_NO_CREDENTIALS: "-",
    Verdict.UNCLASSIFIED: "?",
}


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
        f"ee-standard conformance report — register v{register.version} "
        f"(contract {register.register_contract})",
        "",
    ]
    tier: int | None = None
    for result in sorted(results, key=_sort_key):
        control = result.control
        assert isinstance(control, Control)
        if control.tier != tier:
            tier = control.tier
            lines.append(f"Tier {tier}")
        lines.append(f"  {control.id:<8} {result.verdict!s:<25} {control.title}")
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
        f"{counts[Verdict.UNCLASSIFIED]} unclassified; "
        f"meta-controls: {meta_passed}/{len(meta_results)} passed",
    ]
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
