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

## The fifth slice — the submissions are raised

Landed 2026-08-29. It closes two criteria and it did not close either the way
the plan expected, because three of the five prepared submissions moved between
being written and being sent.

### What went out

| Submission | Where |
| --- | --- |
| 3. `CONTRIBUTING.md` corrections | [ee-skills#550](https://github.com/EqualExperts/ee-skills/pull/550) |
| 5 + 6. `skill-submit-new` | [incubator#655](https://github.com/EqualExperts/ee-skills-incubator/pull/655) |
| 4. `lint-md` | [incubator#656](https://github.com/EqualExperts/ee-skills-incubator/pull/656) |
| 7. `lint-md` reachability | [ee-skills#551](https://github.com/EqualExperts/ee-skills/issues/551) |
| 1. `control-register` | [incubator#657](https://github.com/EqualExperts/ee-skills-incubator/pull/657) |
| 2. `skill-update` widening | Not raised — it shipped |

### The three that moved

**Submission 2 was withdrawn because it had already shipped.** Before writing
it, the installed `skill-update` was read: it carries Step 2.7 *"Is a deployment
owed?"*, a `DEPLOYMENT_STATE`, a *Deployment owed* output block, and the rule
**"Never emit Already done over an owed deployment"** — this submission's own
argument, almost verbatim. Its § Why criterion 5 has two halves states the
failure mode this repository was going to report. Nothing to raise. It is kept
in the promotion table rather than deleted, for the same reason Phase 4's
retired criterion is: a submission that vanishes is indistinguishable from one
nobody noticed.

**Submissions 5 and 6 became one pull request, and had to.**
`/skill-submit-amend` builds `amend/<skill>--<author>-<YYYYMMDD>`. Two
amendments to one skill on one day is one branch. The plan had them as separate
items and the tool's naming settles it.

**Submission 4 went out with two rows instead of three, and the third is the
finding of this slice.** It was going to argue that `invocation` should default
to `node_modules/.bin/markdownlint-cli2`, on the premise — stated in
`local-config.md` upstream and in
[ADR 0020](adr/0020-a-locus-reaches-the-pinned-artefact.md) here — that
`npx --no-install` falls through to `PATH`.

**It does not, on npm 11.17.0 / node 24.19.0.** Three probes, in a directory
with no `package.json` and no `node_modules`:

| Probe | Result |
| --- | --- |
| Real `markdownlint-cli2` first on `PATH` | exit `1` — *"npx canceled due to missing packages"*; the `PATH` copy is not run |
| A `PATH`-only name that is not an npm package | exit `1` — 404 against the registry |
| With a local install present | exit `0`, resolving `node_modules/.bin` |

ADR 0020 § Background records the opposite as measured: *"With `node_modules`
absent, npx falls through to `PATH` … exit 0 (a global answered)"*. What it most
likely observed is the npx **cache** — the run above resolves a specific
version, `markdownlint-cli2@0.23.2`, in a directory containing nothing that
names one.

**ADR 0020's decision survives and its stated mechanism does not.** npx still
resolves a version from somewhere that is not the lockfile, so *a locus reaches
the pinned artefact* holds; *it falls through to `PATH`* is false on this npm.
Under [ADR 0026](adr/0026-an-adr-stands-on-its-own.md) that is the in-place
amendment case — decision unchanged, record factually false — and it is owed by
ADR 0020, CLAUDE.md, and `08-adopting.md` § 3, which tells an adopter the `PATH`
claim outright. **Left open by this slice** rather than folded into it: an
amendment to an accepted ADR is its own act with its own revision.

The row was withdrawn rather than argued down, and the measurement sent to the
maintainers as information rather than as a change request, with the note that
the behaviour may well hold on the npm version they observed it on.

### Submission 1 is one pull request, not nine

The plan, the promotion document and the criterion all said one per skill,
because `/skill-submit-new` is per skill. Assembling it showed what nine would
cost: each branch adds the same `"control-register"` key to
`promote-config.json`, so eight of the nine are textual conflicts on an
**identical** addition, and until the last merges the entry names eight skills
that are not there. `check-promote-registration.py` takes a *list* of changed
skill directories and reported all nine registered from one branch.

The deviation is stated in the pull request, which offers to split them — the
destination holds three layouts at once, and this document already says to ask
rather than pick.

### What it deliberately left open

**ADR 0020's amendment**, above. **And the two criteria that remain are the ones
nobody here can close**: `control-register` installable from the marketplace,
and the consumer repository re-adopting from the marketplace copy. Both wait on
a maintainer, and the second additionally on a host with Docker.

## The sixth slice — submission 7 is answered, and ADR 0044 was right not to wait

Recorded 2026-08-29, hours after the submission went out.

[ee-skills#551](https://github.com/EqualExperts/ee-skills/issues/551) — the ask
that `lint-md` be reachable to adopters outside Equal Experts — was **closed as
a known limitation**: *"This is a current feature of the repository and is
planned to be fixed in the future. Closing as a known feature."*

That is the outcome
[ADR 0044](adr/0044-the-adopter-installs-from-the-public-marketplace.md) was
written for, and it needs no amendment: *"Nothing is blocked on this … A yes
would make that section unnecessary; a no changes nothing and needs no reply."*
The answer is a not-yet, `EqualExperts/ee-skills` stays private today, and the
by-hand route for DOC-001 stays the supported one for an adopter who cannot
reach it. Had this repository made promotion conditional on the answer — the
third alternative that ADR rejected — Phase 6 would now be waiting on somebody
else's roadmap.

**It is also the slice's own correction.** Submission 7 did not come from the
promotion plan. It was added on 2026-08-29 by the ADR 0044 slice, as this
repository's own idea, and then went out inside a blanket *"go ahead with all
the submissions"* alongside four items the plan had carried for over a week. The
authorisation covered the list; the list had grown that morning, and the new
item was not called out as new when it was given. Raising a question in another
organisation's repository is cheap to do and not free to receive, which is the
argument for naming what is new rather than counting it among what was agreed.

Nothing else changes. `08-adopting.md` § 3 already describes the private
marketplace as a fact rather than a temporary state, and § 0.0 already sends an
adopter to the public one.

## The seventh slice — the runners do not fall through, the bare name does

Landed 2026-08-29. It closes no criterion. It pays the debt the fifth slice
recorded and deliberately left open.

### What was wrong

[ADR 0020](adr/0020-a-locus-reaches-the-pinned-artefact.md) § Background said
*"With `node_modules` absent, npx falls through to `PATH`"*, and § Applied case
C said `uv run` does the same when a tool is absent from the project. Both are
statements about a **mechanism**, each made from one observation, on tool
versions nobody recorded. Re-measured on 2026-08-29 at `node v24.19.0`,
`npm 11.17.0`, `uv 0.12.6`, with an impostor first on `PATH`:

```text
npx --no-install markdownlint-cli2 --version   exit 1   npx canceled — missing packages
npm exec --no -- markdownlint-cli2 --version   exit 1   npx canceled — missing packages
markdownlint-cli2 --version           (bare)   exit 0   v9.9.9-IMPOSTOR
uv run ruff --version                          exit 0   ruff 0.16.4  (not the impostor)
ruff --version                        (bare)   exit 0   9.9.9-IMPOSTOR
```

**The runners refuse; the bare name answers.** Neither npx spelling consults
`PATH` — they resolve against their own cache or the registry and fail rather
than run something else. `uv run` does not consult it either: with the tool
absent from the project it produced a real `ruff`, not the impostor. What falls
through to `PATH` is a bare command name, which is ordinary shell resolution and
was never in doubt.

### What did not change

**The decision.** A locus must invoke a pinned tool by the path its lockfile
owns, because every alternative reaches a binary the lockfile does not own — npx
from its cache or the registry, a bare name from wherever `PATH` points. *Which*
wrong binary is reached depends on the tool and its version; *that* a wrong one
is reached has held on all three occasions anyone has looked. ADR 0020 is
amended in place at **revision 3** rather than superseded, which is exactly the
case [ADR 0026](adr/0026-an-adr-stands-on-its-own.md) permits: the decision is
unchanged and the record had become factually false.

### Where it was repeated

The claim had been copied into four `controls.yaml` comments, the checker,
`.claude/skill-config.yaml` and `docs/08-adopting.md` § 3 — the last of which
told an adopter the `PATH` story outright, in a guide this repository publishes.
All are corrected. No control's `rung`, `verify`, `variance` or `applies_to`
moved and no field was added, so **the contract stays at 35**.

Two are deliberately untouched. `docs/09-phase-1.5-review.md` § H6 is a dated
record of what a review found, and dated records are not rewritten — the same
rule that left `standard-check` inside `docs/adr/`. And **CLAUDE.md was checked
and is correct**: it says a bare invocation reaches `npx`, *"which downloads a
version rather than using the one `package-lock.json` pins"*. That is registry
resolution, which is what the new measurement shows, and it happens to be the
one restatement that described the behaviour rather than the mechanism.

### The lesson, which is not about npx

This repository has spent Phase 6 learning that a measurement needs a date, and
learned it twice from someone else's repository — the transport that changed
under a re-verification, and the `CONTRIBUTING.md` line that had been right all
along. This is the same failure in its own record: an observation written up as
a property, in the present tense, with no versions beside it, then repeated
seven times where nothing could check any copy. **Every measurement in the new
section carries the tool versions it was taken on.**

**It is not held by a test, on purpose.** A test asserting how `npx` resolves
would pin another project's behaviour to one machine's npm, and would fail as a
*correct* npm release changed it — reporting a defect here for a change
elsewhere. The guard is the recorded version and date.

## The eighth slice — it installs, as one plugin

Landed 2026-08-29. It closes the criterion that had been waiting on somebody
else since the phase began.

### What happened upstream

[incubator#657](https://github.com/EqualExperts/ee-skills-incubator/pull/657)
merged and `auto-promote.yml` published `plugins/control-register/` into
`EqualExperts/ee-skills`. [#655](https://github.com/EqualExperts/ee-skills-incubator/pull/655)
and [#656](https://github.com/EqualExperts/ee-skills-incubator/pull/656) went
with it, reaching this container as `ee-skills-contribute@0.1.23` and
`lint-md@1.0.10` — both verified to carry the changes this repository argued
for, which is the first time a submission from here has come back as an
installed release.

### How the criterion was judged

**By installing it**, not by reading the manifest.
`claude plugin install control-register@ee-skills` produced one plugin at 0.1.0
with nine skills. The shape the criterion doubts — nine single-skill plugins —
is one the *promotion pipeline* produces from `promote-config.json`, so the
source declaring the right thing proves nothing about the result.

Four artefacts were checked past the skill count, each of which would have left
the install useless while the count looked right:

| Checked | Why it could have failed |
| --- | --- |
| `reference/` at the **plugin root** | Eight of nine skills read it through `${CLAUDE_PLUGIN_ROOT}`; `promote.py` routes bundle-root entries it does not recognise down into `skills/<bundle>/` |
| `templates/` at the plugin root | Same routing, and `gate-build` cannot deploy a devcontainer it cannot find |
| `.claude-plugin/deploys.json` | The per-gate `contractVersion` ADR 0038 added; without it every gate reads `UNRECORDED` forever |
| `LICENSE` | `check_plugin_license.py` fails a plugin without one, and two that disagree is worse than one missing |

All four held. The layout was predicted from `git-summary-plugin`, whose
`backend/` survives at *its* plugin root — a precedent read before the bundle
was assembled rather than a hope confirmed after.

### What did not survive, and is not a re-opening

The marketplace entry reads `"category": "productivity"`, and `categories.json`
still holds `development`, `productivity`, `workflow`, `contributor-tooling`.
**The `governance` category did not land.** It was part of submission 1 and the
pipeline assigned a fallback rather than adding a key.

It is recorded rather than chased because nothing depends on it: no criterion
names the category, the plugin installs and works, and the fix is a one-line
change plus a regenerated README in a repository this project does not own. It
is a follow-up someone may decide to raise, and
[`05-promotion.md`](05-promotion.md) § The `governance` category still holds the
drafted entry and its two consequences.

### The container carries it now

`.devcontainer/setup.sh` installs `control-register` alongside the other six
ee-skills plugins. The two copies do not compete — ADR 0033's symlinks give the
working tree project precedence, so `/gate-*` here still runs what is being
edited. What the installed copy buys is **the artefact an adopter receives being
present to compare against**, which is exactly what this phase kept finding it
could not do from the tree alone: twenty-three dangling links passed every local
test and failed the destination's gate.

### What it deliberately left open

**One criterion remains, and it is the one that matters most.** *The consumer
repo re-adopts from the marketplace copy and still passes* — installing a plugin
is not the same as a repository that did not author it reaching conformance
through the published route. It needs the macOS host with Docker that Phase 4
used. Everything upstream of it is now done.

## The ninth slice — a quoted pin is a pin

Landed 2026-08-29. It closes no criterion. It removes a trap the published copy
of this repository's own template had already fallen into.

### What was found

Installing `control-register` from **both** marketplaces and diffing them showed
the two published copies are not the same plugin. The incubator pushed four
remediation commits onto the submission branch before merging it, and one —
`b1d2220c fix(control-register): make the devcontainer templates
shellcheck-clean` — quoted the placeholders:

```diff
- uv_sha={{UV_SHA256_AARCH64}}
+ uv_sha="{{UV_SHA256_AARCH64}}"
```

That is correct shell style. It broke `tool_versions_match_register`, which
matched `[@=:\s]v?(\d+\.\d+\.\d+)` — a separator followed immediately by
digits — so the quote landed where the separator was expected:

```text
uv_version=0.12.6      -> MATCH 0.12.6
uv_version="0.12.6"    -> NO MATCH — "no uv version pin found"
```

A correctly pinned, shellcheck-clean line read as an unpinned one. An adopter
taking the published template would have failed a control over a version they
had pinned properly.

### The instruction was the defect

CLAUDE.md carried the workaround as a rule — *"Substitute **unquoted**: … a
quote lands where it looks for the separator and the pin is reported missing"* —
which is this checker's brittleness written up as a requirement for every
repository that adopts the standard. It is the shape
[ADR 0018](adr/0018-register-checker-boundary.md) exists to prevent, arriving
from the other direction: not a rule wrongly held in the checker, but a checker
limitation wrongly exported as a rule.

**Two statements here already disagreed, and nobody noticed.**
`tests/test_devcontainer_template.py` asserts `UV_VERSION="{{UV_VERSION}}"`
**passes** — it had stopped believing the instruction, in a test, while the
instruction stood in CLAUDE.md and the assert enforced the opposite. The
disagreement was invisible because no file was ever both quoted and checked.

### The fix, and the hole it also closed

The pattern takes an optional quote after the separator. Five spellings are
covered by `tests/test_section_h.py::test_a_quoted_pin_is_still_a_pin`, and a
sixth test holds the thing that must not follow: tolerating the quote must not
tolerate drift behind it. Confirmed by mutation — reverting the pattern fails
four of the six.

One row is a **hole closed rather than a defect found**: `"uv": "0.12.6"`, a
JSON pin, which the old pattern could not read at all and would have reported as
holding no pin. No `pinned_at` in this register names a `.json` file today, so
nothing was failing; a repository that pinned in JSON would have been told its
pin was missing.

### What it deliberately left open

**Nothing was raised upstream.** The first reading of this was *"they broke our
template"*, and it was wrong: their change is correct, ours was the fragile
half, and an amendment asking them to un-quote a shell script would have been
asking another team to work around a defect in this checker. What remains
outstanding is not a fix but a **divergence** — nine SKILL.md files, ten new
files, and the two template edits — and that is the next slice's job rather than
this one's.

## The tenth slice — the two published copies are one artefact again

Landed 2026-08-30. It closes no criterion. It resolves the divergence the ninth
slice found and deliberately left, and it is the case
[ADR 0044](adr/0044-the-adopter-installs-from-the-public-marketplace.md) named
in advance: *"one artefact published twice, not a fork — and if they ever stop
being the same tree, that is a defect to fix rather than a state to document."*

### What had diverged

The incubator pushed **four remediation commits** onto the submission branch
before merging it, none of which came back here:

| Commit | What it did |
| --- | --- |
| `e41839c3` | `gate-secrets`' description leads with intent rather than control IDs |
| `3ea9bab0` | All nine skills brought to an *Optimised* rubric verdict |
| `3b2298d2` | `gate-quality`'s editor binding rules extracted to their own file |
| `b1d2220c` | The devcontainer templates made shellcheck-clean |

In artefacts: nine `SKILL.md` files rewritten (+27 to +48 lines each, gaining a
`## Calibration` section and a `## Co-update partners` section), ten new files
(an `examples.md` per skill, and `editor-binding-rules.md` for `gate-quality`),
and two template edits. 367 lines of calibration examples that this repository
did not write and that describe its own skills accurately.

### Taken as-is, not rewritten

`plugins/control-register/` is now **byte-identical** to the published copy,
`diff -rq` clean. The alternative — writing our own versions of `examples.md` in
the same shape — was rejected: they pass the rubric, they are accurate, and
restating them differently would be pride rather than engineering. It is the
first time this repository has taken content *from* the marketplace rather than
sending content to it, and the direction is worth noticing: a submission is not
the end of a conversation.

All nine still pass preflight P1–P11. **`gate-repo` is now at 493 lines against
the 500 ceiling**, which is seven lines of headroom on a file that has grown
every time anyone has touched it — the next addition to it fails P1, and it will
fail at submission time unless something here notices first.

### One reference is deliberately left dangling

The `## Co-update partners` sections end with *"Registered in
`docs/skill-relationship-map.md`"* — a registry in the **incubator**, which this
repository does not have. It is kept rather than corrected, for the reason
[ADR 0036](adr/0036-shared-skill-prose-has-one-home.md) already established when
it chose prose citations over links: prose does not dangle, and the sentence is
true where the plugin is maintained. Rewriting it would re-open the divergence
this slice exists to close, over a pointer that costs nothing.

### What made this safe to take

The ninth slice, an hour earlier. `b1d2220c` quoted the template placeholders,
and until `tool_versions_match_register` learned to read a quoted pin, taking
these files would have imported a template that fails DEV-001 on a correctly
pinned container. **Fixing the checker first was what made the merge possible**,
which is the argument for having read the diff before filing an amendment: the
first reading was *"they broke our template"*, and acting on it would have left
this divergence in place and asked another team to work around our defect.

### What it deliberately left open

**Nothing is re-published.** The public marketplace serves this tree, so that
route is current the moment this merges; the `ee-skills` copy is already at this
content. The two are equal without anything being promoted again.

**One criterion remains**: the consumer repository re-adopting from the
marketplace copy, which needs the macOS host with Docker.

## The eleventh slice — the re-adoption ran, on a host this container is not

Ran 2026-08-30 on the macOS Docker host, and closes the criterion the tenth
slice left as the only one outstanding: *the consumer repo re-adopts from the
marketplace copy and still passes*. The runbook it followed is
[`16-marketplace-readoption.md`](16-marketplace-readoption.md).

### Where the record is, and why it is not here

The operator's record is the consumer repository's own `README.md` §
Adoption record, at commit
[`2b89221`](https://github.com/Eaiger-Ent/ee-standard-consumer/commit/2b89221e5f3455520a92668b99f018f9072b578c)
(2026-08-30T08:33:54Z). It is **cited rather than copied**, and pinned to the
commit rather than to the pull request number, for the reason every other
external citation in this file is: a copy of it here would be a second record of
one run, free to drift from the one an adopter reads, and a pull request number
is a pointer to a mutable page where a merge commit is git-tracked and
immutable.

What belongs there is what happened to **that** repository. What belongs here is
what the run proves about **this** one, which is the rest of this section.
[`12-phase-4-review.md`](12-phase-4-review.md) is the same division, and it is
why this repository has a Phase 4 record at all when Phase 4 happened elsewhere.

### What it proves

| Question the criterion asks | What the run measured |
| --- | --- |
| Is the published plugin the same artefact as this tree? | `diff -rq` over the `ee-standard` and `ee-skills` plugin caches is **silent** |
| Does it work when installed rather than developed? | `/register-adopt` dispatched **every** gate from the marketplace install |
| Does the repository still pass? | 12 passed, 0 failed, 1 skipped (`terraform` predicate), 1 unclassified, 3/3 meta-controls, **exit 3** |
| Is the chain to a blocked merge intact? | Both workflows green on `push` and on `pull_request` |

**Exit `3` is the pass**, unchanged from what Phase 4 measured — SEC-003's
remote blocks answer only inside a GitHub Actions job, so a `0` on a developer's
machine would have meant something was skipped that should not have been.

The four failure shapes the runbook named in advance — a control failing that
passed in Phase 4, `DEV-001` failing on the template, a gate unable to resolve
`${CLAUDE_PLUGIN_ROOT}/reference/…`, or a gate that could not be dispatched —
none occurred. Naming them was worth it anyway: three of the four are defects
this phase had already fixed, and a run that found one would have meant a fix
had not held through promotion.

**`/register-adopt` wrote nothing**, every applicable control already being
stamped at register contract 30 by its gate at `0.1.0`. That is the expected
outcome of re-adopting an unchanged repository rather than a no-op to be alarmed
by, and the runbook says so — a gate that rewrites an artefact identically and a
gate that declines to write are the same verdict from the outside.

### The runbook asked for something the consumer cannot run

The one finding, and it is about this repository rather than about the plugin.
§ What passing looks like asks for `register-check deployments`, and the
consumer's checker is pinned at **`v0.5.0`**, which does not have it. The
operator read the gate state from `deployed_by` and the provenance stamps
instead and recorded the substitution, which is the right response and not one a
runbook should require anyone to invent.

**The register contract does not tell you this, and reasoning from it gets the
wrong answer.** The consumer is at contract 30;
[ADR 0038](adr/0038-the-stamp-records-the-deployment-contract.md) landed *at*
contract 30; `v0.5.0` ships contract 30 — and `src/register_check/deployments.py`
is absent from that tag. The contract is a property of the **register** and the
subcommand is a property of the **checker**, and a tag can carry a register
whose contract postdates code the tag was cut before. Checking is one command,
`register-check --help`, and the runbook now says to run it rather than to work
it out.

It is the failure this repository exists to prevent, one document over: a guide
describing tooling that does not exist **at the version the reader has**. The
runbook now asks the question in a form a contract-30 checker can answer, and
says why the newer spelling would not work there.

Two things it is worth being precise about. The consumer being behind is not a
defect — `install.ref` is the last released checker and a consumer pinned to a
tag is exactly what [ADR 0032](adr/0032-the-checker-is-installed-from-a-tagged-ref.md)
prescribes. And the substitution is not equivalent: stamps say what was
deployed, `deployments` reconciles that against what is *installed*
([ADR 0043](adr/0043-a-declination-is-reconciled-against-the-installed-skill.md)),
so the weaker question is the honest one to ask there rather than a shortcut.

### What it deliberately left open

**The record's location was never stated, and that is now fixed rather than
excused.** The runbook said *"Record the result either way"* and named no home,
so the operator chose one; it was a good choice, and it was a choice this
document should have made. Until this slice, the evidence for a criterion of
**this** repository lived only in another repository, reachable by a reader who
already knew the pull request existed.

**One criterion remains**, the last in the phase and in the plan:
[`08-adopting.md`](08-adopting.md) § Status being true on the day of release.
This run is what makes it checkable — the rows claim what the published plugin
does, and until today nothing had installed the published plugin into a
repository that did not author it.
