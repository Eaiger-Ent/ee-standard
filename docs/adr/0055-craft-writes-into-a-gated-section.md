# ADR 0055: Craft Writes Into a Gated Section and Records Every Key

**Status:** Accepted
**Date:** 2026-09-07
**Revision:** 1

## Background

**The problem.** Craft's installer writes tool configuration, and every file it
writes is a file a control already gates.
`docs/craft/design.profiles.md` § The config surface establishes the four
locations: `pyproject.toml` §`tool.ruff.lint` and §`tool.mypy` for Python,
`eslint.config.js` and `tsconfig.json` §`compilerOptions` for React. All four are
named in `controls.yaml`'s `stacks:` block, which is what LNT-001 and TYP-001
read to find a repository's configuration. There is no fifth location: the
register names every place either mandated tool will look, so *Craft writes
somewhere a control is not watching* is not an option that exists.

**Two of those sections are not alike, and the difference is what makes this a
decision.** LNT-001 asserts that the linter is wired at three loci, pinned in
the lockfile, unsuppressed and stamped. It reads no key inside `[tool.ruff]` and
asserts nothing about which rules are selected —
`docs/craft/plan.md` opens on exactly that: *a repository selecting `E501` alone
passes it*. Rule selection is space the control deliberately leaves empty, and
filling it is the whole of what this workstream is for.

`[tool.mypy]` is not empty space. TYP-001's `typecheck-strict-and-blocking`
reads that section and asserts three things about its contents: that the
register's `strict_key` is truthy, that the `coverage_key` covers all
first-party source, and that no `[[tool.mypy.overrides]]` entry carries a
blanket override undoing strict. A Craft profile writing
`disallow_any_explicit` would be adding a fourth key to a section three of a
control's own checks already read.

**Underneath both sits a state this repository has no name for.** A craft rule
installed into a mandated tool makes that tool exit non-zero. The merge is
blocked, at the control's loci, under the control's name — and the rule appears
in neither register. That is already true of every ruff selector a Craft profile
would write; `[tool.mypy]` is only where it became visible, because that section
has a control reading it. Enforced, blocking, and unregistered is a third state
the model describes nowhere, and something invisible that changes a verdict is
the failure shape [ADR 0052](0052-a-profile-is-a-stack-and-a-strictness.md)
rejected a declared archetype for and
[ADR 0045](0045-a-gate-records-where-it-installed-a-tool.md) added a record to
prevent.

**The obvious escape is closed.**
[ADR 0051](0051-a-craft-rule-becomes-a-control-by-being-installed.md) says a
craft property becomes a control by being installed as one, with the installer
writing the `controls.yaml` entry, and its third precondition is that S3 has
measured it. `docs/craft/review.bench.md` § The four numbers records that S3's
C6 did **not** measure `disallow_any_explicit` — it could not, because the bench
configured no type checker. So the one key Craft contributes to type checking is
precisely a key ADR 0051 currently refuses to let cross, and *make it a control*
is not available as an answer.

## Alternatives Considered

### Option 1: Craft never writes a section a control gates

The workstream keeps clear of `controls.yaml`'s declared configuration
locations entirely.

**Pros:** the boundary is a bright line, nobody has to reason about which key
belongs to whom, and no control's configuration acquires a second writer.

**Cons:** there is nowhere left to write. `stacks:` names every config location
for both mandated tools in both stacks, and `[tool.ruff.lint] select` — the gap
this workstream was founded on — is inside LNT-001's gated file by construction.

**Rejected, because it does not restrict Craft, it abolishes it.** An option
whose effect is that the deliverable cannot be delivered is not a conservative
choice; it is the same outcome as abandoning the workstream, reached by a route
that sounds careful.

### Option 2: Craft writes freely, and enforcement under a control's name is treated as ordinary

The installer writes what a profile says, and the fact that a craft rule can
fail a build through a control's tool is accepted without further machinery.

**Pros:** simplest to build; it is what already happens wherever anyone edits a
lint configuration; no new record, no new discipline, and nothing for S5 to
implement beyond writing the files.

**Cons:** a developer whose build fails on a rule they did not choose has no way
to find out what turned it on. `register-check` will not tell them, because the
key is in no register; `controls.yaml` will not, for the same reason; and the
control whose name is on the failure did not assert it. It also leaves Craft
able to write `strict = false` or a blanket `[[tool.mypy.overrides]]` with
nothing but good intentions preventing it.

**Rejected.** It is invisible suppression inverted into invisible enforcement,
and this repository has twice decided that something noisy which runs beats
something silent which changes the answer.

### Option 3: Craft writes into a gated section, may not write a key the control asserts, and records every key it writes

Two rules rather than one: a restriction drawn from the register on *what* may
be written, and a record of what was.

**Pros:** it permits everything Craft actually needs — rule selection, and the
one mypy key — while making it structurally impossible for Craft to weaken a
control, because the keys that would weaken one are exactly the keys it may not
write. The restriction is derived from `stacks:` rather than listed in Craft's
code, so it satisfies [ADR 0018](0018-register-checker-boundary.md) without a
new exception. The record answers *whose rule is this* at the moment somebody
needs the answer.

**Cons:** it accepts a second writer to `pyproject.toml`, which `gate-quality`
also writes, and that needs a discipline neither has today. It leaves the
enforced-but-unregistered state in existence rather than removing it.

**Chosen.**

## Decision

**A Craft profile may write into a section a control gates. It may never write a
key that control asserts, and every key it does write is recorded.**

