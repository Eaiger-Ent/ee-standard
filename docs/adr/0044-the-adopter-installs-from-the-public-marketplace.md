# ADR 0044: The Adopter Installs From the Public Marketplace

**Status:** Accepted
**Date:** 2026-08-29
**Revision:** 1

## Background

The machinery this standard reaches a repository through lives in two
marketplaces, and one of them is private.

`EqualExperts/ee-skills` is `private: true`, measured 2026-08-29. `lint-md`
lives there, and `lint-md` owns the whole DOC-001 lifecycle
([`02-skill-family.md`](../02-skill-family.md)). Phase 4 met this from the
adopter's side and recorded it as finding 12: *"DOC-001 is dispatch elsewhere in
every plan this repository produces, and elsewhere is somewhere you cannot
go."* It resolved the immediate problem by copying the skill into the consumer
repository's `.claude/skills/`, and recorded that as what happened rather than
as a recommendation — a copy of someone else's skill, in the adopter's
repository, going stale silently.

`Eaiger-Ent/ee-standard` is public. It is this repository, it is a plugin
marketplace, and it is what [`08-adopting.md`](../08-adopting.md) § 0.0 tells an
adopter to install `control-register` from today.

Phase 6 promotes `control-register` to `ee-skills`. **That is the decision this
ADR exists to take deliberately, because taken by accident it moves the plugin
behind the same door as `lint-md`.** Promotion is what the phase is for and it
is worth doing — it is how every Equal Experts repository gets the standard
without being told a URL. But *"installable from the marketplace"*, read as
*installable from `ee-skills` instead*, would answer Phase 6's criterion by
making the published route unreachable for the class of adopter that criterion
was added for. The two open criteria are one problem: the access-shaped single
point of failure the devcontainer template was moved into this plugin to escape,
about to be re-acquired by the plugin itself.

Waiting is not neutral either. Asking that `ee-skills` be published is a request
in a repository nobody here owns, with no date attached, and a route that waits
on someone else's access policy is a route that is not published.

## Decision

**The adopter's route is the public marketplace, and promotion adds a route
rather than replacing one.**

Two parts.

**1. `Eaiger-Ent/ee-standard` stays the address in the published guide.**
`08-adopting.md` § 0.0 continues to say `claude plugin marketplace add
Eaiger-Ent/ee-standard`, before promotion and after it. Promotion to `ee-skills`
serves installs inside Equal Experts, where that marketplace is reachable and is
where people already look; it does not become the instruction given to someone
outside. The two copies are the same plugin from the same tree, so this is one
artefact published twice, not a fork — and if they ever stop being the same
tree, that is a defect to fix rather than a state to document.

The coupling is held by a test rather than by this sentence:
`tests/test_adopter_guide.py` derives the marketplace the guide names from
`tools.register-check.install.repository`, which is the address the register
already gives for the checker. An adopter obtains the register, the checker and
the plugin from one public repository, and rewriting the guide to name a second
address fails the build.

**2. A control whose deploying skill an adopter cannot install is satisfied by
hand, and verified by the register.**

DOC-001 is the instance and today the only one. `08-adopting.md` § 3 already
carries the six-step by-hand route — `package-lock.json` as the pin,
`.markdownlint.yaml`, `.markdownlint-cli2.yaml` with `ignores: []`, a root
`.gitignore` carrying `node_modules/`, a pre-commit hook whose `entry` is
`node_modules/.bin/markdownlint-cli2`, and a CI job whose id is `lint-md` —
done and verified in Phase 4's consumer repository. **What changes is its
standing.** It was written as a stopgap, under *"Until that is resolved"*; it is
now the supported route for an adopter who cannot reach `ee-skills`, and the
guide says so.

Three things make that honest rather than a shrug:

- **The register verifies it.** `uv run register-check run --control DOC-001`
  runs the same two blocks over a hand-wired deployment as over a deployed one,
  because a control is verified by what the repository contains and not by what
  wrote it. A hand-wired gate that is wrong fails; this is a deployment route,
  not an exemption.
- **DOC-001 asks for no provenance stamp.** Its verify blocks are the tool and
  `markdown_gate_wired_at_all_loci`; there is no `provenance_stamp_present`, so
  the control passes completely rather than in part. `deployed_by: lint-md` is
  read where a stamp is read, and here nothing reads one. **No stamp naming
  `lint-md` may be written for a deployment `lint-md` did not make** — that is
  the rule ADR 0038 states about filling a field in by hand, applied to the
  whole record.
- **Nothing is copied.** No skill from another plugin is vendored into an
  adopter's repository, and none is vendored into this one.

## Alternatives considered

**Copy `lint-md` into the adopter's repository.** What Phase 4 did, and it
works — for as long as nobody looks. It puts a copy of another plugin's skill
under `.claude/skills/`, where it goes stale with no line to read on the day it
stops matching upstream, and where `register-check deployments` cannot reconcile
it: ADR 0043 reads the plugin inventory, and a copied directory is not an
installed plugin. It is the duplication this standard exists to prevent, in the
repository the standard is being adopted by.

**Write a DOC-001 gate here.** `control-register` gains a `gate-docs`, and the
adopter deploys markdown linting the way they deploy everything else. Rejected
because it forks one lifecycle into two implementations that can drift, which is
the same failure one level up: two gates writing `.markdownlint.yaml` from two
sources, one of which this repository would then have to keep in step with a
skill it does not own. *"Replacing `lint-md`"* is named in
[`04-build-plan.md`](../04-build-plan.md) § What is deliberately not in scope,
and this would be that under another name.

**Make promotion conditional on `ee-skills` being published.** The cleanest
outcome and not ours to schedule. It gates a phase of this repository on a
change to a repository nobody here owns — the ordering
[ADR 0022](0022-a-platform-token-ci-carries.md) rules out for its own
requirements, and the reason [ADR 0037](0037-the-template-is-the-whole-devcontainer-step.md)
retired a criterion rather than leaving it open. Worth asking for; not worth
waiting on. It is raised as a submission in
[`05-promotion.md`](../05-promotion.md) § Submission order and nothing here
depends on the answer.

**Drop DOC-001 for adopters who cannot reach the gate.** A control weakened by
someone else's access policy, which is the substitution
[ADR 0016](0016-exit-codes-for-unverifiable-controls.md) refuses in the exit
code and [ADR 0014](0014-satisfying-remote-locus-controls.md) refuses in the
tier. The register would say markdown is linted and the repository would not
be.

## Consequences

`control-register` is published twice, and the second publication is the one
most people will use while the first is the one the guide names. That asymmetry
is deliberate and it has a cost: an EE-internal installer follows an instruction
this repository does not print, so a defect in the `ee-skills` copy is one
nobody here is told about by the guide. Phase 6's re-adoption criterion is
judged against the marketplace copy, which is what makes the two provably the
same at least once.

**An outside adopter does more by hand than an inside one**, and exactly one
control's worth: six steps, verified by the checker afterwards. That is a real
difference in adoption cost and it is written into `08-adopting.md` rather than
discovered, which is the standing requirement Phase 4 added.

**This ADR does not make `lint-md` reachable.** It decides what this repository
publishes and what it asks of an adopter who cannot reach what it does not
publish. If `ee-skills` is opened later, part 2 becomes unnecessary for DOC-001
and part 1 is unaffected — the public route was never contingent on the private
one being closed.

No control's `rung`, `verify`, `variance` or `applies_to` changes, and the
register gains no field, so **the contract does not move.** That is the shape of
the answer Phase 6's criterion predicted: a publication decision rather than a
code change.
