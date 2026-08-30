---
name: gate-secrets
description: >
  Wire the register's secret scanner at pre-commit and in CI, stamp what it
  writes, verify through register-check — deploys SEC-001, checks SEC-002
  and SEC-003.
  Triggers: 'deploy gate-secrets', 'wire secret scanning', '/gate-secrets'.
argument-hint: "[--repo <path>] [--register <path>]"
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
---

# /gate-secrets — deploy the secrets gate

You are running the **gate-secrets** skill. It deploys SEC-001 (*a commit
containing a secret cannot reach the remote*) and checks SEC-002 (*CI
authenticates without a long-lived cloud credential*) and SEC-003 (*CI carries
no platform credential the register does not name*) in a target repository,
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
- You want every gate, not this one. Use `register-adopt`, which plans across
  the whole register and dispatches here.

## Inputs

| Input | Required | Default | Description |
| ------- | ---------- | --------- | ------------- |
| `--repo <path>` | No | current directory | The repository to deploy into |
| `--register <path>` | No | `<repo>/controls.yaml` | The register to read pins from |

Both flags mirror `register-check`'s own, so a deployment and its audit can
never be pointed at different things by accident.

## Success criteria

1. Every value written came from the register; none was chosen here.
2. Both of SEC-001's local loci — pre-commit and ci — run the scanner, and
   every site in `PINNED_AT` repeats the version the register names.
3. Every path in `SECRET_PATHS` is ignored by a rule git tracks, and none of
   them is itself tracked.
4. Each artefact written carries a provenance stamp naming SEC-001, this skill
   and version, and the register's version and contract.
5. `register-check run --control SEC-001 --control SEC-002 --control SEC-003`
   was run afterwards,
   its output shown, and its verdict reported as given — including a failure.
6. Nothing was written outside the target repository.

---

## Pre-flight — read the register, then read the repository

Nothing is written in this phase. Any file this skill writes that is found
zero-byte or truncated — from an interrupted prior run — is treated as absent.

### 1. Resolve and read the register

```bash
register-check --repo "$REPO" --register "$REGISTER" explain SEC-001
```

If this fails, stop and show the error. A register that does not load cannot be
the authority for anything, and every step below reads it.

Extract and store, from the register's `tools:` table for the scanner SEC-001's
verify block names in `args.tool`:

| State var | From |
| --- | --- |
| `TOOL` | SEC-001's `secrets_gate_wired_at_all_loci` block, `args.tool` |
| `IGNORE_FILE` | the same block, `args.ignore_file` |
| `SECRET_PATHS` | SEC-001's `secret_files_are_gitignored` block, `args.paths` |
| `TOOL_VERSION` | `tools.<TOOL>.version` |
| `TOOL_SHA256` | `tools.<TOOL>.sha256` |
| `TOOL_REPO` | `tools.<TOOL>.release_repo` — `owner/name`, where the release is fetched from |
| `PINNED_AT` | `tools.<TOOL>.pinned_at` — the paths that must repeat the version |
| `CHECKER` | SEC-002's `gate_wired_at_declared_loci` block, `args.tool` — the checker, not the scanner |
| `CHECKER_INVOCATION` | `tools.<CHECKER>.invocation` — how a locus reaches it; a bare name resolves from `PATH` (ADR 0020) |
| `REGISTER_VERSION` | top-level `version` |
| `REGISTER_CONTRACT` | `meta.register_contract` |
| `SKILL_VERSION` | the plugin's `.claude-plugin/plugin.json`, `version` |
| `GATE_CONTRACT` | the plugin's `.claude-plugin/deploys.json`, `gates.gate-secrets.contractVersion` |

