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

Started **2026-09-07** and finished **2026-09-08**. § What has not run keeps
its name and its job: every criterion is answered there, including the ones that
were not applicable, so the document cannot be read as more finished — or less —
than it is. Nothing in it is open. The two rows that were not a bench's to
settle were handed to S4 and taken the same day; § The verdicts the bench handed
S4 records both, and one of them changed what a criterion's own command reads.

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

**These are the numbers of the run C1 records, and two later sections have
changed them.** C5's two demotions remove five selectors — 168 rules under `src`
and 167 under `tests`, with 27 added; § What the demotions changed. S4's `D103`
verdict then moved eight of those into `src/strict.toml`, taking `tests` to
**159** while `src` stays at 168; § The verdicts the bench handed S4. The
`tests` figure has moved twice and the `src` figure once, which is what a count
in a document does when the thing counted is still being decided.

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

**5,008 down to 125.** C5 has since demoted five of the additions, which removes
candidates and can create none, so this result holds over the smaller selection
without re-running — and the marker-comment group below now has the witness this
pass could not write. The disjoint column is the first bench's second removal,
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
| Python | 32, now **27** | **all of them** | 0 |
| React | 1 | **1** | 0 |

The Python row is a range because C5 demoted two rules after this ran and took
their cases with them. The command is the same and reports 27 of 27; § What the
demotions changed is why.

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

## What was probed — C5, and two rules are demoted

Run **2026-09-07**. C5 asks for a probe per rule with a known false-positive
reputation — **correct** code the rule is known to flag, written deliberately —
and for the case to be recorded whether the rule survives or not.

Six probes and four cases the earlier criteria already made. **Three probes
fired, two did not, one is a demonstration, and two rules are demoted.** The
probes are in [`scripts/craft_cases.py`](../../scripts/craft_cases.py), so every
result below can be re-derived rather than believed.

```bash
cd temp/craft-bench/python
ruff check --config strict.toml cases/probes/strict.py
ruff check --config cases/probes/runtime-evaluated.toml cases/probes/strict.py
cd ../react && npx eslint --config strict-probes.config.js probes/Effects.tsx
```

| Probe | Correct code it was given | Fired |
| --- | --- | --- |
| ruff `TC003` | A dataclass whose annotations `get_type_hints` resolves at runtime | **yes** |
| ruff `S104` | A container listening on every interface, which is the correct configuration there | **yes** |
| ruff `PLC0415` | A deferred import — the documented remedy for an optional or circular dependency | **yes** |
| ruff `EM101` | A one-line `NotImplementedError` stub | **yes** |
| ruff `RET504` | An **annotated** intermediate that names what the number is | **no** |
| ruff `D401` | A `@property` whose docstring is a noun phrase | **no** |
| `react-hooks/exhaustive-effect-dependencies` | An effect writing to a ref, which is not reactive and must not be listed | **no** |

**Each negative has a control beside it**, because the first bench established
that a silent rule is worth nothing until it is shown to be looking. The same
assignment without the annotation draws `RET504`; the same docstring on a method
rather than a property draws `D401`; an effect missing a real dependency draws
the React rule. All three controls fire.

### The two that did not fire already carry the escape hatch their reputation is about

`RET504` and `D401` are the rules this bench expected to argue with, and neither
needed the argument. Ruff skips an annotated assignment, which is exactly the
case people complain about — an intermediate that exists to name the value. And
ruff exempts a property, which is the convention PEP 257 documents for one.

That is a finding about reputations rather than about rules: two of the six
probes were written against a version of the rule that no longer exists.

### `TC003` fired, and the remedy breaks working code

The probe is a dataclass whose annotation something resolves at runtime.
`get_type_hints` evaluates the annotation string, so the import the rule wants
deferred is the import that call needs:

```console
$ python model.py     # the TC003 remedy applied
NameError: name 'Decimal' is not defined
```

**This is the first probe in either bench where complying makes the program
wrong**, rather than merely verbose. Everything the first bench probed cost a
suppression; this costs a `NameError` at import time in whatever resolves the
hints — a serialiser, a validator, a dependency injector.

