# The skill family

How the standard reaches a repository, and how it stays current once it is there.

Read [`00-concepts.md`](00-concepts.md) first — particularly § The plugin
boundary, which is the constraint this whole design bends around.

## What already exists

Before designing anything, the `ee-skills` marketplace was surveyed. Two
existing plugins own parts of this problem, and the family below **composes with
them rather than replacing them**. Rebuilding any of these would
create exactly the duplicate-definition drift the register exists to prevent.

| Existing plugin | What it owns | Consequence for us |
| --- | --- | --- |
| `lint-md` | The entire DOC-001 lifecycle — installs `markdownlint-cli2`, writes the config, wires the editor hook, pre-commit hook and CI step, migrates from `pymarkdownlnt` | DOC-001 carries `deployed_by: lint-md`. We do not write a markdown gate. |
| `devcontainer-check` | Health-check that declared CLI tools are installed and authenticated | Complementary: it checks the *environment*, we check the *configuration*. Neither subsumes the other. |

**A third was here and is not any more.** `project-init` owned interactive
devcontainer configuration, and this family deferred to it for the choice of
image. The shipped template now produces a configured `.devcontainer/`, and
`project-init` re-chooses the image in a way that fails DEV-001, so the standard
does not compose with it
([ADR 0037](adr/0037-the-template-is-the-whole-devcontainer-step.md)). Saying so
rather than dropping the row: a table that quietly loses an entry reads as a
survey nobody finished.

`lint-md` is also the shape everything here copies: pre-flight state detection →
install tool → write config → wire every locus → migrate predecessor → verify
its own wiring. That sequence solves the hardest part of config deployment and is
not improved by reinvention.

The key insight from reading it: **the conformance checker is not a new
invention.** It is the pre-flight section of every `lint-md`-shaped skill,
factored out, made schedulable, and driven by the register instead of hard-coded
per skill. `lint-md`'s `check-hook-registered.py` is already a
`verify.kind: file` control — it is just trapped inside one skill.

## Shape of the family

One plugin, several skills — following the `ee-skills-manage` precedent (one
plugin shipping `skill-sync`, `skill-update`, `marketplace-replace-local`) and
the dispatcher model used by `design-authoring`.

```text
plugins/control-register/
  .claude-plugin/
    plugin.json          name, version, dependencies
    deploys.json         sidecar — see § The deploys sidecar
  LICENSE                required by CI on every plugin
  skills/
    register-adopt/      dispatcher — the front door
    register-install/    puts the checker in the repository, pinned to a tag
    register-variance/   classifies and reports local deltas
    gate-secrets/        SEC-001, SEC-002
    gate-supply-chain/   SUP-001, SUP-002, SUP-003
    gate-build/          BLD-001, DEV-001
    gate-repo/           CI-001  (remote locus)
    gate-quality/        LNT-001, TYP-001, TST-001
    gate-iac/            IAC-001
```

Gates are grouped by the artefact they write, not one-per-control. `gate-quality`
writes one pre-commit config and one CI workflow covering three controls; three
separate skills would fight over the same two files.

That tree is the **marketplace's** layout — `ee-skills/plugins/adr-toolkit` has
exactly this shape — and it is what this repository builds. It is not the
incubator's, which stores skills flat and groups them in a config file, and it
is not what `/skill-submit-new` reads. Both differences are Phase 6's and are
recorded in [`05-promotion.md`](05-promotion.md) § What the incubator actually
holds rather than restated here.

`register-install` replaced a planned `register-check/` skill that would have
"installed and wrapped" the checker. The wrapping half was wrong: the checker is
an ordinary executable that CI runs with no Claude present, and a skill that
wrapped it would be a second way to invoke it, free to disagree with the first.
What was left was the install, which is real work nothing else owned — three
Tier-1 controls run a command that, outside this repository, did not exist
([ADR 0032](adr/0032-the-checker-is-installed-from-a-tagged-ref.md)). It writes
no stamp, because no control names *the checker is installed*, and it is the one
skill here whose output belongs to no control.

## The dispatcher: `register-adopt`

The only entry point a user needs.

1. **Pre-flight** — read `controls.yaml`; evaluate every predicate against the
   repo (`pyproject.toml` present? any `*.tf`? any `Dockerfile`?); read every
   provenance stamp already in the repo.
2. **Plan** — present a table: control, applicable?, currently deployed?, stamp
   version, action. Nothing is written yet.
3. **Confirm** — one `AskUserQuestion` covering the whole plan.
4. **Dispatch** — invoke each needed `gate-*` skill in dependency order.
5. **Verify** — run `register-check` and report. A gate that deployed but does
   not verify is reported as a failure of the adoption, not a success.
6. **Commit** — one commit, conventional format, listing the control IDs
   deployed.

Step 5 is the step most such tools omit. Writing the config and confirming the
config works are different claims, and only the second one is worth anything.

## The gates

Every `gate-*` skill follows the `lint-md` sequence:

| Phase | What happens |
| --- | --- |
| Pre-flight | Detect current state — tool installed? config present? hook wired? CI step present? predecessor tool present? |
| Install | Install the pinned tool version |
| Write | Write the config, **including the provenance stamp** |
| Wire | Every locus in the control's `locus` list — editor, pre-commit, CI |
| Migrate | Remove the superseded predecessor, if any |
| Verify | Assert its own wiring — the same asserts the checker uses |

The verify phase calls the *same* assert implementations the checker uses, not a
private copy. A gate that verifies itself with different logic than the auditor
will eventually disagree with the auditor, and the disagreement will be
discovered at the worst time.

### `gate-repo` is different

CI-001 has `locus: [remote]` — there is no file to write. This gate calls the
GitHub API to create the ruleset, and its verification reads platform state back.
It is the only gate that changes something outside the repository, so it always
confirms explicitly before acting, regardless of the plan already approved in
step 3.

## The checker: `register-check`

**The checker is not a skill.** It is an ordinary executable, installed from a
pinned version, that reads `controls.yaml` and exits non-zero on failure. CI runs
it with no Claude present — that is the whole point of the plugin boundary.

The `register-check` *skill* does two things a binary cannot: install and pin the
binary, and explain a failure in context with a proposed fix.

```bash
register-check                 # all applicable controls; exit 1 on any failure
register-check run --tier 1    # subset — the subcommand is required
register-check explain SEC-001 # what it checks, why, and the standard it cites
register-check meta GOV-001    # the meta-controls
register-check schema          # validate controls.yaml itself
```

A selective run — `register-check run --control X --control Y` — is what a
`pre-push` hook invokes, because a full audit on a developer's machine cannot
complete: a `kind: remote` block with no platform credential is `UNCLASSIFIED`,
the run exits `3`, and a hook doing that would refuse every push
([ADR 0039](adr/0039-a-push-is-a-locus.md)).

Verdicts are `PASS`, `FAIL`, `SKIPPED (predicate)`, `SKIPPED (no credentials)`,
and `UNCLASSIFIED`. The two skip reasons are distinct on purpose: a control
skipped because the repo has no Terraform is fine; a remote control skipped
because no token was available is a hole, and must never read as a pass.

## Staleness

The mechanism that keeps a deployed gate current without churning the CI harness.

### Notify, never redeploy

Nothing here rewrites CI configuration automatically. Deployment always produces
a reviewable pull request. The tooling's job is to make *"a deployment is owed"*
knowable at the moment it becomes true.

### The three moments

| Moment | What is known | What happens |
| --- | --- | --- |
| On install | A newly installed plugin deploys config; none present in this repo | "`lint-md` installed. It deploys a config, a hook and a CI step — run `/lint-md` to wire it." |
| On update | A plugin moved past a version where *what it writes* changed | "`lint-md` 1.0.6 → 1.1.0 changes its deployed config. Re-run to pick it up." |
| On sweep | The deployed artefact has been edited away from what the skill would write | Reported by `register-variance` with its direction |

### The noise control

The second moment is where *"we don't want to be reconfiguring the CI harness
constantly"* is won or lost. A plugin's version changes for documentation fixes,
prompt tweaks and new trigger phrases — almost none of which change the files it
writes. Key the recommendation to plugin version and it fires on every release
until people stop reading it; key it to nothing and staleness is invisible.

So each plugin declares **what it deploys, and a contract version that changes
only when the deployed output changes**. Redeployment is recommended when the
installed contract version is ahead of the one stamped in the repo, and stays
silent through every release that did not change the output.

**The stamp carries that number** — `gate-contract`, added by
[ADR 0038](adr/0038-the-stamp-records-the-deployment-contract.md), which is what
gives the comparison above something on the repository's side to compare
against. It was missing for three contracts and nothing noticed, because nothing
read `deploys.json`. A stamp written before it says *unrecorded*, which is
neither current nor stale.

### The `deploys` sidecar

```json
{
  "schemaVersion": 2,
  "gates": {
    "gate-secrets": {
      "contractVersion": 5,
      "controls": ["SEC-001", "SEC-002"],
      "artifacts": [
        ".pre-commit-config.yaml#gitleaks",
        ".github/workflows/register-check.yml#secret-scan"
      ]
    }
  }
}
```

**One contract per gate, not per plugin.** Six gates ship in this one plugin, so
a plugin-wide `contractVersion` would make changing what `gate-quality` writes
recommend redeploying `gate-secrets` — a redeployment notice for a gate whose
output did not move. Phase 5's first two exit criteria are exactly *a version
bump produces no recommendation, a contract bump does*, and a contract that
fires for the wrong gates fails the second while appearing to pass it. The
second gate is what forced the shape; `10-phase-2-review.md` records it as a
decision rather than a refactor nobody wrote down.

`tests/test_plugin.py` holds the sidecar to the register in the one direction
that can be wrong: a control the register marks `deployed_by: <gate>` must
appear under that gate. `SEC-002` is listed under `gate-secrets` without a
`deployed_by` of its own, which is correct — the gate checks it and writes
nothing for it.

