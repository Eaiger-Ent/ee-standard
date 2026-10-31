# ADR 0060: This Marketplace Mirrors the Lint Skills

**Status:** Proposed
**Date:** 2026-10-31
**Revision:** 1

## Background

**The problem.** Two Tier 1 controls are deployed by skills an outside adopter
cannot install. DOC-001 is deployed by `lint-md`, and YML-001 by `lint-yaml`.
Both are published only in `EqualExperts/ee-skills`, which is private
(`private: true`, measured 2026-10-31). So an adopter outside Equal Experts
wires both controls by hand, and each control added this way costs that adopter
more.

**What ADR 0044 decided.** Part 1 made `Eaiger-Ent/ee-standard`, which is
public, the marketplace the adoption guide names. Part 2 said a control whose
deploying skill an adopter cannot install is satisfied by hand, and verified by
the register. It also said nothing is copied: no skill from another plugin is
vendored into an adopter's repository, or into this one. Part 2 was written for
one control, DOC-001, and called "today the only one".

**It is no longer one.** YML-001 joined it on 2026-10-29 at register contract
37. The by-hand route for YML-001 is longer than DOC-001's. It has five
artefacts: `.yamllint.yml`, a PostToolUse hook script, its `.claude/settings.json`
entry, a pre-commit hook and a CI step. The hook script is the hard part. It is
70 lines of Python, and an adopter has no way to write it by hand except by
copying `lint-yaml`'s. That is the copy ADR 0044 forbids, made anyway, with no
record of which version it came from.

**A copy with a record is what this repository already does in the other
direction.** `control-register` is published from this tree to `ee-skills`.
`docs/promotion/published.json` and its digests record every difference between
the two copies, and `tests/test_published_copy.py` fails on one the record does
not declare. ADR 0044 called that "one artefact published twice, not a fork".
Nothing yet does the same for a plugin that flows from `ee-skills` to here.

**Three facts shape the options.**

- **The licence allows redistribution.** `EqualExperts/ee-skills` is licensed
  Apache-2.0, and each plugin carries the `LICENSE` file. Redistributing it
  publicly keeps that file.
- **Whether to publish is not ours to decide.** The repository is private by
  choice. A licence that permits redistribution does not mean its owners want
  the content public.
- **Each lint plugin declares a dependency this marketplace cannot satisfy.**
  Both `plugin.json` files list `"dependencies": ["ee-skills-contribute"]`. No
  file in either skill refers to `ee-skills-contribute`. A copy served from
  here, unchanged, would name a plugin an outside adopter cannot install.

## Alternatives Considered

### Option 1: Keep the by-hand route for both controls — Rejected

This is ADR 0044 part 2 as written. It works for DOC-001, whose six steps were
carried out and verified in Phase 4. For YML-001 it does not hold up. The editor
locus has no by-hand form except copying the hook script, and a copy with no
record is the failure part 2 exists to prevent. Each further control deployed from
`ee-skills` adds to the route an outside adopter walks by hand.

### Option 2: Write a gate for each control here — Rejected

`control-register` would gain a `gate-docs` and a `gate-yaml`. ADR 0044 rejected
this for DOC-001, and the reason is unchanged: two implementations of one
lifecycle, free to drift, one of which this repository would keep in step with
a skill it does not own. "Replacing `lint-md`" is out of scope in
[`04-build-plan.md`](../04-build-plan.md).

### Option 3: Ask for `ee-skills` to be made public — Rejected as the answer

This is the cleanest outcome, and the decision is not ours to schedule. ADR 0044
rejected waiting on it for the same reason. It is still worth asking for, and if
it happens this ADR's mirror becomes unnecessary and can be retired.

### Option 4: Mirror the two plugins here, held to the published copy — Chosen

`plugins/lint-md/` and `plugins/lint-yaml/` are copies of the trees published in
`ee-skills`, at a recorded version and commit. They are never edited here. A
record and a test hold each copy to what was published, which is the mechanism
`published.json` already uses, pointed the other way.

## Decision

**We choose Option 4: this repository's marketplace serves `lint-md` and
`lint-yaml` as mirrors of the copies published in `ee-skills`, and an outside
adopter installs them from here.** This supersedes ADR 0044 part 2. Part 1 is
unaffected.

**Precondition: the owners agree to the publication.** Nothing in this decision
is implemented until a maintainer of `EqualExperts/ee-skills` has agreed to
`lint-md` and `lint-yaml` being republished from a public repository. That yes
is recorded here, by name and date, when this ADR is accepted. If they refuse,
this ADR is rejected and ADR 0044 part 2 stands.

