---
name: gate-iac
description: >
  Deploy IAC-001: run the register's infrastructure analysers over all
  Terraform at pre-commit and in CI, where their exit codes block the merge.
  Triggers: 'deploy gate-iac', 'wire terraform analysis', '/gate-iac'.
argument-hint: "[--repo <path>] [--register <path>]"
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
---

# /gate-iac — deploy the infrastructure analysis gate

You are running the **gate-iac** skill. It deploys IAC-001 (*infrastructure code
is statically analysed before apply*) in a target repository, then verifies its
own work with the same checker that audits it.

**Two rules govern everything below.**

**The register decides, this skill writes.** Which analysers run, with which
arguments, and how a locus reaches the checker all come from `controls.yaml`.
Nothing here hard-codes a tool or a version. If a value you need is not in the
register, stop and say so — inventing one puts a second copy of a rule in a
skill, which is the drift this standard exists to prevent.

**Enforcement is never Claude.** What ships is a pinned checker invoked by a
pre-commit hook and a CI step, running the analysers the register names. This
skill wires them and then has no further part in enforcement.

**Do not use when:**

- The repository has no `controls.yaml` and you have no register path to point
  at. Deploy the register first; there is nothing to derive the analysers from.
- The repository has no `*.tf` file. IAC-001 skips on its predicate — and the
  predicate is evaluated against files, never self-declared, so there is nothing
  to deploy and nothing to force. Say so.
- You want every gate, not this one. Use `register-adopt`, which plans across
  the whole register and dispatches here.

## Inputs

| Input | Required | Default | Description |
| ------- | ---------- | --------- | ------------- |
| `--repo <path>` | No | current directory | The repository to deploy into |
| `--register <path>` | No | `<repo>/controls.yaml` | The register to read the analysers from |

Both flags mirror `register-check`'s own, so a deployment and its audit can
never be pointed at different things by accident.

## Success criteria

1. Every value written came from the register; none was chosen here.
2. Both loci IAC-001 declares are wired — pre-commit and ci.
3. Each artefact written carries a provenance stamp naming IAC-001, this skill
   and version, and the register's version and contract.
4. `register-check run --control IAC-001` was run afterwards, its output shown,
   and its verdict reported as given — including a failure or an
   `UNCLASSIFIED`.
5. Nothing was written outside the target repository.

---

## Pre-flight — read the register, then read the repository

Nothing is written in this phase. Any file this skill writes that is found
zero-byte or truncated — from an interrupted prior run — is treated as absent.

### 1. Resolve and read the register

```bash
register-check --repo "$REPO" --register "$REGISTER" explain IAC-001
```

If this fails, stop and show the error. A register that does not load cannot be
the authority for anything, and every step below reads it.

| State var | From |
| --- | --- |
| `ANALYSERS` | IAC-001's `kind: command` blocks — each `run:` string, verbatim |
| `TOOL` | IAC-001's `gate_wired_at_declared_loci` block, `args.tool` |
| `TOOL_INVOCATION` | `tools.<TOOL>.invocation` — how a locus reaches the checker |
| `SUPPRESSION` | `suppression:` — the idioms nothing this gate writes may contain |
| `REGISTER_VERSION` | top-level `version` |
| `REGISTER_CONTRACT` | `meta.register_contract` |

**`ANALYSERS` is read, not run, and not rewritten.** The arguments in each
`run:` string are the register's — `--compact --quiet`, `--recursive`. A repo
that needs different ones changes the register, because a control whose
arguments a skill chooses is a control nobody can review.

**If `tools.<TOOL>` has no `invocation`**, stop. The pre-commit gate would have
to run a bare tool name, which resolves from `PATH` — and what answered would be
auditing the repository (ADR 0020). That is a defect in the register to fix
there.

### 2. Read the repository's current state

| State var | Command |
| --- | --- |
| `TF_FILES` | every tracked `*.tf` and `*.tfvars` |
| `ANALYSER_STATE` | for each entry in `ANALYSERS`, whether its tool is installed and at what version |
| `PINNED_STATE` | whether `tools:` pins each analyser, and at which loci |
| `WORKFLOWS` | `ls .github/workflows/ 2>/dev/null \|\| echo NONE` |
| `PRECOMMIT_STATE` | `test -f .pre-commit-config.yaml && echo EXISTS \|\| echo ABSENT` |
| `HOOK_STATE` | whether a hook's `entry` runs `TOOL_INVOCATION` for IAC-001 |
| `AUDIT_STATE` | whether a gating step already runs `TOOL_INVOCATION` with no `--control` |
| `LEGACY_STATE` | an existing `terraform validate`, `tfsec` or `terrascan` step the register does not name |

