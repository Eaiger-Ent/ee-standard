# Craft — the second bench

The `strict` level, put through the criteria the first bench wrote.

**Why there is a second one.** `review.bench.md` measured `standard` — every
number in it describes that level and no other — and S4 then defined a level
above it. [ADR
0051](../adr/0051-a-craft-rule-becomes-a-control-by-being-installed.md)'s third
precondition is that S3 has measured a property before it may ever become a
control, so **no strict-only rule is eligible for anything until this document
exists**. `design.profiles.md` § The strictness levels records that as the second
of its three uncomfortable findings.

**The criteria are not restated here.** C1 to C9 are `review.bench.md`
§ The acceptance criteria, written on 2026-09-06 before a scaffold existed, and
a second bench that redefined them would be marking its own homework against a
fresh mark. This document cites them by number and reports what happened.

Started **2026-09-07**. It is not finished, and § What has not run says what is
missing rather than leaving a reader to infer it.

## The configuration extends rather than restates

Written by [`scripts/craft_profile.py --level strict`](../../scripts/craft_profile.py),
into the same gitignored `temp/craft-bench/` the first bench used.

| | Writes | Which is |
| --- | --- | --- |
| Python | `python/strict.toml` | `extend = "ruff.toml"` plus 32 selectors |
| | `python/src/strict.toml` | `extend = "../strict.toml"` plus `S101`, the same scoping `standard` needs |
| | `python/mypy-strict.ini` | `strict = True` and `disallow_any_explicit = True` |
| React | `react/strict.config.js` | the standard flat config spread, plus one rule — and, after C2, the option without which that rule cannot report |

**Every file extends its `standard` counterpart.** S4 defines `strict` as a
superset, and a second full selector list would be a second copy free to
disagree with the definition — the failure this repository exists to prevent,
arriving inside the bench that is supposed to catch it.

**`mypy-strict.ini` is a bench file and not the surface an installed profile
writes.** `design.profiles.md` § The config surface says the profile writes
`pyproject.toml` §`tool.mypy`; the bench keeps its instrument out of the
subject's file for the same reason it writes `ruff.toml` rather than
`[tool.ruff]`, and because the scaffold's `pyproject.toml` belongs to
`craft_scaffold.py`.

## C1 — it assembles, and the numbers are the design's

```bash
cd temp/craft-bench/python
ruff check --config strict.toml     --show-settings tests/test_entries.py
ruff check --config src/strict.toml --show-settings src/ledger/entries.py
```

| What C1 asks | What resolved |
| --- | --- |
| The selected set resolves | **172 rules** under `tests/`, **173** under `src/` — `standard`'s 140 and 141 plus 32 |
| No selector matches nothing | None. Ruff rejects an unknown selector outright |
| The level is a superset | **Nothing is removed.** Diffing the two enabled sets: 32 added, 0 dropped |

**32 is the design's own number**, and it is the narrow reading of
`python.docstring-form` rather than the wide one — `D205` and `D401` as exact
codes, where `D2xx` and `D4xx` would have brought 68. That the configuration
resolves to exactly what § What `strict` adds predicted is the first thing this
bench had to establish and the least interesting.

**Preview enabled the two rules it was asked for and nothing else.**
`preview = true` is on, because `PLR1702` and `PLR0904` cannot be reached
without it. Reading the resolved set against the pinned taxonomy, the preview
rules enabled are `PLR0904` and `PLR1702` — exactly two, and the two named.
C8 measured that on a selection spelled in exact codes and predicted it; this is
the same finding at the level where it actually costs something.

**React adds one rule, and the resolved count says so.** 121 rules on a
component against `standard`'s 120, and `npx eslint --config strict.config.js src`
exits `0`. The asymmetry `design.profiles.md` refused to explain away is visible
here as a single line of configuration.

That count was true and told nobody anything: the rule it counts reported
nothing on any code until C2 wrote a case for it. § React's one added rule was
inert. The number is unchanged by the correction, which is the point of the
finding rather than an aside to it.

## C3 — no contradicting pair, and one family that shadows another

Three passes, and the result is **no contradicting pair among the 5,008 the
additions open**, one candidate that measurement cleared, and one group with no
clean witness whose absence is a finding rather than a failure.

C3's first pass is ruff's own formatter-conflict check, and the first bench
established the discipline that comes with it: **a negative result is worth
nothing unless the check is shown able to fire.**

```console
$ ruff format --check --config strict.toml src tests
4 files already formatted
```

