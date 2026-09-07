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
| React | `react/strict.config.js` | the standard flat config spread, plus one rule |

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

## C3 — the contradiction the design predicted is absent, and shown to be

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

The rest of C3 — the construct partition and a witness per group, over the 32
new rules — has not run. § What has not run.

## C2 — the scaffold was not clean, and one of the two findings was its fault

```bash
ruff check --config src/strict.toml src
```

**Two findings on the first run, on a scaffold `standard` passes clean.**

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

### `TC003`, which stands, and is the one to argue about

```text
typing-only-standard-library-import: Move standard library import `pathlib.Path`
  into a type-checking block
```

**Ruff is correct.** `Path` appears once, as the annotation on
`read_entries(path: Path)`, and the module carries
`from __future__ import annotations`, so the annotation is a string at runtime
and `pathlib` is genuinely not needed then.

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

## What has not run

Named so that this document cannot be read as more finished than it is.

| Criterion | State |
| --- | --- |
| C1 | **Done**, both stacks |
| C2 | **Half.** The clean direction has run and produced the two findings above. The violation file — one deliberate defect per new rule — has not been written |
| C3 | **Pass 1 only.** The formatter check is clean and shown able to fire; the construct partition and witnesses over the 32 new rules have not run |
| C5 | **Not started.** `TC003` has a case already and needs a probe; `D401`, `TRY003` and `EM101` all have false-positive reputations worth writing a case for |
| C7 | **Not started.** Cost per finding for the 32, from `fix_availability` |
| C4, C6, C8, C9 | **Not applicable, and stated rather than skipped.** C4's double-report question is about two React plugins and `strict` adds one rule to neither overlap; C6's four numbers are `standard`'s and unchanged; C8 is answered above; C9 was S2's deferral and is closed |
| The mypy half | **Nothing has run it.** `mypy-strict.ini` is written and `disallow_any_explicit` has not met a line of code |

The last row is the one that matters most, because it is the row ADR 0051's
precondition is really about: the strict level's one type-checker key is still
exactly as unmeasured as C6 left it.
