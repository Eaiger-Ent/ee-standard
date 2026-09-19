#!/usr/bin/env -S uv run python
"""What a Craft profile enables and what it costs, resolved from the register — S5.

`plan.md` § S5 requires the installer to present each applicable profile with
**what it turns on and what each rule costs to satisfy** before anybody says
yes. This is where those two numbers come from, and it reads the Craft register
rather than a document: `craft/*.yaml` is the source after the S4 migration, and
`docs/craft/assess.rules.md` is a stage record.

**Cost is read from the installed tool, not from a table.**
[`review.bench.md`](../docs/craft/review.bench.md) § What each rule costs — C7
measured it from ruff's own `fix_availability` and prints the version it read,
for the reason this script inherits: a 273-row table is stale the first time
either tool is bumped, and the chooser needs the answer for the version the
repository will actually run. `review.strict.md`'s correction comes with it —
what a tool *declares* is a **floor on cheapness** rather than an estimate, and
a rule whose finding survives its own `--fix` is declared fixable all the same.

**What it cannot read, it says.** React cost needs the six plugins resolved from
a `node_modules`, which this repository does not have and a repository at its
first install has not run yet. A profile whose cost could not be read is
reported as unread, with the reason, rather than as free.

`--against-bench` is the check the migration owes: the selection the register
resolves to, against the configuration S3 actually benched in
`scripts/craft_profile.py`. They are two descriptions of one decision, and the
register is only the source of truth if they agree.

Run it:

    uv run python scripts/craft_select.py                      # every profile
    uv run python scripts/craft_select.py --profile python/strict
    uv run python scripts/craft_select.py --per-rule
    uv run python scripts/craft_select.py --against-bench      # register vs S3
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CRAFT = REPO_ROOT / "craft"

#: A ruff rule's three words for whether it can fix what it finds. Passed
#: through rather than collapsed to a boolean, because `sometimes` is not a cost
#: a repository can plan around — `craft_cost.py` made the same choice.
FIX_WORDS = ("Always", "Sometimes", "None")


def load(name: str) -> dict[str, Any]:
    return yaml.safe_load((CRAFT / f"{name}.yaml").read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def properties() -> dict[str, dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for scope in ("python", "react", "any"):
        merged.update(load(scope)["properties"])
    return merged


def bound(stack: str, level: str, levels: list[str]) -> dict[str, dict[str, Any]]:
    """Every property this profile binds.

    A level is a superset of the one below it (ADR 0052), so `strict` takes the
    `standard` rows as well as its own. The scope is the stack's own file plus
    `any.`, whose rows join a profile when their evidence gate is open — none
    of them binds an instrument today, which `report` says out loud rather than
    leaving to be inferred from a zero.
    """
    ceiling = levels.index(level)
    return {
        identity: prop
        for identity, prop in properties().items()
        if identity.split(".", 1)[0] in {stack, "any"}
        and "instrument" in prop
        and prop.get("level") in levels[: ceiling + 1]
    }


def ruff_catalogue() -> tuple[str, dict[str, dict[str, Any]]]:
    """Every rule the installed ruff knows, by code, with the version that knows it."""
    version = subprocess.run(
        ["uv", "run", "ruff", "--version"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    rules = json.loads(
        subprocess.run(
            ["uv", "run", "ruff", "rule", "--all", "--output-format", "json"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    )
    # One rule in 0.16.5 — `pytest-fixture-autouse`, in preview since this
    # release — reports `"code": null`. A catalogue keyed on it would hold a
    # `None` key that every prefix comparison then trips over, which is how it
    # was found. A rule with no code cannot be selected, so it is not in the
    # catalogue.
    return version, {rule["code"]: rule for rule in rules if rule["code"]}


def codes_for(
    instrument: dict[str, Any], catalogue: dict[str, dict[str, Any]]
) -> tuple[list[str], list[str]]:
    """The codes an instrument selects, and the codes it names that ruff does not know.

    A `linter:` is expanded against the installed tool rather than against a
    range, which is the whole reason the schema spells it that way: `DTZ001` to
    `DTZ012` had already missed `DTZ901` when the register cited it, and an
    expansion asks the tool instead of asking a document from last month.
    """
    selected = list(instrument.get("codes", []))
    unknown = [code for code in selected if code not in catalogue]
    if linter := instrument.get("linter"):
        selected += [code for code, rule in catalogue.items() if rule["linter"] == linter]
        if not any(rule["linter"] == linter for rule in catalogue.values()):
            unknown.append(f"linter {linter}")
    return sorted(set(selected)), unknown


def resolve(profile: str, meta: dict[str, Any]) -> dict[str, Any]:
    """One profile, fully resolved: what it binds, what it selects, what that costs."""
    stack, _, level = profile.partition("/")
    rows = bound(stack, level, list(meta["levels"]))
    version, catalogue = ("", {}) if stack != "python" else ruff_catalogue()

    per_code: dict[str, str] = {}
    unknown: list[str] = []
    tools: Counter[str] = Counter()
    settings = 0
    rules: list[str] = []
    for identity, prop in rows.items():
        instrument = prop["instrument"]
        tools[instrument["tool"]] += 1
        settings += 1 if prop.get("settings") or instrument.get("setting") else 0
        rules += instrument.get("rules", [])
        if instrument["tool"] == "ruff":
            codes, missing = codes_for(instrument, catalogue)
            unknown += missing
            for code in codes:
                per_code[code] = identity
    return {
        "profile": profile,
        "stack": stack,
        "level": level,
        "properties": rows,
        "tools": tools,
        "settings": settings,
        "codes": per_code,
        "rules": sorted(set(rules)),
        "unknown": unknown,
        "tool_version": version,
        "catalogue": catalogue,
    }


def residue(stack: str) -> tuple[int, int]:
    """What the profile does not enforce: this stack's rows, and the neutral ones."""
    own = sum(
        1
        for identity, prop in properties().items()
        if identity.startswith(f"{stack}.") and "instrument" not in prop
    )
    neutral = sum(1 for identity in properties() if identity.startswith("any."))
    return own, neutral


