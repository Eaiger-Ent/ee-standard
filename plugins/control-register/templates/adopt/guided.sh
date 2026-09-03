#!/usr/bin/env bash
#
# The guided route: § B, then § C, then § C2, then § D, then a stop for § E.
#
# THIS ONE ACTS. Every other script here reads and reports; this asks questions
# and creates things — a directory, a repository, a project skeleton. It is the
# exception ADR 0049 revision 2 records, and it is kept honest one way: every
# *check* it makes is one of the numbered stage scripts, run and interpreted.
# It never re-implements a check, so there is one copy of each.
#
# It stops at § E because tokens are made in a browser, by you.

set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/_lib.sh"

if inside_container; then
  echo "This is the host route, and you are inside the container."
  detail "§ 5 of START-HERE.md is where the container part begins."
  exit 3
fi

# Reads come from the terminal, never from stdin: this script may have arrived
# down a pipe, in which case stdin is the script itself.
if [ ! -r /dev/tty ]; then
  echo "No terminal to ask questions on. Run this from an interactive shell."
  exit 1
fi

ask() {
  local prompt="$1" default="${2:-}" answer=""
  if [ -n "$default" ]; then
    printf '%s [%s]: ' "$prompt" "$default" > /dev/tty
  else
    printf '%s: ' "$prompt" > /dev/tty
  fi
  IFS= read -r answer < /dev/tty || answer=""
  printf '%s' "${answer:-$default}"
}

confirm() {
  local prompt="$1" answer=""
  printf '%s [y/N]: ' "$prompt" > /dev/tty
  IFS= read -r answer < /dev/tty || answer="n"
  case "$answer" in [yY]*) return 0 ;; *) return 1 ;; esac
}

banner() {
  printf '\n%s──%s %s %s──%s\n' "$DIM" "$RESET" "$1" "$DIM" "$RESET"
}

# ------------------------------------------------------------------ § A and § B

banner "Tools (§ A, § B)"
"$HERE/00-tools.sh"
tools_exit=$?

# Three different answers, and treating them alike was a real complaint: a run
# with every tool present stopped on "install what is missing", which named
# nothing because nothing was missing.
case "$tools_exit" in
  0)
    ;;
  1)
    echo
    echo "The ✗ lines above are what to install. Nothing has been changed."
    exit 1
    ;;
  2)
    echo
    echo "Nothing is missing. The • lines above are a setting or a choice, and none"
    echo "of them stops what follows."
    if ! confirm "Carry on?"; then
      echo "Stopped. Nothing has been changed."
      exit 1
    fi
    ;;
  *)
    echo
    echo "00-tools.sh could not answer from here (exit $tools_exit)."
    echo "Nothing has been changed."
    exit 1
    ;;
esac

# --------------------------------------------------------------------- § C

banner "Where the project lives (§ C)"

base_directory=$(ask "Base directory — where you keep projects" "$HOME/git")
base_directory=${base_directory/#\~/$HOME}

if [ ! -d "$base_directory" ]; then
  if confirm "$base_directory does not exist. Create it?"; then
    mkdir -p "$base_directory"
  else
    echo "Nothing created. Re-run when you have chosen a directory."
    exit 1
  fi
fi

project_name=$(ask "Project name — this becomes the repository name")
if [ -z "$project_name" ]; then
  echo "A name is needed. Nothing has been changed."
  exit 1
fi

project_path="$base_directory/$project_name"
github_account=$(gh api user --jq .login 2>/dev/null || echo "")
remote_exists=no
if [ -n "$github_account" ] && gh repo view "$github_account/$project_name" >/dev/null 2>&1; then
  remote_exists=yes
fi

echo
detail "local directory : $project_path $([ -d "$project_path" ] && echo '(exists)' || echo '(does not exist)')"
detail "on GitHub       : $([ "$remote_exists" = yes ] && echo "yes — $github_account/$project_name" || echo 'no')"

# The four situations § C's table names, decided from what was just read rather
# than from what the reader believes. Running the wrong one of these is the
# mistake § C warns about, so it is not offered as a choice.
if [ "$remote_exists" = yes ] && [ ! -d "$project_path" ]; then
  echo
  echo "It is on GitHub and not here. Cloning it — never recreating it."
  gh repo clone "$github_account/$project_name" "$project_path" || exit 1

elif [ "$remote_exists" = yes ] && [ -d "$project_path" ]; then
  echo
  detail "Both exist. Using what is here; nothing created."

elif [ -d "$project_path" ] && git -C "$project_path" rev-parse --git-dir >/dev/null 2>&1; then
  echo
  echo "A local repository with nothing on GitHub."
  visibility=$(ask "Visibility — private or public" "private")
  if confirm "Publish $project_name as $visibility?"; then
    ( cd "$project_path" && gh repo create "$project_name" "--$visibility" \
        --source=. --remote=origin --push ) || exit 1
  fi

else
  echo
  echo "Neither exists. Creating both."
  visibility=$(ask "Visibility — private or public" "private")
  if ! confirm "Create $project_path and $github_account/$project_name as $visibility?"; then
    echo "Nothing created."
    exit 1
  fi
  mkdir -p "$project_path"
  ( cd "$project_path" \
    && git init -b main -q \
    && git commit -q --allow-empty -m "Initial commit" \
    && gh repo create "$project_name" "--$visibility" --source=. --remote=origin --push ) || exit 1
fi

cd "$project_path" || exit 1
echo
pass "standing in $project_path"

# -------------------------------------------------------------------- § C2

banner "A project for the gates to gate (§ C2)"
if [ -f pyproject.toml ]; then
  detail "pyproject.toml is already here — nothing to create."
else
  echo "This standard cannot be adopted by an empty repository: three controls"
  echo "need a project, a lockfile and a passing test before they mean anything."
  if confirm "Create the smallest project that satisfies all three?"; then
    uv init --name "$(basename "$PWD" | tr '_' '-')" --python 3.14
    uv add --dev pytest
    mkdir -p tests
    printf 'def test_it_runs() -> None:\n    assert True\n' > tests/test_smoke.py
    git add pyproject.toml uv.lock .python-version tests/
    pass "created, and staged — not committed"
  else
    detail "Skipped. § 5 will stop, having written nothing, until this exists."
  fi
fi

# --------------------------------------------------------------------- § D

banner "What your plan supports (§ D)"
"$HERE/20-platform.sh" || true

# --------------------------------------------------------------------- § E

banner "Credentials (§ E) — your turn"
cat <<'MSG'

The next part cannot be scripted. Two tokens are made in a browser, by you, and
one of them decides what every gate can reach:

  START-HERE.md § E                        which tokens, and what each is for
  START-HERE.md § Creating the GitHub token the fields and the exact permissions

Make them, put them in the Keychain as § E says, and then come back.
MSG

echo
if confirm "Done that — check what the Keychain holds now?"; then
  "$HERE/25-credentials.sh" || true
else
  detail "When you have, run: ./25-credentials.sh"
fi

# ------------------------------------------------------------------- handover

banner "Where you are"
"$HERE/status.sh" || true
echo
detail "The container is § 4, and the adoption itself is § 5. Both are in START-HERE.md."
