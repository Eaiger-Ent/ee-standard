---
name: gate-build
description: >
  Deploy BLD-001 and DEV-001: a non-root container user, a digest-pinned image
  and a complete devcontainer lock file, enforced at both declared loci.
  Triggers: 'deploy gate-build', 'pin the devcontainer', '/gate-build'.
argument-hint: "[--repo <path>] [--register <path>]"
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
---

# /gate-build — deploy the build and environment gates

You are running the **gate-build** skill. It deploys BLD-001 (*every container
image stage ends as a non-root user*) and DEV-001 (*devcontainer features are
version-pinned*) in a target repository, then verifies its own work with the
same checker that audits it.

Two controls, one skill, because they read the same file. BLD-001 wants a user
and DEV-001 wants two pins, and both are keys in `devcontainer.json`. Two skills
editing one file in turn would each rewrite what the last one wrote.

**Two rules govern everything below.**

**The register decides, this skill writes.** Which properties are required, how
a locus reaches the checker, and what counts as pinned all come from
`controls.yaml`. Nothing here hard-codes a tool, an image or a version. If a
value you need is not in the register, stop and say so — inventing one puts a
second copy of a rule in a skill, which is the drift this standard exists to
prevent.

**This gate pins what it finds; it does not choose.** The shipped devcontainer
template decides which image and which features a repository starts from, and an
adopter whose stack it does not fit chooses for themselves; DEV-001 insists that
whichever were chosen are pinned, and BLD-001 that the container does not end as
root. Those are different questions, and this gate is only ever asked the second
(ADR 0037). Inventing an image or a user here produces a container that does not
start.

**Do not use when:**

- The repository has no `controls.yaml` and you have no register path to point
  at. Deploy the register first; there is nothing to derive the pins from.
- The repository has neither a `Dockerfile` nor a `.devcontainer/`. Both
  controls skip on their predicates — say so rather than creating a devcontainer
  nobody asked for.
- You want every gate, not these two. Use `register-adopt`, which plans across
  the whole register and dispatches here.

## Inputs

| Input | Required | Default | Description |
| ------- | ---------- | --------- | ------------- |
| `--repo <path>` | No | current directory | The repository to deploy into |
| `--register <path>` | No | `<repo>/controls.yaml` | The register to read pins from |

Both flags mirror `register-check`'s own, so a deployment and its audit can
never be pointed at different things by accident.

## Success criteria

1. Every value written came from the register or from the repository; none was
   chosen here.
2. Both loci each control declares are wired — pre-commit and ci.
3. Each artefact written carries a provenance stamp naming the control whose
   locus it is, this skill and version, and the register's version and contract.
4. `register-check run --control BLD-001 --control DEV-001` was run afterwards,
   its output shown, and its verdict reported as given — including a failure.
5. Nothing was written outside the target repository.

---

## Pre-flight — read the register, then read the repository

Nothing is written in this phase. Any file this skill writes that is found
zero-byte or truncated — from an interrupted prior run — is treated as absent.

### 1. Resolve and read the register

```bash
register-check --repo "$REPO" --register "$REGISTER" explain BLD-001
```

If this fails, stop and show the error. A register that does not load cannot be
the authority for anything, and every step below reads it.

| State var | From |
| --- | --- |
| `TOOL` | BLD-001's `gate_wired_at_declared_loci` block, `args.tool` |
| `TOOL_INVOCATION` | `tools.<TOOL>.invocation` — how a locus reaches the checker |
| `LOCI` | BLD-001's and DEV-001's `locus:` lists |
| `REGISTER_VERSION` | top-level `version` |
| `REGISTER_CONTRACT` | `meta.register_contract` |
| `SKILL_VERSION` | the plugin's `.claude-plugin/plugin.json`, `version` |
| `GATE_CONTRACT` | the plugin's `.claude-plugin/deploys.json`, `gates.gate-build.contractVersion` |