**The rule is not demoted, because ruff has a setting for exactly this shape**
and the profile was missing it:

```toml
[lint.flake8-type-checking]
runtime-evaluated-decorators = ["dataclasses.dataclass"]
```

With that key the probe is clean and nothing else in the file changes — six
findings to five, and the one that goes is `TC003`. The key is now in
`strict.toml`, and `cases/probes/runtime-evaluated.toml` is the configuration
the comparison ran against.

**What is left unmeasured, and said so.** The same problem arrives through
`runtime-evaluated-base-classes` — pydantic, attrs, SQLAlchemy — and that list
is **not** set, because the scaffold declares no third-party dependency and a
list nothing here can run is a guess. S6 is where a repository with a real
dependency answers it.

**And this dissolves the question C2 left open.** The earlier record said
demoting `TC003` alone would split `python.typing-only-imports` along a line the
register does not draw. Nothing needs splitting: the family is kept whole and
configured. What survives of C2's objection is that `TC003`'s payoff is the
smallest of the three, which is a cost question and therefore C7's.

### The three that fired and are kept

| Rule | Verdict | Why |
| --- | --- | --- |
| `S104` | **Keep** | Nothing can tell a container's correct bind-all from a careless one by reading the literal. One suppression per site, and `RUF100` is selected, so a suppression that stops being needed is itself a finding — the first bench's reasoning for `S311`, arriving unchanged |
| `PLC0415` | **Keep, and it is the one to watch at S6** | The deferred import is documented practice for an optional dependency and the standard escape from a circular one, and the rule has no option that can tell those from carelessness. It is this level's widest blast radius with the weakest defence, which is what `ERA001` was at `standard` |
| `EM101` | **Keep** | It fired by design rather than in error: the probe measures what the remedy costs on a one-line stub, not a defect in the rule. With `TRY003` demoted below, `EM101` and `EM102` are the only instrument either exception-message property has |

### The first demotion — `TRY003`, which is satisfied without its property being

C2 measured that `TRY003` fires only where `EM101` or `EM102` already fires: on
a string literal or f-string of **more than one word**, a strict subset of *any
literal, any f-string*. No probe was needed and none is written; the table in
§ `TRY003` cannot be made to fire alone is the evidence.

What decides it is the remedy. `EM101` says *assign to variable first*, and
doing so silences `TRY003` — while the message sits in a local one line above
the `raise`, which is not what `python.exception-type-carries-its-message` asks
for and is not inside the exception class. **A rule that can be satisfied
without its property being satisfied is not an instrument for that property.**

`plan.md` § What this workstream will not do names this exactly: *ship a rule
that claims enforcement it does not have.* So `TRY003` is removed from
`strict.toml`, and `python.exception-type-carries-its-message` has no instrument
at this level and is judgment-only.

**The demotion costs no verdict.** Every defect `TRY003` reported is still
reported, by `EM101` or `EM102`, on the same line.

### The second demotion — `FIX001`–`FIX004`, which made seven codes unreachable

C3's marker-comment group had no clean witness: a comment with an upper-case
tag, an author, a colon, a space after it, a description and an issue link —
everything `TD001`–`TD007` ask for — still failed `FIX002`.

The register states `python.no-untracked-todo` as *a TODO names an owner or an
issue*. Ruff states `FIX002` as *checks for "TODO" comments … consider resolving
the issue before deploying the code*. The second is a different and much
stronger claim, and citing both codes for one property meant **no file
containing a TODO could pass**, so seven of the property's eleven codes could
never change a verdict.

The choice was between dropping the four so the property becomes what it says,
and dropping the seven and renaming the property to what it does. **The four are
dropped**, because the property's own text is the thing the register is
accountable for and no source in it proposes a ban on marker comments.

The demotion pays for itself immediately: `cases/src/wit/groups.py` now carries a
well-formed TODO, and the marker-comment group has the clean witness C3 could
not write.

### What the demotions changed, in the numbers the earlier sections report

