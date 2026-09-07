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

The second half began on 2026-09-07 with the candidate configuration. The
sections still owed are named at the end so their absence is visible rather
than inferred.

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

- A scaffold grows a ruff configuration of its own at the next step — a
  `ruff.toml`, as it turned out — and ruff resolves every file against the
  *nearest* one. A tracked config would quietly become the lint definition
  `ruff check .` applies to part of this tree, in a repository whose central
  invariant is that there is one.
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

## The candidate configuration

Built **2026-09-07** from the resolved register, and materialised by
[`scripts/craft_profile.py`](../../scripts/craft_profile.py) into the same
gitignored `temp/craft-bench/` the scaffolds are written to.

**It is a second script rather than more of `craft_scaffold.py`, and the split
is the bench's.** The scaffold is the *subject*; this is the *instrument*. S3
varies the instrument — a demotion, `preview = true` for C8, a probe flipped on
for C5 — and must leave the subject exactly as it was, which it cannot do if the
two share a file. It also means the Python configuration is a `ruff.toml`
beside the scaffold's `pyproject.toml` rather than a `[tool.ruff]` section
inside it. Which surface the *installed* profile writes is S4's question and
this file does not answer it.

| | Python | React |
| --- | --- | --- |
| Written to | `python/ruff.toml`, `python/src/ruff.toml` | `react/eslint.config.js` |
| At | ruff 0.16.5 | ESLint 9.39.5, plus the six plugins the scaffold pins |
| Size | 65 selectors resolving to **141 rules** | **89 rules named on**, plus one named `off`, over two preset bases |
| Presets used | none — ruff's default `E4`, `E7`, `E9`, `F` is replaced outright | `@eslint-react` `recommended` and `jsx-a11y` `recommended`, and no others |

The 141 is the selection expanded against the pinned taxonomy, not against a
ruff run: **none of the 141 is a preview rule and none is removed**, which is
what C8 predicted — `python.nesting-depth` and `python.class-size` are the two
properties preview would reach, and neither is selected.

**Two rules of construction, both of them the register's.** Presets are used
where the register names a preset and nowhere else: `@eslint-react`'s
`recommended` because the register resolved `react.no-legacy-proptypes` and
`react.jsx-runtime-assumed` by choosing it, `jsx-a11y`'s because the register
counts five of its rules as inherited rather than keyed. And **every rule the
register names is written out even where a base already enables it** — finding 1
is a rule this workstream wants that its plugin ships `off`, and the same
mechanism removes a rule from a preset in a later release without saying so.

### Where the citation had to be read more closely than it was written

Nine places. None of them is a change to the register: each is what building a
configuration from a prose citation costs, and every one is a candidate finding
for the Craft register's schema at S4, where an instrument is data rather than a
sentence.

| # | The register says | The configuration does | Why |
| --- | --- | --- | --- |
| 1 | `python.annotate-public-api` — ruff `ANN001`, `ANN201`, `ANN2xx` | Selects `ANN001`, `ANN201`, `ANN204`, `ANN205`, `ANN206` | `ANN202` is the *private* function's return type and the property says public. Reading `ANN2xx` literally would enforce the opposite of what the row asserts |
| 2 | the same row | Leaves out `ANN002` and `ANN003` | `*args` and `**kwargs` annotations are not cited, and a configuration that adds what it was not given is not built from the register |
| 3 | `python.timezone-aware-datetimes` — `DTZ001`–`DTZ012` | Selects the linter, `DTZ` | The range predates `DTZ901`, which asserts the same property under 0.16.5 |
| 4 | `python.pathlib-over-os-path` — `PTH100`–`PTH210` | Selects `PTH` | Same shape: `PTH211` is outside the range and inside the property |
| 5 | `python.naming-form` — `N801`–`N818` | Selects `N` | Same shape again: `N999` |
| 6 | `python.no-assert-for-enforcement` — `S101` **scoped to the package source path** | A nested `src/ruff.toml` that extends the root and adds `S101` | Ruff has no per-path *select*. It has `per-file-ignores`, which is the exemption the resolution rejected. The scope costs a second configuration file, and an installer writing this profile writes two |
| 7 | `react.list-keys`, `react.no-unknown-dom-property`, `react.safe-external-links`, `react.no-deprecated-api`, `react.props-and-state-immutable` — an `eslint-plugin-react` rule **and** an `@eslint-react` rule | Takes the `@eslint-react` instrument in every case | Naming both is finding 2's double-report at a different pair of plugins. One property, one instrument |
| 8 | `react.no-comment-textnodes` — `react/jsx-no-comment-textnodes` | Takes `@eslint-react/jsx-no-comment-textnodes` | The plugin the register did not cite here has the rule, and the citation is the only reason to prefer the one that would drag a second plugin's preset in |
| 9 | `react.explicit-return-types` — exported non-component functions | `@typescript-eslint/explicit-module-boundary-types` on `src/**/*.ts` and not on `*.tsx` | A file pattern is the closest ESLint gets to "not a component". A component written in a `.ts` file defeats it, which is a real limit and C6's to settle |