The last two rows are the **plugin's** numbers rather than the register's,
read from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/`. `GATE_CONTRACT` is what a
stamp records as `gate-contract`, and it moves only when what this gate writes
changes, so a documentation release of the plugin recommends nothing
(ADR 0038). If `${CLAUDE_PLUGIN_ROOT}` is unset, stop and say so.

**If `tools.<TOOL>` has no `invocation`**, stop. The pre-commit gate would have
to run a bare tool name, which resolves from `PATH` — and what answered would be
auditing the repository (ADR 0020). That is a defect in the register to fix
there.

### 2. Read the repository's current state

| State var | Command |
| --- | --- |
| `DOCKERFILES` | every tracked `Dockerfile`, and the final `USER` of each |
| `DEVCONTAINER` | `.devcontainer/devcontainer.json`, or `ABSENT` |
| `USER_STATE` | `containerUser` and `remoteUser` as declared — **absent counts as root** |
| `IMAGE_STATE` | the `image:` reference, and whether it carries an `@sha256:` digest |
| `BUILD_STATE` | whether the devcontainer builds from `build.dockerfile` rather than `image` |
| `FEATURES` | every id under `features:` |
| `LOCK_STATE` | `.devcontainer/devcontainer-lock.json`, and which of `FEATURES` it pins |
| `SETUP_STATE` | `.devcontainer/setup.sh`, and which other gates' regions it holds |
| `PRECOMMIT_STATE` | `test -f .pre-commit-config.yaml && echo EXISTS \|\| echo ABSENT` |
| `HOOK_STATE` | whether a hook's `entry` runs `TOOL_INVOCATION` for BLD-001 and for DEV-001 |
| `AUDIT_STATE` | whether a gating step already runs `TOOL_INVOCATION` with no `--control` |

**A devcontainer that builds from a `Dockerfile` has no `image:` to pin**, and
DEV-001's digest half reads the Dockerfile's `FROM` instead. Record which shape
this repository has; the two are not interchangeable and writing the wrong key
produces a config the tooling ignores.

### 3. Report the plan before writing

Show a table of what will be written, to which file, for which control, and what
already exists there. If any artefact exists and this skill did not write it —
no `ee-control:` stamp naming `gate-build` — ask via **AskUserQuestion** whether
to take it over. Options: Adopt and stamp / Leave and abort.

Adopting is the honest option, not the polite one: a repository with a
devcontainer at all usually has a user and an image already. Say so in the
stamp's surrounding comment, so the stamp records what happened rather than
claiming a deployment that never took place.

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

## Step 1 — Make the container's user a statement (BLD-001)

**If `USER_STATE` names a non-root user:** write nothing, stamp the key that is
there, and say it was adopted.

**If `USER_STATE` is absent:** the container runs as whatever its base image
uses, which may be root today and may become root on any digest bump. Non-root
by luck is not the property BLD-001 states. Find the user the base image
actually provides and write it as `remoteUser`:

```bash
docker run --rm "$IMAGE" id -un
```

Ask via **AskUserQuestion** before writing a user the image does not define.
Inventing one produces a container that does not start, which is a worse
failure than the one being fixed.

**If `containerUser` or `remoteUser` is `root`:** stop. That is a container that
runs as root whatever the tooling does, and BLD-001 is `variance: forbidden`
with `baseline: null` — there is no tolerated list to add it to, and adding one
is a register change rather than a config change.

**For each entry in `DOCKERFILES` whose final stage ends as root or as numeric
`0`:** report it and stop. A `USER` line this skill appends changes what the
image runs as, and whether the process can still write where it needs to is a
question about that image rather than about this control.

---

## Step 2 — Pin the image and every feature (DEV-001)

Read `${CLAUDE_SKILL_DIR}/templates/devcontainer.json` and substitute
`{{CONTAINER_USER}}`, `{{IMAGE}}`, `{{IMAGE_DIGEST}}`, `{{SKILL_VERSION}}`,
`{{GATE_CONTRACT}}`, `{{REGISTER_VERSION}}` and `{{REGISTER_CONTRACT}}`. Merge it into the
`devcontainer.json` that is there — **as text, not by reparsing and dumping**.
The stamps are `//` comments and a round trip through a JSON writer drops them;
the checker reads this file with a JSONC reader, so the comments stay legal.

