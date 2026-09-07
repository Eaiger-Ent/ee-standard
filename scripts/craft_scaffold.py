#!/usr/bin/env -S uv run python
"""Materialise the Craft bench scaffolds — S3's `docs/craft/review.bench.md`.

**Why a script rather than a committed tree.** A scaffold is a *new repository*
of the shape the Craft profile is for: its own `pyproject.toml`, its own lint
configuration, and — once S3 reaches C2 and C5 — files that are deliberately
wrong. None of that can be tracked here.

- A nested `[tool.ruff]` is a second lint definition inside a repository whose
  central invariant is that there is one. Ruff resolves each file against the
  nearest config, so a tracked scaffold config would silently become the one
  `ruff check .` applies to part of this tree.
- Tracked Python that must *fail* a check cannot coexist with TYP-001 and
  LNT-001, which claim all first-party source and admit no exemption. The
  first attempt at a committed scaffold failed
  `test_h7_this_repository_declares_coverage_for_every_tracked_module` on
  exactly that, which is the check doing its job.

So the scaffolds are written into `temp/` — gitignored, the same place S1 put
its `llm-toolkit` clone — and what is committed is the means to recreate them
byte for byte. A measurement nobody can re-derive is a claim; a scaffold nobody
can rebuild is the same thing one directory down.

Run it:

    uv run python scripts/craft_scaffold.py

It writes nothing outside `temp/craft-bench/` and refuses to overwrite a file
that has been edited, so a scaffold somebody is mid-experiment on is safe.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TARGET = REPO_ROOT / "temp" / "craft-bench"

#: Every file of both scaffolds, keyed by its path under the target directory.
#: The contents are the scaffold — read them here rather than anywhere else.
FILES: dict[str, str] = {
    "python/pyproject.toml": """\
# The Python bench scaffold — a new repository of the shape the Craft profile is
# for, on its first day. It is written for `docs/craft/review.bench.md` and is
# not a sample of anything.
#
# No `[tool.ruff]` section, and there will not be one. The candidate default-on
# selection lives in a `ruff.toml` beside this file, written by
# `scripts/craft_profile.py`, so that the bench can vary the configuration
# without touching the code it is measuring. This file is the subject; that one
# is the instrument.

[project]
name = "ledger"
version = "0.1.0"
description = "The Python bench scaffold for the Craft profile"
requires-python = ">=3.14"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/ledger"]

[tool.pytest.ini_options]
testpaths = ["tests"]
# `src` layout with no install step. The alternative pytest's good practices
# recommend — install the package first — would put a second virtualenv and a
# second lockfile inside the repository that carries this scaffold, for no gain:
# nothing here is packaged and shipped, it is run in place by the bench.
pythonpath = ["src"]
""",
    "python/src/ledger/__init__.py": """\
\"\"\"A small ledger, standing in for the domain a new repository starts with.\"\"\"
""",
    "python/src/ledger/entries.py": """\
\"\"\"Reading and totalling ledger entries.\"\"\"

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path


class LedgerError(Exception):
    \"\"\"A ledger could not be read or does not hold together.\"\"\"


@dataclass(frozen=True)
class Entry:
    \"\"\"One line of the ledger.\"\"\"

    description: str
    amount: Decimal
    recorded_at: datetime


def parse_entry(raw: dict[str, str]) -> Entry:
    \"\"\"Build an entry from one decoded JSON object.\"\"\"
    try:
        return Entry(
            description=raw["description"],
            amount=Decimal(raw["amount"]),
            recorded_at=datetime.fromisoformat(raw["recorded_at"]),
        )
    except KeyError as missing:
        message = "entry is missing a required field"
        raise LedgerError(message) from missing


def read_entries(path: Path) -> list[Entry]:
    \"\"\"Read every entry from a JSON file, newest first.\"\"\"
    if not path.is_file():
        message = "no ledger at that path"
        raise LedgerError(message)
    decoded = json.loads(path.read_text(encoding="utf-8"))
    entries = [parse_entry(item) for item in decoded]
    return sorted(entries, key=lambda entry: entry.recorded_at, reverse=True)


