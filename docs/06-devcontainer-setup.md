# Setting up the devcontainer

**Do this before anything else.** All development on this repository happens
inside the devcontainer. Nothing in Phase 1 should be written on a host
toolchain.

[`03-devcontainer.md`](03-devcontainer.md) specifies *what* the clean
devcontainer is and why. This document is the operator's half: the host values
you must set first, the files to create, and how to verify the result.

## Why this is step zero, not Phase 2

[`04-build-plan.md`](04-build-plan.md) places the devcontainer template in
Phase 2, alongside the gates. That is right for the **template** — the artefact
this repo ships to consumers. It is wrong for **this repo's own environment**,
for two reasons:

**Phase 1 is development work.** Building `standard-check` means writing and
running Python. If that happens on a host toolchain, the first thing the
standard repo does is violate the premise it exists to enforce.

**Phase 1's own exit criterion already requires it.** The last criterion reads
*"The checker's own repo passes every control it can verify locally"*, and calls
it "the real gate". DEV-001 is one of those controls. A repo with no
`.devcontainer/` cannot pass DEV-001, so Phase 1 cannot close without the
devcontainer existing. Deferring it to Phase 2 makes Phase 1 unclosable by its
own terms.

So the sequence is: **build this repo's devcontainer → Phase 1 → Phase 2
generalises it into the shipped template**. Phase 2 still owns the template;
it now has a working reference to generalise from rather than a specification
to implement blind.

## 1 — Host prerequisites (macOS)

| Requirement | Verify with | Notes |
| --- | --- | --- |
| Docker Desktop or OrbStack, running | `docker info` | Any runtime the Dev Containers extension can reach |
| VS Code + **Dev Containers** extension | search `ms-vscode-remote.remote-containers` | |
| Claude Code on the host | `claude --version` | Needed once, to mint the token in step 2 |
| `security` CLI | built into macOS | Reads and writes Keychain entries |
| `devcontainer` CLI | `devcontainer --version` | `npm i -g @devcontainers/cli` — needed to generate the lock file in step 4 |

Apple Silicon and Intel both work. Give Docker Desktop **8 GB** of memory
(Settings → Resources → Memory); the default is tight once a Python toolchain
and a node toolchain are both installed.

## 2 — The macOS Keychain values

`initializeCommand` runs `.devcontainer/fetch-secrets.sh` **on the host**. It
reads each secret with `security find-generic-password -a "$USER" -s <NAME> -w`
and writes the resolved values to `.devcontainer/.env`, which `runArgs` passes
into the container via `--env-file`.

This is the "secrets fetched, never committed" pattern from
[`03-devcontainer.md`](03-devcontainer.md). The `.env` is gitignored, so SEC-001
has nothing to find.

Service names are **generic**, with no repo prefix, so one host-side credential
store serves every ee project on the machine.

### Required

| Keychain service | Container variable | Purpose |
| --- | --- | --- |
| `CLAUDE_OAUTH_TOKEN` | `CLAUDE_CODE_OAUTH_TOKEN` | Claude Code auth on subscription billing |

Without it `fetch-secrets.sh` exits `1` and **the container never builds**. Set
it before your first "Reopen in Container":

```bash
claude setup-token          # on the Mac; prints sk-ant-oat01-...

security add-generic-password -a "$USER" -s "CLAUDE_OAUTH_TOKEN" \
  -w "sk-ant-oat01-..."
```

### Optional

| Keychain service | Container variable(s) | Purpose |
| --- | --- | --- |
| `GITHUB_TOKEN` | `GITHUB_TOKEN` | Authenticates `gh` and git without an interactive `gh auth login` |
| `GIT_AUTHOR_NAME` | `GIT_AUTHOR_NAME`, `GIT_COMMITTER_NAME` | Pre-configures the container's git identity |
| `GIT_AUTHOR_EMAIL` | `GIT_AUTHOR_EMAIL`, `GIT_COMMITTER_EMAIL` | As above |

```bash
security add-generic-password -a "$USER" -s "GITHUB_TOKEN"     -w "ghp_..."
security add-generic-password -a "$USER" -s "GIT_AUTHOR_NAME"  -w "Your Name"
security add-generic-password -a "$USER" -s "GIT_AUTHOR_EMAIL" \
  -w "you@equalexperts.com"
```