Five selectors leave the level, so `strict` is **27 additions rather than 32**,
and it resolves to **168 rules** under `src` and **167** under `tests` against
the 173 and 172 C1 recorded. The `tests` figure moves once more when S4 takes
the `D103` verdict — to **159** — and § The verdicts the bench handed S4 is
that change; the additions stay 27 either way, because scoping a rule to a path
does not remove it from the level.

- **C1 and C2** are restated by that. `--fires` now reports 27 of 27 and 1 of 1,
  and the case files for the demoted rules are gone with them.
- **C3 is not, and does not need re-running.** Removing rules from a selection
  can only remove pairs, never create one, so *no contradicting pair among the
  5,008 the additions opened* holds over the smaller set a fortiori. Its
  arithmetic stands as the record of what was searched, which was more.

## What each rule costs — C7, and the metadata that answers it overstates

Read **2026-09-08** the way [`review.bench.md`](review.bench.md) § What each
rule costs reads it — from the tools' own metadata, which is why that section
says C7 needs no run. It is read here **and then checked against a run**. The
two disagree, and the run is the one to believe.

```bash
uv run python scripts/craft_cost.py --level strict --added        # the 27 and the 1
uv run python scripts/craft_cost.py --level strict                # the whole level
uv run python scripts/craft_cost.py --level strict --fix-applies  # the check
```

`--level` and `--added` are new. The additions are derived by resolving the
strict selection against the standard one, which is how `--fires` already
derives them, so the two modes cannot disagree about what the level added.

### What the metadata says

| | Rules | A fix or a suggestion | Neither — hand-work |
| --- | --- | --- | --- |
| Python, added at `strict` | 27 | 8 | **19 (70%)** |
| React, added at `strict` | 1 | 1 | **0** |
| Python, the whole level | 168 | 77 | **91 (54%)** |
| React, the whole level | 133 | 37 | **96 (72%)** |
| **Both, the whole level** | **301** | **114** | **187 (62%)** |

**The additions are the expensive end of the level.** 70% of the 27 carry no fix
against the level's own 54% and `standard`'s 51%, so a repository moving up does
not buy more of the same — it buys the part the tool cannot do for it. Where
that sits is not a surprise once it is listed:

| Family | Hand-work of the additions | What a finding asks of a person |
| --- | --- | --- |
| `pydocstyle` | 9 of 10 | **Write English.** `D100`–`D107` want a docstring that does not exist and `D401` wants it in the imperative mood. Only `D205`'s blank line is mechanical |
| `flake8-todos` | 6 of 7 | **Supply information.** `TD002` wants an author and `TD003` an issue link, neither of which is in the file. Only `TD006`'s `todo` → `TODO` is mechanical |
| `Pylint` | 3 of 3 | **Restructure.** `PLC0415`, `PLR0904` and `PLR1702` are the additions' three shape rules, and nothing can decide for you that a class has too many methods |
| `flake8-bandit` | 1 of 1 | **Decide.** `S104` is a binding address, which is a deployment question rather than a code one |
| `flake8-type-checking`, `flake8-errmsg`, `flake8-return` | 0 of 6 | Nothing. These six are the whole of the cheap half |

The first bench read `fix_availability` as two values, present or absent. It has
**three** — `always`, `sometimes` and `none` — and `craft_cost.py` now passes
all three through, because a fix that only sometimes applies is not a cost a
team can plan around. Nothing published moves: `none` is `none`, and the
command still prints `standard`'s 273 rules and 168 hand-work exactly. What the
third value adds is the shape of the fixable half. Of ruff's 812 stable rules,
202 are `sometimes` and 189 are `always` — near enough even. Of `strict`'s 168,
**58 are `sometimes` against 19 `always`**, and of the 27 additions, 6 against
2. So the selection is representative on the axis the first bench measured and
three-to-one skewed on the one it did not.

### The check: does `--fix` remove what the metadata claims?

C7 was defined as needing no run, and that is exactly why nobody had ever
checked it. `--fix-applies` lints the violation cases, applies `--fix`, lints
again, and restores the files. A rule whose finding survives its own fix
declared something it did not deliver **on that case** — which is the honest
scope of the claim, since a fix can be conditional and each rule has one case.

