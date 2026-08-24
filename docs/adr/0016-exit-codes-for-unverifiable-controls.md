# ADR 0016: Give "Could Not Verify" Its Own Exit Code

**Status:** Accepted
**Date:** 2026-08-17
**Revision:** 5

Ratified decision from
[`09-phase-1.5-review.md`](../09-phase-1.5-review.md) § Decisions required.

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

**Amended 2026-08-23: the third bullet is no longer true, and the bound has
moved.** Phase 3 implemented `kind: remote` verification and the tolerance did
not expire. The reason is one this ADR could not have known: the Actions
`GITHUB_TOKEN` cannot read `security_and_analysis`, so SEC-001's remote block is
`UNCLASSIFIED` in CI while passing locally — an under-scoped token, which
[ADR 0021](0021-how-remote-verification-authenticates.md) settled must refuse to
guess rather than report a violation it did not observe. Satisfying Phase 3 was
necessary and turned out not to be sufficient.

The tolerance is now bound by
[ADR 0022](0022-a-platform-token-ci-carries.md) instead: it ends when
requirements 1 and 2 of § What the register must gain land and CI carries a
platform token the register can see. That ADR records the reason and accepts the
cost by name.

The first two bullets are unchanged and still hold — only exit `3` is tolerated,
and the incompleteness is still printed on every run. What is recorded here is
that "expires by construction" was a claim about a mechanism, and the mechanism
had a second precondition nobody had looked for. A bound that moves is
acceptable; a bound that moves without the ADR stating it is the drift this ADR
exists to end, and it stood unamended for the six days between Phase 3 landing
and the audit that found it.

What is *not* tolerated is the version of this that would have been easier:
removing `standard-check` from the ruleset's required checks. A gate that exists
but is not a required check is theme **T-3** — declared and unreachable — which
is the failure GOV-001 exists to catch and the one this repository was founded
on.

**Amended 2026-08-24: the tolerance has ended, and one narrower case replaces
it.** The `Standard` workflow's Conformance step passes `--require-complete`.
A run that cannot verify a control now fails, rather than printing that it could
not and passing anyway.

Two things had to land, and neither alone was enough. `PLATFORM_READ_TOKEN`
(register contract 25) let SEC-001 and SEC-003 answer in CI, which is the bound
the 2026-08-23 amendment moved this to. And GOV-001 dropped its `partial:`
(contract 26), which had denied the run a `0` **by design** whatever the
credentials — ADR 0017 gives a partial that property precisely so a control
cannot be part-verified quietly. The 2026-08-23 amendment named the token and
not the partial, so the bound it moved to was still short by one thing; that is
recorded here rather than smoothed over, because this ADR has now twice named a
condition that turned out to have a second precondition nobody had looked for.

**The case that survives is a fork.** A pull request from a fork receives no
repository secret, so `${{ secrets.PLATFORM_READ_TOKEN || github.token }}`
resolves to the job token, SEC-001's remote block cannot read
`security_and_analysis`, and the run reports `UNCLASSIFIED` for a control that
holds. Failing there would fail a contributor for a credential this repository
deliberately does not give them. A fork run therefore tolerates exit `3`, and
only `3`.

It is a narrower exception than the one it replaces and it is bounded
differently — not by a phase or an ADR, but by a fact about the platform that
will not change: a fork does not get the secret. Its two guards are the first
two bullets above, unchanged: a verified violation still fails, and the
incompleteness is still printed. What is new is that the carve-out is
**exercised** — `tests/test_conformance_step.py` runs the step's script with the
checker stubbed and asserts both branches, because a tolerance nobody exercises
is one that quietly becomes general, which is what happened to the tolerance
this replaces.

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
- [ADR 0022: What Must Be True Before CI Carries a Platform Token](0022-a-platform-token-ci-carries.md)
  — where the ratified tolerance's bound moved to, per the amendment above.
- [ADR 0021: How Remote Verification Authenticates](0021-how-remote-verification-authenticates.md)
  — the four outcomes that produce the incomplete state, and why an under-scoped
  token refuses to answer rather than reporting a violation.
- [ADR 0020: Invoke a Pinned Tool by the Path Its Lockfile Owns](0020-a-locus-reaches-the-pinned-artefact.md)
  — reads an absent artefact as `UNCLASSIFIED` under these semantics.
- [ADR 0018: Draw the Boundary Between Register and Checker](0018-register-checker-boundary.md)
  — landed these semantics in the same contract-3 pass, and classifies which
  rules deciding a verdict may live in the checker at all.
- [ADR 0023: Choose the Smallest Model a Task Can Be Trusted To](0023-smallest-model-a-task-can-be-trusted-to.md)
  — AGT-001's unverifiable runtime half produces the same incomplete state.

## References

- [argparse — exit status 2 for usage errors](https://docs.python.org/3/library/argparse.html)

## Revision History

| Rev | Date | What changed | Ratified by |
| --- | --- | --- | --- |
| 1 | 2026-08-17 | Original decision: exit `3` for unverified-but-not-violated, `1` for verified violations, `0` for a complete run, and `--require-complete` to promote `3` to `1`. | Nathan Carney |
| 2 | 2026-08-17 | Ratified with one clause overtaken between drafting and ratification: ADR 0014 was implemented and the repository made public, but `kind: remote` stayed deferred to Phase 3, so the red state persists until Phase 3 rather than until 0014 resolves. | Nathan Carney |
| 3 | 2026-08-17 | § Ratified tolerance added on implementation. `main` became a required status check with no bypass actors, so "CI turns red" had become "no pull request can merge, including the ones that would fix it". The workflow tolerates exit `3` and only `3`. | Nathan Carney |
| 4 | 2026-08-23 | § Ratified tolerance's third bullet corrected. "Expires by construction" did not hold: Phase 3 landed and the tolerance did not expire, because the Actions `GITHUB_TOKEN` cannot read `security_and_analysis`. The bound moved to [ADR 0022](0022-a-platform-token-ci-carries.md) requirements 1 and 2. | Nathan Carney |
| 5 | 2026-08-24 | § Ratified tolerance ended. The Conformance step passes `--require-complete`; a pull request from a fork tolerates exit `3` and only `3`, because a fork receives no repository secret. Records that the 2026-08-23 bound named the token and not GOV-001's `partial:`, and so was short by one thing. | Nathan Carney |

Revisions before 2026-08-23 are backfilled from the amendments in the body and from git, per [ADR 0025](0025-an-amendment-is-a-recorded-revision.md); they were not recorded at the time.