The last two rows are the **plugin's** numbers rather than the register's,
read from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/`. `GATE_CONTRACT` is what a
stamp records as `gate-contract`, and it moves only when what this gate writes
changes, so a documentation release of the plugin recommends nothing
(ADR 0038). If `${CLAUDE_PLUGIN_ROOT}` is unset, stop and say so.

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
| `PREPUSH_STATE` | whether a hook staged `pre-push` runs `CHECKER_INVOCATION` for SEC-002 |
| `AUDIT_STATE` | whether a gating CI step already runs `CHECKER_INVOCATION` with no `--control` |
| `WORKFLOWS` | `ls .github/workflows/ 2>/dev/null \|\| echo NONE` |
| `IGNORE_STATE` | `test -f "$IGNORE_FILE" && echo EXISTS \|\| echo ABSENT` |
| `IGNORED_STATE` | for each `SECRET_PATHS` entry: `git check-ignore --no-index -v -- "$p"` — record the matching rule's **source file**, or `UNIGNORED` |
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

## Before you write a pre-commit hook, make sure something runs it

**Read `${CLAUDE_PLUGIN_ROOT}/reference/pre-commit-runner.md` and do what it
says, before your first write into `.pre-commit-config.yaml`.** A hook in that
file is a statement of intent; the runner and the installed git hook are whether
anything happens, and this gate is one of five writing into it. The steps are
held there rather than here because five copies of a rule is the drift this
standard exists to prevent — see ADR 0036. If `${CLAUDE_PLUGIN_ROOT}` is unset,
the skill was reached as a project skill rather than through the plugin, and the
file is at `plugins/control-register/reference/` in the standard's repository.

## Say what each write is for, before you make it

**Read `${CLAUDE_PLUGIN_ROOT}/reference/write-narration.md` and use the shape it
gives, before your first write.** One line before every file write, and no write
without one: the person approving it sees a diff and nothing else, and this
skill deploys first and verifies last, so nothing has failed or passed yet. The
shape is held there rather than here because seven copies of a rule is the drift
this standard exists to prevent — see ADR 0036. If `${CLAUDE_PLUGIN_ROOT}` is
unset, the skill was reached as a project skill rather than through the plugin,
and the file is at `plugins/control-register/reference/` in the standard's
repository.

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

## Step 2 — Write the local hooks

Read `${CLAUDE_SKILL_DIR}/templates/precommit-hook.yaml` and substitute
`{{TOOL}}`, `{{CHECKER}}`, `{{CHECKER_INVOCATION}}`, `{{SKILL_VERSION}}`,
`{{GATE_CONTRACT}}`, `{{REGISTER_VERSION}}` and `{{REGISTER_CONTRACT}}` from the
values stored in pre-flight. Two blocks: SEC-001's pre-commit hook, and SEC-002's
pre-push hook where the register gives that control a `pre-push` locus. Keep the
second block's `stages:` key — without it the hook runs at every stage the
repository has installed.

- **`PRECOMMIT_STATE` is `ABSENT`:** create `.pre-commit-config.yaml` with a
  single `repos: - repo: local` entry holding the block.
- **`PRECOMMIT_STATE` is `EXISTS`, `HOOK_STATE` is `ABSENT`:** append the block
  to the existing `repo: local` hooks list, preserving every other hook. Do not
  reformat the file — other controls' hooks live there and a wholesale rewrite
  makes this gate's change unreviewable.
- **`HOOK_STATE` is `WIRED`:** replace only the hook's own lines and its stamp,
  and record in the stamp comment that an existing hook was adopted.

One stamp per hook and per control, never one at the top of the file. A stamp
naming SEC-001 must not be credited for SEC-002's artefact.

---

## Step 3 — Wire the ci locus

Read `${CLAUDE_SKILL_DIR}/templates/ci-steps.yaml` and substitute the same
values plus `{{TOOL_VERSION}}`, `{{TOOL_SHA256}}` and `{{TOOL_REPO}}`.

Write the `Credentials` step only if `AUDIT_STATE` shows no gating step already
running the checker with no `--control`: a full audit reaches SEC-002 already, a
second step is the same check twice, and **say that you did not add one**.

- **A gating workflow exists:** add the steps to a job that already runs on
  `push` or `pull_request`, after any checkout step. The checkout must fetch
  full history — `fetch-depth: 0` — because the scanner reads commits, and a
  shallow clone scans a fraction of them while reporting success.
- **Only non-gating workflows exist:** do not add steps to one. Say plainly that
  the repository has CI which cannot gate a merge, and create a new workflow
  that runs on `push` and `pull_request`.
- **No workflows exist:** create `.github/workflows/register-check.yml` with a
  single job holding the steps.

Then check `PINNED_AT`: the register lists every file that repeats this tool's
version. If the workflow you just wrote is not among them, the register and the
repository now disagree, and `tool_versions_match_register` will say so. Add the
path to `tools.<TOOL>.pinned_at` in the register and tell the user you did — it
is their register recording their files
(`docs/08-adopting.md` § 3.3), so it is an edit to report, not one to hide.

---

## Step 3.5 — Wire the developer environment, if there is one

`PINNED_AT` names every file that repeats this tool's version, and in a
repository with a devcontainer one of them is `.devcontainer/setup.sh`. That
file belongs to `gate-build`; the scanner's install block inside it belongs
here, exactly as both gates write their own hooks into one
`.pre-commit-config.yaml`. Shared file, per-region stamps.

This is not a locus of SEC-001's own — the control declares `pre-commit`, `ci`
and `remote`, and a developer environment is none of them. It is where the
pre-commit locus's binary comes from, which is why the register lists it and
`tool_versions_match_register` compares it. Until register contract 15 no gate
claimed it, and a locus with no owner is how a locus gets forgotten.

- **`.devcontainer/setup.sh` exists:** if it already installs `TOOL`, stamp that
  block for SEC-001 and say it was adopted. If it does not, append an install
  block using the same pinned version and checksum Step 1 used, and stamp it.
- **There is no devcontainer:** write nothing, and say so. Creating one to hold
  an install is inventing a DEV-001 artefact this gate does not own.

Do not stamp the whole file. `gate-build` created it and other gates install
into it; a stamp at the top would claim their blocks as SEC-001's.

**Write the `# renovate:` annotation directly above the version, exactly as
`templates/ci-steps.yaml` does for the workflow.** A version literal in a shell
script is the one case no Dependabot manager covers, so without the annotation
this pin is not stale — it is unmanaged, and nothing will ever propose moving
it while SUP-002 stays green over it:

