#!/usr/bin/env bash
# Runs on container create (postCreateCommand).
#
# **This file pins no tool version, and that is a rule rather than an accident.**
# Phase 2's exit criterion reads: *the template pins no tool version by hand;
# every tool it installs is either sourced from a lockfile the consumer repo
# already commits, or from a single toolchain file — never a literal inside
# setup.sh.* A template that scatters pins through a shell script reproduces
# that problem in every repository that adopts the standard, and the consumer
# has no `tool_versions_match_register` of their own until they adopt the
# register too.
#
# So there are exactly two sources of a version here:
#
#   1. A lockfile this repository already commits. `npm ci` and `uv sync
#      --frozen` install what the lockfile says and nothing else.
#   2. A pinned devcontainer feature, resolved to a digest in
#      devcontainer-lock.json.
#
# Anything else — a scanner, a linter, an analyser — is installed by the gate
# that owns the control it serves, which writes its own region into this file
# and stamps it. `gate-secrets` does that for the secret scanner;
# `gate-supply-chain` for the package manager where one is needed.
#
# Deliberately short. Per docs/03-devcontainer.md, anything long enough to need
# sectioning is doing work that belongs in the image or in a pinned feature.
set -euo pipefail

# The named volume mounts root-owned on first create.
sudo chown -R vscode:vscode /home/vscode/.claude

# Install from whichever lockfiles this repository commits. Each is guarded by
# the lockfile's own presence rather than by a language guess: a repository is
# in an ecosystem when it has that ecosystem's lockfile, which is the same test
# SUP-001 applies.
if [ -f package-lock.json ]; then
  npm ci --no-audit --no-fund
fi

if [ -f uv.lock ]; then
  uv sync --frozen
  uv run pre-commit install
elif [ -f poetry.lock ]; then
  poetry install --sync
  poetry run pre-commit install
elif [ -f .pre-commit-config.yaml ]; then
  # A repository with hooks and no Python lockfile still needs them installed.
  # `pre-commit` itself comes from the image or a feature; if it is absent, say
  # so rather than installing an unpinned copy.
  if command -v pre-commit >/dev/null 2>&1; then
    pre-commit install
  else
    echo "note: .pre-commit-config.yaml exists and pre-commit is not installed." >&2
    echo "      Add it to a lockfile this repository commits, or to a feature." >&2
  fi
fi

# The host ~/.gitconfig may name a credential-helper path that does not exist
# in this container.
if command -v gh >/dev/null 2>&1; then
  GH_BIN="$(command -v gh)"
  for host in github.com gist.github.com; do
    git config --global --unset-all "credential.https://${host}.helper" || true
    git config --global --add "credential.https://${host}.helper" \
      "!${GH_BIN} auth git-credential"
  done
fi