The flag is **shown able to fire** before its results are read: a file with a
stray `;;` under `no-extra-semi` is rewritten by the same invocation, so a file
that does not change is evidence rather than an unexercised flag.

At `strict`, of the 27 additions, 8 declare a fix. **One is applied.**

| | Rules | Applied by `--fix` | Only under `--unsafe-fixes` | Removed nothing |
| --- | --- | --- | --- | --- |
| Python additions declaring a fix | 8 | 1 | 6 | 1 |
| React rules that fired, declaring a fix or suggestion | 17 | 1 | 0 | 16 |

**Ruff's `fix_availability` is a property of the rule; applicability is a
property of the diagnostic**, and `ruff check --fix` applies only the safe ones.
`EM101`, `EM102`, `TC001`, `TC002` and `TC003` are all `sometimes` and all
unsafe here; `RET504` is `always` and is unsafe too, which is the sharpest case
— the taxonomy's strongest word and a default run that leaves the finding
standing. Only `TD006` fixes without being asked twice. `D205` fixes neither
way. The same pass at `standard` reports 14 declaring a fix, 4 applied, 7
unsafe-only and 3 removing nothing, so this is the level's shape rather than the
additions'.

An `--unsafe-fixes` fix is not free. It is a fix somebody has to read, which
puts those six between the two columns the metadata offers rather than in the
cheap one.

### The React half, where the metadata is not qualified at all

**Sixteen React rules fired, declared a fix or a suggestion, and removed
nothing.** Two of them declared only `hasSuggestions` and are honest — a
suggestion is by definition something an editor offers and `--fix` does not
apply. The other **fourteen declare `meta.fixable: 'code'`**, and `--fix` left
every finding in place. `@eslint-react/dom-no-unknown-property` is the one rule
in the stack that actually rewrote its case.

Nine of the fourteen are `react-hooks` rules, which makes this a **correction to
the first bench** rather than a new measurement about a new rule:

> `react-hooks` | **1 of 12** | The cheapest group in either stack. The
> compiler-backed rules ship fixes, which is what a rule written against a
> compiler can do

That row is wrong, and it is wrong in the direction the metadata pushes. The
group is the *most* declared-fixable in either stack and the least
actually-fixed: `exhaustive-deps`, `exhaustive-effect-dependencies`,
`immutability`, `no-deriving-state-in-effects`, `purity`, `refs`,
`set-state-in-effect`, `set-state-in-render` and `static-components` all declare
a fix and applied none. The rule this level adds is among them, and it is the
clearest of the nine: it prints `Inferred dependencies: [id]` in the diagnostic,
so it computed the answer, and then did not write it.

This is C1 and C2's finding a third time, from a third direction. A count could
not see a rule that was on and inert; a `--print-config` reading could not see
it either; and `meta.fixable` cannot see a fix that is never emitted. **Each
time, the metadata was the optimistic side and only a run disagreed.**

### What this means for the numbers above

The metadata table stands as what the tools declare, and `plan.md` § S5 still
needs it — the installer has to present a cost before anything is installed,
and it cannot run a bench to do that. But it is a **floor on cheapness rather
than an estimate of it**. Across both levels and both stacks, 30 rules fired
declaring a fix and **five** removed their own finding under a default run.

The honest sentence for an adopter is that at `strict` **at least** 187 of 301
rules are hand-work, the true figure is higher, and the gap is not distributed
evenly: it is concentrated in `react-hooks`, which is the group the first bench
called the cheapest.

## The mypy half, which nothing had run

Run **2026-09-08**, at **mypy 2.3.1**. This is the row ADR 0051's third
precondition is really about: `strict`'s one type-checker key is the whole of
Craft's type-checking contribution across both stacks, and until this section
existed `disallow_any_explicit` had never met a line of code.

The cases are `python/cases/mypy/` in
[`craft_cases.py`](../../scripts/craft_cases.py) — `margin.py`, `probes.py` and
`control.py` — and every command below names its configuration, for a reason
that turned out to matter:

