---
name: gate-secrets
description: >
  Deploy SEC-001 and SEC-002: wire the register's secret scanner at
  pre-commit and CI, stamp what it writes, verify through standard-check.
  Triggers: 'deploy gate-secrets', 'wire secret scanning', '/gate-secrets'.
argument-hint: "[--repo <path>] [--register <path>]"
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
---

# /gate-secrets — deploy the secrets gate

You are running the **gate-secrets** skill. It deploys SEC-001 (*a commit
containing a secret cannot reach the remote*) and checks SEC-002 (*CI
authenticates without a long-lived cloud credential*) in a target repository,
then verifies its own work with the same checker that audits it.

**Two rules govern everything below.**

**The register decides, this skill writes.** The scanner's name, its version,
its checksum and the paths that repeat that version all come from
`controls.yaml`. Nothing here hard-codes a tool or a version. If a value you
need is not in the register, stop and say so — inventing one puts a second copy
of a rule in a skill, which is the drift this standard exists to prevent.

**Enforcement is never Claude.** What ships is a pinned binary invoked by a
pre-commit hook and a CI step. This skill installs and wires it, and then has no
further part in enforcement.

**Do not use when:**

- The repository has no `controls.yaml` and you have no register path to point
  at. Deploy the register first; there is nothing to derive the pins from.
- You want to run the scanner once. Call it directly.
- You want every gate, not this one. Use `standard-adopt`, which plans across
  the whole register and dispatches here.

## Inputs

| Input | Required | Default | Description |
| ------- | ---------- | --------- | ------------- |
| `--repo <path>` | No | current directory | The repository to deploy into |
| `--register <path>` | No | `<repo>/controls.yaml` | The register to read pins from |

Both flags mirror `standard-check`'s own, so a deployment and its audit can
never be pointed at different things by accident.

## Success criteria

1. Every value written came from the register; none was chosen here.
2. Both of SEC-001's local loci — pre-commit and ci — run the scanner.
3. Each artefact written carries a provenance stamp naming SEC-001, this skill
   and version, and the register's version and contract.
4. `standard-check run --control SEC-001 --control SEC-002` was run afterwards,
   its output shown, and its verdict reported as given — including a failure.
5. Nothing was written outside the target repository.

---

## Pre-flight — read the register, then read the repository

Nothing is written in this phase. Any file this skill writes that is found
zero-byte or truncated — from an interrupted prior run — is treated as absent.

### 1. Resolve and read the register

```bash
standard-check --repo "$REPO" --register "$REGISTER" explain SEC-001
```

If this fails, stop and show the error. A register that does not load cannot be
the authority for anything, and every step below reads it.

Extract and store, from the register's `tools:` table for the scanner SEC-001's
verify block names in `args.tool`:

| State var | From |
| --- | --- |
| `TOOL` | SEC-001's `secrets_gate_wired_at_all_loci` block, `args.tool` |
| `IGNORE_FILE` | the same block, `args.ignore_file` |
| `TOOL_VERSION` | `tools.<TOOL>.version` |
| `TOOL_SHA256` | `tools.<TOOL>.sha256` |
| `TOOL_REPO` | `tools.<TOOL>.release_repo` — `owner/name`, where the release is fetched from |
| `PINNED_AT` | `tools.<TOOL>.pinned_at` — the paths that must repeat the version |
| `REGISTER_VERSION` | top-level `version` |
| `REGISTER_CONTRACT` | `meta.register_contract` |

A `tools:` entry with `source: lockfile` carries an `invocation` instead of a
version: the locus must reach the pinned artefact by that path, not by the bare
tool name (ADR 0020). Use it verbatim wherever `{{TOOL}}` appears as a command
below.

**If `args.tool` names a tool the `tools:` table does not define**, stop. The
register mandates a scanner it does not pin, and that is a defect in the
register to fix there, not to paper over here.

### 2. Read the repository's current state

| State var | Command |
| --- | --- |
| `TOOL_STATE` | `command -v "$TOOL" >/dev/null && echo INSTALLED \|\| echo NEEDS_INSTALL` |
| `PRECOMMIT_STATE` | `test -f .pre-commit-config.yaml && echo EXISTS \|\| echo ABSENT` |
| `HOOK_STATE` | `grep -q "id: $TOOL" .pre-commit-config.yaml 2>/dev/null && echo WIRED \|\| echo ABSENT` |
| `WORKFLOWS` | `ls .github/workflows/ 2>/dev/null \|\| echo NONE` |
| `IGNORE_STATE` | `test -f "$IGNORE_FILE" && echo EXISTS \|\| echo ABSENT` |
| `LEGACY_STATE` | `test -f .git/hooks/pre-commit && ! test -f .pre-commit-config.yaml && echo LEGACY \|\| echo ABSENT` |

