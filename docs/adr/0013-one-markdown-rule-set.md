# ADR 0013: One Markdown Rule Set, Deployed Not Duplicated

**Status:** Accepted
**Date:** 2026-08-16
**Revision:** 1

Rationale for control **DOC-001** in `controls.yaml`.

## Background

Markdown is this repository's primary medium — the register's documentation,
the ADRs, and every skill are prose. The failure mode is the same as code
lint's (theme T-2): one rule set for the editor, another in CI, and a third in
someone's memory, drifting until contributors stop trusting any of them.

An existing skill already owns this problem end to end: `lint-md` installs
`markdownlint-cli2` at a pinned version, writes the configuration, and wires
the editor hook, pre-commit hook, and CI step. Writing this repo's own
markdown gate would duplicate a working deployment mechanism — exactly the
drift the register exists to prevent — so the control instead records
`deployed_by: lint-md` and verifies what the skill deploys.

## Alternatives Considered

### Option 1: A repo-local markdown gate

Write this repo's own markdownlint config, hooks, and CI wiring.

**Pros:** Full local control; no dependency on a plugin.
**Cons:** Duplicates what `lint-md` already deploys; the two copies drift
(theme T-2); every future gate skill would inherit the precedent of rebuilding
what exists.

### Option 2: Delegate deployment to `lint-md`, verify in the register

DOC-001 records the property and its verification; `lint-md` owns installing
the pinned tool, writing the config with its provenance stamp, and wiring all
three loci.

**Pros:** One deployment mechanism, many verifications; the provenance stamp
makes staleness computable; `lint-md`'s shape becomes the template every
`gate-*` skill copies.
**Cons:** A dependency on the ee-skills marketplace for the deploying skill —
acceptable because verification stays independent in the checker.

## Decision

We will enforce one shared, pinned markdownlint-cli2 rule set at editor,
pre-commit, and CI, deployed by `lint-md` and verified by the register,
recorded as control DOC-001 at `rung: blocking` with
`variance: narrowing-only`.

## Consequences

**Positive outcomes:**

- Prose gets the same locus discipline as code, from the first commit.
- The deployed config's stamp ties it to a register version, so staleness is
  computable rather than remembered.

**Trade-offs and risks:**

- The pinned tool version lives in both `lint-md`'s deployment and this repo's
  setup and CI wiring; those pins must move together, never separately.
- Rule tightening is local and free; any loosening is a register change first.

## Related ADRs

- [ADR 0009: Lint From One Pinned Definition at Every Locus](0009-single-lint-definition.md)
  — the code half of the same discipline.
- [ADR 0019: Verify Exemptions Against the Files a Repository Tracks](0019-exemptions-cannot-hide-tracked-files.md)
  — governs what DOC-001's deployed config may exclude.
- [ADR 0020: Invoke a Pinned Tool by the Path Its Lockfile Owns](0020-a-locus-reaches-the-pinned-artefact.md)
  — how each of DOC-001's declared loci reaches the pinned markdownlint-cli2.

## References

- [markdownlint-cli2](https://github.com/DavidAnson/markdownlint-cli2)
