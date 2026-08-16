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
    meta_results: list[tuple[str, str, bool, str]],
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
    lines.append("Meta")
    for meta_id, title, passed, message in meta_results:
        verdict = "PASS" if passed else "FAIL"
        lines.append(f"  {meta_id:<8} {verdict:<25} {title}")
        if not passed:
            lines.append(f"           ✗ {message}")
    counts = Counter(result.verdict for result in results)
    meta_failed = sum(1 for m in meta_results if not m[2])
    lines += [
        "",
        "Summary: "
        f"{counts[Verdict.PASS]} passed, "
        f"{counts[Verdict.FAIL]} failed, "
        f"{counts[Verdict.SKIPPED_PREDICATE]} skipped (predicate), "
        f"{counts[Verdict.SKIPPED_NO_CREDENTIALS]} skipped (no credentials), "
        f"{counts[Verdict.UNCLASSIFIED]} unclassified; "
        f"meta-controls: {len(meta_results) - meta_failed}/{len(meta_results)} passed",
    ]
    if counts[Verdict.SKIPPED_NO_CREDENTIALS]:
        lines.append(
            "Note: remote checks were skipped without credentials — this report is "
            "incomplete, not a claim that those controls hold."
        )
    return "\n".join(lines)
