# Phase 5 — staleness and the sweep

[`04-build-plan.md`](04-build-plan.md) is the list of outstanding work; this is
where the evidence behind every criterion it ticks lives, and where what each
slice deliberately left open is written down.

## The first slice — the stamp records the deployment contract

Landed 2026-08-26. It closes three criteria and it did not close them the way
the plan expected, because the mechanism the plan describes was missing a field.

### What was found

`02-skill-family.md` § Staleness has said since Phase 2 that *"redeployment is
recommended when the installed contract version is ahead of the one stamped in
the repo"*, and `00-concepts.md` § The provenance stamp tabulated *"deployed and
stale"* as *"stamp is behind the installed skill's deployment contract"*. **The
stamp did not carry a deployment contract.** It carried the control, the skill
and its version, and the register's version and contract — five fields, none of
them the number the comparison names.

Nothing caught it because nothing read `deploys.json`. The sidecar was held to
the register in one direction by `tests/test_plugin.py`, and the stamps were
read back for soundness by `provenance_stamp_present`; both were correct and
neither joined the other. That is § H's shape a fifth time: two halves of a
chain, each verified, with the join verified by nobody.

The obvious substitute does not work. Every gate stamp in this repository reads
`@0.1.0` because a skill has no version of its own — the eight share
`plugin.json`'s — so a rule keyed to a skill version would move six gates
whenever one of them shipped, which is the plugin-wide contract the per-gate
sidecar exists to avoid, one level down.

[ADR 0038](adr/0038-the-stamp-records-the-deployment-contract.md) adds the field
and records the two alternatives rejected: a `contractSince` history in the
sidecar (unverifiable, and keyed to the same shared version), and a per-repo
ledger beside the stamps (a second copy that can disagree with them).

### What closed, and what the evidence is

| Criterion | Evidence |
| --- | --- |
| Bumping a gate's version *without* changing its output produces **no** redeployment recommendation | `tests/test_deployments.py::test_a_version_bump_alone_recommends_nothing` — the stamp names an older skill version and the installed contract; the state is `CURRENT` and `report.owed` is empty |
| Bumping its contract version *does* | `::test_a_contract_bump_recommends_a_redeployment`, and `::test_the_two_criteria_differ_only_in_the_contract`, which runs the same repository against two sidecars one integer apart |
| A repo that has never deployed is distinguishable from one deployed and current, and from one deployed and stale | `::test_no_stamp_is_never_deployed`, `::test_stamp_at_the_installed_contract_is_current`, `::test_a_contract_bump_recommends_a_redeployment` — three states from three fixtures differing only in the field that decides them |

The three are tested rather than demonstrated against this repository, and that
is the honest way round: on the day the ADR landed **every gate here reports the
same state**, `UNRECORDED`, because every stamp in the tree predates the field.
A report whose every row agrees is no evidence that the rows can differ.

### Two states the plan did not name

`UNRECORDED` is the first. A stamp written before ADR 0038 carries no
`gate-contract`, and neither answer is available: calling it current claims the
deployment is not behind, which nobody knows, and calling it stale claims it is.
It is reported as its own state and counted as owed, because a deployment that
cannot be dated cannot be shown to be current. It resolves by deployment.
Filling the number in by hand is the act Phase 5's own criteria rule out.

`NOT APPLICABLE` is the second, and it arrived from the noise argument coming
the other way. The first run of the report called `gate-iac` **never deployed**
in a repository with no Terraform — true, and an act nobody owes. A predicate
skip is not a gap ([`00-concepts.md`](00-concepts.md) § Predicates), so a gate
none of whose controls apply is reported as owed nothing. *Any* control applying
is enough: `gate-quality` carries three and a repository satisfying one of them
wants the gate.

### What the slice deliberately left open

- **The sweep does not exist.** `register-check deployments` reports one
  repository, on demand. Running unattended across many, and producing a report
  nobody has to ask for, is a later slice — and it is what the phase's first
  criterion is waiting on, since half of it is *how a repository opts into the
  sweep*.
- **The Tier-1 ratchet is not built.** `02-skill-family.md` § Loudness says a
  conformance run fails on an owed deployment belonging to a Tier-1 control. It
  does not: the report is its own command and exits `0` over any number of stale
  gates. Ordering by tier and rung *is* built, and is held to the register by
  `::test_loudness_comes_from_the_register_and_not_from_this_module`, which
  demotes a control in the register and watches the report's order invert.
- **Every gate in this repository is now `UNRECORDED`**, and will stay so until
  each is re-run. That is the mechanism reporting itself correctly rather than a
  defect, and re-running six gates here is a decision — they write into this
  repository — rather than a chore to slip into this slice.
- **`skill-update` is untouched.** Widening its success criteria is a
  `skill-submit-amend` against another plugin, and its own criterion is still
  open.

### One thing repaired on the way

Seven test modules each carried a hand-written copy of the stamp regex, and all
seven failed the moment the format gained a field — which is the copies working
as designed, and also the reason the change was seven edits rather than one.
They now call `stamps_in` from `provenance.py`, the parser its own docstring
says is defined once for all four readers. The eighth copy, in
`tests/test_provenance_stamps.py`, already did.