For each workflow found, establish whether it **gates**: a workflow is the ci
locus only if it runs on `push` or `pull_request`. Record the gating workflows
and their job ids. If there are none, note it — Step 3 has to create one, and a
repository whose only workflow runs on `workflow_dispatch` has a CI file that
gates nothing.

### 3. Report the plan before writing

Show a table of what will be written, to which file, and what already exists
there. If any artefact exists and this skill did not write it — no `ee-control:`
stamp naming `gate-secrets` — ask via **AskUserQuestion** whether to take it
over. Options: Adopt and stamp / Leave and abort.

Adopting is the honest option, not the polite one: hand-wired artefacts are the
normal starting state, and a stamp that records what was already there is how
`lint-md`'s five artefacts came to be stamped in this repository. Say so in the
stamp's surrounding comment.

---

## Step 1 — Install the scanner at the version the register pins

**If `TOOL_STATE` is `INSTALLED`:** confirm the version matches the register.

```bash
"$TOOL" version 2>/dev/null || "$TOOL" --version
```

If it differs from `TOOL_VERSION`, say so and ask whether to replace it. A
scanner at another version is not the gate the register describes, and the
difference will surface later as a verdict nobody can explain.

**If `TOOL_STATE` is `NEEDS_INSTALL`:** install the pinned release and check the
checksum before running anything from it.

```bash
curl -sSfL -o "$TOOL.tgz" \
  "https://github.com/$TOOL_REPO/releases/download/v$TOOL_VERSION/${TOOL}_${TOOL_VERSION}_linux_x64.tar.gz"
echo "$TOOL_SHA256  $TOOL.tgz" | sha256sum -c -
tar -xzf "$TOOL.tgz" "$TOOL" && sudo install "$TOOL" /usr/local/bin/"$TOOL"
rm -f "$TOOL" "$TOOL.tgz"
```

If `sha256sum -c -` fails, **stop**. A downloaded artefact that does not match
the checksum the register records is the one case where continuing is worse than
failing: an unverified secret scanner is a gate in name only.

---

## Step 2 — Write the pre-commit hook

Read `${CLAUDE_SKILL_DIR}/templates/precommit-hook.yaml` and substitute
`{{TOOL}}`, `{{SKILL_VERSION}}`, `{{REGISTER_VERSION}}` and
`{{REGISTER_CONTRACT}}` from the values stored in pre-flight.

- **`PRECOMMIT_STATE` is `ABSENT`:** create `.pre-commit-config.yaml` with a
  single `repos: - repo: local` entry holding the block.
- **`PRECOMMIT_STATE` is `EXISTS`, `HOOK_STATE` is `ABSENT`:** append the block
  to the existing `repo: local` hooks list, preserving every other hook. Do not
  reformat the file — other controls' hooks live there and a wholesale rewrite
  makes this gate's change unreviewable.
- **`HOOK_STATE` is `WIRED`:** replace only the hook's own lines and its stamp,
  and record in the stamp comment that an existing hook was adopted.

The stamp goes at the hook, never at the top of the file.

---

## Step 3 — Wire the ci locus

Read `${CLAUDE_SKILL_DIR}/templates/ci-steps.yaml` and substitute the same
values plus `{{TOOL_VERSION}}`, `{{TOOL_SHA256}}` and `{{TOOL_REPO}}`.

- **A gating workflow exists:** add the two steps to a job that already runs on
  `push` or `pull_request`, after any checkout step. The checkout must fetch
  full history — `fetch-depth: 0` — because the scanner reads commits, and a
  shallow clone scans a fraction of them while reporting success.
- **Only non-gating workflows exist:** do not add steps to one. Say plainly that
  the repository has CI which cannot gate a merge, and create a new workflow
  that runs on `push` and `pull_request`.
- **No workflows exist:** create `.github/workflows/standard-check.yml` with a
  single job holding the steps.

