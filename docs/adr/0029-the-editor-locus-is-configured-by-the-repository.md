# ADR 0029: The Editor Locus Is Configured by the Repository, Not by a Feature

**Status:** Proposed
**Date:** 2026-08-24
**Revision:** 1

## Background

**The problem.** LNT-001 says ruff lints and formats Python at three places:
the editor, pre-commit, and CI. Two of those three were verified to be running
ruff. The editor was not, and it was not running ruff. A devcontainer feature
had configured autopep8 to format Python files, and nothing in this repository
was capable of noticing.

Two things had to be true for that to happen, and both are architectural rather
than accidental. An editor has no exit code, so the technique this repository
uses to verify a locus — make the wrong thing fail a command — does not apply
to it. And a devcontainer feature contributes editor configuration as well as
software, so a component we pin for what it installs also decides things we
never reviewed.

LNT-001 declares `locus: [editor, pre-commit, ci]`. Three loci, one pinned
tool, one configuration — *pin once, reference many*.

[ADR 0020](0020-a-locus-reaches-the-pinned-artefact.md) established that a locus
must reach the artefact its lockfile owns, and that an invocation which falls
through to `PATH` when the artefact is absent asserts an authority nothing
enforces. It reasoned about pre-commit and CI. It does not mention the editor
locus once, and the editor locus is the one where its conclusion does not
transfer, because an editor has no exit code to fall through to.

A single devcontainer rebuild on 2026-08-24 produced two independent failures
there, neither of which any gate reported.

**The pinned tool was not the tool that ran.** The ruff extension resolves an
interpreter, finds ruff beside it, and falls back to a copy it bundles when it
cannot:

```text
08:10:08.317 Resolved Python executable for Ruff lookup: '…/.venv/bin/python'
08:10:08.318 [error] Error while trying to find the Ruff binary:
             Error: spawn …/.venv/bin/python ENOENT
08:10:08.341 Falling back to bundled executable: …/bundled/libs/bin/ruff
```

It does not re-resolve. For that session the editor linted with a binary no
lockfile owns, while pre-commit and CI used the one `uv.lock` pins. Both were
0.16.4. Nothing made them so — the pin had moved four days earlier — and there
is no locus at which the divergence would have been visible.

**A different tool was configured to own the file type.** The container's
machine-scoped settings read:

```json
"python.defaultInterpreterPath": "/usr/local/python/current/bin/python",
"[python]": { "editor.defaultFormatter": "ms-python.autopep8" }
```

Neither line is in this repository. Both are published verbatim by
`ghcr.io/devcontainers/features/python:1`, which also contributes
`ms-python.python`, `ms-python.vscode-pylance` and `ms-python.autopep8`;
`node:2` contributes `dbaeumer.vscode-eslint` the same way. So the formatter for
Python files in a repository whose LNT-001 pins ruff is autopep8, chosen by a
feature, recorded nowhere, and reviewed by nobody.

This is DEV-001's blind spot rather than a failure of it. DEV-001 pins features
by digest, and the digest is honoured: the feature installed exactly what was
pinned. **A pin governs what a feature installs and says nothing about what it
configures.** That is the same conflation
[ADR 0027](0027-the-interpreter-is-a-pinned-tool.md) named between a pinned
feature and a pinned interpreter, one level up — and it arrives through the
`features:` block, which is the part of `devcontainer.json` a reviewer reads as
already governed.

The two failures are not equally bad. The first ran the right tool at an
unverified version. The second ran a **different tool**, which is the precise
thing a single lint definition ([ADR 0009](0009-single-lint-definition.md))
exists to prevent.

The register is not silent on the editor locus today: `stacks:` carries
`editor_extension` per gate, and `linter-wired-at-all-loci` reads it. But it
asks whether the pinned extension is *present*. Presence does not exclude.
`charliermarsh.ruff` was present the whole time autopep8 held the file type.

## Alternatives Considered

### Option 1: Drop `editor` from `locus:` and call it advisory

Honest and free. An editor cannot fail a build, so calling it a locus alongside
CI arguably overstates what it does.

**Rejected.** The editor is where a developer meets a violation first, and the rung
vocabulary already has words for a gate that does not block — `advisory` and
`warn` — so the register can describe a non-blocking locus without pretending
it does not exist. More decisively, dropping the claim does not change the
behaviour: autopep8 would still format Python here. It would only stop the
register from being the place that says otherwise, which is the failure this
repository exists to prevent, not a remedy for it.

### Option 2: Override the feature from `devcontainer.json`

Put `[python].editor.defaultFormatter` into `customizations.vscode.settings`
and rely on the repository's own metadata winning over the feature's.

