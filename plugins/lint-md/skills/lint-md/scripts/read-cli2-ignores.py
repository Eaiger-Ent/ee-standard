#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["pyyaml==6.0.3"]
# ///
"""Prints the `ignores` list already in .markdownlint-cli2.yaml, as a JSON array.

Usage: uv run --script read-cli2-ignores.py   (run from the repository root)

`uv run --script` reads the dependency block above, so PyYAML is there whatever `python3`
the machine has. A bare `python3` in the base devcontainer image is Debian's 3.13 without
PyYAML, and this script failed on `import yaml` before reading anything.

Step 2b compares that list with CLI2_IGNORES to decide whether the file needs editing, and
the comparison has to be made against the *parsed* YAML: grepping the file reports an entry
that is commented out, and misses one written in flow style. This was an inline
`python3 -c "import sys,yaml;..."` in the skill body until #872 — an unextracted script under
the rubric's Token Economy dimension.

A missing key prints `[]`, which is what the comparison has always been made against. A
missing file is an error: Step 2b only reaches this when CLI2_IGNORES_STATE is EXISTS, so the
file not being there means the state read is stale, and printing an empty list would report
that as "already matches" and skip the write.
"""
import json
import sys
from pathlib import Path

import yaml

CONFIG = Path(".markdownlint-cli2.yaml")
if not CONFIG.is_file():
    sys.exit(f"read-cli2-ignores.py: {CONFIG} does not exist — re-read CLI2_IGNORES_STATE")

config = yaml.safe_load(CONFIG.read_text()) or {}
print(json.dumps(config.get("ignores", [])))
