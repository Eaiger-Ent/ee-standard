"""The marketplace's own preflight, run over every skill in the plugin.

P1-P11 belong to `ee-skills` and the script that implements them ships there,
so this repository must not reimplement them — a local copy of the 250-character
ceiling would be a second source of truth for someone else's rule, free to drift
from the one a submission is actually judged against. What is checked here is
that the marketplace's script, when this machine has it, returns no `FAIL`.

The gap this closes is small and had already opened: SUP-004 landed on
2026-08-27 and grew `gate-supply-chain`'s description to 285 characters against
a ceiling of 250, which nothing here noticed, because the promotion plan's
answer was "re-run preflight before submitting", and since 2026-08-28 the
marketplace's own gates run on the submission branch **before** it is pushed —
so a `FAIL` here is not something a reviewer asks about, it is a submission that
is never filed.

**Absence is a state, not a pass** — the same shape ADR 0043 gives the plugin
inventory. CI has no marketplace checkout, so there the test skips and says so.
It answers in the container where skills are edited, and `git push` runs the
suite (ADR 0039), which is the locus that matters for this one.

`Path.home()` is read directly rather than through `$CLAUDE_CONFIG_DIR`:
`conftest.py` redirects that variable autouse so no test reaches the real
inventory by accident, and this test is about the machine's installed
marketplace rather than about anything the checker resolves.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from conftest import REPO_ROOT

SKILLS = sorted(p for p in (REPO_ROOT / "plugins/control-register/skills").iterdir() if p.is_dir())

# Nine byte-identical copies ship, one per plugin that needs it; any is the
# script. See docs/05-promotion.md § Corrections to CONTRIBUTING.md.
_SCRIPT_GLOB = "plugins/*/skills/skill-scripts/scripts/preflight-check.sh"


def _preflight_script() -> Path | None:
    marketplaces = Path.home() / ".claude" / "plugins" / "marketplaces"
    if not marketplaces.is_dir():
        return None
    found = sorted(marketplaces.glob(f"*/{_SCRIPT_GLOB}"))
    return found[0] if found else None


@pytest.mark.parametrize("skill", SKILLS, ids=lambda p: p.name)
def test_the_marketplace_preflight_finds_nothing_to_fail(skill: Path) -> None:
    script = _preflight_script()
    if script is None:
        pytest.skip("no marketplace checkout on this machine; preflight is ee-skills' script")
    done = subprocess.run(
        ["bash", str(script), str(skill)],
        capture_output=True,
        text=True,
        check=False,
    )
    report = json.loads(done.stdout)
    # WARN is not a failure and one is expected: six gates carry side-effect
    # verbs without `disable-model-invocation`, which ADR 0035 decided
    # deliberately, so failing on WARN would fail the build over a ratified
    # decision.
    failed = {
        name: check
        for name, check in report["checks"].items()
        if check.get("status") == "FAIL"
    }
    assert report["overall"] != "FAIL", f"{skill.name}: {failed}"
