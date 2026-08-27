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

## The second slice — a push is a locus

Landed 2026-08-27, at register contract 31. It closes no criterion outright and
that is recorded rather than worked around: half of the criterion it addresses
is unreachable as written, and § What the slice deliberately left open says why.

### What was found

`CLAUDE.md` § Commands asked a person to remember four commands before pushing,
because only one of them was wired. The pre-commit hooks reach ruff, mypy,
gitleaks, markdownlint and three controls of fourteen; `uv run pytest` and a
full `uv run register-check` had no local moment at all. That is a second copy
of the CI definition held in prose — free to drift from
`.github/workflows/register-check.yml` the moment a step is added there, with
nothing comparing them.

The repair the exit criterion rules out by name is a script in `scripts/` that
lists CI's steps, which is the same second copy with a shebang on it. The repair
it prescribes is a register change: `locus:` gains `pre-push`, the controls that
want it declare it, and a gate writes the hook like any other.

**Two things were found on the way that the criterion did not predict.**

The first is a latent hole in the checker. `_precommit_hooks` returned every
hook in `.pre-commit-config.yaml` and no caller asked which stage it ran at —
harmless while `pre-commit` was the only local locus, and not harmless with a
second: a hook staged `[pre-push]` would have satisfied a `pre-commit` locus,
so a control enforced only before a push would have reported itself enforced
before every commit. Stages are now resolved the way pre-commit resolves them —
the hook's own `stages`, else the file's `default_stages`, else every stage.
That last clause matters in the other direction: an absent `stages` genuinely
does run at every installed stage, so reading the absence as `pre-commit` would
have failed a repository that was in fact wired.

The second decided the shape of the hook. **A full `uv run register-check` on a
developer's machine exits `3`, permanently and by design**: SEC-003's two
`kind: remote` blocks answer only inside a GitHub Actions job, so outside one
they are `UNCLASSIFIED` and the run is incomplete. A hook running the full audit
would refuse every push. Both ways out are worse than the problem — a shell
wrapper mapping `3` to `0` is a tolerance nobody reads, and a flag that skipped
`kind: remote` blocks would report SEC-003 as `PASS` on its file block alone,
which is the substitution ADR 0016 exists to refuse. So the locus asks each
control its own question, which is what a locus has always been.

### What landed, and what the evidence is

| Claim | Evidence |
| --- | --- |
| A deleted test refuses the push | Measured, and recorded below this table — the hook is installed here and a failing assertion makes `pre-commit run --hook-stage pre-push` exit non-zero |
| A hook staged for a push does not serve the commit locus | `tests/test_pre_push_locus.py::test_a_hook_staged_for_a_push_does_not_serve_the_commit_locus` |
| A hook naming no stage serves both | `::test_a_hook_that_names_no_stage_serves_both`, with `::test_default_stages_narrows_a_hook_that_names_none` as its other half |
| The loci come from the register, not from the assert | `::test_the_locus_comes_from_the_register_and_not_from_this_module` — one repository, two registers one `locus:` entry apart, opposite verdicts |
| A suppressed hook is not a gate | `::test_a_hook_whose_exit_code_is_absorbed_is_not_a_gate` — the same `suppression:` list the ci locus refuses |
| Both hook types are installed and a missing one is reported | `::test_this_repository_wires_the_locus_it_declares`, over `setup.sh`, the shipped template and `check-auth.sh` |

**The judge, run rather than reasoned about.** A deliberately failing assertion
was added, committed with `--no-verify`, and pushed to a throwaway bare
repository: the hook ran the suite, reported `1 failed, 938 passed`, and git
refused the push with exit 1. Both were then reverted.

Measured the same way before the tests were written: with `|| true` appended to
the test hook's entry, TST-001 fails *"pre-push locus — the hook's exit code is
absorbed: tests"*; with both pre-push hooks removed, all three controls fail
naming the locus and none of the ci blocks moves.

### One control's ci locus was strengthened on the way

Giving SUP-001 and SUP-002 a `gate_wired_at_declared_loci` block reads **every**
locus they declare, not only the new one — and the `ci` half was not satisfied
by the gate's own template, which wrote one step naming SUP-003 alone. Until
now each of those two was verified by its *property*: a lockfile exists, a
dependency-update config covers every ecosystem. That is contract 14's finding
in two more controls, six contracts later, and the fix is contract 14's: the
gate's CI step now names all three controls and carries three stamps.

### What the slice deliberately left open

