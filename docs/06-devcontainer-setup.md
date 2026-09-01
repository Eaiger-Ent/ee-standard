# Setting up the devcontainer

**Do this before anything else.** All development on this repository happens
inside the devcontainer. Nothing in Phase 1 should be written on a host
toolchain.

[`03-devcontainer.md`](03-devcontainer.md) specifies *what* the clean
devcontainer is and why. This document is the operator's half: the host values
you must set first, what the committed files do, and how to verify the result.

The files themselves live in [`.devcontainer/`](../.devcontainer/) and are the
single copy. This document does not restate their contents — a second copy of a
config in prose is exactly theme **T-2**, and it would drift.

## Why this is step zero, not Phase 2

[`04-build-plan.md`](04-build-plan.md) originally placed the devcontainer in
Phase 2, alongside the gates. That is right for the **template** — the artefact
this repo ships to consumers, which Phase 2 still owns. It is wrong for **this
repo's own environment**, for two reasons:

**Phase 1 is development work.** Building `register-check` means writing and
running Python. If that happens on a host toolchain, the first thing the
standard repo does is violate the premise it exists to enforce.

**Phase 1's own exit criterion already requires it.** The last criterion reads
*"The checker's own repo passes every control it can verify locally"*, and calls
it "the real gate". DEV-001 is one of those controls. A repo with no
`.devcontainer/` cannot pass DEV-001, so Phase 1 cannot close without the
devcontainer existing. Deferring it to Phase 2 makes Phase 1 unclosable by its
own terms.

So the sequence is: **Phase 0.5 (this) → Phase 1 → Phase 2 generalises this
container into the shipped template**. Phase 2 now has a working reference to
generalise from rather than a specification to implement blind.

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

[`.devcontainer/fetch-secrets.sh`](../.devcontainer/fetch-secrets.sh) runs **on
the host** as `initializeCommand`. It reads each secret with
`security find-generic-password -a "$USER" -s <NAME> -w` and writes the resolved
values to `.devcontainer/.env`. It then derives `.devcontainer/.env.docker` from
that file, and `runArgs` passes *the derived copy* into the container via
`--env-file`.

Two files, because two parsers read the same values. `check-auth.sh` sources the
`.env` as shell, where `GIT_AUTHOR_NAME=Nathan Carney` would split into a command
— so the script quotes any value that can contain a space. Docker's `--env-file`
does no shell parsing at all, taking everything after the `=` verbatim, so it
reads the copy with that surrounding pair of quotes removed. Edit the fetch, not
the copy: `.env.docker` is regenerated on every host-side run.

This is the "secrets fetched, never committed" pattern from
[`03-devcontainer.md`](03-devcontainer.md). Both files are gitignored, so SEC-001
has nothing to find.

Service names are **generic**, with no repo prefix, so one host-side credential
store serves every ee project on the machine.

### Required

| Keychain service | Container variable | Purpose |
| --- | --- | --- |
| `CLAUDE_OAUTH_TOKEN` | `CLAUDE_CODE_OAUTH_TOKEN` | Claude Code auth on subscription billing |

Without it `fetch-secrets.sh` exits `1` and **the container never builds**. Set
it before your first "Reopen in Container". Run `claude setup-token` on the
Mac; it prints an `sk-ant-oat01-...` token to paste into the second command:

```bash
claude setup-token

security add-generic-password -a "$USER" -s "CLAUDE_OAUTH_TOKEN" \
  -w "sk-ant-oat01-..."
```

### Optional

