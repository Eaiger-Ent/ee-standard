---
name: gate-supply-chain
description: >
  Deploy SUP-001 to SUP-004: frozen install from the lockfile, update
  proposals for every ecosystem, every CI action pinned to a SHA, and every
  pinned release digest checked against what the project published.
  Triggers: 'deploy gate-supply-chain', 'pin CI actions', '/gate-supply-chain'.
argument-hint: "[--repo <path>] [--register <path>]"
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
---

# /gate-supply-chain — deploy the supply-chain gates

You are running the **gate-supply-chain** skill. It deploys SUP-001
(*dependencies resolve from a committed lockfile*), SUP-002 (*dependency updates
are proposed automatically*), SUP-003 (*third-party CI actions are pinned to
a commit SHA*) and SUP-004 (*a pinned release artefact's digest is the one the
project published*) in a target repository, then verifies its own work with the
same checker that audits it.

Four controls, one skill, because they are one property split four ways: what a
build resolves, how it stays current, what it is allowed to fetch, and whether
what it fetched is what was released. Two of
them write into the same gating workflow, and SUP-001's install step has to come
*before* every other gate's steps in it — an ordering no separate skill could
guarantee.

**Two rules govern everything below.**

**The register decides, this skill writes.** Which lockfiles count, what
installing from one looks like, which `package-ecosystem:` spellings a bot
accepts, and how a locus reaches the checker all come from `controls.yaml`.
Nothing here hard-codes a command or a version. If a value you need is not in
the register, stop and say so — inventing one puts a second copy of a rule in a
skill, which is the drift this standard exists to prevent.

**Enforcement is never Claude.** What ships is a pinned checker invoked by a
pre-commit hook and a CI step, a frozen install, and a bot configuration the
platform acts on. This skill wires them and then has no further part in
enforcement.

**Do not use when:**

- The repository has no `controls.yaml` and you have no register path to point
  at. Deploy the register first; there is nothing to derive the commands from.
- The repository has no package manager at all. SUP-001 passes on that finding
  rather than on a predicate that never looked, and there is no install step to
  write. SUP-003 still applies if there are workflows — say so, and deploy it
  alone.
- You want every gate, not these three. Use `register-adopt`, which plans across
  the whole register and dispatches here.

## Inputs

| Input | Required | Default | Description |
| ------- | ---------- | --------- | ------------- |
| `--repo <path>` | No | current directory | The repository to deploy into |
| `--register <path>` | No | `<repo>/controls.yaml` | The register to read commands from |

Both flags mirror `register-check`'s own, so a deployment and its audit can
never be pointed at different things by accident.

## Success criteria

1. Every value written came from the register; none was chosen here.
2. Every locus each control declares is wired — ci for SUP-001 and SUP-002,
   pre-commit **and** ci for SUP-003.
3. Each artefact written carries a provenance stamp naming the control whose
   locus it is, this skill and version, and the register's version and contract.
4. `register-check run --control SUP-001 --control SUP-002 --control SUP-003 --control SUP-004`
   was run afterwards, its output shown, and its verdict reported as given —
   including a failure.
5. Nothing was written outside the target repository.

---

## Pre-flight — read the register, then read the repository

Nothing is written in this phase. Any file this skill writes that is found
zero-byte or truncated — from an interrupted prior run — is treated as absent.

### 1. Resolve and read the register

```bash
register-check --repo "$REPO" --register "$REGISTER" explain SUP-001
```

If this fails, stop and show the error. A register that does not load cannot be
the authority for anything, and every step below reads it.

Then read `ecosystems:` and `tools:` directly. For **each ecosystem whose
manifest the repository has**, store:

| State var | From |
| --- | --- |
| `ECOSYSTEM` | the ecosystem's key |
| `LOCKFILES` | `ecosystems.<ECOSYSTEM>.lockfiles` — any one of these, tracked |
| `FROZEN_INSTALL` | `ecosystems.<ECOSYSTEM>.frozen_install_command` for the lockfile this repository has |
| `ECOSYSTEM_SPELLING` | `ecosystems.<ECOSYSTEM>.dependabot` — the accepted `package-ecosystem:` names |

And once, not per ecosystem:

| State var | From |
| --- | --- |
| `TOOL` | SUP-003's `supply_chain_gate_wired_at_all_loci` block, `args.tool` |
| `TOOL_INVOCATION` | `tools.<TOOL>.invocation` — how a locus reaches the checker |
| `REGISTER_VERSION` | top-level `version` |
| `REGISTER_CONTRACT` | `meta.register_contract` |
| `SKILL_VERSION` | the plugin's `.claude-plugin/plugin.json`, `version` |
| `GATE_CONTRACT` | the plugin's `.claude-plugin/deploys.json`, `gates.gate-supply-chain.contractVersion` |

The last two rows are the **plugin's** numbers rather than the register's,
read from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/`. `GATE_CONTRACT` is what a
stamp records as `gate-contract`, and it moves only when what this gate writes
changes, so a documentation release of the plugin recommends nothing
(ADR 0038). If `${CLAUDE_PLUGIN_ROOT}` is unset, stop and say so.

**`FROZEN_INSTALL` is keyed by lockfile, not by ecosystem.** `uv sync --frozen`
and `poetry install --sync` are both python; which one is right is a fact about
this repository. If the repository has more than one of `LOCKFILES`, ask via
**AskUserQuestion** which package manager governs — two lockfiles is a fact to
establish, not to guess.

**If `tools.<TOOL>` has no `invocation`**, stop. SUP-003's pre-commit gate would
have to run a bare tool name, which resolves from `PATH` — and what answered
would be auditing the repository (ADR 0020). That is a defect in the register to
fix there.

### 2. Read the repository's current state

| State var | Command |
| --- | --- |
| `LOCK_STATE` | which of `LOCKFILES` git tracks, per ecosystem |
| `WORKFLOWS` | `ls .github/workflows/ 2>/dev/null \|\| echo NONE` |
| `INSTALL_STATE` | whether a gating job already installs from the lockfile, and which step it is |
| `UPDATE_STATE` | `.github/dependabot.yml`, `renovate.json` or another Renovate config — which exists, and which ecosystems it covers |
| `PRECOMMIT_STATE` | `test -f .pre-commit-config.yaml && echo EXISTS \|\| echo ABSENT` |
| `HOOK_STATE` | whether a hook's `entry` runs `TOOL_INVOCATION` for SUP-003, and whether one staged `pre-push` runs it for SUP-001 and SUP-002 |
| `AUDIT_STATE` | whether a gating step already runs `TOOL_INVOCATION` with no `--control` — a full audit reaches SUP-003 and needs no step of its own |
| `UNPINNED` | every `uses:` in every workflow that is not a 40-character SHA, excluding those owned by this repository's owner |

For each workflow found, establish whether it **gates**: a workflow is the ci
locus only if it runs on `push` or `pull_request`. Record the gating workflows,
their job ids, and the position of any existing install step.

### 3. Report the plan before writing

Show a table of what will be written, to which file, for which control, and what
already exists there. If any artefact exists and this skill did not write it —
no `ee-control:` stamp naming `gate-supply-chain` — ask via **AskUserQuestion**
whether to take it over. Options: Adopt and stamp / Leave and abort.

Adopting is the honest option, not the polite one: a repository with CI at all
usually has an install step and often a bot config. Say so in the stamp's
surrounding comment, so the stamp records what happened rather than claiming a
deployment that never took place.

**List `UNPINNED` in full here**, before anything is written. Each entry is a
third-party action the repository currently fetches by a tag that its owner can
move. Step 3 rewrites them, and the rewrite changes what CI runs — that is a
change to report before making, not after.

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

## Step 1 — Wire the frozen install (SUP-001)

Read `${CLAUDE_SKILL_DIR}/templates/ci-steps.yaml` and substitute
`{{FROZEN_INSTALL}}`, `{{ECOSYSTEM}}`, `{{TOOL_INVOCATION}}`, `{{TOOL}}`,
`{{SKILL_VERSION}}`, `{{GATE_CONTRACT}}`, `{{REGISTER_VERSION}}` and `{{REGISTER_CONTRACT}}`.

- **`INSTALL_STATE` shows a frozen install already:** write nothing, stamp the
  step that is there for SUP-001, and say it was adopted.
- **`INSTALL_STATE` shows an install that re-resolves** — `uv sync` without
  `--frozen`, `npm install` where `npm ci` belongs — replace only that step's
  `run:`, and say what changed. An install that re-resolves is why a lockfile
  can be committed and ignored.
- **No install step:** add one at the **top** of the gating job's steps, after
  any checkout. Every other gate's steps run tools this one places.
- **No gating workflow:** do not add steps to a non-gating one. Say plainly that
  the repository has CI which cannot gate a merge, and create a workflow that
  runs on `push` and `pull_request`.

**If the repository has no tracked lockfile for an ecosystem it is in**, stop
before writing. SUP-001 fails on that and it is not this gate's to fix: a
lockfile this skill generates pins a resolution nobody reviewed. Say which
lockfile is missing and what command produces it.

**The developer environment, if there is one.** A repository with a
devcontainer installs its package manager in `.devcontainer/setup.sh`, and that
install repeats a version the register pins — `tool_versions_match_register`
compares it, and until register contract 15 no gate claimed it. The file belongs
to `gate-build`; this block inside it belongs here, exactly as three gates write
their own hooks into one `.pre-commit-config.yaml`. Stamp the block for SUP-001,
never the file. If there is no devcontainer, write nothing and say so.

---

## Step 2 — Wire dependency updates (SUP-002)

Read `${CLAUDE_SKILL_DIR}/templates/dependabot.yaml` and write one `updates:`
entry per ecosystem, using a spelling from that ecosystem's
`ECOSYSTEM_SPELLING`.

- **`UPDATE_STATE` shows a config covering every ecosystem:** stamp it, and say
  it was adopted.
- **`UPDATE_STATE` shows a config missing an ecosystem:** add only the missing
  entries. Do not reformat the file — a wholesale rewrite makes this gate's
  change unreviewable.
- **Two bots configured:** leave both. A repository may run Dependabot for the
  ecosystems it understands and Renovate for what it cannot reach — a version
  literal in a shell script has no Dependabot manager. Check they do not overlap
  and say so; duplicate proposals for one ecosystem are noise a reviewer learns
  to ignore, which is how a real proposal gets ignored too.

Two entries are not package ecosystems and are added by repository feature
rather than by manifest: `github-actions` for a repository with workflows, and
`devcontainers` for one with a devcontainer. The checker requires both where the
feature is present. They are what keep SUP-003's SHA pins and DEV-001's digest
pins current — **a pin nothing updates rots at a known version**, which is a
different failure from an unpinned one and not a better one.

**Installing the bot is not this skill's act.** A configuration file is
necessary and not sufficient: Dependabot needs enabling on the repository, and
Renovate needs its app installed and its onboarding pull request left open
rather than closed. Both are platform acts a human with admin takes
(`docs/08-adopting.md` § 1.1). Say which one the repository now needs, and that
the config is inert until it happens.

---

## Step 3 — Pin every third-party action (SUP-003)

For each entry in `UNPINNED`, resolve the tag to the commit it points at **now**
and rewrite the reference, keeping the tag as a trailing comment so a reader can
still see what version it is:

```bash
gh api "repos/$OWNER/$REPO_NAME/commits/$TAG" --jq .sha
```

```yaml
- uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
```

Three cases need care:

- **An action owned by this repository's owner** is exempt, and the checker
  agrees — it reads the owner from the remote rather than being told. Leave it,
  and say which were skipped and why.
- **A `docker://` reference** pins by image digest, not by commit SHA. The
  checker accepts a digest here; a tag is the same failure in another spelling.