`add-generic-password` will not overwrite. To rotate a value, delete first:

```bash
security delete-generic-password -a "$USER" -s "GITHUB_TOKEN"
security add-generic-password    -a "$USER" -s "GITHUB_TOKEN" -w "ghp_new..."
```

### Deliberately absent: `ANTHROPIC_API_KEY`

Setting `ANTHROPIC_API_KEY` in the container makes Claude Code switch from OAuth
to API billing, silently bypassing the subscription. This repo has no runtime
Anthropic client, so the variable has no legitimate use here — do not add it.

A project that *does* need one (a web app, say) must inject it under a different
name, so that Claude Code never sees `ANTHROPIC_API_KEY` in its environment.

### Per-project overrides

Every lookup tries `<REPO_SLUG>_<NAME>` before the generic `<NAME>`, where the
slug is the **checkout directory name**, upper-snake-cased. For a checkout in
`ee-standard`, the prefix is `EE_STANDARD`:

```bash
# A different PAT for this project only:
security add-generic-password -a "$USER" -s "EE_STANDARD_GITHUB_TOKEN" \
  -w "ghp_..."
```

`fetch-secrets.sh` prints which key it resolved, so you can confirm the override
took effect.

## 3 — Create `.devcontainer/`

Six files. The image digest below was resolved on 2026-08-16 and is real —
verify it yourself with the command in step 5 before trusting it.

### `.devcontainer/devcontainer.json`

```jsonc
{
  "name": "ee-standard Dev Environment",

  // DEV-001 — the image is pinned by digest, not by floating tag. No lock file
  // covers images, so this is the one pin that must live inline.
  // mcr.microsoft.com/devcontainers/base:trixie, resolved 2026-08-16.
  "image": "mcr.microsoft.com/devcontainers/base:trixie@sha256:025b74bb5f7ac53edd77e01aa7188c359aab100e23a2f6220bde50bbb9fd31dd",

  // Features are pinned by devcontainer-lock.json (step 4), not here.
  "features": {
    "ghcr.io/devcontainers/features/github-cli:1": {},
    "ghcr.io/devcontainers/features/node:2": {},
    "ghcr.io/devcontainers/features/python:1": {
      "version": "3.13",
      "installTools": false
    },
    "ghcr.io/anthropics/devcontainer-features/claude-code:1": {}
  },

  "initializeCommand": "bash .devcontainer/fetch-secrets.sh",
  "runArgs": ["--env-file", ".devcontainer/.env"],
  "postCreateCommand": "bash .devcontainer/setup.sh",
  "postStartCommand": "bash .devcontainer/check-auth.sh",

  // BLD-001 — the container's final user is not root.
  "remoteUser": "vscode",

  "mounts": [
    "source=ee-standard-claude-home,target=/home/vscode/.claude,type=volume"
  ],

  "customizations": {
    "vscode": {
      "extensions": [],
      "settings": {
        "terminal.integrated.defaultProfile.linux": "zsh"
      }
    }
  }
}
```

Three things differ from the target file sketched in
[`03-devcontainer.md`](03-devcontainer.md), and each is a correction:

| Change | Why |
| --- | --- |
| `/home/vscode/.claude`, not `/home/node/` | `devcontainers/base` runs as `vscode`. `/home/node` only exists on the `javascript-node` image the predecessor used — the sketch carried the path over with the pattern. Mounting at `/home/node` would create a root-owned directory Claude Code never reads. |
| `"remoteUser": "vscode"` stated explicitly | BLD-001 is a Tier-1 control of this register. Relying on the image's default is exactly the "declared but unreachable" shape (T-3) the repo exists to catch. |
| Claude Code as a pinned **feature** | `03-devcontainer.md` ranks a version-pinned feature above `curl … \| sh`. `ghcr.io/anthropics/devcontainer-features/claude-code` is official and lock-file-covered, which removes one of the three pipes-to-shell and shortens `setup.sh`. |

