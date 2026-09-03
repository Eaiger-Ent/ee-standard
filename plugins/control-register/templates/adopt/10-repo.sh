#!/usr/bin/env bash
#
# Stage 1 — the repository.
#
# Three things, in the order they are needed: that there is a repository with a
# remote, that it holds a project (an empty one cannot be adopted — three
# controls have nothing to say about it), and that the register has arrived.

set -uo pipefail
cd "$(dirname "$0")" || exit 1
. ./_lib.sh
cd "$(repository_root)" || exit 1

# ---------------------------------------------------------- repository, remote

section "A repository, and a remote (§ C)"
if ! root=$(git rev-parse --show-toplevel 2>/dev/null); then
  fail "not a git repository — nothing below can work" "C"
  verdict 10-repo.sh ""
  exit 1
fi
pass "git repository — $root"

if ! origin=$(git remote get-url origin 2>/dev/null); then
  fail "no origin remote" "C"
else
  case "$origin" in
    https://github.com/*)
      pass "origin is HTTPS — $origin"
      ;;
    git@github.com:*)
      fail "origin is SSH — the container has no key to push with" "B"
      detail "$origin"
      ;;
    *)
      manual "origin is not a github.com URL — $origin" "C"
      ;;
  esac
fi

if slug=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null); then
  pass "GitHub knows this repository — $slug"
else
  fail "gh cannot resolve this repository — a token or a remote problem" "E"
fi

# ------------------------------------------------------------------ the project

section "A project for the gates to gate (§ C2)"
if [ -f pyproject.toml ]; then
  pass "pyproject.toml"
else
  fail "no pyproject.toml — § 5 stops, having written nothing" "C2"
fi

if [ -f uv.lock ]; then
  pass "uv.lock"
else
  fail "no lockfile — an unrecorded pin is not one" "C2"
fi

if git ls-files --error-unmatch .python-version >/dev/null 2>&1; then
  pass ".python-version is tracked — SUP-001 reads what git tracks"
else
  fail ".python-version is not tracked" "C2"
fi

if [ -n "$(git ls-files 'tests/test_*.py' 'test_*.py' 2>/dev/null)" ]; then
  pass "a test file is tracked"
  detail "TST-001 needs it to pass, not merely to exist. 40-adopt.sh runs it."
else
  fail "no tracked test — pytest exits 5 and your first push is refused" "C2"
fi

# ----------------------------------------------------------------- the register

section "The register (§ 2)"
if [ ! -f controls.yaml ]; then
  fail "no controls.yaml — the register is what you adopt" "2"
else
  pass "controls.yaml is present"

  declared_ref=$(grep -A3 '^    install:' controls.yaml 2>/dev/null | sed -n 's/^ *ref: *//p' | head -1)
  if [ -n "$declared_ref" ]; then
    pass "it names ref $declared_ref"
  else
    fail "no install ref found in it" "2"
  fi
fi

verdict 10-repo.sh 20-platform.sh
