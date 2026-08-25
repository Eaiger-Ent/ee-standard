# ADR 0033: Reach the Skills by Symlink, and Amend the Submission Tool Separately

**Status:** Accepted
**Date:** 2026-08-25
**Revision:** 2

## Background

**The problem.** `/skill-submit-new` cannot see this repository's skills, and it
is the only supported way to submit one.

The tool resolves `<name>/SKILL.md` in the project's Claude skills directory or
in the user-level one. This repository's skills live at
`plugins/control-register/skills/<name>/`, which is the **marketplace's** layout
— `ee-skills/plugins/adr-toolkit/` has exactly that shape, and matching it is
deliberate ([`05-promotion.md`](../05-promotion.md) § What the incubator
actually holds). Nothing sat at `.claude/skills/` at all.

So the destination's layout and the submission tool's expectation disagree, and
this repository is caught between them. `05-promotion.md` recorded the gap on
2026-08-20 and declined to settle it:

> Something has to bridge that at submission time — a copy, a symlink, or an
> amendment to the submission skill that teaches it the plugin layout. **This is
> undecided**, and it is recorded here rather than settled because the third
> option is a fifth submission and that is not a decision to make silently.

**Why it has to be settled now.** Submission 1 is one issue per skill, eight of
them, each carrying a `SKILL.md` the tool reads. A bridge improvised at that
moment is improvised eight times, at exactly the point where the content has to
be right and there is no iterate-in-review loop: submission is an issue, not a
pull request, and you cannot push a fix to it.

## Alternatives Considered

### 1. Copy each skill into `.claude/skills/` at submission time, then delete it

**Rejected.** It works, it leaves nothing tracked, and it is the obvious thing to
reach for.

What is wrong with it is what this repository exists to prevent. Eight copies
made by hand, at the one moment accuracy matters, with the original and the copy
both on disk and nothing comparing them. A copy that is stale by one commit
produces an issue that describes a skill nobody has — and the review that would
catch it is a maintainer's, days later, reading the issue rather than the
repository. "One definition copied, then diverged" is theme T-2, and doing it
deliberately does not make it a different thing.

### 2. Amend `skill-submit-new` to understand the plugin layout

**Rejected as the immediate answer, and adopted as a follow-up.** It is the
right general fix: every multi-skill plugin submitted from a marketplace-shaped
repository hits this, and `preflight-check.sh` in the same marketplace already
resolves `$REPO_ROOT/plugins/<name>/skills/<name>/`, so one of the two tools has
learned about plugin layouts and the other has not.

It cannot be the immediate answer because it serialises this repository's
submission behind someone else's review queue. The amendment is an issue against
the incubator like any other, a maintainer decides when it lands, and until it
does the eight submissions cannot be made at all. A blocker that is not ours to
clear should not be on the critical path when a reversible local change clears
it today.

### 3. Write the eight issues by hand

**Rejected.** The tool does more than paste a file: it checks the skill is not
already in the incubator, gathers trigger examples and test fixtures, and
generates the `promote-config.json` entry. Bypassing it means reproducing all of
that from a reading of its `SKILL.md`, eight times, and the part most likely to
be dropped is the `promote-config.json` entry — which is the single thing that
decides whether one plugin arrives or eight.

## Decision

**We will expose the skills at `.claude/skills/<name>` as tracked symlinks into
`plugins/control-register/skills/<name>`, and submit the amendment to
`skill-submit-new` as a separate, later submission.**

```text
.claude/skills/gate-secrets -> ../../plugins/control-register/skills/gate-secrets
```

Eight links, one per skill, stored by git as symlinks (mode `120000`) rather
than as copies.

**There is one definition and one place it lives.** The plugin directory is the
source; the link is a second *reference*, which is what this repository asks of
every other artefact it governs — *pin once, reference many*. A symlink cannot
drift from its target, so the failure mode option 1 carries does not exist here.

**The link set is checked rather than remembered.** `tests/test_skill_links.py`
fails if a skill in the plugin has no link, if a link points somewhere other
than its own skill, or if a link dangles. A ninth skill added without a link
would otherwise be a skill that silently cannot be submitted, discovered at
submission time.