**Rule 1 — the keys Craft may not write are read from the register, not listed
here.** For each stack's gates, `controls.yaml` names them: the `strict_key`,
the `coverage_key`, and — where the tool has one — the override table
`typecheck-strict-and-blocking` reads. A Craft installer resolves that set from
`stacks:` at install time and refuses to write anything in it. Today that means
`strict` and `tool.mypy.files` for Python, `strict` and `include` for
TypeScript, and no key at all for either lint gate, which asserts wiring rather
than content. **Listing those names in Craft's code would be the checker-side
dictionary ADR 0018 was written about**, and it would go stale the first time a
register contract moved.

**Rule 2 — what Craft writes is recorded twice, in the two places the two
questions get asked.** The Craft register of
[ADR 0053](0053-the-craft-mapping-is-register-data.md) is the source: it says
what a profile *would* write, and it is where a reader asks *what does this
profile turn on*. A stamp in the repository records what was *actually* written,
naming the profile, its version and the keys it set, in the shape
[ADR 0038](0038-the-stamp-records-the-deployment-contract.md) already uses for a
gate — because a reader at a failing build asks a different question, *whose
rule is this*, and asks it of the repository rather than of a register they may
not have.

**This does not make a craft rule a control.** ADR 0051's route is unchanged and
its three preconditions still bind. A craft rule that blocks a merge through a
mandated tool remains a craft rule; the stamp is what stops it being an
anonymous one. Nothing in this record is a route to `controls.yaml`, and a
property that has not been measured by S3 does not acquire one by being
installed.

## Consequences

**Positive outcomes:**

- **Craft cannot weaken a control, by construction rather than by care.** The
  keys that would loosen LNT-001 or TYP-001 are precisely the keys rule 1
  forbids, so `variance: narrowing-only` is respected without a Craft installer
  having to reason about polarity at all.
- **A failing build has an author.** The stamp answers *what turned this on*,
  which is the question option 2 left a developer unable to ask.
- **The restriction cannot drift from the register.** It is resolved from
  `stacks:` at install time, so a register contract that adds a gated key adds it
  to Craft's forbidden set with no Craft change.
- **The type-checker question is settled in the direction the design needs.**
  `disallow_any_explicit` is not a key TYP-001 asserts, so a Python strictness
  level may set it, and `docs/craft/design.profiles.md` § The type checker's open
  question is closed.

**Trade-offs and risks:**

- **`pyproject.toml` acquires a second writer.** `gate-quality` deploys LNT-001
  and TYP-001 into the same file a Craft installer would write. Neither may
  clobber the other, and the merge discipline that guarantees it is S5's to
  build rather than something this record provides.
- **The enforced-but-unregistered state still exists.** This decision makes it
  visible; it does not remove it. Removing it would mean minting a control per
  craft rule, which ADR 0051's preconditions forbid for anything S3 has not
  measured, and which would put a hundred entries in a register whose every row
  is currently something that can fail a build.
- **`register-variance` will report most of what Craft writes as unclassified.**
  `variance.polarity` classifies two keys, `line_length` and `strict`. That is
  correct rather than a defect — the skill is meant to say which keys it could
  not classify — but it means a profile *downgrade* that removes a rule cannot
  be mechanically judged as loosening. Whether a strictness downgrade is a
  loosening under LNT-001 is a real question and it is not answered here.
- **A stamp is only as good as the thing that refreshes it.** This repository
  already knows that failure: `CLAUDE.md` warns never to fill a provenance stamp
  in by hand, and `register-check deployments` exists because a stamp behind its
  register is ordinary staleness. A Craft stamp inherits both the mechanism and
  the hazard.

## Related ADRs

- [ADR 0018](0018-register-checker-boundary.md) — the register/checker boundary,
  which is why rule 1 resolves its forbidden set from `stacks:` rather than
  naming keys in Craft's code.
- [ADR 0051](0051-a-craft-rule-becomes-a-control-by-being-installed.md) — the
  crossing to `controls.yaml` and its three preconditions, one of which closes
  the obvious escape from this problem.
- [ADR 0053](0053-the-craft-mapping-is-register-data.md) — the Craft register,
  which rule 2 makes the source of what a profile would write.
- [ADR 0038](0038-the-stamp-records-the-deployment-contract.md) — the stamp
  shape rule 2 reuses, and the reason a record of a deployment goes stale
  visibly.
- [ADR 0045](0045-a-gate-records-where-it-installed-a-tool.md) — a gate
  recording where it wrote, which is this decision's argument one workstream
  earlier.
- [ADR 0052](0052-a-profile-is-a-stack-and-a-strictness.md) — the rejection of a
  declared archetype on invisible-suppression grounds, which is the reasoning
  option 2 fails.
- [ADR 0009](0009-single-lint-definition.md) — one lint definition at three
  loci, and the `variance: narrowing-only` this decision keeps intact.
- [ADR 0010](0010-strict-typing-from-birth.md) — TYP-001's rationale, and the
  strict mode rule 1 forbids Craft to touch.

## References

- `controls.yaml` § `stacks:` — the gates, their config locations, `strict_key`
  and `coverage_key`, which rule 1 reads.
- `src/register_check/asserts_command.py` — `typecheck_strict_and_blocking` and
  `linter_wired_at_all_loci`, the two asserts whose difference this record turns
  on.
- `docs/craft/design.profiles.md` § The config surface — the four locations, and
  the open question this record closes.
- `docs/craft/review.bench.md` § The four numbers — S3 declining to measure
  `disallow_any_explicit`, which is why ADR 0051's route is unavailable.
