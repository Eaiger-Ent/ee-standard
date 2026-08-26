---
name: register-install
description: >
  Install the control register's checker into a repository, pinned to the
  tagged ref the register names, so every locus that runs it has something to
  run. Triggers: 'install the checker', 'install register-check',
  '/register-install'.
argument-hint: "[--repo <path>] [--register <path>]"
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
---

# /register-install — put the checker where the loci can reach it

You are running the **register-install** skill. It does one thing: it adds
`register-check` to this repository's dependencies, pinned to the tagged ref the
register names, and confirms the repository can run it.

**It owns nothing else.** It writes no gate configuration, wires no locus and
deploys no control. Every artefact belongs to the gate that owns its control;
this skill exists because the gates, the pre-commit hooks and the CI job all
*run* the checker, and none of them installs it.

**It is not a gate, and the thing it installs is not a skill.** The checker is
an ordinary executable that runs in CI with no Claude present. A skill may
install a gate and cannot be one.

**No control names this.** SUP-001, SUP-002 and SUP-003 are about lockfiles,
update proposals and frozen installs; the checker being present is a
precondition of all three being *checkable*, which is a different thing. So
nothing here writes an `ee-control:` stamp — a stamp names a control, and there
is no control to name. That is the reason, and it is not the same as forgetting
([ADR 0032](../../../../docs/adr/0032-the-checker-is-installed-from-a-tagged-ref.md)).

**Do not use when:**

- The repository *is* the checker. Here `uv run register-check` resolves because
  the project being run is the project being checked, and adding a dependency on
  itself is a cycle. Step 1 detects this and stops.
- You want to upgrade an existing pin. Re-run it: Step 3 replaces the pin it
  finds. That is the same command, not a different mode.
- There is no register to read. The address is the register's, not this skill's.

## Inputs

| Input | Required | Default | Description |
| ------- | ---------- | --------- | ------------- |
| `--repo <path>` | No | current directory | The repository to install into |
| `--register <path>` | No | `<repo>/controls.yaml` | The register to read the address from |

## Success criteria

1. The pin written is the register's `tools.register-check.install`, composed
   with the ecosystem's own spelling. No address, tag or grammar is written from
   this file.
2. The lockfile records it. A manifest edit no lockfile followed is a pin that
   resolves differently on the next machine.
3. `register-check --version` runs in the repository afterwards, through the
   package manager rather than off `PATH`.
4. Nothing was written before the plan was shown and confirmed.

---

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

## Step 1 — Pre-flight

Nothing is written in this phase.

### Read the address from the register

```bash
read -r REPOSITORY REF <<<"$(uv run --no-project --with pyyaml python -c '
import sys, yaml
install = yaml.safe_load(open(sys.argv[1]))["tools"]["register-check"].get("install") or {}
print(install.get("repository", ""), install.get("ref", ""))
' "$REGISTER")"
```

**Read through uv, not through `yq`.** This ran as `yq` until Phase 4 met a
container that had none — nothing in the devcontainer template installs one, and
nothing should: `yq` would be a tool this skill needs and no control names, so
no register pins it and nothing keeps it in step. uv is the one tool the whole
standard already depends on, `--with` fetches the parser for the length of one
command, and `--no-project` means this reads the register without touching an
environment the checker is not yet installed into.

**Do not fall back to `grep`.** The register comments these blocks, so a
line-offset extraction returns empty rather than failing — Phase 4 wrote exactly
that into the adoption guide and had to correct it. An extraction that quietly
yields nothing is worse than one that errors, which is why the check below is
for *absence* and stops.

If either is absent, **stop**. The register is older than contract 29 and does
not say where the checker comes from; say so and name the contract, rather than
guessing an address. A guessed address is the one failure mode this skill has
that nobody would notice — it would install *something*.

### Work out the ecosystem, from files

```bash
ls "$REPO"/pyproject.toml "$REPO"/package.json "$REPO"/go.mod 2>/dev/null
ls "$REPO"/uv.lock "$REPO"/poetry.lock "$REPO"/pdm.lock 2>/dev/null
```

Match what is present against `ecosystems.<name>.manifest` and
`.lockfiles` in the register. Never ask which ecosystem this is — a repository
that declares its way into one is a repository whose predicate was not
evaluated, which is the thing `applies_to` exists to prevent.

Then read two commands out of that ecosystem:

| State var | From |
| --- | --- |
| `GIT_DEPENDENCY` | `ecosystems.<eco>.git_dependency` |
| `ADD` | `ecosystems.<eco>.add_dev_dependency.<the lockfile present>` |

**If `git_dependency` is absent, stop and say so.** That ecosystem has no
spelling for a dependency on a git ref in this register, and inventing one is
worse than not having one: the wrong grammar fails at install time in the
adopter's repository rather than here. Today only `python` declares one, and
[ADR 0032](../../../../docs/adr/0032-the-checker-is-installed-from-a-tagged-ref.md)
§ The non-Python adopter is not solved says that is known and not an oversight.

### Compose the requirement

```text
GIT_DEPENDENCY with {package}=register-check, {repository}=$REPOSITORY, {ref}=$REF
```

