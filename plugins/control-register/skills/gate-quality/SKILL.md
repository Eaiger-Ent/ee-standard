---
name: gate-quality
description: >
  Deploy LNT-001, TYP-001 and TST-001: wire the register's linter, type checker
  and test command at every locus they declare, stamp what it writes, verify
  through register-check. Triggers: 'deploy gate-quality', '/gate-quality'.
argument-hint: "[--repo <path>] [--register <path>]"
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
---

# /gate-quality — deploy the code-quality gates

You are running the **gate-quality** skill. It deploys LNT-001 (*lint and format
violations block the merge*), TYP-001 (*static type checking runs in strict mode
and blocks*) and TST-001 (*a failing test fails the build*) in a target
repository, then verifies its own work with the same checker that audits it.

Three controls, one skill, because they share two files. A pre-commit config and
a gating workflow would otherwise be edited by three skills in turn, each
rewriting what the last wrote. Gates are grouped by the artefact they write, not
one per control.

**Two rules govern everything below.**

**The register decides, this skill writes.** Which linter, which type checker,
where each keeps its configuration, which key turns strictness on, which editor
extension serves it, how every locus invokes it and which test-command spellings
are acceptable all come from `controls.yaml`. Nothing here hard-codes a tool, a
version or an invocation. If a value you need is not in the register, stop and
say so — inventing one puts a second copy of a rule in a skill, which is the
drift this standard exists to prevent.

**Enforcement is never Claude.** What ships is a set of pinned binaries invoked
by pre-commit hooks and CI steps. This skill installs and wires them, and then
has no further part in enforcement.

**Do not use when:**

- The repository has no `controls.yaml` and you have no register path to point
  at. Deploy the register first; there is nothing to derive the pins from.
- The repository is in no stack the register's `stacks:` section defines. There
  is no linter to wire, and LNT-001 and TYP-001 skip on their predicate.
  TST-001 still applies — say so, and deploy that alone.
- You want every gate, not these three. Use `register-adopt`, which plans across
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
2. Every locus each control declares is wired — editor, pre-commit and ci for
   LNT-001; pre-commit and ci for TYP-001; ci for TST-001.
3. Every tool wired is pinned in a lockfile the repository tracks. An
   invocation that reaches whatever is on `PATH` is not the pin it names
   (ADR 0020, case C).
4. Each artefact written carries a provenance stamp naming the control whose
   locus it is, this skill and version, and the register's version and contract.
5. `register-check run --control LNT-001 --control TYP-001 --control TST-001`
   was run afterwards, its output shown, and its verdict reported as given —
   including a failure.
6. Nothing was written outside the target repository.

---

## Pre-flight — read the register, then read the repository

Nothing is written in this phase. Any file this skill writes that is found
zero-byte or truncated — from an interrupted prior run — is treated as absent.

### 1. Resolve and read the register

```bash
register-check --repo "$REPO" --register "$REGISTER" explain LNT-001
```

If this fails, stop and show the error. A register that does not load cannot be
the authority for anything, and every step below reads it.

Then read `stacks:` directly. For **each stack whose predicate the repository
satisfies** — the predicate is in `predicates:`, evaluated against files and
never self-declared — store:

| State var | From |
| --- | --- |
| `STACK` | the stack's key |
| `SOURCE_PATTERN` | `stacks.<STACK>.source_globs`, as one anchored regex |
| `LINT_TOOL` | `stacks.<STACK>.gates.lint.tool` |
| `LINT_INVOCATION` | `…gates.lint.invocation` |
| `LINT_HOOK_ID` | `…gates.lint.pre_commit` |
| `EDITOR_EXTENSION` | `…gates.lint.editor_extension` |
| `EDITOR_LANGUAGE` | `…gates.lint.editor_binding.language` — absent means this gate binds no file type |
| `EDITOR_BINDING_SETTING` | `…gates.lint.editor_binding.setting` |
| `LINT_CONFIG` | `…gates.lint.config` — the ordered list of places it may live |
| `TYPECHECK_TOOL` | `…gates.typecheck.tool` |
| `TYPECHECK_INVOCATION` | `…gates.typecheck.invocation` |
| `TYPECHECK_HOOK_ID` | `…gates.typecheck.pre_commit` |
| `STRICT_KEY` | `…gates.typecheck.strict_key` |
| `COVERAGE_KEY` | `…gates.typecheck.coverage_key` |
| `TYPECHECK_CONFIG` | `…gates.typecheck.config` |
| `LINT_PACKAGE` | `…gates.lint.package`, falling back to `…gates.lint.tool` |
| `TYPECHECK_PACKAGE` | `…gates.typecheck.package`, falling back to `…gates.typecheck.tool` |
| `STACK_ECOSYSTEM` | `stacks.<STACK>.ecosystem` — whose lockfile pins those two |
| `ADD_DEPENDENCY` | `ecosystems.<STACK_ECOSYSTEM>.add_dev_dependency` — command per lockfile |

