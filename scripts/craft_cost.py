#!/usr/bin/env -S uv run python
"""What the Craft candidate configuration costs, and what it turns on — S3.

C7 asks what a finding costs to satisfy, per rule, **from the tools' own
metadata rather than from a run**. Ruff records `fix_availability` per rule and this passes its
three words through — `always`, `sometimes`, `none` — because a fix that only
sometimes applies is not a cost a repository can plan around; ESLint plugins
record `meta.fixable` and `meta.hasSuggestions`, reported as `fix` and
`suggestion`. This reads both
and prints the totals, so `docs/craft/review.bench.md` can carry a number that
somebody can re-derive instead of a number somebody typed.

`--against-default` answers a different question, for C2: **which React rules
does the profile enable, or escalate, against the plugin's own `recommended`?**
That is the checklist C2 has to demonstrate firing, and deriving it beats taking
it from a document — `assess.rules.md` names ten, and reading the resolved
configuration against each plugin's default gives three times as many.

`--fires` answers C2's per-rule half at `strict`: **did every rule the level adds
report on a case written for it?** The additions are derived by resolving the
strict selection against the standard one rather than typed out, the findings
come from a run over `cases/strict/`, and the two sets are compared — so a rule
that has quietly stopped firing shows up as a missing rule rather than as a run
that still looks busy. It exits non-zero when one is missing. The mode needs a
level with one below it, which `standard` has not.

`--level` chooses the strictness level to read, and `--added` narrows the
report to the rules that level adds against the level below — C7 at `strict`,
where the interesting number is not what 168 rules cost but what the 27 the
level *adds* cost, since a repository at `standard` has already paid for the
rest. The additions are derived the same way `--fires` derives them, so the two
modes cannot disagree about what the level added.

`--fix-applies` checks all of that against a run, which C7 was defined as not
needing and which is exactly why nobody had checked it: it lints the violation
cases, applies `--fix`, lints again and restores the files, so a rule whose
finding survives its own fix is reported. Ruff gets two passes because
`fix_availability` and a diagnostic's *applicability* are different axes, and
`--fix` alone declines an unsafe fix however strong the taxonomy's word for it.

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
    uv run python scripts/craft_cost.py --fires            # C2 per rule, at strict
    uv run python scripts/craft_cost.py --level strict     # the whole level
    uv run python scripts/craft_cost.py --level strict --added   # C7's delta
    uv run python scripts/craft_cost.py --level strict --fix-applies  # C7, run
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


def _run(command: list[str], *, cwd: Path, expect_findings: bool = False) -> str:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    # A linter asked for violations exits non-zero when it finds them, which is
    # the whole point of the run rather than a failure of it.
    if result.returncode != 0 and not (expect_findings and result.stdout.strip()):
        print(f"failed: {' '.join(command)}\n{result.stderr}", file=sys.stderr)
        raise SystemExit(1)
    return result.stdout


#: Which ruff config files carry a level's selection, and under which key. The
#: `strict` pair *extends* the `standard` one, so both have to be read to
#: resolve it — which is the same statement the profile makes, read back.
PYTHON_LEVELS = {
    "standard": (("ruff.toml", "select"), ("src/ruff.toml", "extend-select")),
    "strict": (
        ("ruff.toml", "select"),
        ("src/ruff.toml", "extend-select"),
        ("strict.toml", "extend-select"),
        ("src/strict.toml", "extend-select"),
    ),
}

#: Which level each level extends. `standard` is the first and has no below,
#: so the delta modes reject it rather than reporting every rule as added.
LEVEL_BELOW = {"strict": "standard"}

#: Where C2's per-rule cases live at `strict`. `cases/preview/control.py` is in
#: the list because the two preview rules keep the cases C8 wrote for them.
STRICT_CASES = ("cases/strict", "cases/preview/control.py")

#: The violation cases per level, and the configuration that reads them. These
#: are what `--fix-applies` runs `--fix` over: a rule with no case cannot be
#: measured, which is the mode's stated limit rather than a silent gap.
PYTHON_CASES = {"standard": ("cases/violations",), "strict": STRICT_CASES}
PYTHON_CONFIG = {"standard": "ruff.toml", "strict": "strict.toml"}
REACT_VIOLATION_CONFIG = {
    "standard": "violations.config.js",
    "strict": "strict-violations.config.js",
}


def _parts(code: str) -> tuple[str, str]:
    match = re.match(r"([A-Z]+)(\d*)", code)
    if match is None:  # pragma: no cover - every ruff code has this shape
        message = f"unreadable rule code: {code}"
        raise ValueError(message)
    return match.group(1), match.group(2)


def _resolve(root: Path, level: str) -> dict[str, tuple[str, str, str]]:
    """Resolve a level's selectors to (code, linter, cost), keyed by code."""
    taxonomy = json.loads(_run(["ruff", "rule", "--all", "--output-format", "json"], cwd=root))
    rules = [rule for rule in taxonomy if rule.get("code")]

    selectors: list[str] = []
    for name, key in PYTHON_LEVELS[level]:
        selectors += tomllib.loads((root / name).read_text(encoding="utf-8"))["lint"][key]

    selected: dict[str, tuple[str, str, str]] = {}
    for selector in selectors:
        alpha, digits = _parts(selector)
        for rule in rules:
            code_alpha, code_digits = _parts(rule["code"])
            if code_alpha == alpha and code_digits.startswith(digits):
                # ruff's own three words, lowercased, rather than a collapse to
                # fix/none: `Sometimes` means the fix does not always apply, and
                # a cost question cannot count it as a fix.
                cost = rule["fix_availability"].lower()
                selected[rule["code"]] = (rule["code"], rule["linter"], cost)
    return selected


