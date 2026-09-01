# ADR 0048: The Published Register Is Derived

**Status:** Proposed
**Date:** 2026-09-01
**Revision:** 1

## Background

`controls.yaml` is two things at once. It is the register **this** repository is
checked against, and it is the register every adopter fetches. Most of it is the
same document for both. Some of it is not, and the first adoption to reach
`/register-adopt` on a repository nobody here owns found out which.

Its summary reported two failures, and both were the register describing us:

**`tools.uv.pinned_at` ships four paths and two are ours.**

```text
.devcontainer/setup.sh                     ← every adopter has it (the template)
.github/workflows/register-check.yml       ← every adopter has it (four gates write it)
.github/workflows/support-floor.yml        ← ours alone
.github/workflows/conformance-sweep.yml    ← ours alone
```

`tool_versions_match_register` fails a declared site that does not exist, **by
design** — that is how a renamed workflow is caught rather than silently dropped
from comparison. So an adopter fails SUP-001 on two files they were never going
to have, told that the register records a pin there.

**`CI-001`'s `required_checks` ships our job ids**, `[register-check, lint-md]`.
`gate-repo` refused to create the ruleset, and refusing was **right**: GitHub
waits forever for a check nothing reports, so a ruleset requiring `lint-md` in a
repository with no such job blocks every merge rather than gating one. A gate
did the correct thing with a register that was wrong about the world.

**Neither is undocumented.** § 3.7 of `08-adopting.md` is titled *Your register
records your own files* and names `pinned_at` as the first edit an adopter
makes. It sits ~1,400 lines into the reference, `START-HERE.md` does not mention
it, and `/register-adopt` does not perform it — so it arrives as two failures
rather than as a step.

**And it is the inverse of a defect already fixed.**
`docs/09-phase-1.5-review.md` § H2 found this repository's filenames hard-coded
in the assert, so an adopter was told their own files were *"pinned at no known
locus"*. Moving the list into the register fixed the checker and left the paths
in the register, where they now ship to everybody. The same facts, one layer up.

## The tension this exposes

The obvious fix — delete the two workflow paths — **loses real coverage here**.
`support-floor.yml` and `conformance-sweep.yml` both install uv at a pinned
version. They genuinely repeat the pin, they genuinely belong in `pinned_at` for
this repository, and dropping them means two sites stop being compared. That is
the drift the field exists to catch.

So this is not a mistake to correct. It is one file being asked to be two
documents, and every value that legitimately differs between repositories is a
place where it fails.

[ADR 0045](0045-a-gate-records-where-it-installed-a-tool.md) named the same
distinction three days earlier for a different purpose. Its argument for letting
a gate write `pinned_at` is that the field *"records where a repository keeps a
file rather than what conformant means, and two conformant repositories
legitimately differ on it"*. If that is true — and it is the premise that ADR
rests on — then shipping one repository's `pinned_at` to every adopter is
shipping a repository-specific fact as though it were policy.

§ 3.7 already lists four such fields: `pinned_at`, `ecosystems`, `release_repo`
and `toolchain`. `required_checks` is a fifth it does not name.

## Decision

**The published register is derived from this one by removing the entries this
repository marks as its own.** A repository-specific value stays where it is
useful — in the file this repository is checked against — and does not reach the
tag an adopter fetches.

An entry is marked with a trailing comment, on its own line, immediately above:

```yaml
pinned_at:
  - .devcontainer/setup.sh
  - .github/workflows/register-check.yml
  # local-only: this repository's own workflows, not published
  - .github/workflows/support-floor.yml
  - .github/workflows/conformance-sweep.yml
```

Three rules, and the third is what stops this becoming a way to hide things.

**1. Only a field § 3.7 names may carry a local-only entry.** `pinned_at`,
`ecosystems`, `release_repo`, `toolchain`, and `required_checks` — which this ADR
adds to that list, because a job id is as repository-specific as a path. A
local-only marker on `rung`, `verify`, `variance`, `applies_to` or `tier` is a
schema error: those are what conformant *means*, and a register that published a
different policy from the one it enforces would be indefensible.

**2. What remains after the removal must still be valid.** The published register
is loaded and schema-checked as part of producing it. `required_checks` may not
become empty — an empty list is a ruleset requiring nothing, which register
contract 19 added the field to prevent.

**3. Every published value must be one the standard's own artefacts create.**
This is the checkable half. A `pinned_at` path must be either a file the shipped
devcontainer template writes or a path a gate declares in `deploys.json`; a
`required_checks` entry must be a job the gates' own CI template produces. Both
lists are already in the repository, so this is a test rather than a judgement:

```text
template: .devcontainer/setup.sh, devcontainer.json, devcontainer-lock.json, …
gates:    .github/workflows/register-check.yml, .pre-commit-config.yaml,
          .github/dependabot.yml, .vscode/settings.json, …
```

`support-floor.yml` and `conformance-sweep.yml` are in neither set, which is
exactly why they are ours — and the test would have caught them the day they were
added rather than at somebody else's first adoption.

## Alternatives considered

**Delete the two paths from the register.** Rejected: it loses real comparison
coverage here, on two files that really do repeat the pin. Fixing an adopter's
experience by weakening our own checking is the wrong trade in a repository whose
whole argument is that unchecked things drift.

**Leave it and make the failure legible** — have
`tool_versions_match_register` say *"this path came from the register you
fetched and does not exist here; if it is not yours, remove it (§ 3.7)"*.
Genuinely better than today and **not sufficient**: it still requires every
adopter to prune a file they did not write, and `gate-repo`'s `required_checks`
failure is not improved by a better message because the ruleset would still be
wrong. Worth doing anyway, and cheap.

**Ship `pinned_at: []` and let gates fill it.** Rejected on measurement: uv's
entry for `.devcontainer/setup.sh` is put there by the adopter's own
substitution in § 2.0, not by any gate, so nothing would ever add it and uv would
be pinned at no compared locus at all. ADR 0045's write covers a gate's own
artefacts and no more.

**A second register file.** Rejected — that is the second copy this repository
exists to prevent, and the two would drift in exactly the way the marker
approach cannot, since a derivation has one source.

## Consequences

The tag an adopter fetches stops describing this repository. That is the whole
benefit and it closes both failures the run reported.

**This repository keeps its own coverage.** Nothing stops being compared here;
the four `pinned_at` entries stay and two of them are marked.

**Producing a release gains a step, and it must be mechanical.** Cutting a tag
without deriving the register would publish the unpublished values, which is
today's behaviour and therefore the easy mistake. It belongs in the same test
that already holds `install.ref` to a real release and to a matching
`pyproject.toml` version.

**§ 3.7 shrinks and should say why.** It currently tells an adopter that
`pinned_at` is the first edit they make. After this it is not — the published
value is already theirs. What survives is the case a gate cannot cover: a
repository that pins a tool in a file of its own naming still adds that path
itself.

**The `required_checks` half changes an adopter's first ruleset.** Published as
`[register-check]` alone, `gate-repo` will create a ruleset requiring one check
rather than refusing. A repository that later adds a second gating job adds it
to its own register, which is § 3.7's remaining case.

This ADR is **Proposed**: it changes how the register is published, the marker
syntax is a judgement nobody has reviewed, and there is a cheaper partial fix
(the second alternative) that is worth taking regardless of whether this is
accepted.
