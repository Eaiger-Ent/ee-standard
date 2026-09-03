# Shared vocabulary for the adoption route. Sourced by every stage, never run.
#
# THE ONE RULE: these scripts report what is true. START-HERE.md says what to do
# about it. A failing check prints the section that explains the fix and not the
# fix itself, because a script holding a copy of an instruction is free to drift
# from the document — the failure this standard exists to prevent.
# tests/test_adopt_route.py fails a section reference that does not resolve.
#
# A stage script reads:
#
#     section "What this group is about (§ B)"
#     if <something is true>; then
#       pass "what holds"
#     else
#       fail "what does not" "B"
#     fi
#     verdict 00-preflight.sh 10-repo.sh
#
# and `verdict` turns the counters into the exit code that names the next stage.

# ---------------------------------------------------------------- presentation

if [ -t 1 ]; then
  GREEN=$'\033[32m'
  RED=$'\033[31m'
  AMBER=$'\033[33m'
  DIM=$'\033[2m'
  RESET=$'\033[0m'
else
  GREEN='' RED='' AMBER='' DIM='' RESET=''
fi

# ------------------------------------------------------------------- reporting
#
# Three verdicts, and the difference between the last two matters:
#   pass    it holds
#   fail    it does not, and fixing it is yours to do
#   manual  nothing here can do it — a browser, a setting, another person
#
# `fail` and `manual` both take the START-HERE.md section as their last
# argument. `_lib.sh` prints the `§`; the caller passes the bare token.

FAILURES=0
MANUAL_ACTS=0

section() {
  local title="$1"
  printf '\n%s\n' "$title"
}

pass() {
  local what="$1"
  printf '  %s✓%s %s\n' "$GREEN" "$RESET" "$what"
}

fail() {
  local what="$1" section_ref="$2"
  printf '  %s✗%s %s  %s→ START-HERE.md § %s%s\n' \
    "$RED" "$RESET" "$what" "$DIM" "$section_ref" "$RESET"
  FAILURES=$((FAILURES + 1))
}

manual() {
  local what="$1" section_ref="$2"
  printf '  %s•%s %s  %s→ START-HERE.md § %s%s\n' \
    "$AMBER" "$RESET" "$what" "$DIM" "$section_ref" "$RESET"
  MANUAL_ACTS=$((MANUAL_ACTS + 1))
}

# Context under a verdict. Never a verdict itself, so it counts towards nothing.
detail() {
  local text="$1"
  printf '    %s%s%s\n' "$DIM" "$text" "$RESET"
}

# --------------------------------------------------------------------- helpers

installed() {
  local command_name="$1"
  command -v "$command_name" >/dev/null 2>&1
}

# /workspaces is where devcontainer.json mounts the repository; /.dockerenv
# catches a container started any other way.
inside_container() {
  if [ -f /.dockerenv ]; then
    return 0
  fi
  case "$PWD" in
    /workspaces/*) return 0 ;;
  esac
  return 1
}

repository_root() {
  git rev-parse --show-toplevel 2>/dev/null || printf '%s' "$PWD"
}

# ----------------------------------------------------------------------- route
#
# The order of the adoption, in one place. status.sh walks this list and nothing
# else, and a test asserts it matches the files on disk in both directions.

ROUTE_SCRIPTS="00-tools.sh 10-repo.sh 20-platform.sh 25-credentials.sh 30-container.sh 40-adopt.sh"

route_title() {
  local stage="$1"
  case "$stage" in
    00-tools.sh)      echo "your Mac has the tools, and git is not rewriting URLs" ;;
    10-repo.sh)      echo "a repository, a remote, a project in it, and the register" ;;
    20-platform.sh)  echo "what your GitHub plan and settings allow" ;;
    25-credentials.sh) echo "the tokens that reach the container are in the Keychain" ;;
    30-container.sh) echo "the devcontainer is substituted and built" ;;
    40-adopt.sh)     echo "inside the container: the gates, and what register-check says" ;;
    *)               echo "unknown stage" ;;
  esac
}

# ---------------------------------------------------------------------- ending
#
# Every stage ends by calling this. The exit code is how one script names the
# next, so it is the whole routing mechanism:
#
#   0  this stage holds                → run `next_stage`
#   1  a check failed                  → fix it, re-run this stage
#   2  a manual act is outstanding     → do it, re-run this stage
#   3  cannot be answered from here    → wrong machine (a stage exits 3 itself)

verdict() {
  local this_stage="$1" next_stage="$2"
  echo

  if [ "$FAILURES" -gt 0 ]; then
    printf '%sBLOCKED%s — %s check(s) failed. Fix them at the sections named, then re-run:\n' \
      "$RED" "$RESET" "$FAILURES"
    printf '  ./%s\n' "$this_stage"
    return 1
  fi

  if [ "$MANUAL_ACTS" -gt 0 ]; then
    printf '%sWAITING%s — %s manual act(s) outstanding. Do them, then re-run:\n' \
      "$AMBER" "$RESET" "$MANUAL_ACTS"
    printf '  ./%s\n' "$this_stage"
    return 2
  fi

  if [ -z "$next_stage" ]; then
    printf '%sDONE%s — this was the last stage.\n' "$GREEN" "$RESET"
    return 0
  fi

  printf '%sOK%s — next:\n' "$GREEN" "$RESET"
  printf '  ./%s   %s(%s)%s\n' "$next_stage" "$DIM" "$(route_title "$next_stage")" "$RESET"
  return 0
}