And once, not per stack:

| State var | From |
| --- | --- |
| `TEST_COMMANDS` | `ecosystems.<eco>.test_commands`, for each ecosystem whose manifest the repository has |
| `SUPPRESSION` | `suppression:` — the idioms nothing this gate writes may contain |
| `REGISTER_VERSION` | top-level `version` |
| `REGISTER_CONTRACT` | `meta.register_contract` |

**`SOURCE_PATTERN` is derived, not chosen.** `source_globs` is the set of
tracked files the stack's gates are claimed to cover; turn those globs into one
regex for the hooks' `files:` key. Picking a pre-commit `types:` tag instead
would be a second statement of that set, free to name fewer files than the
control claims.

**If an `invocation` is a bare tool name** — no path into the lockfile's
artefact, no package-manager runner in front of it — stop and say so before
writing anything. That string is what every locus will run, and a bare name
resolves from `PATH`: the gate would deploy a locus verified against whatever
global happens to be installed rather than against the version the lockfile
pins. This is the failure ADR 0020 measured for DOC-001. Offer via
**AskUserQuestion** to fix the register first. Options: Fix the register / Abort.

### 2. Read the repository's current state

| State var | Command |
| --- | --- |
| `CONFIG_STATE` | for each config location in order, whether the file exists and holds the named section |
| `STRICT_STATE` | whether `STRICT_KEY` is true in whichever location configures the type checker |
| `COVERAGE_STATE` | the value at `COVERAGE_KEY`, and which tracked files matching `SOURCE_PATTERN` it leaves out |
| `EDITOR_STATE` | `EDITOR_EXTENSION` present in `.devcontainer/devcontainer.json` or `.vscode/extensions.json` |
| `BINDING_STATE` | what holds `"[EDITOR_LANGUAGE]".EDITOR_BINDING_SETTING` in `.vscode/settings.json`, and whether `.devcontainer/devcontainer.json` sets it too |
| `PRECOMMIT_STATE` | `test -f .pre-commit-config.yaml && echo EXISTS \|\| echo ABSENT` |
| `HOOK_STATE` | whether a hook's `id` or `entry` mentions `LINT_HOOK_ID`, and the same for `TYPECHECK_HOOK_ID` |
| `WORKFLOWS` | `ls .github/workflows/ 2>/dev/null \|\| echo NONE` |
| `TEST_STATE` | whether a gating step already invokes one of `TEST_COMMANDS` |
| `PIN_STATE` | which of `LINT_PACKAGE` and `TYPECHECK_PACKAGE` a tracked `STACK_ECOSYSTEM` lockfile pins, and which lockfile it is |
| `LEGACY_STATE` | configuration for a superseded linter or formatter the register does not name |

For each workflow found, establish whether it **gates**: a workflow is the ci
locus only if it runs on `push` or `pull_request`. Record the gating workflows
and their job ids, and which of them installs dependencies from the lockfile —
the three CI steps belong in that job, after that install, or they run against
nothing.

### 3. Report the plan before writing

Show a table of what will be written, to which file, for which control, and what
already exists there. If any artefact exists and this skill did not write it —
no `ee-control:` stamp naming `gate-quality` — ask via **AskUserQuestion**
whether to take it over. Options: Adopt and stamp / Leave and abort.

Adopting is the honest option, not the polite one: hand-wired quality gates are
the normal starting state of a repository that has any at all. Say so in the
stamp's surrounding comment, so the stamp records what happened rather than
claiming a deployment that never took place.

---

## Say what each write is for, before you make it

