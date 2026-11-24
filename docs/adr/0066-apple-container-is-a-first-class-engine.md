# ADR 0066: Apple `container` Is a First-Class Container Engine

**Status:** Accepted
**Date:** 2026-11-23
**Supersedes:** [ADR 0065: Ship the Apple `container` Route to Adopters Now](archive/0065-the-adopt-route-accepts-either-runtime-now.md)
**Revision:** 1

## Background

**The question.** [ADR 0065](archive/0065-the-adopt-route-accepts-either-runtime-now.md)
shipped Apple's [`container`](https://github.com/apple/container) to adopters
beside Docker. It still treated it as the second of two engines in three ways:

1. **Nothing in the register named it.** The `devcontainer` CLI that the
   launcher runs was pinned only in `package-lock.json` files. The engine an
   adopter is steered to on an Apple silicon Mac rested on a version no
   register entry named, and a deleted lock file failed nothing until the
   launcher refused on the host.
2. **Nothing reported which launcher a repository held.** ADR 0064 decided
   `register-check deployments` would not track it, so a launcher fix reached an
   adopter only if they happened to look.
3. **Moving to it was optional, and it was evidence-gated.** ADR 0065 kept the
   move for an existing adopter as an optional step, and the five Phase 15 runs
   as evidence still to come.

The template also stated no resource floor. On Apple `container`, a container
that asks for nothing gets 1 GiB (Phase 15 Run A,
[`21-phase-15-runbook.md`](../21-phase-15-runbook.md)), which is the engine
working as designed and the template not asking.

**What happened on 2026-11-23.** The owner reported that Apple `container` is
working well in use. They asked for Run B, the second person on a second Mac,
to be discounted because no second operator is available, and for Apple
`container` to become a first-class engine, including in the register.

**The constraint that does not change.** `devcontainer.json` keeps one reader.
The launcher reads what the pinned CLI resolved, never the file, and refuses by
name a setting it cannot reproduce ([ADR 0063](0063-apple-container-runs-what-the-cli-resolved.md)).
No control's `rung`, `verify` or `applies_to` changes.

## Alternatives Considered

### Option 1: Keep ADR 0065

Leave the CLI pin out of the register, the launcher untracked, and Run B open.

**Pros:** No register contract bump, and no adopter has to move.

**Cons:** Phase 15 cannot close without a second operator nobody can supply.
The engine most new adopters on a Mac now get is the one the register says
nothing about.

### Option 2: First class in the documents only

Retire the "second runtime" wording, write the migration, waive Run B, and
leave the register alone.

**Pros:** No checker change and no contract bump.

**Cons:** The two gaps above remain. A first-class engine whose one pinned tool
and one moving part nothing checks is first class in prose only. This
repository exists to refuse that.

### Option 3: First class in the register and the report

Do Option 2, add the CLI to `tools:`, and make `register-check deployments`
report the launcher.

**Pros:** The CLI pin is a register fact like every other locus's tool, held by
`tool_versions_match_register`. An adopter learns that their launcher is behind
the plugin's from the same report that tells them a gate is.

**Cons:** A contract bump that an existing adopter cannot take without adding
the launcher's files. The move stops being optional for anyone who takes the
new register.

## Decision

We will take **Option 3**. ADR 0065's points 1 to 3 stand. Its points 4 and 5
change as follows.

**1. Both engines are first class.** Apple `container` is the default on an
Apple silicon Mac running macOS 26 or later, in a terminal and `claude`.
Docker is the engine for an Intel Mac, an older macOS, and VS Code's
**Reopen in Container**, which needs Docker. The documents call neither one
"the second". Stage 0 still asks the person to confirm the engine, with Apple
`container` the default when both answer.

**2. The CLI pin is a register fact.** `controls.yaml` `tools:` gains
`devcontainer-cli`, `source: lockfile`, with the lock file
`.devcontainer/package-lock.json` and the invocation
`.devcontainer/node_modules/.bin/devcontainer`. This repository moves its own
pin there from the root, so that this repository and the template agree. `lockfile` is
not a field `register-check publish` may vary, so the published register
describes an adopter only if both are the same. `register_contract` becomes 39.

