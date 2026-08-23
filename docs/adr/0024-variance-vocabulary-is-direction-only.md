# ADR 0024: Keep Only Direction Values in the Variance Vocabulary

**Status:** Accepted
**Date:** 2026-08-23

Recorded retrospectively. The decision was taken and implemented at register
contract 3 on 2026-08-17 ([#8](https://github.com/Eaiger-Ent/ee-standard/pull/8)),
ratified from [`09-phase-1.5-review.md`](../09-phase-1.5-review.md) § E, and was
never given an ADR. It is written down now because it reversed the recorded
decisions of two Accepted ADRs — 0005 and 0012 — and nothing in `docs/adr/` said
so.

## Background

`variance` answers one question about a control: may a deployed artefact differ
from the register, and in which direction. At contract 2 the vocabulary had four
values:

| Value | What it permitted |
| --- | --- |
| `forbidden` | No deviation at all |
| `narrowing-only` | Tightening only; loosening requires a register change first |
| `justified` | **Any** direction, given a recorded reason, owner and expiry |
| `free` | Anything; the control merely had to exist |

`justified` was the value SUP-003 ([ADR 0005](0005-pinned-ci-actions.md)) and
IAC-001 ([ADR 0012](0012-iac-static-analysis.md)) carried, both for the same
reason: each anticipated a rare legitimate exception — an action publishing no
stable history, a policy finding that is a deliberate design — and wanted it
recorded and expiring rather than silent.

The Phase 1.5 review found the value structurally unimplementable rather than
merely unused. `00-concepts.md` § Variance stated that a justified weakening
**is** a baseline entry: the baseline is where the tolerated deviation gets
written down, owned and shrunk. But every Tier-1 control carries
`baseline: null` by design, and the validator rejects any Tier-1 control
carrying a baseline at all. SUP-003 and IAC-001 are both Tier 1. The mechanism
that stopped `justified` becoming a loophole was therefore unreachable for both
controls that used it, and for any Tier-1 control that could ever use it.

What remained was a value permitting weakenings it had no way to record — which
is theme **T-2** in its purest form: a rule whose enforcement mechanism and
whose stated intent had silently diverged. `free` had no users and asserted only
that a control exists, which is not a variance claim.

## Alternatives Considered

### Option 1: Keep `justified`, and let Tier-1 controls carry a baseline

Relax the validator so a `justified` Tier-1 control may record its exceptions in
the baseline, making the anti-loophole mechanism reachable as specified.

**Pros:** Preserves both ADRs' intent exactly; no ADR is overtaken; the rare
legitimate exception keeps the home its authors designed for it.
**Cons:** `baseline: null` on every Tier-1 control is not an incidental
validator rule — it is what "Tier 1" means in this register. GOV-002 fails a
baseline that grows, so a Tier-1 baseline turns the strongest tier into the one
tier whose tolerated violations may expand. Buying two controls their exception
mechanism by weakening the tier definition for all thirteen is the trade this
repository exists to refuse.

### Option 2: Keep `justified`, record exceptions in the verify block instead

Give `justified` its own exception list beside the assert, separate from the
baseline, with reason, owner and expiry per entry.

**Pros:** Reachable for Tier-1 controls; keeps the recorded-and-expiring
property both ADRs asked for.
**Cons:** A second shrink-only tolerated-deviation list with its own expiry
semantics, beside the baseline that already is one. Two mechanisms for one
concept drift, and GOV-002 would check one of them. This is the duplication the
core invariant names by name.

### Option 3: Remove `justified` and `free`; move both controls to `narrowing-only`

Reduce the vocabulary to the two values that state a direction, and let a
control needing a genuine exception change its register entry — which is a
reviewed diff — rather than carrying standing permission to deviate.

**Pros:** Every remaining value is implementable as specified. Both affected
controls move **stricter**, so no control is loosened by the removal and no
deployed artefact becomes non-conformant. The exception route survives: it is a
pull request against `controls.yaml`, which is more visible than a list nothing
reads, not less.
**Cons:** Overtakes the recorded reasoning of two Accepted ADRs. A real
exception now costs a register change rather than a line in a list — deliberate
friction, but friction, and it arrives at the moment someone is under deadline.

## Decision

We will keep only the two values that state a direction — `forbidden` and
`narrowing-only` — and remove `justified` and `free` from the vocabulary.
SUP-003 and IAC-001 move to `narrowing-only`.

Option 3 is chosen because it is the only one under which every value in the
vocabulary can be implemented as written. Options 1 and 2 both keep `justified`
by building it a home, and the homes cost more than the value is worth: one
weakens what Tier 1 means, the other adds a second tolerated-deviation list
beside the baseline.

The direction of the change is what makes it safe to make retrospectively.
`narrowing-only` is strictly stricter than `justified`, so no control was
loosened, no deployed artefact was invalidated, and nothing that passed before
the change fails after it. `tests/test_schema.py::test_justified_variance_is_no_longer_in_the_vocabulary`
holds the closed set, so a register reintroducing the value is a schema error
rather than a silently accepted field.

**What replaces the mechanism, for the case both ADRs were worried about.** A
legitimate exception is still recordable, and in a stronger place: the control's
entry in `controls.yaml`. ADR 0005's action-with-no-stable-history and ADR
0012's deliberate-design-flagged-by-checkov are both answerable by narrowing the
control's `applies_to`, by an `args:` allow-list read by the assert, or — if
neither fits — by a register change reviewed as a pull request. What is gone is
standing permission to deviate without one.

**This ADR does not supersede ADR 0005 or ADR 0012.** Their decisions — pin
third-party actions to commit SHAs, run checkov and tflint with blocking exit
codes — are unchanged and still correct, and both remain the `rationale_adr` for
their controls. Only the variance value each recorded is overtaken. Each carries
a dated amendment pointing here, which is the same treatment ADR 0006 and ADR
0016 already use for a decision that stands with a clause that did not.

## Consequences

**Positive outcomes:**

- Every value in the variance vocabulary is implementable as specified, which
  was not true of the four-value set for either control that used the fourth.
- The removal is recorded where a reader of the ADR corpus will find it. Before
  this, two Accepted ADRs stated a value the schema rejects, and the only
  account of why lived in `00-concepts.md` and a build-plan tickbox.
- An exception now leaves a reviewed diff against the register rather than an
  entry in a list nothing enforced.

**Trade-offs and risks:**

- Writing an ADR six days after the change it records is itself the defect this
  ADR reports. The register moved and the decision record did not; that gap was
  found by an audit rather than by the process, and nothing yet prevents the
  next one.
- A genuine SUP-003 or IAC-001 exception is now more expensive to record. If one
  arrives and the cost is paid by suppressing the finding instead, this decision
  will have made the repository less honest rather than more, and the answer is
  a register change rather than a fourth variance value.
- Two ADRs now carry an amendment contradicting a paragraph of their own
  Alternatives Considered. The amendment says so explicitly rather than editing
  the original reasoning away, because what was considered at the time is the
  part of an ADR worth keeping.

## Related ADRs

- [ADR 0005: Pin CI Actions to Commit SHAs](0005-pinned-ci-actions.md) —
  SUP-003, one of the two controls whose recorded variance this overtakes.
- [ADR 0012: Statically Analyse Infrastructure Code Before Apply](0012-iac-static-analysis.md)
  — IAC-001, the other.
- [ADR 0019: Verify Exemptions Against the Files a Repository Tracks](0019-exemptions-cannot-hide-tracked-files.md)
  — rejected its Option 2 as "`justified` under another name, removed at
  contract 3", which is the reasoning this ADR should have held.
- [ADR 0018: Draw the Boundary Between Register and Checker](0018-register-checker-boundary.md)
  — the variance vocabulary is a property of the register format, so the closed
  set stays in the checker under its test.

## References

- [`00-concepts.md`](../00-concepts.md) § Variance — where the removal has been
  recorded since contract 3, and the only account of it until this ADR.
- [`09-phase-1.5-review.md`](../09-phase-1.5-review.md) § E — the finding that
  `variance` was read by no code path and that one of its four values could not
  be implemented as specified.
- [`04-build-plan.md`](../04-build-plan.md) — the exit criterion "`variance:
  justified` is implementable or removed", ticked as removed with `free`.
- [`01-register-schema.md`](../01-register-schema.md) § Variance — the closed set
  as the schema now enforces it.
