# ADR 0051: A Craft Rule Becomes a Control by Being Installed as One

**Status:** Accepted
**Date:** 2026-09-06
**Revision:** 1

## Background

**The problem.** `docs/craft/plan.md`'s naming standard says *a craft rule is not
a control*, and lists as decision 1 the question it leaves open: whether one may
ever become one, and what it must have first. Until that is answered the boundary
is a slogan rather than a rule, and the first property that wants to cross will
cross by whoever is holding the keyboard.

**Four properties already are controls, and S2 found them by accident.**
`docs/craft/assess.rules.md` registers `any.no-secrets-in-vcs` (SEC-001 and
SEC-002), `any.no-direct-push-to-default` and `any.ci-green-before-merge` (both
CI-001). They are excluded from the bucket shares because counting them would be
Craft claiming credit for gates the register already runs. That exclusion is the
right arithmetic and it settles nothing about direction: it describes properties
that were controls before Craft named them, not properties that became controls.

**One is a genuine gap, and it is the case that forces the decision.**
`any.dependency-vulnerability-scanning` asserts that known CVEs in dependencies
are surfaced. SUP-002 governs *update proposals per ecosystem*, and a Dependabot
configuration that proposes updates surfaces CVEs as a side effect of doing
something else. Nothing in the register asserts the property. So the register has
a hole exactly where a craft property sits, and the two available answers —
Craft leaves it open forever, or Craft closes it — are opposite postures on the
boundary this ADR exists to draw.

**A skill writing the register is not new here.** [ADR
0045](0045-a-gate-records-where-it-installed-a-tool.md) decided that a deploying
gate writes `tools.<tool>.pinned_at` for a tool it has just installed at a path
not already listed, because the alternative was a comment in a generated file
asking the adopter to do it and the adopter did not. The mechanism this ADR needs
already exists; what is missing is permission to use it for a control entry
rather than a pin site.

## Alternatives Considered

### Option 1: A craft rule never becomes a control

The naming standard read literally and permanently. Craft produces profiles and
prose; the register produces controls; nothing crosses.

**Rejected.** It leaves `any.dependency-vulnerability-scanning` asserted by
nothing, in a repository whose whole argument is that an unasserted rule is a
rule nobody has. It also makes the boundary depend on which workstream noticed a
property first, which is an accident of history rather than a principle: SEC-001
exists because Phase 0 needed it, not because secrets-in-version-control is a
different *kind* of property from CVE surfacing.

### Option 2: Craft closes the gap by widening SUP-002

Extend the existing control's assertion from *updates are proposed* to *known
vulnerabilities are surfaced*.

**Rejected, because it changes an existing control's meaning for every adopter.**
SUP-002 is deployed, stamped and pinned in repositories this one does not
control. Widening what it asserts is a change to `verify`, which bumps
`register_contract` and marks every deployment stale — for a property SUP-002 was
never written to hold. It also conflates two things a reader needs separated: a
repository can propose updates diligently and surface no CVE report at all.

### Option 3: Craft's installer mints a new control when it installs enforcement

The crossing happens at deployment. When Craft's installer wires a tool at a
locus such that its exit code blocks a merge, it writes the corresponding entry
into the control register, the same way `gate-secrets` writes a workflow and ADR
0045's gate writes a pin site.

**Chosen.** It ties the crossing to the only event that makes it true. A property
becomes a control when something enforces it, and the thing that knows
enforcement now exists is the thing that just installed it.

## Decision

**A craft property becomes a control by being installed as one, and the installer
that deploys the enforcement is what writes the register entry.** Nothing crosses
by being written about, argued for, or listed in `docs/craft/`.

**Three preconditions, all of which must hold before the entry is written.**

1. **It has a locus, a pinned tool and a verdict** — `docs/00-concepts.md`'s
   definition of a control, unchanged. A property with no tool cannot be one, and
   this is where *enforcement is never Claude* does its work: a rule whose only
   instrument is prose an assistant loads is not eligible, ever.
2. **It is bucket 1 or bucket 2.** A bucket-3 property is judgment-only by its
   own classification. Bucket 4 is not about code at all. Neither can acquire a
   verdict by being wanted badly enough.
3. **S3 has measured it.** A control that floods on install is worse than no
   control, because it teaches a team to ignore a red build. The measurement is
   `review.noise.md`'s, and a property that has not been through it is not ready
   to block a merge in somebody else's repository.

**`any.dependency-vulnerability-scanning` is Craft's to close**, by this route,
as a new control rather than by widening SUP-002.

**The four properties that are already controls do not cross anything.** They
were controls before Craft named them. Their rows in `assess.rules.md` carry the
control ID so the overlap is visible, and they stay excluded from the bucket
shares.

## Consequences

**Minting a control is a register change, with everything that follows.**
`CLAUDE.md` § Rules for editing `controls.yaml` requires a `register_contract`
bump when a control's `rung`, `verify`, `variance` or `applies_to` changes. A
control that did not exist before is a larger change than any of those, so the
conservative reading is that it bumps too, and every deployed artefact is marked
stale. **The implementing work must confirm this against the contract's own
definition rather than inherit this paragraph's assumption** — an unverified
reading in an ADR is the second copy this repository exists to prevent.

**Craft's installer gains write access to `controls.yaml`.** That is a real
widening of what a skill may touch, and it is why this is an ADR. ADR 0045 opened
the door for `tools.<tool>.pinned_at`; this opens it for a control entry, which
is a larger object. The mitigation is the third precondition: nothing is written
that S3 has not measured.

**The boundary is now testable rather than rhetorical.** "Is this a control?"
becomes "does something block a merge on it, and did S3 measure the cost?" —
two questions with answers, replacing one with a slogan.

**A craft rule that crosses stops being Craft's.** Once it is in
`controls.yaml` it is governed by the register's rules — variance direction,
review dates, GOV-001's reachability. `docs/craft/` may keep the row for
provenance, and it may not keep a second copy of the rule.

## Related ADRs

- [ADR 0045](0045-a-gate-records-where-it-installed-a-tool.md) — the precedent: a
  deploying skill writes the register for what it has just installed, because the
  manual alternative was not done.
- [ADR 0018](0018-register-checker-boundary.md) — the register/checker boundary,
  which governs where the rule a control reads is written down. This ADR governs
  whether the control exists at all; 0018 governs where its data lives.
- [ADR 0031](0031-the-plugin-is-named-for-the-register.md) § Option 2 — *a skill
  may install or explain a gate but cannot be one*, quoted there from
  `CLAUDE.md`. That is the constraint precondition 1 restates in Craft's
  vocabulary, and the reason a judgment-only property can never cross.
- [ADR 0020](0020-a-locus-reaches-the-pinned-artefact.md) — what a locus has to
  reach for enforcement to be real, which precondition 1 depends on.

## References

- `docs/craft/plan.md` § Decisions this workstream owes an ADR, decision 1 — the
  question this record answers.
- `docs/craft/assess.rules.md` § Findings, finding 7 — the four properties that
  are already controls and the one that is not quite.
- `docs/00-concepts.md` — a locus, a pinned tool and a verdict.
