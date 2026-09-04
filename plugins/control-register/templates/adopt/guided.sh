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
#: Fetched again inside the container at the end — the host's cache is not
#: mounted there, so the route has to arrive over the network a second time.
BOOTSTRAP_URL=https://raw.githubusercontent.com/Eaiger-Ent/ee-standard/main/adopt.sh

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

# --------------------------------------------------------------------- § 1

banner "The plugin (§ 1)"
if claude plugin list 2>/dev/null | grep -q "control-register@ee-standard"; then
  detail "control-register is already installed."
elif confirm "Install the control-register plugin? It touches no project"; then
  claude plugin marketplace add Eaiger-Ent/ee-standard
  claude plugin install control-register@ee-standard
else
  detail "Skipped. § 4 copies the devcontainer template out of it, so it is needed."
fi

# The plugin cache is versioned, and more than one version can be present — a
# glob would expand to all of them, which is a broken path rather than a newer
# one, and plain `sort` puts 0.1.0 above 0.10.0.
plugin_cache="$HOME/.claude/plugins/cache/ee-standard/control-register"
plugin_version=""
if [ -d "$plugin_cache" ]; then
  plugin_version=$(ls "$plugin_cache" | sort -V | tail -1)
fi

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

# --------------------------------------------------------------------- § 2

banner "The register (§ 2)"
if [ -f controls.yaml ]; then
  detail "controls.yaml is already here — nothing to fetch."
else
  echo "The plugin ships no register. The register is what you adopt, and it"
  echo "becomes yours the moment you edit it — so it is fetched into your"
  echo "repository rather than read from somewhere else."
  echo

  if confirm "Fetch the newest published register?"; then
    register_repo=https://github.com/Eaiger-Ent/ee-standard
    register_tag=$(git ls-remote --tags --refs "$register_repo" \
      | awk -F/ '{print $NF}' | sort -V | tail -1)

    if [ -z "$register_tag" ]; then
      echo "Could not resolve a tag — no network, or the repository moved."
      detail "§ 2 has the four lines to run by hand."
    else
      # controls.published.yaml, not controls.yaml: the register an adopter
      # takes is derived, with this repository's own entries removed
      # (ADR 0048). The tag it ships names that same tag.
      curl -fsSL -o controls.yaml \
        "https://raw.githubusercontent.com/Eaiger-Ent/ee-standard/${register_tag}/controls.published.yaml"
      git add controls.yaml
      echo "  fetched controls.yaml at ${register_tag}, and staged it"
      detail "It is yours now. § 3.7 of the reference is where you start editing it."
    fi
  else
    detail "Skipped. 10-repo.sh will keep reporting it, and § 5 needs it."
  fi
fi

echo
detail "Where the repository stands now:"
"$HERE/10-repo.sh" || true

# --------------------------------------------------------------------- § D

banner "What your plan supports (§ D)"
"$HERE/20-platform.sh" || true

# --------------------------------------------------------------------- § E

banner "Credentials (§ E) — your turn"
cat <<'MSG'

The next part cannot be scripted. The tokens are made in a browser, by you.

  START-HERE.md § E

That one section has both of them: which tokens, what each is for, the exact
fields and permissions, and the command that puts the result in the Keychain.

You only need the first one today. The second is CI's, it is not a Keychain
entry, and nothing before § 6 asks for it.
MSG

echo
if confirm "Done that — check what the Keychain holds now?"; then
  "$HERE/25-credentials.sh" || true
else
  echo "  When you have, run:"
  run_hint 25-credentials.sh
fi

# --------------------------------------------------------------------- § 4

banner "The container (§ 4)"
if [ -d .devcontainer ]; then
  detail ".devcontainer is already here — nothing copied."
elif [ -z "$plugin_version" ]; then
  echo "The plugin cache is empty, so there is no template to copy."
  detail "§ 1 installs it. § 4 has the steps if you would rather do it by hand."
elif ! [ -f controls.yaml ]; then
  echo "No controls.yaml, and the uv version and digest are read out of it."
  detail "§ 2 is where the register comes from."
