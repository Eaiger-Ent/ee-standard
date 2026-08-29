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

## The second slice — the access decision, and the shell that can submit

Landed 2026-08-29. It closes one criterion, the only open one that nothing
outside this repository gated.

### What was found

Two open criteria were one problem. *"DOC-001 has a route for an adopter who
cannot see `ee-skills`"* is about a private marketplace holding the gate that
owns DOC-001's lifecycle. *"`control-register` installable from the marketplace
as one plugin"* is about promoting this plugin **into that same private
marketplace**. Read as *installable from `ee-skills` instead*, closing the second
would have re-acquired the access-shaped single point of failure the devcontainer
template was moved into this plugin to escape — and it would have done so in a
one-line edit to `08-adopting.md` § 0.0, at the moment everyone was thinking
about the destination rather than about who cannot reach it.

Measured 2026-08-29: `EqualExperts/ee-skills` is `private: true`;
`Eaiger-Ent/ee-standard` and `Eaiger-Ent/ee-standard-consumer` are public.

### What was decided

[ADR 0044](adr/0044-the-adopter-installs-from-the-public-marketplace.md), in two
parts. The public marketplace stays the address the guide names, so **promotion
adds a publication rather than replacing an instruction**; and a control whose
deploying skill an adopter cannot install is **satisfied by hand and verified by
the register** — DOC-001 being the instance, with the six steps already written
and verified in Phase 4's consumer repository, promoted from stopgap to
supported route.

Three alternatives were rejected in the ADR, and the reason each looks
reasonable is recorded there: copying `lint-md` into the adopter's repository
(what Phase 4 did, and what `register-check deployments` cannot reconcile, since
a copied directory is not an installed plugin), writing a DOC-001 gate here (one
lifecycle, two implementations, free to drift), and making promotion conditional
on `ee-skills` being published (gates this phase on a repository nobody here
owns — the ordering ADR 0022 rules out and the reason ADR 0037 retired a
criterion rather than leaving it open).

The request is still worth making, so it is **submission 7** rather than a
precondition: nothing here waits on the answer, and a yes makes part 2 of the
ADR unnecessary without touching part 1.

### What holds it

`tests/test_adopter_guide.py::test_the_guide_installs_the_plugin_from_the_repository_the_register_names`
derives the marketplace § 0.0 names from `tools.register-check.install.repository`
and fails a guide that names another. Checked by mutation: rewriting the command
to `EqualExperts/ee-skills` fails the test, and only that test. It is derived
rather than compared against a literal because a fork or an internal mirror is a
thing a repository reasonably differs on (ADR 0032), so the guide must move with
the register and not with the test file.

### The submitting shell

The other half of the slice, and the smallest useful thing in it. Three of the
five machine requirements the first slice found are environment, and together
they are one command — `.devcontainer/.env` sourced for `CLAUDE_CODE_OAUTH_TOKEN`,
`GITHUB_TOKEN` **unset** because `gh` honours one token variable at a time, and
`GH_TOKEN` set to `EE_SKILLS_GITHUB_TOKEN`. Verified by asking the API for
`permissions.push` on the incubator and getting `true`.
[`05-promotion.md`](05-promotion.md) § The submitting shell carries it, with the
verification line as part of the recipe rather than as a note beside it: the
whole failure it guards against is a 404 that means *cannot see* being read as a
404 that means *not there*.

### What it deliberately left open

The register is not touched and **the contract stays at 35**, which is what the
criterion predicted when it said the answer would be a publication decision
rather than a code change.

Nothing was submitted. Submissions 3, 6 and 7 are ready and independent;
submission 1 still needs nine sets of trigger fixtures, which are the operator's
answers to the tool's own questions and cannot be staged here.

## The third slice — the answers are drafted before they are asked

Landed 2026-08-29. It closes no criterion and it removes the largest remaining
piece of preparation from the one criterion nobody can start.

### What was found

The first slice found that `/skill-submit-new` needs `tests/<skill>/triggers.yaml`
and `tests/<skill>/prompt.txt` per skill, that Gate 3 is trigger fidelity, and
that none of the nine existed. What it did not say is how those files come to
exist: the tool asks four questions — slash invocations, natural-language
invocations, prompts that must **not** activate, and a contribution rationale —
validates each answer, and builds the files from them into temp files it commits
onto the branch. **It never reads them from the submitting repository.**

That is the whole argument for drafting them here. Submission 1 is nine pull
requests; without drafts it is thirty-six answers composed live, in the session
where the branch is pushed, at the one moment there is no undo. With drafts it
is nine readings.

### What was drafted

`docs/promotion/fixtures/<skill>/` — `triggers.yaml`, `prompt.txt`, and
`rationale.txt` for Q4. Plain text rather than Markdown for the last one,
because it is typed into a question box and never rendered.

The entries are derived from each skill rather than invented: `should_activate`
opens with the bare slash command, then the argument variants each
`argument-hint` declares, then the natural-language phrases the skill's own
`description` already advertises under `Triggers:`. `should_not_activate` names
a sibling in the family — the confusable that actually exists, since a family of
six gates dispatched by one skill is the realistic way a wrong one fires — plus
a slash command from outside it and a close but out-of-scope prose prompt.

### Two things the drafting found

