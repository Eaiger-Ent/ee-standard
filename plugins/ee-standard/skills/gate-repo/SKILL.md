---
name: gate-repo
description: >
  Deploy CI-001: record the default-branch ruleset the register requires, then
  apply it through the GitHub API after an explicit confirmation.
  Triggers: 'deploy gate-repo', 'protect the default branch', '/gate-repo'.
argument-hint: "[--repo <path>] [--register <path>]"
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
---

# /gate-repo — deploy the default-branch protection gate

You are running the **gate-repo** skill. It deploys CI-001 (*the default branch
cannot be written to without a passing check*) in a target repository.

**This is the only gate that changes something outside the repository.** Every
other gate writes files a human reviews before they take effect. This one calls
the GitHub API, and the ruleset it creates is in force the moment the call
returns — for everyone with access, not only for whoever ran the skill. So it
confirms explicitly before acting, **regardless of any plan already approved**,
including a plan approved in `standard-adopt`.

**Two rules govern everything below.**

**The register decides, this skill writes.** Which requirements a protected
branch must carry come from CI-001's `args:` in `controls.yaml`. Nothing here
decides that a pull request is required or that force-push is forbidden. If a
value you need is not in the register, stop and say so.

**Enforcement is never Claude.** What ships is platform state: a ruleset GitHub
evaluates on every push. This skill creates it and then has no further part in
enforcement.

**Do not use when:**

- The repository has no `controls.yaml` and you have no register path to point
  at. Deploy the register first.
- You have no push access, or no token with `administration: write` on the
  repository. Say so — this is a permission a human with admin grants, not
  something to work around (`docs/08-adopting.md` § 1).
- You want every gate, not this one. Use `standard-adopt`, which plans across
  the whole register and dispatches here — and which does **not** waive this
  gate's own confirmation.

## Inputs

| Input | Required | Default | Description |
| ------- | ---------- | --------- | ------------- |
| `--repo <path>` | No | current directory | The repository to deploy into |
| `--register <path>` | No | `<repo>/controls.yaml` | The register to read requirements from |

Both flags mirror `standard-check`'s own, so a deployment and its audit can
never be pointed at different things by accident.

## Success criteria

1. Every requirement written came from the register; none was chosen here.
2. Every rule carries the `parameters` GitHub's schema requires for its type,
   and every name in `REQUIRED_CHECKS` is a job in a gating workflow that does
   not suppress its own failure.
3. The recorded ruleset carries a provenance stamp naming CI-001, this skill and
   version, and the register's version and contract.
4. The API call was made only after an explicit confirmation of its blast
   radius, and its response was shown.
5. `standard-check run --control CI-001` was run afterwards, its output shown,
   and its verdict reported as given — **including the remote block's
   `SKIPPED (no credentials)`**, which is never reported as a pass.
6. Nothing was written outside the target repository except the ruleset itself.

---

## Pre-flight — read the register, then read the platform

Nothing is written and nothing is called in this phase.

### 1. Resolve and read the register

```bash
standard-check --repo "$REPO" --register "$REGISTER" explain CI-001
```

If this fails, stop and show the error.

| State var | From |
| --- | --- |
| `RULESET_PATH` | CI-001's `ruleset_recorded_matches_register` block, `args.path` |
| `REQUIREMENTS` | the same block's remaining `args:` — each requirement and its value |
| `REQUIRED_CHECKS` | the same block's `args.required_checks` — the status checks a merge must wait for |
| `STRICT_CHECKS` | the same block's `args.require_branches_up_to_date` |
| `REGISTER_VERSION` | top-level `version` |
| `REGISTER_CONTRACT` | `meta.register_contract` |

`REQUIREMENTS` and the `kind: remote` block's `args:` are the **same** values,
and that is deliberate: two blocks would be two definitions of "protected", free
to drift. Read them once.

**`REQUIRED_CHECKS` is a list of job ids, and an empty one is not a deployment.**
A `required_status_checks` rule naming no context requires no check, so a pull
request merges with CI red while the control reports satisfied. If the register
names none, stop: the register is what needs fixing, not this file. Register
contract 19 added the field for exactly this, after the rule shipped without it.

### 2. Read the platform's current state

```bash
gh api "repos/$OWNER/$NAME" --jq '.default_branch'
gh api "repos/$OWNER/$NAME/rulesets" --jq '.[] | {id, name, target, enforcement}'
gh api "repos/$OWNER/$NAME/branches/$DEFAULT/protection" 2>/dev/null
```

