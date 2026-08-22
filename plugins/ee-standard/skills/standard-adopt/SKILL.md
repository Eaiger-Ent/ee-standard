---
name: standard-adopt
description: >
  Adopt the Equal Experts control standard: plan every applicable control,
  confirm once, dispatch the gates, verify through the checker, commit.
  Triggers: 'adopt the standard', 'deploy ee-standard', '/standard-adopt'.
argument-hint: "[--repo <path>] [--register <path>]"
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion, Skill
---

# /standard-adopt — the front door

You are running the **standard-adopt** skill. It is the only entry point a user
needs: it reads the register, works out which controls apply to this repository,
shows a plan, and dispatches the gate skills that deploy them.

**It writes no gate configuration itself.** Every artefact is written by the gate
that owns the control — that is what keeps one control's config in one place. If
you find yourself editing a `.pre-commit-config.yaml` here, a gate is missing and
that is the thing to say.

**Three rules govern everything below.**

**The register decides.** Which controls exist, which apply, and which gate
deploys each are read from `controls.yaml` and from the plugin's `deploys.json`.
Nothing here holds a list of controls or a list of gates. A register that grows a
control this skill has never heard of must still be planned and dispatched.

**Predicates are evaluated, never asked.** Whether this repository is a Python
project, has Terraform, or ships a container is decided from its files. Asking
would let a user declare their way out of a control, which is the one thing
`applies_to` exists to prevent.

**Verification is the point.** Writing the config and confirming the config works
are different claims, and only the second is worth anything. Step 5 is the step
most such tools omit; a gate that deployed and does not verify is reported as a
failure of the adoption, not a success.

**Do not use when:**

- The repository has no `controls.yaml` and you have no register path to point
  at. There is nothing to derive a plan from; deploy the register first.
- You want one gate. Call it directly — `/gate-secrets`, `/gate-quality` and the
  rest each work standalone, and this skill exists to save you knowing which.
- The repository is not a git repository. Every assert reads what git tracks, so
  the plan would be computed against nothing.

## Inputs

| Input | Required | Default | Description |
| ------- | ---------- | --------- | ------------- |
| `--repo <path>` | No | current directory | The repository to adopt into |
| `--register <path>` | No | `<repo>/controls.yaml` | The register to plan from |

Both flags mirror `standard-check`'s own, and are passed through to every gate,
so a plan, a deployment and its audit can never be pointed at different things.

## Success criteria

1. Every applicable control appears in the plan, and every one that does not
   appear is reported with the predicate it failed.
2. Nothing was written before the plan was shown and confirmed.
3. Every gate the plan names was dispatched, in dependency order.
4. `standard-check` was run afterwards over the whole register, its output shown,
   and its verdict reported as given — including a failure.
5. The commit lists the control IDs deployed, and was made only after the verify
   step.

---

## Step 1 — Pre-flight

Nothing is written in this phase.

### Read the register

```bash
standard-check --repo "$REPO" --register "$REGISTER" schema
standard-check --repo "$REPO" --register "$REGISTER" run
```

The first tells you the register loads; if it does not, stop and show the error.
**The second is the starting state**, and it is worth keeping: at the end you
will want to say what changed, and a run taken afterwards cannot tell you.

For every control in the register, record:

| State var | From |
| --- | --- |
| `ID` | the control's id |
| `APPLIES` | whether its `applies_to` predicates hold — from the run above, where a `SKIPPED (predicate)` verdict names the one that did not |
| `GATE` | the control's `deployed_by`, or `—` where the register names none |
| `VERDICT` | its verdict in the starting run |

Then read the plugin's `deploys.json` for each gate named:

| State var | From |
| --- | --- |
| `ARTIFACTS` | `gates.<GATE>.artifacts` — what that gate writes |
| `CONTRACT` | `gates.<GATE>.contractVersion` |

### Read what is already deployed

Every `ee-control:` stamp already in the repository:

```bash
git grep -l 'ee-control:' || echo NONE
```

For each, record the control, the skill and version that wrote it, and the
register contract it names. Three states matter and they are not the same:

- **Absent** — nothing deployed this control here.
- **Behind** — the stamp names a register contract lower than the current one.
  That is *staleness*, which is reported and never enforced. A re-run may be
  owed; it is not owed by this skill's judgement.
