#!/usr/bin/env -S uv run python
"""A Craft profile's configuration, rendered from the register — S5's writer.

`scripts/craft_select.py` answers *what does this profile turn on*. This answers
*what goes in the file*: for Python the `[tool.ruff]` region an installer writes
into `pyproject.toml`, the nested `src/ruff.toml` that two source-scoped
properties need, and at `strict` the one `[tool.mypy]` key ADR 0055 permits; for
React the whole `eslint.config.mjs`, because a flat config is a module and no
span of one means anything on its own.

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
    uv run python scripts/craft_render.py --profile react/standard
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import textwrap
from collections.abc import Callable
from functools import cache
from pathlib import Path
from typing import Any

from craft_select import REPO_ROOT, load, properties, resolve, ruff_catalogue

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
        f"# ee-craft: {profile}@{version}  ee-skill: craft-install@{installer_version()}  "
        "gates: none (no any. property binds an instrument)  "
        f"craft-contract: {meta['craft_contract']}"
    )


@cache
def installer_version() -> str:
    """The plugin's own version, read from the plugin rather than repeated here.

    ADR 0038's stamp names the skill that wrote an artefact, and a Craft stamp
    reuses that shape per ADR 0055 rule 2. It matters for the same reason it
    does there: a reader at a failing build has a rule code, and *which profile*
    and *which installer* are two different questions — the first says what the
    rule is, the second says what to re-run.
    """
    manifest = REPO_ROOT / "plugins/craft/.claude-plugin/plugin.json"
    return str(json.loads(manifest.read_text(encoding="utf-8"))["version"])


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


#: Where a React profile's rules apply, and the only globs Craft chooses for
#: itself. They are a **fixed default the installer reports** rather than a
#: configuration key: a new repository has no tests to infer a convention from,
#: which is the repository ADR 0052 says the profile is for, and a team using
#: another convention can see from the report why their tests are unlinted.
#: `docs/craft/build.installer.md` § The React config is one file, written whole.
SCOPES = {
    None: ["src/**/*.ts", "src/**/*.tsx"],
    "modules": ["src/**/*.ts"],
    "tests": [
        "**/*.test.ts",
        "**/*.test.tsx",
        "**/*.spec.ts",
        "**/*.spec.tsx",
        "**/__tests__/**",
    ],
}

#: ESLint and `typescript-eslint` wiring: the ignores, the parser, the project
#: service and the browser globals. It is not a Craft decision and carries no
#: property identity — the same reason `register_check` keeps VS Code's own
#: settings layout in the checker rather than in the register (ADR 0018).
PREAMBLE = """  {{ ignores: ['node_modules/**', 'dist/**', 'coverage/**'] }},

  // The parser, and the project service the type-checked rules need. No preset
  // rules are attached here: what is enabled is enabled by name below, or by a
  // base the register names in `bases:`.
  {{
    ...{tse}.configs.base,
    files: SOURCE,
    languageOptions: {{
      ...{tse}.configs.base.languageOptions,
      parserOptions: {{ projectService: true, tsconfigRootDir: import.meta.dirname }},
      globals: {{ ...globals.browser }},
    }},
  }},
