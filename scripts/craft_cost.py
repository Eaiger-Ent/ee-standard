#!/usr/bin/env -S uv run python
"""What the Craft candidate configuration costs, and what it turns on — S3.

C7 asks what a finding costs to satisfy, per rule, **from the tools' own
metadata rather than from a run**. Ruff records `fix_availability` per rule;
ESLint plugins record `meta.fixable` and `meta.hasSuggestions`. This reads both
and prints the totals, so `docs/craft/review.bench.md` can carry a number that
somebody can re-derive instead of a number somebody typed.

`--against-default` answers a different question, for C2: **which React rules
does the profile enable, or escalate, against the plugin's own `recommended`?**
That is the checklist C2 has to demonstrate firing, and deriving it beats taking
it from a document — `assess.rules.md` names ten, and reading the resolved
configuration against each plugin's default gives three times as many.

It reports the versions it read. It deliberately **pins nothing**: the profile
does not yet pin its own tools in anything it materialises — that gap is S4's,
recorded in the bench — and a pin here would be a second copy of a version this
script has no authority over.

Run it against a materialised bench:

    uv run python scripts/craft_scaffold.py
    uv run python scripts/craft_profile.py
    uv run python scripts/craft_cost.py            # totals
    uv run python scripts/craft_cost.py --per-rule # every rule, one per line
    uv run python scripts/craft_cost.py --against-default  # C2's checklist
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tomllib
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TARGET = REPO_ROOT / "temp" / "craft-bench"

#: The three file kinds C1 resolves the React configuration for. Cost is read
#: over the union, because a rule scoped to tests still costs what it costs.
REACT_FILES = (
    "src/components/Basket.tsx",
    "src/lib/money.ts",
    "src/components/Basket.test.tsx",
)

#: Read every enabled rule's cost from the installed plugins. Runs in the React
#: target so that bare specifiers resolve against its `node_modules`.
NODE_AGAINST_DEFAULT = """
import fs from 'node:fs'
const files = process.argv.slice(1)
const sev = (v) => {
  const s = Array.isArray(v) ? v[0] : v
  return s === 2 || s === 'error' ? 2 : s === 1 || s === 'warn' ? 1 : 0
}
const packages = {
  '@eslint-react': ['@eslint-react/eslint-plugin', (p) => p.configs.recommended],
  '@typescript-eslint': ['typescript-eslint', (p) => p.configs.recommended],
  'jsx-a11y': ['eslint-plugin-jsx-a11y', (p) => p.flatConfigs.recommended],
  react: ['eslint-plugin-react', (p) => p.configs.flat?.recommended],
  'react-hooks': ['eslint-plugin-react-hooks', (p) => p.configs.recommended],
  'testing-library': [
    'eslint-plugin-testing-library',
    (p) => p.configs['flat/react'],
  ],
}
const defaults = new Map()
const absorb = (cfg) => {
  for (const [k, v] of Object.entries(cfg?.rules ?? {})) {
    defaults.set(k, Math.max(defaults.get(k) ?? 0, sev(v)))
  }
}
for (const [pkg, pick] of Object.values(packages)) {
  const plugin = (await import(pkg)).default
  const chosen = pick(plugin)
  for (const cfg of Array.isArray(chosen) ? chosen : [chosen]) absorb(cfg)
}
const rows = []
for (const f of files) {
  const cfg = JSON.parse(fs.readFileSync(f, 'utf8'))
  for (const [id, v] of Object.entries(cfg.rules)) {
    if (sev(v) === 0) continue
    const d = defaults.get(id)
    if (d === undefined || d === 0) rows.push({ id, why: 'off or absent by default' })
    else if (sev(v) > d) {
      rows.push({ id, why: `severity raised from ${d === 1 ? 'warn' : 'error'}` })
    }
  }
}
const seen = new Map()
for (const row of rows) if (!seen.has(row.id)) seen.set(row.id, row)
console.log(JSON.stringify([...seen.values()].sort((a, b) => a.id.localeCompare(b.id))))
"""

NODE_READ_COST = """
import fs from 'node:fs'
const files = process.argv.slice(1)
const on = (v) => {
  const s = Array.isArray(v) ? v[0] : v
  return s !== undefined && s !== 0 && s !== 'off'
}
const enabled = new Set()
for (const f of files) {
  const cfg = JSON.parse(fs.readFileSync(f, 'utf8'))
  for (const [k, v] of Object.entries(cfg.rules)) if (on(v)) enabled.add(k)
}
const namespaces = [...new Set([...enabled].map((id) => id.slice(0, id.lastIndexOf('/'))))]
const packages = {
  '@eslint-react': '@eslint-react/eslint-plugin',
  '@typescript-eslint': '@typescript-eslint/eslint-plugin',
  'jsx-a11y': 'eslint-plugin-jsx-a11y',
  react: 'eslint-plugin-react',
  'react-hooks': 'eslint-plugin-react-hooks',
  'testing-library': 'eslint-plugin-testing-library',
}
const plugins = {}
const versions = {}
for (const ns of namespaces) {
  const pkg = packages[ns]
  if (!pkg) continue
  plugins[ns] = (await import(pkg)).default
  versions[ns] = JSON.parse(
    fs.readFileSync(`node_modules/${pkg}/package.json`, 'utf8'),
  ).version
}
const rows = []
for (const id of [...enabled].sort()) {
  const i = id.lastIndexOf('/')
  const ns = id.slice(0, i)
  const meta = plugins[ns]?.rules?.[id.slice(i + 1)]?.meta ?? {}
  rows.push({
    id,
    plugin: ns,
    cost: meta.fixable ? 'fix' : meta.hasSuggestions ? 'suggestion' : 'none',
  })
}
console.log(JSON.stringify({ versions, rows }))
"""


def _run(command: list[str], *, cwd: Path) -> str:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print(f"failed: {' '.join(command)}\n{result.stderr}", file=sys.stderr)
        raise SystemExit(1)
    return result.stdout


def python_costs(target: Path) -> tuple[str, list[tuple[str, str, str]]]:
    """Every selected ruff rule as (code, linter, cost), with ruff's version."""
    root = target / "python"
    version = _run(["ruff", "--version"], cwd=root).strip()
    taxonomy = json.loads(_run(["ruff", "rule", "--all", "--output-format", "json"], cwd=root))
    rules = [rule for rule in taxonomy if rule.get("code")]

    selectors: list[str] = []
    configs = ((root / "ruff.toml", "select"), (root / "src" / "ruff.toml", "extend-select"))
    for config, key in configs:
        selectors += tomllib.loads(config.read_text(encoding="utf-8"))["lint"][key]

    def parts(code: str) -> tuple[str, str]:
        match = re.match(r"([A-Z]+)(\d*)", code)
        if match is None:  # pragma: no cover - every ruff code has this shape
            message = f"unreadable rule code: {code}"
            raise ValueError(message)
        return match.group(1), match.group(2)

    selected: dict[str, tuple[str, str, str]] = {}
    for selector in selectors:
        alpha, digits = parts(selector)
        for rule in rules:
            code_alpha, code_digits = parts(rule["code"])
            if code_alpha == alpha and code_digits.startswith(digits):
                available = rule["fix_availability"]
                cost = "none" if available == "None" else "fix"
                selected[rule["code"]] = (rule["code"], rule["linter"], cost)
    return version, sorted(selected.values())