- **A tag the API cannot resolve** — a moved tag, a deleted release, a private
  action. Stop for that reference rather than guessing a SHA, and list it. A
  wrong SHA is worse than an unpinned tag: it pins the repository to code nobody
  chose.

---

## Step 4 — Wire the three controls' local and ci loci

SUP-003 declares `locus: [pre-commit, ci]`, and until register contract 14
neither was verified. `actions-pinned-to-sha` reads the *property* — every
`uses:` is a SHA — out of the files on disk, which is a different claim from
*something enforces this before a commit lands and before a merge does*. Both
are now checked, so both are now written. From contract 31 SUP-001 and SUP-002
declare a `pre-push` locus for the same reason, and the template's second block
serves both.

**The local loci.** Read
`${CLAUDE_SKILL_DIR}/templates/precommit-hook.yaml` and substitute the same
values. Write the second block only for the controls whose register entry
declares `pre-push`, dropping the stamp of any that does not, and keep its
`stages:` key — a hook staged for one moment does not serve the other.

- **`PRECOMMIT_STATE` is `ABSENT`:** create `.pre-commit-config.yaml` with a
  single `repos: - repo: local` entry holding the block.
- **`PRECOMMIT_STATE` is `EXISTS`, `HOOK_STATE` is `ABSENT`:** append the block
  to the existing `repo: local` hooks list, preserving every other hook. Do not
  reformat the file — other controls' hooks live there.
