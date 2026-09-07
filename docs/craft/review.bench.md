# Craft — the bench

Stage **S3** of [`plan.md`](plan.md). What the candidate configuration has to
survive before anyone is asked to install it, and what happened when it was put
through that.

**This document is written in two sittings, by construction.** The acceptance
criteria below were written on **2026-09-06**, before a scaffold existed and
before a single rule was run. Everything after them is the result. Criteria
written after a run are a description of the run, and a stage that grades its
own output against a mark it drew afterwards has measured nothing — which is why
`plan.md` § S3 puts the ordering first and why this file exists before there is
anything to put in its second half.

As of 2026-09-06 only the first half exists. The sections it owes are named at
the end so their absence is visible rather than inferred.

## What this stage is measuring, and what it stopped measuring

`plan.md` § S3 records the rewrite and the reason, and neither is restated here.
What matters for reading the criteria is the shape it left: **the subject is the
configuration, not a body of code.** Every criterion below is decided by
assembling, resolving, running or reading the configuration itself, on a
scaffold written for the purpose. None of them counts findings over an existing
repository, because [ADR
0052](../adr/0052-a-profile-is-a-stack-and-a-strictness.md) targets new ones and
there is no such repository to count over.

Two consequences worth stating before the criteria rather than after:

- **A number this stage sets is a choice with a rationale, not a calibration.**
  Four settings are owed — C6 — and the honest form of each is *this is what we
  chose and why*, revisable at S6 when someone has lived with it. A threshold
  presented as measured, when nothing measured it, would be the most
  self-flattering thing this workstream could ship.
- **A false positive is worth more attention here than it was in the original
  plan, not less.** On a new repository there is no legacy noise for a wrong
  finding to hide in, so it is the whole of what a developer sees. C5 probes the
  rules with a known reputation, one deliberate case each.

## What the criteria are measured on

**A scaffold, per stack.** A repository of the shape the profile is for: the
files a new project has on its first day and nothing else. It is written for
this stage and it is not a sample of anything.

**It is materialised rather than tracked**, by
[`scripts/craft_scaffold.py`](../../scripts/craft_scaffold.py), into `temp/` —
gitignored, the same place S1 put its `llm-toolkit` clone. The first attempt
committed the tree and this repository rejected it, correctly and twice over:

- A scaffold's `pyproject.toml` grows a `[tool.ruff]` section at the next step,
  and ruff resolves every file against the *nearest* configuration. A tracked
  one would quietly become the lint definition `ruff check .` applies to part of
  this tree, in a repository whose central invariant is that there is one.
- Tracked Python that must **fail** a check cannot coexist with TYP-001 and
  LNT-001, which claim all first-party source and admit no exemption. The
  committed attempt failed
  `test_h7_this_repository_declares_coverage_for_every_tracked_module` on its
  first run, which is that check doing exactly what it is for. C2's deliberate
  violations and C5's probes are the same problem, larger.

What is committed is the means to rebuild both scaffolds byte for byte. A
measurement nobody can re-derive is a claim, and a scaffold nobody can rebuild
is the same thing one directory down.

**The constraint that makes that meaningful:** no measurement in this document
may be taken over code that was not written for it. If a number here ever comes
from an existing repository, the rewrite has been quietly undone and the stage
is measuring the risk `plan.md` § S3 says the target does not carry.

**Every run records the version it ran at.** The profile pins tools, so the
bench runs at the versions the profile pins and names them in the result. A
measurement whose version is unrecorded rots the way `survey.sources.md`'s
maintenance signals rot, and this document owes the same re-derivable answer:
the version, and the command that produced it.

## The scaffolds

Two, built 2026-09-07 and rebuilt from
[`scripts/craft_scaffold.py`](../../scripts/craft_scaffold.py) on every run.
Twelve files between them. Both were run before being recorded here: the Python
scaffold's four tests pass and the React scaffold type-checks clean under
`tsc --noEmit` and passes its three.

| | Python — `ledger` | React — `storefront` |
| --- | --- | --- |
| Manifest | `pyproject.toml`, `src` layout, `pythonpath = ["src"]` | `package.json`, `tsconfig.json` with the strict family on, `vitest.config.ts` |
| Source | `src/ledger/entries.py` — a frozen dataclass, a domain error, `pathlib`, `Decimal`, timezone-aware datetimes | `src/lib/money.ts` (no React), `src/components/Basket.tsx` and `BasketRow.tsx` |
| Tests | `tests/test_entries.py`, four cases | `src/components/Basket.test.tsx`, three cases, Testing Library and `user-event` |

