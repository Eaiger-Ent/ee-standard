# The control-register devcontainer template

Copy this directory to `.devcontainer/` in a new repository. It is the state a
repository is in **before** any gate has run: pinned, non-root, and choosing
nothing on your behalf beyond a base image.

Where it is on your machine depends on how you got the plugin. Installed from a
marketplace, it is inside the plugin's install cache rather than in any
repository you can see:

```bash
# Installed plugin — the version directory is the plugin's own version.
cp -R ~/.claude/plugins/cache/<marketplace>/control-register/<version>/templates/devcontainer \
      .devcontainer

# Working from a clone of the standard instead.
cp -R path/to/ee-standard/plugins/control-register/templates/devcontainer .devcontainer
```

Then, in this order:

```bash
rm .devcontainer/README.md              # this file documents the template, not your project
grep -rl '{{' .devcontainer             # every placeholder still to substitute
```

**Delete this file first, and the order is the point.** The grep matches any
file quoting the placeholder pattern, including one that only explains it — so
while this README is in the copy, the check reports it for ever and a clean
result is unobtainable. Phase 4 met that as a live defect rather than a
hypothetical.

## The placeholders

`{{PROJECT_NAME}}`, twice in `devcontainer.json` — the container's display name
and the named volume that carries Claude Code's credential state between
rebuilds. Give the volume a name unique to the project; two repositories sharing
one volume share one authenticated session, which is confusing the first time
and wrong the second.

`{{UV_VERSION}}`, `{{UV_SHA256_X86_64}}` and `{{UV_SHA256_AARCH64}}` in
`setup.sh` — uv, which every verification in this standard runs on and which no
gate can install, because a gate's own verify step is a `uv run`.

**Read the version and the x86_64 checksum out of the register you are
adopting.** Do not use `grep -A<n>` for this: the register comments that block,
so a fixed context window reaches no value, returns empty, and `sed` then
substitutes nothing — leaving the placeholders in a file that fails at
`sha256sum -c` during container create. Read the whole block instead:

```bash
uv_block() { sed -n '/^  uv:/,/^  [a-z-]*:$/p' controls.yaml; }
uv_version=$(uv_block | sed -n 's/^ *version: *"\{0,1\}\([0-9][^"]*\)"\{0,1\} *$/\1/p')
uv_sha_x86=$(uv_block | sed -n 's/^ *sha256: *//p')
```

The register pins **one** checksum, for x86_64. The aarch64 one is published
beside the same release and is compared by nothing here — a gap this standard
carries for its own container too, recorded rather than hidden:

```bash
rel="https://github.com/astral-sh/uv/releases/download/${uv_version}"
uv_sha_arm=$(curl -fsSL "${rel}/uv-aarch64-unknown-linux-gnu.tar.gz.sha256" | cut -d' ' -f1)
```

**Check all three are non-empty before substituting**, because an extraction
that quietly yields nothing is worse than one that errors:

```bash
echo "${uv_version:?} ${uv_sha_x86:?} ${uv_sha_arm:?}"
```

Then substitute, and expect no output from the last line:

```bash
sed -i.bak \
  -e "s/{{PROJECT_NAME}}/$(basename "$PWD")/g" \
  devcontainer.json
sed -i.bak \
  -e "s/{{UV_VERSION}}/${uv_version}/g" \
  -e "s/{{UV_SHA256_X86_64}}/${uv_sha_x86}/g" \
  -e "s/{{UV_SHA256_AARCH64}}/${uv_sha_arm}/g" \
  setup.sh
rm ./*.bak
grep -rl '{{' .
```

`-i.bak` and the `rm` are portability rather than caution: BSD `sed`, which is
what a macOS host has, requires an argument to `-i` where GNU `sed` requires its
absence.

**Substitute the values as they are — do not unquote them, and do not change the
case.** `setup.sh` writes `UV_VERSION="..."`: the quotes are what `shellcheck`
wants, and both readers of that line accept them. The upper case is the one that
matters — Renovate's custom manager matches `[A-Z_]+=`, so a lowercase pin is
one no bot ever proposes an upgrade for.

They are placeholders rather than pins on purpose: the version stays in the
register and this file references it, which is the difference between a
reference and the second copy this standard exists to prevent. Once
`.devcontainer/setup.sh` is named in that tool's `pinned_at`,
`tool_versions_match_register` reconciles the two and a drifted copy is a
verdict rather than a surprise.

Then run `/gate-build`, which pins whatever you changed and stamps it.

## Before the first `devcontainer up`

`initializeCommand` runs `fetch-secrets.sh` on the **host**, and it exits `1`
when the Keychain holds no Claude Code OAuth token — the container never starts.
So one host-side step comes before everything else:

```bash
# Already set? These service names carry no project prefix, so one credential
# serves every project on the machine and a second adoption finds it there.
security find-generic-password -a "$USER" -s "CLAUDE_OAUTH_TOKEN" -w >/dev/null \
  && echo "already set" || echo "not set"

# Setting or replacing it. `add-generic-password` will not overwrite — it fails
# with "The specified item already exists in the keychain" — so delete first.
claude setup-token
security delete-generic-password -a "$USER" -s "CLAUDE_OAUTH_TOKEN" 2>/dev/null
security add-generic-password -a "$USER" -s "CLAUDE_OAUTH_TOKEN" -w "<paste it here>"
```

A GitHub token is optional but wanted, or `gh` inside the container starts
unauthenticated:

