# ADR 0019: Verify Exemptions Against the Files a Repository Tracks

**Status:** Accepted
**Date:** 2026-08-18
**Revision:** 2

Ratified from [`09-phase-1.5-review.md`](../09-phase-1.5-review.md) § H7.

## Background

[`00-concepts.md`](../00-concepts.md) § Variance states the direction rule as a
list of examples: *"adding a lint rule strengthens, raising a coverage floor
strengthens, adding an ignore path weakens. A permitted weakening **is** a
baseline entry."* Every Tier-1 control carries `baseline: null` by design and the
validator rejects a Tier-1 baseline, so for the whole of Tier 1 that sentence
reduces to a flat prohibition, and `CLAUDE.md` states it as one: *"no ignore path
may be added to a `narrowing-only` control with `baseline: null`, which is all of
them."*

**It is a rule this repository does not keep.** `.markdownlint-cli2.yaml` carries
four `ignores:` entries. They are load-bearing, not decorative: markdownlint-cli2
resolves its globs against the filesystem rather than against git, so this
repository's 30 tracked markdown files sit beside 164 more under `node_modules`.
Emptying the list makes DOC-001 fail on third-party READMEs. A rule whose author
breaks it on the first day is not a strict rule; it is an unstated exception.

**And it failed to catch the case it existed for.** `.claude/**` was in that same
list, hiding eleven authored LNT-001 violations, and was found by a person
reading the file rather than by anything mechanical — recorded as Phase 1.5's
unrecorded-weakening criterion. Two of the four remaining entries, `.terraform`
and `.pnpm-store`, name directories this repository neither contains nor
gitignores; they came from `lint-md`'s template and are inert here. Nothing
distinguishes them from an entry that hides real work.

So the prohibition is simultaneously too strict to keep and too weak to catch
what it was written for. Both follow from stating it syntactically — *no ignore
path* — rather than as the property it is reaching for. The distinction it cannot
draw is between content the repository **authors** and content that merely sits
in its working directory, and that distinction is one this codebase already
makes everywhere else: `Repo.present` is `git ls-files -co --exclude-standard`,
and predicates are evaluated against it precisely so that state is never
self-declared.

Phase 2 copies the assert layer into six `gate-*` skills, each deploying a tool
config with an exemption mechanism of its own. Whatever this rule says, it says
six more times.

## Alternatives Considered

### Option 1: Keep the prohibition, record the four entries as an exception

Leave the rule as written and note in `00-concepts.md` that this repository's
markdown gate is exempt from it.

**Pros:** No code, no register change.
**Cons:** There is no honest place to record it. A Tier-1 baseline is a schema
error, which is exactly why `variance: justified` was removed at contract 3 — the
mechanism that stopped a weakening becoming a loophole was structurally
unreachable for the controls that used it. An exception recorded only in prose is
where `.claude/**` already lived for a phase. It also leaves the rule
unimplementable for the six Phase 2 skills, which is how a rule becomes something
each skill interprets for itself.

### Option 2: Allow exemptions with a recorded reason

Permit an ignore path when it carries an owner and a justification, in the
config or in the register.

**Pros:** Expressive; handles vendored content, generated content and
third-party trees uniformly.
**Cons:** This is `justified` under another name, removed at contract 3 for
being unenforceable as specified. A reason is not checkable: nothing can tell a
true reason from a plausible one, so the mechanism degrades to trust, and the
count of exemptions grows the way a baseline that may grow does.

### Option 3: State the property, and check it

An exemption may not hide a file the repository tracks. Two consequences follow.
The common case — third-party and generated trees — needs no exemption at all,
because it can be derived from `.gitignore` (`gitignore: true`), and any entry
that remains is a genuine exemption. And an entry that matches a tracked file is
a **failing verification**, not a review finding.

**Pros:** Draws exactly the distinction the prohibition could not, using the
definition of "this repository's files" the checker already uses for predicates.
Makes the list derivable rather than hand-kept, so the four entries here become
zero. Turns the `.claude/**` class of mistake from something a reader must notice
into something the build reports. Implementable by six gate skills without
further interpretation.
**Cons:** `tracked by git` is a proxy for `authored here` — a vendored directory
that is committed deliberately cannot be exempted without changing the register.
A file may be tracked *and* match `.gitignore`, so deriving from `.gitignore`
alone would still hide it; the explicit check is needed as well as the derived
list, not instead of it.

## Decision

We will define an exemption by what it hides: **no exemption in a deployed gate
configuration may exclude a file the repository tracks**, and the gate's verify
block will check that rather than prohibiting exemptions outright.

For DOC-001 this means `.markdownlint-cli2.yaml` sets `gitignore: true` and
carries an empty `ignores:` list, and `markdown_gate_wired_at_all_loci` fails any
`ignores:` entry that matches a tracked file. `00-concepts.md` § Variance and
`CLAUDE.md` state the property in place of the prohibition, so the six Phase 2
gate skills inherit a rule they can implement identically.

Option 3 was chosen because it is the only one of the three that is *checkable*.
Option 1 preserves a rule already broken in this repository and gives the
breakage nowhere to be recorded; Option 2 re-introduces a value the register
removed for being structurally unenforceable. The rule stays in the checker
rather than moving to the register, per
[ADR 0018](0018-register-checker-boundary.md)'s test: which files a repository
tracks is not something a reasonable Equal Experts repository could need to
differ, because it is a property of git, and "what the repository authors" is a
property of the register format's variance vocabulary rather than of any one
repository.