def react_costs(target: Path) -> tuple[dict[str, str], list[tuple[str, str, str]]]:
    """Every enabled ESLint rule as (id, plugin, cost), with plugin versions."""
    root = target / "react"
    printed = []
    for index, source in enumerate(REACT_FILES):
        path = root / f".craft-cost-{index}.json"
        config = _run(["npx", "eslint", "--print-config", source], cwd=root)
        path.write_text(config, encoding="utf-8")
        printed.append(path.name)
    try:
        raw = _run(["node", "--input-type=module", "-e", NODE_READ_COST, "--", *printed], cwd=root)
    finally:
        for name in printed:
            (root / name).unlink(missing_ok=True)
    payload = json.loads(raw)
    rows = [(row["id"], row["plugin"], row["cost"]) for row in payload["rows"]]
    return payload["versions"], rows


def against_default(target: Path) -> list[tuple[str, str]]:
    """Every enabled React rule the plugin's own `recommended` does not, as (id, why)."""
    root = target / "react"
    printed = []
    for index, source in enumerate(REACT_FILES):
        path = root / f".craft-default-{index}.json"
        config = _run(["npx", "eslint", "--print-config", source], cwd=root)
        path.write_text(config, encoding="utf-8")
        printed.append(path.name)
    try:
        command = ["node", "--input-type=module", "-e", NODE_AGAINST_DEFAULT, "--", *printed]
        raw = _run(command, cwd=root)
    finally:
        for name in printed:
            (root / name).unlink(missing_ok=True)
    return [(row["id"], row["why"]) for row in json.loads(raw)]


def report(title: str, rows: list[tuple[str, str, str]]) -> None:
    counts = Counter(cost for _, _, cost in rows)
    total = len(rows)
    print(f"\n{title}: {total} rules")
    print(f"  a fix or suggestion   {total - counts['none']:>4}")
    print(f"  neither, hand-work    {counts['none']:>4}  ({round(100 * counts['none'] / total)}%)")
    per: defaultdict[str, list[int]] = defaultdict(lambda: [0, 0])
    for _, group, cost in rows:
        per[group][0] += 1
        per[group][1] += cost == "none"
    print("  by family, hand-work of total:")
    for group, (n, none) in sorted(per.items(), key=lambda item: (-item[1][1], item[0])):
        print(f"    {group:<28} {none:>3} of {n:>3}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--per-rule", action="store_true", help="print every rule and its cost")
    parser.add_argument(
        "--against-default",
        action="store_true",
        help="print C2's checklist instead: React rules enabled against a plugin default",
    )
    args = parser.parse_args()

    if args.against_default:
        rows = against_default(args.target)
        print(f"enabled against a plugin default: {len(rows)}")
        for name, why in rows:
            print(f"  {name}\t{why}")
        return 0

    ruff_version, python_rows = python_costs(args.target)
    plugin_versions, react_rows = react_costs(args.target)

    print(f"ruff: {ruff_version}")
    for name, version in sorted(plugin_versions.items()):
        print(f"{name}: {version}")
    report("Python", python_rows)
    report("React", react_rows)

    combined = python_rows + react_rows
    hand = sum(1 for _, _, cost in combined if cost == "none")
    print(
        f"\nBoth stacks: {len(combined)} rules, {hand} hand-work "
        f"({round(100 * hand / len(combined))}%)"
    )

    if args.per_rule:
        print("\nrule\tfamily\tcost")
        for name, group, cost in combined:
            print(f"{name}\t{group}\t{cost}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
