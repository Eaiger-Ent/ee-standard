# ADR 0032: Install the Checker From a Tagged Ref, by a Skill That Owns Nothing Else

**Status:** Accepted
**Date:** 2026-08-24
**Revision:** 1

## Background

**The problem.** There is no way to get the checker into a repository that is
not this one. `register-check` is a Python project in `src/`, it has never been
published anywhere, and nothing in the adoption guide tells an adopter where to
obtain it. The register comes closest, in a comment on `tools.register-check`:

> an adopter installs the checker as a dependency and reaches it however their
> package manager does

That sentence describes the *shape* of an answer and names no artefact. It has
been true and unactionable since register contract 13.

**Three things depend on it, and all three are Tier-1.**

| Where | What runs | What happens today in a repository that is not this one |
| --- | --- | --- |
| pre-commit | `register-check run --control SUP-003`, and BLD-001/DEV-001 | the hook fails: no such command |
| ci | the full audit, as the required status check CI-001 names | the job fails for the same reason |
| the adopter's own audit | `register-check` | nothing to run |

So an adopter who follows [`08-adopting.md`](../08-adopting.md) end to end
reaches § 4 — *Run the checker* — and stops. Phase 4 hits this at step 4 of five,
after the devcontainer, `project-init` and every gate have already run.

**Why it was not answered earlier.** Because this repository *is* the checker.
`uv run register-check` resolves here because the project being run is the
project being checked, and every locus this repository wires has therefore been
exercised against a checker that was already present. The gap is invisible from
inside, which is the shape of defect this project's review record keeps finding:
a property that holds for the author's environment and was never a property of
anything.

## Alternatives Considered

### 1. Publish to PyPI

**Rejected for now, and it is the likely successor.** `pip install
register-check==0.1.0` works from any ecosystem's Python tooling, needs no git,
resolves fast, and is what an outside adopter would expect.

It was rejected because it commits a public package name, and a stable one, to a
project whose first external adopter does not exist yet. Publishing is
[`05-promotion.md`](../05-promotion.md)'s work and Phase 6's; doing it here to
unblock Phase 4 would move the most irreversible step in the plan to the
earliest point at which it could possibly be taken. Nothing in this decision
prevents it later — a tagged ref and a published package are the same artefact
addressed two ways.

### 2. A release artefact with a published checksum

**Rejected, reluctantly.** This is the shape this repository trusts most, and it
already uses it twice: `setup.sh` installs uv and gitleaks from pinned release
tarballs verified against a published sha256, and
[`03-devcontainer.md`](../03-devcontainer.md)'s preference ladder puts it above
everything else.

It needs a release process that does not exist: a build, an attached wheel, a
published digest, and something that keeps all three in step. That is real work
whose value is defence against a compromised source — and the source here is
this repository, over HTTPS, at an immutable tag. The threat that ladder is
about is a third party's release; this is our own.

### 3. Vendor a copy into each adopting repository

**Rejected outright.** A second copy of the checker in every repository, drifting
from the register it reads. This is theme T-2 with extra steps.

### 4. `uv tool install` onto `PATH`

**Rejected as the primary route.** It works for a repository that is not a Python
project, which is a real future need — and it puts the checker on `PATH`, which
[ADR 0020](0020-a-locus-reaches-the-pinned-artefact.md) measured as the way a
locus reaches something other than the pinned artefact. Where a lockfile can
hold the pin, it should.

## Decision

**We will install the checker as a dependency pinned to a tagged ref of this
repository, placed by a new skill, `register-install`, which owns nothing else.**

Two halves, decided separately because they fail separately.

### The artefact: a tagged git ref

```text
register-check @ git+https://github.com/Eaiger-Ent/ee-standard@v0.1.0
```

- **Public, so no credential.** [ADR 0014](0014-satisfying-remote-locus-controls.md)
  makes this repository public; the install needs nothing an adopter has to be
  granted. That is a load-bearing dependency: taking this repository private
  breaks every adopter's install, and would have to be treated as such.
- **A tag, never a branch or a bare URL.** An unpinned git dependency resolves
  to whatever the default branch says today, which is the same defect as a
  floating image tag (DEV-001) and a floating action ref (SUP-003). The tag is a
  pin and is read as one.
