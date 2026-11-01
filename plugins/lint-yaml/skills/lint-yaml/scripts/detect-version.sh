#!/usr/bin/env bash
# Detect the latest yamllint release on PyPI; falls back to DEFAULT.
# Read from the PyPI JSON API rather than `pip index`, which needs a pip this
# skill no longer assumes is installed.
DEFAULT="1.38.0"
VERSION=$(curl -fsS https://pypi.org/pypi/yamllint/json 2>/dev/null \
  | grep -oE '"version": *"[0-9]+\.[0-9]+\.[0-9]+"' | head -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || true)
echo "${VERSION:-$DEFAULT}"
