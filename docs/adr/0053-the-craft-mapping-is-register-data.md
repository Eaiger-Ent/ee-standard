# ADR 0053: The Craft Mapping Is Register Data, in a Register of Its Own

**Status:** Accepted
**Date:** 2026-09-06
**Revision:** 1

## Background

**The problem.** `docs/craft/plan.md` lists as decision 3: where the enforceable
mapping lives, given [ADR 0018](0018-register-checker-boundary.md) — because the
register/checker boundary applies to anything this workstream produces that a
machine reads. Craft now produces exactly that.
`docs/craft/assess.rules.md` holds 181 properties, and around a hundred of them
carry a binding from a property to a named tool and one or more exact rule IDs.
Something has to read those to generate a `[tool.ruff.lint] select` list and a
flat ESLint config. Where the bindings are written down decides whether the thing
that reads them can be varied by a repository or only by us.

**ADR 0018's test answers this in one line, and the answer is obvious.** *Could a
reasonable Equal Experts repository need this to differ without changing the
checker?* A repository selecting a different set of ruff rules is not a defect,
not an exception, and not a change to any tool — it is the ordinary case. It is
the same shape as the failure 0018 was written about, where a checker-side map of
lockfile spellings silently exempted Go, Rust and Java from SUP-001. A
checker-side map of property-to-rule bindings would exempt, just as silently,
every stack nobody thought of.

**So the interesting question is not *data or code*. It is *which register*.**
`controls.yaml` is the control register, and `docs/craft/plan.md`'s naming
standard says a craft rule is not a control. Putting a hundred rule bindings in
`controls.yaml` would make every adopter's conformance run parse rules that
decide no verdict, and would put entries in a file whose every other row is
something that can fail a build.

## Alternatives Considered

### Option 1: The mapping lives in Craft's Python

The installer holds the property-to-rule bindings in code, and generating a
config is a function.

**Rejected by ADR 0018 directly**, without needing a Craft-specific argument. The
bindings answer *yes* to 0018's test, so they belong in data; and an unreasoned
rule in the checker is, in that ADR's words, the failure rather than an exception
to it. There is no reason to record here, because there is no reason.

### Option 2: The mapping lives in `controls.yaml`

One register for everything the organisation asserts about its repositories.

**Rejected, because it makes a craft rule a control by filing.** The boundary
[ADR 0051](0051-a-craft-rule-becomes-a-control-by-being-installed.md) draws is
that a property crosses when something enforces it, not when someone writes it
down; storing every property in the control register would cross the boundary for
a hundred of them by clerical accident. It also loads every adopter's conformance
run with data that decides nothing, and `controls.yaml`'s schema — `rung`,
`verify`, `variance`, `applies_to` — describes verdicts, which is not what a
property binding is.

### Option 3: A Craft register of its own, under the same discipline

A separate data file that Craft's tooling reads, holding properties, their tool
bindings, and the profiles assembled from them.

**Chosen.** It keeps ADR 0018's answer — data, not code — without making
`controls.yaml` mean two things. The discipline is inherited; the file is not.

## Decision

**The enforceable mapping is data, and it lives in a Craft register of its own —
not in `controls.yaml`, and not in Craft's Python.**

**What the Craft register holds:** the properties, their tool and rule-ID
bindings, the profiles of [ADR
0052](0052-a-profile-is-a-stack-and-a-strictness.md), and the evidence gates that
switch the stack-neutral groups on. Anything a reasonable Equal Experts
repository could need to differ.

**What Craft's Python may hold:** the same class of thing ADR 0018 leaves to the
checker — properties of the *format*, not of any repository. The identity
grammar, the profile schema, the assembly of a config from bindings. **Each must
carry its reason in this ADR when it is written**, on the same terms 0018 sets:
an unreasoned rule in the code is the failure, not an exception to it.

**The test is ADR 0018's, unchanged.** Before a rule enters Craft's Python, ask
whether a reasonable Equal Experts repository could need it to differ. Craft does
not get a second test, because a second test is a second copy.

**`docs/craft/assess.rules.md` is not that register.** It is a prose document
recording an assessment, and it will go stale the moment the register exists. The
implementing work must decide whether the register is generated from it, replaces
it, or is written fresh with the document kept as the record of how the
classification was reached — but the two must not both be maintained as sources.
That is the duplication this repository exists to prevent, and it would be a
particularly poor way to acquire it.

## Consequences

**Craft acquires a second register, and this repository now has two.** Every
place that says "the register" has to say which one, and
`docs/14-file-map.md` owes the distinction. The cost is real and it is smaller
than the alternatives: one register holding two kinds of thing is how a schema
stops meaning anything.

**A Craft register needs its own schema and its own validation.** `register-check`
audits `controls.yaml` and has no business reading this one — the checker is for
conformance, and a craft profile decides no verdict until ADR 0051's route is
taken. What validates the Craft register is the implementing work's to build.

**A property that crosses to a control exists in both registers.** ADR 0051 says
what happens: once it is in `controls.yaml` it is governed by the register's
rules, and `docs/craft/` may keep the row for provenance but not a second copy of
the rule. This ADR is where that gets awkward in practice, because a binding is
exactly the thing that would be tempting to keep in both. It must not be.

**Nothing is built yet.** This decides where the mapping lives, not what its
schema is or when it is written. S4 designs it; S5 builds it. An ADR that
specified the schema here would be specifying it before S3 has measured which
bindings survive.

## Related ADRs

- [ADR 0018](0018-register-checker-boundary.md) — the boundary this applies, its
  test quoted rather than restated, and the measured failure that produced it.
- [ADR 0051](0051-a-craft-rule-becomes-a-control-by-being-installed.md) — the
  crossing to `controls.yaml`, which is why the two registers stay separate.
- [ADR 0052](0052-a-profile-is-a-stack-and-a-strictness.md) — the profile model
  whose axes this register has to express.

## References

- `docs/craft/plan.md` § Decisions this workstream owes an ADR, decision 3 — the
  question this record answers.
- `docs/craft/assess.rules.md` — the 181 properties and their bindings, as prose,
  which is what the register would hold as data.
