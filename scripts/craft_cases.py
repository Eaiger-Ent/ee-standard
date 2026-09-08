#!/usr/bin/env -S uv run python
"""Materialise the cases a Craft bench criterion is decided on — S3.

The scaffold (`craft_scaffold.py`) is the subject and the configuration
(`craft_profile.py`) is the instrument. This is neither: it is the code written
to *decide a criterion*, and it is a third file because a case has a different
lifetime from both. A case exists to answer one question, it is named after the
criterion that asked, and it stays afterwards so the answer can be re-derived.

**C3's witnesses.** C3 asks whether any two selected rules
contradict — whether satisfying one necessarily violates the other on otherwise
correct code. A single piece of code where both rules *apply* and both are
*satisfied* refutes the "necessarily" for that pair, so a construct group whose
rules are jointly satisfied by one witness contains no contradicting pair. The
witnesses below are those, one section per group, and
`docs/craft/review.bench.md` § What fought records the partition that says which
groups there are.

**C2's deliberate violations.** C2 asks for a verdict in both directions: clean
over the scaffold, and non-zero on defects with the rule that caught each one
named. One defect per selected ruff family, and one for every React rule the
profile enables or escalates against its own plugin's default. They live outside
`src/` for the same reason the probes do - a directory of defects inside the
clean run would make that run impossible by construction - and
`react/violations.config.js` is the profile *pointed at another directory*
rather than a second copy of it.

At `strict` the same criterion is per *rule* rather than per family, because the
level is defined as thirty-two named additions and a family is too coarse to
show each one working. `python/cases/strict/` is those, split by what a defect
has to be — a file with no docstrings, a file with malformed ones, a file of
marker comments, and a file of everything else — and the two preview rules keep
the cases C8 already wrote for them rather than getting a second pair.
`react/violations/Effects.tsx` is the React half, one case per direction the one
added rule reports.

**C4's shared names.** C4 asks whether one defect ever draws two diagnostics.
`react/violations/Shared.tsx` is one deliberate defect per rule name both
plugins ship, and the count per defect is the answer. It found the pair that a
`disable-conflict` config cannot reach, because that pair is one property under
*two different* names rather than one name in two plugins.

**The mypy half.** The second bench's last row. `python/cases/mypy/` is
`margin.py` — every place an explicit `Any` can be written, which measures what
`disallow_any_explicit` buys over `strict` alone — `probes.py`, which is C5 for
the same key, and `control.py`, which is a defect only `strict` reports so that
a clean run cannot be clean because the config file has a typo in it. **Run
them with `--config-file` and nothing else**: mypy walks up from the current
directory and finds this repository's own `[tool.mypy]` from inside the
gitignored bench, so a run without one measures the wrong settings.

**C8's control.** C8 asks what ruff's `preview = true` costs. The answer turned
out to depend on how the selection is spelled, so the case carries its own
`ruff.toml` — the profile plus preview and the two rules preview reaches — and a
module built to trip both. If the control is clean, preview did not take effect
and the measurement beside it proves nothing.

**C5's probes.** C5 asks what a rule with a known false-positive reputation does
to code that is *correct*. Each probe is that code, and the probe fires or it
does not; either way the case is recorded. Two of them need a rule the profile
leaves `off` or scopes away, which is what `react/probes.config.js` is for — and
the React probes live outside `src/` so that a probe for a rule the profile
*does* enable cannot make C2's clean run dirty by design.

They are written into the same gitignored `temp/craft-bench/` as the scaffold,
for the reasons `craft_scaffold.py` gives, and the React witness lands inside
the scaffold's `src/` because the profile's `files` globs only reach there.

Run it:

    uv run python scripts/craft_scaffold.py
    uv run python scripts/craft_profile.py
    uv run python scripts/craft_cases.py

Then, from `temp/craft-bench/`:

    cd python && ruff check --config src/ruff.toml cases/src
    cd python && ruff check --config ruff.toml cases/tests
    cd python && ruff check --config ruff.toml cases/violations # C2, expected to fire
    cd react  && npx eslint --config violations.config.js violations  # C2, ditto
    cd python && ruff check cases/preview                      # C8, expected to fire
    cd python && ruff check --config ruff.toml cases/preview    # C8, expected clean
    cd python && ruff check --config ruff.toml cases/probes     # C5, expected to fire
    cd python && ruff check --config src/ruff.toml cases/tests # C5, S101 unscoped
    cd react  && npx eslint src && npx tsc --noEmit
    cd react  && npx eslint --config probes.config.js probes   # C5, expected to fire

And at `strict`, where the check that every addition fired is a command rather
than a reading:

    cd python && ruff check --config src/strict.toml cases/strict cases/preview/control.py
    cd react  && npx eslint --config strict-violations.config.js violations
    uv run python scripts/craft_cost.py --fires  # C2 at strict, both stacks

And the mypy half, which is the same criteria over the one key `strict` adds.
Every command names its config, and `MYPYPATH=src` is what lets the witnesses
resolve the scaffold's package:

    cd python && mypy --config-file mypy-strict.ini src tests    # C2, clean
    cd python && MYPYPATH=src mypy --config-file mypy-strict.ini cases/src/wit cases/tests
    cd python && mypy --config-file mypy-strict.ini cases/mypy/margin.py   # C2, fires
    cd python && mypy --config-file mypy-strict.ini cases/mypy/probes.py   # C5, clean
    cd python && mypy --config-file mypy-strict.ini cases/mypy/control.py  # strict is live
    printf '[mypy]\\nstrict = True\\n' > /tmp/strict-only.ini            # the margin:
    cd python && mypy --config-file /tmp/strict-only.ini cases/mypy/margin.py  # 0 against 10
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TARGET = REPO_ROOT / "temp" / "craft-bench"

#: Every case, keyed by its path under the target directory.
FILES: dict[str, str] = {
    "python/cases/src/wit/__init__.py": """\
\"\"\"C3's joint-satisfiability witnesses, one section per construct group.\"\"\"
""",
    "python/cases/src/wit/groups.py": """\
\"\"\"One witness per construct group, each exercising every rule in its group.

A pair of rules contradicts if satisfying one necessarily violates the other on
otherwise-correct code. A single piece of code where both rules *apply* and both
are *satisfied* refutes the "necessarily" for that pair, so a group whose rules
are jointly satisfied by one witness contains no contradicting pair.

