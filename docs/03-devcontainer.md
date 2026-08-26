# The clean devcontainer

The new repo needs a devcontainer built from scratch rather than inherited. This
document specifies what "clean" means, what it deliberately keeps from the
existing template, and what it fixes.

## Why not just copy the existing one

The `generate-ee-slides` devcontainer works, and its *structure* is good. Its
*content* is not portable. Read as ground truth, it carries four kinds of baggage:

| Baggage | Examples |
| --- | --- |
| Project identity | `"name": "generate-ee-slides Dev Environment"`, volume names `generate-ee-slides-uv-cache`, `ralph-wiggum-claude-home` |
| Project runtime | `TEST_DRIVE_FOLDER_ID`, `CLAUDE_GCP_PROJECT: ee-slides`, `CLAUDE_GCP_REGION` |
| Project toolchain | Python 3.14 via uv, OpenTofu, gcloud, graphviz, pnpm, LikeC4 on port 5173 |
| Project harness | The ralph-loop plugin set |

Copying it means the new repo starts by inheriting another project's assumptions
and then deleting them — which is how a "template" becomes a pile of settings
nobody can explain. Starting clean and adding back only what is justified is
cheaper and produces an explainable file.

## What is kept

Three structural patterns from the existing template are genuinely good and are
kept without change in shape:

**Secrets fetched, never committed.** `initializeCommand` runs a script that
fetches secrets into `.devcontainer/.env`, and derives `.devcontainer/.env.docker`
from it for `runArgs` to pass via `--env-file`. Both are gitignored. This is the
right shape: the container gets its secrets, the repository never holds them, and
SEC-001 has nothing to find.

The two files exist because two parsers read the same values and disagree about
quoting. The `.env` is sourced as shell by the start-up check, so a value
containing a space has to be quoted; `--env-file` does no shell parsing and would
read those quotes as part of the value. A template that fetches only tokens will
not notice, but one that fetches a person's name will. Derive the second file
from the first rather than writing both, so there is one fetch to keep correct.

**Auth verified on every start.** `postStartCommand` runs a check script that
reports which CLIs are present and authenticated. This is the same job the
existing `devcontainer-check` skill does interactively, and having it run
automatically on start is better than having to remember to ask.

**Persistent named volumes for credential state.** Claude Code auth and cloud
CLI config survive rebuilds. Without this, every rebuild is followed by a
re-authentication ritual, and rituals get skipped.

## What is fixed

### The base image is not pinned

The current file reads:

```jsonc
"image": "mcr.microsoft.com/devcontainers/javascript-node:24-trixie"
```

That is a floating tag. `devcontainer-lock.json` pins the *features* by digest —

```json
{
  "features": {
    "ghcr.io/devcontainers/features/github-cli:1": {
      "version": "1.1.0",
      "resolved": "ghcr.io/devcontainers/features/github-cli@sha256:d22f50b7…"
    }
  }
}
```

— but the lock file has no concept of the base image, so the largest single
input to the environment is the one thing left unpinned. Two engineers running
`devcontainer build` a month apart get different images, and neither can tell.

**Fix:** pin the image by digest in `devcontainer.json`, and let the automated
dependency updater (SUP-002) propose digest bumps as reviewable PRs. This is the
same discipline SUP-003 applies to CI actions, applied to the one image
everything else runs inside.

This is why control **DEV-001** verifies both halves: `devcontainer-lock.json`
present *and* the image reference containing an `@sha256:` digest. Pinning the
features while floating the image is the more dangerous of the two states,
because the lock file's existence makes it look solved.

### Setup installs by piping the internet into a shell

The current `setup.sh` installs uv, Claude Code, and OpenTofu with three
variations of `curl … | sh`, and adds an apt key by URL. Each fetches whatever
the vendor is serving at that moment.

`CLAUDE.md` in the predecessor already records the operational half of this
problem — *"Prefer apt-based installs over curl scripts for system tools — curl-based
installs have historically failed in this environment"* — which is the same
observation arriving as flakiness rather than as risk.

**Fix, in preference order:**

1. A devcontainer feature that **itself verifies what it installs**,
   version-pinned, so `devcontainer-lock.json` covers it.
