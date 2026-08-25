# ADR 0034: The Template Bootstraps uv, From a Placeholder the Register Fills

**Status:** Accepted
**Date:** 2026-08-25
**Revision:** 1

## Background

Phase 4 built the shipped devcontainer template for the first time, in a
repository that did not author the standard, and the container came up without
uv in it.

That is not a missing convenience. Every verification this standard performs
runs through `uv run register-check`:

- each gate's own verify step, which is `register-check run --control <ID>`
- the pre-commit hooks SUP-003, BLD-001 and DEV-001 declare
- the CI job CI-001 requires
- the adopter's own audit in `docs/08-adopting.md` § 4

The template's own `setup.sh` calls `uv sync --frozen` a few lines below the
point where uv would have to exist, and § 2.3 of the adoption guide tells the
adopter to run `uv run register-install`. None of it can run. The measurement,
inside a freshly built container from the template:

```text
uv       MISSING
poetry   MISSING
python3  Python 3.13.5
```

The interpreter is the base image's `python3-minimal` — below the support floor
[ADR 0028](0028-the-support-floor-is-what-we-run.md) sets, and lacking `venv`,
`ctypes`, `sqlite3` and `http`, so nothing here would run on it at any version.

**Why no gate can fix it.** The obvious shape is the one this repository already
uses for gitleaks: a gate writes a stamped region into `setup.sh` naming the
control it serves. It does not work for uv, and the reason is structural rather
than awkward — a gate verifies itself with `register-check run --control <ID>`,
so a gate that installed uv would be running its own verification on the tool it
had not installed yet. The bootstrap has to precede every gate, which means it
has to be in the template.

**Why the template was written to refuse exactly this.** Phase 2's second
template criterion reads:

> The template pins no tool version by hand. Every tool it installs is either
> sourced from a lockfile the consumer repo already commits, or from a single
> toolchain file — never a literal inside `setup.sh`.

`tests/test_devcontainer_template.py` enforces it as a grep, deliberately, because
[ADR 0020](0020-a-locus-reaches-the-pinned-artefact.md) named this criterion in
advance as one a template could satisfy in letter. A hand-written
`UV_VERSION=0.12.5` in the template is precisely what that grep exists to catch,
and it would be right to catch it: a version typed into a file that ships to
every adopting repository is the second copy this standard exists to prevent,
reproduced once per adopter.

So the two rules point in opposite directions, and neither is wrong.

## Decision

**The template installs uv from the pinned release tarball, verified against the
published sha256, and the three values are double-brace placeholders the adopter
substitutes out of the register they are adopting.**

```bash
uv_version="{{UV_VERSION}}"
case "$(uname -m)" in
  aarch64|arm64) uv_arch=aarch64 uv_sha="{{UV_SHA256_AARCH64}}" ;;
  *)             uv_arch=x86_64  uv_sha="{{UV_SHA256_X86_64}}" ;;
esac
```

`{{UV_VERSION}}` and `{{UV_SHA256_X86_64}}` are `tools.uv.version` and
`tools.uv.sha256`. They join `{{PROJECT_NAME}}` in the substitution step the
template already has, and the template README explains each — a placeholder
nobody documents is one nobody replaces, which `tests/test_devcontainer_template.py`
already fails the build over.

**A placeholder is not a pin, and that is the whole of the reconciliation.** The
criterion above is about where a version *comes from*, and its list was written
before this case existed. A placeholder carries no version at all: the register
holds the number and this file references it, which is the same relationship a
lockfile has and the opposite of a hand-written literal. The grep in
`tests/test_devcontainer_template.py` is widened to say so — a `FOO_VERSION=`
assignment still fails, and one whose value is a placeholder passes — and the
test asserts both directions, because a rule widened to admit a placeholder is
one edit away from admitting the literal it was written to catch.

Once `.devcontainer/setup.sh` is named in `tools.uv.pinned_at` for the adopting
repository, `tool_versions_match_register` reconciles the substituted value
against the register, and a copy that has drifted is a verdict rather than a
surprise. That is the property the criterion was reaching for, and a literal
never has it.

## What was rejected, and why

**A pinned community feature.** `ghcr.io/va-h/devcontainers-features/uv:1` would
satisfy the criterion in letter with no ADR at all, and `devcontainer-lock.json`
would pin it by digest. Its `install.sh` was read rather than assumed:

```bash
curl -sSL -o ${uv_filename} "${uv_url}/releases/download/${UV_VERSION}/${uv_filename}"
```

No checksum, no signature, no attestation. This is the measurement Phase 0.5
already made when it refused to move uv and gitleaks into features and restated
its own criterion as *installs nothing unpinned and nothing unverified*: **a
lock file pins the installer, not the artefact the installer fetches**. Taking
the feature would replace a checksum-verified install with an unverified one
while appearing to strengthen provenance, which is the exact trade that
criterion was restated to forbid. `docs/03-devcontainer.md`'s preference ladder
ranks a feature where its install method ranks, and this one ranks below what it
would replace.

**Telling the adopter to install uv themselves.** Cheapest, and the guide could
carry it in a paragraph. Rejected because this repository has now found *telling*
insufficient often enough to treat it as a known failure mode — it is the same
finding as [ADR 0027](0027-the-interpreter-is-a-pinned-tool.md)'s, and Phase 4's
own interpreter criterion says as much in the build plan. It also leaves the
template's `setup.sh` calling a binary nothing installs, which is a file that
documents its own defect.

## Consequences

The template gains two placeholders and a fourth thing an adopter substitutes.
That is a real cost in a copy-and-fill step, and it is paid once.

**The aarch64 checksum is compared by nothing.** The register pins one, for
x86_64, so the second architecture's digest in the substituted file is a
checksum no assert reads. This is the same gap this repository carries in its
own `setup.sh`, recorded in
[`09-phase-1.5-review.md`](../09-phase-1.5-review.md) § Carried debt. It is
carried here rather than closed by shipping a single-architecture install,
because an adopter on Apple silicon is the ordinary case and a template that
only worked on x86_64 would fail for them at container-create time.

**Phase 2's criterion stays closed and is not restated to fit.** Nothing it
ticked became false: the template still sources every version from a lockfile,
a pinned feature, or now the register, and still contains no literal anybody
typed. What changed is that its enumeration of sources was written before a tool
existed that no gate could install, and the enumeration grew by one. The
distinction this ADR rests on — reference versus copy — is the register's own,
and the test that guards it is stricter after this change than before, not
looser.
