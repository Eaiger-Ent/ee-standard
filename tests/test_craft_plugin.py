"""The plugin an adopter installs, held to the register it was published from.

`plugins/craft/profiles/` is rendered output: the configuration `craft-install`
copies, the residue it hands back, and a manifest of what each profile turns on.
`scripts/craft_publish.py` writes it and this re-runs that, so a change to
`craft/` nobody published is a failing build rather than a plugin quietly a
version behind.

**A committed copy needs a reason**, and this one has two. An adopter installs a
plugin rather than a repository, so the register would otherwise have to travel
with it — 2,600 lines of YAML in a second place. And the installer runs where no
toolchain is guaranteed: a React-only repository may have no Python at all, so a
skill that resolved the register at install time would need one, where a skill
that copies a file needs nothing. `docs/craft/build.installer.md` § The plugin
ships what it writes is the reasoning; this is what keeps it true.
"""

from __future__ import annotations

import json
import re
import sys
from typing import Any

import pytest
import yaml

from conftest import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts"))

from craft_publish import PLUGIN, PROFILES, artefacts
from craft_select import load, resolve

MANIFEST = json.loads((PLUGIN / "profiles/manifest.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def meta() -> dict[str, Any]:
    return load("meta")


def test_the_published_profiles_are_what_the_register_renders(meta: dict[str, Any]) -> None:
    """The check that makes a committed copy safe to keep.

    It fails on a register edit nobody published, on a hand edit to a published
    artefact, and on a renderer change that moved a byte. The fix is the same in
    every case: `uv run python scripts/craft_publish.py`.
    """
    stale = []
    for path, body in sorted(artefacts(meta).items()):
        target = PLUGIN / path
        if not target.is_file():
            stale.append(f"{path} (missing)")
        elif target.read_text(encoding="utf-8") != body:
            stale.append(path)
    assert not stale, f"run `uv run python scripts/craft_publish.py`: {stale}"


def test_nothing_is_published_that_is_no_longer_rendered(meta: dict[str, Any]) -> None:
    """A profile removed from the register leaves its files behind otherwise.

    The residue to worry about is a configuration for a profile that no longer
    exists, sitting in the plugin looking installable.
    """
    rendered = set(artefacts(meta))
    published = {
        str(path.relative_to(PLUGIN))
        for path in (PLUGIN / "profiles").rglob("*")
        if path.is_file()
    }
    assert published - rendered == set()


@pytest.mark.parametrize("profile", PROFILES)
def test_the_manifest_agrees_with_the_register_about_what_is_installed(
    profile: str, meta: dict[str, Any]
) -> None:
    """The manifest is what the chooser presents, so a wrong count misleads a yes."""
    entry = MANIFEST["profiles"][profile]
    resolved = resolve(profile, meta)
    assert entry["version"] == meta["profiles"][profile]["version"]
    assert entry["properties"] == len(resolved["properties"])
    expected = len(resolved["codes"] if resolved["stack"] == "python" else resolved["rules"])
    assert entry["rules"] == expected


@pytest.mark.parametrize("profile", PROFILES)
def test_every_published_configuration_carries_its_stamp(profile: str) -> None:
    """ADR 0055 rule 2, on the artefact that actually reaches a repository.

    The skill copies these bytes and is told never to type a stamp, so the stamp
    has to be in them before they ship.
    """
    slug = profile.replace("/", "-")
    version = MANIFEST["profiles"][profile]["version"]
    configs = [
        path
        for path in (PLUGIN / "profiles" / slug).iterdir()
        if path.suffix in {".toml", ".mjs"}
    ]
    assert configs, slug
    for path in configs:
        text = path.read_text(encoding="utf-8")
        assert f"ee-craft: {profile}@{version}" in text, path.name
        assert text.count(">>> ee-craft") == text.count("<<< ee-craft"), path.name


def test_no_published_configuration_writes_a_key_a_control_asserts() -> None:
    """ADR 0055 rule 1, checked on what ships rather than on what renders.

    `strict` and the coverage key are TYP-001's, read from `stacks:` rather than
    listed here — a register contract that gates another key adds it to this
    test with no change.
    """
    register = yaml.safe_load((REPO_ROOT / "controls.yaml").read_text(encoding="utf-8"))
    forbidden = {
        gate[key]
        for stack in register["stacks"].values()
        for gate in stack["gates"].values()
        for key in ("strict_key", "coverage_key")
        if gate.get(key)
    }
    assert forbidden, "stacks: no longer names a gated key — this test is now vacuous"
    for path in (PLUGIN / "profiles").rglob("*.toml"):
        keys = set(re.findall(r"^([a-z_-]+) =", path.read_text(encoding="utf-8"), re.M))
        assert not keys & forbidden, f"{path.name} writes {sorted(keys & forbidden)}"


def test_the_residue_ships_for_every_combination_a_repository_can_ask_for() -> None:
    """A repository with both stacks gets one document, not two merged by a skill.

    The residue depends on every level installed, because a level binds
    properties the level below leaves unenforced — so the combinations are
    rendered here rather than composed at install time.
    """
    for python in ("python-standard", "python-strict"):
        for react in ("react-standard", "react-strict"):
            assert (PLUGIN / f"profiles/{python}+{react}/unenforced.md").is_file()
    for profile in PROFILES:
        assert (PLUGIN / f"profiles/{profile.replace('/', '-')}/unenforced.md").is_file()


def test_the_skill_reads_the_manifest_rather_than_counting_rules() -> None:
    """The skill's own instruction, held to what it says.

    A skill that counted rules in context would be a second implementation of
    the resolver, in the least reviewable place available — and the number it
    presented would be the one a team consented to.
    """
    skill = (PLUGIN / "skills/craft-install/SKILL.md").read_text(encoding="utf-8")
    assert "profiles/manifest.json" in skill
    assert "you do not count rules yourself" in skill.lower()
    assert "never write a loosening" in skill.lower()
    assert "never fill in a stamp by hand" in skill.lower()


def test_the_skill_carries_the_two_rules_its_first_trial_found() -> None:
    """Both were found by running it, and neither is derivable from the design.

    A later configuration location wins at run time where the register's search
    order reads the first, so a profile written into `pyproject.toml` beside a
    `ruff.toml` applies to nothing the nested configuration does not rescue. And
    a `pyproject.toml` can say *no `[tool.ruff]` section* in a comment, which a
    search for the header finds. `docs/craft/build.installer.md` § The first run
    of the installer is the record of both.
    """
    skill = (PLUGIN / "skills/craft-install/SKILL.md").read_text(encoding="utf-8")
    assert "wins at run time" in skill
    assert "anchored to a line" in skill


def test_the_stamp_names_the_installer_that_wrote_it() -> None:
    """ADR 0038's shape, reused by ADR 0055 rule 2, on Craft's own artefacts.

    *Which profile* and *which installer* are two different questions: the first
    says what the rule is and the second says what to re-run. The version is
    read from the plugin's own manifest when the artefacts are rendered, so a
    plugin version bump that nobody re-published fails
    `test_the_published_profiles_are_what_the_register_renders` rather than
    shipping a stamp that names a version which never wrote anything.
    """
    version = json.loads(
        (PLUGIN / ".claude-plugin/plugin.json").read_text(encoding="utf-8")
    )["version"]
    stamped = [
        path
        for path in (PLUGIN / "profiles").rglob("*")
        if path.is_file() and path.name != "manifest.json"
    ]
    assert len(stamped) == 14, stamped
    for path in stamped:
        assert f"ee-skill: craft-install@{version}" in path.read_text(encoding="utf-8"), path.name
