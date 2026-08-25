# ADR 0031: Name the Plugin and the Checker for the Register

**Status:** Accepted
**Date:** 2026-08-24
**Revision:** 2

## Background

**The problem.** Everything this project ships is named after "the standard",
and that word tells a reader nothing they can act on. The plugin is
`ee-standard`, the checker is `standard-check`, the dispatcher is
`standard-adopt`, and Phase 5's classifier is planned as `standard-variance`.
None of those names says what the thing governs, and *standard* is one of the
most overloaded words available: a coding standard, a style guide, an ISO
document, a standard library, the standard edition of a product.

It becomes a real cost at the moment the plugin is submitted to the ee-skills
marketplace, because the name is the whole of what a reader sees first. Its
siblings there each name their subject:

| Plugin | What the name says |
| --- | --- |
| `lint-md` | it lints markdown |
| `project-init` | it initialises a project |
| `devcontainer-check` | it checks a devcontainer |
| `readme-check` | it checks a README |
| `ee-standard` | — |

Two things are wrong rather than one. The name says nothing, **and** it is
off-convention: no other plugin in that marketplace carries an `ee-` prefix, so
the prefix reads as a namespace collision being avoided rather than as
information.

**We already have a better word, and it is the one this repository is built
around.** `CLAUDE.md` § The core invariant states it: *a register entry in
`controls.yaml` **is** the control, not documentation of one. Every other
artefact — CI workflow, pre-commit config, gate skill, devcontainer, checker —
derives from the register rather than restating it.* The register is the thing
that decides. Everything shipped is either something that writes what the
register requires, or something that reads back whether it holds.

**Why now rather than at promotion.** Three things are about to be built on top
of the current names: a skill that installs the checker
([ADR 0032](0032-the-checker-is-installed-from-a-tagged-ref.md)), the
marketplace submission, and Phase 4's consumer repository — which adopts the
names and writes them into its own register, its own workflow and its own
ruleset. Renaming after any of those is renaming in two repositories instead of
one, and Phase 4's criterion is *no step required knowledge held only by the
author*: a name the author already intends to change is exactly that.

## Alternatives Considered

### 1. Keep `ee-standard` and `standard-check`

**Rejected.** Zero work, and the cost is paid by every reader forever. The
marketplace listing is the first and often only thing an adopter reads before
deciding whether a plugin is for them, and this one currently says nothing. The
`ee-` prefix would still be off-convention.

### 2. Name it for the outcome: `conformance`, `conformance-check`

**Rejected, and it was close.** The vocabulary is already there — "a conformant
repository", "the conformance run", and this repository's own CI job is called
*Conformance*. It reads well and it would need no explanation.

What decided against it is that *conformance* is what a **report** says, not
what the plugin **holds**. A conformance verdict is an output; the register is
the input that produces it, and the input is the thing an adopter edits, forks,
narrows and argues with. A plugin named for the verdict invites the reading that
the tool decides what conformant means, which is precisely the substitution the
core invariant exists to prevent.

### 3. Name it for the mechanism: `repo-gates`, `gate-check`

**Rejected.** Shortest and most concrete, and it names half the work. Gates are
what enforce; the checker *audits* gates and is deliberately not one
(`CLAUDE.md`: *enforcement is never Claude; a skill may install or explain a
gate but cannot be one*). A name that makes the checker sound like a gate
misdescribes the one boundary this project is most careful about. It also
collides conceptually with the six `gate-*` skills, which would then be gates
inside a thing called gates.

### 4. Rename the plugin and skills but leave the `standard-check` binary

**Rejected.** It avoids the one genuinely awkward part of this change — the
required status check on the default branch is named `standard-check`, so the
rename has to be sequenced (§ Consequences). Buying that out costs a plugin and
a binary that no longer share a name, which is a smaller version of exactly the
problem being fixed. The awkwardness is one afternoon and it is bounded; the
mismatch would be permanent.

## Decision

**We will name the plugin, the checker and the non-gate skills for the register.
The plugin is `control-register`, the checker is `register-check`, and the
skills are `register-adopt`, `register-install` and — when Phase 5 builds it —
`register-variance`.**

| Thing | Before | After |
| --- | --- | --- |
| Plugin | `ee-standard` | `control-register` |
| Checker executable | `standard-check` | `register-check` |
| Python package | `src/standard_check/` | `src/register_check/` |
| Dispatcher skill | `standard-adopt` | `register-adopt` |
| Install skill | — (ADR 0032) | `register-install` |
| Phase 5 classifier | `standard-variance` | `register-variance` |
| Gate skills | `gate-secrets`, `gate-quality`, … | **unchanged** |
| The register | `controls.yaml` | **unchanged** |
| Gating workflow | `.github/workflows/standard-check.yml` | `.github/workflows/register-check.yml` |
| Required status check | `standard-check` | `register-check` |

Three things this decision does **not** change, stated so they are not read into
it:

1. **The gates keep their names.** `gate-secrets` already names its subject, and
   a gate's name appears in every provenance stamp it has ever written. Renaming
   them would invalidate stamps across every deployed repository to no purpose.
   For the same reason, **no existing stamp changes**: a stamp names a control
   and a gate, never the checker.

2. **`controls.yaml` keeps its name.** It is already named for what it holds,
   and it is the file an adopter edits. The plugin is being renamed *towards* it,
   not away.

3. **The `ee-` prefix goes and does not come back.** If a name collides in the
   marketplace, the answer is a better name, not a namespace.

## Consequences

### The required check cannot be renamed in one move