```bash
# renovate: datasource=github-releases depName=<TOOL_REPO>
TOOL_VERSION="<version>"
```

`UPPER_SNAKE_CASE` and the quotes both matter and for different reasons: the
quotes are what `shellcheck` wants, and the case is what the custom manager
matches (`[A-Z_]+=`). The checker is blind to both — `tool_versions_match_register`
is case-insensitive and takes an optional quote — so nothing but this
instruction holds the spelling the bot needs.

**Then record the site in the register.** If the file you just wrote into is not
already in `tools.<tool>.pinned_at`, append it — the path you wrote, nothing
else, and never remove one that is there. Say in the narration which path you
added and to which tool.

That is the one field of `controls.yaml` this gate may write, and it is
permitted by [ADR 0045](https://github.com/Eaiger-Ent/ee-standard/blob/main/docs/adr/0045-a-gate-records-where-it-installed-a-tool.md):
`pinned_at` records where a repository keeps a file rather than what conformant
means, adding a path can only widen what is compared, and you know exactly which
file you wrote. **Write no other field, and no stamp** — the register is not a
deployed artefact, so stamping it would claim it as this gate's output. If the
register cannot be written, say so and name the path you would have added; do
not fall back to asking the user in a comment, which is the failure that ADR
replaced.

---

## Step 3.6 — Ignore the files that hold fetched credentials

Every other artefact this gate writes acts **after** a credential is already a
git object: the scanner reads what git carries, and push protection reads what
reached the remote. The ignore rule is the only part of SEC-001 that acts
before, and until register contract 18 nothing verified it — both this
repository's `.gitignore` and the shipped devcontainer template carried a
comment saying *SEC-001 depends on these two lines*, which is a claim rather
than a check.

For each entry in `SECRET_PATHS`, act on what `IGNORED_STATE` recorded:

- **A rule in a file git tracks:** nothing to do. Say which file carries it.
- **`UNIGNORED`:** append the path to the repository's root `.gitignore`,
  creating it if absent, under a stamped comment. **One line per path, never a
  glob.** `.env.docker` is derived from `.env` and holds the same credentials;
  a repository that wrote `.env*` and later added a file the glob missed would
  have no signal, and the two-line form is what makes a missed one visible.
- **A rule git does not track** — `.git/info/exclude`, a global excludes file,
  or an uncommitted `.gitignore`: the file is ignored on this machine and
  unignored in every clone. Add the tracked rule as above, and say plainly that
  the untracked one was never protecting anybody else.
- **The path is already tracked:** stop and report it. An ignore rule added now
  removes nothing from history. Show `git log --oneline -- "$p"`, say that the
  credentials in it must be treated as disclosed and rotated, and do **not**
  write the rule as though it had fixed anything. This gate cannot rewrite
  history and must not imply that it did.

The stamp goes above the lines rather than at the top of the file: `.gitignore`
holds build output, editor droppings and language caches that belong to nobody
in particular, and a whole-file stamp would claim them for SEC-001. Same rule as
`.pre-commit-config.yaml`, and for the same reason.

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
register-check --repo "$REPO" --register "$REGISTER" \
  run --control SEC-001 --control SEC-002 --control SEC-003
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

Exit `3` is the expected result today, and saying so precisely matters. Two
blocks can decline, for different reasons, and neither is a failure:

- **SEC-001's `remote` block** — GitHub secret scanning push protection —
  reports `SKIPPED (no credentials)` with no token, and `UNCLASSIFIED` with one
  that cannot read `security_and_analysis`. Enabling push protection is a
  platform act a human with admin takes (`docs/08-adopting.md` § 1).
- **SEC-003's `remote` block** — the expiry of the credential CI carries —
  reports `UNCLASSIFIED` anywhere that is not a GitHub Actions job, because the
  token in the shell you are running this from is not the one CI carries. It is
  answered by the CI run, not by this deployment.

The local loci are verified either way; the remote ones are not, and are not
claimed.

Never report `3` as a clean pass, and never re-run with a flag that hides it.

---

## Output

**Deployed:**

```text
gate-secrets deployed SEC-001 in <repo>.
  pre-commit  .pre-commit-config.yaml — hook '<tool>' (stamped)
  ci          .github/workflows/<file> — install + secret scan (stamped)
  remote      not deployed — push protection is a platform act (§ 1)
Verified: register-check run --control SEC-001 --control SEC-002 \
  --control SEC-003 → exit 3
  local loci PASS; remote SKIPPED (no credentials), Phase 3.
```

**Failed verification:**

```text
gate-secrets wrote its artefacts, and register-check does not accept them.
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

## Calibration

- **Strong:** `${CLAUDE_SKILL_DIR}/examples.md` §Strong — a deployment where
  every value came from the register, every declared locus is wired and stamped,
  and the checker's verdict is reported as given.
- **Weak:** `${CLAUDE_SKILL_DIR}/examples.md` §Weak — a run whose output
  claims more than the artefacts deliver.

## Co-update partners

Canonical source for both shared standards below:
`${CLAUDE_PLUGIN_ROOT}/reference/`. Registered in
`docs/skill-relationship-map.md`.

- **Write narration shape** (`reference/write-narration.md`) — shared with
  `gate-build`, `gate-iac`, `gate-quality`, `gate-repo`, `gate-secrets`,
  `gate-supply-chain`, `register-adopt`, `register-install` and
  `register-variance`. Change the shape there, never here; ADR 0036 is the
  reason it is one file rather than nine copies.
- **Pre-commit runner precondition** (`reference/pre-commit-runner.md`) —
  shared with every gate skill that writes a pre-commit hook: `gate-build`,
  `gate-iac`, `gate-quality`, `gate-secrets` and `gate-supply-chain`.
- **Provenance stamp and verify contract** — every skill here stamps what it
  writes and verifies through `register-check`. The stamp fields and the
  checker's exit codes are the register's contract, not any one skill's;
  co-update all nine when the contract version changes.
