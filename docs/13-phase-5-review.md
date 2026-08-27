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

## The fourth slice — a declined classification is a verdict

Landed 2026-08-27, at register contract 33. It closes the two criteria Phase 4
handed over on 2026-08-24, and the second of them is the reason the slice needed
a decision rather than an afternoon.

### What was found

The standard has promised a **direction** since Phase 0 and never computed one.
`00-concepts.md` § Variance says a delta usually has a knowable one;
`01-register-schema.md` says the checker *"classifies the delta's direction and
fails on any weakening"* and names three cases where it declines instead.

What existed was a set of asserts that **catch** particular weakenings — an
exemption hiding a tracked file, a markdown ceiling above the register's, a
coverage allow-list leaving a tracked module out. Each answers *is this
repository conformant now*. None answers *which way did this change move*, and
nothing in `src/` read a delta at all.

The hard half is the second criterion. **A classifier that answers *narrowing*
when it does not know is worse than no classifier**: it launders a guess into a
verdict, and the reader cannot tell the two apart. So the design had to make
declining something the mechanism produces rather than something it falls
through to, and [ADR 0040](adr/0040-a-declined-classification-is-a-verdict.md)
records it: three shapes are classifiable — membership, a scalar whose key the
register gives a polarity, and nothing else — and the schema's three cases each
fall out of one of them rather than being handled specially.

### What closed, and what the evidence is

| Criterion | Evidence |
| --- | --- |
| A weakening is **classified by direction**, not merely caught | `tests/test_variance.py::test_a_rule_removed_is_a_loosening` and `::test_a_scalar_moves_the_way_the_register_says`, the second parameterised over both polarities and both value kinds — a sign error would pass one half |
| The three `UNCLASSIFIED` cases report as `UNCLASSIFIED` | `::test_case_one_a_member_replaced_by_a_differently_named_one`, `::test_case_two_a_threshold_whose_polarity_the_register_does_not_give`, `::test_case_three_a_config_that_is_executable_code` — one test per case, each asserting the *reason* and not only the verdict |

Demonstrated against this repository, not only in fixtures: `strict = false` in
`[tool.mypy]` reports `LOOSENING — True → False (stricter is true)` and exits
`1`; adding `ARG` to ruff's `select` reports `NARROWING — added ARG`; renaming
`I` to `ISORT` reports the first declining case with both members named.

### Two bugs the tests found before anything shipped

**A glob is not a path.** `stacks.typescript.gates.lint.config` names
`.eslintrc*`, because eslint accepts several spellings. Passed through as a
filename, `git show <ref>:.eslintrc*` **does not fail** — it resolves the
argument as a revision and prints the commit — so the first run of the command
classified two commit messages as configuration. Patterns are now expanded
against the files git can see, and the read uses `cat-file blob`, which errors
on a path that is not a blob.

**A boolean is an integer in Python.** `isinstance(False, int)` is `True`, so a
ceiling changed from `100` to `off` — which YAML reads as `False` — compared as
`False < 100` and reported a **narrowing**. A relaxation dressed as a tightening
is the single outcome ADR 0040 exists to prevent, and it arrived through the
language rather than through the design. `::test_a_boolean_is_not_a_number_however_python_feels_about_it`
keeps it out.

### Where the direction comes from, and why not from the checker

`variance.polarity` in the register, keyed by a setting's leaf name. ADR 0018's
boundary test decides it: a reasonable Equal Experts repository could gate a tool
this checker has never heard of, so a polarity table in `src/` would be a
coverage limit nobody could see or extend.

Guessing from the key's name — `max_*` is a ceiling, `min_*` is a floor — was
considered and rejected. It looks principled and is wrong the first time a tool
spells a ceiling `limit`, and a wrong polarity is exactly the failure above.

The block is **short by design and honestly so**: three settings, which are the
ones this repository can demonstrate a direction for. The report names every key
it declined on, so the gap is visible and closable rather than silent.

### What the slice deliberately left open

