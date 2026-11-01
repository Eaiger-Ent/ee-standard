#!/usr/bin/env bash
# Report the markdownlint config in the current directory: EXISTS_MARKDOWNLINT,
# EXISTS_MARKDOWNLINT_EMPTY (a 0-byte .markdownlint.yaml left by an interrupted setup),
# EXISTS_MARKDOWNLINT_JSON or ABSENT.
set -euo pipefail
if [ -f .markdownlint.yaml ]; then
  if [ -s .markdownlint.yaml ]; then
    echo "EXISTS_MARKDOWNLINT"
  else
    echo "EXISTS_MARKDOWNLINT_EMPTY"
  fi
elif [ -f .markdownlint.json ]; then
  echo "EXISTS_MARKDOWNLINT_JSON"
else
  echo "ABSENT"
fi