The groups carry the rules `strict` adds as well as the ones `standard` selects,
because a level that adds rules to a group re-opens every pair in it.
\"\"\"

from __future__ import annotations

import hashlib
import logging
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from ledger.entries import Entry

logger = logging.getLogger(__name__)

# --- import: F401, I001, TID252, PLC0415, TC001, TC002, TC003 ---
#
# Every import above is at the top level, sorted, absolute, and used. The two
# that are needed only by an annotation are in the `TYPE_CHECKING` block, which
# is TC001's and TC003's remedy — and the block is a module-level `if`, so
# PLC0415 has nothing to say about the imports inside it. That pair was the
# sharpest candidate the additions brought, and this is where it is cleared.
#
# TC002 has nothing to apply to: the scaffold declares no third-party
# dependency. The limit is stated in `docs/craft/review.strict.md`.


def described(entry: Entry) -> str:
    \"\"\"Render an entry, so the first-party import is used by an annotation.\"\"\"
    return repr(entry)


# --- marker comment: ERA001, TD001-TD007 ---
#
# TODO(craft): keep this witness in step with the register (https://github.com/Eaiger-Ent/ee-standard/issues/1)
#
# One well-formed marker: an upper-case tag, an author, a colon, a space, a
# description and an issue link. **It could not be written while
# `FIX001`-`FIX004` were selected** - C3 found the group had no clean witness
# because FIX fails any file containing a TODO at all - and C5's demotion is
# what makes the group clearable rather than only arguable.


# --- signature: ANN, ARG, PLR0913, PLR0917, FBT, B006, B008, RUF012, UP ---
@dataclass(frozen=True)
class Settings:
    \"\"\"Hold the roots and labels a resolution runs against.

    RUF012 wants a mutable class default to be annotated ClassVar; this is not.
    \"\"\"

    roots: tuple[Path, ...] = ()
    labels: list[str] = field(default_factory=list)


def resolve(root: Path, name: str, *, strict: bool = False) -> Path | None:
    \"\"\"Resolve a name under a root, with three parameters and no mutable default.

    `strict` is a boolean and is keyword-only, which is FBT's remedy and leaves
    PLR0917's positional count at two.
    \"\"\"
    candidate = root / name
    if candidate.is_file():
        return candidate
    if strict:
        return None
    return root


# --- exception handler: E722, BLE001, B904, S110, S112, SIM105, EM101,
#     EM102, TRY003 ---
class WitnessError(Exception):
    \"\"\"Name a domain error, so nothing has to raise a bare Exception.\"\"\"


def read(path: Path) -> str:
    \"\"\"Read a witness file, naming what it catches and chaining from it.

    The message is bound to a name before the raise, which is EM101's remedy and
    EM102's, and it is what leaves TRY003 with nothing to report.
    \"\"\"
    try:
        return path.read_text(encoding="utf-8")
    except OSError as failure:
        message = "could not read the witness"
        raise WitnessError(message) from failure


# --- binding: F841, PLW2901, PLW0603, B023, RET504 ---
def totals(rows: list[list[int]]) -> list[int]:
    \"\"\"Total each row without an unused local, a rebind, a global or a capture.

    RET504 joins this group at `strict`: `running` is built across the loop
    rather than bound on the line above the return, so there is nothing to
    inline away.
    \"\"\"
    running: list[int] = []
    for row in rows:
        scaled = [value * 2 for value in row]
        running.append(sum(scaled))
    return running


# --- comprehension: C4xx, PERF401 ---
def names(rows: list[str]) -> set[str]:
    \"\"\"Build a set comprehension rather than a set() around a list one.\"\"\"
    return {row.strip() for row in rows if row.strip()}


# --- logging call: G001-G004, LOG015 ---
def announce(count: int) -> None:
    \"\"\"Log deferred %-formatting on a module logger, not the root or an f-string.\"\"\"
    logger.info("counted %d rows", count)


# --- security-sensitive call: S105-S107, S311, S324, S501, S608, S104 ---
LISTEN_HOST = "127.0.0.1"


def token() -> str:
    \"\"\"Derive a token from a cryptographic source and a strong hash.\"\"\"
    raw = secrets.token_bytes(32)
    return hashlib.sha256(raw).hexdigest()


def query(table: str) -> str:
    \"\"\"Choose SQL from fixed statements rather than splicing it.\"\"\"
    statements = {
        "entries": "SELECT id FROM entries WHERE recorded_at > ?",
        "totals": "SELECT id FROM totals WHERE recorded_at > ?",
    }
    try:
        return statements[table]
    except KeyError as unknown:
        message = "unknown table"
        raise WitnessError(message) from unknown


# --- body size: PLR0915, C901, PLR1702 ---
def stamped(when: datetime | None = None) -> str:
    \"\"\"Stamp a time, short and unbranching.\"\"\"
    return (when or datetime.now(UTC)).isoformat()


def deepest(rows: list[list[int]], *, only_positive: bool) -> int:
    \"\"\"Walk two levels under two guards, which is four blocks against a cap of five.

    PLR1702 joins this group at `strict`. The witness nests as far as the rule
    allows and no further, so the rule has applied and is satisfied rather than
    having found nothing to look at.
    \"\"\"
    total = 0
    if only_positive:
        for row in rows:
            for value in row:
                if value > 0:
                    total += value
    return total


# --- class body: PLR0904 ---
class Focused:
    \"\"\"Keep a class under the public-method ceiling.

    PLR0904's target is a class body, where every other size rule in the
    profile targets a function, so it pairs with nothing.
    \"\"\"

    def one(self) -> int:
        \"\"\"Return the first.\"\"\"
        return 1

    def two(self) -> int:
        \"\"\"Return the second.\"\"\"
        return 2


# --- docstring: D100-D107, D205, D401 ---
class Documented:
    \"\"\"Carry a docstring on every definition D1xx reaches.

    Each docstring below is multi-line with a blank line after an imperative
    summary, so D205 and D401 have applied to it and passed. That is what
    clears their seventeen pairs with D1xx: a documented definition is one
    node both halves of the property look at.
    \"\"\"

    class Nested:
        \"\"\"Document a public nested class, which is D106's target.

        D101 does not reach here and D106 does, which is why the two are
        disjoint rather than paired.
        \"\"\"

    def __init__(self) -> None:
        \"\"\"Bind the witness value.

        D107's target is this method and no other.
        \"\"\"
        self.value = 1

    def __str__(self) -> str:
        \"\"\"Render the witness.

        D105's target is a magic method, which no other D1xx rule reaches.
        \"\"\"
        return "documented"

    def method(self) -> int:
        \"\"\"Return the witness value.

        D102's target is a public method.
        \"\"\"
        return self.value


