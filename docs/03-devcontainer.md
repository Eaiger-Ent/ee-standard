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
fetches secrets into `.devcontainer/.env`, which `runArgs` passes via
`--env-file`. The `.env` is gitignored. This is the right shape: the container
gets its secrets, the repository never holds them, and SEC-001 has nothing to
find.

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

1. A devcontainer feature, version-pinned, so `devcontainer-lock.json` covers it.
2. A distribution package from a keyring installed by digest.
3. A pinned release artefact with a verified checksum.
4. `curl | sh` — only with a recorded justification and an expiry.

The new repo's `setup.sh` should be short. Anything long enough to need
sectioning is doing work that belongs in the image or a feature.

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
  "runArgs": ["--env-file", ".devcontainer/.env"],
  "postCreateCommand": "bash .devcontainer/setup.sh",
  "postStartCommand": "bash .devcontainer/check-auth.sh",

  "mounts": [
    "source=<repo>-claude-home,target=/home/node/.claude,type=volume"
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

Language toolchains are added as pinned features **when a language is actually
introduced**, not in anticipation. The predicate system in the register already
models this: a repo with no `*.tf` skips IAC-001, and by the same logic it has no
business installing OpenTofu.

The `.devcontainer/` directory carries `fetch-secrets.sh`, `setup.sh`,
`check-auth.sh`, `devcontainer.json`, `devcontainer-lock.json`, and
`claude-user-settings.json` — the same file set as the existing template, with
project-specific content stripped.

## How this composes with `project-init`

`project-init` already owns interactive devcontainer configuration: it asks about
the stack, maps answers to image and features, edits `devcontainer.json`,
validates it with `validate-jsonc.sh`, writes the README, applies `gh repo edit`
settings, and commits.

It has one stated precondition — **`.devcontainer/devcontainer.json` must already
exist.** Its own guidance when it does not is *"Clone the ee-skills-incubator
template repo or add the file manually, then re-run `/project-init`."*

That precondition is the seam, and it decides the division of labour cleanly:

| Step | Owner |
| --- | --- |
| Produce the initial `.devcontainer/` | The template — `ee-skills-incubator`, or a fresh copy of the file above |
| Configure it for this project's stack | `project-init` |
| Pin the image and features, verify pinning holds | `gate-build` (DEV-001) |
| Confirm tools are present and authenticated | `devcontainer-check` |
| Confirm the config still matches the register | `standard-check` |

So `gate-build` runs **after** `project-init`, not instead of it. `project-init`
decides *which* image; DEV-001 insists that whichever it chose is pinned. Those
are different questions, and neither skill should be asked the other's.

One consequence worth stating plainly: `ee-skills-incubator` is a private
repository and is not marked as a GitHub template. Anyone whose access lapses
loses the ability to start a project. Making the template obtainable — a public
template repo, or a `templates/devcontainer/` directory inside the standard
plugin that `project-init` can fall back to — is a real dependency of this plan,
not a nicety. It is tracked as an exit criterion in
[`04-build-plan.md`](04-build-plan.md).
