"""The file map names what is there, and everything at the top level is named.

`docs/14-file-map.md` answers *which file*, and a map nobody checks is a map
that quietly stops being true. Two directions, and they fail differently:

**Every path it names exists.** Catches a rename or a deletion — the ordinary
way a map rots.

**Every tracked root entry and top-level directory is named.** This is the half
that matters and the harder one, because a map is an **allow-list**: what it
leaves out is invisible, there is no line to read and no diff on the day it
stops covering the repository. It is the same argument ADR 0019 makes about
exemptions, applied to documentation.

Below the top level the check is existence only. Requiring every file in `src/`
to appear would make the map a second copy of the tree, and adding a module
would fail a build over documentation — which is how a rule gets deleted rather
than obeyed.
"""

from __future__ import annotations

import re
import subprocess

import pytest

from conftest import REPO_ROOT

MAP = REPO_ROOT / "docs/14-file-map.md"

#: Everything backticked. Which of those is a *path* is decided below, because
#: the map backticks prose too — `deployed_by`, `required_checks` — and reading
#: those as paths would fail the build over a field name.
_CANDIDATE = re.compile(r"`([^`\s]+)`")

#: Top-level files whose name carries no recognisable extension. Spelled out
#: rather than inferred: a rule that treated every bare word as a filename
#: would read prose as paths, and `.python-version` ends in `-version` rather
#: than `.version`, which is the sort of near-miss a clever rule gets wrong.
_KNOWN_FILES = frozenset({"LICENSE", ".gitignore", ".python-version"})

#: The suffixes the map's paths actually use. An unknown one is not silently
#: dropped — `test_every_tracked_root_entry_is_named` fails on the entry that
#: went unnamed, which is the direction that matters.
_SUFFIXES = (
    ".yaml", ".yml", ".json", ".toml", ".md", ".py", ".sh", ".lock",
    ".txt",
)


def _is_path(token: str) -> bool:
    if token.startswith("http") or " " in token:
        return False
    if token.endswith("/") or "/" in token:
        return True
    return token in _KNOWN_FILES or token.endswith(_SUFFIXES)


def _tracked() -> set[str]:
    out = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files"], capture_output=True, text=True, check=True
    )
    return {line for line in out.stdout.splitlines() if line}


def _named_paths() -> set[str]:
    """Every path the map names, as opposed to every backticked word."""
    return {
        token
        for token in _CANDIDATE.findall(MAP.read_text(encoding="utf-8"))
        if _is_path(token) and not token.startswith("adr/")
    }


def test_the_map_exists_and_is_not_empty() -> None:
    """A glob that matched nothing would pass every test below vacuously."""
    assert MAP.is_file()
    assert len(_named_paths()) > 25, "the map names almost nothing — has it been gutted?"


@pytest.mark.parametrize("path", sorted(_named_paths()))
def test_every_path_the_map_names_exists(path: str) -> None:
    """A renamed file is the ordinary way a map stops being true."""
    stripped = path.rstrip("/")
    if "*" in stripped:
        # `plugins/control-register/skills/gate-*/` — one row for six gates,
        # because naming each would make the map a copy of the tree.
        assert list(REPO_ROOT.glob(stripped)), f"{path} matches nothing"
        return
    target = REPO_ROOT / stripped
    if not target.exists():
        # The map names one file that does not exist yet and says so: the
        # skill-config the plugin proposes upstream. A map that could not
        # mention a proposal would be unable to explain the thing people are
        # most likely to ask about.
        text = MAP.read_text(encoding="utf-8")
        row = next((line for line in text.splitlines() if f"`{path}`" in line), "")
        assert "proposed" in row, f"{path} does not exist and the map does not say so"


def test_every_tracked_root_entry_is_named() -> None:
    """The half that catches an addition rather than a rename.

    Root entries and top-level directories are a bounded set, so this direction
    can be exhaustive here where it could not be deeper in the tree.
    """
    named = _named_paths()
    named_roots = {p.rstrip("/").split("/")[0] for p in named}
    roots = {p.split("/")[0] for p in _tracked()}
    missing = sorted(roots - named_roots)
    assert not missing, (
        f"the file map does not mention: {', '.join(missing)}. A map is an "
        "allow-list — what it leaves out is invisible, so a new top-level entry "
        "has to be named or it is not documented at all."
    )


def test_the_three_files_people_confuse_are_all_named() -> None:
    """The distinction the map exists to draw, asserted rather than assumed.

    These three are separate on purpose and the reasons are subtle enough that
    a well-meaning edit could merge them in prose. If a row disappears, the map
    has lost the thing it was written for.
    """
    text = MAP.read_text(encoding="utf-8")
    for path in ("controls.yaml", "deployment-decisions.yaml", ".claude/skill-config.yaml"):
        assert f"`{path}`" in text, path
    assert "exits 2" in text and "continues" in text, (
        "the map no longer says that the two records fail in opposite directions, "
        "which is the sharpest reason they are not one file"
    )


def test_the_map_says_which_workflow_gates() -> None:
    """Four workflows, one of which decides whether a change can merge.

    Someone new adding a check to the wrong file is the failure this row
    prevents, and `support-floor.yml` and `conformance-sweep.yml` must both be
    named as not gating — a bare list would leave that to be guessed.
    """
    text = MAP.read_text(encoding="utf-8")
    workflows = sorted((REPO_ROOT / ".github/workflows").glob("*.yml"))
    assert workflows, "no workflows found — this test would pass vacuously"
    for workflow in workflows:
        rel = workflow.relative_to(REPO_ROOT).as_posix()
        assert f"`{rel}`" in text, f"{rel} is not in the workflow table"
    assert "required_checks" in text