def report(resolved: dict[str, Any], meta: dict[str, Any], *, per_rule: bool) -> None:
    profile = resolved["profile"]
    version = meta["profiles"][profile]["version"]
    print(f"\n{profile}@{version}")
    print(f"  {len(resolved['properties'])} properties bound", end="")
    print("".join(f", {count} by {tool}" for tool, count in sorted(resolved["tools"].items())))

    if resolved["stack"] == "python":
        catalogue = resolved["catalogue"]
        costs = Counter(catalogue[code]["fix_availability"] for code in resolved["codes"])
        preview = [code for code in resolved["codes"] if catalogue[code]["preview"]]
        total = sum(costs.values())
        hand = costs["None"]
        print(f"  {total} ruff rules, read from {resolved['tool_version']}")
        for word in FIX_WORDS:
            print(f"    fix {word.lower():<9} {costs[word]:>4}")
        share = f"{hand / total:.0%}" if total else "n/a"
        print(f"  hand-work: {hand} of {total} ({share}) declare no fix")
        if preview:
            print(f"  preview rules, which a ruff release may move: {', '.join(sorted(preview))}")
        if resolved["unknown"]:
            print(f"  NOT KNOWN to this ruff: {', '.join(sorted(resolved['unknown']))}")
    else:
        print(f"  {len(resolved['rules'])} eslint rules, across {len(_plugins(resolved))} plugins")
        for plugin, count in sorted(_plugins(resolved).items()):
            print(f"    {plugin:<20} {count:>4}")
        print("  cost: UNREAD — needs the six plugins resolved from a node_modules.")
        print("        The installer reads it from the tree it is installing into;")
        print("        review.bench.md § What each rule costs is what a bench read.")

    if resolved["settings"]:
        print(f"  {resolved['settings']} properties carry a threshold or a tool setting")
    own, neutral = residue(resolved["stack"])
    print(f"  residue: {own} {resolved['stack']}. properties with no instrument, and")
    print(f"           {neutral} any. properties — the stack-neutral scope binds nothing")
    print("           at any level, because nothing stack-neutral has been measured")

    if per_rule:
        catalogue = resolved["catalogue"]
        for code, identity in sorted(resolved["codes"].items()):
            fix = catalogue[code]["fix_availability"].lower()
            print(f"    {code:<10} fix {fix:<9} {identity}")
        for rule in resolved["rules"]:
            print(f"    {rule:<40} cost unread")