elif confirm "Copy the devcontainer template and substitute it?"; then
  template="$plugin_cache/$plugin_version/templates/devcontainer"
  cp -R "$template" .devcontainer

  # Its README explains the placeholders, so while it is there the "any
  # placeholders left?" check below can never come back clean.
  rm -f .devcontainer/README.md

  uv_block() { sed -n '/^  uv:/,/^  [a-z-]*:$/p' controls.yaml; }
  uv_version=$(uv_block | sed -n 's/^ *version: *"\{0,1\}\([0-9][^"]*\)"\{0,1\} *$/\1/p')
  uv_sha_x86=$(uv_block | sed -n 's/^ *sha256: *//p')
  uv_sha_arm=$(curl -fsSL \
    "https://github.com/astral-sh/uv/releases/download/${uv_version}/uv-aarch64-unknown-linux-gnu.tar.gz.sha256" \
    | cut -d' ' -f1)

  # An extraction that quietly yields nothing is worse than one that errors: the
  # substitution writes emptiness over the placeholder and the build fails much
  # later at `sha256sum -c`, with nothing pointing back here.
  if [ -z "$uv_version" ] || [ -z "$uv_sha_x86" ] || [ -z "$uv_sha_arm" ]; then
    echo "  one of the three values came back empty — nothing substituted:"
    detail "version='$uv_version' x86='${uv_sha_x86:0:12}' aarch64='${uv_sha_arm:0:12}'"
    rm -rf .devcontainer
    detail "Removed the copy rather than leave a half-substituted one. § 4 by hand."
  else
    sed -i.bak -e "s/{{PROJECT_NAME}}/$(basename "$PWD")/g" .devcontainer/devcontainer.json
    sed -i.bak \
      -e "s/{{UV_VERSION}}/${uv_version}/g" \
      -e "s/{{UV_SHA256_X86_64}}/${uv_sha_x86}/g" \
      -e "s/{{UV_SHA256_AARCH64}}/${uv_sha_arm}/g" \
      .devcontainer/setup.sh
    rm -f .devcontainer/*.bak

    left=$(grep -rl '{{' .devcontainer 2>/dev/null || true)
    if [ -n "$left" ]; then
      echo "  a placeholder survived, in: $left"
      detail "That is what fails the build later at sha256sum -c. § 4 by hand."
    else
      echo "  .devcontainer copied and substituted — uv ${uv_version}"
    fi
  fi
else
  detail "Skipped. § 4 has the steps."
fi

echo
detail "Where the container stands now:"
"$HERE/30-container.sh" || true

echo
echo "Building it is one command and takes a few minutes. It needs"
echo "CLAUDE_OAUTH_TOKEN in the Keychain, which is the § E step above."
if [ -d .devcontainer ] && confirm "Build the container now?"; then
  devcontainer up --workspace-folder . --remove-existing-container
fi

# --------------------------------------------------------------------- § 6

banner "The bots (§ 6)"
if [ -f renovate.json ]; then
  detail "renovate.json is already here."
elif [ -z "$plugin_version" ]; then
  detail "No plugin cache to copy it from. § 6 has the step."
elif confirm "Copy the Renovate config? Without it, uv stays pinned for ever"; then
  cp "$plugin_cache/$plugin_version/templates/renovate/renovate.json" .
  git add renovate.json
  [ -f .github/dependabot.yml ] && git add .github/dependabot.yml
  echo "  renovate.json copied and staged"
  detail "Installing the Renovate app is yours, in a browser: § 6."
fi

# ------------------------------------------------------------------- handover

banner "Where you are"
"$HERE/status.sh" || true

# This script cd'd into the project. Your shell did not — a child process cannot
# move its parent — so a reader who follows a printed command straight after
# this runs it from wherever they started. That happened, and answered
# `zsh: no such file or directory`.
banner "Your shell is still where you started"
cat <<MSG

This ran in $project_path, but your terminal is not there. Before running
anything the route prints, go to the repository:

  cd $project_path

Every command the route prints already includes that line, because each stage
reads the repository you are standing in.
MSG

# The handover used to name § 4 and § 5 and stop. A reader who has got this far
# has been given commands at every step, and being handed a section number at
# the last one is where the momentum goes.
banner "What happens next (§ 5)"
cat <<MSG

Everything from here runs INSIDE the container. Four things, in order.

1. Get a shell in it. From your Mac:

  cd $project_path
  devcontainer exec --workspace-folder . bash

You are in when \`pwd\` prints a path beginning /workspaces. VS Code's
"Reopen in Container" and its built-in terminal do the same thing.

2. Install the plugin again, inside. This is not a mistake in § 1 and not a
mistake here: the container's ~/.claude is a named volume, not your Mac's home
directory, so what you installed on the host is not in it.

  claude plugin marketplace add Eaiger-Ent/ee-standard
  claude plugin install control-register@ee-standard

3. The route is on your Mac, and this is a different machine. ~/.cache is
not mounted into the container, so fetch the bootstrap again in there:

  curl -fsSL $BOOTSTRAP_URL -o /tmp/adopt.sh
  bash /tmp/adopt.sh status

That reports the stages this side can answer for — 40-adopt.sh is the one that
was "n/a here" on your Mac.

4. Run the adoption. It is a Claude Code session rather than a command:

  claude --permission-mode acceptEdits

The first run asks you to choose a login method, and that is not a failure. The
Keychain token is real and works — \`claude -p "say ok"\` answers using it — but
the interactive CLI also wants an account record, and a fresh config directory
has none. Choose the subscription account. It is asked once, not once per build.

Set the terminal interface at its prompt first, or you cannot select and copy
what it prints — and this step prints verdicts you will want:

  /tui default

Then, at the same prompt:

  /register-adopt --repo . --register ./controls.yaml
MSG

echo
detail "§ 4 and § 5 of START-HERE.md are the same steps, with the reasons."
