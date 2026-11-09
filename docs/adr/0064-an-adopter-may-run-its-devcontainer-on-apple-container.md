# ADR 0064: An Adopter May Run Its Devcontainer on Apple `container`

**Status:** Accepted
**Date:** 2026-11-09
**Revision:** 1

## Background

**The question.** [ADR 0063](0063-apple-container-runs-what-the-cli-resolved.md)
accepted Apple's [`container`](https://github.com/apple/container) as a second
runtime for *this* repository, through a host launcher,
`.devcontainer/bin/container-session.mjs`. It deliberately stopped there:

> **Scope: this repository only.** The adopter template is not changed. Under
> ADR 0037 the template is the whole devcontainer step for an adopter, and
> shipping a second runtime there is a separate decision. It should follow
> evidence from this repository's own use, not precede it.

This is that separate decision. The aim of Phase 14 was to prove the route here
so that it could be offered to every repository that adopts the standard. Should
an adopted repository be able to choose Apple `container` instead of Docker for
a terminal and `claude` session, and if so, what must change for that to be true
of the repository and not only of the document?

**Where the standard stands today.** Every adopter-facing artefact assumes
Docker, and
[`08-adopting.md`](../08-adopting.md) § 2.0a says so in terms: *"Apple
`container` is not an adopter's runtime yet … the table above is complete."*
Concretely:

| Artefact | Docker assumption |
| --- | --- |
| `START-HERE.md`, `README.md`, `HOW-IT-WORKS.md` | "A Mac with Docker" is the stated cost; Docker Desktop is the only prerequisite row |
| `templates/adopt/00-tools.sh` | `require_tool docker` and `docker info` must succeed, and Docker's memory is read from `docker info`. A Mac with only `container` fails stage 0 |
| `templates/adopt/30-container.sh` | Looks for a running container with `docker ps` and never asks `container list` |
| `templates/adopt/_lib.sh` | `inside_container()` detects `/.dockerenv`, `REMOTE_CONTAINERS` and `CODESPACES`. Whether an Apple container sets any of these is **unverified** |
| `templates/devcontainer/` | No launcher, no `@devcontainers/cli` pin, no Node manifest |
| `UPGRADING.md` | "Your devcontainer … was copied once, at adoption, and is yours now." No step moves a repository to another runtime |

**What exists to build on, and what does not.** The spike and the launcher ran
on one Mac, once, on 2026-11-08, against *this* repository's `devcontainer.json`
(`container` 1.7.1, `@devcontainers/cli` 0.90.0). The launcher's refusal rule
was written and tested against that file. It has not been run against a
`devcontainer.json` derived from the adopter template and edited by an adopter,
on a second machine, or by a second person. ADR 0063 asked for evidence from use
before widening scope. A day of use is not that evidence, and this ADR records
the gap rather than treating the spike as the answer to a larger question.

**The constraint that does not change.** `devcontainer.json` keeps one reader.
The launcher reads what the pinned CLI resolved, never the file, and refuses a
setting it cannot reproduce. No control changes: DEV-001 and BLD-001 read files,
and CI never reads `devcontainer.json` (ADR 0063).

## Alternatives Considered

### Option 1: Keep the scope. Apple `container` stays this repository's own

**Pros:** Nothing new to ship, support or keep in step. The launcher is free to
change without an adopter depending on it.

**Cons:** It discards the purpose Phase 14 was run for. It also leaves the
standard's own repository as the one place its adopters' route is not the route
it uses, which is the divergence `docs/04-build-plan.md` § The one place this
repository does not do what it asks of everyone else exists to keep small.

### Option 2: Document a manual copy of the launcher; ship nothing

Tell an adopter to copy `container-session.mjs` and the CLI pin from the
standard's repository by hand.

**Pros:** No plugin change, no release set.

**Cons:** A second copy of the launcher in every adopter, free to drift from the
one that is tested, with no mechanism to say which version a repository holds.
That is the duplication this repository exists to prevent, moved into other
people's repositories where nothing here can see it.

### Option 3: Ship the launcher in the template, make the scripts runtime-aware, document a migration

The template carries the launcher and the CLI pin. `adopt.sh`'s host stage
accepts either runtime. `UPGRADING.md` gains an optional step for a repository
adopted before this change. Docker stays the default and the route VS Code uses.

**Pros:** One tested launcher, shipped through the same channel as every other
template file (ADR 0037). A new adopter chooses at stage 0 and the scripts
verify whichever they chose. An existing adopter has a written route that ends
in a check, not a hope.

**Cons:** The standard now owns a runtime adapter for repositories it does not
control, whose `devcontainer.json` differ from this one. The refusal rule turns
most of that into a loud error, which is also a support burden.

## Decision

We will take **Option 3**, and accept it on the evidence that exists: the Phase
14 spike. That is a deliberate choice to decide before the adopter-shaped
evidence exists, not a claim that the spike supplies it. The risk is taken
knowingly, and the release is gated instead (point 5): the decision is binding
now, and **nothing reaches the template or an adopter until the criteria below
are ticked** in a new build-plan phase.

**1. Apple `container` is the default on a Mac that can run it. Docker remains
the route for everything else.** An Apple silicon Mac on macOS 26 or later is
steered to Apple `container` for a terminal and `claude` session. Docker is the
route for an Intel Mac, an older macOS, or any repository edited through VS Code,
which stays on Docker. A host that can run both is told, at stage 0, which was
chosen and how to choose the other. `START-HERE.md`, `README.md` and
`HOW-IT-WORKS.md` change "a Mac with Docker" to name both, and say which applies
to whom.