```bash
cd temp/craft-bench/python
mypy --config-file mypy-strict.ini src tests                  # C2, clean
MYPYPATH=src mypy --config-file mypy-strict.ini cases/src/wit cases/tests
mypy --config-file mypy-strict.ini cases/mypy/margin.py       # C2, ten findings
mypy --config-file mypy-strict.ini cases/mypy/probes.py       # C5, clean
mypy --config-file mypy-strict.ini cases/mypy/control.py      # `strict` is live
printf '[mypy]\nstrict = True\n' > /tmp/strict-only.ini
mypy --config-file /tmp/strict-only.ini cases/mypy/margin.py  # the margin: none
```

### The hazard that came first — mypy reads a config from outside the bench

**mypy walks up the directory tree**, and from
`temp/craft-bench/python/` it finds `/workspaces/ee-standard/pyproject.toml`.
A run without `--config-file` measures **this repository's** `[tool.mypy]` and
not the profile's, three levels above a directory that is gitignored precisely
so the bench cannot touch the repository carrying it.

It was caught the way it deserved to be. A flag comparison run from the wrong
directory reported that nine of `--strict`'s thirteen flags were already on by
default at mypy 2.3.1 — a striking claim about the tool, and entirely an
artefact of `strict = true` being read from this repository. Repeated in a
directory with no configuration above it, bare mypy reports **nothing** on any
of the nine defects and `--strict` reports **all nine**. `--strict` is exactly
as live as the design's table assumed.

This is CLAUDE.md's *a host run once reported green about a uv version it was
not using*, reproduced inside the container by a different mechanism. The
scaffold's own `pyproject.toml` cannot prevent it, because the absence of a
`[tool.mypy]` section is what sends mypy looking further up. `control.py`
carries the warning where somebody running the bench will see it.

### C1 and C2 — it assembles, and the scaffold was clean first time

`mypy-strict.ini` resolves, `strict = True` and `disallow_any_explicit = True`
coexist, and the scaffold's four files pass. **Unlike both ruff runs, the
subject needed no correction** — the two scaffold defects the ruff passes found
were docstring prose, and there is no analogous class of defect for a type
checker to find in code that was written with annotations from the first line.

`control.py` is the guard on that clean result: a function with no annotations
at all, which the ini reports and a configuration missing `strict = True` would
not. A clean run over the scaffold means something only because that one fires.

**C3's witnesses were type-checked for the first time**, and they pass. C3 asks
for *otherwise-correct code*, and until now the only judge of "correct" was the
linter that the witness was written to satisfy. Four files, clean, with
`MYPYPATH=src` so the scaffold's package resolves.

### The margin — none, against ten

`margin.py` writes an explicit `Any` in every place one can be written. With
`strict = True` alone it reports **nothing**. With the key it reports **ten
findings over nine sites**.

| Where the `Any` is | The key | ruff `ANN401` |
| --- | --- | --- |
| A public argument annotation | yes | yes |
| A **private** argument annotation | yes | **yes** |
| A return annotation | yes | yes |
| A local variable annotation | yes | no |
| A PEP 695 `type` alias | yes | no |
| Inside a generic — `list[Any]` | yes | no |
| A `cast(Any, …)` | yes | no |
| `**kwargs` | yes | yes |
| A dataclass field | **yes, twice** | no |

**So Craft's one key is not redundant with TYP-001**, which is the question
`design.profiles.md` § The type checker answered from `--strict`'s flag list and
this answers from a run. Nine sites, none of them reachable by the conformance
the repository already owes.

### C4 — one defect, two diagnostics, twice over

**Within the key.** An `Any` on a dataclass field is reported at the field *and*
at the `class` line, because the dataclass plugin synthesises an `__init__`
carrying the same annotation. A plain class with the same attribute annotation
draws exactly one, which is what makes the plugin the cause rather than the
annotation. It is the C4 shape from a single tool with a single setting.

**Across the tools**, and this is the one that matters. `ANN401` catches four of
the ten and mypy catches all four, so **`ANN401`'s findings are a strict subset
of the key's**. At `strict` both instruments run, and every `ANN401` finding is
reported twice under two different property names.