**One line before every file write, and no write without one.** The person
approving it sees a diff and nothing else: not which control it serves, not
which step of how many, not what will check it. The provenance stamp names the
control, but it arrives buried in the middle of the change it is explaining.
Nothing has failed at that point and nothing has passed — this gate deploys
first and verifies last, which is right, and it means the approver is being
asked to accept a change on trust unless you give them the reason first.

Use exactly this shape:

```text
<CONTROL-ID> · step <n>/<total> · <path>
  what it does:  <one clause>
  why now:       <what is absent or wrong without it>
  verified by:   register-check run --control <CONTROL-ID>, at the verify step
```

If a write serves more than one control, name them all. If it is a re-run and
the file already carries this gate's region, say that instead — *"already
deployed at contract N, replacing this gate's own block"* — because
"idempotent" is a claim the approver cannot check from a diff either.

## Step 1 — Confirm the test invocation

TST-001 is the one control here whose command the register does not settle. It
records the spellings it accepts for each ecosystem — `TEST_COMMANDS` — and a
repository picks one. Which member is a repository's own fact, so ask rather
than choose.

**If `TEST_STATE` shows a gating step already invoking one of them:** that is
the answer. Do not ask, and do not rewrite the step.

**Otherwise:** ask via **AskUserQuestion**, offering the register's spellings for
each ecosystem the repository is in. Two things must be true of the answer, and
say both when you ask:

- It matches one of `TEST_COMMANDS` as an invocation — the checker matches the
  same way, and a command outside that set is a step it will not credit.
- It reaches the artefact the lockfile pins, the way `LINT_INVOCATION` does. A
  bare test runner resolves from `PATH` (ADR 0020).

Store the answer as `TEST_COMMAND`.

---

## Step 2 — Pin the tools, then make the configuration say what the controls claim

The tools are installed by the repository's package manager from its lockfile,
so there is no binary to fetch here and no version for this skill to hold. There
are two things to do: make sure the lockfile actually pins them, and make the
configuration say what the controls claim.

**The pin.** `LINT_INVOCATION` reaches the artefact the lockfile pins — and
reaches whatever is on `PATH` instead if the tool is not in the project at all
(ADR 0020, case C). An invocation cannot assert the existence of the thing it
invokes, so from register contract 13 `LNT-001` and `TYP-001` each verify the
pin as well as the wiring, and a gate that wired a tool it never added would
deploy a control it cannot satisfy.

For each of `LINT_PACKAGE` and `TYPECHECK_PACKAGE` that `PIN_STATE` shows
unpinned, run the `ADD_DEPENDENCY` command for the lockfile the repository has,
substituting the package name for `{package}`:

```bash
# The command comes from the register, keyed by the lockfile that is present.
# Do not spell one here — `uv add` and `poetry add` are both python, and which
# one is right is a fact about the repository.
$(printf '%s' "$ADD_DEPENDENCY_FOR_THIS_LOCKFILE")
```

Two states are not this skill's to resolve. If the repository has **no** tracked
lockfile for `STACK_ECOSYSTEM`, stop: SUP-001 owns that, `gate-supply-chain`
deploys it, and adding a dependency to a project with no lockfile creates one
whose contents nobody reviewed. If it has more than one, ask via
**AskUserQuestion** which package manager governs — two lockfiles is a fact
about the repository, not a thing to guess.

Report every dependency added, by name. A tool the repository did not previously
depend on is a change to what it builds, not a change to how it is checked.

**The linter's configuration.** If no location in `LINT_CONFIG` holds a
configuration, create the first one listed with an empty section for the tool.
An empty section is a real configuration: the tool's defaults, stated in a place
a reviewer can find and a later commit can tighten.

**Strictness.** If `STRICT_STATE` is not true, set `STRICT_KEY` to true in
whichever location configures the type checker. If the repository has existing
type errors this will surface them; report the count and stop rather than
weakening the setting. TYP-001 carries `baseline: null` — there is no tolerated
list to add them to, and adding one is a register change, not a config change.

**Coverage.** If `COVERAGE_KEY` names an allow-list that leaves tracked files
matching `SOURCE_PATTERN` outside it, list every one of them and extend the list
to cover them. An allow-list makes an exclusion into an *absence*: a tracked
module nothing imports is silently unchecked while the control claims all
first-party source (ADR 0019, § H). Do not extend it silently — the files being
added to coverage are the files nobody was checking.

---

## Step 3 — Wire the editor locus

