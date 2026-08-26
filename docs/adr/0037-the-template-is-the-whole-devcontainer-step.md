# ADR 0037: The Shipped Template Is the Whole Devcontainer Step

**Status:** Accepted
**Date:** 2026-08-26
**Revision:** 1

## Background

The plan for this standard has said since its first design document that
`project-init` configures an adopter's devcontainer and `gate-build` pins
whatever it chose — *"different questions, and neither skill should be asked the
other's"* ([`03-devcontainer.md`](../03-devcontainer.md) § How this composes with
`project-init`). That division was written when the only source of a
`.devcontainer/` was a private template repository, and `project-init`'s own
precondition — the file must already exist — was the seam it turned on.

Two things have happened since, and neither was recorded as changing it.

**The template shipped.** `plugins/control-register/templates/devcontainer/`
exists, is obtainable by anyone who can install the plugin, and was built and run
in Phase 4. It is not a bare file for something else to configure: it declares
the image by digest, the features, `setup.sh`, `check-auth.sh`,
`fetch-secrets.sh` and a lock file covering every feature. What `project-init`
was to supply, it supplies.

**The published route stopped mentioning it.** `docs/08-adopting.md` § 2.0 —
the step an adopter actually follows — goes copy the template, substitute four
placeholders, run `/gate-build`. `project-init` appears in that guide twice, both
times explaining why the template ships rather than as something to run. So the
route this standard publishes has not included `project-init` since Phase 2, and
Phase 4 completed an adoption without it.

Meanwhile Phase 4 ran it, and measured what it does to a template-derived
container ([`12-phase-4-review.md`](../12-phase-4-review.md) § `project-init` and
`register-adopt` do fight over `devcontainer.json`):

- Step 4 replaces the digest-pinned image with `mcr.microsoft.com/devcontainers/python:3.12`
  — a floating tag, which fails DEV-001's `devcontainer_image_digest_pinned`, at
  a version below the register's floor;
- it adds `ghcr.io/devcontainers/features/node:1` beside the template's `node:2`,
  because its skip-check tests for the wrong one, leaving a lock file covering
  neither.

The ordering makes this unavoidable rather than incidental. `project-init`
requires `devcontainer.json` to exist, so the template is copied first, and Step
4 then overwrites the two things the template exists to pin.

So the documents describe a composition the route does not perform, of a skill
that undoes the control the route's next step deploys. Eight places said so,
two of them shipped to adopters.

## Alternatives Considered

**Keep it optional, with the conflict stated as a warning.** The honest middle:
the template covers the common case, `project-init` remains available for a stack
it does not fit, and the documents say what it will unpin. Rejected because an
optional step that fails a Tier-1 control is a trap rather than an option — the
adopter who takes it is the one whose stack is unusual, which is the adopter
least able to spot a floating tag among their own changes. A standard should not
document a route it knows fails.

**Fix `project-init` upstream first, and change nothing here until it lands.**
This was the position until now, and it is why the criterion stayed open. It
leaves the standard's own documents contradicting its own guide for as long as a
repository nobody here owns takes to accept a change. The measurement is worth
submitting; waiting on it is not worth publishing wrong instructions.

## Decision

**`project-init` is not part of this standard's adoption route.** The shipped
template is the initial `.devcontainer/` and the configured one. No document of
this standard instructs an adopter to run `project-init`, and none describes a
division of labour with it.

**Where the template's image does not fit a stack, the adopter chooses the
image, and `gate-build` pins it.** That is the same sentence as before with a
different subject: `gate-build` pins what it finds and never chooses, which does
not change. What changes is that the thing it finds was chosen by a person, not
by a skill this standard depends on.

**The composition exit criterion is retired, not met.** It asked whether two
skills compose; the answer is that the route runs one of them. Ticking it would
claim a property nobody demonstrated, and leaving it open would gate a phase on
work the route no longer needs. `docs/04-build-plan.md` § Phase 4 records the
retirement in prose, because a criterion that silently disappears is
indistinguishable from one nobody noticed.

## Consequences

**Eight places change, two of them shipped.** `gate-build`'s `SKILL.md` and
`README.md` and the template's own `README.md` reach adopters, so they were
telling adopters to depend on a skill this standard no longer uses.
`README.md`, `docs/02-skill-family.md`, `docs/03-devcontainer.md` and
`docs/04-build-plan.md` are the internal four.

**No control, contract or gate behaviour changes.** `gate-build` does what it
did; DEV-001 says what it said. This is a decision about a route and the
documents that describe it, so no `contractVersion` moves and the register's
contract stays where it is.

**A stack the template does not fit is now a hand step with no skill behind
it.** Stated rather than hidden: that adopter edits `devcontainer.json`'s image
themselves and runs `/gate-build`, which pins it and fails them if they left a
floating tag. It is a smaller gap than it looks — an image is one line, and the
control that matters is enforced either way — but it is a real one, and it is the
cost of this decision rather than an oversight in it.

**The Phase 4 finding stands as a dated record.** [`12-phase-4-review.md`](../12-phase-4-review.md)
keeps its measurement of what `project-init` Step 4 does; that is what a phase
review is for, and it is the evidence this ADR rests on. The measurement is still
worth submitting upstream, and Phase 6 is still where that would happen — as a
contribution to another plugin, not as a dependency of this one.

**`project-init` is not deprecated, criticised, or anyone's problem here.** It
owns interactive devcontainer setup for repositories that are not adopting this
standard, and it does that well. The conflict is specific: it re-chooses an image
that a control requires to be pinned.

## Related ADRs

- [ADR 0034](0034-the-template-bootstraps-uv.md) — what the shipped template
  installs, and why a gate cannot install it
- [ADR 0032](0032-the-checker-is-installed-from-a-tagged-ref.md) — the other half
  of what an adopter obtains without access to a private repository

## References

- [`docs/08-adopting.md`](../08-adopting.md) § 2.0 — the route as published,
  which this ADR makes the documents agree with
- [`docs/12-phase-4-review.md`](../12-phase-4-review.md) § `project-init` and
  `register-adopt` do fight over `devcontainer.json` — the measurement
