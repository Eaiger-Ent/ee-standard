# The control-register devcontainer template

Copy this directory to `.devcontainer/` in a new repository. It is the state a
repository is in **before** any gate has run: pinned, non-root, and choosing
nothing on your behalf beyond a base image.

```bash
cp -R "$(dirname "$0")" .devcontainer   # or copy it from the plugin directory
grep -rl '{{' .devcontainer             # every placeholder still to replace
```

Two placeholders, both `{{PROJECT_NAME}}` — the container's display name and the
named volume that carries Claude Code's credential state between rebuilds. Give
the volume a name unique to the project; two repositories sharing one volume
share one authenticated session, which is confusing the first time and wrong the
second.

Then run `/gate-build`, which pins whatever you changed and stamps it.

## Why this exists

`project-init` has one stated precondition: `.devcontainer/devcontainer.json`
must already exist. Its guidance when it does not is *"clone the template repo
or add the file manually"* — and that template repo is private, so anyone whose
access lapses loses the ability to start a project.

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

**Choose an image for your stack.** That is `project-init`'s, or yours.
`gate-build` insists that whichever image was chosen is pinned; it does not pick
one, and neither does this.

**Install a secret scanner, a linter or an analyser.** Those belong to the gates
that own their controls, and each writes its own stamped region into `setup.sh`.

**Write anything into `customizations.vscode.extensions`.** The editor locus
belongs to the controls that declare one, and `gate-quality` writes the
extension its register names. An extension added here by hand is a second
statement of what the editor enforces.
