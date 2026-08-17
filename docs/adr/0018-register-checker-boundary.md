# ADR 0018: Draw the Boundary Between Register and Checker

**Status:** Accepted
**Date:** 2026-08-17

Ratified decision from
[`04-build-plan.md`](../04-build-plan.md) § Phase 1.5 § Decisions required.

**Not yet implemented.** Acceptance settles the test and what it classifies, not
the code: every rule listed below is still in Python, SUP-001 still exempts Go,
Rust and Java by accident, and the register has no field for any of it. Phase
1.5's exit criteria track that work.

## Background

The core invariant is that a register entry **is** the control, and that every
other artefact derives from the register rather than restating it. § E of the
build plan found that `standard-check` breaks this in about a dozen places. Each
of the following decides a verdict and is recorded only in Python:

- ruff, eslint, mypy and pytest as *the* mandated tools
- the `charliermarsh.ruff` extension ID as proof of an editor locus
- the six accepted spellings of a test command
- a lockfile map covering Python and Node only
- the Dependabot ecosystem spellings
- the seven-name, case-sensitive cloud-key list
- the failure-suppression patterns
- the predicate grammar
- the `GOV-\d{3}` ID pattern, `rationale_adr` file existence, strict semver, and
  the Tier-1 baseline rule

This is theme **T-2** — a second copy of a rule that can drift from the
register — with the aggravation that the second copy is in a different language
and therefore invisible to anyone reviewing `controls.yaml`.

The harm is not hypothetical. SUP-001's lockfile map knows Python and Node, so a
Go, Rust or Java repository with no lockfile at all passes a Tier-1 control. The
decision to scope SUP-001 to two ecosystems was never taken; it is an artefact of
which dictionary keys someone wrote. Nothing in the register records it, so
nothing can review it and no `review_by` date will ever surface it.

The converse error exists too. GOV-001 reads `kind: command` blocks and ignores
`kind: file` ones, so SUP-002 and DEV-001 — blocking, `ci`, and verified only by
file asserts — have no command token at all and can never be found reachable.
Six further controls collapse to the single token `standard-check`. Whether that
is a checker bug or a register modelling error cannot be answered without
knowing where the boundary is.

Phase 2 copies the assert layer into six `gate-*` skills. Whatever is on the
wrong side of this line gets six more copies, which is the same argument that
created Phase 1.5.

Not everything belongs in the register. How to parse a YAML workflow, what
counts as a step, how to walk a `pyproject.toml` — these are implementation, and
moving them into the register would make it a program. The question is not
*whether* the checker holds knowledge but *which* knowledge it may hold.

## Alternatives Considered

### Option 1: Leave the boundary where it is

The register records intent; the checker records how intent is detected.

**Pros:** No work, and no `register_contract` bump. Arguably the boundary most
tools draw.
**Cons:** Does not survive its own example. "A lockfile is required" is intent;
"only Python and Node repos need one" is also intent, and it lives in the
checker. The distinction between intent and detection is not observable from
either artefact, so in practice every disputed rule lands wherever it was first
written.

### Option 2: Move every verdict-deciding rule into the register

If a rule can change a verdict, it is a control detail and belongs in
`controls.yaml`.

**Pros:** Maximally faithful to the core invariant, and trivially decidable.
**Cons:** The predicate grammar and the YAML-walking rules can change verdicts
too, and expressing them in the register turns it into a policy language — a
real project, and one this plan explicitly excludes. It also makes the register
version-lock to the checker's internals, which is the coupling `register_contract`
exists to avoid.

### Option 3: Classify by whether a consumer would vary it

A rule belongs in the register if a reasonable Equal Experts repository might
need it to differ **without** a checker change. Everything else is the checker's
business.

Applied to the list above: mandated tools, lockfile ecosystems, test-command
spellings, cloud-key names, Dependabot ecosystems and suppression patterns move
to the register — a consumer repo could legitimately need any of them to differ.
The predicate grammar, the ID pattern, semver strictness, `rationale_adr`
existence and the Tier-1 baseline rule stay in the checker: they are properties
of the register format, not of any consumer, and a repo needing them to differ is
a repo asking for a different standard.

**Pros:** One test, answerable per rule, and it produces a defensible answer for
every item § E lists. It also names *why* something stays — being a fact about
the format rather than about a repo — so future additions can be classified the
same way rather than by precedent.
**Cons:** "Might reasonably need" requires judgement, and the boundary will be
argued at the margin. The move is a schema addition and therefore a
`register_contract` bump; done late it invalidates deployed artefacts twice.

## Decision

