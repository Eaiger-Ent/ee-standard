"""This plugin departs from the one the marketplace published only where it says so.

`scripts/record_published.py` explains the record and why it exists. This file
is the half that needs nothing but the repository: it compares the tree with
`docs/promotion/published.*` and fails on any difference the record does not
declare, or on a declaration that has stopped being true. Whether the record
still describes the marketplace is the other half, `--check`, and it needs the
installed checkout that `_no_ambient_plugin_inventory` keeps from every test.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from conftest import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts"))

from record_published import (
    OURS,
    digest,
    drift,
    load_record,
    main,
    normalised,
    read_published,
    reconcile,
    tree,
)


def _record() -> dict[str, Any]:
    return load_record()


def test_this_tree_departs_from_the_published_copy_only_where_declared() -> None:
    assert reconcile(_record(), tree(OURS)) == []


def test_the_record_is_a_reading_rather_than_a_sketch() -> None:
    record = _record()
    assert record["files"], "an empty record would agree with nothing and declare nothing"
    for path, value in {**record["files"], **record["normalised"]}.items():
        assert len(value) == 64 and int(value, 16) >= 0, f"{path}: not a sha256"
    assert len(record["commit"]) == 40, "the commit it was read at, in full"
    assert set(record["normalised"]) <= set(record["files"])


# The rest hold the comparison itself to account, on trees small enough to read.

_PATTERN = r"docs/(?:here|there)\.md"


def _a_record(published: dict[str, bytes], differences: dict[str, Any]) -> dict[str, Any]:
    record: dict[str, Any] = {
        "files": {p: digest(c) for p, c in published.items()},
        "differences": differences,
        "normalised": {},
    }
    for path, content in published.items():
        for glob, difference in differences.items():
            if "normalise" in difference and path.endswith(glob.rsplit("*", 1)[-1]):
                record["normalised"][path] = digest(normalised(content, difference["normalise"]))
    return record


_LINK = {"stance": "by-design", "why": "each names its own map", "normalise": [_PATTERN]}


def test_an_identical_tree_needs_no_declaration() -> None:
    assert reconcile(_a_record({"a.md": b"same"}, {}), {"a.md": b"same"}) == []


@pytest.mark.parametrize(
    ("ours", "expected"),
    [
        ({"a.md": b"changed"}, "a.md: content differs"),
        ({"a.md": b"same", "b.md": b"new"}, "b.md: here only"),
        ({}, "a.md: published only"),
    ],
)
def test_an_undeclared_difference_fails(ours: dict[str, bytes], expected: str) -> None:
    problems = reconcile(_a_record({"a.md": b"same"}, {}), ours)
    assert any(p.startswith(expected) for p in problems), problems


def test_normalising_hides_the_pattern_and_nothing_else() -> None:
    record = _a_record({"s/x/SKILL.md": b"see docs/there.md"}, {"s/*/SKILL.md": _LINK})
    assert reconcile(record, {"s/x/SKILL.md": b"see docs/here.md"}) == []
    beyond = reconcile(record, {"s/x/SKILL.md": b"read docs/here.md"})
    assert any("differs beyond" in p for p in beyond), beyond


def test_a_declaration_that_stopped_being_true_fails() -> None:
    owed = {"stance": "owed-upstream", "why": "ahead here"}
    record = _a_record({"a.md": b"same"}, {"a.md": owed, "gone/*": owed})
    problems = reconcile(record, {"a.md": b"same"})
    assert any("so `a.md` is stale" in p for p in problems), problems
    assert any(p.startswith("gone/*: matches no file") for p in problems), problems


def test_a_pattern_that_matches_nothing_here_hides_nothing_and_fails() -> None:
    record = _a_record({"s/x/SKILL.md": b"see docs/there.md"}, {"s/*/SKILL.md": _LINK})
    problems = reconcile(record, {"s/x/SKILL.md": b"see nothing"})
    assert any("no `normalise` pattern" in p for p in problems), problems


@pytest.mark.parametrize(
    "difference",
    [{"stance": "owed-upstream", "why": " "}, {"stance": "probably-fine", "why": "x"}],
)
def test_a_declaration_says_which_way_and_why(difference: dict[str, Any]) -> None:
    problems = reconcile(_a_record({"a.md": b"x"}, {"a.md": difference}), {"a.md": b"y"})
    assert any(p.startswith("a.md: ") and ("why" in p or "stance" in p) for p in problems)


def test_a_file_matching_two_declarations_fails() -> None:
    owed = {"stance": "owed-upstream", "why": "ahead here"}
    record = _a_record({"a.md": b"x"}, {"a.md": owed, "*.md": owed})
    problems = reconcile(record, {"a.md": b"y"})
    assert any("matches 2 differences" in p for p in problems), problems


# The other half, which a test can reach only with a checkout it builds itself.


def test_with_no_checkout_the_check_verifies_nothing_and_says_so(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["--check"]) == 3
    assert capsys.readouterr().out.startswith("UNVERIFIED")


def _checkout(root: Path, version: str, readme: bytes) -> Path:
    plugin = root / "plugins" / "control-register"
    (plugin / ".claude-plugin").mkdir(parents=True)
    (plugin / ".claude-plugin" / "plugin.json").write_text(json.dumps({"version": version}))
    (plugin / "README.md").write_bytes(readme)
    git = ["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@example.com"]
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "commit", "-qm", "publish"], check=True)
    return root


def test_a_new_publication_is_drift(tmp_path: Path) -> None:
    before = read_published(_checkout(tmp_path / "a", "0.1.0", b"old"), {"differences": {}})
    assert drift(before, read_published(tmp_path / "a", before)) == []
    after = read_published(_checkout(tmp_path / "b", "0.1.1", b"new"), before)
    lines = drift(before, after)
    assert lines[0] == "published 0.1.1, recorded 0.1.0", lines
    assert "files: recorded and published differ" in lines