**The smoke test runs `prompt.txt` for real.** `scripts/smoke-test.sh` executes
`claude -p "$(cat prompt.txt)"` under `--permission-mode bypassPermissions` with
a ten-second deadline. That is worth knowing for a family of skills that writes
files and, in one case, mutates GitHub. It is safe, and the reason is
structural rather than lucky: the run happens in a **fresh empty temp
repository** containing only a shim of the skill under test, and because that
repository has no `controls.yaml`, every gate stops at its own pre-flight. The
gate's only assertion is that the reply is not `Unknown command`. The prompts
were chosen with that in mind — the documented invocation, `--repo .` and
`--register ./controls.yaml`, which is both the realistic example the tool asks
for and the most inert thing these skills can be handed.

**`register-adopt` advertises triggers it cannot answer to.** Q2 is skipped
entirely for a skill carrying `disable-model-invocation: true`, and after
[ADR 0035](adr/0035-a-dispatched-skill-is-reachable.md) `register-adopt` is the
only one of the nine that still does — so its fixture is three slash entries and
no prose, correctly. But its `description` says
`Triggers: 'adopt the standard', 'deploy the control register', '/register-adopt'`,
and the first two of those cannot fire, because the flag is exactly what stops
the model invoking it. Nothing checks that a description's advertised triggers
are reachable; preflight P4 checks the opposite direction. **Recorded rather
than fixed**: the flag is deliberate (the entry point is a person's, ADR 0033
revision 2), the description is what a reader sees, and which of the two should
move is a decision, not a typo.

### What holds it

`tests/test_submission_fixtures.py`, deriving the set from the plugin in both
directions the way `tests/test_skill_links.py` derives the symlinks — a skill
with no answers, and answers for no skill, fail differently and neither is more
likely. The per-file rules are **the tool's own**, read from
`skill-submit-new-qa.md`: one slash entry at least, two must-not-activate
entries including a slash command, a rationale of ten words, the bare command
first. One rule is this repository's: `prompt.txt` must be an entry
`triggers.yaml` already lists, because the tool derives it from the answers and
a prompt appearing nowhere in the triggers is a draft that has drifted from
itself. Mutation-checked in both directions.

### What it deliberately left open

**These are drafts, not fixtures.** Nothing in the submission path reads them,
and a test cannot make them true — it can only keep them present, well-formed
and in step with the skill list. Whether an entry is a *good* trigger is Gate 3's
judgement and a reviewer's, which is the same boundary
`tests/test_adr_revisions.py` draws when it holds the form of a revision history
and not the accuracy of its summaries.

Nothing was submitted.

## The fourth slice — a link that resolves here and nowhere else

Landed 2026-08-29, in the middle of assembling submission 1, and it is the
reason that submission paused rather than shipped.

### What was found

`ee-skills-incubator` runs `scripts/check-path-hygiene.sh` over everything under
`skills/`, and it forbids `../` outright. The first assembly of the submission
bundle failed it — **twenty-three links across eleven files in nine of the nine
skills**, every one of the form
`[ADR 0035](../../../../docs/adr/0035-a-dispatched-skill-is-reachable.md)`.

They resolve in this repository and nowhere else. A plugin is copied into its
own install cache; `docs/` is not shipped and never will be. Every one of those
links dangles the moment anybody installs the plugin.

**[ADR 0036](adr/0036-shared-skill-prose-has-one-home.md) had already made this
exact argument**, and made it well: its two shared reference files cite it *in
prose rather than by link*, because "a relative link out of the plugin resolves
here and dangles in every installation". The rule was stated, applied to the two
files the ADR was about, and never applied to the skills — where it mattered
more, because a skill is what an adopter reads.

Nothing here caught it. `tests/test_plugin.py` checks that no value the register
pins appears under `plugins/`; nothing checked where a link points. It was found
by a gate in somebody else's repository, at the one moment there is no undo,
which is the worst available place to learn it and the reason the rule is now
held here.

### The fix that was tried first, and why it was wrong

The obvious replacement is an `https` citation of this public repository — the
decision register contract 30 already took for `rationale_adr`, for the same
reason: a register fetched into a repository that did not author it cannot
resolve a path either.

It was applied, and `tests/test_register_install.py` failed:
`test_the_skill_writes_no_address_of_its_own` forbids the value of
`tools.register-check.install.repository` from appearing anywhere in a skill's
files, because a skill must read that address from the register at run time or
not at all. The URL contains it.

That test is right and the citation is not worth an exception, so the links
became **prose** — `ADR 0035`, no link — which is what ADR 0036's own files do.
The cost is honest: a reader of an installed skill sees the reference and cannot
click it. The alternative was a link that looked clickable and went nowhere.

### What holds it

`tests/test_plugin_links.py`, in both directions. No markdown under
`plugins/` may link out of the plugin; and every `ADR NNNN` cited in that
markdown must name an ADR this repository has, `docs/adr/archive/` included,
because an archived ADR is still a decision that was taken. A citation naming a
decision that does not exist is the mirror failure — a reference the reader can
neither follow nor verify.

### What it deliberately left open

**The rule is checked for the plugin, not for the repository.** `docs/` links to
`docs/` freely and should: those files ship together and resolve together. The
boundary is the plugin, because the plugin is the thing that gets copied.

**Nothing was submitted in this slice.** Submission 1's bundle was assembled,
passed preflight P1–P11 on all nine skills, passed the incubator's
markdownlint, promote-config registration and skill-invocation-conflict checks,
and failed path hygiene. It is re-assembled from this commit.
