# ADR 0030: Bootstrap uv From a Pinned Release, and Remove the Python Feature

**Status:** Proposed
**Date:** 2026-08-24
**Revision:** 1

## Background

**The problem.** We install a devcontainer feature that sets up a complete
Python development environment. We want one thing from it: a `python3` that can
run `pip install uv`. Everything else it brings, we did not ask for, and one of
those things quietly overrode a gate.

The feature is `ghcr.io/devcontainers/features/python:1`. Its entire use in this
repository is a single line in `.devcontainer/setup.sh`:

```bash
pip install --quiet uv==0.12.5
```

After that line runs, uv owns everything. It creates the environment, it
resolves the interpreter from `.python-version`, and every locus reaches every
tool through it. The feature's interpreter is never used again.

**What we get in exchange.** The feature's published manifest contributes:

| Kind | What |
| --- | --- |
| Extensions | `ms-python.python`, `ms-python.vscode-pylance`, `ms-python.autopep8` |
| Settings | `python.defaultInterpreterPath`, and `[python].editor.defaultFormatter` set to autopep8 |

`devcontainer.json` already passes `installTools: false` to switch off the
tooling it would otherwise install. There is no equivalent switch for the
extensions or the settings.

**Why this matters, in three separate ways.**

*First, it picked our formatter.* LNT-001 pins ruff. The feature bound Python
files to autopep8, and that binding was live in this container until
[ADR 0029](0029-the-editor-locus-is-configured-by-the-repository.md). ADR 0029
defends against this in general, by putting editor bindings in a tracked
`.vscode/settings.json` at a scope that wins. This ADR is about the specific
source.

*Second, it puts a second interpreter on `PATH`.* This is the hazard
[ADR 0028](0028-the-support-floor-is-what-we-run.md) revision 2 was written to
manage. A shebang resolves against `PATH`, so `./scripts/plan_progress.py` ran
on the feature's interpreter while the gates ran on uv's. The repair was to give
every tracked script `#!/usr/bin/env -S uv run python` and add
`tests/test_toolchain_pin.py` to enforce it. That repair works. It manages a
hazard rather than removing it, because the second interpreter is still there.

*Third, we do not verify what it installs.* `docs/03-devcontainer.md` sets out a
preference ladder, and it prefers a pinned release artefact whose checksum we
check over a feature that fetches a release without checking one. `setup.sh`
already follows that ladder for gitleaks, in the same file, a few lines below
the `pip install`.

**What would replace it.** uv is a single static binary. It needs no Python to
run, and it can install the interpreter itself:

- uv publishes per-architecture tarballs on each GitHub release, each with a
  `.sha256` sidecar. For 0.12.5, the version already in `controls.yaml`:

  ```text
  uv-aarch64-unknown-linux-gnu.tar.gz  9bf43b4d1a07665bf64d4c4e710930b382321a785e0eb10aac07f46471f86a31
  uv-x86_64-unknown-linux-gnu.tar.gz   68a509da24b06b4223a1c0175fb5eb5bc79342b76cbeff0cfe51ac3f5b17b6b2
  ```

- `uv sync` downloads a managed CPython when the interpreter `.python-version`
  names is not present. No system Python is involved at any point.

That is the same shape `setup.sh` already uses for gitleaks: fetch a pinned
release, verify a checksum, install the binary.

## Alternatives Considered

### Option 1: Keep the feature, and override what it configures

Leave `python:1` in place. Correct its settings in `.vscode/settings.json`,
which is what ADR 0029 decided.

**Rejected as a complete answer** — though it stays as the general defence. It
fixes the binding that competed with LNT-001 today. It leaves the second
interpreter on `PATH`, leaves the unverified installer, and leaves three
unwanted extensions installed. It also puts us in the position of correcting a
component every time it changes its mind, with no notification when it does: a
feature's customizations are not part of the digest review, so a digest bump can
change what the editor is configured to do without anyone reading a diff.

### Option 2: Keep the feature, but choose a leaner base image

Move from `mcr.microsoft.com/devcontainers/base:trixie` to a plainer Debian, on
the theory that the base image is what is over-supplied.

**Rejected, because the premise is false.** `base:trixie` is Debian plus
`common-utils:2` and `git:1`. Its own `devcontainer.json` declares no
`customizations`. It contributes zero extensions and zero tool bindings. Every
extension and every binding in this container comes from a feature we listed
ourselves — three extensions and both bindings from `python:1`, one extension
from `node:2`. A leaner base would remove none of them, and we would have to
rebuild the non-root `vscode` user that BLD-001 depends on.

### Option 3: Install uv from a pinned release, and remove the feature

Fetch the uv tarball for the container's architecture, verify its published
checksum, install the binary, and let uv fetch the interpreter. Delete
`ghcr.io/devcontainers/features/python:1` from `devcontainer.json` and its entry
from `devcontainer-lock.json`.

