#!/usr/bin/env bash
#
# The whole route, and where you are on it.
#
# Runs every stage quietly and reports the first one that is not satisfied —
# that is the one to run for its detail. Nothing here writes anything.

set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/_lib.sh"

printf 'Adoption route — %s\n' "$(repository_root)"
if inside_container; then
  detail "inside the container"
else
  detail "on the host"
fi
echo

first_unsatisfied=""

for stage in $ROUTE_SCRIPTS; do
  "$HERE/$stage" >/dev/null 2>&1
  stage_exit=$?

  case "$stage_exit" in
    0) label="${GREEN}done${RESET}    " ;;
    1) label="${RED}blocked${RESET} " ;;
    2) label="${AMBER}waiting${RESET} " ;;
    3) label="${DIM}n/a here${RESET}" ;;
    *) label="?       " ;;
  esac

  printf '  %s  %-16s %s%s%s\n' "$label" "$stage" "$DIM" "$(route_title "$stage")" "$RESET"

  # Exit 3 is the other machine's business, not an outstanding item on this one.
  if [ -z "$first_unsatisfied" ] && [ "$stage_exit" != 0 ] && [ "$stage_exit" != 3 ]; then
    first_unsatisfied="$stage"
  fi
done

echo
if [ -n "$first_unsatisfied" ]; then
  printf 'Run this for the detail:\n'
  run_hint "$first_unsatisfied"
  exit 1
fi

printf '%sEvery stage this machine can answer for is satisfied.%s\n' "$GREEN" "$RESET"
detail "A stage marked 'n/a here' is answered on the other machine — host vs container."