Row 7 has a consequence worth stating on its own. **`eslint-plugin-react` ends
up carrying exactly one rule** — `jsx-no-duplicate-props`, the one property in
the register with no `@eslint-react` instrument. The plugin is one rule away
from being unnecessary, which is the shape of the answer the C9 coverage
question is looking for rather than the answer itself.

### What this already puts to the criteria, without settling any of it

Three things the build ran into. Each belongs to a criterion that has not been
run yet, and each is recorded here so the criterion meets it rather than
discovers it.

- **C1 asks for both `disable-conflict` configs applied; this configuration
  applies one.** `disable-conflict-eslint-plugin-react-hooks` is applied,
  because `react-hooks` owns the nine names finding 2 lists.
  `disable-conflict-eslint-plugin-react` is not, because nothing from
  `eslint-plugin-react`'s presets is installed and a single rule outside them
  has nothing to stand down. Whether C1's clause is satisfied, unsatisfiable, or
  pointing at a better configuration is C1's to decide — the criterion is not
  edited to fit what was built. **C1 has since decided, and the belief in this
  bullet was wrong**: the config applied here stands down the wrong plugin, and
  the configuration now applies neither. § The defect C1 found is what happened.
  The bullet stands as written because a prediction corrected is worth more than
  a prediction deleted.
- **C4 has a candidate pair that finding 2 does not list.**
  `react-hooks/static-components` and
  `@eslint-react/no-nested-component-definitions` are cited by the register for
  one property, `react.no-nested-component-definitions`, under two different
  rule names — so the conflict config, which works by name, will not separate
  them. Both are selected, deliberately, so that C4 has the pair in front of it.
- **C9's premise is off by one.** The installed `eslint-plugin-react` 7.37.5
  carries **103** rules, not the 104 `todo.md` names. The coverage question is
  unchanged; the number it is asked against is corrected here, and § What was
  read from an installed tree answers it.

### What has not happened

**Nothing in either configuration has been run.** The React config's module
loads and its imports resolve, which was checked while writing it and is not
C1: `eslint --print-config` over one file of each kind is C1, and it has not
been run. The ruff selection has been expanded against the pinned taxonomy and
not passed to ruff.

Two settings are carried at ruff's own defaults and marked provisional in the
file, because they are C6's to justify and C6 has not run: `max-complexity = 10`
and `max-statements = 50`, both halves of `python.function-length`.
`line-length = 88` is the register's own proposal and satisfies its constraint
by construction — one key serves `ruff format` and `E501`, so the two cannot
disagree — but the number still owes C6 its paragraph.

One question the build could not answer and C1 can. `target-version` is absent
from `ruff.toml`, deliberately, on the same reasoning `CLAUDE.md` gives for this
repository: ruff derives the floor and writing it out is a second copy. Whether
ruff still derives it from `requires-python` in a *sibling* `pyproject.toml`
when the configuration it is reading is a `ruff.toml` is not something reading
the taxonomy answers.

## What ran — C1, the configuration assembles

Run **2026-09-07**, at ruff **0.16.5** and ESLint **9.39.5** with the plugin
versions the scaffold pins. Every command below is re-runnable against a
scaffold rebuilt from the two scripts.

**C1 is met on both stacks, and it found a defect on the way.** The defect is
the third subsection; it is recorded before the verdict rather than after,
because a criterion that reports only its verdict has thrown away the thing it
was for.

### Python

```bash
cd temp/craft-bench/python
ruff check --show-settings src/ledger/entries.py
ruff check --show-settings tests/test_entries.py
```

