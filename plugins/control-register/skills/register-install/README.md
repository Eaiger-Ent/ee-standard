# register-install

Adds `register-check` to a repository, pinned to the tagged ref the register
names, and writes the one CI step that runs it over the whole register.

## What it does

It adds the checker to the repository's dependencies, pinned to a git tag, and
confirms `register-check --version` runs through the package manager. Then it
appends a Conformance step to the job CI-001's `required_checks:` names, so the
check a merge waits for carries every control's verdict (ADR 0057). Run it as
`/register-install`, or let `/register-adopt` dispatch it. Pass `--yes` to
pre-answer the one Install / Cancel question. It prints a plan before writing
anything and a report afterwards. Nothing is committed.

## Approach

### Why this exists at all

Because the checker had no way into a repository that was not its own.

`register-check` lives in `src/` of the repository that defines the standard.
Inside that repository `uv run register-check` resolves, because the project
being run is the project being checked — and every locus the standard wires has
therefore been exercised against a checker that was already present. From
outside, three Tier-1 controls run a command that does not exist: the pre-commit
hooks for SUP-003, BLD-001 and DEV-001, the CI job CI-001 requires, and the
adopter's own audit.

That gap was invisible from inside, which is the shape of defect this project's
review record keeps finding — a property that holds for the author's environment
and was never a property of anything.

### What it installs

A dependency pinned to a git tag:

```text
register-check @ git+https://github.com/<owner>/<repo>@v<x.y.z>
```

Every part of that comes from the register. The repository and the tag are
`tools.register-check.install`; the grammar that joins them to a package name is
`ecosystems.<name>.git_dependency`, because PEP 440's direct reference is a fact
about Python and not about this standard. A fork, an internal mirror or a new
release changes the address without changing this skill.

**A tag, never a branch.** An unpinned git dependency resolves to whatever the
default branch says today — the same defect as a floating image tag (DEV-001) or
a floating action ref (SUP-003). The checker would be the one tool in an
adopting repository that could change under it between two runs of one commit.

**Public, so no credential.** The repository is public, which is what makes the
install work for someone who has been granted nothing. That is a load-bearing
dependency rather than a convenience: taking the repository private would break
every adopter's install.

### Why a skill of its own

Three candidates were considered and two rejected
(ADR 0032).

**Not `register-adopt`'s pre-flight.** The dispatcher *verifies through* the
checker — every gate it dispatches ends with `register-check run --control <ID>`.
A step that installs the instrument it then measures with belongs on its own,
where it can be run, re-run and reasoned about without the plan around it. It
also strands anyone deploying a single gate: `gate-secrets` alone needs the
checker as much as the whole family does.

**Not `gate-supply-chain`.** A gate writes the artefacts its controls name, and
no control names *the checker is installed*. SUP-001, SUP-002 and SUP-003 are
about lockfiles, update proposals and frozen installs; the checker being present
is a precondition of all three being *checkable*, which is a different thing. A
gate writing something no control names is the drift this repository watches for.

### Why it also writes the Conformance step

Because nothing else asked the register for its verdict. Each gate's CI step
runs that control's tools, and a control can pass its tools while failing its
own checks: `uv run mypy` passes while TYP-001 fails on a module `files` leaves
out. One adopting repository read TYP-001 FAIL for 27 days under a green build.
The step runs the checker over the whole register as the **last** step of the
job a merge waits for, so that verdict blocks the merge (ADR 0057).

It goes in the job CI-001 names, not a new one, because a check no merge waits
for blocks nothing. Where no gating workflow exists yet the step is deferred
rather than written into a new workflow, because the workflow's setup belongs to
the gates. `register-adopt` re-runs this skill after the gates for that case.
The step lets exit `3` (nothing failed, something unverifiable) through and
nothing else. It never uses `continue-on-error` or `|| true`, which would let a
verified violation through as well.

## What it does not do

It writes no `ee-control:` stamp. A stamp names a control and the gate that
deployed it, and there is no control here to name — so the absence is the
decision rather than an omission. The Conformance step is unstamped for the same
reason: it deploys no control, it computes the verdict of the ones the gates
deployed.

It does not run the full audit afterwards. `register-check run` over a
repository with no gates deployed reports failures for every control, which
reads as this skill having broken something. `register-adopt` takes that run as
its starting state, which is where the output means something. The one local run
it does make comes *before* the Conformance step is written. It names every
control that will fail the required check once the step lands, so a red build
after the merge is the expected one.

It does not commit. What it changes is a manifest, a lockfile and a workflow,
and where they go is a decision for whoever is adopting.

`--yes` answers the Install / Cancel question and nothing else. The plan is
still printed. `reference/unattended.md` lists what it must never answer.

## What is still open

**Whether a bot proposes an upgrade.** SUP-002 requires a bot that proposes
dependency updates, and whether Dependabot or Renovate proposes a bump for a
`git+https` dependency pinned to a tag is **not verified**. Recorded as
unverified rather than assumed: if neither does, an adopter's pin rots at a
known version, which is a different failure from an unpinned one and not a
better one.

**The non-Python adopter.** A repository that is not a Python project cannot put
a Python package in its lockfile. `uv tool install` onto `PATH` is the only
remaining route and carries the hazard ADR 0020 measured. This skill stops and
says so rather than inventing a spelling.

## Invocation

Invoked by `register-adopt`, which dispatches it through the Skill tool — do
not add `disable-model-invocation: true` here. A dispatched skill carrying that
flag cannot be reached at all, which is preflight P9 and is what stopped the
front door at Step 0 in Phase 4. The reasoning, and what guards the platform
mutations instead, is
ADR 0035.

## References

- [PEP 440 — direct references](https://peps.python.org/pep-0440/#direct-references) — the `name @ git+<url>@<tag>` grammar the pin uses
- [uv — Git dependencies](https://docs.astral.sh/uv/concepts/projects/dependencies/#git) — how the pin is resolved and locked
- [GitHub Actions — `continue-on-error`](https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions#jobsjob_idstepscontinue-on-error) — why the Conformance step must not carry it
- ADRs 0016 (exit codes), 0020, 0032, 0035, 0036 and 0057, in the `ee-standard` repository
