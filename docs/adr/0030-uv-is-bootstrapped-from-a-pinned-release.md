# ADR 0030: Bootstrap uv From a Pinned Release, and Remove the Python Feature

**Status:** Accepted
**Date:** 2026-08-24
**Revision:** 2

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
extensions are not installed, the settings are never written, the interpreter we
put on `PATH` is gone, and the installer is verified. It also makes the container
match what ADR 0027 already decided: the interpreter that runs the gates is a
pinned tool that uv resolves, and after this nothing we install resolves to
another one by accident. It does not leave the container with a single
interpreter — the base image ships one of its own, which
§ A third interpreter, uncovered by the rebuild records.

## Decision

**We will install uv from a pinned, checksum-verified GitHub release, and
remove `ghcr.io/devcontainers/features/python:1` from the devcontainer. This is
Option 3.**

Concretely:

| Thing | Before | After |
| --- | --- | --- |
| How uv is installed | `pip install uv==0.12.5`, using the feature's Python | pinned release tarball, checksum verified, in `setup.sh` |
| How the interpreter arrives | the feature installs 3.14; uv separately resolves `.python-version` | uv fetches the interpreter `.python-version` names; nothing else installs one |
| `python:1` in `devcontainer.json` | present | **removed**, with its `devcontainer-lock.json` entry |
| Interpreters on `PATH` | two, neither the one the gates run on | one, still not the one the gates run on: the base image's `python3-minimal` (§ A third interpreter, uncovered by the rebuild) |
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
python3`, which asks the wrong question either way: it reports whatever `python3`
resolves to, which is the feature's interpreter before this change and the base
image's `python3-minimal` after it, and neither is the interpreter the gates run
on. The question it should ask is the one the loci ask:
`uv run python --version`.

**`devcontainer-lock.json` loses an entry.** DEV-001's
`devcontainer_lock_covers_all_features` compares the lock against the features
declared, so removing both together keeps it passing. The entry is removed by
hand here, because regenerating the lock needs Docker and this container has
none — but a rebuild regenerates it, so the hand edit is a stand-in until then
rather than the state it stays in. `build` and `up` write the lockfile by
default (`--no-lockfile` opts out, `--frozen-lockfile` enforces the existing
one); `devcontainer upgrade` is for moving the pins forward without building.

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

*The rebuild was run on 2026-08-24, and this ADR now records an outcome.* uv
0.12.5 is installed at `/usr/local/bin/uv` from the release tarball and
`/usr/local/python` no longer exists; `uv run python -V` reports 3.14.7 from a
managed CPython; `devcontainer-lock.json` carries three features and none of
them is `python:1`, and DEV-001 passes; the installed extensions are
`charliermarsh.ruff`, `DavidAnson.vscode-markdownlint`, `anthropic.claude-code`,
`dbaeumer.vscode-eslint` and `github.vscode-pull-request-github`, with no
`ms-python.*` among them; `check-auth.sh` reports `python — Python 3.14.7`;
gitleaks 8.30.1 installed and the pre-commit hook was written, so the rest of
`setup.sh` survived losing the interpreter it used to start with. What it also
showed is in § A third interpreter, uncovered by the rebuild. What the rebuild
does **not** close is the shipped template at
`plugins/ee-standard/templates/devcontainer/`, which is a different artefact and
still unbuilt.

*`devcontainer-lock.json` is no longer the hand edit either.* The rebuild wrote
it, as the CLI does on every `build` and `up`, and it wrote back what the hand
edit already said — the file's content is unchanged, which is the hand edit
being confirmed rather than left standing. Its mtime is 10:03 UTC, seven
minutes before the container was created at 10:10 and fifteen after the only
git operation of the morning, so nothing else was in a position to write it.
The content was then checked against the registry independently of the file:
all three `resolved` digests are what `ghcr.io` serves for the tags
`devcontainer.json` declares.

## A third interpreter, uncovered by the rebuild

**Amended 2026-08-24: the rebuild this ADR ended by asking for was run, and it
falsified one claim — that removing the feature leaves the container with a
single interpreter. Everything else the decision predicted held. The decision —
install uv from a pinned release, remove the feature — is unchanged.**

`mcr.microsoft.com/devcontainers/base:trixie` installs `python3-minimal`, so
`/usr/bin/python3` exists in this container and always did. The feature's
interpreter sat ahead of it on `PATH` and answered first, which is why
[ADR 0028](0028-the-support-floor-is-what-we-run.md) revision 2 measured
`/usr/local/python/current/bin/python3` and had no reason to look past it.
Removing the feature uncovered what was behind it:

```text
bash -lc 'command -v python3; python3 -V'
    /usr/bin/python3
    Python 3.13.5
