#!/usr/bin/env bash
# Report how .pre-commit-config.yaml wires yamllint: LEGACY_PINNED (the rev-pinned
# adrienverge/yamllint mirror an earlier version of this skill wrote), PRESENT (a yamllint
# hook already there) or ABSENT (no hook, or no config file).
set -euo pipefail
CFG=.pre-commit-config.yaml
if [ ! -f "$CFG" ]; then
  echo "ABSENT"
elif grep -q "adrienverge/yamllint" "$CFG"; then
  echo "LEGACY_PINNED"
elif grep -q "id: yamllint" "$CFG"; then
  echo "PRESENT"
else
  echo "ABSENT"
fi
