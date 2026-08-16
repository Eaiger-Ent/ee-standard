#!/usr/bin/env bash
# Runs on container create (postCreateCommand).
#
# Deliberately short. Per docs/03-devcontainer.md, anything long enough to need
# sectioning is doing work that belongs in the image or a pinned feature.
# Everything installable here is a feature; what remains is wiring.
set -euo pipefail

# The named volume mounts root-owned on first create.
sudo chown -R vscode:vscode /home/vscode/.claude

# markdownlint-cli2 at the version the register records for DOC-001, so the
# editor and CI cannot disagree about what the control means (theme T-2).
# Change this and the CI pin together, never one alone.
npm install -g markdownlint-cli2@0.23.2

# The host ~/.gitconfig may name a Homebrew gh path that does not exist here.
GH_BIN="$(command -v gh)"
for host in github.com gist.github.com; do
  git config --global --unset-all "credential.https://${host}.helper" || true
  git config --global --add "credential.https://${host}.helper" \
    "!${GH_BIN} auth git-credential"
done

echo "✓ setup complete"