This is the part worth stating plainly, because discovering it on a blocked pull
request is worse than planning for it. The default-branch ruleset requires a
status check named `standard-check` (CI-001's `required_checks:`). A single pull
request that renames the job removes the check the ruleset is waiting for, so
that pull request can never merge: GitHub waits forever for a context nothing
reports. It is § 4.2 of [`08-adopting.md`](../08-adopting.md) read from the
other end.

So the rename lands in **two moves**, forced by the platform:

1. Rename everything the register does not hold against the platform: the
   package, the executable, the plugin, the skills, the workflow *file*, the
   tests and the documents. Four things keep the old name — CI-001's
   `required_checks:`, the recorded ruleset's context, the gating job's id, and
   the ruleset GitHub enforces. This pull request can merge, because nothing it
   changes is a status-check context.
2. Rename those four **in one change**: a pull request moving the other three,
   and a confirmed `/gate-repo` API call moving the platform. The pull request's
   first check run fails GOV-001 — the register asks for a check the platform
   does not yet enforce — and passes once the call has been made. It then merges
   against a ruleset requiring the check its own branch reports.

**Amended 2026-08-25: this was three moves, and the middle one does not work.**
The original sequence kept a second job reporting `standard-check` while a new
`register-check` job did the work, so that the ruleset always had a context to
wait for. GOV-001 refuses it. The meta-control asks which job the blocking
controls' steps are reached from and whether a ruleset requires *that* job — so
a job that only mirrors another's result is a required check with no gate behind
it, which is the T-3 shape GOV-001 exists to catch. It was written, run, and
failed with all eleven blocking controls named. Duplicating the whole job under
both ids would satisfy GOV-001 and is a second copy of the gate, which is worse
than the thing being avoided.

What is left is a smaller intermediate state than the one first planned: no
duplicate job, and the two names coexist only between the pull request opening
and the API call — long enough for one red check run, which is the run that
proves the platform had not been changed yet. The cost is that any *other* pull
request open across that call is blocked until it is rebased onto the new job
id, which is a reason to make the call promptly rather than a reason not to.

### The finish condition stops at the ADR corpus

`grep -rn 'standard[-_]check'` returning nothing is the finish condition
**outside `docs/adr/`**. An ADR is a dated record of a decision taken, and the
ten accepted ADRs that mention the checker were correct on their dates; rewriting
them would spend [ADR 0025](0025-an-amendment-is-a-recorded-revision.md)'s
revision machinery — which exists to make governance acts visible — on a
find-and-replace, and would leave ten ADRs whose revision history says nothing
about what was decided. The corpus is governed by
[ADR 0026](0026-an-adr-stands-on-its-own.md), and a reader who greps an old ADR's
`standard-check` finds this one.

Everywhere else the name is a live reference — something a reader would type, a
path they would open, or a file a machine reads — and there it changes.

### The register contract bumps

CI-001's `required_checks:` is inside a verify block's `args:`, and
`tools.standard-check` becomes `tools.register-check` with a new `invocation`.
Both are changes a skill reading the register must understand, so
`meta.register_contract` moves — the rule in `CLAUDE.md` § Rules for editing
`controls.yaml`, applied to a rename like any other change.

### Churn, and its bound

Every document, workflow, hook, test and skill that says `standard-check` says
`register-check` afterwards. That is a large diff in a repository whose whole
discipline is not carrying second copies — and it is safe for the same reason
the discipline exists: there is exactly one authority for each of these strings,
so a rename is a rename rather than a reconciliation. `grep -rn 'standard[-_]check'`
returning nothing is the finish condition.

### What this buys

An adopter reading the marketplace sees a plugin that says what it governs. An
adopter reading their own `.github/workflows/register-check.yml` sees a job
named for the file it reads. And the noun this project uses in every explanation
of itself — *the register* — is the noun in its commands.

### What it costs, honestly

Anyone with the current plugin installed has to reinstall it under the new name;
there is no rename path for an installed plugin. Nobody outside this repository
has it installed today, which is the reason to do this now rather than after the
marketplace submission.

## Revision History

| # | Date | Change | Ratified by |
| --- | --- | --- | --- |
| 1 | 2026-08-24 | Original decision: the plugin, checker and non-gate skills are named for the register | Nathan Carney |
| 2 | 2026-08-25 | The rename is two moves, not three: GOV-001 refuses a transitional job that reports a context with no gate behind it. The finish-condition grep is bounded to exclude the ADR corpus | Nathan Carney |

## Related ADRs

- [ADR 0032: Install the Checker From a Tagged Ref](0032-the-checker-is-installed-from-a-tagged-ref.md)
  — the skill that places the checker in an adopting repository. It is named by
  this decision and it is why this decision could not wait.
- [ADR 0018: The Register–Checker Boundary](0018-register-checker-boundary.md)
  — the boundary that makes *register* the right noun: what a reasonable
  repository could need to differ on lives in the register, and the checker
  reads it.
- [ADR 0008: Protect the Default Branch by Ruleset](0008-protected-default-branch.md)
  — CI-001, whose `required_checks:` names the job this rename moves.

## References

- [Claude Code — plugins](https://docs.claude.com/en/docs/claude-code/plugins)
  — a plugin's name is its identity in a marketplace listing and in
  `installed_plugins.json`; there is no rename mechanism for an installed one.
- `EqualExperts/ee-skills` — the marketplace this plugin is being submitted to,
  and the source of the sibling names in § Background. The repository is
  **private**, so no URL is given: a link that 404s for most readers is worse
  than a name they can search for. Its catalogue is readable from an installed
  checkout at `~/.claude/plugins/marketplaces/ee-skills/plugins/`, which is
  where those names were read.