For python that reads:

```text
register-check @ git+https://github.com/<owner>/<repo>@v<x.y.z>
```

**Do not write that string from this file.** It is shown here so a reader knows
what to expect, not so a skill can shortcut to it. Every field comes from the
register, and the ADR's whole point is that a fork, an internal mirror or a new
release changes the address without changing this skill.

### Is it already installed?

```bash
grep -n 'register-check' "$REPO"/pyproject.toml || echo ABSENT
```

Three states, and they are not the same:

- **Absent** — nothing to replace; this is an install.
- **Pinned to this ref** — nothing to do. Say so and stop at Step 4's verify.
  Re-running must be safe, and a no-op that reports success is not the same as a
  no-op that reports having done something.
- **Pinned to another ref** — this is an *upgrade*, and the plan says which ref
  it replaces. A reader who thinks they are installing and is in fact moving a
  version has been told the wrong thing.

### The one repository this does not run in

```bash
grep -n '^name = "register-check"' "$REPO"/pyproject.toml && echo SELF
```

If this repository *is* the checker, **stop**. It cannot depend on itself, and
the loci here already reach it through the project's own environment.

---

## Step 2 — Plan, and confirm once

Show what will change, then ask.

```text
register-install will add to <repo>:

  register-check @ git+<repository>@<ref>        (dev dependency)

  written by:  <ADD, with {package} substituted>
  recorded in: <the lockfile present>
  replacing:   <the ref currently pinned, or "nothing — this is a new install">
```

One **AskUserQuestion**. Options: **Install** / **Cancel**.

Say what the pin means, because it is the part a reader is entitled to weigh:
the checker will not move until this ref does, and moving it is a change to this
repository that someone reviews. A dependency that tracked a branch would change
under them between two runs of the same commit.

---

## Step 3 — Install

```bash
cd "$REPO" && <ADD, with {package} replaced by the composed requirement>
```

For a `uv.lock` repository that is `uv add --dev "register-check @ git+…@v…"`,
which writes the manifest **and** the lockfile in one call. If the ecosystem's
command writes only the manifest, run that ecosystem's lock command afterwards
and say that you did — a manifest edit no lockfile followed is a pin that
resolves differently on the next machine.

**On failure, show the package manager's output verbatim and stop.** The two
that happen are a tag that does not exist in that repository, and a repository
that is not reachable without a credential. Both are answers about the address
in the register, and paraphrasing them loses the only diagnosis available.

---

## Step 4 — Verify

```bash
cd "$REPO" && <the ecosystem's runner> register-check --version
```

Through the package manager — `uv run register-check` for uv — and never a bare
`register-check`, which resolves from `PATH` and would report success against
some other copy entirely ([ADR 0020](../../../../docs/adr/0020-a-locus-reaches-the-pinned-artefact.md)).

Then confirm the lockfile carries it:

```bash
grep -n 'register-check' "$REPO"/<lockfile> || echo "NOT LOCKED"
```

`NOT LOCKED` is a failure, not a warning. It is the state in which every locus
works on the machine that ran the install and on no other.

**Do not run the full audit here.** `register-check run` over a repository with
no gates deployed reports failures for every control, which reads as this skill
having broken something. `register-adopt` runs it at Step 1 as its starting
state, which is where that output means something.

---

## Output

**Installed:**

```text
register-install added register-check @ git+<repository>@<ref> to <repo>.
  written to:  <manifest>
  locked in:   <lockfile>
  verified:    <runner> register-check --version → <version>
Not committed.
```

**Already present:**

```text
register-install found register-check already pinned to <ref> in <repo>.
Nothing was written. Verified: <runner> register-check --version → <version>.
```

**Upgraded:**

```text
register-install moved register-check from <old ref> to <new ref> in <repo>.
```

**Stopped:**

```text
register-install wrote nothing: <the reason, verbatim>.
```

## Error handling

| Condition | Action |
| ----------- | -------- |
| The register has no `tools.register-check.install` | Stop. Name the contract the register declares and the contract this needs (29). Never guess an address |
| The ecosystem has no `git_dependency` | Stop. Say which ecosystem, and that no spelling for a git dependency exists for it in this register |
| No lockfile matches the ecosystem's list | Stop. There is nowhere to record the pin, and an unrecorded pin is not one |
| This repository *is* the checker | Stop. It cannot depend on itself |
| The package manager cannot resolve the ref | Stop and show its output. The tag is the register's claim, and it is wrong |
| Installed but not in the lockfile | Report a failure. A manifest-only pin resolves differently on the next machine |

## Idempotency

Re-running is safe and is how the pin is moved: the plan names the ref being
replaced, and installing the ref already present writes nothing. There is no
provenance stamp to refresh, because nothing here deploys a control.

## Standards

- Why a tagged git ref rather than a published package, and why this is a skill
  of its own: `${CLAUDE_SKILL_DIR}/README.md`
- The decision: `docs/adr/0032-the-checker-is-installed-from-a-tagged-ref.md`
- What an adopter must do that no skill can: `docs/08-adopting.md`