def documented() -> int:
    \"\"\"Return one, from a public function.

    D103's target is a public function, and this docstring is the shape D205
    and D401 ask for.
    \"\"\"
    return 1
""",
    "python/cases/tests/__init__.py": """\
\"\"\"Hold C3's test-construct witness, which D104 asks a package to document.\"\"\"
""",
    "python/cases/tests/test_witness.py": """\
\"\"\"C3's witness for the test construct group: PT006, PT007, PT011, PT012, PT018.

Standalone by design. It imports nothing first-party, so that isort's
first-party question — which depends on where the witness sits rather than on
any rule under test — cannot colour the result.
\"\"\"

from __future__ import annotations

import pytest


class WitnessError(Exception):
    \"\"\"A domain error, so `pytest.raises` has something narrow to name.\"\"\"


def query(table: str) -> str:
    \"\"\"Choose SQL from fixed statements rather than splicing it.\"\"\"
    statements = {
        "entries": "SELECT id FROM entries WHERE recorded_at > ?",
        "totals": "SELECT id FROM totals WHERE recorded_at > ?",
    }
    try:
        return statements[table]
    except KeyError as unknown:
        message = "unknown table"
        raise WitnessError(message) from unknown


@pytest.mark.parametrize(
    ("table", "expected"),
    [
        ("entries", "SELECT id FROM entries WHERE recorded_at > ?"),
        ("totals", "SELECT id FROM totals WHERE recorded_at > ?"),
    ],
)
def test_query_returns_a_fixed_statement(table: str, expected: str) -> None:
    \"\"\"Return the statement the table names.

    D103 reaches a test function like any other, and a case is written to
    satisfy the instrument where the scaffold is not.
    \"\"\"
    assert query(table) == expected


def test_an_unknown_table_is_a_witness_error() -> None:
    \"\"\"Raise a witness error for a table that is not in the set.

    The docstring is D103's, and the narrow `pytest.raises` is PT011's.
    \"\"\"
    with pytest.raises(WitnessError, match="unknown table"):
        query("nowhere")


def test_the_two_statements_differ() -> None:
    \"\"\"Distinguish the two statements.

    One behaviour and one assertion, which is what PT018 asks for.
    \"\"\"
    assert query("entries") != query("totals")
""",
    "python/cases/probes/__init__.py": """\
""",
    "python/cases/probes/false_positives.py": """\
\"\"\"C5's probes: correct code that a rule with a reputation is known to flag.

Each function is code a reviewer would pass. If the rule fires here, the finding
is a false positive and `docs/craft/review.bench.md` records the case whether the
rule survives it or not.
\"\"\"

from __future__ import annotations

import random
from typing import Any


def jitter(base: float) -> float:
    \"\"\"S311. Sampling jitter is not a secret, and `secrets` is the wrong tool.\"\"\"
    return base * random.uniform(0.9, 1.1)


def select_from(table: str) -> str:
    \"\"\"S608. The table name is chosen from a fixed set, so nothing user-supplied
    reaches the statement - but it is still interpolated.
    \"\"\"
    allowed = {"entries", "totals"}
    if table not in allowed:
        message = "unknown table"
        raise ValueError(message)
    return f"SELECT id FROM {table} WHERE recorded_at > ?"


def describe(value: Any) -> str:
    \"\"\"ANN401. A `repr` helper genuinely takes anything.\"\"\"
    return repr(value)


# The wire format this module reads, documented for a reader rather than run:
# entries = [{"amount": "1.00", "recorded_at": "2026-09-01T09:00:00+00:00"}]
def documented() -> int:
    \"\"\"ERA001. The comment above is a documented example, not dead code.\"\"\"
    return 1
""",
    "python/cases/probes/strict.py": """\
\"\"\"C5's probes for the rules `strict` adds: correct code a rule is known to flag.

Each probe is code a reviewer would pass. Where a probe does **not** fire, a
control sits beside it — the same shape without the thing that excuses it — so
that a silent rule is shown to be looking rather than assumed to be. The first
bench established that discipline on `anchor-ambiguous-text` and it is the only
reason a negative result here is worth anything.

`docs/craft/review.strict.md` § What was probed records what each one did.
\"\"\"

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import get_type_hints

BIND_ALL = "0.0.0.0"  # S104. A container listens on every interface by design.


def render(payload: dict[str, object]) -> str:
    \"\"\"Render a payload, importing the renderer only when one is asked for.

    PLC0415. A deferred import is the documented remedy for an optional
    dependency and for a circular one, and the rule cannot tell either from a
    careless import.
    \"\"\"
    import json

    return json.dumps(payload)


@dataclass
class Money:
    \"\"\"Hold an amount whose annotation a runtime consumer has to resolve.

    TC003. `get_type_hints` below evaluates this annotation, so moving `Decimal`
    into a type-checking block raises `NameError` rather than deferring
    anything. The rule reads the annotation and not its consumer.
    \"\"\"

    amount: Decimal


def field_types() -> dict[str, object]:
    \"\"\"Resolve the annotations at runtime, which is what needs `Decimal` imported.\"\"\"
    return dict(get_type_hints(Money))


def settled(rows: list[int]) -> int:
    \"\"\"Total the rows through a name that says what the number is.

    RET504, and it does **not** fire: ruff skips an annotated assignment, which
    is the escape hatch the rule's reputation is about. `unsettled` below is the
    control.
    \"\"\"
    settlement: int = sum(rows)
    return settlement


def unsettled(rows: list[int]) -> int:
    \"\"\"Control for RET504: the same shape with the annotation removed.\"\"\"
    settlement = sum(rows)
    return settlement


