#!/usr/bin/env -S uv run python
"""Report whether a deployed hook still matches the canonical script it was copied from.

Deployment is a copy, so the deployed file is a snapshot of the skill as it was on the day
it ran. Asking "does the deployed hook mention the linter?" is a test every deployment
passes forever, which means a fix to the canonical script never reaches a repository that
already has a hook (#842). This compares the two files instead.

The one difference a deployment is allowed to carry is the LINT_INVOCATION line, which the
deploying step rewrites with the value the repository configured; it is ignored here.

Shipped byte-identical by more than one skill (#709), so it names no skill, no hook and no
step number — both paths are arguments.

Usage:   python3 <this script> <canonical-script> <deployed-hook>
Prints:  ABSENT — the deployed hook is not there; deploy it
         STALE  — it is there and differs from canonical; redeploy it
         FRESH  — it matches; leave it alone
Exit status is 0 for all three: this reports state, it does not judge it. Exit 2 is a
usage error or an unreadable canonical script.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

INVOCATION_RE = re.compile(r'^LINT_INVOCATION = ".*"$')
PLACEHOLDER = "LINT_INVOCATION = <configured>"


def normalise(text: str) -> list[str]:
    return [
        PLACEHOLDER if INVOCATION_RE.match(line) else line for line in text.splitlines()
    ]


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(
            f"usage: {Path(argv[0]).name} <canonical-script> <deployed-hook>",
            file=sys.stderr,
        )
        return 2

    canonical, deployed = Path(argv[1]), Path(argv[2])

    if not canonical.is_file():
        print(f"ERROR: canonical script not found: {canonical}", file=sys.stderr)
        return 2

    if not deployed.is_file():
        print("ABSENT")
        return 0

    fresh = normalise(deployed.read_text()) == normalise(canonical.read_text())
    print("FRESH" if fresh else "STALE")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