| What C1 asks | What resolved |
| --- | --- |
| The selected set resolves | **141 rules** under `src/`, **140** under `tests/` |
| No selector matches nothing | None. Ruff rejects an unknown selector outright, and the 141 is the same number the pinned taxonomy gave when the selection was written |
| `python.no-assert-for-enforcement` is scoped, not exempted | `S101` is in the `src/` set and absent from the `tests/` set, and `linter.per_file_ignores = {}` in both. The scope holds and no exemption exists to drift |

Two settings the criterion did not ask about and the last slice left open.
**`target_version` resolves to 3.14** — `linter.unresolved_target_version`,
`formatter.unresolved_target_version` and `analyze.target_version` all read it —
so ruff *does* infer the floor from `requires-python` in a sibling
`pyproject.toml` when the configuration it is reading is a `ruff.toml`. The
question that opened was whether writing the version out could be avoided; it
can. And `linter.line_length` and `formatter.line_width` both resolve to 88 from
the single key, which is `python.line-length`'s constraint demonstrated rather
than asserted.

### React

```bash
cd temp/craft-bench/react
npx eslint --print-config src/components/Basket.tsx   # a component
npx eslint --print-config src/lib/money.ts            # a plain module
npx eslint --print-config src/components/Basket.test.tsx
npx eslint src                                        # it executes
```

| What C1 asks | What resolved |
| --- | --- |
| A resolved configuration for one file of each kind | All three print, with no error |
| All six plugins loaded | Six: `@eslint-react` 5.18.9, `@typescript-eslint` 8.69.0, `jsx-a11y` 6.10.2, `eslint-plugin-react`, `react-hooks`, and `testing-library` 7.16.2 on the test file only |
| No rule name unknown to its plugin | **133 distinct rules enabled across the three files, and every one of them is in its plugin's `rules` map.** Checked by reading the plugins rather than by waiting for ESLint to say so |
| The type-checked rules bound to a real `tsconfig` | `projectService: true` with a `tsconfigRootDir` in all three, **and demonstrated**: a throwaway file with an unawaited promise drew `@typescript-eslint/no-floating-promises`, which cannot fire without type information |
| All three presets resolved | **Two**, not three, and the shortfall is a correction rather than a failure — see below |
| Both `disable-conflict` configs applied | **Neither, deliberately.** See below |

The counts per file: 121 rules on a component, 122 on a plain module — the extra
one is `explicit-module-boundary-types`, which is scoped to `*.ts` and so lands
on the module and not the component, exactly as `react.explicit-return-types`
asks — and 132 on a test.

`npx eslint src` **exits 0 over the scaffold's five files with no diagnostics**.
That is half of C2 arriving early. It is not C2: the other half is a deliberate
violation per rule family and the checklist of rules that had to be enabled
against their own plugin's default, and neither has been written.

### The defect C1 found: both conflict configs point the other way

`assess.rules.md` finding 2 says `@eslint-react` ships
`disable-conflict-eslint-plugin-react` and
`disable-conflict-eslint-plugin-react-hooks` because the enforceable React set
is covered twice, and left what they contain to be read here. Read from the
installed tree, they are:

| Config | Contains |
| --- | --- |
| `disable-conflict-eslint-plugin-react` | 40 entries, all `off`, **all of them `react/*`** |
| `disable-conflict-eslint-plugin-react-hooks` | 12 entries, all `off`, **all of them `react-hooks/*`** |

**Both stand down the other plugin so that `@eslint-react` owns the overlap.**
That is a coherent design and it is the opposite of what this register cites:
most Rules-of-React and effects rows name a `react-hooks` rule, and the two
rules this profile most wants — `no-deriving-state-in-effects`, which is
finding 1, and `preserve-manual-memoization` — have no `@eslint-react`
equivalent at all.

The candidate configuration had applied
`disable-conflict-eslint-plugin-react-hooks` **believing it stood down
`@eslint-react`'s copies**. It did not, and because the `react-hooks` block came
after it and re-enabled the twelve it had turned off, the config was a no-op and
**seven rules were resolving twice**: `rules-of-hooks`, `purity`,
`set-state-in-render`, `set-state-in-effect`, `exhaustive-deps`, `use-memo` and
`static-components`. On a new repository that is one defect arriving under two
rule names on the first commit, which is what C4 exists to prevent — and it
would have been invisible to anything short of resolving the configuration and
counting.

