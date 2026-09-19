#!/usr/bin/env -S uv run python
"""A Craft profile's configuration, rendered from the register — S5's writer.

`scripts/craft_select.py` answers *what does this profile turn on*. This answers
*what goes in the file*, for the Python stack: the `[tool.ruff]` region an
installer writes into `pyproject.toml`, the nested `src/ruff.toml` that two
source-scoped properties need, and at `strict` the one `[tool.mypy]` key ADR
0055 permits.

**Nothing here chooses where the configuration lives.** `controls.yaml`'s
`stacks:` block names the ordered locations per stack and
`docs/craft/design.profiles.md` § The config surface takes the first of them, so
what this renders is a region and what an installer does is place it.

**The region is delimited, and the delimiters are the discipline.** ADR 0055
left S5 to build the rule that stops two writers clobbering each other. The
region markers make Craft's write identifiable, re-writable and — with the stamp
ADR 0055 rule 2 requires at its head — attributable at a failing build.
`docs/craft/build.installer.md` § What the installer writes is the reasoning.

**Two things are asked of the installed ruff rather than carried in a table.**
Where a setting lives (`max-statements` is `lint.pylint`'s, `max-complexity` is
`lint.mccabe`'s) is read from `ruff config`, which enumerates its own option
tree; and whether the four linter selectors this profile uses are preview-free
is read from the catalogue, because `preview = true` against a linter selector
picks up preview rules wholesale where against an exact code it picks up
nothing. Both would otherwise be a dictionary of ruff knowledge inside Craft,
which is the shape ADR 0018 exists to refuse.

Run it:

    uv run python scripts/craft_render.py --profile python/standard
    uv run python scripts/craft_render.py --profile python/strict --file src
"""

from __future__ import annotations

import argparse
import json
import subprocess
from functools import cache
from pathlib import Path
from typing import Any

from craft_select import REPO_ROOT, load, resolve, ruff_catalogue

#: What opens and closes a region Craft owns. An installer rewrites between
#: them and touches nothing outside, which is the whole of the merge discipline
#: ADR 0055 handed S5.
OPEN = "# >>> ee-craft"
CLOSE = "# <<< ee-craft"