Silent. And the same check, over the wide reading of `python.docstring-form`
that S4's schema slice rejected:

```console
$ ruff format --check --config wide.toml src
warning: `incorrect-blank-line-before-class` (D203) and `no-blank-line-before-class`
  (D211) are incompatible. Ignoring `incorrect-blank-line-before-class`.
warning: `multi-line-summary-first-line` (D212) and `multi-line-summary-second-line`
  (D213) are incompatible. Ignoring `multi-line-summary-second-line`.
```

**Both pairs, both warnings, and ruff resolving each by dropping one side.** The
schema slice argued from the taxonomy that an instrument must be a closed set of
codes or a coextensive linter and never a range; this is that argument run
rather than reasoned. The rule it produced is the reason the strict level has no
contradiction to report.

### Pass 2 — the additions re-open a group, so what is counted is new pairs

The first bench cleared 9,870 pairs over `standard`'s 141 rules. `strict` is 173,
which is 14,878 pairs, so **5,008 of them are new**: 4,512 where an addition
meets a rule `standard` already selected, and 496 among the additions
themselves. A rule added to a group re-opens every pair in that group, and the
pairs a level does not touch stay cleared.

The construct partition is the first bench's, re-derived for the additions.
**The standard members of each group are named** so the assignment can be
checked rather than taken; the method itself, and the limit it carries, are
`review.bench.md` § The method and are not restated.

| Construct | `standard` | added | pairs | already cleared | disjoint | candidates |
| --- | --- | --- | --- | --- | --- | --- |
| marker comment | `ERA001` | 11 | 66 | 0 | 6 | **60** |
| exception handler | 6 | 3 | 36 | 15 | 1 | **20** |
| docstring | none | 10 | 45 | 0 | 28 | **17** |
| import | 3 | 4 | 21 | 3 | 3 | **15** |
| security literal | 7 | 1 | 28 | 21 | 0 | **7** |
| binding | 4 | 1 | 10 | 6 | 0 | **4** |
| body size | 2 | 1 | 3 | 1 | 0 | **2** |
| class body | none | `PLR0904` | 0 | 0 | 0 | **0** |
| | | **32** | | | | **125** |

**5,008 down to 125.** The disjoint column is the first bench's second removal,
applied to the families the additions bring: `TC001`/`TC002`/`TC003` split an
import three ways by origin, `FIX001`–`FIX004` split a line four ways by tag,
`EM101` and `EM102` split a raise argument into a literal and an f-string, and
`D100`–`D107` split eight *different definitions* between them. No two rules in
any of those can apply to one node.

**`D100`–`D107` against `D205` and `D401` is not disjoint, and the reason is
worth a sentence.** It is tempting to read them as absence-versus-content and
call them exclusive. They are not: a documented public function is one node
where `D103` has looked and passed *and* `D205` and `D401` are reading the
docstring `D103` required. Sixteen of the docstring group's seventeen candidate
pairs are that shape.

### Pass 3 — a witness per group that gained a rule

Seven groups gained a rule and six of them have a witness. The witnesses are the
first bench's, extended rather than duplicated: `cases/src/wit/groups.py`
carries the strict members of each group alongside the standard ones, so there
is one witness set that has to be clean at **both** levels.

```bash
ruff check --config src/ruff.toml   cases/src   # standard
ruff check --config src/strict.toml cases/src   # strict
ruff check --config ruff.toml       cases/tests
ruff check --config strict.toml     cases/tests
npx eslint src && npx eslint --config strict.config.js src && npx tsc --noEmit
```

All six exit `0`, at both levels, and the test witness's four tests still pass.
Two of the extensions are worth naming.

**The React witness had no effect in it at all.** `exhaustive-effect-dependencies`
joins the hook group, and until this pass the group's witness used `useMemo` and
`useCallback` and never called `useEffect` — so the added rule had nothing to
apply to and cleared nothing. The witness now carries an effect that subscribes
and returns its own teardown, with every reactive value listed and no others.
**Shown to have applied**: drop `selected` from the array and the added rule
reports *Found missing effect dependencies* alongside `exhaustive-deps`; put it
back and both are silent.

**The test witness needed docstrings and the scaffold did not get them.** `D103`
reaches a test function, which is C2's standing finding. A *case* exists to
satisfy the instrument, so the witness is written to pass; the *scaffold* is
what is being measured, so it is left alone and its four findings stand. That
line — case yes, subject no — is the same one the `D401` and `D205` corrections
were argued on from the other side.