**What changed.** Neither shipped config is applied. `react-hooks` keeps the
ownership the register gives it, and the seven `@eslint-react` copies are turned
off by hand in the same block that claims them, so the claim and the standing-down
read together. `disable-conflict-eslint-plugin-react` stays unapplied for the
reason the last slice guessed and this run confirmed: it turns off forty
`react/*` rules and this profile enables one, `jsx-no-duplicate-props`, which is
not among them. After the change **no rule name resolves twice** across the
three files.

That is C1's verdict on its own last clause: the clause asked for both configs
and the answer is that applying either would have been the defect rather than the
fix. The criterion is not edited to match; it is answered, and what it was
standing in for — one defect, one diagnostic — is still C4's to measure with
deliberate cases.

### Three corrections this run makes to the register

- **The overlap is twelve rule names, not nine.** `assess.rules.md` finding 2
  lists nine; the plugins ship `globals`, `immutability` and `refs` under both
  names too. Seven of the twelve were the ones actually resolving twice here,
  because the other five are enabled on one side only.
- **There are two rule-carrying presets, not three.** `@eslint-react`'s
  `recommended` and `jsx-a11y`'s. The third thing this configuration composes,
  `tseslint.configs.base`, carries a parser and a plugin registration and **no
  rules**, so counting it as a preset would inflate what was inherited.
- **`eslint-plugin-react-hooks` misreports its own version.** The installed
  package is 7.1.1 and its `meta.version` says 7.0.0, which is what
  `--print-config` echoes. A version recorded from the resolved configuration
  would be wrong; this document takes plugin versions from the lockfile.

## What was read from an installed tree — C9's coverage answer

`assess.contested.md` rows 10 and 11 took option **B** — `@eslint-react`'s
`recommended` as the JSX-correctness base, `eslint-plugin-react`'s `recommended`
not installed — and left the decision *contingent on S3 confirming rule
coverage*. This is that confirmation, read on **2026-09-07** from the installed
5.18.9 and 7.37.5 rather than from either plugin's documentation.

**The contingency holds.** One rule of the register's own is uncovered, and it
is the one the configuration already takes directly. One rule outside the
register is genuinely lost, and it is named below rather than left to be
discovered.

### The method, and why it is not a name match

`@eslint-react` ships `disable-conflict-eslint-plugin-react`, and that config
**is the plugin author's own declaration of what it overlaps**: 40 entries, all
`react/*`, all `off`. Coverage read from it is coverage the replacing plugin
asserts, not coverage inferred by matching names — which would have failed
immediately, because the counterparts are not named alike. `react/no-danger`
is `@eslint-react/dom-no-dangerously-set-innerhtml`; `react/jsx-key` is
`no-missing-key`. A name match would have reported both as gaps.

The number is **103 rules, not the 104** `todo.md` carried.

### Recommended against recommended

`eslint-plugin-react`'s `flat.recommended` turns on 21 rules. Thirteen are
declared covered. The eight that are not, read by hand:

| Rule | What B does about it |
| --- | --- |
| `react/jsx-no-duplicate-props` | **A real gap, and the one the register cites.** `react.no-duplicate-props` has no `@eslint-react` instrument, which is why the configuration takes this single rule from `eslint-plugin-react` outside its presets |
| `react/no-unescaped-entities` | **A real loss.** No counterpart, and no register row asserts the property either — so B drops a rule A would have installed, silently, unless it is written down. It is written down here |
| `react/react-in-jsx-scope` | Not covered because it is obsolete. This is `react.jsx-runtime-assumed`, and not having it is the whole point of row 11 |
| `react/jsx-uses-react` | The other half of the same obsolescence — it exists to mark `React` used for a `no-unused-vars` rule that no longer needs it |
| `react/jsx-uses-vars` | Marks JSX-referenced identifiers as used for core `no-unused-vars`. This profile enables no unused-variable rule on the React side, so nothing depends on it. **A strictness level that adds one would need it back**, and that is S4's to remember |
| `react/jsx-no-undef` | An undefined JSX identifier is a TypeScript error before a lint rule sees it. Covered by the compiler, which `react.strict-type-checking` already requires |
| `react/no-is-mounted` | Class-component legacy. `react.no-class-components` is on, so the construct it guards cannot exist |
| `react/require-render-return` | The same: a `render` method needs a class |