2. A distribution package from a keyring installed by digest.
3. A pinned release artefact with a verified checksum.
4. `curl | sh` — only with a recorded justification and an expiry.

**Corrected 2026-08-18.** Rank 1 previously read "a devcontainer feature,
version-pinned", and that ranking was wrong in a way worth spelling out, because
it is the mistake the whole ladder exists to prevent.

`devcontainer-lock.json` pins the feature's **installer** by digest. It says
nothing about the artefact that installer then fetches. Both community features
available for the tools this repository installs — `uv` and `gitleaks` — were
measured on 2026-08-18: each `curl`s a GitHub release tarball and extracts it,
with no checksum, no signature and no attestation. A feature that does that is a
rank-4 install wearing a rank-1 badge, and adopting one would have replaced this
repository's checksum-verified gitleaks install with an unverified one while
appearing to strengthen provenance.

So a feature earns rank 1 only if it verifies its own download. Otherwise it
ranks where its install method ranks, and the lock file's digest is a fact about
the wrong artefact.

The new repo's `setup.sh` should install nothing unpinned and nothing
unverified. Length is a symptom worth watching — a long script usually means
installs that a feature or the image should own — but it is not the property:
a short script that pipes curl to a shell is worse than a long one that verifies
every artefact it fetches. `tests/test_devcontainer_setup.py` checks the
property; nothing checks the length.

### Global installs are unversioned

`npm install -g markdownlint-cli2` installs whatever is current. Meanwhile CI
installs its own copy, also unversioned. This is theme **T-2** — one definition
copied, then diverged — arriving as two tools with the same name and different
behaviour, and it is exactly the class of drift `locus` discipline exists to
prevent.

**Fix:** every tool a control depends on is installed at a pinned version, from
the version recorded in the register, at every locus. If the editor and CI cannot
agree on a version, the control is not deployable and should not be marked
`blocking`.

## The target file

Minimal, and honest about what it does not yet know:

```jsonc
{
  "name": "<repo> Dev Environment",

  // Pinned by digest — DEV-001. Bumps arrive as PRs via SUP-002.
  "image": "mcr.microsoft.com/devcontainers/base:trixie@sha256:<digest>",

  "features": {
    "ghcr.io/devcontainers/features/github-cli:1": {}
  },

  "initializeCommand": "bash .devcontainer/fetch-secrets.sh",
  "runArgs": ["--env-file", ".devcontainer/.env.docker"],
  "postCreateCommand": "bash .devcontainer/setup.sh",
  "postStartCommand": "bash .devcontainer/check-auth.sh",

  "mounts": [
    "source=<repo>-claude-home,target=/home/node/.claude,type=volume"
  ],

  "customizations": {
    "vscode": {
      "extensions": [],
      "settings": {
        "terminal.integrated.defaultProfile.linux": "zsh",
        "remote.autoForwardPorts": false
      }
    }
  }
}
```

Language toolchains are added as pinned features **when a language is actually
introduced**, not in anticipation. The predicate system in the register already
models this: a repo with no `*.tf` skips IAC-001, and by the same logic it has no
business installing OpenTofu.

**A pinned feature is not a pinned interpreter**, and the two are easy to
conflate — this repository did, and ran its gates on 3.13 locally and 3.14 in CI
until [ADR 0027](adr/0027-the-interpreter-is-a-pinned-tool.md). A feature pins
what the *image* installs; the interpreter that runs the gates is whatever the
project's resolver picks, and a support constraint like `requires-python`
selects nothing. The template's job is the first; a toolchain file at the
repository root — `.python-version`, `.nvmrc`, `.go-version` — is the second,
and nothing in `.devcontainer/` can stand in for it.

**The project environment belongs in the container layer**, not at the
repository root. A workspace folder is a bind mount, so a `.venv/` — or
`node_modules/`, or any other resolver-built tree — outlives the container that
built it and is stale the moment a feature version moves. The resolver's own
recovery is to delete and rebuild it, and that happens inside
`postCreateCommand`, which runs concurrently with the editor's extension host:
an extension that resolves the environment during that window finds nothing and
falls back to whatever it bundles, for the rest of the session. That is how the
editor locus comes to run an unpinned tool while pre-commit and CI run the
pinned one, with nothing reporting the divergence. Point the resolver
elsewhere — `UV_PROJECT_ENVIRONMENT` for uv — and name that path in the
editor's interpreter setting so the two cannot disagree. It does not close the
race on a fresh create, which nothing without a Dockerfile can; it removes the
stale half, which is the half that recurs on every rebuild.

