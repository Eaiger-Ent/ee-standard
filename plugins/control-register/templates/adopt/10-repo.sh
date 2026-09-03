#!/usr/bin/env bash
# Stage 1 — the repository itself: that there is one, that it has a remote, that
# it holds a project three controls need, and that the register has arrived.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; . "$HERE/_lib.sh"

head_ "A repository, and a remote (§ C)"
if root=$(git rev-parse --show-toplevel 2>/dev/null); then
  ok "git repository — $root"
  cd "$root" || exit 1
else
  bad "not a git repository — nothing below can work" "C"
  verdict 10-repo.sh ""; exit 1
fi

if origin=$(git remote get-url origin 2>/dev/null); then
  case "$origin" in
    https://github.com/*) ok "origin is HTTPS — $origin" ;;
    git@github.com:*)     bad "origin is SSH — the container has no key to push with" "B"
                          note "$origin" ;;
    *)                    wait_on "origin is not a github.com URL — $origin" "C" ;;
  esac
else
  bad "no origin remote" "C"
fi

if have gh && gh repo view --json nameWithOwner -q .nameWithOwner >/dev/null 2>&1; then
  ok "GitHub knows this repository — $(gh repo view --json nameWithOwner -q .nameWithOwner)"
else
  bad "gh cannot resolve this repository — a token or a remote problem" "E"
fi

head_ "A project for the gates to gate (§ C2)"
if [ -f pyproject.toml ]; then
  ok "pyproject.toml"
  if [ -f uv.lock ]; then ok "uv.lock"; else bad "no lockfile — an unrecorded pin is not one" "C2"; fi
else
  bad "no pyproject.toml — § 5 stops having written nothing" "C2"
fi

if git ls-files --error-unmatch .python-version >/dev/null 2>&1; then
  ok ".python-version is tracked — SUP-001 reads what git tracks"
else
  bad ".python-version is not tracked" "C2"
fi

if [ -n "$(git ls-files 'tests/test_*.py' 'test_*.py' 2>/dev/null)" ]; then
  ok "a test file is tracked"
  note "TST-001 needs it to pass, not merely to exist — 40-adopt.sh runs it."
else
  bad "no tracked test — pytest exits 5 and your first push is refused" "C2"
fi

head_ "The register (§ 2)"
if [ -f controls.yaml ]; then
  ok "controls.yaml is present"
  ref=$(grep -A3 '^    install:' controls.yaml 2>/dev/null | sed -n 's/^ *ref: *//p' | head -1)
  if [ -n "$ref" ]; then ok "it names ref $ref"; else bad "no install ref found in it" "2"; fi
else
  bad "no controls.yaml — the register is what you adopt" "2"
fi

verdict 10-repo.sh 20-platform.sh