- **`HOOK_STATE` is wired:** replace only this hook's own lines and its stamp.

**The ci locus.** If `AUDIT_STATE` shows a gating step already running the
checker with no `--control`, that step audits every applicable control and
reaches SUP-003. Write no second step; stamp the one that is there and **say
that you did not add one**. Otherwise add the `Supply chain` step from
`ci-steps.yaml`.

**Running the checker is not the same as auditing with it.** A hook or step
invoking `register-check schema`, `meta`, `assert` or `explain` reaches no
control at all, and the verify step below will not credit it. This repository's
own pre-commit config ran exactly that and would have been credited with a
SUP-003 gate that could never have failed it.

---

## Step 5 — Verify, through the checker and not otherwise

```bash
register-check --repo "$REPO" --register "$REGISTER" \
  run --control SUP-001 --control SUP-002 --control SUP-003 --control SUP-004
```

This is the only verification step. It runs the controls' own verify blocks
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
| `3` | No violation, but something could not be verified | Say which block was skipped and why |

Exit `0` is the expected result. None of these three controls declares a
`remote` locus, so nothing is waiting on Phase 3 and a `3` means a block
declared itself partial — read which, rather than rounding up.

---

## Output

**Deployed:**

```text
gate-supply-chain deployed SUP-001, SUP-002, SUP-003, SUP-004 in <repo>.
  ci          .github/workflows/<file> — frozen install (stamped)
  ci          .github/dependabot.yml — <n> ecosystems (stamped)
  pre-commit  .pre-commit-config.yaml — hook '<tool>-supply-chain' (stamped)
  pre-push    .pre-commit-config.yaml — hook '<tool>-supply-chain-pre-push'
              (stamped, SUP-001 and SUP-002)
  ci          SUP-003 reached by the existing full audit — no step added
  pinned      <n> action references rewritten to SHAs; <n> owner-owned skipped
Needs a human: <Dependabot enabled | the Renovate app installed> (§ 1.1)
Verified: register-check run --control SUP-001 --control SUP-002 \
  --control SUP-003 --control SUP-004 → exit 0
```

**Failed verification:**

```text
gate-supply-chain wrote its artefacts, and register-check does not accept them.
<the failing block, verbatim>
This is a failed deployment, not a partial one. Nothing has been committed.
```

**Aborted:**

```text
gate-supply-chain stopped at <phase>: <reason>. Nothing was written.
```

## Error handling

| Condition | Action |
| ----------- | -------- |
| No register found or it fails to load | Stop. Emit **Aborted**; there is nothing to derive commands from |
| `tools.<TOOL>` has no `invocation` | Stop. SUP-003's gate would resolve from `PATH`, and what answered would be auditing the repository |
| An ecosystem is present with no tracked lockfile | Stop before writing. Say which, and the command that produces it — a lockfile this skill generates pins a resolution nobody reviewed |
| More than one lockfile for one ecosystem | Ask which package manager governs. Do not guess |
| A tag that cannot be resolved to a SHA | Stop for that reference and list it. A wrong SHA pins the repository to code nobody chose |
| Verify exits `1` | Report a failed deployment. Do not retry with a narrower check |
| Verify exits `3` | Report which block declared itself partial. Never report `3` as a clean pass |

## Idempotency

Re-running is safe. Pre-flight reads what is already wired, Step 1 replaces only
an install step that re-resolves, Step 2 adds only missing ecosystems, Step 3
rewrites only references that are not already SHAs, and Step 4 replaces only
this gate's own hook and stamp. A re-run after a register bump rewrites the
stamps with the new contract, which is what makes a stale deployment visible
rather than permanent.

This skill never commits. Deployment produces a reviewable change and a human
decides whether it lands (`docs/00-concepts.md` § Notify, never redeploy).

## Standards

- Human-readable overview, and why this gate takes no opinions of its own:
  `${CLAUDE_SKILL_DIR}/README.md`
- The artefacts it writes: `${CLAUDE_SKILL_DIR}/templates/ci-steps.yaml`,
  `${CLAUDE_SKILL_DIR}/templates/dependabot.yaml` and
  `${CLAUDE_SKILL_DIR}/templates/precommit-hook.yaml`
