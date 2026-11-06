# ADR 0061: A Rung Below Blocking Never Sets the Exit Code

**Status:** Accepted
**Date:** 2026-11-06
**Revision:** 1

## Background

**The problem.** The register has four rungs, and the checker treats them all
as `blocking`. `docs/00-concepts.md` § The enforcement ladder says a `warn`
control is "surfaced prominently, still does not fail the build", and an
`advisory` one "never fails anything". `runner.exit_code` never reads `rung`.
Any `FAIL` exits `1`, and any partial or unverified block exits `3`, whatever
the control's rung. Nobody has noticed because all 16 controls are `blocking`.

**Why it matters now.** [ADR 0023](0023-smallest-model-a-task-can-be-trusted-to.md)
adds `AGT-001`, the first control below `blocking`. It chose `warn` because a
`blocking` control "would fail every repository including this one on the day
it lands". It also gives AGT-001's verify block a `partial:`, with an expiry no
later than 2027-02-28, because runtime model selection cannot be read from
files. Under today's checker, both of those break the build:

| What AGT-001 does | What the checker does today | Effect in this repository's CI |
| --- | --- | --- |
| A definition file falls below its floor | `FAIL`, exit `1` | The required check fails |
| Every run, because of the `partial:` | Exit `3` | `--require-complete` turns `3` into `1`, so the required check fails on every pull request |

So the `warn` rung ADR 0023 chose would block every merge from the day AGT-001
lands, which is the outcome it chose `warn` to avoid. The second row is the
worse one: it fails on a repository that has done nothing wrong.

**Where the current behaviour comes from.** [ADR 0016](0016-exit-codes-for-unverifiable-controls.md)
keeps `1` for verified violations and reserves `3` for a run that could not
verify something. It was written when every control was `blocking`, and it does
not mention rungs. The rule that a partial denies exit `0` is the runner
combining ADR 0016 with [ADR 0017](0017-partial-verification-is-reported.md):
ADR 0017 itself says only that a partial is reported, and expires.

## Alternatives Considered

### Option 1: Only blocking controls set the exit code

**Chosen.** The exit code is computed over controls at `blocking` or
`blocking (baselined)`, and over meta-controls, which have no rung. A control
at `warn` or `advisory` is run and reported in full, with its verdict, its
partial and its rung, and contributes nothing to the exit code: neither `1`
for a `FAIL`, nor `3` for a partial or an unverified block.

This is what `docs/00-concepts.md` has said since Phase 0. The expiry still
bites: GOV-003 is a meta-control, so a partial past its expiry fails the run at
any rung, exactly as ADR 0017 intends.

### Option 2: A failing `warn` control exits `3`

**Rejected.** `3` means "no violation found, something unverified". A `warn`
control that fails has been verified and has found a violation, so `3` would
make the code mean two things. It also does not solve the problem: CI passes
`--require-complete`, which turns `3` into `1`.

### Option 3: A new exit code for a violation below blocking

**Rejected.** Every pipeline that reads `register-check` reads `0`, `1`, `2` and
`3`. Most CI treats any non-zero exit as failure, so an unknown code blocks
the build in exactly the case it was added to let through. And it would leave
the partial row in the table above unsolved.

### Option 4: `warn` stops the exit code on a `FAIL`, but a partial still counts

**Rejected.** It is the smallest change to ADR 0016 and keeps the rule that a
partial denies exit `0`. But it leaves the second row of the table: AGT-001's
partial would turn this repository's required check red on every pull request
until 2027-02-28. A rung that "does not fail the build" except on every run is
not that rung.

### Option 5: Leave the checker alone, and move AGT-001

**Rejected.** AGT-001 could land at `blocking` without its partial. That
reverses two things ADR 0023 decided, and an ADR that implements another
should not quietly overrule it. It would also leave `warn` and `advisory` in
the schema meaning something the checker does not do, for the next control to
find.

## Decision

**We choose Option 1: only controls at `blocking` or `blocking (baselined)`,
and meta-controls, set the exit code.**

| A control at | Its `FAIL` | Its partial or unverified block | In the report |
| --- | --- | --- | --- |
| `blocking`, `blocking (baselined)` | Exit `1` | Exit `3` | Unchanged |
| `warn` | No effect | No effect | Verdict, partial and rung, printed **above** the blocking results, with a summary line counting them |
| `advisory` | No effect | No effect | Verdict, partial and rung, in their usual order |
| Any meta-control | Exit `1` | Exit `3` | Unchanged. GOV-003 failing an expired partial counts at every rung |

Three rules come with it:

1. **Exit `0` means every blocking control was verified.** It says nothing
   about controls below `blocking`. The report is what says it, and it must:
   a `warn` result that is not printed has been silenced, not surfaced.
2. **`--require-complete` reads the same set.** It turns `3` into `1`, and only
   blocking controls and meta-controls can produce `3`. So it does not promote
   a `warn` control by the back door.
3. **This is a property of the register format, not of any repository.** What
   each rung means is defined by the schema, so it belongs in the checker, by
   [ADR 0018](0018-register-checker-boundary.md)'s test. ADR 0018's list of what
   the checker may hold gains this rule when it is implemented.

Ratified on 2026-11-06 by Nathan Carney, choosing Option 1 over Options 2 to 5
as set out above.

## Consequences

**What this buys:**

- `warn` and `advisory` do what `docs/00-concepts.md` has said they do. A rung
  is a decision about enforcement, and the checker now honours it.
- AGT-001 can land as ADR 0023 decided: at `warn`, with its partial, and with
  the required check still green.
- Promoting a control up the ladder changes the exit code, as the concepts doc
  says only an explicit decision may.

**Trade-offs and risks:**

- **A `warn` failure can be ignored.** That is what `warn` means, and why the
  concepts doc ties promotion to a decision with an owner and a date. The risk
  is the one ADR 0023 names, a control that stays advisory for a year. Its
  answer stands: AGT-001's `review_by` is the date its promotion is decided.
- **Exit `0` no longer means "nothing was unverified".** It means nothing
  blocking was. A reader who wants the whole picture reads the report, and a
  run with a `warn` partial prints it on every run. This narrows the composition
  of ADR 0016 and ADR 0017 described above, for controls below `blocking`
  only. Neither ADR's decision text changes.
- **An adopter's pipeline is affected only if it has a control below
  `blocking`.** No control in the register today is, so no adopter's exit code
  changes until AGT-001 lands, and AGT-001 then cannot fail their build.

## Related ADRs

- [ADR 0016](0016-exit-codes-for-unverifiable-controls.md): the exit-code
  contract. Unchanged for blocking controls; this ADR says which controls it
  is computed over.
- [ADR 0017](0017-partial-verification-is-reported.md): partial declarations
  and their expiry. The expiry still fails the run through GOV-003.
- [ADR 0018](0018-register-checker-boundary.md): why rung semantics belong in
  the checker.
- [ADR 0023](0023-smallest-model-a-task-can-be-trusted-to.md): AGT-001, the
  first control this decision applies to.

## References

- [`docs/00-concepts.md`](../00-concepts.md) § The enforcement ladder: the
  meaning of each rung, which this ADR implements.
- [`src/register_check/runner.py`](../../src/register_check/runner.py),
  `exit_code`: where the rung is not read today.
- [`.github/workflows/register-check.yml`](../../.github/workflows/register-check.yml):
  the `--require-complete` step that turns `3` into `1`.