Python `3.13` is the one genuinely open choice here — change it in this one
place if the checker should target something else. `installTools: false` keeps
the feature from installing an unpinned grab-bag of linters, which would
reintroduce the unversioned-global-install problem (T-2) the spec calls out.

### `.devcontainer/fetch-secrets.sh`

Runs on the **host**, before the container starts.

```bash
#!/usr/bin/env bash
# Runs on the host before container start. Fetches secrets from the macOS
# Keychain into .devcontainer/.env for injection via runArgs --env-file.
#
# Service names are generic (no per-repo prefix) so one host-side credential
# store is reused across projects. Prefix any name with the checkout directory
# in UPPER_SNAKE_CASE to override a single project: EE_STANDARD_GITHUB_TOKEN.
set -euo pipefail

echo "==> Fetching secrets from Keychain..."
: > .devcontainer/.env

PROJECT_PREFIX=$(basename "$PWD" | tr '[:lower:]-' '[:upper:]_')

# Tries ${PROJECT_PREFIX}_${1}, then ${1}. Sets LAST_SECRET_KEY to the hit.
fetch_secret() {
  local name="$1" prefixed="${PROJECT_PREFIX}_${1}" value
  value=$(security find-generic-password -a "$USER" -s "$prefixed" -w 2>/dev/null) || true
  if [ -n "$value" ]; then
    LAST_SECRET_KEY="$prefixed"; printf '%s' "$value"; return
  fi
  value=$(security find-generic-password -a "$USER" -s "$name" -w 2>/dev/null) || true
  LAST_SECRET_KEY="$name"; printf '%s' "$value"
}

CLAUDE_CODE_OAUTH_TOKEN=$(fetch_secret "CLAUDE_OAUTH_TOKEN")
if [ -z "$CLAUDE_CODE_OAUTH_TOKEN" ]; then
  echo "  ✗ No Claude Code OAuth token in Keychain."
  echo "    Run 'claude setup-token' on your Mac, then:"
  echo "      security add-generic-password -a \"\$USER\" \\"
  echo "        -s \"CLAUDE_OAUTH_TOKEN\" -w \"sk-ant-oat01-...\""
  exit 1
fi
echo "CLAUDE_CODE_OAUTH_TOKEN=${CLAUDE_CODE_OAUTH_TOKEN}" >> .devcontainer/.env
echo "  ✓ CLAUDE_CODE_OAUTH_TOKEN [${LAST_SECRET_KEY}]"

GITHUB_TOKEN=$(fetch_secret "GITHUB_TOKEN")
if [ -n "$GITHUB_TOKEN" ]; then
  echo "GITHUB_TOKEN=${GITHUB_TOKEN}" >> .devcontainer/.env
  echo "  ✓ GITHUB_TOKEN [${LAST_SECRET_KEY}]"
fi

GIT_AUTHOR_NAME=$(fetch_secret "GIT_AUTHOR_NAME")
if [ -n "$GIT_AUTHOR_NAME" ]; then
  {
    echo "GIT_AUTHOR_NAME=\"${GIT_AUTHOR_NAME}\""
    echo "GIT_COMMITTER_NAME=\"${GIT_AUTHOR_NAME}\""
  } >> .devcontainer/.env
  echo "  ✓ GIT_AUTHOR_NAME [${LAST_SECRET_KEY}]"
fi

GIT_AUTHOR_EMAIL=$(fetch_secret "GIT_AUTHOR_EMAIL")
if [ -n "$GIT_AUTHOR_EMAIL" ]; then
  {
    echo "GIT_AUTHOR_EMAIL=\"${GIT_AUTHOR_EMAIL}\""
    echo "GIT_COMMITTER_EMAIL=\"${GIT_AUTHOR_EMAIL}\""
  } >> .devcontainer/.env
  echo "  ✓ GIT_AUTHOR_EMAIL [${LAST_SECRET_KEY}]"
fi

echo "  ✓ Written to .devcontainer/.env"
```

### `.devcontainer/setup.sh`

Runs once, on container create. Deliberately short — per
[`03-devcontainer.md`](03-devcontainer.md), *"anything long enough to need
sectioning is doing work that belongs in the image or a feature."* Everything
installable is a pinned feature; what remains is wiring.