- **Ahead** — the stamp names a contract the register has not reached. That is a
  defect, not staleness, and `provenance_stamp_present` fails it.

### The controls that are not simply "deploy"

Four plan rows, and only the first is the ordinary case. None of the other three
is an error, and **none may be dropped from the plan** — a control absent from
the plan reads as a control that does not apply.

| Row | When | What the plan says |
| --- | --- | --- |
| **deploy** | `deployed_by` names a gate in this plugin | the gate's name |
| **dispatch elsewhere** | `deployed_by` names a skill this plugin does not contain — DOC-001 is `lint-md`'s | the skill's name, and that it is another plugin's |
| **checked, not deployed** | `deploys.json` lists the control under a gate, and the control has no `deployed_by` | the gate that verifies it, and that nothing is written for it |
| **manual** | neither | a pointer to `docs/08-adopting.md` |

**The third row is not a gap in the register.** SEC-002 — *CI authenticates
without a long-lived cloud credential* — is satisfied by a workflow **not**
referencing a static credential. There is no artefact to write and so no
`deployed_by` to name; `gate-secrets` verifies it and writes nothing for it.

A control satisfied by an absence still has to appear in the plan, and has to be
distinguishable from one nobody has got to yet. Planning it as **manual** would
tell a reader there is an act they owe, and there is not.

---

## Step 2 — Plan

Show one table. One row per control, in register order:

```text
Control  Applies  Now                Gate               Action
SEC-001  yes      FAIL               gate-secrets       deploy
SEC-002  yes      PASS               gate-secrets       verify only
SUP-001  yes      FAIL               gate-supply-chain  deploy
…
IAC-001  no       SKIPPED (terraform) —                 not applicable
DOC-001  yes      FAIL               lint-md            dispatch elsewhere
```

Then, below it, three things the table cannot hold:

**What will be written**, by file rather than by control — the union of every
selected gate's `ARTIFACTS`. A reader wants to know which files in their
repository are about to change, and the per-control view does not answer that.

**What needs a human**, gathered from the gates rather than guessed:
Dependabot or Renovate enabled on the repository, GitHub secret-scanning push
protection, and `administration: write` for the branch ruleset. These are
platform acts (`docs/08-adopting.md` § 1), and a plan that omits them promises
an outcome it cannot reach.

**What will not be verified today.** `kind: remote` blocks report
`SKIPPED (no credentials)` until Phase 3, so SEC-001's push protection and
CI-001's ruleset are deployed and unverified. Say it here, before deployment,
rather than explaining an exit `3` afterwards.

---

## Step 3 — Confirm, once

One **AskUserQuestion** covering the whole plan. Options: **Deploy all** /
**Choose gates** / **Cancel**.

On **Choose gates**, ask a second, multi-select question listing the gates the
plan selected. A partial adoption is a legitimate answer — and say what it
costs: the controls left out keep failing, and `standard-check` will exit
non-zero until they are deployed or the register says they do not apply.

**This confirmation does not cover `gate-repo`.** That gate calls the GitHub API
and its ruleset is in force the moment the call returns, for everyone with
access. It confirms again on its own, and it is right to — this plan covers what
will be written to files, and that call is not a file. Do not describe its
second confirmation as redundant, and never pass a flag that suppresses it.

---

## Step 4 — Dispatch

Invoke each selected gate in this order, and the order is not alphabetical:

| # | Gate | Why here |
| --- | --- | --- |
| 1 | `gate-build` | Owns `.devcontainer/` and creates `setup.sh`, which two later gates write their own regions into |
| 2 | `gate-supply-chain` | Writes the frozen install that every other gate's CI steps run after — a lint step before it lints against nothing |
| 3 | `gate-secrets` | Writes into `setup.sh` and the gating workflow, both of which now exist |
| 4 | `gate-quality` | Same two files, plus the editor locus |
| 5 | `gate-iac` | Independent; last of the file-writing gates |
| 6 | `gate-repo` | Last, because it is the only one whose effect is not a file and cannot be reviewed before it takes effect |

Pass `--repo` and `--register` through to each. **Do not batch them**: run one,
read its output, and stop the sequence if it reports a failed deployment. A gate
that failed and a gate that ran after it are two problems reported as one.

