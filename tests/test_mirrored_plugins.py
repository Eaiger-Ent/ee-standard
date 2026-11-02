"""Each mirrored plugin is what `ee-skills` published, less the one declared difference.

`scripts/mirror_plugin.py` explains the record and why it exists (ADR 0060).
This file is the half that needs nothing but the repository: it compares each
`plugins/<name>/` the record names with `docs/promotion/mirrored.json`, and fails
on a file that differs, or that is present on one side only. Whether a mirror
is behind what is published now is the other half, `--check`, and it needs the
installed checkout that `_no_ambient_plugin_inventory` keeps from every test.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from conftest import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts"))

from mirror_plugin import PLUGINS, load_record, main, read_upstream, reconcile
from record_published import digest, tree

RECORD = load_record()
MIRRORS = sorted(RECORD["plugins"])
MARKETPLACE = json.loads((REPO_ROOT / ".claude-plugin/marketplace.json").read_text())


def test_the_record_names_the_two_plugins_adr_0060_mirrors() -> None:
    """The consent ADR 0060 records covers these two and nothing wider."""
    assert MIRRORS == ["lint-md", "lint-yaml"]
    assert RECORD["marketplace"] == "EqualExperts/ee-skills"


@pytest.mark.parametrize("name", MIRRORS)
def test_the_mirror_is_what_was_published_and_nothing_else(name: str) -> None:
    assert reconcile(RECORD["plugins"][name], tree(PLUGINS / name)) == []


@pytest.mark.parametrize("name", MIRRORS)
def test_the_record_is_a_reading_rather_than_a_sketch(name: str) -> None:
    entry = RECORD["plugins"][name]
    assert entry["files"], "an empty record would agree with nothing"
    for row in entry["files"]:
        for key in ("sha256", "mirrored_sha256"):
            if key in row:
                assert len(row[key]) == 64 and int(row[key], 16) >= 0, f"{row['path']}: {key}"
    assert len(entry["commit"]) == 40, "the commit it was read at, in full"


@pytest.mark.parametrize("name", MIRRORS)
def test_the_one_declared_difference_is_the_dependency_and_the_version_is_upstream_s(
    name: str,
) -> None:
    """ADR 0060 rules 3 and 5: `plugin.json` loses `dependencies`, and keeps its version.

    The version is the published one, so `ee-skill: lint-yaml@0.1.20` in a stamp
    means the same thing whichever marketplace installed the skill.
    """
    entry = RECORD["plugins"][name]
    assert list(entry["differences"]) == [".claude-plugin/plugin.json"]
    manifest = json.loads((PLUGINS / name / ".claude-plugin/plugin.json").read_text())
    assert "dependencies" not in manifest
    assert manifest["name"] == name
    assert manifest["version"] == entry["version"]


@pytest.mark.parametrize("name", MIRRORS)
def test_the_marketplace_serves_the_mirror_from_its_own_directory(name: str) -> None:
    listed = {plugin["name"]: plugin for plugin in MARKETPLACE["plugins"]}
    assert name in listed, f"{name} is mirrored and .claude-plugin/marketplace.json omits it"
    assert listed[name]["source"] == f"./plugins/{name}"


# The rest hold the comparison itself to account, on trees small enough to read.

_DROP = {
    "stance": "by-design",
    "why": "names a plugin nobody here serves",
    "remove": [r',\n\s*"dependencies": \[[^\]]*\]'],
}
_PUBLISHED = b'{\n  "name": "x",\n  "dependencies": ["y"]\n}\n'
_MIRRORED = b'{\n  "name": "x"\n}\n'


def _entry(differences: dict[str, Any] | None = None) -> dict[str, Any]:
    files = [{"path": "README.md", "sha256": digest(b"same")}]
    if differences:
        files.append(
            {"path": "p.json", "sha256": digest(_PUBLISHED), "mirrored_sha256": digest(_MIRRORED)}
        )
    return {"version": "1", "commit": "0" * 40, "differences": differences or {}, "files": files}


def test_an_identical_mirror_needs_no_declaration() -> None:
    assert reconcile(_entry(), {"README.md": b"same"}) == []


@pytest.mark.parametrize(
    ("ours", "expected"),
    [
        ({"README.md": b"edited"}, "README.md: differs from the record"),
        ({"README.md": b"same", "new.md": b"x"}, "new.md: here only"),
        ({}, "README.md: published only"),
    ],
)
def test_an_edit_or_a_one_sided_file_fails(ours: dict[str, bytes], expected: str) -> None:
    problems = reconcile(_entry(), ours)
    assert any(p.startswith(expected) for p in problems), problems


def test_the_declared_removal_is_allowed_and_nothing_beyond_it() -> None:
    entry = _entry({"p.json": _DROP})
    assert reconcile(entry, {"README.md": b"same", "p.json": _MIRRORED}) == []
    beyond = reconcile(entry, {"README.md": b"same", "p.json": b'{\n  "name": "z"\n}\n'})
    assert "p.json: differs from the record" in beyond, beyond


def test_a_removal_upstream_has_already_made_is_stale() -> None:
    """The day `ee-skills` drops the key, the declaration has to go with it."""
    entry = _entry({"p.json": _DROP})
    entry["files"][1] = {"path": "p.json", "sha256": digest(_MIRRORED)}
    problems = reconcile(entry, {"README.md": b"same", "p.json": _MIRRORED})
    assert any("so it is stale" in p for p in problems), problems


def test_a_mirror_admits_no_owed_upstream_stance() -> None:
    """A mirror ahead of its source is a fork (ADR 0060 rule 1)."""
    entry = _entry({"p.json": {**_DROP, "stance": "owed-upstream"}})
    problems = reconcile(entry, {"README.md": b"same", "p.json": _MIRRORED})
    assert any("only stance is by-design" in p for p in problems), problems


# The other half, which a test can reach only with a checkout it builds itself.


def test_with_no_checkout_the_check_verifies_nothing_and_says_so(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["--check"]) == 3
    assert capsys.readouterr().out.startswith("UNVERIFIED")


def _checkout(root: Path, version: str) -> Path:
    plugin = root / "plugins" / "lint-x"
    (plugin / ".claude-plugin").mkdir(parents=True)
    manifest = {"name": "lint-x", "dependencies": ["y"], "version": version}
    (plugin / ".claude-plugin" / "plugin.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (plugin / "README.md").write_text(f"lint-x {version}\n")
    git = ["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@example.com"]
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "commit", "-qm", "publish"], check=True)
    return root


def test_a_mirror_is_written_reconciled_and_reported_behind_without_failing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """ADR 0060 rule 4: behind is reported, and `--check` still exits 0 over it."""
    drop = {**_DROP, "remove": [r'\n\s*"dependencies": \[[^\]]*\],']}
    record = tmp_path / "mirrored.json"
    record.write_text(json.dumps({"plugins": {"lint-x": {"differences": {"*.json": drop}}}}))
    into = tmp_path / "plugins"
    common = ["--record", str(record), "--plugins-dir", str(into)]

    assert main(["--checkout", str(_checkout(tmp_path / "a", "0.1.0")), *common]) == 0
    assert "dependencies" not in (into / "lint-x/.claude-plugin/plugin.json").read_text()
    entry = json.loads(record.read_text())["plugins"]["lint-x"]
    assert reconcile(entry, tree(into / "lint-x")) == []

    newer = _checkout(tmp_path / "b", "0.1.1")
    capsys.readouterr()
    assert main(["--check", "--checkout", str(newer), *common]) == 0
    assert "BEHIND: lint-x: published 0.1.1, mirrored 0.1.0" in capsys.readouterr().out
    assert read_upstream(newer, "lint-x", entry)[0]["version"] == "0.1.1"


#: The skill step that copies a script into the adopter's repository.
_HOOK_COPY = re.compile(r'cp "\$\{CLAUDE_SKILL_DIR\}/scripts/([\w.-]+)" \.claude/hooks/')


def _deployed_hooks() -> list[Path]:
    return [
        skill.parent / "scripts" / script
        for name in MIRRORS
        for skill in sorted((REPO_ROOT / "plugins" / name / "skills").glob("*/SKILL.md"))
        for script in _HOOK_COPY.findall(skill.read_text(encoding="utf-8"))
    ]


def _strictest_craft_line_length() -> int:
    regions = (REPO_ROOT / "plugins/craft/profiles").glob("*/pyproject-region.toml")
    limits = [
        int(found)
        for region in regions
        for found in re.findall(r"^line-length = (\d+)", region.read_text(), re.MULTILINE)
    ]
    assert limits, "no Craft profile sets line-length — this test is now vacuous"
    return min(limits)


def test_the_skills_still_say_which_hooks_they_deploy() -> None:
    """Checked separately so a reworded copy step fails here, not by emptying the test below."""
    assert {hook.name for hook in _deployed_hooks()} == {"md-lint-hook.py", "yaml-lint-hook.py"}


@pytest.mark.parametrize("hook", _deployed_hooks(), ids=lambda hook: hook.name)
def test_a_deployed_hook_fits_every_craft_profile(hook: Path) -> None:
    """An adopter can neither fix a deployed hook's lint failures nor exempt the file.

    A deployed copy may differ from upstream only by `LINT_INVOCATION`, so
    rewrapping it locally makes it read as tampered with, and the next
    redeploy undoes the edit. An `extend-exclude` or `per-file-ignores` entry
    weakens LNT-001, which admits no exemptions. So a hook wider than a Craft
    profile fails every adopter who installs both, and only upstream can fix it.
    lint-md 1.0.23 and lint-yaml 0.1.20 did exactly that (#285). This
    repository's own limit is 100, so nothing here noticed.
    """
    limit = _strictest_craft_line_length()
    long = [
        f"{number}: {len(line)}"
        for number, line in enumerate(hook.read_text(encoding="utf-8").splitlines(), 1)
        if len(line) > limit
    ]
    assert not long, f"{hook.name} has lines over {limit} (line: width): {long}"