def _react_config(level: str) -> list[str]:
    """The `--config` flag a level needs, if any. `standard` is `eslint.config.js`."""
    return [] if level == "standard" else ["--config", f"{level}.config.js"]


def python_costs(target: Path, level: str = "standard") -> tuple[str, list[tuple[str, str, str]]]:
    """Every selected ruff rule as (code, linter, cost), with ruff's version."""
    root = target / "python"
    version = _run(["ruff", "--version"], cwd=root).strip()
    return version, sorted(_resolve(root, level).values())


def react_costs(
    target: Path, level: str = "standard"
) -> tuple[dict[str, str], list[tuple[str, str, str]]]:
    """Every enabled ESLint rule as (id, plugin, cost), with plugin versions."""
    root = target / "react"
    flag = _react_config(level)
    printed = []
    for index, source in enumerate(REACT_FILES):
        path = root / f".craft-cost-{index}.json"
        config = _run(["npx", "eslint", *flag, "--print-config", source], cwd=root)
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


def python_fires(target: Path) -> tuple[list[str], list[str]]:
    """The rules `strict` adds, split into those that fired on a case and those that did not."""
    root = target / "python"
    added = sorted(set(_resolve(root, "strict")) - set(_resolve(root, "standard")))
    command = [
        "ruff",
        "check",
        "--config",
        "strict.toml",
        "--output-format",
        "json",
        *STRICT_CASES,
    ]
    raw = _run(command, cwd=root, expect_findings=True)
    fired = {finding["code"] for finding in json.loads(raw)}
    return [code for code in added if code in fired], [code for code in added if code not in fired]


def react_fires(target: Path) -> tuple[list[str], list[str]]:
    """The same question for React, where `strict` adds one rule."""
    root = target / "react"
    standard = _run(["npx", "eslint", "--print-config", REACT_FILES[0]], cwd=root)
    strict = _run(
        ["npx", "eslint", *_react_config("strict"), "--print-config", REACT_FILES[0]],
        cwd=root,
    )

    def enabled(config: str) -> set[str]:
        rules = json.loads(config)["rules"].items()
        severities = {name: v[0] if isinstance(v, list) else v for name, v in rules}
        return {name for name, severity in severities.items() if severity not in (0, "off")}

    before, after = enabled(standard), enabled(strict)
    added = sorted(after - before)

    command = [
        "npx",
        "eslint",
        "--config",
        "strict-violations.config.js",
        "--format",
        "json",
        "violations",
    ]
    raw = _run(command, cwd=root, expect_findings=True)
    fired = {message["ruleId"] for report in json.loads(raw) for message in report["messages"]}
    return [name for name in added if name in fired], [name for name in added if name not in fired]