| State var | From |
| --- | --- |
| `DEFAULT_BRANCH` | the repository's default branch |
| `RULESETS` | every existing ruleset, with its id, name and enforcement |
| `CONTEXTS` | the job ids of every workflow that runs on `push` or `pull_request`, and whether each carries `continue-on-error` |
| `LEGACY_PROTECTION` | a classic branch-protection rule, if one exists |
| `RECORDED` | `RULESET_PATH` in the repository, if it exists, and whether this skill wrote it |
| `TOKEN_SCOPE` | whether the token can write rulesets |

**If `TOKEN_SCOPE` shows no `administration: write`,** stop before writing
anything. Say which permission is missing and who grants it. A skill that writes
the record and cannot apply it leaves a repository looking protected in a diff
and unprotected in fact — the exact half-state this gate must not create.

### 3. Report the plan, and what it will change for everyone

Show a table of what will be recorded and what will be called. Then state the
blast radius plainly, in these terms:

- Which branch stops accepting direct pushes, and from whom — **everyone**,
  including administrators, unless a bypass is configured.
- Whether any open pull request will now require a check that has never run.
- What happens to `LEGACY_PROTECTION` if one exists.

---

## Step 1 — Record the ruleset

Read `${CLAUDE_SKILL_DIR}/templates/default-branch.json` and substitute
`{{RULESET_NAME}}`, `{{REQUIRED_CHECKS}}`, `{{REQUIRE_BRANCHES_UP_TO_DATE}}`,
`{{SKILL_VERSION}}`, `{{REGISTER_VERSION}}` and `{{REGISTER_CONTRACT}}`. Write it
to `RULESET_PATH` and **git-add it**; a ruleset git does not carry is not one
anybody can review.

`{{REQUIRED_CHECKS}}` becomes one `{ "context": "<job id>" }` object per entry
in `REQUIRED_CHECKS`, comma-separated. Before writing them, check each against
`CONTEXTS`:

- **A name no gating job produces.** GitHub waits forever for a check nothing
  reports, so the ruleset blocks every merge rather than gating one. Stop, show
  `CONTEXTS`, and say which name has no job — the register and the workflows
  disagree, and only a human knows which of the two is right.
- **A name whose job carries `continue-on-error`.** It reports success whatever
  happens, so requiring it requires nothing. Stop and say so.

Do not quietly drop either kind. A ruleset that was accepted because it required
less is a control silently downgraded.

The file is JSONC, as `.devcontainer/devcontainer.json` is, and for the same
reason: the stamp is a `//` comment and a file that cannot carry one cannot
carry its own provenance. Step 2 strips those lines before the API call.

**If `RECORDED` shows a ruleset already on the platform that this skill did not
write**, transcribe what `GET /rulesets/<id>` returns rather than what a
deployment would have produced, and say in the stamp's comment that it was
adopted. A record that disagrees with what is enforced is worse than one that
carries more than the register asks for.

Render each entry in `REQUIREMENTS` into GitHub's own spelling. One mapping
needs stating rather than inferring: `allow_force_push: false` becomes the
`non_fast_forward` rule, because the register says what is *allowed* and GitHub
names what is *blocked*. Reading one as the other is how a control ends up
inverted.

**Every rule carries the `parameters` its type requires, and no others.**
GitHub's REST schema requires a `parameters` object on `pull_request` and
`required_status_checks`, and accepts none on `non_fast_forward` or `deletion`.
The template already has this right; the point of saying it here is that a rule
added by hand needs the same treatment. Until register contract 19 this skill
wrote bare `{ "type": ... }` objects for all four, and the apply call in Step 2
returned 422 every time — a gate that could not deploy the one control it
exists for, with nothing to show for the failure but an error nobody had seen.

Target `~DEFAULT_BRANCH`, never a branch name. A ruleset naming `main` stops
protecting the default branch the day the default moves, silently.

**`enforcement` is `active`.** GitHub also accepts `evaluate`, which reports
what would have happened and blocks nothing. That is a control declared and
unreachable, and the checker rejects it.

---

## Step 2 — Confirm, then apply

**Ask via AskUserQuestion before the API call, every time.** Not "shall I
proceed with the plan" — name the change:

> This creates an active ruleset on `<owner>/<name>`. From the moment it
> returns, `<default branch>` cannot be pushed to directly by anyone, every
> merge requires a pull request with a passing check, and history cannot be
> rewritten. It affects every collaborator, not only you. Apply it?

Options: **Apply now** / **Record only, do not apply**.

This confirmation is not waivable by an earlier approval. `standard-adopt`'s
plan step covers what will be written to files; this call is not a file.

**On Apply now:**

```bash
# The record is JSONC so that it can carry its own stamp; GitHub's API takes
# strict JSON, so the comment lines come out on the way. A filter on a payload,
# not a second copy of the ruleset — every value still comes from the file.
grep -v '^[[:space:]]*//' "$RULESET_PATH" |
  gh api --method POST "repos/$OWNER/$NAME/rulesets" --input -
```