- **It is not a gate, and must not become one.** The command runs on demand and
  a report that runs on demand is not a gate. The controls that fail on a
  weakening still do, through their own asserts. Moving one of those checks here
  would trade a build failure for a command somebody has to remember.
- **The delta is between two git revisions, not against what the gate would
  write.** `02-skill-family.md` § The three moments describes the sweep as
  noticing that *"the deployed artefact has been edited away from what the skill
  would write"*, and that is right about the moment and wrong about the
  instrument: rendering a gate's template inside the checker re-implements that
  gate's substitution, which is a second copy of the gate living in the auditor.
  What the sweep can still ask — *is this gate owed a re-run* —
  `register-check deployments` already answers from the stamp.
- **`--path` exists because DOC-001's config is not in `stacks:`.** It is
  `lint-md`'s control in another plugin, so no gate's `config` entry names its
  file. That is a gap in what the register knows about, not in the classifier,
  and closing it means the register naming the markdown config location — which
  is a decision about a control this repository does not own.
- **Nothing classifies a `kind: command` gate's behaviour**, only its
  configuration. A tool whose defaults changed between two pinned versions moves
  no config key and this reports `UNCHANGED`, correctly and unhelpfully.

## The fifth slice — a pinned digest is checked against what was published

Landed 2026-08-27, at register contract 34. It closes the checksum row, which
was added to the plan on 2026-08-26 after fixing Renovate's uv bump by hand.

### What was found, and what the row did not anticipate

The row is right about the failure: #74 moved the version literal at all four
sites the register names and left **all three** sha256 digests at 0.12.5's
values, and every check passed. What it would have merged is a container that
cannot build.

It is also right that two halves are needed, and for a sharper reason than it
gives. **#74's two sites agreed with each other**, so the offline reconciliation
passes it — measured, not assumed. Only the comparison against what the project
published fails it. The offline half earns its place on the opposite mistake:
one site edited and not the other, which the network half passes whenever the
edited site happens to be right.

Two things the row got wrong, both in the same direction:

**The per-asset `.sha256` it names covers one pinned tool of two.** uv publishes
`<asset>.sha256`; gitleaks does not — measured, `404`. Both publish a
**manifest**: uv `sha256.sum`, gitleaks `gitleaks_<version>_checksums.txt`, each
a list of `<digest>  <filename>` lines. One shape reads both, so the register
names a manifest.

**The aarch64 digest is no longer compared by nothing.**
`09-phase-1.5-review.md` recorded it as unverifiable and the row repeats that. A
manifest lists every architecture, so the register names the second digest in
`checksums.also` and the same fetch checks it. Four digests are now compared
where the row expected one.

### Why it is a control of its own

SUP-001 was the natural home — it already carries `tool_versions_match_register`
— and it is the wrong one. SUP-001 declares a `pre-push` locus from contract 31,
so `register-check run --control SUP-001` runs in a git hook, and a `kind: remote`
block on it puts a network fetch in front of every push. Offline that is
`UNCLASSIFIED`, exit `3`, and the hook refuses: a developer on a train could not
push a documentation fix.

So the property gets a control and the control gets the locus its verification
can answer at — `ci` alone. That is ADR 0039's test applied in the other
direction: there, SEC-003 was kept *out* of a local locus because its remote
blocks need an Actions job; here, a new control is given a `ci`-only locus
because its remote block needs a network.

### One thing the runner had to learn

Every remote block until now reads a repository's own platform state, so the
runner resolves a credential first and reports `SKIPPED (no credentials)` when
there is none. A release manifest is **public**, and a check that can answer
without a token reporting `SKIPPED` for want of one is the checker declining a
question it could have answered. `PUBLIC_REMOTE_ASSERTS` names the exception and
the runner skips credential resolution for it.

### What closed, and what the evidence is

| Criterion | Evidence |
| --- | --- |
| A version bump that leaves a checksum behind fails something | `tests/test_checksums.py::test_the_renovate_case_fails` reproduces #74's exact shape — version moved, digest left, both sites agreeing — and the offline half passes it while the network half fails it |

