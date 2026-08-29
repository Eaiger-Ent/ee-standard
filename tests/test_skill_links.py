"""The plugin's skills are reachable where the submission tool looks for them.

[ADR 0033](../docs/adr/0033-the-submission-tool-reaches-the-skills-by-symlink.md)
exposes each skill at `.claude/skills/<name>` as a symlink into
`plugins/control-register/skills/<name>`, because `/skill-submit-new` resolves
`<name>/SKILL.md` in the project's Claude skills directory and this repository
uses the marketplace's plugin layout instead.

The failure this file exists to catch is a **tenth skill added without a link**.
Nothing would break: the plugin tests would pass, the preflight would pass, and
the skill would simply be invisible to the tool — discovered at submission time,
when the operator expected a pull-request URL and got a "skill not found" from
someone else's script.

The link set is therefore derived from the plugin in both directions. A skill
with no link cannot be submitted; a link with no skill is a `/name` that resolves
to nothing. Neither is more likely than the other, so neither is the one to check.

`LICENSE` is checked here too, for a related reason rather than an unrelated one:
both are things a submission needs that no control requires, so nothing else in
this repository would notice their absence.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import REPO_ROOT

PLUGIN = REPO_ROOT / "plugins/control-register"
SKILLS_DIR = PLUGIN / "skills"
LINKS_DIR = REPO_ROOT / ".claude/skills"

SKILL_NAMES = sorted(p.name for p in SKILLS_DIR.iterdir() if p.is_dir())


def test_the_plugin_has_skills_to_link() -> None:
    """A glob that matched nothing would pass every parametrised test vacuously."""
    assert len(SKILL_NAMES) >= 8, SKILL_NAMES


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_every_skill_is_reachable_where_the_submission_tool_looks(name: str) -> None:
    """The direction that fails silently: a new skill nobody linked.

    `/skill-submit-new` resolves `<name>/SKILL.md` in the project Claude skills
    directory. A skill absent from it is one the tool reports as not found —
    and the natural response to that, at submission time, is to copy the file,
    which is the second copy ADR 0033 rejected.
    """
    link = LINKS_DIR / name
    assert link.is_symlink(), (
        f".claude/skills/{name} is not a symlink. Create it with "
        f"`ln -s ../../plugins/control-register/skills/{name} .claude/skills/{name}` "
        "(ADR 0033) — a copy would be a second definition of the skill."
    )
    target = str(link.readlink())
    assert target == f"../../plugins/control-register/skills/{name}", (
        f".claude/skills/{name} points at {target!r}, which is not its own skill"
    )
    assert (link / "SKILL.md").is_file(), f".claude/skills/{name} dangles"


@pytest.mark.parametrize(
    "link", sorted(LINKS_DIR.iterdir()) if LINKS_DIR.is_dir() else [], ids=lambda p: p.name
)
def test_every_link_names_a_skill_that_exists(link: Path) -> None:
    """The other direction: a `/name` that resolves to nothing.

    A renamed skill leaves a link behind, and a link that dangles is worse than
    an absent one — it is a command that exists and does not work.
    """
    assert link.name in SKILL_NAMES, (
        f".claude/skills/{link.name} names no skill in the plugin — a leftover from a rename"
    )


def test_the_links_are_symlinks_in_git_and_not_files() -> None:
    """The Windows-checkout case ADR 0033 § Consequences records as a stated cost.

    Git writes a symlink as a plain text file containing the target path where
    `core.symlinks` is off. What arrives then is eight files whose contents are
    relative paths, and a submission built from one of those describes nothing.
    Failing here is the right outcome, and this says why in the message.
    """
    for name in SKILL_NAMES:
        link = LINKS_DIR / name
        assert not (link.is_file() and not link.is_symlink()), (
            f".claude/skills/{name} is a regular file, not a symlink. On Windows git "
            "writes symlinks as text files unless core.symlinks is on — this checkout "
            "cannot submit skills, and would submit their target paths instead."
        )


def test_the_plugin_ships_a_licence_and_it_is_the_repository_s() -> None:
    """`check_plugin_license.py` fails a plugin without one, and there was none.

    Each plugin is copied independently into a Claude Code install cache, so a
    single root `LICENSE` does not follow it — which is why the marketplace
    requires a copy per plugin rather than treating the root one as sufficient.
    Held byte-identical here because two licences that disagree is a worse
    problem than one that is missing.
    """
    root = REPO_ROOT / "LICENSE"
    plugin = PLUGIN / "LICENSE"
    assert root.is_file(), (
        "the repository declares Apache-2.0 in pyproject.toml and ships no LICENSE"
    )
    assert plugin.is_file(), (
        "plugins/control-register/LICENSE is missing — check_plugin_license.py fails the "
        "submission without it, and the plugin is copied without the repository root"
    )
    assert root.read_bytes() == plugin.read_bytes(), (
        "the plugin's LICENSE differs from the repository's. Copy the root one; two "
        "licences that disagree is worse than one that is absent"
    )
    assert "Apache License" in root.read_text(encoding="utf-8")
    text = root.read_text(encoding="utf-8")
    assert "[name of copyright owner]" not in text, (
        "the copyright placeholder is unfilled — the appendix is an instruction, and a "
        "shipped licence that still carries it names no owner"
    )