So of the eight, one is handled directly, one is a recorded loss, two are the
obsolescence row 11 exists to shed, and four are made unreachable by rules this
profile already enables.

### What the register actually needed

The register cites eight `eslint-plugin-react` rule names across six properties.
**Seven are declared covered; `jsx-no-duplicate-props` is the eighth.**

| Cited | Covered |
| --- | --- |
| `jsx-key`, `jsx-no-comment-textnodes`, `jsx-no-target-blank`, `no-unknown-property`, `no-deprecated`, `no-direct-mutation-state`, `no-danger` | yes |
| `jsx-no-duplicate-props` | **no** |

That is the same answer the configuration reached when it was built, arrived at
from the other direction: five properties took an `@eslint-react` instrument
because one existed, and this one did not.

### The other 56

Fifty-six of the 103 are uncovered *and* outside `recommended` — the plugin's
opinionated and stylistic surface: `jsx-sort-props`, `jsx-max-depth`,
`forbid-component-props`, `function-component-definition`, and the JSX spacing
family. **Neither option installs them and no register row cites one**, so they
are not a coverage question. They are recorded here so that "64 rules have no
counterpart" cannot later be read as a gap when 56 of them are a surface nobody
selected.

## What fought — C3, the contradiction pass

Run **2026-09-07**. C3 asks for an exhaustive pass **by a method recorded here
rather than by having looked**, and for the pairs cleared as well as any found.
The method is three passes and a stated limit; the result is **no contradicting
pair among the selected rules**, one rule-versus-configuration conflict that
measurement dissolved, and seven pairs cleared by name.

### The method

**A pair contradicts if satisfying one *necessarily* violates the other on code
that is otherwise correct.** That word is what makes the search tractable: a
single piece of code where both rules **apply** and both are **satisfied**
refutes it. So the pass is not an argument about 9,870 pairs; it is a reduction
followed by witnesses.

**Pass 1 — the formatter.** `python.consistent-formatting` is met by running
`ruff format`, so a selected rule that fights the formatter is a contradiction
between two things this profile requires. Ruff answers this itself.

```bash
ruff format --check --config ruff.toml src      # the candidate selection
```

It prints no warning. **That negative result is only worth something because the
check was shown able to fire**: the same command over a copy of the selection
with `COM812`, `ISC001` and `W191` added prints

> warning: The following rule may cause conflicts when used with the formatter:
> `missing-trailing-comma` (`COM812`) …

so the silence over the candidate selection is ruff saying nothing is wrong
rather than ruff not looking.

**Pass 2 — reduce by construct.** Two rules can only contradict if both can
apply to the same construct. Each of the 141 selected rules is assigned the
construct it constrains, and only pairs inside one construct are candidates.
Then one further removal: within a family whose rules target **disjoint**
constructs by construction — `PTH`, `DTZ`, `N`, `C4`, `ARG`, `G` — no two rules
can apply to one expression at all, so no pair inside them is a candidate
either.

| | Pairs |
| --- | --- |
| Brute force over 141 rules | 9,870 |
| Same construct | 1,220 |
| **After removing the disjoint-target families** | **273** |

| Construct | Rules | Candidate pairs |
| --- | --- | --- |
| signature | 20 | 180 |
| security-sensitive call | 7 | 21 |
| test | 7 | 21 |
| comprehension | 20 | 19 |
| exception handler | 6 | 15 |
| binding | 4 | 6 |
| logging call | 5 | 4 |
| import | 3 | 3 |
| line layout | 3 | 3 |
| body size | 2 | 1 |
| filesystem call, datetime call, name | 35, 10, 16 | 0 — disjoint targets |
| attribute access, comment, suppression | 1 each | 0 — nothing to pair with |

**Pass 3 — a witness per construct.** For each group, one piece of code in which
every rule in the group applies and every rule is satisfied. A clean witness
clears every pair in its group at once. The witnesses are
[`scripts/craft_cases.py`](../../scripts/craft_cases.py) — committed, because a
cleared pair nobody can re-derive is a claim.

```bash
cd temp/craft-bench/python && ruff check --config src/ruff.toml cases/src
cd temp/craft-bench/python && ruff check --config ruff.toml cases/tests
cd temp/craft-bench/react  && npx eslint src && npx tsc --noEmit
```

All clean, and the Python test witness's four tests pass. The React witness
type-checks as well as lints, because "otherwise correct code" has to compile
before a lint result about it means anything.

