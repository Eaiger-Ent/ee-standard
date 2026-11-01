#!/usr/bin/env -S uv run python
"""Prints PRESENT if the named hook is in .claude/settings.json, else ABSENT.

Usage: <this script> <hook-filename>   (e.g. md-lint.py)

The hook filename is an argument rather than a literal so this file is byte-identical in
every plugin that ships it (#709). lint-md and lint-yaml carried two copies differing only
in that one string, in two different plugins, with nothing comparing them — so which
behaviour a user got depended on which plugin they installed, and a fix to either copy
forked the other silently. scripts/check-mirrored-files.sh declares the pair and fails on
divergence, which it can only do while the copies are identical.

A missing argument is an error, not a default: defaulting would have this copy report on
some other skill's hook and answer PRESENT for a hook this skill never wrote.
"""
import json
import sys
from pathlib import Path

if len(sys.argv) != 2:
    sys.exit(f"usage: {Path(__file__).name} <hook-filename>  (e.g. md-lint.py)")
hook = sys.argv[1]
p = Path('.claude/settings.json')
s = json.loads(p.read_text()) if p.exists() else {}
hooks = s.get('hooks', {}).get('PostToolUse', [])
found = any(
    any(hook in h.get('command', '') for h in e.get('hooks', []))
    for e in hooks
)
print('PRESENT' if found else 'ABSENT')