class Ledger:
    \"\"\"Hold a balance behind a property.\"\"\"

    def __init__(self, balance: int) -> None:
        \"\"\"Bind the balance.\"\"\"
        self._balance = balance

    @property
    def balance(self) -> int:
        \"\"\"The amount currently held.

        D401, and it does **not** fire: ruff exempts a property, which is the
        convention PEP 257 documents for one. `held` below is the control.
        \"\"\"
        return self._balance

    def held(self) -> int:
        \"\"\"The amount currently held.

        Control for D401: the same docstring on a method rather than a property.
        \"\"\"
        return self._balance

    def area(self) -> float:
        \"\"\"Return the area, in a stub a subclass is expected to replace.

        EM101. The remedy binds a name for a one-line stub, which is the cost
        this probe is about rather than a defect in the rule.
        \"\"\"
        raise NotImplementedError("subclasses must implement area")
""",
    "python/cases/probes/runtime-evaluated.toml": """\
# C5's TC003 escape hatch, and **not** the profile.
#
# The probe beside it shows the rule breaking a dataclass whose annotations
# `get_type_hints` resolves. Ruff has a setting for exactly that shape, and the
# file exists so that the claim is a run rather than a reading: with this
# configuration the probe is clean and nothing else changes.

extend = "../../strict.toml"

[lint.flake8-type-checking]
runtime-evaluated-decorators = ["dataclasses.dataclass"]
""",
    "react/probes/Effects.tsx": """\
/* C5's probe for the rule `strict` adds: correct code it is known to flag.
 *
 * A ref is deliberately not reactive — React guarantees the object identity is
 * stable — so a dependency array that omits it is correct. A rule that demanded
 * it listed would be asking for a dependency that can never change. */
import { useEffect, useRef } from 'react'

export function RefInEffect({ id }: { id: string }) {
  const seenRef = useRef<string | null>(null)
  useEffect(() => {
    seenRef.current = id
  }, [id])
  return <p>{id}</p>
}

export function Control({ id, other }: { id: string; other: string }) {
  useEffect(() => {
    console.log(id, other)
  }, [id])
  return <p>{id}</p>
}
""",
    "react/strict-probes.config.js": """\
import reactHooks from 'eslint-plugin-react-hooks'
import base from './probes.config.js'

export default [
  ...base,
  {
    files: ['probes/**/*.tsx'],
    plugins: { 'react-hooks': reactHooks },
    rules: {
      'react-hooks/exhaustive-effect-dependencies': [
        'error',
        { environment: { validateExhaustiveEffectDependencies: 'all' } },
      ],
    },
  },
]
""",
    "python/cases/preview/__init__.py": """\
""",
    "python/cases/preview/ruff.toml": """\
# C8's configuration, and **not** the profile.
#
# The register expected `preview = true` to arrive with all of ruff's preview
# rules, because a broad selector picks up its own preview rules once preview is
# on. This selection is almost entirely exact codes, so it picks up none — which
# is what makes the two properties reachable at all. The file exists so that
# claim can be run rather than read.

extend = "../../ruff.toml"
preview = true

[lint]
extend-select = [
  "PLR1702",  # python.nesting-depth
  "PLR0904",  # python.class-size
]
""",
    "python/cases/preview/control.py": """\
\"\"\"C8's control: the two properties preview would reach, made to fire.

If these are clean, `preview = true` did not take effect and the C8
measurement beside them proves nothing.
\"\"\"

from __future__ import annotations


def nested(rows: list[list[list[int]]], *, flag: bool) -> int:
    \"\"\"PLR1702. Six levels, which is past the default of five.\"\"\"
    total = 0
    if flag:
        for outer in rows:
            for middle in outer:
                for value in middle:
                    if value > 0:
                        while total < value:
                            total += 1
    return total


class Wide:
    \"\"\"PLR0904. Twenty-five public methods, past the default of twenty.\"\"\"

    def m01(self) -> int:
        \"\"\"One of many.\"\"\"
        return 1

    def m02(self) -> int:
        \"\"\"One of many.\"\"\"
        return 2

    def m03(self) -> int:
        \"\"\"One of many.\"\"\"
        return 3

    def m04(self) -> int:
        \"\"\"One of many.\"\"\"
        return 4

    def m05(self) -> int:
        \"\"\"One of many.\"\"\"
        return 5

    def m06(self) -> int:
        \"\"\"One of many.\"\"\"
        return 6

    def m07(self) -> int:
        \"\"\"One of many.\"\"\"
        return 7

    def m08(self) -> int:
        \"\"\"One of many.\"\"\"
        return 8

    def m09(self) -> int:
        \"\"\"One of many.\"\"\"
        return 9

    def m10(self) -> int:
        \"\"\"One of many.\"\"\"
        return 10

    def m11(self) -> int:
        \"\"\"One of many.\"\"\"
        return 11

    def m12(self) -> int:
        \"\"\"One of many.\"\"\"
        return 12

    def m13(self) -> int:
        \"\"\"One of many.\"\"\"
        return 13

    def m14(self) -> int:
        \"\"\"One of many.\"\"\"
        return 14

    def m15(self) -> int:
        \"\"\"One of many.\"\"\"
        return 15

    def m16(self) -> int:
        \"\"\"One of many.\"\"\"
        return 16

    def m17(self) -> int:
        \"\"\"One of many.\"\"\"
        return 17

    def m18(self) -> int:
        \"\"\"One of many.\"\"\"
        return 18

    def m19(self) -> int:
        \"\"\"One of many.\"\"\"
        return 19

    def m20(self) -> int:
        \"\"\"One of many.\"\"\"
        return 20

    def m21(self) -> int:
        \"\"\"One of many.\"\"\"
        return 21

    def m22(self) -> int:
        \"\"\"One of many.\"\"\"
        return 22

    def m23(self) -> int:
        \"\"\"One of many.\"\"\"
        return 23

    def m24(self) -> int:
        \"\"\"One of many.\"\"\"
        return 24

    def m25(self) -> int:
        \"\"\"One of many.\"\"\"
        return 25
""",
    "python/cases/violations/python_violations.py": """\
\"\"\"C2's deliberate violations: one defect per selected rule family.

Every line here is wrong on purpose. The file is linted, never imported and
never run - it exists so that "the configuration produces a verdict in both
directions" is a run rather than a claim, and so that a family which has
silently stopped firing cannot look like a family with nothing to say.

It carries no `__init__.py` on purpose either: that is the INP001 defect.
\"\"\"

from typing import Optional  # I001 + UP045: unsorted, and a legacy Optional
import hashlib
import logging
import os.path

from .. import something  # TID252: a relative import from the parent

BUILTIN = 1


class lowercase_class:  # N801: not PascalCase
    defaults = {}  # RUF012: a mutable class default, unannotated

    def reach(self, other: "lowercase_class") -> int:
        return other._private  # SLF001: private member access