Then check `PINNED_AT`: the register lists every file that repeats this tool's
version. If the workflow you just wrote is not among them, the register and the
repository now disagree, and `tool_versions_match_register` will say so. Add the
path to `tools.<TOOL>.pinned_at` in the register and tell the user you did — it
is their register recording their files
(`docs/08-adopting.md` § 3.1), so it is an edit to report, not one to hide.

---

## Step 4 — Migrate what this replaces

- **`LEGACY_STATE` is `LEGACY`:** a hand-written `.git/hooks/pre-commit` runs
  only for whoever has that clone and is invisible to review. Show its contents,
  and offer via **AskUserQuestion** to remove it now that the pre-commit
  framework covers the same ground. Options: Remove / Keep.
- **`IGNORE_STATE` is `EXISTS`:** read every entry. An entry that suppresses a
  finding in a file **git tracks** hides authored content from a control whose
  `baseline` is `null` and whose `variance` is `forbidden` — it must go, and
  whatever it hid must be dealt with. An entry naming nothing git tracks scopes
  the scanner rather than weakening it, and stays
  (ADR 0019, *Exemptions cannot hide tracked files*).

Do not delete an entry silently in either direction. List what is going, what is
staying, and why each.

---

## Step 5 — Verify, through the checker and not otherwise

```bash
standard-check --repo "$REPO" --register "$REGISTER" \
  run --control SEC-001 --control SEC-002
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
| `0` | Every selected control verified and clean | Deployment succeeded |
| `1` | A verified violation | Deployment **failed** — show the failing block verbatim |
| `2` | Usage error, or the target is not a repository | Fix the invocation; nothing was verified |
| `3` | No violation, but something could not be verified | Deployment succeeded **at the local loci**; say which block was skipped and why |

Exit `3` is the expected result today, and saying so precisely matters.
SEC-001's `remote` block — GitHub secret scanning push protection — reports
`SKIPPED (no credentials)` until Phase 3 implements `kind: remote`. The two
local loci are verified; the remote one is not, and is not claimed. Enabling
push protection is a platform act a human with admin takes
(`docs/08-adopting.md` § 1).

Never report `3` as a clean pass, and never re-run with a flag that hides it.

---

## Output

**Deployed:**

```text
gate-secrets deployed SEC-001 in <repo>.
  pre-commit  .pre-commit-config.yaml — hook '<tool>' (stamped)
  ci          .github/workflows/<file> — install + secret scan (stamped)
  remote      not deployed — push protection is a platform act (§ 1)
Verified: standard-check run --control SEC-001 --control SEC-002 → exit 3
  local loci PASS; remote SKIPPED (no credentials), Phase 3.
```

**Failed verification:**

```text
gate-secrets wrote its artefacts, and standard-check does not accept them.
<the failing block, verbatim>
This is a failed deployment, not a partial one. Nothing has been committed.
```

**Aborted:**

```text
gate-secrets stopped at <phase>: <reason>. Nothing was written.
```

## Error handling

| Condition | Action |
| ----------- | -------- |
| No register found or it fails to load | Stop. Emit **Aborted**; there is nothing to derive pins from |
| `args.tool` names a tool `tools:` does not pin | Stop. The register mandates a scanner it does not pin — fix it there |
| Checksum mismatch on the downloaded release | Stop. Do not run the binary or write any artefact |
| No gating workflow, and the user declines to create one | Write the pre-commit hook, then report SEC-001 as **not deployed** — one locus of two is a partial deployment and is reported as one |
| Verify exits `1` | Report a failed deployment. Do not retry with a narrower check |
| Verify exits `3` | Report success at the local loci, naming the skipped block |

## Idempotency

Re-running is safe. Pre-flight reads what is already wired, Step 2 replaces only
this gate's own hook and stamp, and Step 3 adds steps only where they are
missing. A re-run after a register bump rewrites the stamps with the new
contract, which is what makes a stale deployment visible rather than permanent.

This skill never commits. Deployment produces a reviewable change and a human
decides whether it lands (`docs/00-concepts.md` § Notify, never redeploy).

## Standards

- Human-readable overview, and why this gate takes no opinions of its own:
  `${CLAUDE_SKILL_DIR}/README.md`
- The artefacts it writes: `${CLAUDE_SKILL_DIR}/templates/precommit-hook.yaml`
  and `${CLAUDE_SKILL_DIR}/templates/ci-steps.yaml`
