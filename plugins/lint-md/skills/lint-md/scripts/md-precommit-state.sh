#!/usr/bin/env bash
# Report how .pre-commit-config.yaml wires markdownlint-cli2: LEGACY_PINNED (the rev-pinned
# DavidAnson/markdownlint-cli2 repo an earlier version of this skill wrote), PRESENT (a
# markdownlint-cli2 hook already there) or ABSENT (no hook, or no config file).
set -euo pipefail
CFG=.pre-commit-config.yaml
if [ ! -f "$CFG" ]; then
  echo "ABSENT"
elif grep -q "DavidAnson/markdownlint-cli2" "$CFG"; then
  echo "LEGACY_PINNED"
elif grep -q "markdownlint-cli2" "$CFG"; then
  echo "PRESENT"
else
  echo "ABSENT"
fi