**3. `register-check deployments` reports the launcher.** It compares
`.devcontainer/bin/container-session.mjs` with the installed plugin's template
copy and reports `CURRENT`, `DIFFERS` or `ABSENT`. Like a gate's staleness
([ADR 0038](0038-the-stamp-records-the-deployment-contract.md)), this is reported and
never enforced, so it sets no exit code. A plugin that ships no launcher, or a
repository with no devcontainer, gets no line. This reverses ADR 0064's "does
not track the launcher".

**4. The move is part of contract 39.** An existing adopter who takes contract
39 adds the three files UPGRADING.md names. With the CLI pin in `tools:`,
`tool_versions_match_register` fails a repository whose
`.devcontainer/package-lock.json` is untracked. Adding the files does not change
which engine the repository runs on, because Docker keeps working, and no tool
writes into the adopter's `.devcontainer/`. The adopter copies the files. This
replaces the "optional" in ADR 0065 point 4.

**5. The template states a resource floor:** `--cpus 4 --memory 4g` in
`runArgs`. On Apple `container` it sizes the container. On Docker it bounds the
container inside Docker Desktop's VM. Four of each, not this repository's
eight, because Docker refuses a container that asks for more CPUs than its VM
has, and a default should fit a small Mac. An adopter whose build needs more
raises both.

**6. Run B and Run E's second half are waived, not passed.** Both need a
second person, and no second person on a second Mac is available. Each waiver
is recorded in the build plan and the run sheet, under its own name, and does
not count as a result. Run E's criterion closes on its first half, E1, in
which the author follows `UPGRADING.md`'s step and corrects it. Runs C, D and E1
continue as evidence. A run that fails re-opens the question in a new ADR.

## Consequences

**Positive outcomes:**

- The register names every tool the Apple `container` engine depends on, and
  CI fails a repository that loses its pin.
- An adopter learns that their launcher is behind from `register-check
  deployments`, which they already run.
- An adopter on Apple `container` gets 4 GB rather than 1 GiB.
- Phase 15 can close without a second operator.

**Trade-offs and risks:**

- Contract 39 obliges an adopter to add three files to move to it, including an
  adopter who never uses Apple `container`.
- The engine rests on one operator's runs on one Mac. Run B's waiver means no
  second operator has followed the run sheet, so a gap that only a different
  operator or Mac would have hit can reach adopters first.
- `.devcontainer/package-lock.json` is a new npm directory, which a Dependabot
  entry at `/` never reaches. `gate-supply-chain` contract 7 writes an entry
  per lockfile directory, so an adopter has proposals for the CLI only after
  re-running that gate.
- `init=/sbin/vminitd` remains Apple's implementation detail (ADR 0065).
- The ee-skills copy of `control-register` changes only through an incubator
  amendment (ADRs 0042, 0043, 0057, 0060). Until one ships, an adopter on the
  marketplace plugin has no template launcher to copy. `deployments` then
  prints no launcher line, because there is nothing to compare against.

**What this ADR does not change.** No control's `rung`, `verify` or
`applies_to`. ADR 0063's launcher, refusal rule and parent mount stand. VS Code
stays on Docker.

## Related ADRs

- [ADR 0065](archive/0065-the-adopt-route-accepts-either-runtime-now.md):
  superseded. Its points 1 to 3 stand here, and points 4 and 5 change.
- [ADR 0064](archive/0064-an-adopter-may-run-its-devcontainer-on-apple-container.md):
  superseded by ADR 0065. Its "does not track the launcher" is reversed here.
- [ADR 0063](0063-apple-container-runs-what-the-cli-resolved.md): the launcher
  and its refusal rule.
- [ADR 0018](0018-register-checker-boundary.md): why the CLI's lock file is a
  register fact and the launcher's path is the checker's.
- [ADR 0038](0038-the-stamp-records-the-deployment-contract.md): reported, never
  enforced.
- [ADR 0026](0026-an-adr-stands-on-its-own.md): why a change to ADR 0065's
  decision is a new ADR.

## References

- [`21-phase-15-runbook.md`](../21-phase-15-runbook.md): Run A's record, Run B's
  waiver, and the runs still to come.
- [`06-devcontainer-setup.md`](../06-devcontainer-setup.md) § 1: both engines.
- [`UPGRADING.md`](../../UPGRADING.md): the step contract 39 requires.
- [apple/container](https://github.com/apple/container).