```bash
security add-generic-password -a "$USER" -s "GITHUB_TOKEN" -w "ghp_..."
```

Either name may be prefixed with the checkout directory in `UPPER_SNAKE_CASE` to
scope it to one project — a checkout in `my-app` reads `MY_APP_GITHUB_TOKEN`
before `GITHUB_TOKEN`. `check-auth.sh` reports which entry answered on every
container start, so a value that came from the wrong place is visible rather
than assumed.

## Why this exists

Until this directory existed, the only source of a conformant `.devcontainer/`
was a private template repository, so anyone whose access lapsed lost the ability
to start a project.

This directory is the obtainable answer. It ships with the plugin, so anyone who
can install `control-register` can start a conformant container.

## What it pins, and what it refuses to

**The image, by digest.** No lock file covers images, so this is the one pin
that lives inline. The digest was resolved from the registry on 2026-08-21 and
is the same one `mcr.microsoft.com/devcontainers/base:trixie` served then.

**The features, by digest**, in `devcontainer-lock.json`. Regenerate with
`devcontainer upgrade --workspace-folder .` after adding one. **A lock file
covering some features reads as solved and is not** — DEV-001 fails a partial
one, and this project's own Phase 0.5 exit criterion was re-opened over exactly
that.

**No tool version, anywhere in `setup.sh`.** That is a rule, not an accident.
Phase 2's exit criterion reads: *the template pins no tool version by hand;
every tool it installs is either sourced from a lockfile the consumer repo
already commits, or from a single toolchain file — never a literal inside
`setup.sh`*. A template that scatters pins through a shell script reproduces
that problem in every repository that adopts the standard, and the consumer has
no `tool_versions_match_register` of their own until they adopt the register
too.

So `setup.sh` has exactly two sources of a version: a lockfile the repository
commits, and a pinned feature. Everything else — a scanner, a linter, an
analyser — is installed by the gate that owns the control it serves, which
writes its own region into that file and stamps it.

## Language toolchains are added when a language arrives

Not in anticipation. The register's predicates already model this: a repository
with no `*.tf` skips IAC-001, and by the same logic it has no business
installing OpenTofu. Add the feature when the language does, and re-run
`devcontainer upgrade` so the lock file keeps covering everything.

**Three features are here regardless, and none of them is a language choice.**
`github-cli` because every repository needs it. `claude-code` because the
published route into this standard is `/register-adopt`, a Claude Code skill —
a container that cannot run Claude Code cannot adopt the register from inside
itself, and `check-auth.sh` has always probed for `claude`. And `node`, which is
Claude Code's runtime: the `claude-code` feature declares node a **soft**
dependency, so the CLI drops it from the install order rather than pulling it
in, and the feature's own apt fallback finds no `nodejs`/`npm` pair on trixie.
The build then fails with *"Node.js and npm are required but could not be
installed"*. Naming node here is what turns that soft dependency into a real
one.

**A feature added to an existing container needs the container rebuilt, not
restarted.** `devcontainer up` on a container that already exists reuses it, and
the lock file is regenerated only on a build — so the lock ends up covering the
features you had, not the ones you declared, which is precisely the partial lock
DEV-001 fails:

```bash
devcontainer up --workspace-folder . --remove-existing-container
```

## The two files that must stay gitignored

`fetch-secrets.sh` writes real credentials into `.devcontainer/.env` and derives
`.devcontainer/.env.docker` from it. The `.gitignore` in this directory names
both, and **SEC-001 depends on those lines staying there**. Deleting that file
does not fail a build; it fails quietly, later, in someone else's clone — and a
secret that reaches a remote is not undone by removing it.

Two files rather than one because two parsers read the same values and disagree
about quoting. `.env` is sourced as shell, where a value containing a space must
be quoted; `--env-file` does no shell parsing and would read those quotes as
part of the value. One fetch writes the first and derives the second, so there
is one thing to keep correct. A project that fetches only tokens will not notice
the difference; one that fetches a person's name will.

## What each hook is for

| Hook | Script | What it does |
| --- | --- | --- |
| `initializeCommand` | `fetch-secrets.sh` | On the **host**, before the container starts. Copies from the Keychain into two gitignored files |
| `postCreateCommand` | `setup.sh` | Once, on create. Installs from whichever lockfiles the repository commits |
| `postStartCommand` | `check-auth.sh` | Every start. **Reports** auth and tool state — a start-up hook that silently repaired state would hide which credential stopped working, and when |

`check-auth.sh` probes each tool **the way its loci invoke it**, not by looking
for a bare binary. A lockfile-sourced tool lives in the project tree and never
on `PATH`; probing for the binary reported it missing on a container where every
locus ran it fine. Add a `check_tool` line per tool your register pins, passing
the invocation — `check_tool ruff uv run ruff` probes what pre-commit and CI
both run.

## What this template does not do

**Choose a different image for your stack.** This template declares one, pinned
by digest, and it is the starting point rather than a menu. If it does not fit
your stack, replace the image yourself and run `/gate-build`, which pins what it
finds and fails you if you left a floating tag. No skill in this standard chooses
an image for you (ADR 0037).

**Install a secret scanner, a linter or an analyser.** Those belong to the gates
that own their controls, and each writes its own stamped region into `setup.sh`.

**Write anything into `customizations.vscode.extensions`.** The editor locus
belongs to the controls that declare one, and `gate-quality` writes the
extension its register names. An extension added here by hand is a second
statement of what the editor enforces.