**Rejected, on the specification's own words.** Both values land in the same
machine-scoped file, and the containers.dev merge table gives exactly one
instruction for the `customizations` property:

> Merging is left to the tools.

Every other property in that table states its rule — *last value wins*, *union
without duplicates*, *collected list*. This one declines to, so an override
here is not a guarantee but an observation about the current VS Code
implementation, unverifiable without a rebuild and revisable without notice. It
is also invisible to the checker, which would have to parse JSONC devcontainer
metadata and re-implement an undefined merge to know what the editor received.

### Option 3: Own the editor locus in committed workspace settings

`.vscode/settings.json` is workspace scope, which outranks machine scope
unconditionally and by documented rule rather than by merge order. It is a
tracked file: it appears in a diff, it passes under the same gates as
everything else, and a `kind: file` assert can read it without knowing anything
about devcontainer metadata.

**Chosen.** It is the only one of the three that both changes the behaviour and
leaves evidence a checker can read.

## Decision

**We will configure the editor locus in a tracked `.vscode/settings.json` held
in the repository, and verify it there. This is Option 3.**

That decision has five parts.

1. **`.vscode/settings.json` is the editor locus's configuration**, tracked, and
   the only place this repository binds editor behaviour for a gated file type.
   `devcontainer.json` keeps container concerns — environment, features, user,
   mounts — and stops carrying editor settings, so neither file restates the
   other.

2. **A feature's VS Code customizations are an untrusted default.** DEV-001's
   digest pin governs installation and is not extended by this decision. What a
   feature configures is overridden where it matters and ignored where it does
   not.

3. **The register owns the binding, not the checker.** `stacks:` already names
   `editor_extension` per gate; it gains the file-type binding that extension
   must hold. Mandating a different formatter stays a register change rather
   than a checker change ([ADR 0018](0018-register-checker-boundary.md)).

4. **The editor assert changes from presence to exclusivity.** Verifying that
   the pinned extension is installed is not verifying that it is the tool which
   runs. The assert must fail when another extension holds a gated file type,
   which is the case that occurred.

5. **The editor locus is verified by configuration, not by exit code.** It
   remains incapable of failing a build, and nothing here promotes it. A
   `kind: file` assert over a tracked file is what verification means at this
   locus, and it is enough to catch both failures above.

## Consequences

`.vscode/` becomes a tracked directory in this repository and in the template.
It is a small file with a large precedence, which is the point.

Adopters gain a step: `docs/08-adopting.md` must say that a repository using the
`python` or `node` devcontainer features inherits editor configuration it did
not write, and what to put in `.vscode/settings.json` to take it back. This is
not specific to those two features — it is a property of the feature mechanism —
but those two are the ones an Equal Experts repository will meet.

The register gains a field and therefore a contract bump when point 3 lands.
Point 4 changes what `linter-wired-at-all-loci` asserts, which is a `verify`
change and bumps it again if taken separately.

**What this does not close.** An extension that bundles a fallback binary can
always use it; no workspace setting forbids that. `ruff.importStrategy` states
the intent and the interpreter path makes the pinned binary findable, but on a
fresh container create the environment does not exist when the extension host
starts, and the fallback is legitimate at that moment. Closing that needs the
environment present in the image, which needs a Dockerfile this repository does
not have. What the decision closes is the *silent* half: a different tool
holding the file type, which is a state a tracked file can be asked about.

Feature-contributed extensions remain installed. `ms-python.autopep8` will still
be on disk; it will not be the formatter. Uninstalling it is not available from
`devcontainer.json`, and this decision does not pretend otherwise.

## Related ADRs

- [ADR 0007](0007-pinned-devcontainer-features.md) — pins features by digest.
  This decision names the boundary of that pin rather than extending it.
- [ADR 0009](0009-single-lint-definition.md) — one lint definition across loci.
  A second formatter at one locus is the violation this decision found.
- [ADR 0018](0018-register-checker-boundary.md) — why the binding belongs in
  `stacks:` and not in `src/standard_check/`.
- [ADR 0020](0020-a-locus-reaches-the-pinned-artefact.md) — a locus reaches the
  pinned artefact. This extends the question to the locus it did not consider.
- [ADR 0027](0027-the-interpreter-is-a-pinned-tool.md) — a pinned feature is not
  a pinned interpreter; the same conflation, one level down.

## References

- [VS Code settings precedence](https://code.visualstudio.com/docs/configure/settings)
- [Dev Container spec — merge logic](https://containers.dev/implementors/spec/#merge-logic)
- [`devcontainers/features` — `python` feature manifest](https://github.com/devcontainers/features/blob/main/src/python/devcontainer-feature.json)
- [Ruff editor settings](https://docs.astral.sh/ruff/editors/settings/)