def total(entries: list[Entry]) -> Decimal:
    \"\"\"Sum the entries, to the precision they were recorded at.\"\"\"
    return sum((entry.amount for entry in entries), start=Decimal(0))


def recorded_today(entries: list[Entry], *, now: datetime | None = None) -> list[Entry]:
    \"\"\"Return the entries recorded on the current UTC day.\"\"\"
    today = (now or datetime.now(UTC)).date()
    return [entry for entry in entries if entry.recorded_at.date() == today]
""",
    "python/tests/__init__.py": """\
\"\"\"Tests are a package, which is what INP001 asks for. C3 measured the
alternative: without this file every test file draws a finding, and pytest
collects and passes either way.
\"\"\"
""",
    "python/tests/test_entries.py": """\
\"\"\"The scaffold's tests. Small on purpose: this is a repository's first day.\"\"\"

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from ledger.entries import Entry, LedgerError, read_entries, recorded_today, total


def _entry(amount: str, *, day: int = 1) -> Entry:
    return Entry(
        description="coffee",
        amount=Decimal(amount),
        recorded_at=datetime(2026, 9, day, 9, 0, tzinfo=UTC),
    )


def test_total_sums_without_losing_precision() -> None:
    assert total([_entry("0.10"), _entry("0.20")]) == Decimal("0.30")


def test_read_entries_returns_the_newest_first(tmp_path: Path) -> None:
    path = tmp_path / "ledger.json"
    raw = [
        {
            "description": "tea",
            "amount": "1.00",
            "recorded_at": "2026-09-01T09:00:00+00:00",
        },
        {
            "description": "cake",
            "amount": "2.00",
            "recorded_at": "2026-09-02T09:00:00+00:00",
        },
    ]
    path.write_text(json.dumps(raw), encoding="utf-8")
    assert [entry.description for entry in read_entries(path)] == ["cake", "tea"]


def test_a_missing_ledger_is_a_ledger_error(tmp_path: Path) -> None:
    with pytest.raises(LedgerError, match="no ledger"):
        read_entries(tmp_path / "absent.json")


def test_recorded_today_reads_the_clock_it_is_given() -> None:
    entries = [_entry("1.00", day=1), _entry("2.00", day=2)]
    now = datetime(2026, 9, 2, 18, 0, tzinfo=UTC)
    recorded = recorded_today(entries, now=now)
    assert [entry.amount for entry in recorded] == [Decimal("2.00")]
""",
    "react/package.json": """\
{
  "name": "storefront",
  "private": true,
  "version": "0.1.0",
  "description": "The React bench scaffold — a new repository on its first day",
  "type": "module",
  "scripts": {
    "lint": "eslint .",
    "test": "vitest run",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "react": "19.2.8",
    "react-dom": "19.2.8"
  },
  "devDependencies": {
    "@eslint-react/eslint-plugin": "5.18.9",
    "@testing-library/jest-dom": "7.0.1",
    "@testing-library/react": "16.3.3",
    "@testing-library/user-event": "14.6.7",
    "@types/react": "19.2.18",
    "@types/react-dom": "19.2.7",
    "eslint": "9.39.5",
    "eslint-plugin-jsx-a11y": "6.10.2",
    "eslint-plugin-react": "7.37.5",
    "eslint-plugin-react-hooks": "7.1.1",
    "eslint-plugin-testing-library": "7.16.2",
    "globals": "17.12.0",
    "jsdom": "30.0.1",
    "typescript": "5.9.3",
    "typescript-eslint": "8.69.0",
    "vitest": "4.1.11"
  }
}
""",
    "react/tsconfig.json": """\
{
  "compilerOptions": {
    "target": "ES2023",
    "lib": ["ES2023", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "types": ["vitest/globals", "@testing-library/jest-dom"],
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "noFallthroughCasesInSwitch": true,
    "verbatimModuleSyntax": true,
    "skipLibCheck": true,
    "noEmit": true
  },
  "include": ["src", "eslint.config.js", "vitest.config.ts"]
}
""",
    "react/vitest.config.ts": """\
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/setup-tests.ts'],
  },
})
""",
    "react/src/setup-tests.ts": """\
import '@testing-library/jest-dom/vitest'
""",
    "react/src/lib/money.ts": """\