This ships as `.claude-plugin/deploys.json`, a **sidecar rather than a key in
`plugin.json`**. The precedent is `readme-meta.json` in `ee-skills`, which exists
as a sidecar because `claude plugin validate` rejects unknown keys in
`marketplace.json`. Whether `plugin.json` tolerates unknown keys has not been
confirmed, and a sidecar costs nothing while removing the risk entirely. If
validation is later confirmed to permit it, folding the block into `plugin.json`
is a trivial change.

### Where the recommendation surfaces

`skill-update` already collects `id`, `version`, `scope` and `installPath` for
every plugin at its discovery step. Reading each plugin's `deploys.json` from
`installPath` needs no new infrastructure — the data is in hand at the point the
skill already pauses to report. Per-gate contracts do not change that: it is
still one file at one path, and the gate a stamp names is the key to compare
against.

The reconciliation itself is `register-check deployments`, so `skill-update` and
`register-adopt` report the same states from the same code rather than each
computing its own.

It gains a read-only reconciliation section and an offer to hand off to
`register-adopt`. It never writes gate config itself. `lint-md` sets
`disable-model-invocation: true` anyway, so recommending is the only available
move — the correct constraint rather than an obstacle.

**One change is required to `skill-update` itself.** Its success criteria
currently require that "at least one plugin was identified as stale", otherwise
it reports *Already done*. A repo whose plugins are all current but whose gates
were never deployed would report success — precisely the wrong answer. That
criterion must widen from *a stale plugin* to *a stale plugin or an owed
deployment*, or the new report will be computed and then contradicted by the
summary printed underneath it. This is a `skill-submit-amend` against
`ee-skills-manage`, tracked separately from the `control-register` submission.

### Loudness

Ordering comes from the register at no extra cost: sort the report by the tier
and rung of the controls each pending deployment carries. A Tier-1 security
control awaiting deployment reads differently from a markdown rule without
inventing a severity field to say so.

In CI, `register-check` **reports** a pending deployment rather than failing on
it — except where the owed deployment belongs to a Tier-1 control, which fails.
That is the ratchet: stability everywhere it can be afforded, and no quiet
erosion where it cannot.

## Version policy

Each control may declare how its tool version is resolved:

| Value | Behaviour |
| --- | --- |
| `pinned` | Exact version. Changing it is a register commit. |
| `floating-minor` | Patch and minor updates proposed automatically. |
| `latest` | Resolved at deploy time. Tier 3 only. |

Version resolution is a **proposal** mechanism, not an install mechanism: it
opens an update PR against the register. The gate itself always installs an exact
pinned version, because a gate whose version floats at install time makes CI
non-reproducible — the failure the pinning discipline exists to prevent.

## Constraints from `ee-skills`

Every skill in this family must satisfy the marketplace's own gates, verified
against the current `preflight-check.sh` (P1–P11, not the P1–P6 stated in
`CONTRIBUTING.md`, which is out of date):

| Check | Limit |
| --- | --- |
| P1 line count | SKILL.md ≤ 500 lines |
| P2 description length | ≤ 250 characters |
| P3–P11 | name field, invocation, argument hint, supporting files, `dependencies` in JSON, `${CLAUDE_SKILL_DIR}` paths, sub-skill invocation, no duplicate dir, argument flags |

Plus, from `CONTRIBUTING.md`:

- Every plugin ships a copy of the repo-root `LICENSE`.
- Hooks and scripts use `${CLAUDE_PLUGIN_ROOT}`, never hardcoded paths — a
  hardcoded path breaks when the plugin is copied into the install cache.
- An entry is required in both `marketplace.json` and `readme-meta.json`.

The 500-line limit is the binding constraint on `register-adopt`. The dispatcher
must stay a dispatcher: plan, confirm, delegate, verify, report. Every table of
per-control detail belongs in the register or a `templates/` file the skill
reads, not inline in the SKILL.md.

It bound `gate-quality` first, and for a different reason
([ADR 0036](adr/0036-shared-skill-prose-has-one-home.md)). Two of Phase 4's
fixes were written as a section pasted into every skill they governed — twelve
copies of two rules — and the count reached 510 before anything noticed. So
**prose more than one skill must follow is shipped once**, under
`plugins/control-register/reference/`, and read at runtime through
`${CLAUDE_PLUGIN_ROOT}`; the skill carries a pointer and nothing more. Two files
exist: `pre-commit-runner.md` and `write-narration.md`.
`tests/test_shared_reference.py` fails a pointer to a file the plugin does not
ship, and a skill that takes the section back.

## Category

None of the four existing categories (`development`, `productivity`, `workflow`,
`contributor-tooling`) fits a conformance family cleanly. `workflow` is the
closest but is described as coordinating cross-issue processes, which this is
not.

Per `CONTRIBUTING.md`, a poor fit should be resolved by adding a category in the
same PR rather than forcing one. Proposed: **`governance`** — *skills that
define, deploy, or audit engineering standards across repositories*. This
requires an entry in `.claude-plugin/categories.json` in the submission PR.
