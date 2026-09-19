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

import sys
import tomllib
from typing import Any

import pytest

from conftest import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts"))

from craft_render import contributions, render, scoped
from craft_select import load, resolve

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