```

A bare `python3` still answers, and still answers below the floor. Three things
follow, and none of them is a reason to reopen the decision.

**What is struck is "one interpreter", not the choice.** What removing the
feature bought is that no interpreter *we install* is unaccounted for: uv
resolves `.python-version`, `uv sync` builds the environment, and nothing else
in `setup.sh` or `devcontainer.json` puts one there. What remains is a
distribution component of an image pinned by digest. It is Option 2's premise in
reverse — the base image contributes no extensions and no bindings, which is
what that option was weighed on, but it does contribute an interpreter.

**Upgrading it is not available, and would not be worth taking.** Trixie's only
Python is 3.13: `apt-cache policy python3` gives candidate `3.13.5-1`, and
`python3.13` is the only versioned package in the suite. Nor would a matching
version help, because the package is `python3-minimal` rather than `python3`:

```text
python3 -c 'import venv'            ModuleNotFoundError: No module named 'venv'
python3 -c 'import ctypes'          ModuleNotFoundError: No module named 'ctypes'
python3 -c 'import sqlite3'         ModuleNotFoundError: No module named 'sqlite3'
python3 -c 'import urllib.request'  ModuleNotFoundError: No module named 'http'
```

Nothing this repository ships could run on it at any version. Making its number
agree with `.python-version` would put the pin in a second place kept in step by
hand — what ADR 0027 deleted `[tool.ruff] target-version` to avoid — and two
numbers agreeing is the state that hid the original gap for as long as it did.

**Removing it was considered and rejected.** It is a leaf:
`apt-get -s remove python3-minimal` removes that package alone and leaves
`libpython3.13-minimal` and `python3.13-minimal` autoremovable, and no installed
package depends on it. It is rejected because it mutates apt state inside an
image pinned by digest, so the digest stops describing the container; because
the shipped template would have to repeat it or an adopter's container would
behave differently from ours; and because it cannot be the general defence in
any case — an adopter's base image may ship a full `python3`, and a host running
a tracked script outside a container has whatever it has.

**So point 3 of § Decision is the whole defence, not a second one beside it.**
`#!/usr/bin/env -S uv run python` on every tracked script, enforced by
`tests/test_toolchain_pin.py`, is what makes a `python3` on `PATH` harmless —
here, in an adopter's container, and on a host with no container at all. This
ADR removed a hazard we had installed. It did not remove the class, and saying
it had was the error.

## Related ADRs

- [ADR 0007](0007-pinned-devcontainer-features.md) — features are pinned by
  digest. This removes one feature; the rest stay pinned.
- [ADR 0027](0027-the-interpreter-is-a-pinned-tool.md) — the interpreter is a
  pinned tool that uv resolves. This makes the container agree with that for
  every interpreter we install. The base image's `python3-minimal` stays, and
  § A third interpreter, uncovered by the rebuild records why it is left alone.
- [ADR 0028](0028-the-support-floor-is-what-we-run.md) — revision 2 managed the
  second-interpreter hazard. This removes the source that ADR measured, and the
  rebuild found another behind it; revision 2 of this ADR records why the
  management, not the removal, is what the hazard actually rests on.
- [ADR 0029](0029-the-editor-locus-is-configured-by-the-repository.md) — the
  editor locus is configured by the repository. That is the general defence;
  this is the specific source.

## References

- [`devcontainers/features` — `python` feature manifest](https://github.com/devcontainers/features/blob/main/src/python/devcontainer-feature.json)
- [uv — installation](https://docs.astral.sh/uv/getting-started/installation/)
- [uv — Python versions](https://docs.astral.sh/uv/concepts/python-versions/)
- [`astral-sh/uv` releases](https://github.com/astral-sh/uv/releases)

## Revision History

| Rev | Date | What changed | Ratified by |
| --- | --- | --- | --- |
| 1 | 2026-08-24 | Original decision: install uv from a pinned, checksum-verified release and remove `ghcr.io/devcontainers/features/python:1`. | Nathan Carney |
| 2 | 2026-08-24 | § A third interpreter, uncovered by the rebuild — the rebuild showed the base image ships `python3-minimal`, so the claim that removal leaves one interpreter was false. Upgrading and removing it are both rejected; the shebang rule is the defence. The decision is unchanged. | Nathan Carney |
