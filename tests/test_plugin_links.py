"""A link inside the plugin resolves wherever the plugin is installed.

A plugin is copied into its own install cache, so a relative link that walks out
of it — `../../../../docs/adr/0035-….md` — resolves in this repository and
dangles in every installation. `docs/` is not shipped and never will be.

[ADR 0036](../docs/adr/0036-shared-skill-prose-has-one-home.md) already made
this argument about the two shared reference files, which cite it in prose
rather than by link for exactly this reason. It was never applied to the skills
themselves, and twenty-three such links reached nine of them.

Nothing here noticed. It was found by the **destination's** gate:
`ee-skills-incubator`'s `scripts/check-path-hygiene.sh` forbids `../` anywhere
under `skills/`, and the first assembly of the submission bundle failed it in
eleven files. A gate somebody else runs is a poor place to learn this, because
it is the one moment there is no undo — so the rule is held here now.

The replacement is a **prose citation** — `ADR 0035`, not a link — which is what
ADR 0036's own reference files do. A public `https` URL was tried first and is
the wrong answer here: `tests/test_register_install.py` forbids the address in
`tools.register-check.install.repository` from appearing in a skill's files at
all, because a skill must read it from the register at run time or not at all,
and a citation is not worth carving an exception into that rule for.

Both directions are checked. A citation that names an ADR this repository does
not have is the mirror failure — a reference the reader cannot follow *and*
cannot verify — and `docs/adr/archive/` counts, because an archived ADR is still
a decision that was taken.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from conftest import REPO_ROOT

PLUGIN = REPO_ROOT / "plugins/control-register"
ADR_DIRS = (REPO_ROOT / "docs/adr", REPO_ROOT / "docs/adr/archive")

MARKDOWN = sorted(PLUGIN.rglob("*.md"))

#: A markdown link whose target starts by walking up out of its own directory.
_ESCAPING = re.compile(r"\]\(((?:\.\./)+[^)]*)\)")

#: A prose citation of a decision — `ADR 0035`. Four digits, so a version number
#: or a control id cannot be read as one.
_CITATION = re.compile(r"\bADR (\d{4})\b")


def test_the_plugin_ships_markdown_to_check() -> None:
    assert len(MARKDOWN) >= 9, MARKDOWN


@pytest.mark.parametrize("path", MARKDOWN, ids=lambda p: str(p.relative_to(PLUGIN)))
def test_no_link_walks_out_of_the_plugin(path: Path) -> None:
    escaping = _ESCAPING.findall(path.read_text(encoding="utf-8"))
    assert not escaping, (
        f"{path.relative_to(REPO_ROOT)} links to {escaping} by walking out of the plugin. "
        "Cite it in prose instead — the plugin is copied into an install cache and "
        "docs/ does not go with it."
    )


#: A repository path named in prose — `docs/02-skill-family.md`, in backticks.
#: The plugin cites these deliberately: `docs/` is not shipped, so a reader
#: follows one in the standard's repository rather than in their install.
_DOCS_PATH = re.compile(r"`(docs/[A-Za-z0-9._/-]+\.md)`")


@pytest.mark.parametrize("path", MARKDOWN, ids=lambda p: str(p.relative_to(PLUGIN)))
def test_every_repository_path_the_plugin_names_exists(path: Path) -> None:
    """A pointer to a document nobody wrote reads exactly like a working one.

    Nine skills sent a reader to `docs/skill-relationship-map.md`, which has
    never existed in this repository. The registry it meant is
    `docs/02-skill-family.md`. It survived because the sentence is copied into
    every skill and read by nobody: the link-shape rule beside this one forbids
    walking out of the plugin, and a **prose** path walks nowhere to check.

    Unlike the ADR citations above, this cannot be satisfied by naming a
    decision — a document either exists or it does not, and the reader who
    follows one that does not gets no second guess.
    """
    text = path.read_text(encoding="utf-8")
    missing = sorted({m for m in _DOCS_PATH.findall(text) if not (REPO_ROOT / m).is_file()})
    assert not missing, (
        f"{path.relative_to(PLUGIN)} sends a reader to a document this repository "
        f"does not have: "
        f"{', '.join(missing)}"
    )


@pytest.mark.parametrize("path", MARKDOWN, ids=lambda p: str(p.relative_to(PLUGIN)))
def test_every_citation_names_a_decision_that_exists(path: Path) -> None:
    for number in _CITATION.findall(path.read_text(encoding="utf-8")):
        assert any(
            any(d.glob(f"{number}-*.md")) for d in ADR_DIRS
        ), f"{path.relative_to(REPO_ROOT)} cites ADR {number}, which this repository does not have"
