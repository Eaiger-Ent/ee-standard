#!/usr/bin/env bash
#
# Stage 2 — the platform.
#
# None of this is in a git clone, and two of the fifteen controls depend on it
# entirely. Finding out at step 3 that your plan cannot reach them wastes the
# four steps before it. Everything here reads; nothing here writes.

set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/_lib.sh"

if ! installed gh || ! gh auth status >/dev/null 2>&1; then
  echo "gh is not authenticated, so none of these questions can be asked."
  detail "00-preflight.sh settles that first."
  exit 3
fi
cd "$(repository_root)" || exit 1

# ------------------------------------------------------------ visibility, plan

section "Visibility and plan (§ D)"
visibility=$(gh api "repos/{owner}/{repo}" --jq .visibility 2>/dev/null || echo unknown)
case "$visibility" in
  public)
    pass "public — every control below is reachable"
    ;;
  private)
    detail "private — whether two controls are reachable depends on the plan"
    ;;
  *)
    fail "cannot read this repository's visibility" "E"
    verdict 20-platform.sh ""
    exit 1
    ;;
esac

if gh api "repos/{owner}/{repo}/rulesets" >/dev/null 2>&1; then
  rulesets_available=yes
  pass "rulesets are available on this plan"
else
  rulesets_available=no
  fail "rulesets are not available — CI-001 and SEC-001's remote block cannot hold" \
    "If your plan has no rulesets"
  detail "Thirteen of fifteen controls still hold. That section says what to record."
fi

# ------------------------------------------------------------- push protection

section "Secret-scanning push protection (§ 3)"
push_protection=$(gh api "repos/{owner}/{repo}" \
  --jq '.security_and_analysis.secret_scanning_push_protection.status' 2>/dev/null || echo unknown)

case "$push_protection" in
  enabled)
    pass "enabled — the only stop that is not on a contributor's machine"
    ;;
  disabled)
    manual "disabled — a setting in the browser, and nothing here can turn it on" "3"
    ;;
  *)
    if [ "$rulesets_available" = no ]; then
      detail "not offered on this plan for a private repository — nothing you have failed to do"
    else
      manual "cannot read the push protection status" "3"
    fi
    ;;
esac

# --------------------------------------------------------------- default branch

section "The default branch, as GitHub enforces it (§ 3)"
default_branch=$(gh api "repos/{owner}/{repo}" --jq .default_branch 2>/dev/null || echo "")
if [ -z "$default_branch" ]; then
  fail "cannot read the default branch" "3"
else
  detail "default branch: $default_branch  (looked up, not assumed — {branch} would resolve to yours)"

  is_protected=$(gh api "repos/{owner}/{repo}/branches/$default_branch" --jq .protected 2>/dev/null || echo unknown)
  ruleset_names=$(gh api "repos/{owner}/{repo}/rulesets" --jq '[.[].name] | join(", ")' 2>/dev/null || echo "")

  if [ "$is_protected" = true ]; then
    pass "protected — rulesets: ${ruleset_names:-none named}"
  else
    detail "not protected yet, which is expected before § 5. /gate-repo applies it, not this script."
  fi
fi

verdict 20-platform.sh 25-credentials.sh