It cannot be resolved by dropping `ANN401` at `strict`. S4's § Naming,
versioning, and what a re-run does settles that the levels are nested and **the
installer never writes a loosening**, because removing selectors is a loosening
of LNT-001, which is `narrowing-only`. So the duplicate is not an oversight in
the selection — **the profile model guarantees it** wherever a strict property
subsumes a standard one carried by a different tool, and no configuration in
either tool can see across the pair. It goes in the Craft register's
`alternatives:` field with its reason, which is the same verdict C4 reached for
React and for the same structural reason.

### The register says `ANN401` is exactly the public scope, and it is not

`python.no-any` asserts *`Any` does not appear in a **public** signature*, and
`assess.rules.md` records `ANN401` as "exactly this scope". The run says
otherwise: `_private_argument` draws `ANN401`. Ruff's `flake8-annotations`
settings do not offer a public/private axis, so the instrument over-reaches its
property by construction and no configuration closes the gap.

**S4 owes a choice**, and both options are ordinary: reword the property to what
its instrument does, or keep the wording and record the over-reach as the
divergence it is. It is exactly the case ADR 0053's `coextensive:` reason exists
to force somebody to state, found by running the instrument against the
property's own words.

### C5 — four probes, and the reputation is about an older Python

The complaint against banning explicit `Any` is that some shapes cannot be
written without it. Each probe is one of those shapes, written the way the
current type system says to write it, and **all four are clean**:

| Probe | What it would have needed `Any` for | What removes it |
| --- | --- | --- |
| A pass-through decorator | `Callable[..., Any]` and `*args: Any` | PEP 612's `ParamSpec` |
| Decoded JSON | `Any` from `json.loads` | a `TypedDict` for the row |
| A parameter that genuinely accepts anything | `value: Any` | `object` |
| `**kwargs` forwarded onward | `**kwargs: Any` | `**kwargs: object` |

**No demotion**, and this is C5's third instance of the same shape: two of the
six probes at `strict` fired against a version of the rule that no longer
exists, and all four here are written against a version of *Python* that no
longer needs the escape. A false-positive reputation is a claim with a date on
it.

### C7 — nothing to read, and hand-work by construction

C7's method is the tools' own metadata. mypy publishes none, and has no `--fix`
at all, so every finding this key reports is hand-work — by construction rather
than by measurement, which is what § What each rule costs already says of it.

## The verdicts the bench handed S4

Both taken **2026-09-08**, by S4 rather than by this document, and recorded here
because this is where the case for each was measured.

### `D103` on tests — `D100`–`D107` move to `src/strict.toml`

C2's clean run reported `D103` four times on `tests/test_entries.py`, and C5
declined it as *a selection question rather than a probe*. The selection is now
made: `python.docstring-presence` is selected in `src/strict.toml`, not at the
root.

**The mechanism is `S101`'s, deliberately.** `assess.rules.md`'s resolution for
`python.no-assert-for-enforcement` rejected `per-file-ignores` — the exemption —
and expressed the scope the only way ruff allows, as a nested configuration the
source tree resolves against and the test tree does not. The same shape carries
the same kind of statement here, so the profile has one way of saying *this
property is about the package's own source* rather than two.

**Why the property is scoped and not weakened.** A test function's name is its
documentation; requiring a docstring as well is the kind of rule a team turns
off, and `plan.md` says this workstream will not ship one. The property is
unchanged — it asserts what it always did, about the code it was always about.

**`python.docstring-form` stays at the root**, and the asymmetry is the point:
`D205` and `D401` say that a docstring which exists is well formed, which is as
true of a test's docstring as of anything else. The level requires none from a
test and reads the ones it is given. The bench's own test witnesses have
docstrings and pass either way.

What moved, measured rather than predicted:

| | Before | After |
| --- | --- | --- |
| Rules resolving under `src` | 168 | **168** |
| Rules resolving under `tests` | 167 | **159** |
| `D103` on the scaffold's tests | 4 | **0** |
| Everything else on the scaffold | `TC003` ×2 | **`TC003` ×2**, unchanged |

