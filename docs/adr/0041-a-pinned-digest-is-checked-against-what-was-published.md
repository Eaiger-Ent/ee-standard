# ADR 0041: A Pinned Digest Is Checked Against What the Project Published

**Status:** Accepted
**Date:** 2026-08-27
**Revision:** 1

## Background

Renovate proposed uv `0.12.5` → `0.12.6` in [#74](https://github.com/Eaiger-Ent/ee-standard/pull/74).
It moved the version literal at all four sites the register names and left
**all three** sha256 digests at 0.12.5's values — two in
`.devcontainer/setup.sh`, one in `tools.uv.sha256`. Every check passed.

What that pull request would have merged is a container that cannot build:
`sha256sum -c` exits `1` on a tarball whose digest names the previous release.
That is the right behaviour and the last line of defence rather than the first —
the failure surfaces at container-create, on somebody's machine, a day after the
merge that caused it.

`tool_versions_match_register` reconciles *versions* across `pinned_at`. Nothing
reconciles a digest with anything. The register's own comment beside
`tools.uv.sha256` says a bump *"still needs a human"*, and no check made one.

## Decision

**Two checks, and a control of their own to carry them.**

**1. Offline: every digest the register pins appears where the register says it
is repeated, and no digest appears there that the register does not name.**
Both directions, because they catch different mistakes. The first catches a
human who edited the register and not `setup.sh`; the second catches a human who
edited `setup.sh` and not the register, and it is the half that would have
caught #74 had the bot moved one of the three.

**2. Network: every digest the register pins equals the one the project
published.** Both tools publish a checksum **manifest** — uv as `sha256.sum`,
gitleaks as `gitleaks_<version>_checksums.txt` — each a list of
`<digest>  <filename>` lines. One shape reads both, which is why the register
names a manifest rather than a per-asset `.sha256`: uv publishes both forms and
gitleaks publishes only the manifest, so the per-asset form would have covered
one tool of two.

The manifest form also reaches **the digests nothing has ever compared**. The
aarch64 digest in `.devcontainer/setup.sh` was recorded as unverified in
`09-phase-1.5-review.md` and stayed that way because the register held only the
x86_64 one. A manifest lists every architecture, so the register can name the
second digest and have it checked by the same fetch.

**3. It is a new control, SUP-004, whose only locus is `ci`.** This is the part
that is not obvious, and it is forced rather than chosen.

The natural home looked like SUP-001, which already carries
`tool_versions_match_register`. But SUP-001 declares a `pre-push` locus from
register contract 31, so `register-check run --control SUP-001` runs in a git
hook — and a `kind: remote` block on it would put a network fetch in front of
every push. Offline, the block reports `UNCLASSIFIED`, the run exits `3`, and
the hook refuses the push. A developer on a train could not push a
documentation fix.

So the property gets a control, and the control gets the locus its verification
can actually answer at. That is the same test ADR 0039 applied to SEC-003, in
the other direction: there, a control was kept *out* of the pre-push locus
because its remote blocks need a GitHub Actions job; here, a new control is
given a `ci`-only locus because its remote block needs a network.

**4. A tool that publishes no manifest reports having nothing to compare, and
passes.** It is not `UNCLASSIFIED`. Whether a project publishes checksums is a
fact about that project, and a register whose tools happened not to would fail
its conformance run for ever under `--require-complete` — punishing a repository
for somebody else's release process. The absence is stated in the report so it
is visible rather than silent, in the same way `coverage_key`'s absence is a
statement.

## Alternatives considered

**A test rather than a control.** `tests/` covers this repository and nothing
else, and the register ships to adopters who pin their own tools. The offline
half in particular is exactly the kind of rule an adopter needs and would not
inherit from a test in someone else's repository.

**Per-asset `.sha256` URLs.** Rejected on measurement: uv publishes them and
gitleaks does not (`404`). A mechanism that covered one pinned tool of two would
have looked complete and been half a check.

**Deriving the digest instead of comparing it** — fetching the artefact and
hashing it. It is the same bytes either way, and downloading two release
tarballs on every conformance run to learn what a 200-byte manifest already says
is a cost with no extra assurance. Comparing against the manifest also fails
loudly if the project's own manifest disagrees with the artefact, which is the
project's bug to fix rather than ours to absorb.

**Putting the remote block on SUP-001 and accepting the offline case.**
Rejected — see point 3. A gate that stops working on an aeroplane is a gate
people learn to pass with `--no-verify`.

## Consequences

**The conformance run now depends on a release endpoint being reachable.** Under
`--require-complete`, an unreachable network is exit `1` rather than a warning:
`UNCLASSIFIED` is what an unanswerable check reports, and `--require-complete`
promotes it. That is the accepted cost of this being a control rather than a
test, and it is the reason point 3 keeps the block off every local locus — the
fragility is confined to the one place that always has a network.

**All four digests in this repository were checked against upstream while this
was written**, and all four match: uv x86_64 and aarch64, gitleaks x64 and
arm64. The control therefore lands green, which is the honest but weaker
position — it demonstrates the mechanism runs, not that it bites. What
demonstrates that is `tests/test_checksums.py`, which moves each digest by one
character and watches both halves fail.

**A version bump now fails something.** A bot that moves a version and leaves a
digest fails the offline half if it edited one site of two, and the network half
either way. The register's *"still needs a human"* comment stays true — a human
still has to fetch the new digest — but forgetting is no longer silent.