## Consequences

**Positive outcomes:**

- DOC-001's deployed configuration carries no exemptions at all, so
  `narrowing-only` with `baseline: null` is literally true here rather than
  aspirationally true.
- The exemption list stops being hand-maintained. The two entries that named
  directories this repository does not have could not have been noticed by
  review; a derived list cannot contain them.
- The weakening that Phase 1.5 found by reading is now a failing build. That
  criterion was closed by deleting the offending entry, which fixed the instance
  and not the class.
- Six Phase 2 gate skills inherit one property rather than six interpretations
  of a prohibition none of them can honour.

**Trade-offs and risks:**

- `gitignore: true` requires the linter to run inside a git working tree.
  **Accepted 2026-08-18, not carried as a risk:** development happens in a
  git-controlled environment by premise — [`03-devcontainer.md`](../03-devcontainer.md)
  makes a clone the unit of work, and this whole standard evaluates a repository
  through `git ls-files`. A tarball extract would lint its vendored content and
  fail, and that is not an environment we support.
- A repository that deliberately commits vendored markdown (a `third_party/`
  tree) now has no way to exempt it without a register change. That is the
  intended direction: such an exemption should be visible in the register rather
  than in a config file, and no repository here has one.
- The check reads one config format. Each Phase 2 gate skill must implement the
  property for its own tool's exemption mechanism, and a tool with no such
  mechanism needs no check — an absence that has to be deliberate rather than
  overlooked.
- `.markdownlint-cli2.yaml` is a `lint-md`-deployed artefact, so this change
  widens the amend already raised as
  [ee-skills-incubator#530](https://github.com/EqualExperts/ee-skills-incubator/issues/530)
  and the file stays un-refreshable until a maintainer ships it.

## Applied — TYP-001, register contract 9

The rule was written for exemption lists and applies unchanged to allow-lists,
which are exemption lists whose entries are everything they do not name.
`[tool.mypy] files = ["src", "tests", "scripts", ".claude/hooks"]` was the four
paths that existed when somebody wrote the line, against a control claiming *all
first-party source*.

Measured, not reasoned about: a tracked module with a genuine type error, which
nothing under those four paths imported, left `uv run mypy` reporting *"Success:
no issues found in 31 source files"* and `standard-check` reporting TYP-001
**PASS**. mypy found the error the moment it was pointed at the file.

`stacks.<stack>.source_globs` names the tracked files a stack's gates must cover
and `gates.<role>.coverage_key` names where the allow-list lives, so the same
comparison runs: what the list leaves out must be something git does not track.
The same repository now reports

```text
TYP-001  FAIL  ✗ python: pyproject.toml: tool.mypy.files does not cover 1 tracked
               python file(s) (tools/deploy.py) — mypy runs over what this list
               names, and the control claims all first-party source
```

Two consequences are deliberate. **Import-reachable files are not credited.**
mypy follows imports out of the allow-list, so such a module is checked today by
accident of somebody importing it, and unchecked again the day that import goes;
coverage withdrawable without editing the coverage list is not declared coverage.
And **an absent allow-list is not an exemption** — `tsc` with no `include`
compiles everything below its tsconfig, so there is nothing to judge.

`pyproject.toml` is unchanged. Its list covers every tracked module today, which
is the point: an exemption may exist, and may not hide anything.

## Related ADRs

- [ADR 0013: One Markdown Rule Set, Deployed Not Duplicated](0013-one-markdown-rule-set.md)
  — DOC-001's rationale; this ADR governs what its deployed config may exclude.
- [ADR 0018: Draw the Boundary Between Register and Checker](0018-register-checker-boundary.md)
  — the test under which this rule stays in the checker rather than moving to
  the register.
- [ADR 0009: Lint From One Pinned Definition at Every Locus](0009-single-lint-definition.md)
  — LNT-001, whose `.claude/**` exclusion was the instance that prompted this.
- [ADR 0020: Invoke a Pinned Tool by the Path Its Lockfile Owns](0020-a-locus-reaches-the-pinned-artefact.md)
  — `markdown_gate_wired_at_all_loci` carries both this rule and that one.
- [ADR 0024: Keep Only Direction Values in the Variance Vocabulary](0024-variance-vocabulary-is-direction-only.md)
  — this ADR's Option 2 was rejected as `justified` under another name; ADR 0024
  records the removal it refers to.

## References

- [markdownlint-cli2](https://github.com/DavidAnson/markdownlint-cli2) — the
  `gitignore` configuration property, and DOC-001's cited standard.
- [`00-concepts.md`](../00-concepts.md) § Variance — the direction rule this ADR
  restates.
- [`09-phase-1.5-review.md`](../09-phase-1.5-review.md) § H7 — the finding, and
  the measurements behind it.

## Revision History

| Rev | Date | What changed | Ratified by |
| --- | --- | --- | --- |
| 1 | 2026-08-18 | Original decision: no exemption in a deployed gate configuration may exclude a file the repository tracks, checked rather than prohibited. | Nathan Carney |
| 2 | 2026-08-19 | § Applied — TYP-001, register contract 9. The rule extended beyond DOC-001 to the type checker's exclusions. | Nathan Carney |

Revisions before 2026-08-23 are backfilled from the amendments in the body and from git, per [ADR 0025](0025-an-amendment-is-a-recorded-revision.md); they were not recorded at the time.
