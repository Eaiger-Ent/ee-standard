#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["pyyaml==6.0.3"]
# ///
"""Prints OK if the named config file parses, else INVALID and the parse error.

Usage: <this script> <path>   (e.g. .claude/settings.json, .pre-commit-config.yaml)

The format is taken from the extension: `.json` is parsed as JSON, `.yaml`/`.yml` as YAML.
Both lint skills write `.claude/settings.json` and `.pre-commit-config.yaml` and then have to
know the write left something parseable behind. That check used to be an inline
`python3 -c "import json; json.load(open(...))"` in each skill body, which TE Q1b of
skills/skill-quality/skill-design-standards.md makes an extraction trigger: a one-liner
carrying imports is an unextracted script. It also could not report *why* a file failed to
parse — the traceback went to stderr while `|| echo "INVALID"` swallowed the detail the skill
then asks the user to act on.

This file is byte-identical in every plugin that ships it (#709), so nothing here names one
skill's step numbers; scripts/check-mirrored-files.sh declares the pair and fails on
divergence.

A file that is missing, or empty, is INVALID rather than OK. Every caller runs this
immediately after writing the file, so "nothing there" is a failed write, not a clean slate;
`yaml.safe_load` on an empty file returns None and the old one-liner called that OK.

Run it with `uv run --script`, which reads the dependency block above and gives the script
an environment with PyYAML in it. A bare `python3` is whatever the machine has: the base
devcontainer image ships Debian's 3.13 without PyYAML, so `import yaml` failed there and
the skill stopped on a check that had nothing wrong to report.

Exit status matches the printed word (0 for OK, 1 for INVALID) so a caller may branch on
either.
"""
import json
import sys
from collections.abc import Callable
from pathlib import Path

if len(sys.argv) != 2:
    sys.exit(f"usage: {Path(__file__).name} <path>  (e.g. .pre-commit-config.yaml)")

path = Path(sys.argv[1])
parse: Callable[[str], object]
if path.suffix == ".json":
    parse, module = json.loads, "json"
elif path.suffix in (".yaml", ".yml"):
    import yaml
    parse, module = yaml.safe_load, "yaml"
else:
    sys.exit(f"{Path(__file__).name}: cannot tell the format of {path} from its extension"
             " — want .json, .yaml or .yml")

if not path.is_file():
    print(f"INVALID: {path} does not exist")
    sys.exit(1)

text = path.read_text()
if not text.strip():
    print(f"INVALID: {path} is empty")
    sys.exit(1)

try:
    if parse(text) is None:
        print(f"INVALID: {path} holds no {module} document")
        sys.exit(1)
except Exception as exc:  # json.JSONDecodeError or yaml.YAMLError, both worth quoting
    print(f"INVALID: {path} — {exc}")
    sys.exit(1)

print("OK")
