#!/usr/bin/env bash
# Runs on the HOST before container start (devcontainer.json initializeCommand).
# Fetches secrets from the macOS Keychain into .devcontainer/.env, which
# runArgs --env-file injects into the container. The .env is gitignored.
#
# Service names are generic (no per-repo prefix) so one host-side credential
# store is reused across projects. Prefix any name with the checkout directory
# in UPPER_SNAKE_CASE to override for one project: EE_STANDARD_GITHUB_TOKEN.
#
# See docs/06-devcontainer-setup.md for the full value list.
set -euo pipefail

echo "==> Fetching secrets from Keychain..."
: > .devcontainer/.env

PROJECT_PREFIX=$(basename "$PWD" | tr '[:lower:]-' '[:upper:]_')

# Tries ${PROJECT_PREFIX}_${2}, then ${2}, writing the value into the
# variable named by $1. Sets LAST_SECRET_KEY to the hit.
# Run directly (not via command substitution) so these assignments land in
# the caller's shell rather than a throwaway subshell.
fetch_secret() {
  local __outvar="$1" name="$2" prefixed="${PROJECT_PREFIX}_${2}" value
  value=$(security find-generic-password -a "$USER" -s "$prefixed" -w 2>/dev/null) || true
  if [ -n "$value" ]; then
    LAST_SECRET_KEY="$prefixed"
  else
    value=$(security find-generic-password -a "$USER" -s "$name" -w 2>/dev/null) || true
    LAST_SECRET_KEY="$name"
  fi
  printf -v "$__outvar" '%s' "$value"
}

fetch_secret CLAUDE_CODE_OAUTH_TOKEN "CLAUDE_OAUTH_TOKEN"
if [ -z "$CLAUDE_CODE_OAUTH_TOKEN" ]; then
  echo "  ✗ No Claude Code OAuth token in Keychain."
  echo "    Run 'claude setup-token' on your Mac, then:"
  echo "      security add-generic-password -a \"\$USER\" \\"
  echo "        -s \"CLAUDE_OAUTH_TOKEN\" -w \"sk-ant-oat01-...\""
  exit 1
fi
echo "CLAUDE_CODE_OAUTH_TOKEN=${CLAUDE_CODE_OAUTH_TOKEN}" >> .devcontainer/.env
echo "  ✓ CLAUDE_CODE_OAUTH_TOKEN [${LAST_SECRET_KEY}]"

fetch_secret GITHUB_TOKEN "GITHUB_TOKEN"
if [ -n "$GITHUB_TOKEN" ]; then
  echo "GITHUB_TOKEN=${GITHUB_TOKEN}" >> .devcontainer/.env
  echo "  ✓ GITHUB_TOKEN [${LAST_SECRET_KEY}]"
fi

# Second PAT, for the EqualExperts org (ee-skills, ee-skills-incubator,
# generate-ee-slides) — GITHUB_TOKEN above is scoped to Eaiger-Ent and would
# otherwise shadow gh's own auth for those repos too. Consumed via the
# `gh-ee-skills` wrapper (setup.sh), never as the ambient GITHUB_TOKEN.
fetch_secret EE_SKILLS_GITHUB_TOKEN "EE_SKILLS_GITHUB_TOKEN"
if [ -n "$EE_SKILLS_GITHUB_TOKEN" ]; then
  echo "EE_SKILLS_GITHUB_TOKEN=${EE_SKILLS_GITHUB_TOKEN}" >> .devcontainer/.env
  echo "  ✓ EE_SKILLS_GITHUB_TOKEN [${LAST_SECRET_KEY}]"
fi

fetch_secret GIT_AUTHOR_NAME "GIT_AUTHOR_NAME"
if [ -n "$GIT_AUTHOR_NAME" ]; then
  {
    echo "GIT_AUTHOR_NAME=\"${GIT_AUTHOR_NAME}\""
    echo "GIT_COMMITTER_NAME=\"${GIT_AUTHOR_NAME}\""
  } >> .devcontainer/.env
  echo "  ✓ GIT_AUTHOR_NAME [${LAST_SECRET_KEY}]"
fi

fetch_secret GIT_AUTHOR_EMAIL "GIT_AUTHOR_EMAIL"
if [ -n "$GIT_AUTHOR_EMAIL" ]; then
  {
    echo "GIT_AUTHOR_EMAIL=\"${GIT_AUTHOR_EMAIL}\""
    echo "GIT_COMMITTER_EMAIL=\"${GIT_AUTHOR_EMAIL}\""
  } >> .devcontainer/.env
  echo "  ✓ GIT_AUTHOR_EMAIL [${LAST_SECRET_KEY}]"
fi

echo "  ✓ Written to .devcontainer/.env"
