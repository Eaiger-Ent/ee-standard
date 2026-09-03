#!/usr/bin/env bash
#
# Stage 2.5 — the credentials (§ E, § 4).
#
# Separate from the tools because it comes after them in the document and after
# § C and § D in practice: you cannot scope a token to a repository that does
# not exist yet. Nothing here creates a token — every one is made in a browser,
# by you, and this reports which of them have arrived in the Keychain.

set -uo pipefail
cd "$(dirname "$0")" || exit 1
. ./_lib.sh
cd "$(repository_root)" || exit 1

if ! installed security; then
  echo "No 'security' command — this is not macOS, so the Keychain cannot be read."
  detail "§ A states the contract a replacement for fetch-secrets.sh owes."
  exit 3
fi

keychain_has() {
  local service_name="$1"
  security find-generic-password -a "$USER" -s "$service_name" -w >/dev/null 2>&1
}

# ------------------------------------------------------------- Claude Code

section "Claude Code (§ 4)"
if keychain_has CLAUDE_OAUTH_TOKEN; then
  pass "CLAUDE_OAUTH_TOKEN — the container will not start without it"
else
  manual "CLAUDE_OAUTH_TOKEN is not in the Keychain" "4"
fi

# ----------------------------------------------------------------- GitHub

section "The GitHub PAT (§ E)"

# fetch-secrets.sh looks the project-scoped name up first, so this checks in the
# same order: a token named for this project wins wherever both exist.
project_prefix=$(basename "$PWD" | tr '[:lower:]-' '[:upper:]_')

if keychain_has "${project_prefix}_GITHUB_TOKEN"; then
  pass "${project_prefix}_GITHUB_TOKEN — project-scoped, and it wins over the plain name"
  token_present=yes
elif keychain_has GITHUB_TOKEN; then
  pass "GITHUB_TOKEN — shared across every project on this machine"
  token_present=yes
else
  manual "no GitHub PAT in the Keychain" "E"
  token_present=no
fi

# A token that exists and a token that can see this repository are different
# facts, and the second is the one that matters. GitHub answers 404 rather than
# 403 for a repository a token cannot see, so this cannot say which it is —
# § E's four-line block is what tells a scoping problem from a missing remote.
if [ "$token_present" = yes ]; then
  keychain_token=$(security find-generic-password -a "$USER" -s "${project_prefix}_GITHUB_TOKEN" -w 2>/dev/null \
    || security find-generic-password -a "$USER" -s GITHUB_TOKEN -w 2>/dev/null)

  if [ -n "$keychain_token" ] && installed gh; then
    if GH_TOKEN="$keychain_token" gh api "repos/{owner}/{repo}" --jq .full_name >/dev/null 2>&1; then
      pass "and it can read this repository"
    else
      fail "it is stored but cannot read this repository" "E"
      detail "404 and 403 read identically here. § E tells them apart in four lines."
    fi
  fi

  case "$keychain_token" in
    github_pat_*) pass "fine-grained — SEC-003 wants this one" ;;
    ghp_*)        fail "classic — SEC-003 fails a classic token in CI" "E" ;;
  esac
fi

section "The second PAT (§ E)"
detail "<repo>-actions is a GitHub environment secret, not a Keychain entry."
detail "It belongs to a later sitting and nothing here can see it."

verdict 25-credentials.sh 30-container.sh