**What changes.**

| | Before (ADR 0044 part 2) | After |
| --- | --- | --- |
| Where an outside adopter gets `lint-md` and `lint-yaml` | Nowhere. Both controls are wired by hand | `claude plugin install lint-md@ee-standard`, and the same for `lint-yaml` |
| The editor hook script | Copied from somewhere, with no record | Deployed by the skill, from a recorded version |
| A provenance stamp naming `lint-md` | Forbidden, because `lint-md` did not run | Written by `lint-md` when it runs, as for an `ee-skills` install |
| `08-adopting.md` § 3 | The supported route for an outside adopter | A fallback, for an adopter who will not install a plugin |
| `marketplace.json` | `control-register`, `craft` | Adds `lint-md` and `lint-yaml` |

**The mirror rules.**

1. **A mirror is never edited here.** A change goes upstream first, as an
   incubator amendment (incubator#1220 was one), and comes back by re-mirroring
   the release that shipped it. There is no `owed-upstream` stance for a mirror,
   because a mirror ahead of its source is a fork.
2. **The record is a file and a test.** `docs/promotion/mirrored.json` holds,
   per plugin, the `ee-skills` version and commit mirrored and a digest of
   every file. A test fails on any file that differs from the record, and on a
   file present on one side only.
3. **One difference is allowed, and it is declared.** The mirror's `plugin.json`
   drops the `dependencies` key, which names a plugin this marketplace does not
   serve. The record declares that difference with its reason, as `by-design`,
   and the file may differ by nothing else. It is also asked of upstream: if
   `ee-skills` drops the unused key, the mirror becomes byte-identical and the
   declaration is removed.
4. **Re-mirroring is a script, run by hand.** It copies a plugin from the
   installed `ee-skills` marketplace checkout and rewrites the record, and with
   `--check` it reports whether the mirror is behind. CI cannot run it, because
   `ee-skills` is private. So a mirror that falls behind is reported, never
   enforced, which is how ADR 0038 treats a stale gate.
5. **The version is upstream's.** A mirror keeps the version number it was
   published with, so a stamp `ee-skill: lint-yaml@0.1.16` means the same thing
   whichever marketplace installed it. `register-check deployments` already
   strips the marketplace from an installed plugin's name.

## Consequences

**An outside adopter's route has no by-hand control left.** Every Tier 1
control is deployed by a skill they can install. Phase 9's item for a YML-001
by-hand route in `08-adopting.md` becomes an item to install `lint-yaml` from
this marketplace instead.

**This repository republishes two plugins it does not own.** That has a cost.
A defect in `lint-md` reaches outside adopters through this marketplace, and is
fixed here only by re-mirroring a release that fixed it upstream. A mirror can
fall behind for as long as nobody runs the script. The record names the version
it holds, so how far behind it is can be read.

**The marketplace changes what it serves, so ADR 0044's test must keep up.**
`tests/test_adopter_guide.py` derives the guide's marketplace from the register.
The guide will name `lint-md@ee-standard` and `lint-yaml@ee-standard`, so the
test needs to accept two more plugin names from the same address.

**ADR 0044 is amended, not archived.** Its part 1 stays in force, so it stays
Accepted. On acceptance of this ADR, ADR 0044 gains a revision noting that part
2 is superseded here, and it moves to `archive/` only if part 1 is superseded
too.

**The register does not change.** `deployed_by: lint-md` and
`deployed_by: lint-yaml` name skills, not marketplaces, and no control's `rung`,
`verify`, `variance` or `applies_to` moves. So the contract does not move.

## Related ADRs

- [ADR 0044](0044-the-adopter-installs-from-the-public-marketplace.md): part 1
  stays in force; part 2 is superseded here
- [ADR 0038](0038-the-stamp-records-the-deployment-contract.md): why a mirror
  that is behind is reported rather than enforced
- [ADR 0043](0043-a-declination-is-reconciled-against-the-installed-skill.md):
  how `deployments` reads the installed plugin, whichever marketplace it came
  from
- [ADR 0059](0059-yaml-is-linted-before-anything-reads-it.md): YML-001, the
  second control ADR 0044 part 2 was not written for

## References

- [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0), § 4:
  redistribution keeps the licence
- [Claude Code plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces):
  `marketplace.json` and a plugin's `source`
- [`docs/05-promotion.md`](../05-promotion.md) § What differs from the
  published copy: the record this mirrors
