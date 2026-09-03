#!/usr/bin/env bash
#
# Stage 0 — the tools on your Mac (§ A and § B).
#
# Every one of these is a precondition something later depends on silently. A
# missing tool or an SSH-shaped git does not announce itself when it matters; it
# announces itself three steps later, as something else. Credentials are § E and
# are 25-credentials.sh, because they come after § C and § D.

set -uo pipefail
cd "$(dirname "$0")" || exit 1
. ./_lib.sh

if inside_container; then
  echo "This stage is about your Mac, and you are inside the container."
  detail "Run it in a terminal on the host, from your repository root."
  exit 3
fi

# --------------------------------------------------------------------- tools

require_tool() {
  local command_name="$1" label="$2"
  if installed "$command_name"; then
    pass "$label"
  else
    fail "$label — not on PATH" "B"
  fi
}

section "Tools (§ B)"
require_tool brew "Homebrew"
require_tool docker "Docker"
require_tool claude "Claude Code"
require_tool npm "npm"
require_tool devcontainer "devcontainer CLI"
require_tool gh "GitHub CLI"
require_tool uv "uv"

if installed code; then
  pass "VS Code"
else
  manual "VS Code — optional, but § 5 offers it as one of two ways in" "B"
fi

# -------------------------------------------------------------------- docker

section "Docker is running (§ A)"
if ! installed docker || ! docker info >/dev/null 2>&1; then
  fail "docker info fails — Docker Desktop is not running" "A"
else
  pass "docker info succeeds"

  memory_bytes=$(docker info --format '{{.MemTotal}}' 2>/dev/null || echo 0)
  memory_gb=$((memory_bytes / 1000000000))
  if [ "$memory_gb" -ge 8 ]; then
    pass "${memory_gb} GB of memory"
  else
    manual "Docker has ${memory_gb} GB of memory, and the build wants 8" "B"
  fi
fi

# ------------------------------------------------------------ git URL rewrites

section "git is not rewriting GitHub URLs (§ 1)"
rewrites=$(git config --global --get-regexp 'url\..*\.insteadof' 2>/dev/null || true)
if [ -z "$rewrites" ]; then
  pass "no url.*.insteadOf rewrite"
else
  fail "a global rewrite will turn the plugin's HTTPS clone into SSH" "1"
  printf '%s\n' "$rewrites" | while IFS= read -r line; do
    detail "$line"
  done
fi

# ------------------------------------------------------------------ gh protocol

section "gh talks HTTPS, not SSH (§ B)"
if ! installed gh || ! gh auth status >/dev/null 2>&1; then
  fail "gh is not authenticated" "B"
else
  pass "gh is authenticated"

  protocol=$(gh config get git_protocol 2>/dev/null || echo unknown)
  case "$protocol" in
    https)
      pass "git_protocol is https"
      ;;
    ssh)
      fail "git_protocol is ssh — § C would write an origin the container cannot push to" "B"
      ;;
    *)
      manual "git_protocol is '$protocol', which is neither" "B"
      ;;
  esac
fi

verdict 00-tools.sh 10-repo.sh