### The pairs worth naming, and why each is clear

| Pair | Why it is not a contradiction |
| --- | --- |
| `TC001`, `TC003` ↔ `PLC0415` | **The sharpest one the additions brought.** `TC`'s remedy is to move the import into an `if TYPE_CHECKING:` block, and `PLC0415` forbids an import that is not at the top level of the file. Run rather than argued: the block is a module-level `if`, `PLC0415` does not reach inside it, and the import witness carries both satisfied |
| `D100`–`D107` ↔ `D205`, `D401` | Sixteen pairs on one shape — a definition that carries a docstring of the form the other two ask for. The witness documents a module, a package, a class, a nested class, a method, a magic method, an `__init__` and a function, each with an imperative summary and a blank line after it |
| `EM101`, `EM102`, `TRY003` ↔ `B904` | The message bound to a name before the `raise`, chained with `from`. One line satisfies four rules, and it is the line the standard witness already carried — the additions joined a group that was already answering them |
| `RET504` ↔ `F841` | They look opposed: one wants the binding gone, the other wants it used. Both are satisfied by a binding used somewhere other than the line below it, which is what a loop accumulator is |
| `PLR1702` ↔ `C901`, `PLR0915` | Nesting, complexity and statement count pull the same way — flattening reduces all three. The witness nests to four against a cap of five, so the rule has looked rather than found nothing |
| `S104` ↔ `S105`–`S107` | Both read a string constant. A loopback literal satisfies `S104` and is not a credential, so one constant clears the seven pairs at once |
| `react-hooks/exhaustive-effect-dependencies` ↔ `exhaustive-deps` | One dependency array satisfies both, in both directions. This is also C4's React duplicate, and the two criteria disagree about it in the ordinary way: cleared here, counted there |

### The marker-comment group has no witness, and that is the finding

Sixty of the 125 candidate pairs are in one group, and the group has no clean
witness. Not because one was hard to write — because none exists.

```console
$ cat b.py
# TODO(nc): reconcile the register (https://github.com/Eaiger-Ent/ee-standard/issues/1)
$ ruff check --config strict.toml b.py
b.py:1:3: line-contains-todo: Line contains TODO, consider resolving the issue
```

That comment has an upper-case tag, an author, a colon, a space after it, a
description and an issue link. It is everything `TD001`–`TD007` ask for, and
`FIX002` fails it anyway. **No file containing a TODO can satisfy the group**,
and the only files that do satisfy it are files where `TD001`–`TD007` have
nothing to look at.

**C3 does not fail on this**, and the reason is the first bench's own. A pair
contradicts if satisfying one *necessarily* violates the other; a file with no
marker comment satisfies all twelve rules, and that file is what both halves are
asking for — the same clearing the first bench gave
`no-static-element-interactions` against `prefer-tag-over-role`, where neither
horn is satisfiable and the correct code is a third thing.

What the pass found instead is a property whose instrument asserts something
else. `assess.rules.md` states `python.no-untracked-todo` as *a TODO names an
owner or an issue*. Ruff states `FIX002` as *checks for "TODO" comments …
consider resolving the issue before deploying the code*. Those are different
claims, and the register cites both codes for the one property, so:

- **`TD001`–`TD007` can never fire on a file that passes.** Seven of the
  property's eleven codes cannot change a verdict.
- **The property as installed forbids marker comments**, which is not what its
  own text says and is a much stronger rule than the sources support.

This is the third instrument this bench has found not measuring its property —
after `TRY003` inside `EM101`, and `D103` reaching test functions the property
did not have in view. It differs from those two in being a *whole family*
shadowed rather than a rule, and in needing no probe: the console block above is
the evidence. **The verdict is C5's**, and it is a choice between dropping
`FIX001`–`FIX004`, so the property becomes what it says, and dropping
`TD001`–`TD007` and renaming the property to what it does.

## C2 — both directions, and neither was quiet

C2 asks for a verdict in **both** directions: clean over the scaffold, and
non-zero on deliberate defects with the rule that caught each one named. At
`strict` the second half is per **rule** rather than per family. The first bench
demonstrated 26 selected families from 37 rules, which is the honest form of the
question when a selection is 141 rules wide; this level is defined as
thirty-two named additions, and a family is too coarse to show each of them
working.

### The clean direction, and what running `tests/` as well found

```bash
ruff check --config src/strict.toml src
ruff check --config strict.toml     tests
```