**And it moved a check that could have gone quiet.** `craft_cost.py --fires`
ran `ruff check --config strict.toml` over the strict cases. With eight rules
now selected a level down, that command would have reported them as never having
fired — a criterion failing because the criterion was reading the wrong file.
The mode reads `src/strict.toml` instead, which resolves the whole selection,
and it still reports 27 of 27 and 1 of 1.

### `python.no-any` — the wording stands, the over-reach is recorded

The mypy half found `ANN401` firing on a private argument where the property
says *public*, with no setting in `flake8-annotations` to scope it. Two answers
were available and the register takes the second.

**Rewording the property to match the instrument was rejected.** It would make
the register a description of what ruff currently does rather than a statement
of what Equal Experts asks of code, and the next time the tool changed the
property would change with it — which is the direction of dependency this whole
workstream exists to keep pointing the other way. The property keeps its words;
`assess.rules.md` § Corrected by measurement carries the correction, and the
Craft register carries the reason in the `coextensive:` field ADR 0053 requires.

The cost of that answer is honest and small: at `strict` a private argument
annotated `Any` is reported, and the register says so rather than pretending the
instrument is exact.

## What has not run

Named so that this document cannot be read as more finished than it is. Every
row is now answered; two of them answer *this is somebody else's decision*.

| Criterion | State |
| --- | --- |
| C1 | **Done**, both stacks |
| C2 | **Done**, both directions and both stacks. The clean run produced four findings and the violation run demonstrated all 33 additions, by a command rather than a reading |
| C3 | **Done**, all three passes. 5,008 new pairs to 125 candidates, six witnesses clean at both levels, no contradicting pair — and the marker-comment group's missing witness, which is a shadowing rather than a fight |
| C4 | **Done**, and it was recorded as not applicable until the React rule started reporting. One duplicated defect per stack |
| C5 | **Done.** Six probes, three fired, two did not with a control each, and two rules demoted with the case that demoted them. `D103` on tests is the one verdict it did **not** take: § What has not run's last row but one |
| `D103` on tests | **Taken by S4, 2026-09-08.** `D100`–`D107` are selected in `src/strict.toml`, the mechanism `S101` already uses. 159 rules resolve under `tests` against 168 under `src`, and `--fires` moved with it — see § The verdicts the bench handed S4 |
| C7 | **Done**, and it went further than the criterion asks. The metadata is read for the 27 and for the level, and then **checked against a run** — 30 rules across both levels declare a fix and five apply one. The declared number is a floor on cheapness, not an estimate of it |
| C6, C8, C9 | **Not applicable, and stated rather than skipped.** C6's four numbers are `standard`'s and unchanged; C8 is answered above; C9 was S2's deferral and is closed |
| The mypy half | **Done**, at mypy 2.3.1, and it is the row ADR 0051's precondition is really about. The margin is **none against ten**: `strict` alone reports nothing where the key reports ten findings over nine sites, so Craft's one key is not redundant with TYP-001. C4 fires twice more — a dataclass field reports at the field and at the class, and `ANN401`'s findings are a strict subset of the key's, which the profile model guarantees rather than overlooks. C5's four probes are clean |
| `ANN401`'s scope | **Taken by S4, 2026-09-08: the wording stands and the over-reach is recorded.** Rewording a property to match its instrument would make the register a description of ruff. `assess.rules.md` § Corrected by measurement is the record |

**ADR 0051's third precondition is met.** Every rule `strict` adds has been
measured: 27 ruff codes and one React rule against C1 to C5 and C7, and the one
mypy key against the same criteria. That does not make any of them a control —
the precondition is one of three — but it is the one that was blocking, and no
strict-only property is barred by it any longer.

The two rows that were selections rather than measurements were taken by S4 on
2026-09-08 and are recorded in § The verdicts the bench handed S4. Neither was a
question a bench could answer, which is why each stayed open rather than being
taken quietly — and one of them moved a criterion's own command, which is the
part that would not have been noticed by reading.

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