def added_costs(
    target: Path, level: str
) -> tuple[list[tuple[str, str, str]], list[tuple[str, str, str]]]:
    """What the rules `level` adds cost, per stack, against the level below."""
    below = LEVEL_BELOW[level]
    root = target / "python"
    above = _resolve(root, level)
    added = sorted(set(above) - set(_resolve(root, below)))
    python_rows = [above[code] for code in added]

    _, after = react_costs(target, level)
    _, before = react_costs(target, below)
    known = {row[0] for row in before}
    react_rows = [row for row in after if row[0] not in known]
    return python_rows, react_rows


def _snapshot(root: Path, paths: tuple[str, ...]) -> dict[Path, str]:
    """Every file under `paths`, so an in-place `--fix` can be undone."""
    saved: dict[Path, str] = {}
    for name in paths:
        where = root / name
        files = [where] if where.is_file() else sorted(p for p in where.rglob("*") if p.is_file())
        for path in files:
            saved[path] = path.read_text(encoding="utf-8")
    return saved


def _restore(saved: dict[Path, str]) -> None:
    for path, text in saved.items():
        path.write_text(text, encoding="utf-8")


def python_fix_applies(target: Path, level: str) -> list[tuple[str, str, int, int, int]]:
    """Per fired rule: (code, declared cost, removed by `--fix`, removed allowing unsafe, before).

    Two passes rather than one, because ruff's `fix_availability` and its fix
    *applicability* are different axes: a rule can say `always` and still mark
    the fix unsafe, which `--fix` alone declines to apply.
    """
    root = target / "python"
    paths = PYTHON_CASES[level]
    config = PYTHON_CONFIG[level]
    declared = _resolve(root, level)
    fix = ["ruff", "check", "--config", config, "--fix", *paths]

    def fired() -> Counter[str]:
        command = ["ruff", "check", "--config", config, "--output-format", "json", *paths]
        raw = _run(command, cwd=root, expect_findings=True)
        return Counter(finding["code"] for finding in json.loads(raw))

    before = fired()
    saved = _snapshot(root, paths)
    try:
        _run(fix, cwd=root, expect_findings=True)
        safe = fired()
        _restore(saved)
        _run([*fix, "--unsafe-fixes"], cwd=root, expect_findings=True)
        unsafe = fired()
    finally:
        _restore(saved)
    return [
        (
            code,
            declared[code][2] if code in declared else "?",
            count - safe.get(code, 0),
            count - unsafe.get(code, 0),
            count,
        )
        for code, count in sorted(before.items())
    ]


def react_fix_applies(target: Path, level: str) -> list[tuple[str, str, int, int, int]]:
    """The same question for ESLint, whose plugins declare `fixable` far more freely."""
    root = target / "react"
    config = REACT_VIOLATION_CONFIG[level]
    _, costs = react_costs(target, level)
    declared = {row[0]: row[2] for row in costs}

    def fired() -> Counter[str]:
        command = ["npx", "eslint", "--config", config, "--format", "json", "violations"]
        raw = _run(command, cwd=root, expect_findings=True)
        return Counter(
            message["ruleId"]
            for report_ in json.loads(raw)
            for message in report_["messages"]
            if message["ruleId"]
        )

    before = fired()
    saved = _snapshot(root, ("violations",))
    try:
        command = ["npx", "eslint", "--config", config, "--fix", "violations"]
        _run(command, cwd=root, expect_findings=True)
        after = fired()
    finally:
        _restore(saved)
    # ESLint has no safe/unsafe axis, so the two removal columns are the same
    # number by construction rather than by measurement.
    rows = []
    for name, count in sorted(before.items()):
        removed = count - after.get(name, 0)
        rows.append((name, declared.get(name, "?"), removed, removed, count))
    return rows


