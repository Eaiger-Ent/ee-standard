#!/usr/bin/env bash
# Runs on container create (postCreateCommand).
#
# Deliberately short. Per docs/03-devcontainer.md, anything long enough to need
# sectioning is doing work that belongs in the image or a pinned feature.
# Everything installable here is a feature; what remains is wiring.
set -euo pipefail

# The named volume mounts root-owned on first create.
sudo chown -R vscode:vscode /home/vscode/.claude

# The claude-code feature runs `npm install -g` as root, so the package tree it
# writes is root-owned while the container's user is vscode (BLD-001) — and
# `claude update` then fails with "Insufficient permissions to install update"
# on a release cadence of roughly one a day. Hand the one package it owns to
# vscode; the surrounding node_modules and bin are already group-writable.
for d in /usr/local/share/nvm/versions/node/*/lib/node_modules/@anthropic-ai; do
  [ -d "$d" ] && sudo chown -R vscode:vscode "$d"
done

# DOC-001's tool, from the one authority that owns its version:
# package-lock.json. Every locus runs `npx markdownlint-cli2`, so there is no
# version to keep in step here — the lockfile is the pin, and SUP-001 already
# enforces that it is committed and installed frozen.
npm ci --no-audit --no-fund

# uv bootstraps the Python environment, so it cannot come from it — its
# version is a literal at each locus, kept in step by Renovate rather than by
# a human remembering. See controls.yaml `tools:`.
# renovate: datasource=pypi depName=uv
pip install --quiet uv==0.12.5
uv sync --frozen
uv run pre-commit install

# gitleaks at SEC-001's shared pin, verified by checksum (a pinned release
# artefact — preference 3 in docs/03-devcontainer.md). Same version as CI.
# renovate: datasource=github-releases depName=gitleaks/gitleaks
GITLEAKS_VERSION=8.30.1
case "$(uname -m)" in
  aarch64|arm64) GL_ARCH=arm64 GL_SHA=e4a487ee7ccd7d3a7f7ec08657610aa3606637dab924210b3aee62570fb4b080 ;;
  *)             GL_ARCH=x64   GL_SHA=551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb ;;
esac
curl -sSfL -o /tmp/gitleaks.tgz \
  "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_${GL_ARCH}.tar.gz"
echo "${GL_SHA}  /tmp/gitleaks.tgz" | sha256sum -c --quiet -
tar -xzf /tmp/gitleaks.tgz -C /tmp gitleaks
sudo install /tmp/gitleaks /usr/local/bin/gitleaks
rm /tmp/gitleaks.tgz /tmp/gitleaks

# The host ~/.gitconfig may name a Homebrew gh path that does not exist here.
GH_BIN="$(command -v gh)"
for host in github.com gist.github.com; do
  git config --global --unset-all "credential.https://${host}.helper" || true
  git config --global --add "credential.https://${host}.helper" \
    "!${GH_BIN} auth git-credential"
done

# A second PAT for the EqualExperts org, scoped per invocation. The wrapper is a
# reviewed file rather than a heredoc — it is an executable that lands on PATH,
# so it belongs in a diff and under the same gates as the rest of the repo.
sudo install -m 0755 .devcontainer/bin/gh-ee-skills /usr/local/bin/gh-ee-skills

# The ee-skills plugins this repo's workflow depends on (docs/02-skill-family.md).
# Plugin state lives in the ~/.claude volume, so this only does work on a fresh
# volume. The marketplace repo is private to the EqualExperts org, so both the
# add and the installs run under the second PAT — the ambient GITHUB_TOKEN is
# Eaiger-Ent-scoped and cannot clone it.
if [ -n "${EE_SKILLS_GITHUB_TOKEN:-}" ]; then
  if ! claude plugin marketplace list 2>/dev/null | grep -q "EqualExperts/ee-skills"; then
    GITHUB_TOKEN="${EE_SKILLS_GITHUB_TOKEN}" GH_TOKEN="${EE_SKILLS_GITHUB_TOKEN}" \
      claude plugin marketplace add EqualExperts/ee-skills
  fi
  installed="$(claude plugin list 2>/dev/null || true)"
  for plugin in adr-toolkit lint-md devcontainer-check skill-preflight ee-skills-manage clarify-all; do
    echo "${installed}" | grep -q "${plugin}@ee-skills" && continue
    GITHUB_TOKEN="${EE_SKILLS_GITHUB_TOKEN}" GH_TOKEN="${EE_SKILLS_GITHUB_TOKEN}" \
      claude plugin install "${plugin}@ee-skills"
  done
else
  echo "⚠ EE_SKILLS_GITHUB_TOKEN not set — skipping ee-skills plugin install" >&2
fi

echo "✓ setup complete"