- **The register names where it comes from.** A fork or an internal mirror is a
  reasonable thing for a repository to differ on, so by
  [ADR 0018](0018-register-checker-boundary.md) the source belongs in the
  register — in the shape `tools.<tool>` already uses for a fetched artefact —
  and the skill writes what it reads there. Whether that is a new `source` value
  or a field on the existing entry is settled by the implementing slice; what is
  decided here is that it is not hard-coded in the skill.

### The owner: a new skill

`register-install` places and pins the dependency and does nothing else. It is
runnable on its own, and `register-adopt` dispatches it **first**, before any
gate.

Three candidates were considered for the job and two were rejected:

- **`register-adopt`'s pre-flight.** Rejected because the dispatcher *verifies
  through* the checker — every gate it dispatches ends with
  `register-check run --control <ID>`. A step that installs the instrument it
  then measures with belongs on its own, where it can be run, re-run and
  reasoned about without the plan around it. It also strands anyone deploying a
  single gate: `gate-secrets` alone needs the checker as much as the whole
  family does.
- **`gate-supply-chain`.** Rejected because a gate writes the artefacts its
  controls name, and no control names *the checker is installed*. SUP-001,
  SUP-002 and SUP-003 are about lockfiles, update proposals and frozen installs;
  the checker being present is a precondition of all three being *checkable*,
  which is a different thing. A gate writing something no control names is the
  drift this repository watches for.

**This does not make the checker a skill.** `register-install` installs a binary
and stops; the binary is what runs at every locus, with no Claude present.
Enforcement is never Claude, and a skill that installs a gate is still not one.

## Consequences

### A release-tagging discipline has to exist

This repository has **no tags today** (`git tag` is empty). The decision makes a
tag the thing an adopter pins, so a tag has to exist and has to mean something:
`v0.1.0` matching `pyproject.toml`'s `version`, cut deliberately rather than
whenever someone remembers. That is new work this ADR creates, and it is the
part most likely to be skipped, because the first install will work against a
tag cut by hand and nothing will complain until the second one is needed.

### Dependency-update proposals are an open question

SUP-002 requires a bot that proposes dependency updates, and this repository
already runs both Dependabot and Renovate. Whether either proposes a bump for a
`git+https` dependency pinned to a tag is **not verified**, and is recorded as
unverified rather than assumed. If neither does, an adopter's checker pin rots
at a known version — a different failure from an unpinned one and not a better
one, in the words `03-devcontainer.md` already uses about image pins. Resolving
it is Phase 5's staleness work, where it belongs.

### The non-Python adopter is not solved

A consumer repository that is not a Python project cannot put a Python package
in its lockfile, and `uv tool install` — rejected above as the primary route —
becomes the only remaining one, with the `PATH` hazard ADR 0020 measured. Phase
4's consumer repository is Python + uv, so this decision is sufficient for it
and does not pretend to be general. The first non-Python adopter reopens this.

### Phase 4 gains a step, and the guide gains a section

`08-adopting.md` gains the install as its own step, before § 4 rather than
inside it, because a checker that is not installed is not a checker that reports
`SKIPPED`. Phase 4's first criterion — *every step the consumer repo needed is in
the guide before the criterion below is judged* — is what that has to satisfy.

## Related ADRs

- [ADR 0031: Name the Plugin and the Checker for the Register](0031-the-plugin-is-named-for-the-register.md)
  — names `register-install` and `register-check`. This decision is why that one
  could not wait: the skill would otherwise be built under a name already known
  to be wrong.
- [ADR 0018: The Register–Checker Boundary](0018-register-checker-boundary.md)
  — why the install source lives in the register rather than in the skill.
- [ADR 0020: A Locus Reaches the Pinned Artefact](0020-a-locus-reaches-the-pinned-artefact.md)
  — why a lockfile dependency is preferred to a tool on `PATH`.
- [ADR 0014: Satisfying Remote-Locus Controls](0014-satisfying-remote-locus-controls.md)
  — this repository is public, which is what makes an unauthenticated install
  possible and what this decision now depends on.

## References

- [uv — dependency sources: git](https://docs.astral.sh/uv/concepts/projects/dependencies/#git)
  — the `git+https://…@<tag>` form and how a tag is recorded in `uv.lock`.
- [PEP 440 — direct references](https://peps.python.org/pep-0440/#direct-references)
  — the `name @ url` spelling this decision writes, and its exclusion from
  published indexes, which is why option 1 remains a separate step rather than a
  consequence of this one.
