# Phase 6 — promotion

[`04-build-plan.md`](04-build-plan.md) is the list of outstanding work; this is
where the evidence behind every criterion it ticks lives, and where what each
slice deliberately left open is written down.

Phase 6 is the phase whose work happens in someone else's repository, so it is
also the phase where this repository's habit of checking a claim rather than
carrying it matters most: every fact it acts on is a fact about `ee-skills` and
`ee-skills-incubator`, and neither is ours to hold still.

## The first slice — the transport changed

Landed 2026-08-28. It closes no criterion. It is recorded first because it
invalidated the sentence three of them were written on top of, and because of
how close it came to being carried into a submission unnoticed.

### What was found

`docs/05-promotion.md` opened with *"Three properties of this route shape the
build plan"*, and the first was **"Submission is an issue, not a pull request."**
Measured against the installed marketplace checkout at
`~/.claude/plugins/marketplaces/ee-skills/` (`0ff6b28`, 2026-08-28 19:25), it is
false, and so is the consequence drawn from it:

| Was written | Is |
| --- | --- |
| Both submission skills "open a GitHub issue" | Both build a branch — `new/<skill>--<author>-<YYYYMMDD>`, `amend/<skill>--<author>-<YYYYMMDD>` — and open a pull request. *"Nothing is serialised into text: the commit is the submission"* (#608, #611, #615) |
| "You do not push a branch, and you cannot self-merge" | You push a branch, to upstream or to a fork. You still cannot self-merge |
| "There is no iterate-in-review loop under your control" | There is: `submit-branch.sh` is idempotent — *"PR already open for $BRANCH — branch updated, no new PR created"* |
| "A plugin shipping nine skills is nine issues" | Nine pull requests. **This one survived**: the unit of submission is still a skill |

The change is not old. `git log -S'pull request'` on
`plugins/ee-skills-contribute/skills/skill-submit-new/SKILL.md` in that checkout
dates it to two commits on 2026-08-28, `7551f0e` at 11:07 UTC and `3815530` at
18:24 UTC — the same day this repository was reading the file.

### Why nothing here caught it

This is the interesting half, and it is [§ A](09-phase-1.5-review.md) again in a
document rather than in an assert.

`docs/05-promotion.md` was re-verified **that morning**, at `d83e1c6`, and the
re-verification is recorded in it: *"All four re-verified … and again on
2026-08-28 against the same checkout at `d83e1c6`."* The four are the four
`CONTRIBUTING.md` corrections. `7551f0e` is an ancestor of `d83e1c6` by
twenty-nine minutes, so **the transport had already changed in the tree that was
read**. What was checked was the list of things previously found wrong; what was
not checked was the paragraph above the list, which nothing had ever found wrong
and which therefore nothing looked at.

A verification that re-reads its own findings and not its own premises is the
shape this repository keeps finding in its asserts — `linter-wired-at-all-loci`
asking whether the pinned extension was present and not whether it held the
language, `markdown_gate_wired_at_all_loci` reading one of the editor locus's two
artefacts, `decision_problems` comparing a declination against the stamp rather
than against the installed skill. Here it cost nothing, because the correction
landed before a submission did. It is worth writing down that it cost nothing
**by timing**: the same miss, made a day later, is nine pull requests opened by a
plan describing a tool that no longer exists.

There is no assert to add. The premise lives in another organisation's
repository and changed on an ordinary Friday; what this phase can do is date
every measurement and re-take them in the same pass, which is what the corrected
document now does.

### What else the re-measurement found

Everything below was read at `0ff6b28` and, where it is a claim about this
machine, measured here.

**Row 1 of the `CONTRIBUTING.md` corrections shrank from two errors to one.**
It said *"Run `/submit-amendment`; it opens a PR against the incubator on branch
`amend/<skill>--<author>-<YYYYMMDD>`"*, and this document recorded both halves as
wrong. The branch half is now exactly what `submit-branch.sh` builds. Only the
name is wrong. `CONTRIBUTING.md` described the transport correctly the whole
time and was recorded as wrong — accurately, on the day it was read, which is the
argument for dating a measurement rather than stating a fact. Rows 2 to 4 were
re-measured and all three stand: no `scripts/promote.py`; `preflight-check.sh`
implements P1 to P11 and ships as nine copies of one md5 under
`plugins/<plugin>/skills/skill-scripts/scripts/`, with no `skill-review` plugin
among the forty-nine; and the second `P1–P6` line is still in the file.

**A submission now needs four things from the machine it runs on, and this
container supplies two of them.** `claude` and `uv` are present.
`tests/<skill>/triggers.yaml` and `tests/<skill>/prompt.txt` do not exist for any
of the nine skills and are built interactively at submission time — Gate 3 is
trigger fidelity, so they are not optional, and nine sets of them is the largest
remaining piece of submission 1. And `submit-branch.sh` invokes `gh` itself,
which the `gh-ee-skills` wrapper cannot help with, because the wrapper scopes a
single invocation and the invocations are inside someone else's script: the
ambient `GITHUB_TOKEN` is scoped to `Eaiger-Ent` and returns 404 for
`EqualExperts/ee-skills-incubator`, while `EE_SKILLS_GITHUB_TOKEN` has `push` and
`admin` on it. A submission must be run with the second as `GH_TOKEN` for the
whole run.

**`skill-submit-new` reads a 404 as an answer, which is submission 6.** Step 1a
runs `gh api repos/EqualExperts/ee-skills-incubator/contents/skills/<name>` and
treats failure as *the skill is new — continue*. A token that cannot see a
private repository returns exactly that failure, so with the ambient token the
check clears every name, including one already in the incubator. It is the
error this repository refuses in its own asserts — SEC-001 raising rather than
reading an omitted `security_and_analysis` as "push protection is off", ADR 0043
giving a missing plugin inventory a third state rather than reading it as
agreement — and it is worth raising before submission 1 rather than after,
because submission 1 is what would meet it nine times.

**The `lint-md` rows still stand at 1.0.9.** `lint-md` moved to 1.0.9 in the
same window, so submission 4's three rows were re-measured against what is
installed rather than against what was measured at 1.0.8: `local-config.md`
still defaults `invocation` to `npx --no-install` and `ignores` to a list
containing `.claude/**`, and `SKILL.md` still mentions no `ee-control` header at
its overwrite prompt. Three rows, unchanged, now dated to the release this
repository actually deployed.

### What the slice changed

- `docs/05-promotion.md` — the route diagram, the three properties, the
  consequences drawn from them, the `CONTRIBUTING.md` row that shrank, the
  incubator's four pre-push gates, submission 6, and two new rows in
  § What is ready that are **not** ready.
- § The `promote-config.json` entry — new. The consolidated entry was an
  ellipsis, `"control-register": {"skills": [ … ]}`, in the one place nine
  branches each have to carry the same text. It is written out, and
  `tests/test_promote_entry.py` derives both fields from the plugin so it cannot
  drift from it.
- `CLAUDE.md`, `docs/04-build-plan.md`, `tests/test_preflight.py` and
  `tests/test_skill_links.py` — four places that said "issue" and now say what
  the tool does.

### What it deliberately left open

**[ADR 0033](adr/0033-the-submission-tool-reaches-the-skills-by-symlink.md) is
not edited**, although its rationale says *"submission is an issue, not a pull
request"*. An ADR is a dated record of what was true when it was written
([ADR 0026](adr/0026-an-adr-stands-on-its-own.md)), the decision it took —
tracked symlinks — is unaffected, and the tool still resolves
`<name>/SKILL.md` in the Claude skills directory, so the symlinks still do the
job they were added for. This is the same rule under which `standard-check`
survives inside `docs/adr/` and `adr-toolkit@0.1.11` survives in ADRs 0025 and
0026.

**No criterion is ticked.** The first Phase 6 criterion —
`08-adopting.md` describing installation from the marketplace, with its § Status
table true on the day of release — cannot be closed before the release it names,
and this slice did not touch it. The submissions themselves are acts in another
organisation's repository and none is raised without being asked for.
