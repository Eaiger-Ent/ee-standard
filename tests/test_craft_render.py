"""What the installer would write, checked against what the register says.

`scripts/craft_render.py` turns a profile into the region an installer places.
These tests hold it to the three things that make such a region safe to write
into a file a control already gates: it is **valid** (ruff's own option tree
decides where a setting goes, and a mis-placed key is silently ignored by the
tool that reads it), it is **complete** against the register, and it writes
**no key TYP-001 asserts**, which is ADR 0055 rule 1 in the only form a test can
hold — a rendering, not an intention.

They shell out to the installed ruff, because that is the design: where an
option lives and whether a linter carries a preview rule are facts about the
tool the repository will run, not constants Craft may keep.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

import pytest

from conftest import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts"))

from craft_render import contributions, render, render_react, render_residue, scoped
from craft_select import load, resolve
from craft_select import properties as _register_properties

PROFILES = ("python/standard", "python/strict")


@pytest.fixture(scope="module")
def meta() -> dict[str, Any]:
    return load("meta")


def _parsed(text: str) -> dict[str, Any]:
    return tomllib.loads(text)


@pytest.mark.parametrize("profile", PROFILES)
def test_the_rendered_region_is_valid_toml(profile: str, meta: dict[str, Any]) -> None:
    """A region that does not parse is a repository that does not build."""
    assert _parsed(render(profile, meta))


@pytest.mark.parametrize("profile", PROFILES)
def test_every_selector_the_register_resolves_is_written(
    profile: str, meta: dict[str, Any]
) -> None:
    """The rendering is the register's selection, not a subset of it.

    Source-scoped properties are in the nested configuration rather than the
    root one, so the two are read together — which is also the check that the
    scope does not quietly drop a rule on its way out of the register.
    """
    document = _parsed(render(profile, meta))
    nested = _parsed(scoped(profile, meta) or "")
    written = set(document["tool"]["ruff"]["lint"]["select"])
    written |= set(nested.get("lint", {}).get("extend-select", []))

    resolved = resolve(profile, meta)
    expected: set[str] = set()
    for prop in resolved["properties"].values():
        instrument = prop["instrument"]
        if instrument["tool"] != "ruff":
            continue
        expected |= set(instrument.get("codes", []))
    assert expected <= written, sorted(expected - written)


@pytest.mark.parametrize("profile", PROFILES)
def test_a_setting_lands_where_ruff_keeps_it(profile: str, meta: dict[str, Any]) -> None:
    """`max-complexity` is mccabe's and `max-statements` is pylint's.

    Written into the wrong table, both parse and neither applies — ruff ignores
    an unknown key in a table it owns, so the failure mode is a threshold that
    silently does nothing. The placement is asked of `ruff config`; this is what
    holds the answer to the file.
    """
    lint = _parsed(render(profile, meta))["tool"]["ruff"]["lint"]
    assert lint["mccabe"]["max-complexity"] == 10
    assert lint["pylint"]["max-statements"] == 25


def test_strict_sets_the_one_mypy_key_and_none_the_control_asserts(meta: dict[str, Any]) -> None:
    """ADR 0055 rule 1, in the only form a test can hold: what was rendered.

    `strict` and `files` are TYP-001's — `typecheck-strict-and-blocking` reads
    both — and a profile that wrote either could weaken the control under its
    own name. The rule is resolved from `stacks:` at render time, so this test
    asserts the outcome rather than restating the list.
    """
    mypy = _parsed(render("python/strict", meta))["tool"]["mypy"]
    assert mypy == {"disallow_any_explicit": True}


def test_standard_writes_no_mypy_section_at_all(meta: dict[str, Any]) -> None:
    """The level below contributes nothing to type checking, and says so by absence."""
    assert "mypy" not in _parsed(render("python/standard", meta)).get("tool", {})


@pytest.mark.parametrize("profile", PROFILES)
def test_the_stamp_is_written_once_and_names_the_profile(
    profile: str, meta: dict[str, Any]
) -> None:
    """ADR 0055 rule 2. One stamp per file, however many regions it has."""
    text = render(profile, meta)
    stamps = [line for line in text.splitlines() if line.startswith("# ee-craft:")]
    version = meta["profiles"][profile]["version"]
    assert len(stamps) == 1
    assert f"{profile}@{version}" in stamps[0]
    assert text.count("# >>> ee-craft") == text.count("# <<< ee-craft")
    markers = [line for line in text.splitlines() if ">>> ee-craft" in line]
    assert all(f"{profile}@{version}" in line for line in markers)


@pytest.mark.parametrize("profile", PROFILES)
def test_rendering_is_deterministic(profile: str, meta: dict[str, Any]) -> None:
    """A re-run that changes nothing is S5's exit criterion, and it starts here."""
    assert render(profile, meta) == render(profile, meta)


def test_a_contribution_is_lines_rather_than_a_table(meta: dict[str, Any]) -> None:
    """The merge discipline ADR 0055 left to S5, asserted at its narrowest.

    Two writers to one TOML file cannot each own a table header: a second
    `[tool.mypy]` is not a merge, it is an invalid document, and TYP-001
    requires that table to exist already. So nothing Craft renders may carry a
    header of its own.
    """
    for _, lines in contributions("python/strict", meta):
        headers = [
            line for line in lines if line.lstrip().startswith("[") and line.rstrip().endswith("]")
        ]
        assert not headers


def test_the_source_scope_carries_exactly_the_rows_the_register_scopes(
    meta: dict[str, Any],
) -> None:
    """A scope is a nested configuration, and its contents are the register's."""
    nested = _parsed(scoped("python/strict", meta))
    identities = {
        line.split("# ")[-1].strip()
        for line in scoped("python/strict", meta).splitlines()
        if "# python." in line
    }
    expected = {
        identity
        for identity, prop in resolve("python/strict", meta)["properties"].items()
        if prop.get("scope") == "source"
    }
    assert identities == expected
    assert nested["extend"] == "../pyproject.toml"