LNT-001 is the only one of the three that declares an `editor` locus, so this
step writes one stamp and it names LNT-001.

Read `${CLAUDE_SKILL_DIR}/templates/editor-extensions.json` and substitute
`{{EDITOR_EXTENSION}}`, `{{STACK}}`, `{{SKILL_VERSION}}`,
`{{REGISTER_VERSION}}` and `{{REGISTER_CONTRACT}}`.

- **The repository has a devcontainer:** merge the extension into
  `customizations.vscode.extensions`, preserving every other entry.
- **It does not:** write the extension into `.vscode/extensions.json` as a
  `recommendations` entry instead. Do not create a devcontainer for this —
  demanding one would invent a dependency of LNT-001 on DEV-001's artefact, and
  a repository whose editor locus is `.vscode/` satisfies the control (§ D).

### Step 3b — Bind the file type, where the register says one

Installing the extension is not the extension being the tool that runs, and the
difference is the failure this step exists for: `charliermarsh.ruff` was
installed for the whole time a devcontainer feature had Python files bound to
`ms-python.autopep8`, and LNT-001 passed throughout (ADR 0029 point 4).

**Skip this sub-step where `EDITOR_LANGUAGE` is absent.** A gate whose register
entry declares no `editor_binding` holds no file type, and writing one would
mandate a binding the register does not — eslint is a linter, not TypeScript's
formatter.

Otherwise read `${CLAUDE_SKILL_DIR}/templates/editor-settings.json`, substitute
`{{EDITOR_LANGUAGE}}`, `{{EDITOR_BINDING_SETTING}}`, `{{EDITOR_EXTENSION}}`,
`{{STACK}}`, `{{SKILL_VERSION}}`, `{{REGISTER_VERSION}}` and
`{{REGISTER_CONTRACT}}`, and merge it into **`.vscode/settings.json`**,
preserving every other setting. Create the file where it does not exist.

- **`BINDING_STATE` shows another extension holding the language:** replace that
  value and say in the stamp comment which extension was displaced. A repository
  that deliberately mandates a different one changes the register, not this
  file.
- **`BINDING_STATE` shows `devcontainer.json` also setting it:** remove it from
  there. The binding belongs at workspace scope alone — a copy in
  `devcontainer.json` lands in the same machine-scoped file a feature's does and
  merges on terms the specification declines to state. The checker fails the
  duplicate even when the two agree.

Never write the binding into `devcontainer.json`, whichever file the extension
list went into in Step 3.

The editor reads the same configuration pre-commit and CI read. Write nothing
that configures rules here: an editor with rules of its own is the second copy
this standard exists to prevent.

---

## Step 4 — Wire the pre-commit locus

Read `${CLAUDE_SKILL_DIR}/templates/precommit-hooks.yaml` and substitute the
stack's values. One pair of hooks per applicable stack.

- **`PRECOMMIT_STATE` is `ABSENT`:** create `.pre-commit-config.yaml` with a
  single `repos: - repo: local` entry holding the blocks.
- **`PRECOMMIT_STATE` is `EXISTS`, `HOOK_STATE` is `ABSENT`:** append the blocks
  to the existing `repo: local` hooks list, preserving every other hook. Do not
  reformat the file — other controls' hooks live there, and a wholesale rewrite
  makes this gate's change unreviewable.
- **A hook is already wired:** replace only that hook's own lines and its stamp,
  and record in the stamp comment that an existing hook was adopted.

The stamps go at the hooks, never at the top of the file.

---

## Step 5 — Wire the ci locus

Read `${CLAUDE_SKILL_DIR}/templates/ci-steps.yaml` and substitute the same
values plus `{{TEST_COMMAND}}`.

- **A gating workflow exists with a frozen-install step:** add the three steps
  to that job, after the install. They run the tools the lockfile just placed,
  and a lint step before the install lints against nothing.
- **A gating workflow exists without one:** say plainly that the repository's CI
  does not install from its lockfile, which is SUP-001's property rather than
  this gate's, and that the steps below will not run until it does. Add the
  steps; report the control as **not deployed** at the ci locus.
- **Only non-gating workflows exist:** do not add steps to one. Say that the
  repository has CI which cannot gate a merge, and create a new workflow that
  runs on `push` and `pull_request`.
- **No workflows exist:** create `.github/workflows/register-check.yml` with a
  single job holding a checkout, a frozen install and the steps.