We will classify every rule that decides a verdict by a single test — *could a
reasonable Equal Experts repository need this to differ without changing the
checker?* — move the rules that answer yes into `controls.yaml`, and record in
this ADR the rules that answer no together with the reason they are properties of
the register format rather than of any repository.

The move lands in the same pass that bumps `register_contract` to 3, alongside
[ADR 0017](0017-partial-verification-is-reported.md)'s partial-declaration field
and the unknown-key rejection. Batching them is deliberate: each bump marks every
deployed artefact stale, and three bumps for one phase's work would train
consumers to ignore the signal that staleness is supposed to carry.

Option 2 was rejected because expressing the predicate grammar in the register
makes the register a program, which the build plan excludes by name. Option 1 was
rejected because it has already failed in the one case that was measured: SUP-001
silently exempts three major ecosystems, and no reading of "the register records
intent" would have caught it.

Ratified on 2026-08-17. The classification above is the ratified part; the list
is not closed, and a rule discovered later is classified by the same test rather
than by where it happens to have been written. A rule that stays in the checker
must carry its reason in this ADR — an unreasoned omission is the failure this
record exists to stop, not an application of it.

### Applied — first pass, register contract 3

| Rule | Where it lives now | Why |
| --- | --- | --- |
| Package ecosystems: manifests, lockfiles, Dependabot spellings | Register, `ecosystems:` | The measured harm. A repo may legitimately use a lockfile spelling the checker has not heard of, and the checker-side map exempted Go, Rust and Java from SUP-001 entirely |
| Pinned tool versions and the gitleaks checksum | Register, `tools:` | Four documents already claimed the register held these. A repo pinning a different markdownlint-cli2 is an ordinary variance, not a checker change |
| `requirements.txt` as a lockfile | Removed | It pins nothing. Accepting it was a false negative (§ D), not a policy |

Asserts now take the register as well as the repository. An assert that cannot
read the register has nowhere to read a register-owned rule from, which is how
the checker became a second source of truth in the first place.

### Staying in the checker — with reasons

| Rule | Why it is not a register fact |
| --- | --- |
| `github-actions`, `devcontainers`, `docker`, `terraform` Dependabot spellings | Not package ecosystems with manifests and lockfiles but repository features, detected by predicates the register already owns. The spellings are GitHub's, not ours, so no repo could reasonably need them to differ |
| The predicate grammar | Expressing it in the register makes the register a program — excluded by name in the build plan |
| `AAA-NNN` / `GOV-NNN` ID patterns, semver strictness, `rationale_adr` existence, the Tier-1 baseline rule | Properties of the register *format*, not of any repository. A repo needing them to differ is asking for a different standard |
| Reading YAML, walking workflow steps, parsing `pyproject.toml` | Implementation of detection, not the rule being detected |

### Not yet applied

The mandated tool names and their per-locus evidence — ruff, eslint, mypy,
pytest, the `charliermarsh.ruff` extension ID, the test-command spellings and
the suppression patterns — are still in the checker. They answer *yes* to the
test and belong in the register; moving them means modelling per-stack tool
roles and their evidence at each locus, which is a larger design than the two
cases above and is tracked as its own exit criterion rather than being quietly
dropped from this list.

## Consequences

**Positive outcomes:**

- Every rule that can change a verdict is either in the register or has a
  recorded reason for not being, so § E's list stops being open-ended.
- SUP-001's ecosystem scope becomes reviewable, and gains a `review_by` date like
  everything else in the register.
- Phase 2's six gate skills inherit a boundary rather than a habit, which is the
  whole reason to settle it before they are written.

**Trade-offs and risks:**

- A `register_contract` bump and a schema addition, on top of ADR 0017's.
  Batching limits it to one bump but not to zero.
- The classification is a judgement, and a rule placed wrongly is harder to move
  after Phase 2 than before it.
- Moving tool names into the register makes the register longer and more
  opinionated. That is the intended effect — an opinion nobody can find is not a
  standard — but it raises the cost of every future review.

## Related ADRs

- [ADR 0017: Report a Partially Implemented Control as Partial](0017-partial-verification-is-reported.md)
  — the other schema addition in the same `register_contract` bump.
- [ADR 0016: Give "Could Not Verify" Its Own Exit Code](0016-exit-codes-for-unverifiable-controls.md)
  — a rule moved into the register can be declared partially implemented rather
  than silently absent.
- [ADR 0009: Lint From One Pinned Definition at Every Locus](0009-single-lint-definition.md)
  — the same argument applied to a tool's configuration rather than to the
  register.

## References

- [OpenSSF Baseline](https://baseline.openssf.org/)
- [Open Policy Agent — policy language](https://www.openpolicyagent.org/docs/policy-language)
