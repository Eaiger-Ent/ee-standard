# ADR 0052: A Profile Is a Stack and a Strictness, and Stack-Neutral Rules Gate on Evidence

**Status:** Accepted
**Date:** 2026-09-06
**Revision:** 1

## Background

**The problem.** `docs/craft/plan.md` lists as decision 2: what a profile is, and
whether "archetype" — backend service, library, application — is a real axis or
whether stack alone carries it. It was deliberately deferred until S2 could show
whether rules actually vary that way, because an axis invented before the
evidence is an axis nobody can remove later.

**S2's evidence says archetype is real but narrow.**
`docs/craft/assess.rules.md` registers 181 properties: 71 Python, 68 React and 42
stack-neutral. The properties that vary by what an application *is* are almost
entirely the `any.` ones — a library has no endpoints to authorise, no OpenAPI
document to lint and no CORS configuration to check. The `python.` and `react.`
rows barely vary at all: a mutable default argument is a defect in a library and
in a service, and `useEffect` deriving state is wrong in every React codebase
that has one.

**Nine of the 42 stack-neutral rows cannot be checked at all without an
artefact.** Every `spectral` row needs an OpenAPI document. `assess.rules.md`
records this as a condition on the bucket rather than a property of the rule:
where a repository has none, the whole group is bucket 3 by default. That is the
observation the axis question turns on — the variation is not really about what
kind of application it is, it is about whether the evidence exists.

**The target is new codebases.** Confirmed 2026-09-06. That removes a third
candidate axis before it is proposed: codebase age.
`docs/craft/assess.contested.md` row 9 records `react.no-class-components` as
evidence for an age axis — on for greenfield, off for an existing codebase — and
rows 10 and 11 record two rules in `eslint-plugin-react`'s `recommended` that are
only defensible for a codebase predating React 17. With new codebases as the
target, none of the three needs an axis: the answer is current practice, and a
rule is not held back because an old repository would fail it.

## Alternatives Considered

### Option 1: Three axes — stack, archetype, strictness

Archetype declared explicitly at install and gating the `any.` rows, which is
where the variation actually is.

**Rejected, because a declared archetype is an answer nobody re-checks.** It is
given once, at install, by someone guessing which of three words fits; and when
it is wrong it does not fail — it silently disables real rules, which is the
failure shape [ADR 0019](0019-exemptions-cannot-hide-tracked-files.md) describes
about exemptions and [ADR 0045](0045-a-gate-records-where-it-installed-a-tool.md)
about allow-lists. Something invisible that suppresses checks is worse than
something noisy that runs them. It is also a third axis to version, and profile
versioning is already the hardest part of this model.

### Option 2: Two axes, with the stack-neutral rules as an all-or-nothing bundle

Stack and strictness; `any.` taken whole or not at all.

**Rejected.** A library that wants commit conventions would also get nine API
rows it cannot satisfy, on a repository with no OpenAPI document for them to read.
That is findings-on-install with no possible fix, which is precisely the noise S3
exists to measure and prevent. The simplicity is real and it is bought with the
one outcome the workstream has said it will not ship.

### Option 3: Two axes, with the stack-neutral rules gating on evidence

Stack and strictness. Each `any.` group switches on when the artefact it reads is
present in the repository.

**Chosen.** It gates on the same fact the rule needs to run at all, so the gate
and the rule cannot disagree. Nothing is declared, so nothing can be declared
wrongly, and there is no third axis to version.

## Decision

**A profile is a stack and a strictness.** Two axes:

- **Stack** — `python` or `react`, matching the identity scopes in
  `docs/craft/plan.md`'s naming standard.
- **Strictness** — a named level within a stack, the axis S3's measurements
  populate. What the levels are is S3's and S4's to settle; that there are
  exactly two axes is settled here.

**Archetype is not an axis.** The 42 `any.` properties are grouped by the
artefact they read, and each group switches on when that artefact is present:
an OpenAPI document turns the API group on, its absence leaves the group off. A
repository declares nothing.

**There is no codebase-age axis.** Craft targets new codebases and encodes
current practice. `react.no-class-components` is on; `react/prop-types` and
`react/react-in-jsx-scope` are out, which is `docs/craft/assess.contested.md`
rows 10 and 11 resolved in favour of option B on those rows alone — the choice of
which React plugin supplies the base is S3's and is not decided here.

**A profile is versioned and pinned by the consumer**, in the shape
`.claude/skill-config.yaml` already uses for `lint-md`. When a profile changes, an
installed repository keeps the version it pinned until someone re-runs the
installer; the installer reports what moved between the pinned version and the
current one. A profile does not change under a repository that is not looking.

## Consequences

**Two repositories on the same profile can run different rules.** That is the
cost of gating on evidence, and it is a real one: "we are both on
`python/standard`" stops being a complete description of what runs. The
mitigation is that **the installer must report which `any.` groups it switched on
and which artefact switched them**, and record it where the next reader will find
it. An evidence gate nobody can see is the invisible suppression this ADR
rejected option 1 for.

**Adding an artefact to a repository turns rules on.** Writing a first OpenAPI
document enables nine rules that were previously inert, on a codebase that has
never been checked against them. That is correct — the rules were never
satisfied, only unchecked — and it will feel like a regression at the worst
moment. S3 owes a measurement of that specific transition, not only of the
install case.

**Strictness carries the whole burden of "how much".** With archetype gone and
age gone, every question of the form *should this repository get more or fewer
rules* resolves to strictness. If S3 finds that levels alone cannot express what
teams need, this ADR is what has to be amended, and the evidence for amending it
will be in `review.noise.md`.

**The three properties the age question raised are settled and stay settled.** A
future adopter with an old codebase is not a reason to reopen it. Craft's answer
to an old codebase is that it may not be the audience, which is a smaller and
more honest claim than a profile that pretends to serve both.

## Related ADRs

- [ADR 0051](0051-a-craft-rule-becomes-a-control-by-being-installed.md) — when a
  craft property becomes a control. A profile is what installs the enforcement
  that makes the crossing true.
- [ADR 0019](0019-exemptions-cannot-hide-tracked-files.md) — an exemption that
  hides a tracked file is invisible suppression, which is the argument that
  rejected the declared archetype.
- [ADR 0042](0042-a-deploying-skill-reads-local-configuration.md) — the
  `.claude/skill-config.yaml` shape a profile pin follows.

## References

- `docs/craft/plan.md` § Decisions this workstream owes an ADR, decision 2 — the
  question this record answers, and the deferral it was answered after.
- `docs/craft/assess.rules.md` § What this stage did not settle — the archetype
  evidence, stated there as evidence rather than as a conclusion.
- `docs/craft/assess.contested.md` rows 9, 10 and 11 — the codebase-age
  candidate, and what removing it resolves.