```bash
#!/usr/bin/env bash
# Runs on container create. Keep this short — installs belong in features.
set -euo pipefail

# The named volume mounts root-owned on first create.
sudo chown -R vscode:vscode /home/vscode/.claude

# markdownlint-cli2 at the version the register records, so the editor and CI
# cannot disagree about what DOC-001 means (theme T-2).
npm install -g markdownlint-cli2@0.23.2

# The host ~/.gitconfig may name a Homebrew gh path that does not exist here.
GH_BIN="$(command -v gh)"
for host in github.com gist.github.com; do
  git config --global --unset-all "credential.https://${host}.helper" || true
  git config --global --add "credential.https://${host}.helper" \
    "!${GH_BIN} auth git-credential"
done

echo "✓ setup complete"
```

Pin `markdownlint-cli2` to whatever version the register records for DOC-001,
and change both together. CI must install the same version — two unversioned
copies of one tool is the drift this repo exists to prevent.

### `.devcontainer/check-auth.sh`

Runs on **every** container start, so a rotated Keychain value takes effect on
restart rather than needing a full rebuild.

```bash
#!/usr/bin/env bash
# Runs on every container start. Re-sources .env, then reports auth state.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

# runArgs --env-file only applies at create; this hook makes restarts enough.
if [ -f "$ENV_FILE" ]; then
  set -a; . "$ENV_FILE"; set +a
  TMP=$(mktemp)
  cat > "$TMP" <<EOF
#!/bin/sh
# Auto-generated by .devcontainer/check-auth.sh — do not edit.
if [ -f "$ENV_FILE" ]; then set -a; . "$ENV_FILE"; set +a; fi
EOF
  sudo install -m 0644 -o root -g root "$TMP" /etc/profile.d/devcontainer-env.sh
  rm -f "$TMP"
fi

echo ""
echo "═══════════════ environment ═══════════════"

if gh auth status &>/dev/null; then
  echo "  ✓ GitHub CLI — authenticated"
elif [ -n "${GITHUB_TOKEN:-}" ]; then
  echo "  ✗ GitHub CLI — GITHUB_TOKEN set but rejected (expired? wrong scopes?)"
else
  echo "  ✗ GitHub CLI — not authenticated. Run: gh auth login"
fi

if [ -n "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]; then
  echo "  ✓ Claude Code — OAuth token present (subscription billing)"
else
  echo "  ✗ Claude Code — no OAuth token. See docs/06-devcontainer-setup.md"
fi

for tool in claude python3 node markdownlint-cli2; do
  if command -v "$tool" &>/dev/null; then
    echo "  ✓ ${tool} — $("$tool" --version 2>/dev/null | head -1)"
  else
    echo "  ✗ ${tool} — missing (re-run: bash .devcontainer/setup.sh)"
  fi
done

if git config user.email &>/dev/null; then
  echo "  ✓ git — $(git config user.name) <$(git config user.email)>"
else
  echo "  ✗ git — identity not configured"
fi

echo "═══════════════════════════════════════════"
echo ""
```

### `.devcontainer/claude-user-settings.json`

Seeded into the persistent volume on first create. Start empty and add settings
as they are justified:

```json
{}
```

### `.gitignore`

The repo has none yet. It needs, at minimum:

```gitignore
.devcontainer/.env
```

This is load-bearing, not hygiene — it is the half of the
"secrets fetched, never committed" pattern that does the *never committed* part.

## 4 — Build, and generate the lock file

```bash
cd ee-standard
chmod +x .devcontainer/*.sh
code .
# → "Reopen in Container"
```

First build takes several minutes. Then generate the lock file that DEV-001
requires — it is written by the CLI, never by hand:

```bash
devcontainer upgrade --workspace-folder .   # writes devcontainer-lock.json
git add .devcontainer/devcontainer-lock.json
```

Confirm it pins **every** feature named in `devcontainer.json` — four entries,
each with a `resolved` digest. A lock file that covers three of four features
reads as solved and is not.

## 5 — Verify the pins are real

Both halves of DEV-001, checked independently of any tool that might be wrong
in the same direction:

