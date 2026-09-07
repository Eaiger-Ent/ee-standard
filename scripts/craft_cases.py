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
    cd python && ruff check cases/preview                      # C8, expected to fire
    cd python && ruff check --config ruff.toml cases/preview    # C8, expected clean
    cd python && ruff check --config ruff.toml cases/probes     # C5, expected to fire
    cd python && ruff check --config src/ruff.toml cases/tests # C5, S101 unscoped
    cd react  && npx eslint src && npx tsc --noEmit
    cd react  && npx eslint --config probes.config.js probes   # C5, expected to fire
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
\"\"\"

from __future__ import annotations

import hashlib
import logging
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)


# --- signature: ANN, ARG, PLR0913, PLR0917, FBT, B006, B008, RUF012, UP ---
@dataclass(frozen=True)
class Settings:
    \"\"\"RUF012 wants a mutable class default to be annotated ClassVar; this is not.\"\"\"

    roots: tuple[Path, ...] = ()
    labels: list[str] = field(default_factory=list)


def resolve(root: Path, name: str, *, strict: bool = False) -> Path | None:
    \"\"\"Three parameters, all read, all annotated, no mutable or called default.

    `strict` is a boolean and is keyword-only, which is FBT's remedy and leaves
    PLR0917's positional count at two.
    \"\"\"
    candidate = root / name
    if candidate.is_file():
        return candidate
    if strict:
        return None
    return root


# --- exception handler: E722, BLE001, B904, S110, S112, SIM105 ---
class WitnessError(Exception):
    \"\"\"A domain error, so nothing has to raise a bare Exception.\"\"\"


def read(path: Path) -> str:
    \"\"\"Names what it catches, chains from it, and suppresses nothing silently.\"\"\"
    try:
        return path.read_text(encoding="utf-8")
    except OSError as failure:
        message = "could not read the witness"
        raise WitnessError(message) from failure


# --- binding: F841, PLW2901, PLW0603, B023 ---
def totals(rows: list[list[int]]) -> list[int]:
    \"\"\"No unused local, no rebound loop variable, no global, no captured closure.\"\"\"
    running: list[int] = []
    for row in rows:
        scaled = [value * 2 for value in row]
        running.append(sum(scaled))
    return running


# --- comprehension: C4xx, PERF401 ---
def names(rows: list[str]) -> set[str]:
    \"\"\"A set comprehension rather than a set() around a list comprehension.\"\"\"
    return {row.strip() for row in rows if row.strip()}


# --- logging call: G001-G004, LOG015 ---
def announce(count: int) -> None:
    \"\"\"Deferred %-formatting on a module logger, not the root and not an f-string.\"\"\"
    logger.info("counted %d rows", count)


# --- security-sensitive call: S105-S107, S311, S324, S501, S608 ---
def token() -> str:
    \"\"\"A cryptographic source, a strong hash, no literal secret.\"\"\"
    raw = secrets.token_bytes(32)
    return hashlib.sha256(raw).hexdigest()


def query(table: str) -> str:
    \"\"\"SQL is built here, and it is chosen from fixed statements rather than spliced.\"\"\"
    statements = {
        "entries": "SELECT id FROM entries WHERE recorded_at > ?",
        "totals": "SELECT id FROM totals WHERE recorded_at > ?",
    }
    try:
        return statements[table]
    except KeyError as unknown:
        message = "unknown table"
        raise WitnessError(message) from unknown


# --- body size: PLR0915, C901 ---
def stamped(when: datetime | None = None) -> str:
    \"\"\"Short and unbranching, so neither statement count nor complexity bites.\"\"\"
    return (when or datetime.now(UTC)).isoformat()
""",
    "python/cases/tests/__init__.py": """\
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
    \"\"\"The subject. Fixed statements, chosen rather than spliced.\"\"\"
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
    assert query(table) == expected


def test_an_unknown_table_is_a_witness_error() -> None:
    with pytest.raises(WitnessError, match="unknown table"):
        query("nowhere")


def test_the_two_statements_differ() -> None:
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
    "react/src/cases/Witness.tsx": """\
import { createContext, useCallback, useMemo, useState } from 'react'

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
}

export function Witness({ rows, onSave }: WitnessProps) {
  const [selected, setSelected] = useState<string | null>(null)

  // `use-memo` and `preserve-manual-memoization` both apply here, and
  // `exhaustive-deps` wants every reactive value listed. One dependency array
  // satisfies all three.
  const select = useCallback((id: string) => {
    setSelected(id)
  }, [])
  const value = useMemo<WitnessContext>(() => ({ selected, select }), [selected, select])

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