Measured against this repository before the tests were written: with `0.12.5`'s
digest at both sites and the version at `0.12.6`, SUP-004 reports
*"uv-x86_64-unknown-linux-gnu.tar.gz is pinned at 68a509da24b0… and the release
published 8681d8921e7d…"*. With `setup.sh`'s aarch64 digest altered, the offline
half reports both directions in one verdict — the digest no locus repeats, and
the digest the register does not name.

All four digests were checked against upstream while this was written and all
four match, so the control lands green. That is the honest but weaker position:
it shows the mechanism runs, not that it bites. What shows that is the test.

### What the slice deliberately left open

- **The conformance run now depends on a release endpoint.** Under
  `--require-complete` an unreachable network is exit `1`, because
  `UNCLASSIFIED` is what an unanswerable check reports and the flag promotes it.
  That is the accepted cost of this being a control rather than a test, and the
  `ci`-only locus is what confines the fragility to the one place that always
  has a network.
- **A tool that publishes no manifest passes**, saying so in the report. Whether
  a project publishes checksums is a fact about that project, and failing a
  repository for someone else's release process would make its conformance run
  unpassable for a reason nobody in it could fix.
- **Nothing verifies the artefact itself.** The comparison is register against
  published manifest; if a project's own manifest disagrees with its own
  tarball, that is the project's defect and this does not see it. Downloading
  two release tarballs on every run to learn what a 200-byte manifest already
  says was rejected as cost without assurance.
- **The register still needs a human to fetch a new digest on a bump.** The
  comment beside `tools.uv.sha256` saying so stays true. What changed is that
  forgetting is no longer silent.

## The sixth slice — the route out of the lint-md impasse

Landed 2026-08-27. It closes no criterion and is not meant to: it fixes a
contract so that the issue raised upstream and the amendment submitted after it
describe the same thing, and so a future release can be judged against something
citable rather than against whatever anyone remembered wanting.

### What was found

The plan's four rows are right about what `lint-md@1.0.7` does — re-measured
against the installed skill: `npx --no-install markdownlint-cli2` at **eight**
sites, and `.claude/**` appended to `ignores` at Step 2b. What the plan gets
wrong is the response.

Arguing both rows upstream resolves two values and leaves the mechanism that
produced them in place. The next release picks a value this register disagrees
with somewhere else, and the skill is unrunnable again. Every disagreement then
looks like a defect in the skill, when most of them are legitimate differences
between repositories.

[ADR 0042](adr/0042-a-deploying-skill-reads-local-configuration.md) proposes the
generalisation: a skill that deploys artefacts takes the values it writes as
**input**, read from a repository-local file keyed by skill name, with an absent
file meaning exactly today's behaviour. Both rows become one line of local
configuration each.

### The one thing that made this worth an ADR rather than an issue

The local file is a **second statement** of two values `controls.yaml` already
holds, which is the duplication this repository exists to prevent. Accepting it
needed a reason, and the reason is that the alternative is worse: generating the
file from the register at deploy time would put a `controls.yaml` reader inside a
plugin that must work for repositories with no register at all.

What keeps the copy honest is that `markdown_gate_wired_at_all_loci` already
reads the deployed artefacts against `tools.markdownlint-cli2.invocation`, so a
local config that drifted from the register fails the build on the next run. The
copy is **checked**, which is the condition this repository has always put on the
ones it keeps.

### What the slice deliberately left open

- **It is a proposal.** Nothing ships until `ee-skills` takes it, and the
  working amendment against `lint-md` is the next step rather than part of this
  one.
- **The two rows still need raising**, and the contract does not retire them.
  Setting `ignores: []` locally stops `.claude/**` reaching this repository and
  not anyone else's; ADR 0019's argument is about any repository.
- **Neither of the phase's two upstream-release criteria closes here.** Taking a
  release with a recorded outcome, and distinguishing *nobody redeployed* from
  *the release would revert a narrowing*, both need a mechanism that records the
  declination and a report that reads it. What this slice gives them is the
  reason to record — which was previously an argument in prose.

