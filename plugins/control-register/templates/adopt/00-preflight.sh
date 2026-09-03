#!/usr/bin/env bash
# Stage 0 — your Mac. Runs before there is a container, and before step 1 has
# anything to say. Detects only; § B and § E of START-HERE.md instruct.
set -uo pipefail
cd "$(dirname "$0")" && . ./_lib.sh

if in_container; then
  echo "This stage is about your Mac, and you are inside the container."
  note "Run it in a terminal on the host, from your repository root."
  exit 3
fi

head_ "Tools (§ B)"
for pair in "brew:Homebrew" "docker:Docker" "claude:Claude Code" "npm:npm" \
            "devcontainer:devcontainer CLI" "gh:GitHub CLI" "uv:uv"; do
  cmd=${pair%%:*}; label=${pair#*:}
  if have "$cmd"; then ok "$label"; else bad "$label — not on PATH" "B"; fi
done
if have code; then ok "VS Code"; else wait_on "VS Code — optional, but § 5 mentions it" "B"; fi

head_ "Docker is running (§ A)"
if have docker && docker info >/dev/null 2>&1; then
  ok "docker info succeeds"
  mem=$(docker info --format '{{.MemTotal}}' 2>/dev/null || echo 0)
  if [ "${mem:-0}" -ge 8000000000 ] 2>/dev/null; then
    ok "$((mem / 1000000000)) GB of memory"
  else
    wait_on "Docker has under 8 GB of memory" "B"
  fi
else
  bad "docker info fails — Docker Desktop is not running" "A"
fi

head_ "git is not rewriting GitHub URLs (§ 1)"
rewrites=$(git config --global --get-regexp 'url\..*\.insteadof' 2>/dev/null || true)
if [ -z "$rewrites" ]; then
  ok "no url.*.insteadOf rewrite"
else
  bad "a global rewrite will turn the plugin's HTTPS clone into SSH" "1"
  printf '%s\n' "$rewrites" | while IFS= read -r line; do note "$line"; done
fi

head_ "gh talks HTTPS, not SSH (§ B)"
if have gh && gh auth status >/dev/null 2>&1; then
  ok "gh is authenticated"
  proto=$(gh config get git_protocol 2>/dev/null || echo unknown)
  case "$proto" in
    https) ok "git_protocol is https" ;;
    ssh)   bad "git_protocol is ssh — § C would write an origin the container cannot push to" "B" ;;
    *)     wait_on "git_protocol is '$proto'" "B" ;;
  esac
else
  bad "gh is not authenticated" "B"
fi

head_ "Keychain entries (§ E, § 4)"
if have security; then
  if security find-generic-password -a "$USER" -s CLAUDE_OAUTH_TOKEN -w >/dev/null 2>&1; then
    ok "CLAUDE_OAUTH_TOKEN — the container will not start without it"
  else
    wait_on "CLAUDE_OAUTH_TOKEN not in the Keychain" "4"
  fi
  prefix=$(basename "$PWD" | tr '[:lower:]-' '[:upper:]_')
  if security find-generic-password -a "$USER" -s "${prefix}_GITHUB_TOKEN" -w >/dev/null 2>&1; then
    ok "${prefix}_GITHUB_TOKEN — project-scoped, and it wins over the plain name"
  elif security find-generic-password -a "$USER" -s GITHUB_TOKEN -w >/dev/null 2>&1; then
    ok "GITHUB_TOKEN — shared across every project on this machine"
  else
    wait_on "no GitHub PAT in the Keychain" "E"
  fi
else
  echo "  no 'security' command — this is not macOS."
  note "§ A states the contract a replacement for fetch-secrets.sh owes."
  exit 3
fi

verdict 00-preflight.sh 10-repo.sh