**2. The template carries the launcher and its CLI pin.** The adopter template
gains `bin/container-session.mjs`. The pinned `devcontainer` CLI goes in
`.devcontainer/package.json` and its lock file, **not** the repository root.
An adopter's root `package.json` is theirs, and many adopters have none. The
launcher invokes the CLI by path (ADR 0020) and the template's lock file pins it,
so no locus names a version of its own.

**3. The adopt scripts accept either runtime and verify the one in use.**
`00-tools.sh` requires *a* runtime: Docker answering `docker info`, or
`container system status` answering, and reads the resource floor from
whichever. `30-container.sh` asks that runtime whether a container for this
folder is running. `inside_container()` is checked against an Apple container
before it is trusted. A host with both is told which was used.

**4. An existing adopter's move is a documented, optional upgrade step, with no
tooling behind it.** It is **not** automatic, and no skill or script performs it:
a tool that writes into the adopter's `.devcontainer/` would write into a
directory the adopter owns. `UPGRADING.md` already says an upgrade never re-copies the
devcontainer, and this keeps that true. The step lists the files to copy from
the tag they upgraded to, the host prerequisites, and a check that ends in the
launcher's own `check-auth.sh` table. A repository whose `devcontainer.json` the
launcher refuses stays on Docker, and the refusal names what it could not
reproduce.

**5. The release is gated on five criteria**, each a criterion in a new
`docs/04-build-plan.md` phase. None of the template, adopt-script or
upgrade-guide changes ships until all five are ticked, and an unticked one
re-opens the question rather than being waived:

- the launcher runs a repository adopted from the template, not this one, to a
  `claude` session where `check-auth.sh` passes;
- the same, on a second Mac, by someone other than the author;
- the refusal rule is shown against an adopter-shaped `devcontainer.json` with at
  least one key the launcher does not handle, and the refusal names it;
- `adopt.sh` stage 0 and stage 3 pass on a host with `container` and no Docker;
- the migration step, followed literally on a repository adopted at the previous
  release, ends green.

### Decided at acceptance

These were open in the first draft and were decided on 2026-11-09. A later ADR
may reverse any of them without the rest falling:

- **The CLI pin lives in `.devcontainer/package.json`,** with its own lock file,
  not the repository root. The cost is a second place to run `npm ci`. ADR 0063
  left open whether the pin belongs in `controls.yaml` `tools:`, and that stays
  open here.
- **The launcher's test does not ship.** `tests/test_container_session.py` stays
  in this repository, which tests the launcher it ships. An adopter's copy is
  unchecked by anything they own, and is held to the tested one by being
  byte-identical.
- **`register-check deployments` does not track the launcher.** A launcher fix
  reaches an adopter only if they take it, which Trade-offs states.
- **No second reader was required.** As with ADR 0063, the decision is accepted
  on one person's authority.

**Accepted 2026-11-09**, on one person's authority and with no second reader,
with the four choices above as recorded. Acceptance does not authorise the
template, adopt-script or documentation changes: those wait for point 5.

## Consequences

**Positive outcomes:**

- A repository adopting the standard is not required to run Docker Desktop to
  work in a terminal.
- This repository stops being the only one whose route differs from the one it
  publishes.
- A divergence between runtimes still shows up as a refused key rather than a
  quietly different container (ADR 0063).

**Trade-offs and risks:**

- The standard owns a runtime adapter that runs against configurations it did
  not write. ADR 0063's residual risk, that a change in what an *accepted* key
  means passes silently, now applies to every adopter.
- The template is copied once, so a launcher fix reaches an adopter only if they
  take it. The standard has no mechanism to push one or to see which copy an
  adopter holds, and this ADR does not add one.
- The decision is taken on the spike alone. If the five criteria find the
  launcher does not hold for an adopter-shaped repository, this ADR is
  superseded rather than the criteria softened.
- Stage 0 of `adopt.sh` becomes two-pathed, and each path needs a test. A
  Docker-only regression there would affect every new adopter.
- A template change is an upstream amendment through the incubator, then a
  release set (ADRs 0042, 0043, 0057, 0060), so reaching adopters takes as long
  as that does. `plugins/control-register/templates/` is not edited here before
  then.
- Support: "it works on Docker and not on Apple" becomes a question the standard
  answers, with a host it cannot see.

**What this ADR does not change.** No control, `rung`, `verify` or `applies_to`.
No `register_contract` bump is implied. If the template change alters a file a
gate reads, the owning gate's contract question is answered at that time, not
assumed here. ADR 0063's decision, the launcher, its refusal rule, the CLI pin
and the parent mount, stands; only its **Scope** paragraph is overtaken, and on
acceptance ADR 0063 carries a dated amendment pointing here, as ADR 0024 did for
0005 and 0012.

## Related ADRs

- [ADR 0063](0063-apple-container-runs-what-the-cli-resolved.md) — the decision
  whose scope paragraph this one overtakes.
- [ADR 0037](0037-the-template-is-the-whole-devcontainer-step.md) — why the
  template is the whole devcontainer step, and so where a second runtime must
  land to reach an adopter.
- [ADR 0020](0020-a-locus-reaches-the-pinned-artefact.md) — the launcher calls
  the pinned CLI by path.
- [ADR 0018](0018-register-checker-boundary.md) — the test the CLI pin's
  location is measured against.
- [ADR 0026](0026-an-adr-stands-on-its-own.md) — why this is a new ADR and not an
  edit to 0063.

## References

- [`20-apple-container-spike.md`](../20-apple-container-spike.md) — the spike
  and the launcher's pass record, 2026-11-08.
- [`08-adopting.md`](../08-adopting.md) § 2.0a — the adopter's host/container
  split, which names Apple `container` as not yet theirs.
- [`UPGRADING.md`](../../UPGRADING.md) § What an upgrade does not touch.
- [apple/container](https://github.com/apple/container).