They are small deliberately. A scaffold is not a demonstration of the language;
it is the smallest thing that gives every selected rule somewhere to look. What
each file is there to carry:

- **A component, a plain module and a test**, because C1 resolves the
  configuration for one file of each kind and the type-checked rules need a
  `tsconfig` that actually covers them.
- **A hook, a `useMemo` and a `setState` in an event handler**, so the
  Rules-of-React and effects rules have a subject. `Basket.tsx` derives its
  total during render rather than in an effect, which is the property
  `react.no-derived-state-in-effect` asserts — the anti-pattern React's own
  documentation opens with, and the rule its plugin ships `off`.
- **A link whose text is ambiguous and whose `aria-label` is not.**
  `<a href="/checkout" aria-label="Continue to checkout">Continue</a>` is C5's
  first probe, written into the scaffold rather than bolted on: correct code
  that `jsx-a11y/anchor-ambiguous-text` is known to flag because it cannot see
  the label.
- **`assert` in a test and nowhere else**, which is what
  `python.no-assert-for-enforcement` scoped to the source path has to
  distinguish.

### What building them already found

**The profile's ESLint version is decided by its quietest dependency.** Read
from the published peer ranges rather than the release notes:

| Package | Peer range | Consequence |
| --- | --- | --- |
| `eslint-plugin-jsx-a11y` 6.10.2 | `^3 \|\| … \|\| ^9` | ESLint 10 is out |
| `eslint-plugin-react` 7.37.5 | `^3 \|\| … \|\| ^9.7` | ESLint 10 is out |
| `typescript-eslint` 8.69.0 | `typescript >=4.8.4 <6.1.0` | TypeScript 7 is out |
| `eslint-plugin-react-hooks` 7.1.1, `eslint-plugin-testing-library` 7.16.2 | `^10.0.0` accepted | not the constraint |

ESLint is at **10.10.0** and TypeScript at **7.0.2**. The scaffold pins ESLint
**9.39.5** and TypeScript **5.9.3**, and npm reports 9.39.5 as no longer
supported on install.

That is not a scaffold decision, it is a profile one, and it is the survey's
finding 8 arriving with a bill: `jsx-a11y` was registered as *the quietest
source here* on a last publish of 2024-10-26, and it is the only instrument for
eleven accessibility properties. A profile that wants them is on ESLint 9. The
alternative — dropping the accessibility group to reach a supported ESLint — is
a real option and belongs to S4, with this measurement under it rather than a
preference.

**The Python scaffold needs `pythonpath` rather than an install.** `src` layout
with no packaging step; pytest's own good practices recommend installing the
package first, which would put a second virtualenv and a second lockfile inside
the repository carrying the scaffold for no gain. Recorded because
`python.test-layout` is a selected property and this is the shape it will be
measured against.

## The acceptance criteria

Nine. Each states what it asserts, what decides it, and **how it fails** — a
criterion with no failing case is a description wearing a criterion's clothes,
and this repository has an ADR about writing those down rather than discovering
them later.

They are numbered C1 to C9 so a demotion later in this document can cite the
criterion that demoted it.

### C1 — The configuration assembles

Both stacks' candidate default-on configurations load, at pinned versions, with
every selected rule resolving to a rule the tool actually has.

**Decided by.** Python: the selected set resolves under the pinned ruff, with no
selector matching nothing. React: `eslint --print-config` returns a resolved
configuration for one file of each kind the scaffold contains — a `.tsx`
component, a plain `.ts` module, and a test file — with all six plugins loaded,
all three presets resolved, both `disable-conflict` configs applied and the
type-checked rules bound to a real `tsconfig`.

**Fails if.** Any plugin or preset fails to resolve; any rule name is unknown to
its plugin; any selector matches no rule; or the type-checked rules load without
a `tsconfig` for them to read, which is a configuration that will fail on the
developer's machine rather than on ours.

This is first because it is the first thing a developer meets, and because it is
genuinely unknown. Six plugins, three presets and two conflict configs have
never been composed together in this workstream, and `assess.rules.md` finding 2
says as much in the register rather than asserting the composition works.

### C2 — It runs, and it is shown to be running

The configuration produces a verdict in both directions: clean on the scaffold,
and non-zero on deliberate violations.