REACT = ("react/standard", "react/strict")


def _react_rules(text: str) -> list[str]:
    """Every rule entry in a rendered flat config, in the order it is written."""
    return [
        line.split("'")[1]
        for line in text.splitlines()
        if line.strip().startswith("'") and "':" in line
    ]


@pytest.mark.parametrize("profile", REACT)
def test_every_rule_the_register_binds_is_written_once(profile: str, meta: dict[str, Any]) -> None:
    """A flat config is written whole, so completeness is the whole of its safety.

    The Python region can be read back out of a TOML document; this cannot be
    parsed without a JavaScript engine, so the test reads the rule entries it
    writes and holds them to the register.
    """
    written = _react_rules(render_react(profile, meta))
    assert len(written) == len(set(written)), "a rule is written twice"
    bound = {
        rule
        for prop in resolve(profile, meta)["properties"].values()
        for rule in prop["instrument"].get("rules", [])
    }
    assert bound <= set(written), sorted(bound - set(written))


@pytest.mark.parametrize("profile", REACT)
def test_only_a_base_namespace_is_stood_down(profile: str, meta: dict[str, Any]) -> None:
    """An `off` for a rule nothing enabled is a line no reader can account for.

    C1 resolved seven `@eslint-react` overlaps in `react-hooks`' favour, and the
    base config is what enables the losing copies — so the `off` lines follow
    from `bases:` rather than from a judgement in the renderer.
    `eslint-plugin-react` ships no preset here, which is why its two recorded
    alternatives get no line at all.
    """
    text = render_react(profile, meta)
    off = [
        line.split("'")[1]
        for line in text.splitlines()
        if line.strip().endswith("'off',")
    ]
    bases = {base["namespace"] for base in load("react")["bases"]}
    assert off, "the overlaps C1 resolved are not being stood down"
    assert all(rule.rsplit("/", 1)[0] in bases for rule in off), off


@pytest.mark.parametrize("profile", REACT)
def test_every_namespace_written_is_imported(profile: str, meta: dict[str, Any]) -> None:
    """A rule whose plugin is not imported is a configuration that will not load."""
    text = render_react(profile, meta)
    packages = {
        source["namespace"]: source["package"]
        for source in meta["sources"].values()
        if source.get("namespace")
    }
    imported = {line.split("'")[1] for line in text.splitlines() if line.startswith("import ")}
    for rule in _react_rules(text):
        assert packages[rule.rsplit("/", 1)[0]] in imported, rule


def test_the_test_scope_carries_the_testing_library_rules(meta: dict[str, Any]) -> None:
    """The scope the migration lost, asserted where it is now recorded.

    The bench scoped `testing-library` to tests; `craft/react.yaml` did not
    carry it until the renderer needed it, and a profile that lints production
    code for `prefer-screen-queries` is a profile a team switches off.
    """
    text = render_react("react/standard", meta)
    tests_block = text.split("files: TESTS,", 1)[1]
    assert all(rule.startswith("testing-library/") for rule in _react_rules(tests_block))
    before = _react_rules(text.split("files: TESTS,", 1)[0])
    assert not any(rule.startswith("testing-library/") for rule in before)


@pytest.mark.parametrize("profile", REACT)
def test_the_flat_config_is_stamped_and_deterministic(profile: str, meta: dict[str, Any]) -> None:
    text = render_react(profile, meta)
    version = meta["profiles"][profile]["version"]
    assert f"// ee-craft: {profile}@{version}" in text
    assert text.count("// >>> ee-craft") == text.count("// <<< ee-craft") == 1
    assert text == render_react(profile, meta)


def test_the_residue_lists_every_unenforced_property_and_claims_none(
    meta: dict[str, Any],
) -> None:
    """The residue is the half the profile could not install, and says so.

    Two states are counted rather than listed, and the distinction is the point:
    a `satisfied_by` property holds because of a choice the profile made, and an
    `out_of_scope` one is a control's or a gate's. Handing either to a reader as
    *yours to watch* would be asking them to re-check something that is already
    checked.
    """
    profiles = ["python/standard", "react/standard"]
    text = render_residue(profiles, meta)
    assert "**Every property below is unenforced.**" in text

    listed = set(re.findall(r"^### `([a-z]+\.[a-z0-9-]+)`$", text, re.M))
    counted = set(re.findall(r"^- `([a-z]+\.[a-z0-9-]+)`", text, re.M))
    rows = {
        identity: prop
        for identity, prop in _register_properties().items()
        if identity.split(".", 1)[0] in {"python", "react", "any"} and "instrument" not in prop
    }
    assert listed | counted == set(rows), sorted(set(rows) ^ (listed | counted))
    for identity in listed:
        prop = rows[identity]
        assert not prop.get("satisfied_by") and not prop.get("out_of_scope"), identity


def test_the_residue_passes_the_markdown_gate_it_will_be_linted_by(
    meta: dict[str, Any], tmp_path: Path
) -> None:
    """Craft writes Markdown into a repository whose Markdown DOC-001 lints.

    A residue that failed that gate would install a violation of the control
    register alongside the profile, which is the one thing an installer of this
    standard must not do. The first render failed three rules — a code span with
    spaces in it, `__init__` read as emphasis, and a trailing blank line.
    """
    document = tmp_path / "unenforced.md"
    document.write_text(render_residue(["python/strict", "react/strict"], meta))
    result = subprocess.run(
        [str(REPO_ROOT / "node_modules/.bin/markdownlint-cli2"), str(document)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr or result.stdout
