#!/usr/bin/env bash
#
# Stage 4 — inside the container.
#
# What the adoption needs before it runs, and what the register says once it
# has. This stage refuses to run on the host: a host run once reported green
# about a uv version it was not using, which is the worst kind of answer.

set -uo pipefail
cd "$(dirname "$0")" || exit 1
. ./_lib.sh

if ! inside_container; then
  echo "This stage runs inside the container, and you are on your Mac."
  detail "§ 5 of START-HERE.md is how you get a shell in there."
  exit 3
fi
cd "$(repository_root)" || exit 1

# --------------------------------------------------------------- the plugin

section "The plugin, again, in here (§ 5)"
if claude plugin list 2>/dev/null | grep -q control-register; then
  pass "control-register is installed in this container"
else
  fail "not installed — the container's ~/.claude is a volume, not your Mac's home" "5"
fi

# --------------------------------------------------------------- the checker

section "The checker (§ You are done when)"
if ! grep -q register-check pyproject.toml 2>/dev/null; then
  manual "not installed yet — the adoption step is what installs it" "5"
else
  pass "register-check is a dependency"

  if grep -q register-check uv.lock 2>/dev/null; then
    pass "and the lockfile records the pin"
  else
    fail "it is in pyproject.toml but not in the lockfile" "You are done when"
  fi
fi

# ----------------------------------------------------------------- the hooks

section "Hooks that actually run (§ When it goes wrong)"
for hook in pre-commit pre-push; do
  if [ -x ".git/hooks/$hook" ]; then
    pass ".git/hooks/$hook is installed"
  else
    fail ".git/hooks/$hook is not installed — a wired locus is not an installed hook" \
      "When it goes wrong"
  fi
done

# ------------------------------------------------------------------ the bots

section "The bots (§ 6)"
if [ -f renovate.json ]; then
  pass "renovate.json"
else
  manual "no renovate.json — uv stays pinned at today's version for ever without it" "6"
fi

if [ -f .github/dependabot.yml ]; then
  pass ".github/dependabot.yml"
else
  manual "no .github/dependabot.yml" "6"
fi

# ------------------------------------------------------------- the register

section "What the register says"
if ! installed uv || ! grep -q register-check pyproject.toml 2>/dev/null; then
  detail "register-check is not installed yet, so the register cannot report."
  verdict 40-adopt.sh ""
  exit $?
fi

report=/tmp/adopt-register-check.txt
uv run register-check >"$report" 2>&1
register_check_exit=$?

case "$register_check_exit" in
  0)
    pass "register-check exits 0"
    ;;
  3)
    pass "register-check exits 3 — nothing in violation, something unverified"
    detail "Permanent locally: SEC-003's remote blocks answer only inside an Actions job."
    ;;
  1)
    fail "register-check exits 1 — a real violation" \
      "Your first full report, and what each failure means"
    grep -E 'FAIL' "$report" 2>/dev/null | head -8 | while IFS= read -r line; do
      detail "$line"
    done
    ;;
  *)
    fail "register-check exits $register_check_exit" \
      "Your first full report, and what each failure means"
    ;;
esac
detail "full output: $report"

verdict 40-adopt.sh ""