**Chosen.** It removes the cause rather than correcting the effect. The
extensions are not installed, the settings are never written, there is no second
interpreter on `PATH`, and the installer is verified. It also makes the
container match what ADR 0027 already decided: the interpreter that runs the
gates is a pinned tool that uv resolves, and after this there is no other
interpreter for anything to resolve to by accident.

## Decision

**We choose Option 3: install uv from a pinned, checksum-verified GitHub
release, and remove `ghcr.io/devcontainers/features/python:1` from the
devcontainer.**

Concretely:

| Thing | Before | After |
| --- | --- | --- |
| How uv is installed | `pip install uv==0.12.5`, using the feature's Python | pinned release tarball, checksum verified, in `setup.sh` |
| How the interpreter arrives | the feature installs 3.14; uv separately resolves `.python-version` | uv fetches the interpreter `.python-version` names; nothing else installs one |
| `python:1` in `devcontainer.json` | present | **removed**, with its `devcontainer-lock.json` entry |
| Interpreters on `PATH` | two | one |
| `tools.uv` in `controls.yaml` | `source: literal`, `version`, `pinned_at` | gains `release_repo` and `sha256`, matching the `gitleaks` entry |

Three points that this decision does **not** change, stated so they are not read
into it:

1. **ADR 0029 stands.** The editor bindings stay in `.vscode/settings.json`.
   Removing this feature removes today's instance of the problem; ADR 0029
   removes the class, and the class recurs — the base image carries a
   `devcontainer.metadata` label of its own, and any future feature can bind a
   file type.

2. **`node:2` stays.** DOC-001 runs `markdownlint-cli2` through node at every
   locus. That feature contributes one extension and no bindings, so it is not
   competing with a gate.

3. **`tests/test_toolchain_pin.py` stays**, and so does
   `#!/usr/bin/env -S uv run python` on every tracked script. The test defends
   against the shape — a first-party script resolving its interpreter from
   `PATH` — not against this particular feature. Removing the feature is not a
   reason to stop checking.

## Consequences

**`.devcontainer/check-auth.sh` must change.** It probes `check_tool python3
python3`, which will find nothing once no system Python exists. The question it
should ask is the one the loci ask: `uv run python --version`.

**`devcontainer-lock.json` loses an entry.** DEV-001's
`devcontainer_lock_covers_all_features` compares the lock against the features
declared, so removing both together keeps it passing. Regenerating the lock
needs `devcontainer upgrade --workspace-folder .`, which needs Docker.

**The register gains two fields on an existing tool.** `tools.uv` takes
`release_repo` and `sha256`, the same pair `tools.gitleaks` already carries. No
control's `rung`, `verify`, `variance` or `applies_to` changes, and no skill
reads a field it did not already understand, so this does not bump
`meta.register_contract`.

**The checksum is published rather than derived.** `controls.yaml` records, for
gitleaks, that a bumped version needs a bumped digest and no bot can compute
one. uv publishes the checksum beside the artefact, so a bump can fetch and
compare it rather than requiring a human to produce it. This makes the problem
smaller. It does not remove it, because fetching the vendor's checksum from the
vendor's release proves the download matches what was published, not that what
was published is what we intended.

**Three extensions stop being installed**: `ms-python.python`,
`ms-python.vscode-pylance`, `ms-python.autopep8`. Pylance is the Python language
server, so completion, navigation and hover for Python go away with it. This is
a real loss, and it is the honest cost of the decision: the editor keeps ruff
for linting and formatting, mypy remains the type checker at pre-commit and CI,
and neither of those covers what a language server does. A repository that wants
Pylance back should install `ms-python.python` explicitly, in
`devcontainer.json`, as a reviewed line — which is the difference between
choosing it and inheriting it.

**Nothing here is verified until someone rebuilds.** This container has no
Docker. The commands an operator runs are in `docs/08-adopting.md` § 2.0. Until
then this ADR records a decision and not an outcome.

## Related ADRs

- [ADR 0007](0007-pinned-devcontainer-features.md) — features are pinned by
  digest. This removes one feature; the rest stay pinned.
- [ADR 0027](0027-the-interpreter-is-a-pinned-tool.md) — the interpreter is a
  pinned tool that uv resolves. This makes the container agree with that by
  leaving no other interpreter present.
- [ADR 0028](0028-the-support-floor-is-what-we-run.md) — revision 2 managed the
  second-interpreter hazard. This removes its source.
- [ADR 0029](0029-the-editor-locus-is-configured-by-the-repository.md) — the
  editor locus is configured by the repository. That is the general defence;
  this is the specific source.

## References

- [`devcontainers/features` — `python` feature manifest](https://github.com/devcontainers/features/blob/main/src/python/devcontainer-feature.json)
- [uv — installation](https://docs.astral.sh/uv/getting-started/installation/)
- [uv — Python versions](https://docs.astral.sh/uv/concepts/python-versions/)
- [`astral-sh/uv` releases](https://github.com/astral-sh/uv/releases)