/** Formatting and totalling money, with no React in sight. */

export interface LineItem {
  readonly sku: string
  readonly title: string
  readonly pence: number
  readonly quantity: number
}

export function formatPence(pence: number, locale = 'en-GB'): string {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: 'GBP',
  }).format(pence / 100)
}

export function subtotal(items: readonly LineItem[]): number {
  return items.reduce((running, item) => running + item.pence * item.quantity, 0)
}
""",
    "react/src/components/BasketRow.tsx": """\
import type { LineItem } from '../lib/money'
import { formatPence } from '../lib/money'

interface BasketRowProps {
  readonly item: LineItem
  readonly onRemove: (sku: string) => void
}

export function BasketRow({ item, onRemove }: BasketRowProps) {
  return (
    <li className="basket-row">
      <span className="basket-row__title">{item.title}</span>
      <span className="basket-row__quantity">{item.quantity}</span>
      <span className="basket-row__price">{formatPence(item.pence * item.quantity)}</span>
      <button
        type="button"
        onClick={() => {
          onRemove(item.sku)
        }}
      >
        Remove {item.title}
      </button>
    </li>
  )
}
""",
    "react/src/components/Basket.tsx": """\
import { useMemo, useState } from 'react'

import type { LineItem } from '../lib/money'
import { formatPence, subtotal } from '../lib/money'
import { BasketRow } from './BasketRow'

interface BasketProps {
  readonly initialItems: readonly LineItem[]
}

export function Basket({ initialItems }: BasketProps) {
  const [items, setItems] = useState<readonly LineItem[]>(initialItems)

  // Derived during render rather than synchronised in an effect, which is the
  // property `react.no-derived-state-in-effect` asserts.
  const total = useMemo(() => subtotal(items), [items])

  function remove(sku: string): void {
    setItems((current) => current.filter((item) => item.sku !== sku))
  }

  if (items.length === 0) {
    return <p>Your basket is empty.</p>
  }

  return (
    <section aria-labelledby="basket-heading">
      <h2 id="basket-heading">Basket</h2>
      <ul>
        {items.map((item) => (
          <BasketRow key={item.sku} item={item} onRemove={remove} />
        ))}
      </ul>
      <p>
        Subtotal: <output>{formatPence(total)}</output>
      </p>
      <a href="/checkout" aria-label="Continue to checkout">
        Continue
      </a>
    </section>
  )
}
""",
    "react/src/components/Basket.test.tsx": """\
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import type { LineItem } from '../lib/money'
import { Basket } from './Basket'

const items: readonly LineItem[] = [
  { sku: 'tea-01', title: 'Loose leaf tea', pence: 450, quantity: 2 },
  { sku: 'pot-01', title: 'Teapot', pence: 1800, quantity: 1 },
]

it('totals the basket at the price a shopper would read', () => {
  render(<Basket initialItems={items} />)

  expect(screen.getByRole('status')).toHaveTextContent('£27.00')
})

it('drops a line when its remove button is pressed', async () => {
  const user = userEvent.setup()
  render(<Basket initialItems={items} />)

  await user.click(screen.getByRole('button', { name: 'Remove Teapot' }))

  expect(screen.queryByText('Teapot')).not.toBeInTheDocument()
  expect(screen.getByRole('status')).toHaveTextContent('£9.00')
})

it('says so when there is nothing in it', () => {
  render(<Basket initialItems={[]} />)

  expect(screen.getByText('Your basket is empty.')).toBeInTheDocument()
})
""",
}


def write(target: Path, *, force: bool = False) -> int:
    """Write every scaffold file under `target`. Returns the number written."""
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
        help=f"where to write the scaffolds (default: {DEFAULT_TARGET})",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite files that differ from the scaffold rather than stopping",
    )
    args = parser.parse_args()

    written = write(args.target, force=args.force)
    if written < 0:
        print("nothing was written. Re-run with --force to discard those edits.", file=sys.stderr)
        return 1
    print(f"wrote {written} files to {args.target}")
    print("python: cd python && uv run --isolated --no-project --with pytest python -m pytest")
    print("react:  cd react && npm install && npx tsc --noEmit && npx vitest run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
