# ADR 0020: Invoke a Pinned Tool by the Path Its Lockfile Owns

**Status:** Accepted
**Date:** 2026-08-18

Ratified from [`09-phase-1.5-review.md`](../09-phase-1.5-review.md) § H6.

## Background

The register records an authority for every tool version.
[ADR 0018](0018-register-checker-boundary.md)'s third pass made `source:
lockfile` mean *"a package manager owns the version; every locus invokes the
tool through it, so there is nothing to keep in step"* — and that is the only
option which eliminates duplication rather than reconciling it. DOC-001's
`markdownlint-cli2` is the one tool in this register that qualifies.

**Nothing enforced the second half of that sentence.** Every locus invoked the
tool as `npx --no-install markdownlint-cli2`, and `--no-install` means *do not
fetch*, not *resolve locally*. With `node_modules` absent, npx falls through to
`PATH`. Measured in this container, in a repository with no local install:

```text
npx --no-install markdownlint-cli2 --version    exit 0   (a global answered)
npm exec --no -- markdownlint-cli2 --version    exit 0   (the same global)
node_modules/.bin/markdownlint-cli2 --version   exit 127
```

The global that answered was `markdownlint-cli2@0.23.2`, left on `PATH` by the
`setup.sh` that predates `bd23bfb` — the same version the lockfile pins, by
coincidence rather than by mechanism. A different one would have passed
identically, and DOC-001 would have reported a rule set enforced by a binary
nobody pinned.

So `source: lockfile` was a claim about where the version comes from, verified by
nothing about which artefact runs. `tool_versions_match_register` checks that
`package-lock.json` is tracked; it cannot check what a shell resolved.

This is not a defect confined to one control. Phase 2 builds the devcontainer
template and six gate skills, and its exit criterion reads: *"The template pins
no tool version by hand. Every tool it installs is either sourced from a lockfile
the consumer repo already commits, or from a single toolchain file."* That
criterion is about the **source** of a version. A template with exactly this hole
satisfies it, which makes it a criterion met in letter — the failure this
project's review record exists to catch, visible this time before the phase
rather than after it.

## Alternatives Considered

### Option 1: Keep `npx --no-install` and verify the version at runtime

Leave the invocation and have the assert run the tool, parse `--version`, and
compare it with the lockfile.

**Pros:** No change to any deployed artefact; catches a mismatched global
directly.
**Cons:** The checker would have to execute the tool to verify a wiring
property, which every other locus check avoids. It also verifies the wrong
moment: the version at audit time says nothing about the version the pre-commit
hook resolved an hour earlier. And it cannot distinguish "the right version, from
the wrong place" — a global that happens to match still means the lockfile is
not the authority.

### Option 2: Rely on `npm run` scripts

Declare a `lint:md` script in `package.json` and have every locus call
`npm run lint:md`.

**Pros:** One place to change the arguments; conventional in Node projects.
**Cons:** `npm run` *prepends* `node_modules/.bin` to `PATH` rather than
restricting to it, so a missing local install still falls through to a global.
It relocates the invocation without closing the hole, and adds a second file
(`package.json` scripts) that each locus's behaviour now depends on.

### Option 3: Invoke the artefact the lockfile owns, by path

Every locus runs `node_modules/.bin/markdownlint-cli2`. A missing local install
is exit 127, not a silent substitution.

**Pros:** The property becomes structural rather than checked after the fact —
there is no resolution order to reason about, because there is no search. It is
also readable: the invocation states where the binary comes from, so a reviewer
can see the authority in the line itself. Under
[ADR 0016](0016-exit-codes-for-unverifiable-controls.md) an absent artefact is
then `UNCLASSIFIED — cannot verify`, which is the honest verdict for a tool that
is not installed, where today it is a pass.
**Cons:** The path is npm's layout, so the register has to record it per tool
rather than deriving it. `node_modules/.bin` must exist before the gate runs,
which means every locus needs `npm ci` ahead of it — true already at each of
ours, and a real constraint on the Phase 2 template.

## Decision

We will invoke a `lockfile`-sourced tool by the path its package manager owns,
and record that path in the register as `tools.<tool>.invocation`.

The field pairs with `pinned_at` and the two are symmetric: a `literal` tool is
installed onto `PATH` at each locus, so the register records **where its version
is repeated**; a `lockfile` tool is resolved from a package tree, so the register
records **how the pinned artefact is reached**. Both are then verified rather
than trusted — `invocation` is required under `source: lockfile` and rejected
under `source: literal`, because a literal tool's pin is its version and not the
path it is reached by.

`markdown_gate_wired_at_all_loci` checks every declared locus against that form
rather than against the tool's name, so a locus reverting to `npx` fails with the
locus named. Option 3 was chosen over Option 1 because a property that holds by
construction beats one re-measured after the fact, and over Option 2 because
`npm run` moves the invocation without removing the fallback that caused the
problem.

## Consequences

**Positive outcomes:**

- `source: lockfile` now means what ADR 0018 said it meant. The authority is
  reachable in exactly one way, and the way is written down.
- An absent local install reports `UNCLASSIFIED — cannot verify` instead of
  passing on a global. That is ADR 0016's verdict for an absent tool, which
  DOC-001 was previously the one control to evade.
- Phase 2 gains a criterion that can fail. "The pin is what runs" is now
  demonstrable by deleting the artefact and watching the locus fail, rather than
  inferred from where the version is written.
- The hole is closed before six gate skills inherit it, which is the argument
  that created Phase 1.5.

**Trade-offs and risks:**

- Every locus must install the package tree before the gate runs. CI does
  (`npm ci`), the devcontainer does (`setup.sh`), and pre-commit relies on the
  devcontainer having done so. A locus that forgets now fails loudly, which is
  the intended direction but is a change from failing silently in the other
  direction.
- The recorded path is npm-shaped. A `lockfile` tool from another ecosystem —
  a Python console script from `.venv/bin`, a Go binary — records its own form,
  and the field is a plain string precisely so it can.
- `.pre-commit-config.yaml` and `.github/workflows/lint.yml` are `lint-md`
  artefacts, so this is a further hand-edit and widens the amend at
  [ee-skills-incubator#530](https://github.com/EqualExperts/ee-skills-incubator/issues/530).
- The check is per gate. Each Phase 2 gate applies it for its own tool, and a
  gate whose tool is not lockfile-sourced has nothing to apply — an absence that
  has to be deliberate rather than overlooked.

## Related ADRs

- [ADR 0018: Draw the Boundary Between Register and Checker](0018-register-checker-boundary.md)
  — established `source: lockfile`; this ADR makes its second clause verifiable.
- [ADR 0016: Exit Codes for Unverifiable Controls](0016-exit-codes-for-unverifiable-controls.md)
  — an absent tool is `UNCLASSIFIED`, which is what a missing local install now
  reports.
- [ADR 0019: Verify Exemptions Against the Files a Repository Tracks](0019-exemptions-cannot-hide-tracked-files.md)
  — the same move at the other end of the gate: what it checks, and now what
  runs it.
- [ADR 0013: One Markdown Rule Set, Deployed Not Duplicated](0013-one-markdown-rule-set.md)
  — DOC-001's rationale.

## References

- [markdownlint-cli2](https://github.com/DavidAnson/markdownlint-cli2) —
  DOC-001's cited standard and the tool in question.
- [npm-exec](https://docs.npmjs.com/cli/v11/commands/npm-exec) — the resolution
  order `--no-install` does and does not change.
- [`09-phase-1.5-review.md`](../09-phase-1.5-review.md) § H6 — the finding and
  its measurements.
