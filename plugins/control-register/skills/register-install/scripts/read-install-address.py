#!/usr/bin/env -S uv run --no-project --with pyyaml python
"""Print the checker's address — repository and ref — out of the control register.

Run through uv, not directly, and not through `yq`:

    uv run --no-project --with pyyaml python read-install-address.py <register.yaml>

That spelling is the point of the file, not an accident of it. This ran as `yq` until
Phase 4 met a container that had none — nothing in the devcontainer template installs one,
and nothing should, because `yq` would be a tool this skill needs and no control names, so
no register pins it and nothing keeps it in step. uv is the one tool the whole standard
already depends on; `--with` fetches the parser for the length of one command, and
`--no-project` reads the register without touching an environment the checker is not yet
installed into.

Prints two space-separated fields on one line, either of which may be empty:

    <repository> <ref>

Empty rather than absent, deliberately. A register older than contract 29 does not say
where the checker comes from, and the caller stops on that — so this reports what the
register holds and leaves the judgement upstream, where the stop is written. What it must
never do is guess an address: that is the one failure mode this skill has that nobody would
notice, because it would install *something*.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {argv[0].rsplit('/', 1)[-1]} <register.yaml>", file=sys.stderr)
        return 2

    with Path(argv[1]).open(encoding="utf-8") as fh:
        register = yaml.safe_load(fh)

    install = register["tools"]["register-check"].get("install") or {}
    print(install.get("repository", ""), install.get("ref", ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