**A feature you barely use still charges full price.** The ladder ranks *how* a
tool is installed, and it is worth asking first whether a feature is needed at
all. This repository listed `python:1` to obtain a `python3` that runs one line,
`pip install uv`, after which uv owns the environment and the feature's
interpreter is never used again — and in exchange took three extensions, two
editor settings and a second interpreter on `PATH`. uv is a static binary that
needs no Python and fetches the interpreter itself, so the feature buys nothing
that a checksum-verified release artefact does not
([ADR 0030](adr/0030-uv-is-bootstrapped-from-a-pinned-release.md)). Rank a
feature against what it costs, not only against how it installs.

**A feature pin governs installation, not configuration.** DEV-001 pins every
feature by digest, and a digest-pinned feature still contributes VS Code
extensions *and settings* that nobody in the adopting repository wrote —
`python:1` sets `[python].editor.defaultFormatter` to autopep8, which is not the
linter LNT-001 pins. The template does not fight this in `devcontainer.json`:
the containers.dev merge table specifies no rule for `customizations`, so a
binding written there competes with the feature's on undefined terms. Editor
bindings for gated file types belong in a tracked `.vscode/settings.json`, at
workspace scope, which wins by documented rule and appears in a diff
([ADR 0029](adr/0029-the-editor-locus-is-configured-by-the-repository.md)).
`devcontainer.json` keeps container concerns; `.vscode/settings.json` keeps the
editor locus; neither restates the other.

**The template forwards no ports.** A repository that serves nothing still
accumulates forwarded ports, because the editor's own loopback services — the
server, the extension host, the agent host, each language server — bind
ephemeral ports and the default `remote.autoForwardPorts` picks them up. The
numbers differ on every container start, so the list reads as though it were
growing. A repository that does serve something declares it in `forwardPorts`,
where it is reviewable.

The `.devcontainer/` directory carries `fetch-secrets.sh`, `setup.sh`,
`check-auth.sh`, `devcontainer.json`, `devcontainer-lock.json`, and
`claude-user-settings.json` — the same file set as the existing template, with
project-specific content stripped.

## Who owns which step

The template produces the `.devcontainer/`, and it produces a configured one:
the image by digest, the features, `setup.sh`, `check-auth.sh`,
`fetch-secrets.sh` and a lock file covering every feature. There is no
configure-it-afterwards step, and no skill of this standard performs one.

| Step | Owner |
| --- | --- |
| Produce the `.devcontainer/` | The template — `plugins/control-register/templates/devcontainer/`, copied and substituted |
| Choose a different image, where the template's does not fit the stack | The adopter, by hand |
| Pin the image and features, verify pinning holds | `gate-build` (DEV-001) |
| Confirm tools are present and authenticated | `devcontainer-check` |
| Confirm the config still matches the register | `register-check` |

`gate-build` **pins what it finds and never chooses**, which is why the second
row has a person in it rather than a skill. An image is one line, and the control
that matters is enforced either way — the gate fails a floating tag whoever left
it there.

**`project-init` was in this table until 2026-08-26**, owning the
configure-for-the-stack row, and it is not any more
([ADR 0037](adr/0037-the-template-is-the-whole-devcontainer-step.md)). The short
version: it re-chooses the image, replacing the template's digest pin with a
floating tag below the register's floor, and its precondition forces it to run
*after* the template is copied — so the composition the row described undoes the
control the next row deploys. The measurement is in
[`12-phase-4-review.md`](12-phase-4-review.md).

**The template's obtainability was the other reason that section existed**, and
it is closed: `ee-skills-incubator` is private and not a GitHub template, so a
lapsed access once meant no way to start a project. A directory inside the plugin
is obtainable by anyone who can install the plugin, and Phase 4 obtained it that
way with access to no private repository at all.