def mutable_default(items: list[int] = []) -> None:  # B006: mutable default
    \"\"\"Two defects: the default above, and the unused argument below.\"\"\"


def unused_argument(used: int, ignored: int) -> int:  # ARG001: never read
    return used


def positional_flag(value: int, verbose: bool) -> int:  # FBT001: a boolean trap
    return value if verbose else 0


def rebind_global() -> None:
    global BUILTIN  # PLW0603: rebinding module state
    BUILTIN = 2


def blind() -> None:
    try:
        rebind_global()
    except Exception:  # BLE001: catches everything
        pass  # S110 + SIM105: swallowed in silence


def bare() -> None:
    try:
        rebind_global()
    except:  # E722: a bare except
        raise ValueError("no context")  # B904: raised without `from`


def naive_time() -> object:
    import datetime  # PLC0415 is not selected; this is here for DTZ below

    return datetime.datetime.now()  # DTZ005: no timezone


def weak_hash(payload: bytes) -> str:
    return hashlib.md5(payload).hexdigest()  # S324: an insecure hash


def joined(root: str, name: str) -> str:
    return os.path.join(root, name)  # PTH118: os.path rather than pathlib


def unnecessary_call(values: list[int]) -> list[int]:
    return list([value for value in values])  # C411: a list around a comprehension


def appended(values: list[int]) -> list[int]:
    out = []
    for value in values:
        out.append(value * 2)  # PERF401: an append loop
    return out


def legacy(value: Optional[int]) -> int:  # UP045: not PEP 604
    return value or 0


def many(a: int, b: int, c: int, d: int, e: int, f: int) -> int:  # PLR0913
    return a + b + c + d + e + f


def long_body() -> int:
    \"\"\"PLR0915: past the twenty-five statements C6 settled on.\"\"\"
    n01 = 1
    n02 = 2
    n03 = 3
    n04 = 4
    n05 = 5
    n06 = 6
    n07 = 7
    n08 = 8
    n09 = 9
    n10 = 10
    n11 = 11
    n12 = 12
    n13 = 13
    n14 = 14
    n15 = 15
    n16 = 16
    n17 = 17
    n18 = 18
    n19 = 19
    n20 = 20
    n21 = 21
    n22 = 22
    n23 = 23
    n24 = 24
    n25 = 25
    n26 = 26
    return (
        n01 + n02 + n03 + n04 + n05 + n06 + n07 + n08 + n09 + n10 + n11 + n12 + n13
        + n14 + n15 + n16 + n17 + n18 + n19 + n20 + n21 + n22 + n23 + n24 + n25 + n26
    )


def logged(count):  # ANN001 + ANN201: unannotated
    logging.info(f"count is {count}")  # G004 + LOG015: f-string, root logger


def tangled(values: list[int]) -> int:
    \"\"\"C901: past the complexity ceiling of ten.\"\"\"
    total = 0
    for value in values:
        if value == 1:
            total += 1
        elif value == 2:
            total += 2
        elif value == 3:
            total += 3
        elif value == 4:
            total += 4
        elif value == 5:
            total += 5
        elif value == 6:
            total += 6
        elif value == 7:
            total += 7
        elif value == 8:
            total += 8
        elif value == 9:
            total += 9
        else:
            total -= 1
    return total


# result = joined("a", "b")
def trailing() -> int:
    return 1
""",
    "python/cases/violations/test_violations.py": """\
\"\"\"C2's deliberate violations for the pytest family, which only fire in a test.

Linted, never collected. `pytest` is imported for the decorators the rules read.
\"\"\"

from __future__ import annotations

import pytest


@pytest.mark.parametrize("value,expected", ((1, 2), (2, 3)))  # PT006 + PT007
def test_parametrised(value: int, expected: int) -> None:
    assert value + 1 == expected


def test_raises_too_broad() -> None:
    with pytest.raises(Exception):  # PT011: no `match`, and too broad
        raise ValueError


def test_raises_with_multiple_statements() -> None:
    with pytest.raises(ValueError, match="x"):  # PT012: more than one statement
        value = 1
        raise ValueError(value)


def test_composite_assertion() -> None:
    value = 2
    assert value > 0 and value < 10  # PT018: a composite assertion
""",
    "python/cases/strict/__init__.py": "",
    "python/cases/strict/undocumented.py": """\
from __future__ import annotations


class Undocumented:
    class Nested:
        pass

    def __init__(self) -> None:
        self.value = 1

    def __str__(self) -> str:
        return "undocumented"

    def method(self) -> int:
        return self.value


def function() -> int:
    return 1
""",
    "python/cases/strict/docstring_form.py": """\
\"\"\"D205 and D401: docstrings that exist and are the wrong shape.\"\"\"

from __future__ import annotations


def no_blank_line_after_summary() -> int:
    \"\"\"Return one, in a summary line.
    D205: there is no blank line between that summary and this description.
    \"\"\"
    return 1


def not_imperative() -> int:
    \"\"\"Returns one, in the indicative mood PEP 257 does not ask for.\"\"\"
    return 1
""",
    "python/cases/strict/todo_comments.py": """\
\"\"\"TD001 to TD007: one malformed marker comment each.

**`FIX001`-`FIX004` were here and are demoted**, C5's second demotion. They read
the marker's *presence* where TD reads its *form*, so every line below used to
draw a FIX finding as well - and, worse, so did a marker comment with nothing
wrong with it. `cases/src/wit/groups.py` now carries the well-formed TODO that
was unwritable while they were selected.
\"\"\"

from __future__ import annotations

# FIXME: TD001 wants the tag to be TODO
# TODO: TD002 - no author
# TODO(nc): TD003 - no issue link
# TODO(nc) TD004 - no colon
# TODO(nc):
# todo(nc): TD006 - the tag is not upper case
# TODO(nc):TD007 - no space after the colon
# XXX: TD001 again, with the other invalid tag
""",
    "python/cases/strict/strict_violations.py": """\
\"\"\"The strict additions that are neither docstrings nor marker comments.

PLR1702 and PLR0904 are deliberately **not** here. Their cases were written for
C8, in `cases/preview/control.py`, and they are exactly the defects C2 needs;
writing a second six-deep function and a second twenty-five-method class would
be a copy free to drift from the one the preview measurement reads.
\"\"\"

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from ledger.entries import Entry

