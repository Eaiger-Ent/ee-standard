#!/usr/bin/env bash
# Report the state of .yamllint.yml in the current directory: EXISTS_NONEMPTY, EXISTS_EMPTY
# (a 0-byte file left by an interrupted setup) or ABSENT.
set -euo pipefail
if [ ! -f .yamllint.yml ]; then
  echo "ABSENT"
elif [ -s .yamllint.yml ]; then
  echo "EXISTS_NONEMPTY"
else
  echo "EXISTS_EMPTY"
fi