**Decided by.** A clean run over the scaffold exits `0` with no diagnostics. A
violation file per stack — one deliberate defect per selected rule family —
exits non-zero and names the rule that caught each.

**And, separately: every rule the profile enables against its own plugin's
default fires on a case written for it.** `assess.rules.md` names ten React
rules that are `off` in every preset, `strict`-only, `type-checked`-only or in
no preset at all; that list is the checklist. For Python, where ruff's default
selection is `E4`, `E7`, `E9` and `F` and the profile therefore enables
everything else against the default, the demonstration is per selected rule
family rather than per code.

**Fails if.** The clean scaffold reports anything; a deliberate defect reports
nothing; or a rule on the checklist cannot be made to fire. The third is the one
worth the trouble: a rule name that resolves and then never runs — shadowed by a
later config object, or set at a severity that reports nothing — is
indistinguishable from a rule that is working, and it is the failure this
workstream would be least able to see.

### C3 — No two selected rules contradict each other

For no pair of selected rules does satisfying one necessarily violate the other
on code that is otherwise correct.

**Decided by.** An exhaustive pass over the selected set, by a **method recorded
here** rather than by having looked. The known pair is `python.return-count`:
`PLR0911` counts exit points, an early return is the recommended fix for
`clean-code 102`'s nesting, and the two cannot both hold — it is recorded as
`incompatible` and permanently off. The pass looks for the others, and it
records the pairs it considered and cleared as well as any it finds.

**Fails if.** A contradicting pair is found and both rules remain selected; or
the method is not written down, in which case the negative result is a claim
rather than a search.

A cleared pair is evidence and an unrecorded search is not, which is why the
considered-and-cleared list is part of the criterion and not a courtesy.

### C4 — No defect is reported twice

One defect produces one diagnostic.

**Decided by.** The nine rule names `assess.rules.md` finding 2 lists as shipped
by both `react-hooks` 7.x and `@eslint-react` 5.x — `rules-of-hooks`,
`exhaustive-deps`, `set-state-in-effect`, `set-state-in-render`, `purity`,
`static-components`, `use-memo`, `error-boundaries` and `unsupported-syntax`.
One deliberate defect each, and a count of the diagnostics: exactly one.

**Fails if.** Any deliberate defect draws two diagnostics from two plugins, and
the profile still names both plugins without the conflict config that separates
them.

Double-reporting is not a cosmetic problem on a new repository. It is the same
defect arriving twice with two different rule names attached, which teaches a
developer on their first day that the tool does not know what it is talking
about.

### C5 — Every probed false-positive case is clean, or the rule is demoted with the case recorded

**Decided by.** A probe per rule with a known false-positive reputation: a piece
of **correct** code that the rule is known to flag, written deliberately. Three
are named by `todo.md` and are the starting set, not the whole of it —
`jsx-a11y/anchor-ambiguous-text` against a link carrying an `aria-label`, ruff
`S101` against a test, and
`@typescript-eslint/explicit-module-boundary-types` against a component.

**Fails if.** A probe fires and the rule remains selected with no recorded case;
or a probe is dropped because it fired.

Note the second half. A rule may survive a probe that fired — the case may be
rare enough, or the finding arguable enough, that keeping it is right — but the
case goes in this document either way. What may not happen is a probe quietly
disappearing between being written and being reported, which would make the
clean sweep an artefact of the sweeping.

### C6 — Every number the resolutions left owed is set, with a stated rationale

Four, from `assess.rules.md` § Resolved: `python.function-length`'s threshold,
`python.line-length`'s default, `python.no-any`'s strict variant, and
`react.explicit-return-types`' scope.

**Decided by.** Each carries a value and a paragraph saying why that value and
not its neighbours, together with what would change it.

**Fails if.** A number ships without a rationale, **or a rationale cites a
corpus measurement this stage did not make.** The second clause is the guard: a
threshold justified by "typical codebases show" would be the deleted premise
walking back in wearing a citation, and the whole reason S3 was rewritten is
that this stage has no corpus to cite.

`python.line-length` carries an extra constraint from its resolution — the
number must equal `ruff format`'s — so its rationale settles one number and not
two.

### C7 — Cost per finding is recorded for every selected rule

What a finding costs to satisfy, per rule, from the tools' own metadata.