@cache
def _option_paths() -> tuple[str, ...]:
    """Every option the installed ruff has, fully qualified.

    `ruff config --output-format json` answers in one call and keys itself by
    the path a configuration file spells — `lint.pylint.max-statements`. The
    text form does not: asking it about a leaf prints that option's prose, so
    walking it section by section runs a description into the next command.
    """
    listed = subprocess.run(
        ["uv", "run", "ruff", "config", "--output-format", "json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return tuple(json.loads(listed))


def table_of(setting: str) -> str:
    """Where ruff keeps `setting`, asked of ruff rather than remembered.

    A table here would be a copy of the tool's own layout, stale the first
    release that moves an option — and ADR 0018's test sends tool knowledge the
    tool can be asked for back to the tool. Ambiguity fails loudly: a name in
    two sections is a rendering nobody could predict.
    """
    found = [path.rpartition(".")[0] for path in _option_paths() if path.split(".")[-1] == setting]
    if len(found) != 1:
        raise SystemExit(f"{setting}: ruff lists it at {found or 'nowhere'}")
    return found[0]


def _value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return f'"{value}"'
    if isinstance(value, list):
        return "[" + ", ".join(_value(item) for item in value) + "]"
    return str(value)


def stamp(profile: str, meta: dict[str, Any]) -> str:
    """ADR 0055 rule 2's record, in the shape `design.profiles.md` specifies.

    The gate half is honest rather than decorative: no stack-neutral property
    binds an instrument at any level, so there is no group for a predicate to
    switch on, and saying `none` with the reason beats printing predicates
    nothing would have consulted.
    """
    version = meta["profiles"][profile]["version"]
    return (
        f"# ee-craft: {profile}@{version}  gates: none "
        "(no any. property binds an instrument)  "
        f"craft-contract: {meta['craft_contract']}"
    )


def _select_lines(resolved: dict[str, Any], scope: str | None) -> list[str]:
    """One line per property, its codes then its identity.

    Grouped by property rather than sorted by code, because the comment is the
    answer to *whose rule is this* and a reader at a failing build has the code,
    not the identity.
    """
    lines = []
    for identity, prop in sorted(resolved["properties"].items()):
        if prop.get("scope") != scope:
            continue
        instrument = prop["instrument"]
        if instrument["tool"] != "ruff":
            continue
        selectors = [*instrument.get("codes", [])]
        if linter := instrument.get("linter"):
            selectors.append(_linter_selector(linter))
        if not selectors:
            continue
        spelled = ", ".join(f'"{selector}"' for selector in sorted(selectors))
        lines.append(f"  {spelled},")
        lines[-1] = f"{lines[-1]:<52}# {identity}"
    return lines


@cache
def _linter_prefixes() -> dict[str, str]:
    """Each linter's own selector, derived from the codes the catalogue carries."""
    _, catalogue = ruff_catalogue()
    prefixes: dict[str, str] = {}
    for code, rule in catalogue.items():
        linter = rule["linter"]
        if linter not in prefixes:
            prefixes[linter] = code
            continue
        while not code.startswith(prefixes[linter]):
            prefixes[linter] = prefixes[linter][:-1]
    return prefixes


def _linter_selector(linter: str) -> str:
    selector = _linter_prefixes().get(linter)
    if selector is None:
        raise SystemExit(f"{linter}: the installed ruff has no rules from it")
    return selector


def preview_risk(resolved: dict[str, Any]) -> list[str]:
    """Linters this profile selects wholesale that carry a preview rule.

    C8 measured that `preview = true` costs nothing *for a selection spelled in
    exact codes*. This profile is not spelled only in codes — four instruments
    are `linter:` selectors — so the same switch would pick up whatever preview
    rules those linters hold. They hold none at ruff 0.16.5, which is a fact
    about a version rather than a property of the design, so it is checked at
    render time instead of trusted.
    """
    _, catalogue = ruff_catalogue()
    selected = {
        prop["instrument"]["linter"]
        for prop in resolved["properties"].values()
        if prop["instrument"].get("linter")
    }
    return sorted(
        {
            rule["linter"]
            for rule in catalogue.values()
            if rule["linter"] in selected and rule["preview"]
        }
    )


def _commented(statement: str, identity: str) -> str:
    """A key and the property it exists for, one column apart at least."""
    return f"{statement:<{max(len(statement) + 1, 52)}}# {identity}"


def contributions(profile: str, meta: dict[str, Any]) -> list[tuple[str, list[str]]]:
    """What the profile contributes, as (table, lines) pairs.

    **A contribution is a span of lines, not a table**, and that is the whole of
    the merge discipline ADR 0055 handed S5. Two writers to one TOML file cannot
    each own a table header: a second `[tool.mypy]` is not a merge, it is an
    invalid document, and TYP-001 already requires that table to exist. So Craft
    renders the lines it owns and an installer places them — inside the table if
    it is there, with the header if it is not.
    """
    resolved = resolve(profile, meta)
    catalogue = resolved["catalogue"]
    preview = sorted(code for code in resolved["codes"] if catalogue[code]["preview"])
    tables: dict[str, list[str]] = {}

    for identity, prop in sorted(resolved["properties"].items()):
        for setting, value in (prop.get("settings") or {}).items():
            table = table_of(setting)
            tables.setdefault(table, []).append(
                _commented(f"{setting} = {_value(value)}", identity)
            )
    if preview:
        if risky := preview_risk(resolved):
            raise SystemExit(
                f"{profile} selects {', '.join(risky)} wholesale and needs "
                "preview = true: a preview rule in either would be enabled unasked"
            )
        tables.setdefault("", []).append(
            _commented("preview = true", ", ".join(preview))
        )

    tables.setdefault("lint", [])
    tables["lint"] = ["select = [", *_select_lines(resolved, None), "]", *tables["lint"]]

    ordered = [(table, lines) for table, lines in sorted(tables.items()) if lines]
    if mypy := _mypy(resolved):
        ordered.append(("mypy", mypy))
    return ordered


def render(profile: str, meta: dict[str, Any], *, surface: str = "pyproject") -> str:
    """The regions an installer places, each one headed by its table.

    The header is context rather than content: an installer writes it only where
    the table is absent, and never a second time into a file that has it.
    """
    out: list[str] = []
    first = True
    for table, lines in contributions(profile, meta):
        if surface != "pyproject":
            header = table
        elif table == "mypy":
            header = "tool.mypy"
        else:
            header = ".".join(filter(None, ("tool.ruff", table)))
        version = meta["profiles"][profile]["version"]
        out += [f"[{header}]" if header else "", f"{OPEN} {profile}@{version}"]
        # The stamp once per file, at the first region. Every region names the
        # profile in its own marker, which is what a reader at a failing build
        # needs; the version, the gates and the contract are a record of the
        # install and repeating them six times would make the file harder to
        # read without making it more true.
        out += [stamp(profile, meta)] if not out[:-2] or first else []
        first = False
        out += [*lines, CLOSE, ""]
    return "\n".join(out).strip() + "\n"


def _mypy(resolved: dict[str, Any]) -> list[str]:
    """The one type-checker key a Python level sets, and never a key TYP-001 reads."""
    forbidden = _gated_keys("python")
    lines = []
    for identity, prop in sorted(resolved["properties"].items()):
        instrument = prop["instrument"]
        if instrument["tool"] != "mypy":
            continue
        setting = instrument["setting"]
        if setting in forbidden:
            raise SystemExit(f"{identity} writes {setting}, which TYP-001 asserts (ADR 0055)")
        lines.append(f"{setting} = {_value(instrument['value'])}".ljust(52) + f"# {identity}")
    return lines


def _gated_keys(stack: str) -> set[str]:
    """ADR 0055 rule 1: the keys a control asserts, read from `stacks:`."""
    import yaml

    register = yaml.safe_load((REPO_ROOT / "controls.yaml").read_text(encoding="utf-8"))
    gates = register["stacks"][stack]["gates"]
    return {
        gate[key]
        for gate in gates.values()
        for key in ("strict_key", "coverage_key")
        if gate.get(key)
    }


def scoped(profile: str, meta: dict[str, Any]) -> str:
    """The nested `src/ruff.toml`, for the properties the register scopes to source.

    Ruff has no per-path `select`, and `per-file-ignores` is the exemption the
    register's own resolution rejected, so a scope is a nested configuration the
    source tree resolves against and the test tree does not.
    """
    resolved = resolve(profile, meta)
    lines = _select_lines(resolved, "source")
    if not lines:
        return ""
    return "\n".join(
        [
            f"{OPEN} {profile}@{meta['profiles'][profile]['version']} (source-scoped)",
            stamp(profile, meta),
            "",
            'extend = "../pyproject.toml"',
            "",
            "[lint]",
            "extend-select = [",
            *lines,
            "]",
            CLOSE,
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="python/standard")
    parser.add_argument(
        "--file",
        choices=("root", "src"),
        default="root",
        help="the root region, or the source-scoped nested configuration",
    )
    args = parser.parse_args()
    meta = load("meta")
    if args.profile not in meta["profiles"]:
        parser.error(f"{args.profile} is not a profile the register defines")
    if not args.profile.startswith("python/"):
        parser.error("only the Python stack renders today — the flat config is owed")
    text = render(args.profile, meta) if args.file == "root" else scoped(args.profile, meta)
    print(text or f"{args.profile} scopes nothing to the package source")
    return 0


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())