Show the response. If it fails, show the error verbatim and **do not retry with
a weaker ruleset** — a ruleset that was accepted because it required less is a
control silently downgraded, and CI-001 is `variance: forbidden` with
`baseline: null`.

**On Record only:** say plainly that the file is written, that nothing on the
platform has changed, and that CI-001 is **not** deployed. A recorded ruleset
protects nothing.

**If a ruleset with this name already exists**, use `PUT
repos/$OWNER/$NAME/rulesets/$ID` rather than creating a second. Two rulesets
targeting one branch is two places a requirement can be removed from, and only
one of them is the one anybody looks at.

---

## Step 3 — Migrate what this replaces

**If `LEGACY_PROTECTION` exists:** a classic branch-protection rule and a
ruleset both apply, and the *union* of their requirements is enforced — so
leaving the old one is safe but confusing, and removing it is a real reduction
in what protects the branch until the ruleset is confirmed active.

Show what the classic rule requires, show what the ruleset requires, and ask via
**AskUserQuestion** whether to remove the classic rule. Options: Remove / Keep.
Do not remove it in the same breath as creating the ruleset: confirm the ruleset
is active first, then ask.

---

## Step 4 — Verify, through the checker and not otherwise

```bash
standard-check --repo "$REPO" --register "$REGISTER" run --control CI-001
```

This is the only verification step. **Do not** call the API again and read the
ruleset back yourself to decide whether the deployment worked — a second opinion
computed a second way is exactly the disagreement that surfaces at the worst
moment.

Report the verdict as given:

| Exit | Meaning | What to say |
| --- | --- | --- |
| `0` | Verified and clean | Not reachable today — see below |
| `1` | A verified violation | The recorded ruleset does not match the register — show the block verbatim |
| `2` | Usage error, or the target is not a repository | Fix the invocation; nothing was verified |
| `3` | No violation, but something could not be verified | The expected result — say which block was skipped and why |

**Exit `3` is the expected result, and saying so precisely matters.** CI-001's
`remote` block reports `SKIPPED (no credentials)` until Phase 3 implements
`kind: remote`. What is verified is that the repository **records** the ruleset
the register requires. What is not verified — by anything, yet — is that GitHub
is enforcing it.

Say both. The API call's response is evidence that it was applied; it is not
evidence that it is still applied tomorrow, and it is not this checker's verdict.
Never report `3` as a clean pass, and never re-run with a flag that hides it.

---

## Output

**Deployed:**

```text
gate-repo deployed CI-001 in <owner>/<name>.
  recorded  .github/rulesets/default-branch.json (stamped)
  applied   POST /repos/<owner>/<name>/rulesets → 201, ruleset id <id>
            ~DEFAULT_BRANCH: pull request required, checks required,
            force-push forbidden, enforcement active
Verified: standard-check run --control CI-001 → exit 3
  the recorded ruleset matches the register; whether GitHub enforces it is
  SKIPPED (no credentials) until Phase 3, and is not claimed here.
```

**Recorded only:**

```text
gate-repo recorded CI-001's ruleset and did not apply it.
Nothing on the platform has changed. The default branch is unprotected.
CI-001 is not deployed.
```

**Aborted:**

```text
gate-repo stopped at <phase>: <reason>. Nothing was written and nothing
was called.
```

## Error handling

| Condition | Action |
| ----------- | -------- |
| No register found or it fails to load | Stop. Emit **Aborted** |
| No `administration: write` on the token | Stop **before writing the record**. Say which permission is missing and who grants it |
| The user chooses **Record only** | Write the file, report CI-001 as not deployed, and do not soften that |
| The API call fails | Show the error verbatim. Do not retry with a weaker ruleset |
| A ruleset of this name already exists | `PUT` it rather than creating a second |
| Verify exits `1` | The record disagrees with the register. Report a failed deployment |
| Verify exits `3` | The expected result. Report what is verified and what is not |

## Idempotency

Re-running is safe and is the intended way to reconcile drift: Step 1 rewrites
the record from the register, and Step 2 updates an existing ruleset rather than
creating a second. The confirmation is asked **every time**, including on a
re-run that would change nothing — a call whose effect is invisible until it is
wrong is not one to make silently.

This skill never commits the recorded file. Deployment produces a reviewable
change and a human decides whether it lands (`docs/00-concepts.md` § Notify,
never redeploy). The API call is the exception, and is why Step 2 exists.

## Standards

- Human-readable overview, and why a recorded ruleset is not a protected branch:
  `${CLAUDE_SKILL_DIR}/README.md`
- The artefact it writes:
  `${CLAUDE_SKILL_DIR}/templates/default-branch.json`
