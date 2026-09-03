#!/usr/bin/env bash
# The whole route, and where you are on it. Runs every stage quietly and reports
# the first one that is not satisfied — that is the one to run for its detail.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; . "$HERE/_lib.sh"

printf 'Adoption route — %s\n' "$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")"
if in_container; then note "inside the container"; else note "on the host"; fi
echo

first_open=""
for stage in $ROUTE_SCRIPTS; do
  "$HERE/$stage" >/dev/null 2>&1; rc=$?
  case "$rc" in
    0) mark="${_g}done${_n}    " ;;
    1) mark="${_r}blocked${_n} " ;;
    2) mark="${_y}waiting${_n} " ;;
    3) mark="${_d}n/a here${_n}" ;;
    *) mark="?       " ;;
  esac
  printf '  %s  %-16s %s%s%s\n' "$mark" "$stage" "$_d" "$(route_title "$stage")" "$_n"
  if [ -z "$first_open" ] && [ "$rc" != 0 ] && [ "$rc" != 3 ]; then first_open="$stage"; fi
done

echo
if [ -n "$first_open" ]; then
  printf 'Run this for the detail:\n  ./%s\n' "$first_open"
  exit 1
fi
printf '%sEvery stage this machine can answer for is satisfied.%s\n' "$_g" "$_n"
note "A stage marked 'n/a here' is answered on the other machine — host vs container."
