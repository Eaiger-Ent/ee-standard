# ADR 0057: `register-install` Writes the Conformance Step, and GOV-001 Fails Without It

**Status:** Accepted
**Date:** 2026-10-19
**Revision:** 1

## Background

**The problem.** In a repository adopted exactly as the skills describe, nothing
in CI asks the register for its verdict. Each gate writes CI steps that run its
tools — ruff, mypy, pytest, gitleaks — and some write a `register-check run
--control …` step for their own controls. None runs the whole register. So a
control whose tools pass and whose file asserts fail reads FAIL in a local run
and green in every build. In the Craft trial repository TYP-001 stood at FAIL
for 27 days, and LNT-001 for a week, under 148 green runs on `main`.

**The step exists; it is a hand step.** `docs/08-adopting.md` § 4.1 and § 4.3
tell the adopter to add a *Conformance* step running `uv run register-check`,
and checklist rows 8 and 10 depend on it. The trial repository's owner followed
the skills and did not take that step, and nothing told them. The sweep template
assumes it is there: *conformance drift is caught instead by that workflow's own
`schedule:` trigger*.

**Nothing notices its absence, because GOV-001 asks a narrower question.** GOV-001
passes when every blocking control is reached by a CI step that can fail. A step
running the control's *tool* counts as reaching it. So `uv run mypy` reaches
TYP-001, and GOV-001 passes, while TYP-001's own verdict — `files` does not cover
a tracked module — is computed nowhere CI runs.

**It cannot be a hook.** `CLAUDE.md` records why: a full run exits `3` locally
for good, because SEC-003's remote blocks answer only inside an Actions job, and
a hook that tolerated `3` would accept a run that verified nothing.

## Alternatives Considered

### Option 1: Keep it a documented step, and add nothing — Rejected

**Pros:** No change. The guide is already right about what the step should be.

**Cons:** It has been tried. The first repository adopted outside this one
missed it, and the cost was invisible for a month. A step that a check depends
on and nothing writes or reports is the *declared and unreachable* failure the
standard names theme T-3.

### Option 2: GOV-001 fails without a full-audit step, which stays a hand step — Rejected

GOV-001's file half also requires a gating step that runs the checker with no
`--control`.

**Pros:** The absence becomes a verdict, in a meta-control that already reads
the chain from control to merge.

**Cons:** GOV-001 itself is computed only by a full audit — the thing that is
missing. An adopter would learn of it from a local run or from the checklist,
which is where they learn it today. Detection without a writer moves the hand
step one document over.

### Option 3: A gate writes it — `gate-repo`, beside the ruleset that requires it — Rejected

**Pros:** CI-001's `required_checks:` names the conformance job, and `gate-repo`
writes the ruleset that waits for it.

**Cons:** `gate-repo` is the gate adopters most often cannot finish. Its apply
needs repository administration, and a private repository on GitHub Free has no
rulesets to apply (ADR 0047). The trial repository never ran it. Tying the one
step that computes every verdict to the gate most likely to be skipped is the
wrong dependency.

### Option 4: `register-install` writes it, and GOV-001 fails without it — Chosen

`register-install` puts the checker in the lockfile. The step's whole job is to
run that checker, and it is the first skill every adoption runs: nothing
downstream works without it.

**Pros:** The step arrives with the thing it runs, on every adoption, including
the ones that never reach `gate-repo`. GOV-001 then holds it in place: removing
the step fails GOV-001 in any full run, including a local one.

**Cons:** `register-install` has said until now that it *wires no locus*, and
[ADR 0032](0032-the-checker-is-installed-from-a-tagged-ref.md) decided it is a
skill *that owns nothing else*. Both change, for one step and with the reason
stated.

## Decision

**We choose Option 4: `register-install` writes a Conformance step that runs the
whole register in the gating workflow, and GOV-001's file half fails a
repository with no such step.**

**1. What the step runs.** `uv run register-check`, in the gating job, after the
frozen install, with `GITHUB_TOKEN` passed as `docs/08-adopting.md` § 4.1 shows.
A verified violation (exit `1`) fails it. Exit `3` passes, and only `3`, in the
shape § 4.3 already gives for a run without a credential — the report still
prints what was not verified. `--require-complete` is the adopter's upgrade once
a credential exists (checklist row 10), as it is today. This ADR moves who
writes the step and changes nothing about exit codes: that is
[ADR 0016](0016-exit-codes-for-unverifiable-controls.md)'s.

**2. Where it goes.** Into the job CI-001's `required_checks:` names, so the
check the ruleset waits for is the one that carries the verdict. If no gating
workflow exists, `register-install` creates one, as the gates do.

**3. No stamp.** No control is deployed by it — the reason
`register-install` writes none today, and the reason this repository's own
Conformance step carries none.

**4. GOV-001.** Its file half additionally requires a step, in a job the register
requires, that runs the checker with no `--control`. A register contract bump,
because a skill reading GOV-001 must understand it.

| | Before | After |
| --- | --- | --- |
| Who writes the Conformance step | The adopter, by hand, from § 4.3 | `register-install` |
| GOV-001 with no full-audit step | Passes if every control's tool is reached | Fails, naming the missing step |
| A file-assert FAIL with green tools | Seen only in a local run | Fails the required check |

## Consequences

**Positive outcomes:**

- **The register's verdict is computed where a merge waits for it**, in every
  adoption, from the first skill run. The trial repository's two FAILs would have
  failed its first pull request after they appeared.
- **The guide's hand step becomes a skill's**, and § 4.3 is left describing the
  exit-code choice rather than also carrying the step.

**Trade-offs and risks:**

- **An adoption fails its own CI until it is finished.** A repository that has
  run `register-install` and not yet `gate-repo` reads CI-001 FAIL on its file
  blocks, and its required check is red until the ruleset is recorded. That is
  the register being right about an unfinished adoption. It will still be met
  as friction, and `register-adopt`'s order should run `gate-repo`'s record half
  early.
- **Some command blocks run twice in CI.** The full audit runs `gitleaks
  detect`, `hadolint` and the rest that the gates' own steps already run. That
  costs minutes, not correctness. Removing the duplicates is a later
  optimisation, and removing them first would reopen this gap.
- **Existing adopters get the step only by re-running `register-install`**, and
  meet GOV-001's new requirement when they move to the new contract.

## Related ADRs

- [ADR 0016](0016-exit-codes-for-unverifiable-controls.md) — the exit codes the
  step reads, unchanged.
- [ADR 0047](0047-a-plan-limit-is-recorded-not-tolerated.md) — why a plan-limited
  repository's full run exits `3` at best, and so why the step tolerates `3`.
- [ADR 0039](0039-a-push-is-a-locus.md) — the hooks, and why the full run cannot
  be one.
- [ADR 0032](0032-the-checker-is-installed-from-a-tagged-ref.md) — installs the
  checker *by a skill that owns nothing else*. **This decision changes that
  clause**, for one step: if it is accepted, 0032's *owns nothing else* becomes
  *owns nothing else but the step that runs what it installs*, and 0032 is
  revised to point here rather than restating it.

## References

- [`docs/craft/review.trial.md`](../craft/review.trial.md) § The control
  register, in the same four weeks — the 27 days.
- [`docs/08-adopting.md`](../08-adopting.md) § 4.1 and § 4.3 — the step as the
  guide already gives it.
