#!/usr/bin/env -S uv run python
"""Adds the named PostToolUse hook to .claude/settings.json.

Usage: <this script> <hook-filename>   (e.g. md-lint.py)

The hook filename is an argument rather than a literal so this file is byte-identical in
every plugin that ships it (#709) — see the registration check beside it for why.
A missing argument is an error, not a default: defaulting would wire some other skill's
hook into the user's settings.

The wrapper written here fails OPEN (#865, #872). `git rev-parse --show-toplevel` resolves
to the *worktree* root, not the main checkout, so a worktree that does not hold
.claude/hooks/<hook> made `uv run` exit non-zero on every Write/Edit — and on a PreToolUse
hook a non-zero exit blocks the tool call, which wedges the session. The
`[ -f <target> ] || exit 0` guard makes an absent target a no-op instead. Outside a git repo
the `2>/dev/null` assignment fails, the `&&` chain short-circuits, and the same `|| exit 0`
applies. scripts/test-hook-wrappers.py pins this exact shape, generator included.
"""
import json
import sys
from pathlib import Path

if len(sys.argv) != 2:
    sys.exit(f"usage: {Path(__file__).name} <hook-filename>  (e.g. md-lint.py)")
hook = sys.argv[1]
p = Path('.claude/settings.json')
s = json.loads(p.read_text()) if p.exists() else {}
ptu = s.setdefault('hooks', {}).setdefault('PostToolUse', [])
e = next((x for x in ptu if x.get('matcher') == 'Write|Edit'), None)
t = '.claude/hooks/' + hook
cmd = {
    'type': 'command',
    'command': "bash -c 'root=$(git rev-parse --show-toplevel 2>/dev/null)"
    " && cd \"$root\" && [ -f " + t + " ] || exit 0; uv run python " + t + "'",
}
if e:
    e.setdefault('hooks', []).append(cmd)
else:
    ptu.append({'matcher': 'Write|Edit', 'hooks': [cmd]})
p.write_text(json.dumps(s, indent=2) + '\n')
print('updated')