**The image digest.** If `IMAGE_STATE` shows a floating tag, resolve it to the
digest the registry serves *now* and write both:

```bash
docker buildx imagetools inspect "$IMAGE" --format '{{"{{"}}.Manifest.Digest{{"}}"}}'
```

Keep the tag in a comment beside it. A digest with no readable version is a pin
a reviewer cannot judge.

**The lock file.** Every id under `features:` must appear in
`.devcontainer/devcontainer-lock.json`, resolved to a digest:

```bash
devcontainer upgrade --workspace-folder "$REPO"
```

**A lock file covering some features is the state this control exists to catch.**
Phase 0.5's own criterion was re-opened over exactly this: a lock file pinning
three of four features reads as solved and is not. If `LOCK_STATE` shows a
partial lock, say which features are missing before regenerating, so the diff is
readable as a fix rather than as noise.

**A complete lock file over a floating image tag is the more dangerous
half-state.** Both halves or neither — do not report success on one.

---

## Step 3 — Own `.devcontainer/setup.sh`, and only your part of it

This gate creates `setup.sh` when the devcontainer has none and it is named as
the `postCreateCommand`. It does **not** own what other gates install there:
`gate-secrets` writes and stamps the scanner's install block, exactly as both
gates write their own hooks into one `.pre-commit-config.yaml`.

- **`SETUP_STATE` is `ABSENT`:** create it with `set -euo pipefail` and nothing
  else. A setup script long enough to need sectioning is doing work that belongs
  in the image or in a pinned feature (`docs/03-devcontainer.md`).
- **`SETUP_STATE` shows another gate's region:** leave it untouched, including
  its stamp. Reformatting the file makes that gate's change unreviewable and
  makes its stamp claim a deployment this skill performed.

This skill writes no stamp of its own into `setup.sh`. Neither BLD-001 nor
DEV-001 has a locus there, and a stamp naming a control whose locus the file is
not is a claim rather than a record.

---

## Step 4 — Wire both loci

Both controls declare `locus: [pre-commit, ci]`, and until register contract 15
neither locus was verified for either. The blocks that were there read the
*property* — the final `USER`, the declared container user, the lock file's
coverage — out of the files on disk, which is a different claim from *something
enforces this before a commit lands and before a merge does*.

**The pre-commit locus.** Read
`${CLAUDE_SKILL_DIR}/templates/precommit-hook.yaml` and substitute the same
values.

- **`PRECOMMIT_STATE` is `ABSENT`:** create `.pre-commit-config.yaml` with a
  single `repos: - repo: local` entry holding the block.
- **`PRECOMMIT_STATE` is `EXISTS`, `HOOK_STATE` is `ABSENT`:** append the block
  to the existing `repo: local` hooks list, preserving every other hook.
- **`HOOK_STATE` is wired:** replace only this hook's own lines and its stamps.

One hook, two stamps. The read-back matches on the control being evaluated, so a
hook stamped for BLD-001 alone leaves DEV-001's pre-commit locus unrecorded even
though the same command enforces it.

**The ci locus.** If `AUDIT_STATE` shows a gating step already running the
checker with no `--control`, that step audits every applicable control and
reaches both of these. Write no second step; stamp the one that is there and
**say that you did not add one**. Otherwise read
`${CLAUDE_SKILL_DIR}/templates/ci-steps.yaml`, substitute the same values, and
add its step to a job that runs on `push` or `pull_request`.

**Running the checker is not the same as auditing with it.** A hook or step
invoking `register-check schema`, `meta`, `assert` or `explain` reaches no
control at all, and the verify step below will not credit it.

---

## Step 5 — Verify, through the checker and not otherwise