For each workflow found, establish whether it **gates**: a workflow is the ci
locus only if it runs on `push` or `pull_request`. Record the gating workflows
and their job ids.

**If `TF_FILES` is empty**, stop and say so. The predicate is not satisfied,
IAC-001 skips, and deploying a gate for infrastructure the repository does not
have is a hook that can only ever be noise.

### 3. Report the plan before writing

Show a table of what will be written, to which file, and what already exists
there. If any artefact exists and this skill did not write it — no `ee-control:`
stamp naming `gate-iac` — ask via **AskUserQuestion** whether to take it over.
Options: Adopt and stamp / Leave and abort.

**Report `ANALYSER_STATE` and `PINNED_STATE` here, before writing anything.**
This is the state most likely to make the deployment report something other than
a pass, and saying it up front is cheaper than explaining it afterwards.

---

## Step 1 — Make sure the analysers are pinned, or say they are not

IAC-001's blocks name two analysers and the register may pin neither. An absent
analyser is `UNCLASSIFIED — cannot verify`, not a pass
([ADR 0016](../../../../docs/adr/0016-exit-codes-for-unverifiable-controls.md)),
and that is the honest verdict for a control whose tool is not installed.

- **`PINNED_STATE` shows a `tools:` entry for each analyser:** install each at
  the version the register names, verifying the checksum before running
  anything from it, and add the install's file to that tool's `pinned_at` if it
  is not already listed.
- **`PINNED_STATE` shows no entry:** **do not install anything.** Say plainly
  that the register mandates an analyser it does not pin, that the control will
  report `UNCLASSIFIED` until it does, and what closes it — a `tools.checkov`
  and `tools.tflint` entry in *this repository's* register, naming the loci it
  installs them at (`docs/08-adopting.md` § 3.5).

Installing an unpinned tool is the tempting move and the wrong one: it makes the
report green while leaving the version unrecorded, which is precisely the
condition `tool_versions_match_register` exists to fail.

---

## Step 2 — Wire both loci

IAC-001 declares `locus: [pre-commit, ci]`, and until register contract 16
neither was verified. The blocks that were there run the analysers over the
files, which is a different claim from *something enforces this before a commit
lands and before a merge does*.

**One hook for two analysers.** The hook runs the control and the control runs
both, so there is no second wiring for either and the two can never disagree
about what "analysed" means.

**The pre-commit locus.** Read
`${CLAUDE_SKILL_DIR}/templates/precommit-hook.yaml` and substitute `{{TOOL}}`,
`{{TOOL_INVOCATION}}`, `{{SKILL_VERSION}}`, `{{REGISTER_VERSION}}` and
`{{REGISTER_CONTRACT}}`.

- **`PRECOMMIT_STATE` is `ABSENT`:** create `.pre-commit-config.yaml` with a
  single `repos: - repo: local` entry holding the block.
- **`PRECOMMIT_STATE` is `EXISTS`, `HOOK_STATE` is `ABSENT`:** append the block
  to the existing `repo: local` hooks list, preserving every other hook.
- **`HOOK_STATE` is wired:** replace only this hook's own lines and its stamp.

**The ci locus.** If `AUDIT_STATE` shows a gating step already running the
checker with no `--control`, that step audits every applicable control and
reaches this one. Write no second step; stamp the one that is there and **say
that you did not add one**. Otherwise read
`${CLAUDE_SKILL_DIR}/templates/ci-steps.yaml`, substitute the same values, and
add its step to a job that runs on `push` or `pull_request`.

**Nothing this gate writes may carry a suppression.** No `continue-on-error`,
and no idiom from `SUPPRESSION` after the invocation. IAC-001 is
`narrowing-only` with `baseline: null`: a step that reports findings without
blocking is a gate that is not a gate, and there is no tolerated list to record
its findings in.

**Running the checker is not the same as auditing with it.** A hook or step
invoking `register-check schema`, `meta`, `assert` or `explain` reaches no
control at all, and the verify step below will not credit it.

---

## Step 3 — Migrate what this replaces

- **`LEGACY_STATE` shows a `terraform validate` step:** leave it. It checks
  syntax and provider schema, which neither analyser does; it is not a
  predecessor, it is a different check.
