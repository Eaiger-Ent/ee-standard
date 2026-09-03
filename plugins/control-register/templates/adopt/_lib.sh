# Shared vocabulary for the adoption route. Sourced, never executed.
#
# **These scripts detect; START-HERE.md instructs.** Every failure prints the
# section that says what to do about it and no script repeats those words. That
# is the whole design constraint: a script holding a copy of an instruction is
# free to drift from the document, which is the failure this repository exists
# to prevent. `tests/test_adopt_route.py` fails a reference to a section that
# does not exist.
#
# Exit codes, which are how one script names the next:
#
#   0  this stage holds        → run the NEXT script it prints
#   1  a check failed          → yours to fix, at the section named
#   2  waiting on a manual act → you, or somebody with rights you lack
#   3  cannot verify from here → wrong machine (host vs container)

if [ -t 1 ]; then
  _g=$'\033[32m'; _r=$'\033[31m'; _y=$'\033[33m'; _d=$'\033[2m'; _n=$'\033[0m'
else
  _g=''; _r=''; _y=''; _d=''; _n=''
fi

FAILED=0
PENDING=0

# `ok    <what>`            a fact that holds
# `bad   <what> <section>`  a fact that does not, and where it is explained
# `wait  <what> <section>`  a manual act nothing here can perform
# `note  <text>`            context, never a verdict
ok()   { printf '  %s✓%s %s\n' "$_g" "$_n" "$1"; }
bad()  { printf '  %s✗%s %s  %s→ START-HERE.md § %s%s\n' "$_r" "$_n" "$1" "$_d" "$2" "$_n"; FAILED=$((FAILED + 1)); }
wait_on() { printf '  %s•%s %s  %s→ START-HERE.md § %s%s\n' "$_y" "$_n" "$1" "$_d" "$2" "$_n"; PENDING=$((PENDING + 1)); }
note() { printf '    %s%s%s\n' "$_d" "$1" "$_n"; }
head_() { printf '\n%s\n' "$1"; }

have() { command -v "$1" >/dev/null 2>&1; }

# /workspaces is where devcontainer.json mounts this repository; /.dockerenv is
# the fallback for a container started any other way.
in_container() {
  [ -f /.dockerenv ] && return 0
  case "$PWD" in /workspaces/*) return 0 ;; esac
  return 1
}

# The route, in order. One line per stage: script, then what it settles.
# `status.sh` walks this and nothing else, so adding a stage is one line here.
ROUTE_SCRIPTS="00-preflight.sh 10-repo.sh 20-platform.sh 30-container.sh 40-adopt.sh"
route_title() {
  case "$1" in
    00-preflight.sh) echo "your Mac has the tools, and git is not rewriting URLs" ;;
    10-repo.sh)      echo "a repository, a remote, a project in it, and the register" ;;
    20-platform.sh)  echo "what your GitHub plan and settings allow" ;;
    30-container.sh) echo "the devcontainer is substituted and built" ;;
    40-adopt.sh)     echo "inside the container: the gates, and what register-check says" ;;
    *)               echo "unknown stage" ;;
  esac
}

# Called last by every stage script. Turns the counters into the exit code and
# names the next script, so the output itself is the routing.
verdict() {
  local this="$1" next="$2"
  echo
  if [ "$FAILED" -gt 0 ]; then
    printf '%sBLOCKED%s — %s check(s) failed. Fix them at the sections named, then re-run:\n' "$_r" "$_n" "$FAILED"
    printf '  ./%s\n' "$this"
    return 1
  fi
  if [ "$PENDING" -gt 0 ]; then
    printf '%sWAITING%s — %s manual act(s) outstanding. Do them, then re-run:\n' "$_y" "$_n" "$PENDING"
    printf '  ./%s\n' "$this"
    return 2
  fi
  if [ -z "$next" ]; then
    printf '%sDONE%s — this was the last stage.\n' "$_g" "$_n"
    return 0
  fi
  printf '%sOK%s — next:\n  ./%s   %s(%s)%s\n' "$_g" "$_n" "$next" "$_d" "$(route_title "$next")" "$_n"
  return 0
}
