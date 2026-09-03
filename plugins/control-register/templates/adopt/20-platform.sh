#!/usr/bin/env bash
# Stage 2 — the platform. None of this is in a git clone, and two of the
# fifteen controls depend on it. It reads; it changes nothing.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; . "$HERE/_lib.sh"

if ! have gh || ! gh auth status >/dev/null 2>&1; then
  echo "gh is not authenticated, so nothing here can be asked."
  note "00-preflight.sh settles that first."
  exit 3
fi
cd "$(git rev-parse --show-toplevel 2>/dev/null || echo .)" || exit 1

head_ "Visibility and plan (§ D)"
vis=$(gh api "repos/{owner}/{repo}" --jq .visibility 2>/dev/null || echo unknown)
case "$vis" in
  public)  ok "public — every control below is reachable" ;;
  private) note "private — whether two controls are reachable depends on the plan" ;;
  *)       bad "cannot read this repository's visibility" "E"; verdict 20-platform.sh ""; exit 1 ;;
esac

rulesets_ok=no
if gh api "repos/{owner}/{repo}/rulesets" >/dev/null 2>&1; then
  rulesets_ok=yes
  ok "rulesets are available on this plan"
else
  bad "rulesets are not available — CI-001 and SEC-001's remote block cannot hold" "If your plan has no rulesets"
  note "Thirteen of fifteen controls still hold. That section says what to record."
fi

head_ "Secret-scanning push protection (§ 3)"
pp=$(gh api "repos/{owner}/{repo}" --jq '.security_and_analysis.secret_scanning_push_protection.status' 2>/dev/null || echo unknown)
case "$pp" in
  enabled)  ok "enabled — the only stop that is not on a contributor's machine" ;;
  disabled) wait_on "disabled — a setting, and nothing here can turn it on" "3" ;;
  *)        if [ "$rulesets_ok" = no ]; then
              note "not offered on this plan for a private repository — nothing you have failed to do"
            else
              wait_on "cannot read push protection status" "3"
            fi ;;
esac

head_ "The default branch, as GitHub enforces it (§ 3)"
default=$(gh api "repos/{owner}/{repo}" --jq .default_branch 2>/dev/null || echo "")
if [ -z "$default" ]; then
  bad "cannot read the default branch" "3"
else
  note "default branch: $default  (looked up, not assumed — {branch} would resolve to yours)"
  protected=$(gh api "repos/{owner}/{repo}/branches/$default" --jq .protected 2>/dev/null || echo unknown)
  names=$(gh api "repos/{owner}/{repo}/rulesets" --jq '[.[].name] | join(", ")' 2>/dev/null || echo "")
  if [ "$protected" = true ]; then
    ok "protected — rulesets: ${names:-none named}"
  else
    note "not protected yet. Expected before § 5: /gate-repo applies the ruleset, not this script."
  fi
fi

verdict 20-platform.sh 30-container.sh