**Decided by.** Python: `fix_availability` from the pinned ruff taxonomy reads
`always`, `sometimes` or `none` per rule, and needs no run — 421 of the 812
stable rules carry no fix at all. React: the same question is answered by each
rule's own `meta.fixable` and `meta.hasSuggestions`, read from the installed
plugins. The profile's selection carries the totals.

**Fails if.** A selection is published without them. This is the criterion S5
consumes directly: `plan.md` § S5 requires the installer to present each profile
with **what S3 found each rule costs to satisfy**, and a selection with no cost
column leaves that promise with nothing behind it.

### C8 — The preview question is answered by enumeration, not by preference

`python.nesting-depth` and `python.class-size` are reachable only through ruff's
`preview = true`, which enables all 140 preview rules at once and cannot be
enabled for two of them.

**Decided by.** Enumerating the 140 from the pinned taxonomy, classifying what
else they would turn on, and running the preview set over the scaffold. The
outcome is a decision with a number behind it: either the profile enables
preview and names everything else that arrives with it, or the two properties
stay off and are recorded as **unreachable** rather than as declined.

**Fails if.** The answer is a preference with no enumeration behind it.

The distinction between *unreachable* and *declined* is the whole value of the
criterion. A property this workstream wants and cannot have is a finding about
the tool; a property it chose against is a finding about the profile. Recording
one as the other loses the reason anybody would revisit it.

### C9 — What S2 deferred is read from an installed tree, not asserted

Two questions, both deferred here by name.

**Decided by.** Installing the plugins and reading them. What
`@eslint-react`'s `disable-conflict-eslint-plugin-react` and
`disable-conflict-eslint-plugin-react-hooks` configs actually contain —
`assess.rules.md` records that S2 could not resolve them from the published
bundle and *recorded that rather than asserting it*. And `@eslint-react`'s
coverage against the 104 rules `eslint-plugin-react` carries, which is what
`assess.contested.md` rows 10 and 11 were resolved contingent on.

**Fails if.** Either is answered from documentation. S2's sharpest findings came
from reading published bundles rather than documentation sites — findings 1 to 3
exist only because of it, and the ruff count was corrected the same way — and a
stage that reverted to the docs would be discarding the method that produced the
register it is benching.

## What these criteria deliberately do not contain

- **No findings-per-KLOC ceiling**, and no threshold of any kind over a body of
  existing code. `plan.md` § S3 records why the original had one and why it went.
- **No sampling.** The false-positive question is answered by deliberate probes
  — C5 — because sampling needs a corpus and there is none.
- **No judgment of whether the rules are the right rules.** That was S2's, it is
  in `assess.rules.md`, and re-litigating it here would be a second copy of a
  register that already exists. This stage asks whether the configuration works,
  not whether the selection is wise.
- **No feel.** Whether the profile is pleasant to work under is S6's, and
  `plan.md` says so in terms: since the rewrite, S6 is the only stage that
  observes the profile in a repository somebody is working in.

## How these criteria discharge the stage's exit criterion

`plan.md` § S3's exit criterion is:

> the configuration assembles and runs clean on a scaffold of each stack, no
> selected rule contradicts another, and every demotion cites the case that
> demoted it.

Three clauses, discharged by C1 and C2, by C3, and by C5 respectively.

**The other five criteria are more than the exit criterion asks for**, and that
is deliberate rather than accidental scope. C4 and C9 answer questions
`assess.rules.md` explicitly deferred to this stage; C6 settles what its
resolutions left owed; C7 is what S5 has been promised; C8 closes the one
question S2 named as *a real decision with a measurable cost, and S3's to
measure*. A stage that met only its exit criterion would leave all five for
someone to rediscover.

The criterion is still the criterion. **This stage is finished when `plan.md`'s
three clauses hold, however many of C1 to C9 are ticked** — the same rule
`todo.md` states about boxes, applied to a document that could otherwise grade
itself generously by counting its own headings.

## What this document still owes

Named so their absence is visible, in the order they will be written:

- **The candidate configuration** — the default-on selection per stack, built
  from the resolved register.
- **What ran** — C1, C2, C4 and C8, with versions and commands.
- **What fought** — C3's pass: the method, the pairs cleared, and anything found.
- **What was probed** — C5, one case per rule, with the outcome of each.
- **What each rule costs** — C7's table.
- **The four numbers** — C6, each with its rationale.
- **What was read from an installed tree** — C9's two answers.
- **What was demoted, and the case that demoted it** — the criterion each
  demotion cites.