**The `tests/` half had not been run when this section was first written**, and
it carries three of the five findings. Nothing in the earlier record claimed it
was clean; nothing said it was missing either, which is the omission this run
closes.

| Where | Rule | Verdict |
| --- | --- | --- |
| `src/ledger/entries.py` | `D401` | the scaffold's defect, corrected |
| `tests/__init__.py` | `D205` | the scaffold's defect, corrected |
| both files | `TC003` ×2 | stands |
| `tests/test_entries.py` | `D103` ×4 | stands, and it collides with a decision |

### `D401`, where the rule was right and the scaffold was wrong

```text
non-imperative-mood: First line of docstring should be in imperative mood:
  "The entries recorded on the current UTC day."
```

PEP 257 — which `assess.rules.md` cites for this property — says a docstring
*prescribes the function's effect as a command*. The scaffold's did not, and no
rule in `standard` reads docstring prose, so nothing had ever looked. **The
scaffold is corrected**: `Return the entries recorded…`, in
`craft_scaffold.py` so it rebuilds that way.

Changing the subject to satisfy the instrument needs justifying, and here it is:
`D401` is not in `standard`, so `standard`'s recorded runs are untouched —
re-verified, `ruff check --config src/ruff.toml src` still exits `0` and the
four tests still pass. **The finding is about the scaffold, and it is the kind
only a stricter level can produce**: a defect that existed all along in a file
written to be exemplary.

### `D205` on `tests/__init__.py`, which is the same finding a second time

```text
missing-blank-line-after-summary: 1 blank line required between summary line
  and description
```

That docstring was written during the *first* bench, to explain why the file
exists at all — `tests/__init__.py` is `INP001`'s remedy, and C3 measured it.
It has been wrong since the day it was written, in a file the first bench added
deliberately and read carefully. Corrected in `craft_scaffold.py`, on the same
justification as `D401` and with the same re-verification: `standard` still
exits `0` over `src` and `tests`, `ruff format --check` still reports four files
already formatted, and the four tests still pass.

### `TC003`, which stands, and is the one to argue about

```text
typing-only-standard-library-import: Move standard library import `pathlib.Path`
  into a type-checking block
```

**Ruff is correct.** `Path` appears once, as the annotation on
`read_entries(path: Path)`, and the module carries
`from __future__ import annotations`, so the annotation is a string at runtime
and `pathlib` is genuinely not needed then. The `tests/` run finds the second
instance, in `test_entries.py`, for the same reason.

What complying costs is the question. It is an `if TYPE_CHECKING:` block and an
import of `typing` — three lines of indirection — to avoid importing a standard
library module that is already loaded in essentially any Python process. The
benefit of deferring an import scales with what the import costs, and **`TC003`
is precisely the member of its trio where that cost is smallest**: `TC001` is
first-party, `TC002` third-party, `TC003` the standard library.

This is a demotion candidate and it is not demoted here, for a reason worth
recording rather than resolving quietly. The property is
`python.typing-only-imports` and it cites all three codes; dropping one member
would split a property along a line the register does not draw, which is the
schema slice's *one instrument per property* question arriving in a new shape.
C5 is where it gets a probe and a verdict.

### `D103` on every test, and the ordinary remedy is one the design refused

Four findings, one per test function, all of the same shape:

```text
undocumented-public-function: Missing docstring in public function
  --> tests/test_entries.py:23:5
   |
23 | def test_total_sums_without_losing_precision() -> None:
```

`python.docstring-presence` is `D100`–`D107` and `strict` selects all eight, so
it reaches test functions like any other. The remedy every Python project
reaches for is `per-file-ignores` dropping `D1xx` under `tests/` — and that is
the one remedy this profile cannot take. `design.profiles.md` § The config
surface calls `per-file-ignores` *the exemption the register's resolution
rejected*, because `python.test-code-quality` asserts the lint profile applies
to test code too; the whole reason `S101` needs a nested `src/ruff.toml` is that
ruff has no per-path `select` and the exemption was off the table.

So `strict` puts two of its own decisions against each other, and neither is
obviously the one to give up:

- Write four docstrings that restate four test names. The names are already
  sentences — `test_read_entries_returns_the_newest_first` — so the docstring
  adds a line and no information, which is the cost `D103` is charging.
- Demote `python.docstring-presence` at `strict`, or scope it. Scoping it to
  `src/` needs the second configuration file `S101` already needs, so the
  mechanism exists; what it costs is the property, which says *public* and not
  *public outside tests*.