**The limit, stated rather than left to be found.** The construct partition is a
judgement, not a proof: a pair that contradicts only through some third
construct would pass straight through it. And a witness clears the shapes it
exercises, not every shape of its group. This pass is a reduction plus evidence,
and it is stronger than reading 273 pairs and weaker than deciding 9,870.

### The pairs worth naming, and why each is clear

| Pair | Why it is not a contradiction |
| --- | --- |
| `jsx-a11y/no-static-element-interactions` ↔ `jsx-a11y/prefer-tag-over-role` | **The sharpest one.** A `div` with an `onClick` and no role trips the first; add `role="button"` and it trips the second. Neither horn is satisfiable — and that is the point: both are satisfied by a native `<button>`, which is the fix both rules were asking for. A pair that cannot be satisfied *in the construct it complains about* is not contradictory if the correct code is a different construct |
| `@eslint-react/no-missing-key` ↔ `@eslint-react/no-array-index-key` | A key is required and the index is banned. A stable id satisfies both; the pair only bites where there is no id, which is a data problem rather than a rule fight |
| `react-hooks/exhaustive-deps` ↔ `preserve-manual-memoization` ↔ `use-memo` | One dependency array satisfies all three. The witness carries a `useCallback` inside a `useMemo`'s dependencies, which is where they would collide if they did |
| `@typescript-eslint/no-floating-promises` ↔ `no-misused-promises` | The first wants the promise handled, the second wants the handler not to *be* a promise. A `void`-returning handler that calls `.catch()` satisfies both |
| ruff `SIM105` ↔ `S110`, `S112` | The register flagged this one itself and restated the property as *explicit* suppression. `contextlib.suppress` — SIM105's own fix — is not a `try/except/pass`, so the other two do not fire on it |
| ruff `FBT001`, `FBT002` ↔ `PLR0917` | FBT's remedy is to make the boolean keyword-only, which *reduces* the positional count `PLR0917` limits. They pull the same way |
| ruff `E501` ↔ `ruff format` | Not a rule pair but the documented residue: the formatter cannot split a long string or comment, so `E501` can still fire on formatted code. It is a leftover finding rather than a fight, and `line-length` is one key serving both |

### The one thing that did fight, and what settled it

**`INP001` against pytest's own layout guidance.** `python.test-layout` cites
two instruments — ruff `INP001` and pytest's import-mode configuration — and on
the scaffold they disagreed: `INP001` fires on every test file in a directory
with no `__init__.py`, which is the layout pytest's good practices describe for
a `src` project.

This is worse than a pair contradiction if it holds, because it is a property's
two instruments contradicting each other. **It does not hold, and the way that
was settled was to try it rather than to argue it:**

```bash
touch cases/tests/__init__.py
ruff check --config ruff.toml cases/tests   # INP001 gone
python -m pytest cases/tests                 # 4 passed
```

Both instruments are satisfied by the same tree. `INP001` is a layout
requirement rather than a conflict, and what it costs is one empty file. **The
scaffold owes that file**, and its absence is one of the findings C2 has to
clear rather than a demotion C3 makes.

### What was already known and stays out

`python.return-count` is the register's one `incompatible` row — ruff `PLR0911`
counts exit points and an early return is the recommended fix for the nesting
`clean-code 102` warns about. It is **not selected**, so it is not a pair this
pass could find; it is recorded here so that "no contradicting pair among the
selected rules" is read as what it says.

## What this document still owes

Named so their absence is visible, in the order they will be written:

- ~~**The candidate configuration** — the default-on selection per stack, built
  from the resolved register.~~ Written 2026-09-07 — § The candidate
  configuration.
- **What ran** — ~~C1~~ done 2026-09-07; C2, C4 and C8 still owed, with
  versions and commands.
- ~~**What fought** — C3's pass: the method, the pairs cleared, and anything
  found.~~ Done 2026-09-07 — § What fought.
- **What was probed** — C5, one case per rule, with the outcome of each.
- **What each rule costs** — C7's table.
- **The four numbers** — C6, each with its rationale.
- ~~**What was read from an installed tree** — C9's two answers.~~ Both done
  2026-09-07: the `disable-conflict` configs under C1, the coverage comparison
  in its own section.
- **What was demoted, and the case that demoted it** — the criterion each
  demotion cites.