**Nothing becomes model-invocable.** All eight skills carry
`disable-model-invocation: true`, so exposing them makes them available as
`/gate-secrets` and the rest to a person in this repository and never to a model
choosing for itself. That is a side effect worth having: the gates can now be
exercised here, against the repository that defines what they deploy.

> **Amended 2026-08-25.** The paragraph above stopped being true, and the
> decision it supports did not change. Seven of the eight skills — the six gates
> and `register-install` — dropped `disable-model-invocation: true` under
> [ADR 0035](0035-a-dispatched-skill-is-reachable.md), because
> `register-adopt` dispatches them and a callee carrying that flag cannot be
> reached at all: the front door stopped at Step 0 the first time anyone ran it
> outside this repository. `register-adopt` itself keeps the flag, so the entry
> point is still a person's. What guards `gate-repo`'s platform mutations is its
> own per-call confirmation, enumerated by
> `tests/test_gate_repo_confirmation.py`, and not this frontmatter key. The
> symlinks, and every argument for them above, are unaffected — the links exist
> so `/skill-submit-new` can resolve `<name>/SKILL.md`, which has nothing to do
> with who may invoke what.

## Consequences

### The amendment is submission 5, and it is not conditional on this

Teaching `skill-submit-new` the plugin layout stays worth doing after the
symlinks exist, because the next repository to hit this will not have read this
ADR. It is recorded in `05-promotion.md` § Submission order so that it is
tracked rather than remembered — a submission absent from that table is one that
gets forgotten at promotion time, which is the reason submission 4 is listed
there too.

Its relationship to this decision is worth stating plainly: **the symlinks are
not a workaround waiting to be removed.** If the amendment lands, the links stay
useful for invoking the skills locally; if it never lands, nothing here breaks.

### Windows checkouts are a stated cost

Git on Windows writes a symlink as a plain text file containing the target path
unless `core.symlinks` is on and the account may create links. A contributor in
that state gets eight files whose contents are relative paths, and
`test_skill_links.py` fails for them — which is the right outcome, because the
alternative is a submission built from a file that is not the skill. All
development here happens inside the devcontainer, where this does not arise.

### `.claude/` is now partly a tracked interface

`.claude/hooks/` was already tracked and stamped. Adding `skills/` means a
second thing in that directory belongs to the repository rather than to whoever
is running Claude in it. `settings.local.json` remains untracked and must stay
so.

## Related ADRs

- [ADR 0031: Name the Plugin and the Checker for the Register](0031-the-plugin-is-named-for-the-register.md)
  — the plugin's name is what the `promote-config.json` entry these submissions
  ask for must say, and why it had to be settled before any of them.
- [ADR 0019: Exemptions Cannot Hide Tracked Files](0019-exemptions-cannot-hide-tracked-files.md)
  — the same instinct from the other side: what is tracked is what is governed,
  and a path that hides from the tooling hides from review.

## References

- `EqualExperts/ee-skills` — `plugins/ee-skills-contribute/skills/skill-submit-new/SKILL.md`
  § Locate the skill, which lists the two directories it resolves against, and
  `plugins/skill-preflight/skills/skill-scripts/scripts/preflight-check.sh`,
  which resolves plugin layouts as well. Read from an installed checkout at
  `~/.claude/plugins/marketplaces/ee-skills/` on 2026-08-25; the repository is
  private, so no URL is given — a link that 404s for most readers is worse than
  a path they can look at.
- [Git — symbolic links in the index](https://git-scm.com/docs/git-config#Documentation/git-config.txt-coresymlinks)
  — mode `120000`, and the `core.symlinks` behaviour the Windows consequence
  above describes.

## Revision History

| Revision | Date | Summary | Ratifier |
| --- | --- | --- | --- |
| 1 | 2026-08-25 | Original decision: the submission tool reaches the skills by tracked symlink | Nathan Carney |
| 2 | 2026-08-25 | Corrects the "nothing becomes model-invocable" consequence, which ADR 0035 made false for seven of the eight skills | Nathan Carney |