```bash
register-check --repo "$REPO" --register "$REGISTER" \
  run --control BLD-001 --control DEV-001
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

Neither control declares a `remote` locus, so nothing is waiting on Phase 3.

**`UNCLASSIFIED` is the verdict to read carefully.** A repository with a
`Dockerfile` runs BLD-001's `hadolint` block, and an absent linter is
`UNCLASSIFIED — cannot verify`, not a pass (ADR 0016). Say so plainly, and say
what closes it: a `tools.hadolint` entry in *that repository's* register naming
the loci it installs the linter at (`docs/08-adopting.md` § 3.4). Do not install
a tool the register does not pin.

---

## Output

**Deployed:**

```text
gate-build deployed BLD-001, DEV-001 in <repo>.
  BLD-001     .devcontainer/devcontainer.json — remoteUser (stamped)
  DEV-001     .devcontainer/devcontainer.json — image digest (stamped)
  DEV-001     .devcontainer/devcontainer-lock.json — <n> features pinned
  pre-commit  .pre-commit-config.yaml — hook '<tool>-build' (stamped ×2)
  ci          reached by the existing full audit — no step added
Verified: register-check run --control BLD-001 --control DEV-001 → exit 0
```

**Failed verification:**

```text
gate-build wrote its artefacts, and register-check does not accept them.
<the failing block, verbatim>
This is a failed deployment, not a partial one. Nothing has been committed.
```

**Aborted:**

```text
gate-build stopped at <phase>: <reason>. Nothing was written.
```

## Error handling

| Condition | Action |
| ----------- | -------- |
| No register found or it fails to load | Stop. Emit **Aborted**; there is nothing to derive pins from |
| `tools.<TOOL>` has no `invocation` | Stop. The pre-commit gate would resolve from `PATH`, and what answered would be auditing the repository |
| `containerUser` or `remoteUser` is `root` | Stop. BLD-001 is `variance: forbidden` with `baseline: null`; there is nowhere to record it |
| A Dockerfile's final stage ends as root | Report and stop. Whether the process can still write where it needs to is a question about that image |
| The base image defines no non-root user | Ask before writing one. An invented user produces a container that does not start |
| A tag that cannot be resolved to a digest | Stop for that image and say so. A wrong digest pins the repository to an image nobody chose |
| Verify reports `UNCLASSIFIED` for `hadolint` | Report it as unverified, not as a pass, and say what closes it |
| Verify exits `1` | Report a failed deployment. Do not retry with a narrower check |

## Idempotency

Re-running is safe. Pre-flight reads what is already wired, Steps 1 and 2 write
only keys that are absent or unpinned, Step 3 leaves other gates' regions
untouched, and Step 4 replaces only this gate's own hook and stamps. A re-run
after a register bump rewrites the stamps with the new contract, which is what
makes a stale deployment visible rather than permanent.

This skill never commits. Deployment produces a reviewable change and a human
decides whether it lands (`docs/00-concepts.md` § Notify, never redeploy).

## Standards

- Human-readable overview, and why this gate pins rather than chooses:
  `${CLAUDE_SKILL_DIR}/README.md`
- The artefacts it writes:
  `${CLAUDE_SKILL_DIR}/templates/devcontainer.json`,
  `${CLAUDE_SKILL_DIR}/templates/precommit-hook.yaml` and
  `${CLAUDE_SKILL_DIR}/templates/ci-steps.yaml`

## Calibration

- **Strong:** `${CLAUDE_SKILL_DIR}/examples.md` §Strong — a deployment where
  every value came from the register, every declared locus is wired and stamped,
  and the checker's verdict is reported as given.
- **Weak:** `${CLAUDE_SKILL_DIR}/examples.md` §Weak — a run whose output
  claims more than the artefacts deliver.

## Co-update partners

Canonical source for both shared standards below:
`${CLAUDE_PLUGIN_ROOT}/reference/`. Registered in
`docs/02-skill-family.md`.

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