- **`LEGACY_STATE` shows `tfsec` or `terrascan`:** these overlap with `checkov`
  and the register does not name them. Show what each is configured to do, and
  ask via **AskUserQuestion** whether to remove it. Options: Remove / Keep. A
  second analyser is not a violation — but two analysers with two suppression
  files is two places a finding can be hidden, and only one of them is a place
  this standard checks (ADR 0019).
- **An analyser suppression file** — `.checkov.yaml` skips, `.tflint.hcl`
  disabled rules — is judged by what it hides. An entry that suppresses a
  finding in a file **git tracks** weakens a `narrowing-only` control with
  `baseline: null`; one naming nothing tracked scopes the tool. List what is
  going, what is staying, and why each.

---

## Step 4 — Verify, through the checker and not otherwise

```bash
register-check --repo "$REPO" --register "$REGISTER" run --control IAC-001
```

This is the only verification step. It runs the control's own verify blocks
through the same code path that audits the repository, so this gate cannot pass
itself where the auditor would fail it. **Do not** re-implement any of these
checks here, and do not read the files back yourself to decide whether the
deployment worked — a second opinion computed a second way is exactly the
disagreement that surfaces at the worst moment.

Report the verdict as given:

| Exit | Meaning | What to say |
| --- | --- | --- |
| `0` | Verified and clean | Deployment succeeded |
| `1` | A verified violation | Either the wiring is wrong or the Terraform has findings — show the failing block verbatim |
| `2` | Usage error, or the target is not a repository | Fix the invocation; nothing was verified |
| `3` | No violation, but something could not be verified | Say which block was skipped and why |

**Exit `1` here has two very different causes and they must not be conflated.**
A failing `gate_wired_at_declared_loci` or `provenance_stamp_present` block is a
failed deployment. A failing `checkov` or `tflint` block is a **successful**
deployment finding real problems in the repository's infrastructure — the gate
working on its first run. Say which, quote the block, and do not describe the
second as a deployment failure.

**`UNCLASSIFIED` is not a pass.** An absent analyser means the control could not
be verified; report it as unverified and repeat what closes it.

---

## Output

**Deployed:**

```text
gate-iac deployed IAC-001 in <repo>.
  pre-commit  .pre-commit-config.yaml — hook '<tool>-iac' (stamped)
  ci          reached by the existing full audit — no step added
  analysers   <checkov, tflint> — <pinned and installed | not pinned, see below>
Verified: register-check run --control IAC-001 → exit 0
```

**Findings rather than a failure:**

```text
gate-iac deployed IAC-001, and the gate is doing its job on the first run.
<the failing analyser block, verbatim>
The wiring verified; these are findings in the repository's Terraform.
```

**Failed verification:**

```text
gate-iac wrote its artefacts, and register-check does not accept them.
<the failing block, verbatim>
This is a failed deployment, not a partial one. Nothing has been committed.
```

**Aborted:**

```text
gate-iac stopped at <phase>: <reason>. Nothing was written.
```

## Error handling

| Condition | Action |
| ----------- | -------- |
| No register found or it fails to load | Stop. Emit **Aborted**; there is nothing to derive the analysers from |
| No `*.tf` in the repository | Stop. The predicate is not satisfied and a gate for absent infrastructure can only be noise |
| `tools.<TOOL>` has no `invocation` | Stop. The pre-commit gate would resolve from `PATH`, and what answered would be auditing the repository |
| The register names an analyser it does not pin | Do **not** install it. Report `UNCLASSIFIED` as the expected verdict and say what closes it |
| Checksum mismatch on a pinned analyser | Stop. Do not run the binary or write any artefact |
| Verify exits `1` on an analyser block | Report a **successful** deployment with findings, not a failed one |
| Verify exits `1` on a wiring or stamp block | Report a failed deployment. Do not retry with a narrower check |

## Idempotency

Re-running is safe. Pre-flight reads what is already wired, Step 1 installs only
what the register pins, and Step 2 replaces only this gate's own hook and stamp.
A re-run after a register bump rewrites the stamp with the new contract, which
is what makes a stale deployment visible rather than permanent.

This skill never commits. Deployment produces a reviewable change and a human
decides whether it lands (`docs/00-concepts.md` § Notify, never redeploy).

## Standards

- Human-readable overview, and why one hook runs two analysers:
  `${CLAUDE_SKILL_DIR}/README.md`
- The artefacts it writes:
  `${CLAUDE_SKILL_DIR}/templates/precommit-hook.yaml` and
  `${CLAUDE_SKILL_DIR}/templates/ci-steps.yaml`