HOST = "0.0.0.0"


def imports_inside(path: Path) -> str:
    \"\"\"PLC0415: an import that is not at the top level.\"\"\"
    import json

    return json.dumps(str(path))


def raises_a_literal() -> None:
    \"\"\"EM101: a string literal handed to an exception.\"\"\"
    raise ValueError("the ledger is closed")


def raises_an_fstring(day: str) -> None:
    \"\"\"EM102: an f-string handed to an exception.\"\"\"
    raise ValueError(f"the ledger is closed on {day}")


def assigns_before_return(rows: list[int]) -> int:
    \"\"\"RET504: a name bound only to be returned on the next line.\"\"\"
    total = sum(rows)
    return total


def annotated(entry: Entry, *, when: datetime, path: Path, item: pytest.Item) -> str:
    \"\"\"TC001, TC002 and TC003: four imports used only in this signature.

    The three named parameters are keyword-only so that PLR0917, which is a
    `standard` rule and not one of the additions, has nothing to say about a
    case written for something else.
    \"\"\"
    return f"{entry} {when} {path} {item}"
""",
    "python/cases/mypy/margin.py": """\
\"\"\"Every place an explicit `Any` can be written, one site per definition.

C2's violation direction for `disallow_any_explicit`, and the measurement of
its **margin**: run this file with `strict = True` alone and with the key as
well, and the difference is what Craft's one type-checker contribution buys.
Four of the sites are also `ANN401`, which is `standard`'s instrument for the
narrower property, and the other five are not — that difference is C4's.
\"\"\"

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast


def public_argument(value: Any) -> str:
    \"\"\"An `Any` in a public argument annotation. ANN401 as well.\"\"\"
    return str(value)


def _private_argument(value: Any) -> str:
    \"\"\"The same on a private function. ANN401 as well, which is a finding.\"\"\"
    return str(value)


def public_return(value: str) -> Any:
    \"\"\"An `Any` in a return annotation. ANN401 as well.\"\"\"
    return value


def variable_annotation() -> str:
    \"\"\"An `Any` in a local variable annotation. Not a signature, so not ANN401.\"\"\"
    holder: Any = "x"
    return str(holder)


type Alias = dict[str, Any]
\"\"\"An `Any` inside a PEP 695 alias, which is what a 3.14 repository writes.\"\"\"


def generic_parameter(rows: list[Any]) -> int:
    \"\"\"An `Any` inside a generic rather than as the whole annotation.\"\"\"
    return len(rows)


def through_cast(value: str) -> str:
    \"\"\"An `Any` in a `cast`, which is the documented escape hatch.\"\"\"
    return str(cast(Any, value))


def kwargs_passthrough(**kwargs: Any) -> int:
    \"\"\"An `Any` on `**kwargs`. ANN401 as well.\"\"\"
    return len(kwargs)


@dataclass(frozen=True)
class Holder:
    \"\"\"An `Any` on a dataclass field, which is the one that reports twice.\"\"\"

    payload: Any
""",
    "python/cases/mypy/probes.py": """\
\"\"\"C5 for `disallow_any_explicit`: correct code, and the rule's reputation.

The complaint against banning explicit `Any` is that some shapes cannot be
written without it. Each probe is one of those shapes, written the way the
current type system says to write it. All four are clean, which is the finding:
the reputation is about a version of Python that no longer needs the escape.
\"\"\"

from __future__ import annotations

import functools
import json
from collections.abc import Callable
from pathlib import Path
from typing import ParamSpec, TypedDict, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def timed(func: Callable[P, R]) -> Callable[P, R]:
    \"\"\"P1: a pass-through decorator. PEP 612's `ParamSpec` removed the `Any`.\"\"\"

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return func(*args, **kwargs)

    return wrapper


class Row(TypedDict):
    \"\"\"P2's shape for decoded JSON, which is the documented remedy.\"\"\"

    description: str
    amount: str


def read_rows(path: Path) -> list[Row]:
    \"\"\"P2: decoded JSON given a shape rather than left as `Any`.\"\"\"
    decoded: list[Row] = json.loads(path.read_text(encoding="utf-8"))
    return decoded


def describe(value: object) -> str:
    \"\"\"P3: `object` where a signature genuinely accepts anything.\"\"\"
    return str(value)


def forward(**kwargs: object) -> int:
    \"\"\"P4: `**kwargs` as `object` rather than `Any`.\"\"\"
    return len(kwargs)
""",
    "python/cases/mypy/control.py": """\
\"\"\"A control for the `strict = True` half of the bench config.

`disallow_any_explicit` is Craft's whole contribution, but `mypy-strict.ini`
also reproduces TYP-001's `strict`, and a typo there would make every clean run
above clean for the wrong reason. This is a defect **only** `strict` reports:
mypy with no configuration says nothing about it.

**Run it from `temp/craft-bench/python/`.** mypy discovers a configuration from
the current directory, so a run started at the repository root reads this
repository's `[tool.mypy]` and measures the wrong settings entirely. That is how
the flag comparison below was first got wrong.
\"\"\"


def untyped(value):  # noqa: ANN001, ANN201 - the missing annotation is the defect
    \"\"\"A function with no annotations at all.\"\"\"
    return value
""",
    "react/violations/Violations.tsx": """\
/* Every defect in this file is deliberate. */
import { createContext, useEffect, useState, forwardRef, useContext } from 'react'
import * as React from 'react'

const NumberContext = createContext<{ n: number } | null>(null)

export class Legacy extends React.Component {
  render() {
    return <div />
  }
}

export function Unknown() {
  return <div class="wrong" />
}

export function TargetBlank() {
  return <a href="https://example.com" target="_blank">Away</a>
}

export function DuplicateKeys() {
  return (
    <ul>
      <li key="a">one</li>
      <li key="a">two</li>
    </ul>
  )
}

export function LeakedConditional({ count }: { count: number }) {
  return <div>{count && <p>some</p>}</div>
}

export function UnstableContext({ n }: { n: number }) {
  return (
    <NumberContext.Provider value={{ n }}>
      <span />
    </NumberContext.Provider>
  )
}

export function DerivedInEffect({ first, last }: { first: string; last: string }) {
  const [full, setFull] = useState('')
  useEffect(() => {
    setFull(`${first} ${last}`)
  }, [first, last])
  return <p>{full}</p>
}