## The seventh slice — a declination is a record, not a memory

Landed 2026-08-27. It closes the two upstream-release criteria, and the location
question that had been the phase's last open design decision.

### Where it went, and the three places it could not go

`deployment-decisions.yaml`, at the repository root beside `controls.yaml`.
Excluded first, each by a rule already in force:

- **`controls.yaml` and anything under `plugins/`** — a declination is this
  repository's posture, and ADR 0022 requirement 6 keeps posture out of what an
  adopter installs. `tests/test_deployment_decisions.py` holds that boundary for
  this file as `tests/test_posture.py` holds it for the platform-token choice.
- **`.claude-plugin/deploys.json`** — the *plugin's* sidecar, declaring what a
  gate writes. This is the consuming repository's record about a skill it did
  not run.
- **`.claude/skill-config.yaml`**, the file ADR 0042 revision 1 proposes — its
  name and location belong to `ee-skills`, and writing our records into someone
  else's contract is how that contract stops being one.

The root is right rather than merely available: this is the counterpart to the
provenance stamps. A stamp records what *was* deployed; this records what
deliberately was not. They belong at the same level of the tree.

### What makes it a record rather than an opt-out

Two rules, both checked:

**An entry covers the version it names and no later one.** Declining
`lint-md@1.0.7` does not decline 1.0.8. A new release re-opens the question, and
that re-opening *is* the criterion about distinguishing a chore from a decision.

**An entry expires.** One that never does is the `variance: justified` loophole
register contract 3 removed — a weakening permitted by a recorded reason, with
the mechanism meant to stop it becoming permanent structurally unreachable.

Three ways the record can stop describing reality, and each **fails** the
command: expired, superseded by a deployment the repository has since made, or
naming a skill nothing here stamps. That is the asymmetry the command now turns
on — a stale *deployment* is a recommendation and exits `0`; a stale *record* is
a claim that has stopped being true and exits `1`. A file that will not parse
exits `2` rather than reading as no declinations, which would report every
declined deployment as a chore nobody got to, in a report that looked entirely
ordinary.

### What closed, and what the evidence is

| Criterion | Evidence |
| --- | --- |
| Taking an upstream release has a recorded outcome — redeployed, or declined with the disagreement named | The `lint-md@1.0.7` entry, read back by `register-check deployments` under *Deliberately not deployed* with the reason, the ADR and the expiry. `::test_the_command_reports_this_repository_s_declination` |
| A deployment behind because nobody redeployed is distinguishable from one behind because the release would revert a narrowing | The same report shows five gates `UNRECORDED` (chores) and one skill `DECLINED` (a decision), from two different mechanisms. `::test_a_stale_record_fails_where_a_stale_deployment_does_not` holds the exit codes apart |

Measured by hand against this repository before the tests were written: with the
expiry moved into the past, the superseded version, and an unknown skill name,
each reports its own line and exits `1`; a truncated file exits `2`.

### One bug the tests caught

`_version_key` returned a *partial* parse for an unreadable version, so an empty
key sorted below every deployed version and the record was reported as
superseded — telling someone to delete a live declination. Both sides must parse
before the comparison is made at all, and
`::test_a_version_that_does_not_parse_never_claims_to_be_superseded` keeps it
that way.

### What the slice deliberately left open

- **Nothing here knows what version is available.** The checker reads the
  record and the stamps; it cannot see that `lint-md@1.0.8` exists, so it cannot
  tell you a declination has been overtaken by a newer release. That comparison
  belongs to `skill-update`, which reads installed plugins — and whose own
  criterion is still open.
- **A declination is not a variance.** It says a release was not taken. It says
  nothing about whether the deployed artefacts still satisfy the control, which
  is the register's own asserts' job and unaffected.
- **ADR 0042 was amended rather than superseded**, and a stricter reading of
  ADR 0026 would have made this a new ADR. It was folded in because it is the
  same decision's other half and the ADR was a day old; the revision history
  says so rather than leaving the choice implicit.

