# ADR 0065: Ship the Apple `container` Route to Adopters Now

**Status:** Accepted
**Date:** 2026-11-23
**Supersedes:** [ADR 0064: An Adopter May Run Its Devcontainer on Apple `container`](archive/0064-an-adopter-may-run-its-devcontainer-on-apple-container.md)
**Revision:** 1

## Background

**The question.** [ADR 0064](archive/0064-an-adopter-may-run-its-devcontainer-on-apple-container.md)
decided that an adopted repository may run its devcontainer on Apple's
[`container`](https://github.com/apple/container) instead of Docker. It also
held the change back: nothing reached the template or the adopt scripts until
five evidence criteria in `docs/04-build-plan.md` § Phase 15 were ticked. It
said that if the criteria could not be met as written, the ADR is superseded
rather than the criteria softened. Should the route ship before the five runs
finish?

**What happened on 2026-11-23.** The owner ran `adopt.sh` (v0.11.1) on a Mac
with Apple `container` and no Docker. Stage 0 stopped on two lines:

```text
✗ Docker — not on PATH  → START-HERE.md § B
✗ docker info fails — Docker Desktop is not running  → START-HERE.md § A
```

Every other tool passed. The owner does not want an adopter to need Docker, and
asked for stage 0 to fail only when neither runtime is there, and to ask the
person to confirm the runtime it found.

**Where the evidence stands.** Of the five criteria, Run A (an adopted
repository, `ee-standard-consumer`, on Apple `container`) reached a `claude`
session with every `check-auth.sh` line ✓. Its criterion stays open only on a
`register-check` result that comes from the archived repository's settings, not
from the runtime. Run D's baseline is the output above. Runs B, C and E have
not been run. `docs/21-phase-15-runbook.md` holds each record.

**The constraint that does not change.** `devcontainer.json` keeps one reader.
The launcher reads what the pinned CLI resolved, never the file, and refuses by
name a setting it cannot reproduce (ADR 0063). No control changes.

## Alternatives Considered

### Option 1: Keep ADR 0064's gate

Wait for Runs B to E before anything ships.

**Pros:** The route reaches adopters with the evidence ADR 0064 asked for.

**Cons:** An adopter without Docker stays blocked at stage 0 until a second
person on a second Mac is found for Run B. The scripts that Run D tests do not
exist until they are written, so the gate also holds back its own evidence.

### Option 2: Change only stage 0

Let stage 0 accept Apple `container`, and change nothing else.

**Pros:** The smallest change.

**Cons:** A person who chooses Apple `container` passes stage 0, and then has
no launcher to build with. The template carries none, so the route fails later
and further from its cause.

### Option 3: Ship ADR 0064's decision now, with the runs as follow-up evidence

Ship the launcher in the template, and make the adopt scripts accept either
runtime and ask which to use. The five runs continue, and their results can
re-open this decision.

**Pros:** An adopter needs no Docker from the next release. Run D tests the
shipped scripts, not a stand-in.

**Cons:** Adopters take a route that only one person has run, on one Mac. A
fault that Run B, C or E would have found reaches them first.

## Decision

We will take **Option 3**. ADR 0064's points 1 to 4 stand, with the two changes
below, and its point 5, the release gate, is withdrawn.

**1. Either runtime will do, and the person confirms the one used.** Stage 0
(`00-tools.sh`) passes when Docker answers `docker info` or Apple `container`
answers `container system status`, and fails only when neither answers. It
names each runtime that answers. The guided route (`guided.sh`) then asks. With
one runtime, it asks the person to confirm its use. With both, it asks which,
and Apple `container` is the default answer. A no stops the route with nothing
changed. This replaces ADR 0064's "is told which was chosen".

**2. The template carries the launcher and its CLI pin**, as ADR 0064 point 2
decided: `bin/container-session.mjs`, byte-identical to the tested one, and
`.devcontainer/package.json` with its lock file pinning `@devcontainers/cli` at
the version the repository root pins. A test holds both to the tested copies.

**3. The scripts verify the runtime in use**, as ADR 0064 point 3 decided.
Stage 0 reads Docker's memory floor as before. Apple `container` has no VM to
size, because each container gets what `runArgs` asks for. Stage 3
(`30-container.sh`) asks each runtime that answers whether this folder's
container is running. `inside_container()` also recognises Apple's init on the
kernel's boot line (`init=/sbin/vminitd`), which Run A's container showed.

**4. Who each runtime is for, and an existing adopter's move**, as ADR 0064
points 1 and 4 decided. Apple `container` is for an Apple silicon Mac on macOS
26 or later, in a terminal and `claude`. Docker is for everything else and for
VS Code. The move for an existing adopter stays a documented, optional step.
Until Run E writes it, `START-HERE.md` § 4 names the three files to copy.

**5. The five runs continue as evidence, not as a gate.** A run that fails is a
finding against this decision. It re-opens the question in a new ADR, and is
not edited away.

## Consequences

**Positive outcomes:**

- A new adopter on a Mac with Apple `container` needs no Docker.
- Run D now tests the scripts that ship.
- The person chooses the runtime, so a Mac with both is never switched without
  being asked.

**Trade-offs and risks:**

- The route ships on one person's run, on one Mac. Runs B, C and E may find
  faults after adopters have the route.
- The template's lack of resource flags is untested on Apple `container`.
  Its default VM is 1 GiB and 4 CPUs (spike § S4), and Run A did not record
  the size it ran at.
- `init=/sbin/vminitd` is Apple's implementation detail, and a `container`
  release could rename it.
- The template is copied once, so a launcher fix reaches an adopter only if
  they take it. Nothing reports which copy an adopter holds.
- The ee-skills copy of `control-register` changes only through an incubator
  amendment (ADRs 0042, 0043, 0057, 0060). Until one ships, an adopter who
  installs the plugin from ee-skills gets the template without the launcher.

**What this ADR does not change.** No control, `rung`, `verify` or
`applies_to`, and no `register_contract` bump. ADR 0063's launcher, refusal
rule and parent mount stand.

## Related ADRs

- [ADR 0064](archive/0064-an-adopter-may-run-its-devcontainer-on-apple-container.md)
  — superseded. Its points 1 to 4 stand here with the changes above.
- [ADR 0063](0063-apple-container-runs-what-the-cli-resolved.md) — the launcher
  and its refusal rule.
- [ADR 0049](0049-the-adoption-route-is-executable.md) — the scripts detect,
  and `guided.sh` acts.
- [ADR 0037](0037-the-template-is-the-whole-devcontainer-step.md) — why the
  launcher must be in the template to reach an adopter.
- [ADR 0026](0026-an-adr-stands-on-its-own.md) — why a change to the gate is a
  new ADR.

## References

- [`21-phase-15-runbook.md`](../21-phase-15-runbook.md) — Run A's record, and
  the runs still to come.
- [`20-apple-container-spike.md`](../20-apple-container-spike.md) — the spike.
- [`06-devcontainer-setup.md`](../06-devcontainer-setup.md) § 1 — the
  launcher's commands and limits.
- [apple/container](https://github.com/apple/container).