If a gate stops and asks something — which package manager governs, whether to
adopt a hand-wired artefact, whether to remove a predecessor tool — that is the
gate doing its job. Answer it, or pass it to the user. Do not re-invoke the gate
with a flag that skips the question.

---

## Step 5 — Verify

```bash
standard-check --repo "$REPO" --register "$REGISTER" run
```

Over the **whole register**, not only the controls just deployed. A gate that
wired its own control and broke another's CI step is exactly what a per-gate
verify cannot see, and it is the reason this step exists at the adoption level
as well as inside each gate.

Report the verdict as given:

| Exit | Meaning | What to say |
| --- | --- | --- |
| `0` | Every applicable control verified and clean | Adoption succeeded and is fully verified |
| `1` | A verified violation | Adoption **failed** — show every failing block verbatim |
| `2` | Usage error, or the target is not a repository | Fix the invocation; nothing was verified |
| `3` | No violation, but something could not be verified | Adoption succeeded **at the local loci** — name every block that was skipped and why |

**Exit `3` is the expected result today** and is not a pass. SEC-001's and
CI-001's remote blocks report `SKIPPED (no credentials)` until Phase 3. Say which
blocks, and say that the platform acts from Step 2 are still owed.

Then show the difference from the starting run recorded in Step 1: which
controls changed verdict, and which did not. A control that was failing and still
is has not been adopted, whatever was written for it.

**Never report `3` as a clean pass, and never re-run with a flag that hides it.**

---

## Step 6 — Commit

Only after Step 5, and only if it did not exit `1` or `2`.

One commit, conventional format, listing the control IDs deployed:

```text
chore(standard): adopt SEC-001, SUP-001, SUP-002, SUP-003, LNT-001, …

Deployed by standard-adopt against register v<version> (contract <n>).
Verified: standard-check → exit 3 (remote blocks skipped, Phase 3).
Still owed, and not this commit's: <the platform acts from Step 2>.
```

Show the diff before committing. This is the last moment anyone sees what
changed as one change rather than as a repository they have to re-read.

Do not push, and do not open a pull request unless asked. Deployment produces a
reviewable change and a human decides where it goes.

---

## Output

**Adopted:**

```text
standard-adopt deployed <n> controls in <repo>.
  gate-build         BLD-001, DEV-001
  gate-supply-chain  SUP-001, SUP-002, SUP-003
  gate-secrets       SEC-001, SEC-002
  gate-quality       LNT-001, TYP-001, TST-001
  gate-repo          CI-001
  not applicable     IAC-001 (no *.tf)
  dispatch elsewhere DOC-001 (lint-md)
Verified: standard-check → exit 3
  local loci PASS; SEC-001 and CI-001 remote SKIPPED (no credentials), Phase 3.
Still owed by a human: <platform acts>.
Committed: <sha> — not pushed.
```

**Failed:**

```text
standard-adopt stopped at <gate>: <the failing block, verbatim>.
<n> gates ran before it and their changes are in the working tree, uncommitted.
Nothing has been committed and nothing has been pushed.
```

**Cancelled:**

```text
standard-adopt showed the plan and wrote nothing.
```

## Error handling

| Condition | Action |
| ----------- | -------- |
| No register found or it fails to load | Stop. There is nothing to plan from |
| Not a git repository | Stop. Every assert reads what git tracks |
| A control's `deployed_by` names a gate this plugin does not have | Plan it as **dispatch elsewhere** or **manual**. Never drop it from the plan |
| A gate reports a failed deployment | Stop the sequence. Do not run the gates after it |
| A gate asks a question | Answer it or pass it on. Do not re-invoke with the question suppressed |
| Verify exits `1` | Report a failed adoption and **do not commit** |
| Verify exits `3` | Report success at the local loci, naming every skipped block |
| A stamp names a contract ahead of the register | A defect, not staleness. Report it and stop |

## Idempotency

Re-running is safe and is how a stale deployment is refreshed: every gate reads
what is already wired and replaces only its own regions. The plan will show
`verify only` for controls already passing, and those gates can be deselected in
Step 3 — but running them changes nothing except a stamp's contract number,
which is the point of re-running after a register bump.

## Standards

- Human-readable overview, and why the dispatch order is what it is:
  `${CLAUDE_SKILL_DIR}/README.md`
- What an adopter must do that no skill can: `docs/08-adopting.md`