def _plugins(resolved: dict[str, Any]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for rule in resolved["rules"]:
        counts[rule.rsplit("/", 1)[0] if "/" in rule else "(core)"] += 1
    return dict(counts)


def _expand(selector: str, catalogue: dict[str, dict[str, Any]]) -> set[str]:
    """A ruff selector's codes, resolved the way ruff resolves one.

    Not a textual prefix match, which is the shape this started as and got
    wrong: `N` is pep8-naming, and `"NPY001".startswith("N")` is true. A
    selector that *is* a linter's own prefix selects that linter and no other,
    so the linter prefixes are derived from the catalogue — the longest common
    prefix of each linter's codes — and an exact match wins before the textual
    fallback that serves `ANN2` and `S1`.
    """
    prefixes: dict[str, str] = {}
    for code, rule in catalogue.items():
        linter = rule["linter"]
        known = prefixes.get(linter)
        if known is None:
            prefixes[linter] = code
            continue
        while not code.startswith(prefixes[linter]):
            prefixes[linter] = prefixes[linter][:-1]
    for linter, prefix in prefixes.items():
        if prefix == selector:
            return {code for code, rule in catalogue.items() if rule["linter"] == linter}
    return {code for code in catalogue if code.startswith(selector)}


def against_bench(meta: dict[str, Any]) -> int:
    """The register's selection against the configuration S3 benched.

    Two descriptions of one decision. The bench's were written by hand from the
    resolved rows of `assess.rules.md`; the register's were migrated from the
    same rows by a different pass. Agreement is what makes the register the
    source rather than the second copy, and this is the only thing that checks
    it — `tests/test_craft_register.py`'s superset test holds the register to
    the *document*, not to the configuration anybody ran.

    Both of the bench's files are read per level. The profile writes two configs
    for one property — `S101` is scoped to the package source, which ruff can
    only express as a nested configuration — so a comparison reading the root
    file alone reports a disagreement that is really a second file.
    """
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    # Imported here rather than at the top: this is the only mode that reads
    # S3's bench configuration, and `scripts/` is not a package.
    from craft_profile import FILES, STRICT_FILES

    _, catalogue = ruff_catalogue()
    sources = {
        "standard": (FILES["python/ruff.toml"], FILES["python/src/ruff.toml"]),
        "strict": (STRICT_FILES["python/strict.toml"], STRICT_FILES["python/src/strict.toml"]),
    }
    problems = 0
    for level, files in sources.items():
        resolved = resolve(f"python/{level}", meta)
        benched: set[str] = set()
        for source in files:
            for body in re.findall(r"(?:extend-)?select = \[(.*?)\]", source, re.S):
                benched |= set(body.split('"')[1::2])
        expanded: set[str] = set()
        for selector in benched:
            expanded |= _expand(selector, catalogue)
        register = set(resolved["codes"])
        if level == "strict":
            register -= set(resolve("python/standard", meta)["codes"])
            expanded -= {
                code
                for selector in _benched_selectors(FILES)
                for code in _expand(selector, catalogue)
            }
        problems += _disagreements(f"python/{level}", benched=expanded, register=register)

    problems += _react_against_bench(meta, FILES, STRICT_FILES)
    print(f"\n{problems} disagreements between the register and the benched configuration")
    return 1 if problems else 0


def _disagreements(profile: str, *, benched: set[str], register: set[str]) -> int:
    for missing in sorted(benched - register):
        print(f"  {profile}: benched, not in the register — {missing}")
    for added in sorted(register - benched):
        print(f"  {profile}: in the register, not benched — {added}")
    return len(benched ^ register)


#: A rule in a flat config, in both spellings: `'id': 'error'` and the options
#: form `'id': ['error', {...}]`. Reading only the first form reports two
#: disagreements that are really two rules carrying options — which is how the
#: React half of this comparison first ran.
FLAT_RULE = re.compile(r"""'([@a-z][@a-z0-9/._-]*/[a-z0-9-]+)'\s*:\s*(?:'(?:error|warn)'|\[)""")


def _react_against_bench(
    meta: dict[str, Any], files: dict[str, str], strict_files: dict[str, str]
) -> int:
    """The same check for React, where the configuration is a flat config.

    The bench writes `strict` as a file that spreads `standard` and adds to it,
    so the register's strict-only rules are compared against the additions
    rather than against the whole.
    """
    standard = set(FLAT_RULE.findall(files["react/eslint.config.js"]))
    added = set(FLAT_RULE.findall(strict_files["react/strict.config.js"])) - standard
    problems = _disagreements(
        "react/standard", benched=standard, register=set(resolve("react/standard", meta)["rules"])
    )
    register_added = set(resolve("react/strict", meta)["rules"]) - set(
        resolve("react/standard", meta)["rules"]
    )
    return problems + _disagreements("react/strict", benched=added, register=register_added)


def _benched_selectors(files: dict[str, str]) -> set[str]:
    """Every selector a level's files name, so the level above can subtract them."""
    found: set[str] = set()
    for name, source in files.items():
        if not name.startswith("python/"):
            continue
        for body in re.findall(r"(?:extend-)?select = \[(.*?)\]", source, re.S):
            found |= set(body.split('"')[1::2])
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", help="one profile, e.g. python/strict")
    parser.add_argument("--per-rule", action="store_true", help="every rule and its cost")
    parser.add_argument(
        "--against-bench",
        action="store_true",
        help="compare the register's Python selection with the configuration S3 benched",
    )
    args = parser.parse_args()

    meta = load("meta")
    if args.against_bench:
        return against_bench(meta)

    names = [args.profile] if args.profile else sorted(meta["profiles"])
    for name in names:
        if name not in meta["profiles"]:
            parser.error(f"{name} is not a profile the register defines")
        report(resolve(name, meta), meta, per_rule=args.per_rule)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
