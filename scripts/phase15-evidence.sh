#!/usr/bin/env bash
# Collect the OBSERVATIONS docs/21-phase-15-runbook.md asks an operator to record.
#
# It gathers facts and decides nothing. It does not tick a criterion, does not
# say pass or fail, and does not restate what a run should expect: the runbook
# is the only place the criteria and the steps live, and this file is a
# recorder for them, not a second copy. Paste the output under the run's
# heading in that file.
#
# Three modes, one per place the runbook asks for evidence:
#
#   host     on the Mac, outside any container: § "Record, for every run", the
#            Docker-absent check, the running containers, and the secrets-in-
#            the-process-list COUNT (a number; never a value).
#   inside   from a shell inside the Apple container: the `inside_container()`
#            signals of Run D, the user, `check-auth.sh`'s verdict lines.
#   run      -- CMD...   runs CMD and records its output and exit code between
#            two `container list` snapshots. For Run C: a refusal that names the
#            key, a non-zero exit, and no container created are all visible in
#            one record.
#
# Writes to $PHASE15_OUT (default ~/phase15), one file per invocation, and
# prints the path. The file holds no secret value and no username: $HOME is
# written as ~. It is bash 3.2 clean, because that is what a Mac ships.
set -uo pipefail

usage() {
  echo "usage: $0 host | inside | run -- COMMAND [ARG...]" >&2
  exit 2
}

mode="${1:-}"
case "$mode" in host | inside | run) ;; *) usage ;; esac
shift
if [ "$mode" = run ]; then
  [ "${1:-}" = "--" ] && [ "$#" -ge 2 ] || usage
fi

out_dir="${PHASE15_OUT:-$HOME/phase15}"
mkdir -p "$out_dir"
out="$out_dir/evidence-$(date -u +%Y%m%dT%H%M%SZ)-$mode.txt"

# $HOME becomes ~, so the record can be pasted into a public repository.
scrub() { sed "s|$HOME|~|g"; }

section() { printf '\n## %s\n' "$1"; }

# Print "name: output" for a command that may be absent; never fail the run.
probe() {
  local label="$1"
  shift
  if command -v "$1" >/dev/null 2>&1; then
    printf '%s: %s\n' "$label" "$("$@" 2>&1 | head -n 1)"
  else
    printf '%s: not on PATH\n' "$label"
  fi
}

# The exit status of a command, and nothing it printed.
status_of() {
  "$@" >/dev/null 2>&1
  echo $?
}

containers() {
  if command -v container >/dev/null 2>&1; then
    container list --all 2>&1 || echo "(container list exited $?)"
  else
    echo "container: not on PATH"
  fi
}

record_host() {
  section "versions (the runbook: a run without its versions is not evidence)"
  echo "date (UTC): $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  probe "macOS" sw_vers -productVersion
  echo "arch: $(uname -m)"
  echo "model: $(sysctl -n hw.model 2>/dev/null || echo unknown)"
  probe "container" container --version
  probe "node" node --version
  if [ -x node_modules/.bin/devcontainer ]; then
    echo "devcontainer CLI (./node_modules/.bin): $(node_modules/.bin/devcontainer --version 2>&1 | head -n 1)"
  else
    echo "devcontainer CLI (./node_modules/.bin): absent in $(pwd | scrub)"
  fi

  section "docker (a run with Docker answering proves nothing)"
  if command -v docker >/dev/null 2>&1; then
    echo "docker on PATH: yes ($(command -v docker | scrub))"
    echo "docker info exit status: $(status_of docker info)"
  else
    echo "docker on PATH: no"
  fi

  section "gh (exit status only; no account name is recorded)"
  if command -v gh >/dev/null 2>&1; then
    echo "gh auth status exit status: $(status_of gh auth status)"
  else
    echo "gh: not on PATH"
  fi

  section "containers"
  containers

  section "secrets in the host process list (a count; the runbook expects 0)"
  # The prefix reaches grep through a file descriptor, not its argument list, so
  # this command does not put the value it is looking for into the process list.
  token="${GITHUB_TOKEN:-}"
  if [ -z "$token" ] && [ -f .devcontainer/.env ]; then
    token="$( (set -a; . .devcontainer/.env >/dev/null 2>&1; printf '%s' "${GITHUB_TOKEN:-}") )"
  fi
  if [ -n "$token" ]; then
    count="$(ps -axww -o args | grep -c -F -f <(printf '%s\n' "$(printf '%s' "$token" | head -c 12)"))"
    echo "processes whose arguments contain the first 12 characters of GITHUB_TOKEN: $count"
  else
    echo "not checked: GITHUB_TOKEN is not in the environment and .devcontainer/.env was not found in $(pwd | scrub)"
  fi
  unset token
}

record_inside() {
  section "versions"
  echo "date (UTC): $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "arch: $(uname -m)"
  echo "kernel: $(uname -sr)"

  section "inside_container() signals (Run D)"
  if [ -e /.dockerenv ]; then echo "/.dockerenv: present"; else echo "/.dockerenv: absent"; fi
  echo "REMOTE_CONTAINERS: '${REMOTE_CONTAINERS:-}'"
  echo "CODESPACES: '${CODESPACES:-}'"

  section "user (the runbook expects uid=1000(vscode))"
  id

  section "check-auth.sh verdict lines (✓ / ✗ only)"
  if [ -x .devcontainer/check-auth.sh ]; then
    # The git line carries the committer's name and email; keep its verdict only.
    .devcontainer/check-auth.sh 2>&1 | grep -E '^ +[✓✗]' \
      | sed -E 's/^( +[✓✗] git) — .*/\1 — (identity not recorded)/' || echo "(no verdict lines)"
  else
    echo ".devcontainer/check-auth.sh: not found in $(pwd | scrub)"
  fi

  section "lock file and tree (the runbook expects the lock file unchanged)"
  git status --short 2>&1 | head -n 20
  echo "(end of git status)"

  section "register-check (the runbook expects exit 3 locally)"
  if command -v uv >/dev/null 2>&1; then
    uv run register-check >/dev/null 2>&1
    echo "uv run register-check exit status: $?"
  else
    echo "uv: not on PATH"
  fi
}

record_run() {
  [ "${1:-}" = "--" ] || usage
  shift
  [ "$#" -gt 0 ] || usage
  section "command"
  echo "$*" | scrub
  section "containers before"
  containers
  section "output"
  "$@" 2>&1 | scrub
  rc="${PIPESTATUS[0]}"
  echo
  echo "exit status: $rc"
  section "containers after"
  containers
}

{
  echo "# Phase 15 evidence: $mode"
  echo "# Observations only. Paste under the run's heading in docs/21-phase-15-runbook.md;"
  echo "# the criteria, and whether this passes, are that file's to say."
  case "$mode" in
    host) record_host ;;
    inside) record_inside ;;
    run) record_run "$@" ;;
  esac
} 2>&1 | scrub | tee "$out"

echo
echo "written to: ${out/#$HOME/\~}"
