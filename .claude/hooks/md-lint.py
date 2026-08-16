#!/usr/bin/env python3
import json, sys, subprocess, os

d = json.load(sys.stdin)
f = d.get('tool_input', {}).get('file_path', '')

if not f.endswith('.md') or not os.path.exists(f):
    sys.exit(0)

# Claude's auto-memory files (~/.claude/projects/*/memory/*.md) are managed
# by Claude's memory system, not this repo's markdown conventions.
memory_root = os.path.join(os.path.expanduser('~'), '.claude', 'projects')
if f.startswith(memory_root) and f'{os.sep}memory{os.sep}' in f:
    sys.exit(0)

name = os.path.basename(f)

# Auto-fix what markdownlint can repair on its own.
subprocess.run(['markdownlint-cli2', '--fix', f], capture_output=True)

# Re-check for anything that couldn't be auto-fixed.
r = subprocess.run(['markdownlint-cli2', f], capture_output=True, text=True)
out = (r.stdout + r.stderr).strip()

if r.returncode != 0:
    print(f'\n\n⚠ STOP: markdownlint [{name}] has unfixable errors — do not proceed until resolved.\n'
          f'Fix each issue listed below by editing {f}, then re-save:\n\n{out}\n')
    sys.exit(1)
else:
    print(f'markdownlint [{name}]: OK')