export function IncompleteDeps({ id }: { id: string }) {
  const [seen, setSeen] = useState('')
  useEffect(() => {
    setSeen(id)
  }, [])
  return <p>{seen}</p>
}

export function IndexKeys({ rows }: { rows: string[] }) {
  return (
    <ul>
      {rows.map((row, index) => (
        <li key={index}>{row}</li>
      ))}
    </ul>
  )
}

export const Forwarded = forwardRef<HTMLDivElement>((_props, ref) => <div ref={ref} />)

export function UsesContext() {
  const value = useContext(NumberContext)
  return <span>{value?.n}</span>
}

export function CommentTextNode() {
  return <div>// this renders as text</div>
}

export function Dangerous({ html }: { html: string }) {
  return <div dangerouslySetInnerHTML={{ __html: html }} />
}

export function RoleOverTag() {
  return <div role="button" tabIndex={0} onClick={() => {}} onKeyDown={() => {}} />
}

export function BadLang() {
  return <html lang="foo" />
}

export function MisusedPromise({ save }: { save: () => Promise<void> }) {
  return <button type="button" onClick={save} />
}

export function Leaks({ el }: { el: HTMLElement }) {
  useEffect(() => {
    el.addEventListener('click', () => {})
    setTimeout(() => {}, 100)
    setInterval(() => {}, 100)
    void fetch('/x')
    new IntersectionObserver(() => {}).observe(el)
    new ResizeObserver(() => {}).observe(el)
  }, [el])
  return null
}

export function UnlabelledControl() {
  return (
    <form>
      <input type="text" />
    </form>
  )
}
""",
    "react/violations/Shared.tsx": """\
/* C4: one deliberate defect per rule name both plugins ship. Each should draw
 * exactly one diagnostic, from one plugin. */
import { useMemo, useRef, useState } from 'react'

export function ConditionalHook({ on }: { on: boolean }) {
  if (on) {
    const [n] = useState(0)
    return <p>{n}</p>
  }
  return null
}

export function ImpureRender() {
  return <p>{Date.now()}</p>
}

export function GlobalInRender() {
  window.scrollTo(0, 0)
  return <p>global</p>
}

export function MutatesProps({ item }: { item: { n: number } }) {
  item.n = 1
  return <p>{item.n}</p>
}

export function SetsStateInRender() {
  const [n, setN] = useState(0)
  setN(n + 1)
  return <p>{n}</p>
}

export function ReadsRefInRender() {
  const ref = useRef<number>(0)
  return <p>{ref.current}</p>
}

export function BadMemo({ n }: { n: number }) {
  const value = useMemo(() => {
    n + 1
  }, [n])
  return <p>{String(value)}</p>
}

export function NestedComponent() {
  function Inner() {
    return <span>inner</span>
  }
  return <Inner />
}
""",
    "react/violations/types.ts": """\
/* Deliberate: the type-aware @typescript-eslint rules, plus the two scoped ones. */
declare const loose: any

export function unsafeReturn() {
  return loose
}
export function unsafeCall(): void {
  loose()
}
export function unsafeMember(): unknown {
  return loose.field
}
export function unsafeAssign(): void {
  const taken: string = loose
  void taken
}
export function unsafeArgument(): void {
  JSON.stringify(loose as string, loose)
}
export function nonNull(value?: string): number {
  return value!.length
}
export function thrown(): void {
  throw 'a string, not an Error'
}
export async function work(): Promise<void> {
  await Promise.resolve()
}
export function floating(): void {
  work()
}
""",
    "react/violations/Debug.test.tsx": """\
/* Deliberate: the testing-library rules the profile escalates or adds. */
import { render, screen } from '@testing-library/react'

it('leaves debug output behind', () => {
  render(<p>hello</p>)
  screen.debug()
  expect(screen.getByText('hello')).toBeTruthy()
})
""",
    "react/violations.config.js": """\
// C2's violation configuration. **It is not the profile** — it is the profile
// pointed at another directory.
//
// The deliberate defects cannot live under `src/`, because C2's other half is a
// clean run over `src/` and a directory of defects would make that impossible
// by construction. So the profile's blocks are remapped from `src/` to
// `violations/`, which keeps one definition of what is enabled: if a rule is
// dropped from the profile it stops being demonstrated here too, rather than
// this file quietly asserting a rule the profile no longer has.
import profile from './eslint.config.js'