**Neither is taken here.** It is the second demotion candidate this level has
produced, both of them out of the `tests/` run, and C5 is where both get a probe
and a verdict.

## C2's other half — 32 cases, and a command that compares them

`cases/strict/` is one deliberate defect per added rule, split by what a defect
has to *be* rather than by property: a package `__init__.py` and a module with
no docstrings anywhere, a module whose docstrings are the wrong shape, a module
of malformed marker comments, and a module for everything else.

**The two preview rules keep the cases C8 already wrote for them.**
`cases/preview/control.py` is a six-deep function and a twenty-five-method
class, written for the preview measurement and already exactly the defects
`PLR1702` and `PLR0904` need. A second pair would be a copy free to drift from
the one the preview measurement reads.

```bash
ruff check --config strict.toml cases/strict cases/preview/control.py
uv run python scripts/craft_cost.py --fires
```

| | Added | Fired on a case | Silent |
| --- | --- | --- | --- |
| Python | 32 | **32** | 0 |
| React | 1 | **1** | 0 |

The check is mechanical rather than visual, and the mechanism is the point: the
additions are derived by resolving the strict selection against the standard one
— the same superset statement `strict.toml` makes, read back — the findings are
parsed from the run, and the two sets are compared. A rule that stops firing
shows up as a missing rule rather than as a run that still looks busy.

**And it is shown able to fire.** With the React correction below reverted,
`--fires` reports `React: 0 of 1` and exits `1`. A negative result from a check
nobody has watched fail is worth nothing, which is the discipline the first
bench established for C3 and which applies here for the same reason.

The 49 Python findings are **exactly** the 32 additions, with no rule from
`standard` among them. That is not a requirement of C2 and it is worth one
sentence: it means each case is answering the question it was written for rather
than incidentally tripping something else.

### `TRY003` cannot be made to fire alone, and its remedy is not its property

Two rules on one line is ordinary; the first bench's cases carry several. This
pair is different, and the difference is not the double report.

| Raised as | `EM101`/`EM102` | `TRY003` |
| --- | --- | --- |
| `ValueError("closed")` | fires | silent |
| `ValueError("the ledger is closed")` | fires | fires |
| `ValueError(f"closed on {day}")` | fires | fires |
| `ValueError(", ".join(parts))` | silent | silent |
| `ValueError("the ledger " + "is closed")` | silent | silent |
| `ValueError("closed on %s" % day)` | silent | silent |
| `message = "…"` then `ValueError(message)` | silent | silent |

**`TRY003`'s trigger is a string literal or f-string of more than one word** — a
strict subset of `EM101`/`EM102`'s *any literal, any f-string*. It is not a
length threshold: a twenty-character single word is silent and `a b` is not.

The consequence is about the remedy, not the count. `EM101` says *assign to
variable first*, and doing that silences `TRY003` too — while leaving the
message exactly where `python.exception-type-carries-its-message` says it should
not be, which is outside the exception class. A local variable one line above
the `raise` is not the exception class. **So the rule as installed enforces the
shape `EM101` already enforces, and not the property it was cited for.**

That is a demotion candidate of a different kind from `TC003` and `D103`: those
two cost more than they are worth, and this one does not measure what it claims.
It is the third case C5 inherits, and unlike the other two it does not need a
probe — the table above is the evidence. What it needs is a verdict on whether a
property with no instrument that reaches it keeps a citation to one that does
not.

### React's one added rule was inert, and `--print-config` said it was on

`'react-hooks/exhaustive-effect-dependencies': 'error'` is what § The
configuration extends rather than restates recorded and what C1 counted as
React's 121st rule. **It reported nothing, on any code.** Four effects written
against it — a missing dependency, an extra one, a whole object where a field is
read, no dependency array at all — and the rule was silent on all four while
`exhaustive-deps` caught the first from `standard`.

```console
$ npx eslint --print-config violations/Effects.tsx | jq '.rules["react-hooks/exhaustive-effect-dependencies"]'
[2]
```

Severity 2, enabled, reporting nothing. The rule is a view onto the React
Compiler's own analysis rather than a lint pass of its own, and that analysis is
gated separately: in `eslint-plugin-react-hooks` 7.1.1 the compiler
environment's `validateExhaustiveEffectDependencies` is `'off'` by default, and
a rule's severity does not reach it. The plugin merges a rule's `environment`
option over that default, so the switch is reachable — from the rule's
**options**, never from its severity:

```js
'react-hooks/exhaustive-effect-dependencies': [
  'error',
  { environment: { validateExhaustiveEffectDependencies: 'all' } },
],
```

**The profile is corrected** in `craft_profile.py`, and with the option the rule
reports both directions. Two things about this are worth keeping.

- It is C2's third clause landing on the only rule this level adds to React. The
  criterion says a rule that resolves and then never runs *is indistinguishable
  from a rule that is working, and it is the failure this workstream would be
  least able to see*. It was indistinguishable for a day: C1 counted it, the
  resolved configuration reported it at severity 2, and the whole of React's
  strict level did nothing.
- **A count cannot see this.** C1's evidence was 121 rules against `standard`'s
  120, and that number is the same before the correction and after it. The only
  instrument that separates an enabled rule from a working one is a case written
  for it, which is what C2 is.

## C4 — applicable after all, and the answer is once per stack

§ What has not run recorded C4 as not applicable at `strict`, on the grounds
that the level adds one React rule and that rule sits in neither plugin overlap.
That was true of the overlap C4 was written about — two plugins shipping one
rule name — and wrong about the criterion, which asks whether one defect ever
draws two diagnostics. It does, once in each stack, and both were invisible
until the added rules started reporting.

**React.** An effect that reads `id` with an empty dependency array:

```text
 9:17  react-hooks/exhaustive-effect-dependencies  Found missing effect dependencies
11:6   react-hooks/exhaustive-deps                 React Hook useEffect has a missing
                                                   dependency: 'id'
```

An effect listing a dependency it does not read draws one, from the added rule
alone — `exhaustive-deps` has no opinion about extra dependencies. So the added
rule's whole margin over `standard` is the **extra**-dependency direction, and
its cost is a second diagnostic on every missing-dependency defect.

The plugin takes `'missing-only'`, `'extra-only'` or `'all'`, so `'extra-only'`
would remove the duplicate and keep the margin. **It is not taken.**
`react.effect-dependencies-exhaustive` is exhaustiveness in both directions, and
narrowing the instrument to dodge a duplicate would leave the register asserting
a property its configuration no longer enforces — which is the mistake S4's
schema slice made unspellable for ranges and which would arrive here by hand.
The alternative and the reason belong in the Craft register's `alternatives:`
field, which is the mechanism that slice built for exactly this.

**Python.** `TRY003` against `EM101`/`EM102`, above. Same shape, worse
consequence: the React pair reports one defect twice and both diagnostics are
true, while the Python pair reports one defect twice and one of the two goes
quiet on a remedy that does not satisfy it.

## What has not run

Named so that this document cannot be read as more finished than it is.

| Criterion | State |
| --- | --- |
| C1 | **Done**, both stacks |
| C2 | **Done**, both directions and both stacks. The clean run produced four findings and the violation run demonstrated all 33 additions, by a command rather than a reading |
| C3 | **Done**, all three passes. 5,008 new pairs to 125 candidates, six witnesses clean at both levels, no contradicting pair — and the marker-comment group's missing witness, which is a shadowing rather than a fight |
| C4 | **Done**, and it was recorded as not applicable until the React rule started reporting. One duplicated defect per stack |
| C5 | **Not started, and it now inherits four cases with the argument already made** — `TC003`, `D103` on tests, `TRY003`, and `TD001`–`TD007` under `FIX002`. `D401` and `EM101` still want a probe of their own |
| C7 | **Not started.** Cost per finding for the 32, from `fix_availability` |
| C6, C8, C9 | **Not applicable, and stated rather than skipped.** C6's four numbers are `standard`'s and unchanged; C8 is answered above; C9 was S2's deferral and is closed |
| The mypy half | **Nothing has run it.** `mypy-strict.ini` is written and `disallow_any_explicit` has not met a line of code |

The last row is the one that matters most, because it is the row ADR 0051's
precondition is really about: the strict level's one type-checker key is still
exactly as unmeasured as C6 left it.

**And C2 changed what the earlier rows are worth.** C1 counted React's added
rule and C3's first pass found nothing to report about it, both correctly, while
the rule could not have reported anything at all. Neither criterion was wrong; a
count and a conflict check cannot see an inert rule, and only a case written for
the rule can. Where a row above says a number, read it as a number.

C3's third pass found the same shape once more, from the other end: the React
witness cleared the hook group without ever calling `useEffect`, so the rule
that group gained had nothing to apply to. A clean witness is worth what the
rules it exercises are worth, which is why the pass now shows the rule firing
when the witness is broken.