Nothing written here may carry `continue-on-error`, and no `run:` may contain an
idiom from `SUPPRESSION`. LNT-001 and TST-001 both verify through
`no-failure-suppression`, and a suppressed step is a gate that reports rather
than blocks.

---

## Step 6 — Migrate what this replaces

- **`LEGACY_STATE` names a superseded linter or formatter:** the register
  mandates one linter per stack, and a second one configured alongside it is a
  second rule set — two tools disagreeing about the same file, with no recorded
  decision about which wins. Show what is configured, and offer via
  **AskUserQuestion** to remove its configuration and its hooks. Options:
  Remove / Keep. Keeping is a variance, so say what it is a variance from.
- **A per-file opt-out exists in the type checker's configuration** — a blanket
  override that ignores errors for every module, or a suppression comment
  regime — read every one. TYP-001's `enforces` says *no per-file opt-out beyond
  the recorded baseline*, and its baseline is `null`. An override that switches
  strictness off in a second place is strict mode not being on.

Do not delete anything silently in either direction. List what is going, what is
staying, and why each.

---

## Step 7 — Verify, through the checker and not otherwise

```bash
register-check --repo "$REPO" --register "$REGISTER" \
  run --control LNT-001 --control TYP-001 --control TST-001
```

This is the only verification step. It runs each control's own verify blocks
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
| `3` | No violation, but something could not be verified | Say which block was skipped and why, and do not round it up |

Exit `0` is the expected result here: all three controls verify from files, and
none of them declares a `remote` locus. If the run reports `3`, something
declared itself partial or could not be classified — name it rather than
treating it as a pass.

---

## Output

**Deployed:**

```text
gate-quality deployed LNT-001, TYP-001 and TST-001 in <repo>.
  editor      <file> — <extension> (stamped, LNT-001)
  pre-commit  .pre-commit-config.yaml — hooks '<lint>', '<typecheck>' (stamped)
  ci          .github/workflows/<file> — lint, type check, tests (stamped)
Coverage: <n> tracked file(s) added to <coverage key>, previously unchecked.
Verified: register-check run --control LNT-001 --control TYP-001
          --control TST-001 → exit 0
```

**Failed verification:**

```text
gate-quality wrote its artefacts, and register-check does not accept them.
<the failing block, verbatim>
This is a failed deployment, not a partial one. Nothing has been committed.
```

**Aborted:**

```text
gate-quality stopped at <phase>: <reason>. Nothing was written.
```

## Error handling

| Condition | Action |
| ----------- | -------- |
| No register found or it fails to load | Stop. Emit **Aborted**; there is nothing to derive pins from |
| The repository is in no stack the register defines | Deploy TST-001 alone and say that LNT-001 and TYP-001 skip on their predicate |
| An `invocation` is a bare tool name | Stop. The register names a locus that resolves from `PATH` (ADR 0020) — fix it there |
| A stack's gate names no `pre_commit` or `editor_extension` its control's loci need | Stop. The register declares a locus it gives no way to wire |
| Turning strictness on surfaces existing type errors | Report the count and stop. `baseline: null` means there is nowhere to put them |
| No gating workflow, and the user declines to create one | Write the editor and pre-commit artefacts, then report the ci locus as **not deployed** — a partial deployment is reported as one |
| Verify exits `1` | Report a failed deployment. Do not retry with a narrower check |

## Idempotency

Re-running is safe. Pre-flight reads what is already wired, Step 4 replaces only
this gate's own hooks and stamps, and Step 5 adds steps only where they are
missing. A re-run after a register bump rewrites the stamps with the new
contract, which is what makes a stale deployment visible rather than permanent.

This skill never commits. Deployment produces a reviewable change and a human
decides whether it lands (`docs/00-concepts.md` § Notify, never redeploy).

## Standards

- Human-readable overview, and why one skill deploys three controls:
  `${CLAUDE_SKILL_DIR}/README.md`
- The artefacts it writes:
  `${CLAUDE_SKILL_DIR}/templates/editor-extensions.json`,
  `${CLAUDE_SKILL_DIR}/templates/editor-settings.json`,
  `${CLAUDE_SKILL_DIR}/templates/precommit-hooks.yaml` and
  `${CLAUDE_SKILL_DIR}/templates/ci-steps.yaml`
