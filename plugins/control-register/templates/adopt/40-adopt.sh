#!/usr/bin/env bash
# Stage 4 — inside the container. What /register-adopt needs before it runs,
# and what register-check says once it has.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; . "$HERE/_lib.sh"

if ! in_container; then
  echo "This stage runs inside the container, and you are on your Mac."
  note "§ 5 of START-HERE.md is how you get a shell in there."
  note "A host run reports green about a uv version it is not using."
  exit 3
fi
cd "$(git rev-parse --show-toplevel 2>/dev/null || echo .)" || exit 1

head_ "The plugin, again, in here (§ 5)"
if claude plugin list 2>/dev/null | grep -q control-register; then
  ok "control-register is installed in this container"
else
  bad "not installed — the container's ~/.claude is a volume, not your Mac's home" "5"
fi

head_ "The checker (§ You are done when)"
if grep -q register-check pyproject.toml 2>/dev/null; then
  ok "register-check is a dependency"
  if grep -q register-check uv.lock 2>/dev/null; then
    ok "and the lockfile records the pin"
  else
    bad "it is in pyproject.toml but not in the lockfile" "You are done when"
  fi
else
  wait_on "not installed yet — the adoption step is what installs it" "5"
fi

head_ "Hooks that actually run (§ When it goes wrong)"
for hook in pre-commit pre-push; do
  if [ -x ".git/hooks/$hook" ]; then
    ok ".git/hooks/$hook is installed"
  else
    bad ".git/hooks/$hook is not installed — a wired locus is not an installed hook" "When it goes wrong"
  fi
done

head_ "The bots (§ 6)"
[ -f renovate.json ] && ok "renovate.json" || wait_on "no renovate.json — uv stays pinned for ever without it" "6"
[ -f .github/dependabot.yml ] && ok ".github/dependabot.yml" || wait_on "no dependabot.yml" "6"

head_ "What the register says"
if have uv && grep -q register-check pyproject.toml 2>/dev/null; then
  uv run register-check >/tmp/adopt-rc.txt 2>&1; rc=$?
  case "$rc" in
    0) ok "register-check exits 0" ;;
    3) ok "register-check exits 3 — nothing in violation, something unverified"
       note "Permanent locally: SEC-003's remote blocks answer only inside an Actions job." ;;
    1) bad "register-check exits 1 — a real violation" "Your first full report, and what each failure means"
       grep -E 'FAIL' /tmp/adopt-rc.txt 2>/dev/null | head -8 | while IFS= read -r l; do note "$l"; done ;;
    *) bad "register-check exits $rc" "Your first full report, and what each failure means" ;;
  esac
  note "full output: /tmp/adopt-rc.txt"
else
  note "register-check is not installed yet, so the register cannot report."
fi

verdict 40-adopt.sh ""