## The eighth slice — the sweep

Landed 2026-08-27. It closes the phase's headline criterion and the standing
adopter-facing one that was waiting on it, and it closes them as **two**
scheduled runs rather than the one the plan describes.

### What was found

The plan says *"a scheduled sweep running `register-check` across repos"*. The
across-repos half was already settled — this repository manages itself and does
not reach into another — but the remaining question was what a per-repository
sweep should actually run, and the answer turned out to be *not one thing*.

**A full conformance run needs tools.** gitleaks, markdownlint and the frozen
node install all have to be present or the report is a wall of `UNCLASSIFIED`.
Installing them in a sweep workflow is a **second copy of
`register-check.yml`'s setup**, free to drift from it — the duplication this
repository exists to prevent, arriving through the back door of a new workflow.

So the conformance half was solved by not writing it: `register-check.yml`
gained a `schedule:` trigger. The run that already knows how to install its
tools is the run that should do it, and the change is one line rather than a
file. A schedule run has no pull request, so `FROM_A_FORK` is empty and the step
takes the `--require-complete` branch — correct, because it runs on the default
branch carrying the repository secret.

**That leaves the report with no other home.** `register-check deployments`
reads the sidecar, the stamps and the declination record — files, no external
tool — so the sweep needs uv and nothing else.

### Why any of this is worth a schedule

Several controls can start failing with **no commit at all**, and that is the
argument for the whole slice rather than a detail of it:

- **SUP-004** reads what a project published, and a release can be re-cut.
- **GOV-003** expires on a date.
- **SEC-001's and SEC-003's remote blocks** read platform state an
  administrator can change — push protection turned off is exactly the drift no
  diff would ever show.

Without a schedule the first person to know is whoever opens the next pull
request, which in a quiet month is nobody.

### The report has two homes, because they answer different questions

The **job summary** is the record of this run, written whether or not anything
is owed — so a green sweep is visible rather than silent. The **issue** is the
record of the *condition*: opened when something is owed, edited while it
persists, closed when it clears. One issue, never one per run, or the sweep
becomes the noise it exists to prevent.

**The job does not fail on findings**, and that is the design rather than a
softness. A red scheduled workflow is a notification people learn to dismiss,
and staleness is reported and never enforced. It fails only when the sweep
itself could not run — exit `2` from the report, or no summary line to parse.

### One register change the sweep forced

`PLATFORM_READ_TOKEN` permitted `[push, pull_request]`. A scheduled run
referencing it would have failed SEC-003 — a secret under an event the register
does not permit — so `schedule` joined them. It is also the *safest* of the
three: a schedule fires only on the default branch, where a `pull_request` run
can be proposed by anyone.

### Two things caught by the checks rather than by review

**`|| true` in a comment is `|| true`.** The findings step carried a comment
explaining why the idiom was avoided, and `no-failure-suppression` scans the
whole `run:` block — so LNT-001 and TST-001 both failed on prose. Correct
behaviour: a comment is a place a real suppression could hide.

That is the second time in one day a scanner has caught a marker in prose — the
declination record's header carried a literal `ee-control:` and was read as a
malformed stamp. Both are the same shape, and both were found by a check rather
than by a reader.

### What the slice deliberately left open

- **Nothing compares against what is available upstream.** The sweep reports
  what this repository has and has decided; it cannot see that a newer `lint-md`
  exists. That comparison is `skill-update`'s, whose criterion is still open.
- **The sweep has never fired.** It is scheduled weekly and carries
  `workflow_dispatch` so it need not be discovered by waiting for a cron, but
  the first real run is ahead of this record rather than behind it. What is
  demonstrated here is that the workflow parses, that the report it runs exits
  `0` with five gates owed, and that the summary line it parses says `5`.
- **The tracking issue's title is the join key.** A renamed issue orphans the
  record and the next run opens a second. A label would be sturdier and needs a
  label to exist first; this is the smaller assumption, recorded rather than
  hidden.
