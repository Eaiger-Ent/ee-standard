# register-adopt

The front door. Reads the register, works out which controls apply to your
repository, shows a plan, dispatches the gates, verifies, commits.

## It writes no gate configuration

Every artefact is written by the gate that owns the control. That is what keeps
one control's config in one place, and it is why this skill is short: it decides
*which* gates run and in *what order*, and nothing else.

If a control has no gate, it is planned as **dispatch elsewhere** (DOC-001 is
`lint-md`'s, in another plugin) or as **manual**, with a pointer to
`08-adopting.md`. Neither is dropped from the plan — a control absent from the
plan reads as a control that does not apply.

## It dispatches `register-install` first, and that is not a gate

Everything this skill does runs `register-check` — including the pre-flight that
computes the plan. So Step 0 checks the checker is there and, if it is not,
dispatches `/register-install`.

It is not in the dispatch table below and is not selectable. No control names
*the checker is installed*, so it deploys nothing and appears in no plan row; a
plan that offered to skip it would offer to compute itself without the
instrument it is computed with.

## Why the dispatch order is what it is

Not alphabetical, and not the order the gates were built.

| # | Gate | Why here |
| --- | --- | --- |
| 1 | `gate-build` | Owns `.devcontainer/` and creates `setup.sh`, which two later gates write their own regions into |
| 2 | `gate-supply-chain` | Writes the frozen install every other gate's CI steps run after — a lint step before it lints against nothing |
| 3 | `gate-secrets` | Writes into `setup.sh` and the gating workflow, both of which now exist |
| 4 | `gate-quality` | The same two files, plus the editor locus |
| 5 | `gate-iac` | Independent; last of the file-writing gates |
| 6 | `gate-repo` | Last, because its effect is not a file and cannot be reviewed before it takes effect |

The first two positions are load-bearing. Everything else is preference.

## One confirmation, and one exception to it

Step 3 asks once, covering the whole plan. `gate-repo` asks **again** on its own,
and that is right rather than redundant: this plan covers what will be written to
files, and a GitHub API call is not a file. Its ruleset is in force the moment
the call returns, for everyone with access.

## Predicates are evaluated, never asked

Whether your repository is a Python project, has Terraform, or ships a container
is decided from its files. Asking would let a user declare their way out of a
control, which is the one thing `applies_to` exists to prevent.

## Verification is the point

Writing the config and confirming the config works are different claims, and
only the second is worth anything. Step 5 is the step most such tools omit.

It runs over the **whole register**, not only the controls just deployed. A gate
that wired its own control and broke another's CI step is exactly what a per-gate
verify cannot see.

**Exit `3` is the expected result today, and it is not a pass.** SEC-001's and
CI-001's remote blocks report `SKIPPED (no credentials)` until Phase 3 implements
`kind: remote`. The skill names which blocks were skipped rather than rounding
up, and it will not commit on an exit `1`.

## What it cannot do

**Grant a permission or install a bot.** Dependabot or Renovate enabled on the
repository, GitHub secret-scanning push protection, and `administration: write`
for the branch ruleset are platform acts a human with admin takes
(`08-adopting.md` § 1). They are listed in
the plan *before* deployment, because a plan that omits them promises an outcome
it cannot reach.

**Prove that a model followed it.** This is prose, and prose is followed or it is
not. `tests/test_register_adopt.py` drives the sequence it describes through the
six gates' shipped templates and watches the verify step fail on a broken
config — so what is proved is that the pipeline works, not that the instructions
were obeyed. That limit is the same one every gate's tests carry, and it is
stated rather than glossed.