const remap = (pattern) =>
  pattern.startsWith('src/') ? pattern.replace(/^src\\//, 'violations/') : pattern

export default profile.map((block) => {
  const moved = { ...block }
  if (Array.isArray(block.files)) moved.files = block.files.map(remap)
  if (Array.isArray(block.ignores)) moved.ignores = block.ignores.map(remap)
  if (block.languageOptions?.parserOptions?.projectService) {
    moved.languageOptions = {
      ...block.languageOptions,
      parserOptions: {
        ...block.languageOptions.parserOptions,
        projectService: false,
        project: './tsconfig.violations.json',
      },
    }
  }
  return moved
})
""",
    "react/tsconfig.violations.json": """\
{
  "extends": "./tsconfig.json",
  "include": ["violations"]
}
""",
    "react/violations/Effects.tsx": """\
/* C2 at `strict`: cases written for react-hooks/exhaustive-effect-dependencies,
 * the one rule that level adds. Both directions the rule reports, because the
 * missing one overlaps `exhaustive-deps` and the extra one does not. */
import { useEffect, useState } from 'react'

export function MissingDep({ id }: { id: string }) {
  const [seen, setSeen] = useState('')
  useEffect(() => {
    console.log(id)
    setSeen('x')
  }, [])
  return <p>{seen}</p>
}

export function ExtraDep({ id, other }: { id: string; other: string }) {
  useEffect(() => {
    console.log(id)
  }, [id, other])
  return <p>{id}</p>
}
""",
    "react/strict-violations.config.js": """\
// C2's violation configuration at `strict`, and it is `violations.config.js`
// one level up: the **strict** profile pointed at `violations/` rather than a
// second copy of what that level enables.
import profile from './strict.config.js'

const remap = (pattern) =>
  pattern.startsWith('src/') ? pattern.replace(/^src\\//, 'violations/') : pattern

export default profile.map((block) => {
  const moved = { ...block }
  if (Array.isArray(block.files)) moved.files = block.files.map(remap)
  if (Array.isArray(block.ignores)) moved.ignores = block.ignores.map(remap)
  if (block.languageOptions?.parserOptions?.projectService) {
    moved.languageOptions = {
      ...block.languageOptions,
      parserOptions: {
        ...block.languageOptions.parserOptions,
        projectService: false,
        project: './tsconfig.violations.json',
      },
    }
  }
  return moved
})
""",
    "react/src/cases/Witness.tsx": """\
import { createContext, useCallback, useEffect, useMemo, useState } from 'react'

interface Row {
  readonly id: string
  readonly label: string
}

interface WitnessContext {
  readonly selected: string | null
  readonly select: (id: string) => void
}

const SelectionContext = createContext<WitnessContext | null>(null)

interface WitnessProps {
  readonly rows: readonly Row[]
  readonly onSave: (id: string) => Promise<void>
  readonly onWatch: (id: string) => () => void
}

export function Witness({ rows, onSave, onWatch }: WitnessProps) {
  const [selected, setSelected] = useState<string | null>(null)

  // `use-memo` and `preserve-manual-memoization` both apply here, and
  // `exhaustive-deps` wants every reactive value listed. One dependency array
  // satisfies all three.
  const select = useCallback((id: string) => {
    setSelected(id)
  }, [])
  const value = useMemo<WitnessContext>(() => ({ selected, select }), [selected, select])

  // The effect group. `exhaustive-effect-dependencies` joins it at `strict`
  // and is the only rule in the profile that reads the array in *both*
  // directions, so the witness lists every reactive value the body reads and
  // no others. `set-state-in-effect` and `no-deriving-state-in-effects` apply
  // to the same effect and are satisfied by it synchronising with something
  // outside React rather than computing state.
  useEffect(() => {
    if (selected === null) return undefined
    return onWatch(selected)
  }, [onWatch, selected])

  // `no-floating-promises` and `no-misused-promises` both apply to an async
  // handler: the promise is caught rather than dropped, and the handler passed
  // to `onClick` returns void rather than a promise.
  const save = (id: string): void => {
    onSave(id).catch(() => {
      setSelected(null)
    })
  }

  return (
    <SelectionContext value={value}>
      <fieldset>
        <legend>Witness</legend>
        <label htmlFor="witness-filter">Filter</label>
        <input id="witness-filter" name="filter" type="text" />
      </fieldset>
      <ul>
        {rows.map((row) => (
          // `no-missing-key` requires a key and `no-array-index-key` forbids the
          // index. A stable id satisfies both, so the pair is jointly
          // satisfiable rather than contradictory.
          <li key={row.id}>
            <button
              type="button"
              onClick={() => {
                save(row.id)
              }}
            >
              {row.label}
            </button>
          </li>
        ))}
      </ul>
    </SelectionContext>
  )
}
""",
    "react/probes/Probes.tsx": """\
import { useState } from 'react'

const STEPS = ['Basket', 'Delivery', 'Payment'] as const

/** `no-array-index-key`. A frozen literal list with no ids and no reordering. */
export function Steps() {
  return (
    <ol>
      {STEPS.map((step, index) => (
        <li key={index}>{step}</li>
      ))}
    </ol>
  )
}

/** `anchor-ambiguous-text`. The visible text is on the rule's own ambiguous
 * list; the `aria-label` says exactly where the link goes. */
export function Checkout() {
  return (
    <a href="/checkout" aria-label="Continue to checkout">
      Learn more
    </a>
  )
}

/** `explicit-module-boundary-types`. An exported component, inferred as JSX. */
export function Counter() {
  const [count, setCount] = useState(0)
  return (
    <button
      type="button"
      onClick={() => {
        setCount((current) => current + 1)
      }}
    >
      {count}
    </button>
  )
}
""",
    "react/probes/Control.tsx": """\
/** The control for the `anchor-ambiguous-text` probe: the same ambiguous text
 * with no `aria-label`. If this does not fire, the probe proves nothing. */
export function Bare() {
  return <a href="/checkout">Learn more</a>
}
""",
    "react/probes.config.js": """\
// C5's probe configuration. **It is not the profile.**
//
// A probe is correct code that a rule with a reputation is known to flag, and
// some of those rules the profile leaves `off` or scopes away - so they need a
// configuration that turns them on before they can be shown doing it. The
// probes live outside `src/`, because a probe for a rule the profile *does*
// enable would otherwise make C2's clean run dirty by design.
//
// No project service: none of the probed rules needs type information, and
// asking for types here would put the probes in the scaffold's `tsconfig`.
import jsxA11y from 'eslint-plugin-jsx-a11y'
import eslintReact from '@eslint-react/eslint-plugin'
import tseslint from 'typescript-eslint'

export default [
  {
    ...tseslint.configs.base,
    files: ['probes/**/*.tsx'],
  },
  { ...eslintReact.configs.recommended, files: ['probes/**/*.tsx'] },
  { ...jsxA11y.flatConfigs.recommended, files: ['probes/**/*.tsx'] },
  {
    files: ['probes/**/*.tsx'],
    rules: {
      // On in the profile. Probed because a frozen literal list has no id to
      // use instead of the index.
      '@eslint-react/no-array-index-key': 'error',
      // `off` in the profile - `react.a11y-link-purpose` is bucket 3 and this
      // rule is the register's named false-positive case.
      'jsx-a11y/anchor-ambiguous-text': 'error',
      // Scoped to `*.ts` in the profile, so a component never meets it.
      '@typescript-eslint/explicit-module-boundary-types': [
        'error',
        { allowTypedFunctionExpressions: true },
      ],
    },
  },
]
""",
}


def write(target: Path, *, force: bool = False) -> int:
    """Write every case under `target`. Returns the number written."""
    written = 0
    for relative, contents in FILES.items():
        path = target / relative
        if path.exists() and path.read_text(encoding="utf-8") != contents and not force:
            print(f"refusing to overwrite an edited file: {path}", file=sys.stderr)
            return -1
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")
        written += 1
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        type=Path,
        default=DEFAULT_TARGET,
        help=f"where to write the cases (default: {DEFAULT_TARGET})",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite files that differ from the case rather than stopping",
    )
    args = parser.parse_args()

    written = write(args.target, force=args.force)
    if written < 0:
        print("nothing was written. Re-run with --force to discard those edits.", file=sys.stderr)
        return 1
    print(f"wrote {written} files to {args.target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