def report_applies(title: str, rows: list[tuple[str, str, int, int, int]]) -> int:
    """Print the run, and return how many rules declared a fix and applied none."""
    print(f"\n{title}: {len(rows)} rules fired on the cases")
    claimed = [row for row in rows if row[1] not in ("none", "?")]
    applied = [row for row in claimed if row[2] > 0]
    unsafe_only = [row for row in claimed if row[2] == 0 and row[3] > 0]
    empty = [row for row in claimed if row[3] == 0]
    print(f"  declared a fix or suggestion  {len(claimed):>4}")
    print(f"    a default run removed it    {len(applied):>4}")
    print(f"    only with --unsafe-fixes    {len(unsafe_only):>4}")
    for name, cost, _, _, _ in unsafe_only:
        print(f"      {name:<44} {cost}")
    print(f"    removed nothing             {len(empty):>4}")
    for name, cost, _, _, count in empty:
        print(f"      {name:<44} {cost:<11} {count} finding(s) survived")
    surprises = [row for row in rows if row[1] == "none" and row[3] > 0]
    for name, _, _, removed, _ in surprises:
        print(f"  declared no fix and removed {removed}: {name}")
    return len(empty)


def report(title: str, rows: list[tuple[str, str, str]]) -> None:
    if not rows:
        print(f"\n{title}: none")
        return
    counts = Counter(cost for _, _, cost in rows)
    total = len(rows)
    print(f"\n{title}: {total} rules")
    print(f"  a fix or suggestion   {total - counts['none']:>4}")
    for value, count in sorted(counts.items()):
        if value != "none":
            print(f"    {value:<20}{count:>4}")
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
        "--level",
        default="standard",
        choices=sorted(PYTHON_LEVELS),
        help="which strictness level to read",
    )
    parser.add_argument(
        "--fix-applies",
        action="store_true",
        help="check the declared cost against a run: does --fix remove what the metadata claims?",
    )
    parser.add_argument(
        "--added",
        action="store_true",
        help="C7 above the first level: cost of the rules this level adds, not of all of them",
    )
    parser.add_argument(
        "--against-default",
        action="store_true",
        help="print C2's checklist instead: React rules enabled against a plugin default",
    )
    parser.add_argument(
        "--fires",
        action="store_true",
        help="C2 per rule at strict: did every rule the level adds report on a case?",
    )
    args = parser.parse_args()

    if args.fires:
        missing = 0
        for stack, (fired, silent) in (
            ("Python", python_fires(args.target)),
            ("React", react_fires(args.target)),
        ):
            print(f"\n{stack}: {len(fired) + len(silent)} rules added at strict")
            print(f"  fired on a case  {len(fired):>4}")
            print(f"  silent           {len(silent):>4}")
            for name in silent:
                print(f"    {name}")
            missing += len(silent)
        if missing:
            print(f"\n{missing} added rules never fired.", file=sys.stderr)
            return 1
        return 0

    if args.fix_applies:
        empty = 0
        for stack, measured in (
            ("Python", python_fix_applies(args.target, args.level)),
            ("React", react_fix_applies(args.target, args.level)),
        ):
            empty += report_applies(f"{stack}, at {args.level}", measured)
        print(f"\n{empty} rules declare a fix and applied none.")
        return 0

    if args.added:
        if args.level not in LEVEL_BELOW:
            message = f"--added needs a level with one below it; {args.level} has none"
            print(message, file=sys.stderr)
            return 2
        python_rows, react_rows = added_costs(args.target, args.level)
        report(f"Python, added at {args.level}", python_rows)
        report(f"React, added at {args.level}", react_rows)
        if args.per_rule:
            print("\nrule\tfamily\tcost")
            for name, group, cost in python_rows + react_rows:
                print(f"{name}\t{group}\t{cost}")
        return 0

    if args.against_default:
        rows = against_default(args.target)
        print(f"enabled against a plugin default: {len(rows)}")
        for name, why in rows:
            print(f"  {name}\t{why}")
        return 0

    ruff_version, python_rows = python_costs(args.target, args.level)
    plugin_versions, react_rows = react_costs(args.target, args.level)

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
