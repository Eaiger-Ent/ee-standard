# ADR 0038: A Provenance Stamp Records the Deployment Contract of the Gate That Wrote It

**Status:** Accepted
**Date:** 2026-08-26
**Revision:** 1

## Background

Phase 5's first two exit criteria are one sentence split in half: *bumping a
gate's version without changing its output produces no redeployment
recommendation*, and *bumping its contract version does*. They are the whole
noise argument. A mechanism that fires on every release is ignored within a
month, and one that fires on nothing is invisible.

The design that answers them was settled in Phase 2 and is recorded in
[`02-skill-family.md`](../02-skill-family.md) § Staleness: each gate declares a
`contractVersion` in `.claude-plugin/deploys.json` that moves only when what the
gate writes changes, and *"redeployment is recommended when the installed
contract version is ahead of the one stamped in the repo"*.

The stamp does not carry it. What a stamp records today is:

```text
# ee-control: SEC-001  ee-skill: gate-secrets@0.1.0  register: v0.15.0  register-contract: 15
```

Four fields: the control, the skill and its version, and the register's version
and contract. The gate's deployment contract is in none of them, so the
comparison the design names has nothing on the repository's side to compare
against. `docs/00-concepts.md` § The provenance stamp states the row —
*"Deployed and stale | Stamp is behind the installed skill's deployment contract
or the register contract"* — as though the number were there.

Nothing caught it because nothing read `deploys.json`. The sidecar is held to
the register by `tests/test_plugin.py` in the direction that can be wrong (a
control the register marks `deployed_by: <gate>` appears under that gate), and
`provenance_stamp_present` reads a stamp back for soundness and never for
currency. Both halves are correct on their own terms and neither joins the
other, which is the shape § H found four times in Phase 1.5.

**The skill version cannot stand in for it.** Every gate stamp in this
repository reads `@0.1.0`, because a skill has no version of its own: the eight
skills share `plugin.json`'s. So a version is not a per-gate fact at all, and
any rule derived from it — *this gate's output changed at version X* — would
move all six gates the moment one of them shipped. That is precisely the
plugin-wide contract the sidecar exists to avoid, reintroduced one level down.

## Alternatives Considered

**A version-to-contract history in the sidecar.** Give each gate a
`contractSince` naming the skill version its current `contractVersion` shipped
in, and compare the stamped version against it. It needs no stamp change and
classifies today's stamps immediately. It fails on two counts: the six gates
share one version, so `contractSince` would be a claim about a number that moves
for reasons unrelated to the gate; and it is an unverifiable assertion — nothing
can check that `contractSince: "0.3.0"` is the release the output actually
changed in, so a bumped `contractVersion` with a forgotten `contractSince`
silently reports every deployment current.

**A sidecar written into the adopting repository.** Have each gate record
`gate → contractVersion` in a file at the target repo's root. It works, and it
is a second copy: the stamps already say which gate wrote which artefact, and a
per-repo ledger beside them can disagree with them. The failure mode is the one
this register exists to prevent, bought to save a field.

**Hand-refreshing the existing stamps.** Rejected on the phase's own terms: a
stamp is what wrote the artefact, and writing `gate-contract: 4` into a file
deployed at some unrecorded earlier contract records a redeployment that did not
happen. Phase 5's exit criteria name that act specifically as not one of the
outcomes.

## Decision

**A provenance stamp records the deployment contract of the gate that wrote it**,
as a fifth field, immediately after the skill it qualifies:

```text
# ee-control: SEC-001  ee-skill: gate-secrets@0.1.0  gate-contract: 5  register: v0.23.0  register-contract: 30
```

The number is `gates.<gate>.contractVersion` from the plugin's `deploys.json`,
read at deploy time by the gate that is writing, from the file it ships with. It
therefore cannot drift: the writer and the declaration are the same artefact.

Four consequences follow directly, and each is one of the phase's criteria:

1. A skill version bump with no output change leaves `contractVersion` alone, so
   every stamp still matches and nothing is recommended.
2. A contract bump makes the installed number higher than every stamp naming
   that gate, and the gate is reported stale.
3. A gate with no stamp anywhere in the repository has never been deployed,
   which is a different report from a stamp that is behind.
4. A stamp naming a contract the installed gate has not reached is a defect, as
   a register contract ahead of the register already is.

**The field is optional in the parser, and its absence is its own state.** Every
stamp written before this ADR lacks it, and the honest report for those is
neither current nor stale but *unrecorded* — the deployment predates the field
that would have said. They resolve when each gate next deploys, by deployment
and not by editing.

**Every gate's `contractVersion` bumps in the change that adds the field**,
because a stamp is output and every gate's output moves. That is not a
side-effect to be worked around; it is the mechanism reporting itself correctly
the first time it is asked.

## Consequences

`register-check deployments` is the reader, and this repository is its first
subject: six gates, every one of them reporting *unrecorded* until it is
redeployed. A report whose every row says the same thing is a weak
demonstration, so the states are held apart by `tests/test_deployments.py`
rather than by what this repository happens to look like on the day.

Staleness stays **reported, never enforced** ([`00-concepts.md`](../00-concepts.md)
§ Notify, never redeploy): the command exits `0` over any number of stale or
undeployed gates and non-zero only for a defect — a stamp ahead of the installed
gate, or naming a control the register does not define. The Tier-1 ratchet that
`02-skill-family.md` § Loudness describes for a conformance *run* is not part of
this decision and is not implemented by it.

The cost is that the stamp is one field wider in twelve files' worth of
templates and in every artefact deployed from here on, and that
`docs/00-concepts.md`'s example, the gate skills' substitution steps and
`register-adopt`'s reading step all had to move together. They are the four
readers `provenance.py` was written to keep in step, and the pattern is still
defined once.

## Related ADRs

- [ADR 0018](0018-register-checker-boundary.md) — the deployment contract is a
  plugin fact rather than a register one, which is why it is not in
  `controls.yaml`
- [ADR 0026](0026-an-adr-stands-on-its-own.md) — this supersedes nothing;
  `02-skill-family.md`'s design is unchanged, and what changes is that the
  number it compares now exists

## References

- [`02-skill-family.md`](../02-skill-family.md) § Staleness
- [`00-concepts.md`](../00-concepts.md) § The provenance stamp
- [`04-build-plan.md`](../04-build-plan.md) § Phase 5