- **The criterion is not ticked.** `uv run pytest` is wired and the full
  `register-check` is not, for the reason above. Closing the row means either
  giving the remaining locally-verifiable controls the locus — SEC-002 needs a
  gate to write its hook before it can have one — or amending the row to say
  *what CI runs that this machine can answer*. `docs/04-build-plan.md` records
  the choice rather than making it.
- **`uv sync --frozen` stays a remembered command**, and deliberately. At this
  locus it would verify the wrong thing: every hook above it invokes `uv run`,
  which re-locks on disk before `--frozen` is reached, so it would pass on a
  machine whose `uv.lock` has been rewritten and not committed — the exact state
  that fails CI.
- **No control checks that the hook is installed**, and none can: `.git/hooks/`
  is untracked and CI has no hooks. `setup.sh` installs both types and
  `check-auth.sh` reports either missing — reported, never repaired, the same
  boundary the `pre-commit` locus already had.
- **The three meta-controls declare no locus** and so can never run at one. That
  is the schema's rule rather than an omission, and it is half of why *what CI
  runs* is not a reachable target locally.
- **Every gate here is still `UNRECORDED`.** This slice bumped `gate-quality`'s
  and `gate-supply-chain`'s `contractVersion`, which is the sidecar working as
  designed — what they write changed — and neither gate was re-run, because
  re-running six gates in this repository is a decision rather than a chore.

## The third slice — the last control that could take the locus

Landed 2026-08-27, at register contract 32. It closes the criterion the second
slice deliberately left open, and the way it closes it is worth stating plainly,
because the row as written names a target that does not exist.

### What was found

SEC-002 was the one control whose verification a developer's machine can finish
and which had no local locus at all. It also had **no `deployed_by`** — it had
sat in `register-adopt`'s *checked, not deployed* row since Phase 0, on the
reasoning that a control satisfied by an absence has no artefact to write.

That reasoning was right about the property and wrong about the locus. An
absence still needs something that notices when it stops being true, and a locus
is something a gate installs — so giving SEC-002 a locus gives `gate-secrets`
its first SEC-002 artefact, and `deployed_by` follows from that rather than from
a change of mind about what the control asserts. The plan row moved with it, and
the lesson recorded in `register-adopt`'s SKILL.md is the general one: which row
a control belongs in is read from the register at plan time and never
remembered, because a control can move between rows.

**SEC-003 stays in that row**, and the boundary was measured rather than
assumed: `register-check run --control SEC-003` exits `3` on this machine,
because its two remote blocks answer only inside a GitHub Actions job. A hook
running it would refuse every push. The test for whether a control can take this
locus is whether the machine at that locus can *finish* verifying it — which is
ADR 0039 § Decision point 4 applied to one more control.

### What closed, and what the evidence is

| Criterion | Evidence |
| --- | --- |
| A developer can run what CI runs, before pushing, in one wired step | `tests/test_pre_push_locus.py` for the mechanism; `tests/test_gate_secrets_deploy.py::test_the_pre_push_hook_is_staged_and_sec_003_is_not_in_it` for the boundary; the second slice's measured push refusal for the judge |

Measured against this repository: with the hook's entry pointed at SEC-003
instead, SEC-002 fails *"pre-push locus — nothing runs 'uv run register-check'
for SEC-002"* while its property block still passes — the two claims failing
independently, which is the whole point of the locus assert.

### What "what CI runs" had to be narrowed to

The row's literal reading is unreachable and this is the honest record of that.
Three things remain CI's alone:

- **SEC-001's and SEC-003's `kind: remote` blocks** answer only where the
  credential is.
- **CI-001** is `locus: [remote]` outright — there is no file to run.
- **The three meta-controls** declare no locus at all, because the schema
  forbids one on a control that checks the register rather than the repository.

So the criterion is closed as *every control whose verification this machine can
finish now has a local locus*, and a green push is a promise about those. It is
not a promise that the conformance job will pass. Anyone reading it as one has
made the substitution this register spends most of its asserts refusing.

### What the slice deliberately left open

- **The pre-commit hooks do not run again at push.** `default_stages:
  [pre-commit]` means a hook without `stages:` runs at commit time only, so the
  union of the two moments is what covers CI rather than the push alone. A
  developer who commits with `--no-verify` and then pushes gets the pre-push
  hooks and nothing else. Making the push re-run everything was considered and
  not done: it would run the markdown, lint and type gates a second time on
  files that had not changed since they passed, and `gitleaks protect --staged`
  would scan an empty stage — a check that cannot fail is worse than no check.
- **Nothing verifies that the second git hook is installed**, here as at the
  first locus. `.git/hooks/` is untracked, CI has no hooks, and `check-auth.sh`
  reports rather than repairs.
