# ADR 0016: Give "Could Not Verify" Its Own Exit Code

**Status:** Accepted
**Date:** 2026-08-17

Ratified decision from
[`04-build-plan.md`](../04-build-plan.md) § Phase 1.5 § Decisions required.

**Not yet implemented.** Acceptance settles the semantics, not the code:
`standard-check` still exits `0` on `SKIPPED (no credentials)`, still reports an
absent binary as `FAIL` rather than `UNCLASSIFIED`, and `--require-complete`
does not exist. Phase 1.5's exit criteria track that work.

## Background

`standard-check` currently exits non-zero only on `FAIL` or `UNCLASSIFIED`. A
`SKIPPED (no credentials)` verdict leaves the exit code at `0`, so the run that
cannot verify SEC-001's push protection or any of CI-001 reports the same status
as a run that verified everything and found nothing wrong. The report prints an
explicit *"this report is incomplete"* note, but the exit code is the only thing
CI reads, and the `Standard` workflow has been green over two unverified Tier-1
controls since it was created.

The build plan already demands otherwise in two places. Phase 1's criterion says
neither skip is *"counted as a pass in the exit code"*; Phase 3's says that with
no credentials *"the run does **not** exit 0 on that basis alone"*.

A second, separate case needs the same treatment. When a gate's binary is
absent — `hadolint`, `checkov` and `tflint` are not installed in this
container — the command block fails and the control reports `FAIL`. So "I could
not check this" is reported identically to "this repository violates the
control". The `UNCLASSIFIED` verdict exists for exactly this and is currently
unreachable from every code path.

So there are four distinct states, and today only three are distinguishable:
verified pass, verified violation, not applicable (a predicate skip, which is
genuinely fine), and **could not verify** — which currently splits confusingly
across a silent `0` and a misleading `FAIL`.

## Alternatives Considered

### Option 1: Keep exit 0 and rely on the report text

Leave the semantics alone; expect readers to notice the note.

**Pros:** No caller has to change.
**Cons:** Contradicts two written exit criteria, and a note no machine reads
cannot gate anything. This is the state that produced a green pipeline over two
unverified Tier-1 controls.

### Option 2: Treat "could not verify" as failure

Any unverifiable control exits `1`.

**Pros:** Simple, and safe in the direction that matters — the authoritative
pipeline cannot be green on incomplete evidence.
**Cons:** Every developer run without credentials goes red, permanently and
unavoidably. The register's own noise argument applies: a signal that is always
red is one people stop reading, and it makes a real violation harder to see, not
easier.

### Option 3: A distinct exit code for incompleteness

Reserve a third code: `0` all applicable controls verified and passing, `1` at
least one verified violation, `3` no violations but at least one control could
not be verified. Add a flag — `--require-complete` — that promotes `3` to `1` for
the pipeline that must be authoritative.

**Pros:** The three outcomes a caller actually cares about are separable, so CI
can demand completeness while a local run distinguishes "clean" from "clean as
far as I could tell". Predicate skips stay `0`, because not-applicable is a
legitimate pass. `3` rather than `2` because argparse already reserves `2` for
usage errors, and colliding those two would be a fresh ambiguity.
**Cons:** Callers must learn a third code, and the flag is extra surface. The
default remains permissive, so the workflow has to opt in — an omission would
reproduce today's silence.

## Decision

We will reserve exit code `3` for a run in which no violation was found but at
least one applicable control could not be verified, keep `1` for verified
violations, keep `0` for a run in which every applicable control was verified,
and add `--require-complete` to promote `3` to `1`.

`SKIPPED (no credentials)` and a control whose tool is absent both produce this
state, the latter reported as `UNCLASSIFIED` rather than `FAIL`, which gives that
verdict its first producer. `SKIPPED (predicate)` continues to exit `0`: a repo
with no Terraform genuinely satisfies IAC-001's applicability, and conflating
not-applicable with unverified would make the code meaningless in the common
case. The repository's own `Standard` workflow will pass `--require-complete`,
so this repo's CI turns red until [ADR 0014](0014-satisfying-remote-locus-controls.md)
is resolved — which is the correct reading of its current state.

Ratified on 2026-08-17. One clause above was overtaken between drafting and
ratification: ADR 0014 is now implemented and this repository is public, but
`kind: remote` verification remains deferred to Phase 3, so the credentials are
still not read and the red state persists until Phase 3 lands rather than until
0014 resolves. The exit-code semantics ratified here are unchanged by that.

### Ratified tolerance — the `Standard` workflow, until Phase 3

Amended 2026-08-17, on implementation. The clause committing this repository's
own workflow to `--require-complete` was written when `main` was unprotected. It
is now a **required status check** with no bypass actors, so the ratified
consequence changed under us: "CI turns red" became "no pull request can merge,
including the pull requests that would remove the incompleteness". A standard
that forbids its own remediation has stopped being a standard.

The workflow therefore tolerates exit `3` — and only `3` — until Phase 3
implements `kind: remote` verification. This is a bounded exception, recorded
here rather than left as a comment in YAML, because an unrecorded tolerance is
indistinguishable from the silence this ADR exists to end. Three things bound
it:

- The tolerance is **exit-code-specific**. A verified violation still exits `1`
  and still fails the check; only "could not verify" is tolerated.
- The incompleteness is **still loud**: the report prints the note, the summary
  counts the skips, and both appear in the workflow log on every run.
- It **expires by construction**. Phase 3's exit criteria require that with no
  credentials the run does not exit 0 on that basis alone, so satisfying Phase 3
  is what flips the step to `--require-complete`; the tolerance cannot outlive
  the condition that justified it.

What is *not* tolerated is the version of this that would have been easier:
removing `standard-check` from the ruleset's required checks. A gate that exists
but is not a required check is theme **T-3** — declared and unreachable — which
is the failure GOV-001 exists to catch and the one this repository was founded
on.

## Consequences

**Positive outcomes:**

- The authoritative pipeline can no longer be green on evidence it never
  gathered.
- "Cannot verify" stops masquerading as "violates", so a missing binary is
  diagnosable from the verdict alone.
- Phase 3's criterion becomes satisfiable without making local runs useless.

**Trade-offs and risks:**

- Three success-ish codes are more than most tools have, and anything consuming
  the exit status must be updated; the flag must be set in CI or the default
  permissiveness hides the very thing this fixes.
- Phase 2's gate skills verify through the same asserts, so they inherit these
  semantics — which is the reason to settle it before they are written rather
  than after.

## Related ADRs

- [ADR 0017: Report a Partially Implemented Control as Partial](0017-partial-verification-is-reported.md)
  — the other half of the same honesty problem, and a second producer of the
  incomplete state.
- [ADR 0014: Make Remote-Locus Controls Satisfiable on This Repository](0014-satisfying-remote-locus-controls.md)
  — resolving it is what returns this repository to exit `0`.
- [ADR 0011: Make Test Failures Terminal](0011-test-failures-are-terminal.md) —
  the same principle applied to a test suite's exit code.

## References

- [argparse — exit status 2 for usage errors](https://docs.python.org/3/library/argparse.html)