```bash
# The image digest in devcontainer.json matches what the registry serves
curl -sI \
  -H "Accept: application/vnd.oci.image.index.v1+json" \
  -H "Accept: application/vnd.docker.distribution.manifest.list.v2+json" \
  https://mcr.microsoft.com/v2/devcontainers/base/manifests/trixie \
  | grep -i docker-content-digest

# The image reference contains a digest at all
grep -q '@sha256:' .devcontainer/devcontainer.json && echo "image pinned"

# The lock file exists and names every feature
grep -c '"resolved"' .devcontainer/devcontainer-lock.json   # expect 4
```

For reference, the feature digests resolved on 2026-08-16:

| Feature | Version | Digest |
| --- | --- | --- |
| `devcontainers/features/github-cli` | 1.1.0 | `sha256:d22f50b70ed75339b4eed1ba9ecde3a1791f90e88d37936517e3bace0bbad671` |
| `devcontainers/features/node` | 2.1.0 | `sha256:8c0de46939b61958041700ee89e3493f3b2e4131a06dc46b4d9423427d06e5f6` |
| `devcontainers/features/python` | 1.8.0 | `sha256:fbcad6955caeecc5ad3f7886baf652e25cba5225a6c4c2287c536de2e5607511` |
| `anthropics/devcontainer-features/claude-code` | 1.0.5 | `sha256:cfc2e7d3e9fd3b9b01f8d5cb158508a884c8c0ede2e23ed10f32dea5d4ffe69a` |

The `github-cli` digest matches the one already quoted in
[`03-devcontainer.md`](03-devcontainer.md), which is a useful independent
confirmation that the resolution method is sound.

## What survives a rebuild

One named volume, `ee-standard-claude-home`, mounted at `/home/vscode/.claude`.
It holds Claude Code's auth, memory and plugin state, so a rebuild does not
start with a re-authentication ritual — and rituals get skipped.

Everything else is reproducible from pinned inputs, which is the point. If
losing it on rebuild hurts, it either belongs in a volume or should never have
been created by hand.

## Troubleshooting

### The build stops at "Running the initializeCommand" with no further logs

`fetch-secrets.sh` exited `1` — no `CLAUDE_OAUTH_TOKEN` in the Keychain. Run it
directly on the host to see the message:

```bash
bash .devcontainer/fetch-secrets.sh
```

### `403 Write access to repository not granted`, or a spurious `404`

The injected `GITHUB_TOKEN` **shadows** `gh auth login`. Both `gh` and git's
credential helper prefer the environment variable, so you authenticate as the
Keychain PAT regardless of what you configured inside the container. The errors
read as *the repo does not exist* or *you lack admin* — never as *wrong
identity*.

Check it first whenever a permission error does not match the access you believe
you have:

```bash
env -u GITHUB_TOKEN gh auth status
env -u GITHUB_TOKEN git push
```

This was confirmed against `Eaiger-Ent/ee-standard` on 2026-08-16, where it
presented as `404` then `403`. Fix it by widening the PAT's scope or removing
the Keychain entry and relying on `gh auth login`, which persists in the volume.

It is also a live instance of theme **T-5** — the credential boundary least
defended — arriving as a support question rather than as a breach, which is the
usual way.

### A tool is missing after a rebuild

```bash
bash .devcontainer/setup.sh
```

If it is missing *repeatedly*, it is being installed by the wrong mechanism.
Promote it to a pinned feature rather than adding a retry.

## Known gap in DEV-001

[`03-devcontainer.md`](03-devcontainer.md) states that DEV-001 "verifies both
halves: `devcontainer-lock.json` present *and* the image reference containing an
`@sha256:` digest." The register does not yet say that — `controls.yaml`
DEV-001 `enforces` covers only the lock file:

> `.devcontainer/devcontainer-lock.json` exists and pins every feature
> referenced by `devcontainer.json` to a resolved digest.

As written, a repo with a complete lock file and a floating `image` tag passes
DEV-001 — which `03-devcontainer.md` identifies as "the more dangerous of the
two states, because the lock file's existence makes it look solved."

That is theme **T-1** (a stated standard that nothing enforces) inside the
register itself. It should be closed by amending the DEV-001 `enforces` text
and its assertions before Phase 1 treats the control as implemented, not by
relying on this document to describe the intent.
