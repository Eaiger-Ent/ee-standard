#!/usr/bin/env bash
#
# Stage 0 — the tools on your Mac (§ A and § B).
#
# Every one of these is a precondition something later depends on silently. A
# missing tool or an SSH-shaped git does not announce itself when it matters; it
# announces itself three steps later, as something else. Credentials are § E and
# are 25-credentials.sh, because they come after § C and § D.

set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/_lib.sh"

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

# Either runtime will do, and neither is required by name (ADR 0065). Each is
# asked whether it is running, not only whether it is installed: an installed
# runtime that does not answer builds nothing.
docker_answers=false
if installed docker && docker info >/dev/null 2>&1; then
  docker_answers=true
fi
apple_answers=false
if installed container && container system status >/dev/null 2>&1; then
  apple_answers=true
fi

section "Tools (§ B)"
require_tool brew "Homebrew"
require_tool claude "Claude Code"
require_tool npm "npm"

# Only the Docker route builds with a `devcontainer` on PATH. The Apple route
# runs the CLI that `.devcontainer/package.json` pins, by its path (ADR 0020).
if installed devcontainer; then
  pass "devcontainer CLI"
elif [ "$docker_answers" = true ]; then
  fail "devcontainer CLI — not on PATH, and the Docker route builds with it" "B"
else
  optional "devcontainer CLI"
  detail "The Apple container route runs the CLI that .devcontainer/package.json pins."
fi

require_tool gh "GitHub CLI"
require_tool uv "uv"

# `code` on PATH is the shell command, not the editor. It is a separate install
# ("Shell Command: Install 'code' command in PATH"), so testing for it reports
# VS Code missing on a Mac that is running it — which it did, to the first
# person who ran this, inside a VS Code terminal.
vs_code_present() {
  installed code && return 0
  [ -d "/Applications/Visual Studio Code.app" ] && return 0
  [ -d "$HOME/Applications/Visual Studio Code.app" ] && return 0
  [ "${TERM_PROGRAM:-}" = vscode ] && return 0
  return 1
}

if vs_code_present; then
  pass "VS Code"
  if ! installed code; then
    detail "the 'code' command is not on PATH, which is a separate install and optional"
  fi
else
  optional "VS Code"
  detail "§ 5 offers two ways into the container and only one of them is VS Code."
fi

# ----------------------------------------------------------- container runtime

section "A container runtime is running (§ A)"
if [ "$apple_answers" = true ]; then
  pass "$RUNTIME_APPLE — container system status succeeds"
  detail "Each container gets the memory its devcontainer.json runArgs ask for. There is no VM to size."
fi

if [ "$docker_answers" = true ]; then
  pass "$RUNTIME_DOCKER — docker info succeeds"

  memory_bytes=$(docker info --format '{{.MemTotal}}' 2>/dev/null || echo 0)
  memory_gb=$((memory_bytes / 1000000000))
  if [ "$memory_gb" -ge 8 ]; then
    pass "Docker has ${memory_gb} GB of memory"
  else
    manual "Docker has ${memory_gb} GB of memory, and the build wants 8" "B"
  fi
fi

if [ "$apple_answers" = false ] && [ "$docker_answers" = false ]; then
  fail "no container runtime answers — neither Apple container nor Docker" "A"
fi

# Installed and not running is worth naming, whichever way the verdict went.
if [ "$apple_answers" = false ] && installed container; then
  detail "Apple container is installed, and container system status fails: its services are not running."
fi
if [ "$docker_answers" = false ] && installed docker; then
  detail "Docker is installed, and docker info fails: Docker is not running."
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
