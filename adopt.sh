#!/usr/bin/env bash
#
# The bootstrap. This is the one file you fetch by hand; it gets the rest.
#
#   curl -fsSL https://raw.githubusercontent.com/Eaiger-Ent/ee-standard/main/adopt.sh -o adopt.sh
#   bash adopt.sh
#
# It needs nothing installed but git and curl, and no credentials: this
# repository is public, so the clone below is anonymous. That is the point —
# every other route into this standard needs Claude Code and a plugin first,
# and § B is exactly what a new adopter has not done yet.
#
#   bash adopt.sh          the guided route: § B, § C, § C2, § D, then § E
#   bash adopt.sh status   what still needs doing, and nothing else
#
# **This file is fetched from `main` and pins nothing** — it is four lines of
# fetching. What it clones IS pinned: the newest tag, which is the same version
# START-HERE.md § 2 tells you to take the register from.

set -euo pipefail

REPOSITORY=https://github.com/Eaiger-Ent/ee-standard
CACHE_ROOT="${XDG_CACHE_HOME:-$HOME/.cache}/ee-standard"

for required in git curl; do
  if ! command -v "$required" >/dev/null 2>&1; then
    echo "adopt.sh needs '$required' and it is not on PATH." >&2
    echo "START-HERE.md § B lists what to install and how." >&2
    exit 1
  fi
done

echo "Resolving the newest release..."
tag=$(git ls-remote --tags --refs "$REPOSITORY" | awk -F/ '{print $NF}' | sort -V | tail -1)
if [ -z "$tag" ]; then
  echo "Could not resolve a tag from $REPOSITORY — no network, or the repository moved." >&2
  exit 1
fi
echo "  $tag"

# One checkout per tag, reused on a second run. A tag is immutable, so a
# checkout that exists is already the right one and is not re-fetched.
checkout="$CACHE_ROOT/$tag"
if [ -d "$checkout/.git" ]; then
  echo "Using the checkout already at $checkout"
else
  mkdir -p "$CACHE_ROOT"
  echo "Fetching $tag into $checkout"
  git -c advice.detachedHead=false clone --depth 1 --branch "$tag" --quiet "$REPOSITORY" "$checkout"
fi

route="$checkout/plugins/control-register/templates/adopt"
if [ ! -d "$route" ]; then
  echo "The route is not in $tag — it lands in the release after this one." >&2
  echo "Follow START-HERE.md directly until then." >&2
  exit 1
fi

case "${1:-guided}" in
  status) exec "$route/status.sh" ;;
  guided) exec "$route/guided.sh" ;;
  *)      exec "$route/${1}" ;;
esac