| Keychain service | Container variable(s) | Purpose |
| --- | --- | --- |
| `EE_STANDARD_GITHUB_TOKEN` | `GITHUB_TOKEN` | Authenticates `gh` and git without an interactive `gh auth login`. Scoped to **Eaiger-Ent** (this repo's org), which is *not* generic across ee projects — stored under the per-project override name (see "Per-project overrides" below), not the bare `GITHUB_TOKEN` service, so it can't leak in as the default PAT for an unrelated project on this machine. |
| `EE_SKILLS_GITHUB_TOKEN` | `EE_SKILLS_GITHUB_TOKEN` | A second PAT, scoped to the **EqualExperts** org (`ee-skills`, `ee-skills-incubator`, `generate-ee-slides`). Used only via the `gh-ee-skills` wrapper below — it never becomes the ambient `GITHUB_TOKEN`. |
| `GIT_AUTHOR_NAME` | `GIT_AUTHOR_NAME`, `GIT_COMMITTER_NAME` | Pre-configures the container's git identity |
| `GIT_AUTHOR_EMAIL` | `GIT_AUTHOR_EMAIL`, `GIT_COMMITTER_EMAIL` | As above |

```bash
security add-generic-password -a "$USER" -s "EE_STANDARD_GITHUB_TOKEN" -w "ghp_..."
security add-generic-password -a "$USER" -s "EE_SKILLS_GITHUB_TOKEN"   -w "ghp_..."
security add-generic-password -a "$USER" -s "GIT_AUTHOR_NAME"  -w "Your Name"
security add-generic-password -a "$USER" -s "GIT_AUTHOR_EMAIL" \
  -w "you@equalexperts.com"
```

### Two PATs, two orgs

`gh` (and the git credential helper that shells out to it) only honours one
`GH_TOKEN`/`GITHUB_TOKEN` at a time, host-wide — it has no notion of "use PAT A
for org X, PAT B for org Y". Rather than fight that, `setup.sh` installs a
one-off wrapper, `gh-ee-skills`, that scopes the second PAT to a single
invocation:

```bash
gh-ee-skills issue create --repo EqualExperts/ee-skills-incubator ...
```

Plain `gh ...` (no wrapper) keeps using `GITHUB_TOKEN`, i.e. Eaiger-Ent. Do not
export `EE_SKILLS_GITHUB_TOKEN` as `GH_TOKEN` in the shell profile — that would
just recreate the ambient-shadowing problem the troubleshooting section below
describes, with the second PAT instead of the first.

If this container ever needs to `git push`/`pull` against an EqualExperts-org
repo directly (not just `gh`), embed that PAT in that remote's URL instead —
`git remote set-url origin https://<PAT>@github.com/EqualExperts/<repo>.git` —
rather than extending the credential helper. Out of scope for now: this
container's git operations are all against Eaiger-Ent/ee-standard.

`add-generic-password` will not overwrite. To rotate a value, delete first:

```bash
security delete-generic-password -a "$USER" -s "EE_STANDARD_GITHUB_TOKEN"
security add-generic-password    -a "$USER" -s "EE_STANDARD_GITHUB_TOKEN" -w "ghp_new..."
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
`ee-standard`, the prefix is `EE_STANDARD` — which is how `EE_STANDARD_GITHUB_TOKEN`
above resolves to the container's `GITHUB_TOKEN` without ever touching a bare
`GITHUB_TOKEN` Keychain entry. Use the bare, unprefixed service name only for a
value that is genuinely identical across every ee project (author name/email);
anything org- or repo-scoped, like a PAT, belongs under the prefix.

`fetch-secrets.sh` prints which key it resolved, so you can confirm the override
took effect.

## 3 — What is committed, and why

Four files, plus the lock file you generate in step 4.

| File | Runs | Does |
| --- | --- | --- |
| [`devcontainer.json`](../.devcontainer/devcontainer.json) | — | Digest-pinned image, four pinned features, `remoteUser: vscode`, one persistent volume |
| [`fetch-secrets.sh`](../.devcontainer/fetch-secrets.sh) | Host, before start | Keychain → `.devcontainer/.env`, then → `.env.docker` |
| [`setup.sh`](../.devcontainer/setup.sh) | Container, on create | Volume ownership, `markdownlint-cli2` pin, git credential helper |
| [`check-auth.sh`](../.devcontainer/check-auth.sh) | Container, every start | Re-sources `.env`, prints the auth banner |

Three things differ from the target file sketched in
[`03-devcontainer.md`](03-devcontainer.md), and each is a correction to that
sketch rather than a deviation from it:

| Change | Why |
| --- | --- |
| `/home/vscode/.claude`, not `/home/node/` | `devcontainers/base` runs as `vscode`. `/home/node` only exists on the `javascript-node` image the predecessor used — the sketch carried the path over with the pattern. Mounting at `/home/node` would create a root-owned directory Claude Code never reads. |
| `"remoteUser": "vscode"` stated explicitly | BLD-001 is a Tier-1 control of this register. Relying on the image's default is exactly the "declared but unreachable" shape (T-3) the repo exists to catch. |
| Claude Code as a pinned **feature** | `03-devcontainer.md` ranks a version-pinned feature above `curl … \| sh`. `ghcr.io/anthropics/devcontainer-features/claude-code` is official and lock-file-covered, which removes one of the three pipes-to-shell and shortens `setup.sh` to wiring only. |

**There is no python feature**, from
[ADR 0030](adr/0030-uv-is-bootstrapped-from-a-pinned-release.md). There used to
be, carrying `installTools: false` to stop it installing an unpinned grab-bag of
linters, and it existed to supply the `python3` that ran one line of `setup.sh`
— `pip install uv`. `setup.sh` now installs uv from its pinned release against a
published checksum, the way it already installed gitleaks, and `uv sync` fetches
the interpreter `.python-version` names. **Nothing we install puts a second
interpreter in the container** — but the base image ships one. `base:trixie`
installs `python3-minimal`, so `/usr/bin/python3` is Python 3.13.5, and the
feature used to sit ahead of it on `PATH` and hide it. It is left alone, for
the reasons in ADR 0030 revision 2: trixie has no 3.14 to raise it to, a
matching version number would be a second copy of the pin, and the package has
no `venv`, `ctypes`, `sqlite3` or `http`, so nothing here runs on it in any
case. Reach the interpreter through `uv run`, never through `python3`.

Until [ADR 0027](adr/0027-the-interpreter-is-a-pinned-tool.md) this page said
the feature's `version` was the interpreter your gates run on — *"change it in
that one place"*, where there were three places and the one that decided the
answer in CI was none of them.

The interpreter the gates run on is `.python-version`, at the repository root,
and uv reads it at every locus. That is the one place, and now it really is one:

| File | What it decides |
| --- | --- |
| `.python-version` | The interpreter every locus runs the gates on. **Change this one.** |
| `pyproject.toml` `requires-python` | Which interpreters `register-check` claims to support. A floor, published in package metadata — not this container's choice |

**Why the shebangs still say `uv run`.** `.python-version` binds only what goes
through uv, and while the feature existed a bare `python3` in a login shell was
*its* interpreter — so `./scripts/plan_progress.py` ran on 3.13 while mypy and
ruff checked it at 3.14 ([ADR 0028](adr/0028-the-support-floor-is-what-we-run.md)
revision 2). Two repairs were made: every tracked script reads
`#!/usr/bin/env -S uv run python`, and the feature was raised to match. ADR 0030
has since removed the feature, which took the second repair with it and
uncovered the base image's `python3-minimal` underneath — so a bare `python3`
still answers, and still answers below the floor.

The first repair stays, and `tests/test_toolchain_pin.py` still fails any script
that resolves from `PATH`. It defends the shape rather than that one feature: a
shebang resolving against `PATH` is wrong wherever it happens, including on a
host where a script is run outside the container entirely. Removing a hazard's
current source is not a reason to stop checking for it.

`setup.sh` does **not** pin `markdownlint-cli2`. It runs `npm ci`, so
`package-lock.json` is the authority and there is no version here to keep in
step with CI's — the change ADR 0020 made, one tool at a time, for exactly the
drift the previous sentence on this page warned about while creating it.

The `.gitignore` entries for `.devcontainer/.env` and `.devcontainer/.env.docker`
are load-bearing, not hygiene — they are the half of the "secrets fetched, never
committed" pattern that does the *never committed* part. Both hold the same
credentials, so adding a value to the fetch never means adding a path here, but
adding a *file* to it does.

## 4 — Build, and generate the lock file

```bash
cd ee-standard
chmod +x .devcontainer/*.sh
code .
# → "Reopen in Container"
```

First build takes several minutes. It also writes the lock file DEV-001
requires: the CLI generates `devcontainer-lock.json` on every `build` and `up`,
so there is no separate step and nothing to remember. `--no-lockfile` opts out
and `--frozen-lockfile` fails rather than rewriting; use neither.

`devcontainer upgrade` is a different job — moving the pins forward to the
current tags without building:

The upgrade rewrites `devcontainer-lock.json`:

```bash
devcontainer upgrade --workspace-folder .
git add .devcontainer/devcontainer-lock.json
```

Either way the lock is written by the CLI, never by hand. Confirm it pins
**every** feature named in `devcontainer.json` — three entries today, each with
a `resolved` digest. A lock file that covers two of three reads as solved and is
not.

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

# The lock file exists and names every feature. Expect 3.
grep -c '"resolved"' .devcontainer/devcontainer-lock.json

# Neither secrets file has ever been committed. Expect no output.
git log --all --oneline -- .devcontainer/.env .devcontainer/.env.docker
```

For reference, the digests resolved on 2026-08-16:

| Reference | Version | Digest |
| --- | --- | --- |
| `mcr.microsoft.com/devcontainers/base:trixie` | — | `sha256:025b74bb5f7ac53edd77e01aa7188c359aab100e23a2f6220bde50bbb9fd31dd` |
| `devcontainers/features/github-cli` | 1.1.0 | `sha256:d22f50b70ed75339b4eed1ba9ecde3a1791f90e88d37936517e3bace0bbad671` |
| `devcontainers/features/node` | 2.1.0 | `sha256:8c0de46939b61958041700ee89e3493f3b2e4131a06dc46b4d9423427d06e5f6` |
| `anthropics/devcontainer-features/claude-code` | 1.0.5 | `sha256:cfc2e7d3e9fd3b9b01f8d5cb158508a884c8c0ede2e23ed10f32dea5d4ffe69a` |

`devcontainers/features/python` was resolved here too, at 1.8.0. It is no
longer declared (ADR 0030), so its digest is not listed.

**The `node` row is wrong, and is left as it was recorded.** `devcontainer.json`
declares `node:2`, which resolves to
`sha256:586c9a6f7dd40bd3ba2cd41e7f2f88dcc31fbe5d1442afcbf07ffbc66b686857` — what
`devcontainer-lock.json` holds. The digest in the table is what `node:1` serves,
so the snapshot resolved the wrong tag. The lock is the authority DEV-001 reads
and it is right; this table is a dated note beside it, kept as written so the
error stays visible rather than being quietly repaired. Resolve a tag you are
checking, not a tag next to it.

The `github-cli` digest matches the one already quoted in
[`03-devcontainer.md`](03-devcontainer.md), which is a useful independent
confirmation that the resolution method is sound.

Only the image digest is authoritative in `devcontainer.json`; the feature
digests above are a cross-check against the lock file, which is where features
are actually pinned.

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
presented as `404` then `403`, and again the same day when pushing this
document — `env -u GITHUB_TOKEN git push` succeeded where the plain push had
failed. Fix it permanently by widening the PAT's scope, or by removing the
Keychain entry and relying on `gh auth login`, which persists in the volume.

It is also a live instance of theme **T-5** — the credential boundary least
defended — arriving as a support question rather than as a breach, which is the
usual way.

### A tool is missing after a rebuild

```bash
bash .devcontainer/setup.sh
```

If it is missing *repeatedly*, it is being installed by the wrong mechanism.
Promote it to a pinned feature rather than adding a retry.

## Closed gap in DEV-001

[`03-devcontainer.md`](03-devcontainer.md) states that DEV-001 "verifies both
halves: `devcontainer-lock.json` present *and* the image reference containing an
`@sha256:` digest." The register originally said less — its `enforces` covered
only the lock file, so a repo with a complete lock file and a floating `image`
tag passed DEV-001. That was theme **T-1** (a stated standard that nothing
enforces) inside the register itself.

Closed at register `v0.2.0` (contract 2), as Phase 0.5's final exit criterion
required: DEV-001's `enforces` text now covers both halves, and its `verify`
list carries `devcontainer_image_digest_pinned` alongside
`devcontainer_lock_covers_all_features`. The register entry is authoritative;
this section remains only as the record of how the gap was found and closed.