"""

#: The namespace the preamble registers by spreading `configs.base`. A second
#: registration of it would be Craft declaring a plugin the wiring above already
#: declared — and `typescript-eslint`'s default export is not the plugin object,
#: so the second one would be wrong as well as redundant.
PREAMBLE_REGISTERS = ("@typescript-eslint",)


def _namespace(rule: str) -> str:
    return rule.rsplit("/", 1)[0]


def _packages(meta: dict[str, Any]) -> dict[str, str]:
    return {
        source["namespace"]: source["package"]
        for source in meta["sources"].values()
        if source.get("namespace")
    }


def _identifier(package: str) -> str:
    """The name an import binds. `@eslint-react/eslint-plugin` is `eslintReact`."""
    stem = package.replace("@", "").replace("/eslint-plugin", "").replace("eslint-plugin-", "")
    head, *rest = stem.replace("/", "-").split("-")
    return head + "".join(word.capitalize() for word in rest)


def _js(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return f"'{value}'"
    if isinstance(value, dict):
        inside = ", ".join(f"{key}: {_js(item)}" for key, item in value.items())
        return "{ " + inside + " }"
    if isinstance(value, list):
        return "[" + ", ".join(_js(item) for item in value) + "]"
    return str(value)


def _rule_lines(profile: str, meta: dict[str, Any], scope: str | None) -> list[str]:
    """Every rule at this scope, once, under the properties it serves.

    **Once** is the part that needed care: `react-hooks/rules-of-hooks` is the
    instrument of two properties and `react-hooks/purity` of two more, so a
    naive pass per property writes four duplicate keys into one object literal.
    JavaScript takes the last of them silently, which is a configuration nobody
    can read back — so a rule is written where it first appears and its comment
    names every property it carries.

    `alternatives:` become `'off'` **only where the losing rule's namespace is a
    base**: a preset that is not applied has nothing to stand down, and writing
    `off` for a rule nothing enabled would be a line no reader could account
    for. `craft/react.yaml`'s `bases:` is what makes that derivable rather than
    a judgement the renderer makes.
    """
    resolved = resolve(profile, meta)
    bases = {base["namespace"] for base in load("react").get("bases", [])}
    owners: dict[str, list[str]] = {}
    spelling: dict[str, str] = {}
    for identity, prop in sorted(resolved["properties"].items()):
        if prop.get("scope") != scope or prop["instrument"]["tool"] != "eslint":
            continue
        instrument = prop["instrument"]
        settings = prop.get("settings") or {}
        stood_down = [
            rule
            for alternative in prop.get("alternatives", [])
            for rule in alternative.get("rules", [])
            if _namespace(rule) in bases
        ]
        for rule in stood_down:
            owners.setdefault(rule, []).append(identity)
            spelling.setdefault(rule, f"      '{rule}': 'off',")
        for position, rule in enumerate(instrument["rules"]):
            owners.setdefault(rule, []).append(identity)
            value = f"['error', {_js(settings)}]" if settings and position == 0 else "'error'"
            spelling.setdefault(rule, f"      '{rule}': {value},")

    lines: list[str] = []
    previous: list[str] = []
    for rule, carried in owners.items():
        if carried != previous:
            lines.append(f"      // {', '.join(carried)}")
            previous = carried
        lines.append(spelling[rule])
    return lines


def render_react(profile: str, meta: dict[str, Any]) -> str:
    """The whole `eslint.config.mjs`, because a flat config is code.

    The Python surface takes spans inside a file somebody else may own; this one
    cannot. A flat config is a module with imports and an exported array, and
    there is no span of it that means anything on its own — so Craft writes the
    file whole or writes nothing, and `build.installer.md` § The React config is
    one file, written whole is why the refusal is the same shape as the Python
    one rather than a weaker version of it.
    """
    resolved = resolve(profile, meta)
    packages = _packages(meta)
    used = sorted({_namespace(rule) for rule in resolved["rules"]})
    imports = [(packages[namespace], _identifier(packages[namespace])) for namespace in used]
    imports.append(("globals", "globals"))

    body = [
        f"// >>> ee-craft {profile}@{meta['profiles'][profile]['version']}",
        f"//{stamp(profile, meta)[1:]}",
        "// Written by craft-install from the Craft register. Re-run it rather",
        "// than editing here: a hand edit is what the next run reports.",
        "",
        *[
            f"import {name} from '{package}'"
            for package, name in sorted(imports, key=lambda pair: pair[1])
        ],
        "",
        f"const SOURCE = {_js(SCOPES[None])}",
        f"const MODULES = {_js(SCOPES['modules'])}",
        f"const TESTS = {_js(SCOPES['tests'])}",
        "",
        "export default [",
        PREAMBLE.format(tse=_identifier(packages['@typescript-eslint'])),
    ]
    for base in load("react").get("bases", []):
        name = _identifier(packages[base["namespace"]])
        body.append(f"  {{ ...{name}.{base['config']}, files: SOURCE }},")
    body.append("")

    for scope, files in (("SOURCE", None), ("MODULES", "modules"), ("TESTS", "tests")):
        lines = _rule_lines(profile, meta, files)
        if not lines:
            continue
        bases = {base["namespace"] for base in load("react").get("bases", [])}
        provided = bases.union(PREAMBLE_REGISTERS)
        plugins = sorted(
            {_namespace(rule.split("'")[1]) for rule in lines if "'" in rule} - provided
        )
        registered = ", ".join(
            namespace
            if _identifier(packages[namespace]) == namespace
            else f"'{namespace}': {_identifier(packages[namespace])}"
            for namespace in plugins
        )
        body += [
            "  {",
            f"    files: {scope},",
            *([f"    plugins: {{ {registered} }},"] if registered else []),
            "    rules: {",
            *lines,
            "    },",
            "  },",
        ]
    body += ["]", "// <<< ee-craft"]
    return "\n".join(body) + "\n"


#: The residue, in the four shapes a property with no instrument can take, and
#: the order the document prints them. `docs/craft/build.installer.md` § The
#: residue is a document of its own is why three of them are handed to a reader
#: and the fourth is a count.
RESIDUE_SECTIONS: tuple[tuple[str, str, Callable[[dict[str, Any]], bool]], ...] = (
    (
        "Judgment only",
        "Nothing can decide these but a person. They are the half of *well-made* "
        "a linter has no access to, and a rule claiming otherwise would be worse "
        "than the silence.",
        lambda prop: bool(prop.get("unenforced")) and prop.get("bucket") in (3, "3"),
    ),
    (
        "A check could hold these, and none is written",
        "Enforceable in principle, at a cost nobody has paid. They are the list a "
        "later profile version is drawn from, and until then they are yours.",
        lambda prop: bool(prop.get("unenforced")) and prop.get("bucket") in (2, "2"),
    ),
    (
        "An instrument exists, and this profile does not install it",
        "Either it was measured and demoted — the reason is with it, and it is the "
        "reason not to re-enable it — or nothing has measured it and ADR 0051's "
        "third precondition is unmet.",
        lambda prop: bool(
            (prop.get("unenforced") and prop.get("bucket") in (1, "1")) or prop.get("candidate")
        ),
    ),
)


def _wrap(text: str) -> list[str]:
    """Prose at a width a diff can show.

    The residue is Markdown in somebody else's repository, and DOC-001 lints
    Markdown — so a document Craft writes has to pass the gate the register
    already requires, which the first render did not.
    """
    return textwrap.wrap(" ".join(text.split()), width=88) or [""]


def _tool(name: str) -> str:
    """A candidate's tool, which is sometimes two tools and a conjunction.

    `commitlint with @commitlint/config-conventional, or commitizen` is one
    value in the register, and wrapping it in backticks whole produces a code
    span with spaces in it — which DOC-001 rejects, and which reads as a package
    nobody can install.
    """
    name = name.strip()
    return f"`{name}`" if " " not in name else name


def _bucket_only(reason: str) -> bool:
    """Whether a reason says only what its section heading already said."""
    return bool(re.fullmatch(r"Bucket [0-9]\.?", reason.strip()))


def _residue_rows(profiles: list[str]) -> dict[str, dict[str, Any]]:
    """Every property in scope for these profiles that binds no instrument."""
    stacks = {profile.partition("/")[0] for profile in profiles} | {"any"}
    return {
        identity: prop
        for identity, prop in sorted(properties().items())
        if identity.split(".", 1)[0] in stacks and "instrument" not in prop
    }


def render_residue(profiles: list[str], meta: dict[str, Any]) -> str:
    """The judgment-only half, as prose an assistant loads — labelled unenforced.

    `plan.md` § S5 requires the installer to hand this back and **the label is
    the whole of what makes it honest**: everything here is a property the
    profile could not install, so nothing in this document fails a build and
    nothing in it is a rule. A file that read like the configuration would be
    claiming enforcement the workstream says it will not ship.

    Two states are deliberately counted rather than listed. `satisfied_by` holds
    because of a choice the profile already made, so asking a reader to check it
    would be asking them to re-derive a decision; `out_of_scope` is somebody
    else's surface — a control, or `gate-repo`'s platform state — and repeating
    it here would be Craft taking credit for a gate that already runs.
    """
    rows = _residue_rows(profiles)
    stamps = [f"{profile}@{meta['profiles'][profile]['version']}" for profile in profiles]
    listed: set[str] = set()

    # The markers are HTML comments here, and not the `#` form the two
    # configurations use: `# >>> ee-craft` in a Markdown file is a level-one
    # heading, which is what the first render produced.
    out = [
        "# What Craft does not enforce here",
        "",
        f"<!-- >>> ee-craft {' '.join(stamps)} -->",
        f"<!-- ee-craft: {', '.join(stamps)}  "
        f"ee-skill: craft-install@{installer_version()}  gates: none "
        f"(no any. property binds an instrument)  craft-contract: "
        f"{meta['craft_contract']} -->",
        "<!-- <<< ee-craft -->",
        "",
        "**Every property below is unenforced.** Nothing here fails a build, no",
        "tool reports on it, and none of it is a rule — it is what the Craft",
        "register holds that this profile could not install, written out so that",
        "an assistant reading this repository knows what is expected of the code",
        "and knows that nothing is checking.",
        "",
        "Generated by `craft-install` from the Craft register. Re-run it rather",
        "than editing here — a hand edit is what the next run reports.",
    ]

    for title, blurb, matches in RESIDUE_SECTIONS:
        chosen = {
            identity: prop
            for identity, prop in rows.items()
            if identity not in listed and matches(prop)
        }
        listed |= set(chosen)
        out += ["", f"## {title} ({len(chosen)})", "", *_wrap(blurb), ""]
        for identity, prop in chosen.items():
            reason = prop.get("unenforced") or (prop.get("candidate") or {}).get("why_not", "")
            out.append(f"### `{identity}`")
            out += ["", *_wrap(f"{prop['asserts']}."), ""]
            if candidate := prop.get("candidate"):
                out += _wrap(f"**An instrument exists:** {_tool(candidate['tool'])}. {reason}")
                out.append("")
            elif not _bucket_only(reason):
                # `Bucket 3.` and nothing else is the register saying what the
                # section heading has already said. Printing it would pad a
                # document whose whole value is that a reader gets through it.
                out += [*_wrap(f"**Why nothing checks it:** {reason}"), ""]

    elsewhere = {identity: prop for identity, prop in rows.items() if identity not in listed}
    out += [
        "",
        f"## Recorded elsewhere, and not yours to check ({len(elsewhere)})",
        "",
        "Listed by name only. Each is either satisfied by a choice this profile",
        "already made, or owned by a control or a gate that runs without you.",
        "",
    ]
    for identity, prop in elsewhere.items():
        owner = prop.get("out_of_scope") or "the profile's own base choice"
        out += textwrap.wrap(
            f"- `{identity}` — {prop['asserts']}. Owned by {owner}.",
            width=88,
            subsequent_indent="  ",
        )
    squeezed: list[str] = []
    for line in out:
        if line or (squeezed and squeezed[-1]):
            squeezed.append(line)
    return "\n".join(squeezed).rstrip("\n") + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="python/standard")
    parser.add_argument(
        "--file",
        choices=("root", "src", "residue"),
        default="root",
        help="the root region, or the source-scoped nested configuration",
    )
    args = parser.parse_args()
    meta = load("meta")
    chosen = args.profile.split(",")
    for name in chosen:
        if name not in meta["profiles"]:
            parser.error(f"{name} is not a profile the register defines")
    if args.file == "residue":
        # `end=""` because the document already ends in a newline, and DOC-001
        # rejects the blank line `print` would add — which is the residue's
        # whole lesson in miniature: Craft writes Markdown into a repository
        # whose Markdown is gated.
        print(render_residue(chosen, meta), end="")
        return 0
    args.profile = chosen[0]
    if args.profile.startswith("react/"):
        print(render_react(args.profile, meta))
        return 0
    text = render(args.profile, meta) if args.file == "root" else scoped(args.profile, meta)
    print(text or f"{args.profile} scopes nothing to the package source")
    return 0


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())
