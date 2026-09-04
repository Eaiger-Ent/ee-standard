"""Prose several skills must follow has one home, and the skills point at it.

[ADR 0036](../docs/adr/0036-shared-skill-prose-has-one-home.md) moved two
normative sections out of the skills that had pasted them — seven copies of the
write narration, five of the pre-commit runner check — into
`plugins/control-register/reference/`, read at runtime through
`${CLAUDE_PLUGIN_ROOT}`.

Two failures are checked, and they are not the same failure.

A **pointer to a file that is not there** is a skill that reads nothing and
carries on. Preflight P8 catches it too, but P8 ships in `ee-skills` and cannot
run in this repository's CI, so the plugin's own tests hold it as well.

A **skill that re-inlines a shared section** is the failure ADR 0036 exists to
prevent, and it is the one nothing else would see: the skill would be correct,
self-contained and longer, and the rule would have two homes again. Detected by
the heading rather than by comparing text, because a copy that has already
drifted is still a copy — and drift is what makes it worth catching.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from conftest import REPO_ROOT

PLUGIN = REPO_ROOT / "plugins/control-register"
REFERENCE = PLUGIN / "reference"
SKILLS = sorted(p for p in (PLUGIN / "skills").iterdir() if p.is_dir())

#: The heading each shared file owns, as it reads in the file's own H1. A skill
#: whose SKILL.md carries one of these as a section body rather than a pointer
#: has taken the copy back.
SHARED_HEADINGS = {
    "plan-limits.md": "When the platform refuses on the plan, not the token",
    "pre-commit-runner.md": "Before you write a pre-commit hook, make sure something runs it",
    "unattended.md": "Running without being asked the same question again",
    "write-narration.md": "Say what each write is for, before you make it",
}

REF_PATTERN = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/reference/([A-Za-z0-9._-]+)")


def _skill_text(skill: Path) -> str:
    return (skill / "SKILL.md").read_text(encoding="utf-8")


def test_the_reference_directory_has_files_to_check() -> None:
    """A glob that matched nothing would pass every test below vacuously."""
    assert sorted(p.name for p in REFERENCE.glob("*.md")) == sorted(SHARED_HEADINGS)


@pytest.mark.parametrize("name,heading", sorted(SHARED_HEADINGS.items()))
def test_each_shared_file_states_the_rule_it_owns(name: str, heading: str) -> None:
    """The file is the home of the rule, so its own title says which rule."""
    text = (REFERENCE / name).read_text(encoding="utf-8")
    assert text.startswith(f"# {heading}\n"), f"{name}: H1 is not the rule it owns"
    assert "ADR 0036" in text, f"{name}: does not say where the decision to move it is recorded"
    assert "](../" not in text, (
        f"{name}: cites something outside the plugin by relative link. `docs/` is not "
        "shipped, so the link resolves here and dangles in every installation"
    )


@pytest.mark.parametrize("skill", SKILLS, ids=lambda p: p.name)
def test_every_reference_a_skill_points_at_exists(skill: Path) -> None:
    missing = sorted(
        name for name in REF_PATTERN.findall(_skill_text(skill)) if not (REFERENCE / name).is_file()
    )
    assert not missing, (
        f"{skill.name}: points at {', '.join(missing)}, which the plugin does not ship"
    )


@pytest.mark.parametrize("skill", SKILLS, ids=lambda p: p.name)
def test_no_skill_takes_a_shared_section_back(skill: Path) -> None:
    """A pointer is a heading and a paragraph; a copy is the whole rule again.

    The pointer keeps the shared heading — it is the right name for the section
    — so presence cannot be the test. What separates them is that a pointer
    names the file it defers to, in the section itself.
    """
    text = _skill_text(skill)
    lines = text.splitlines()
    for name, heading in SHARED_HEADINGS.items():
        start = next((i for i, line in enumerate(lines) if line == f"## {heading}"), None)
        if start is None:
            continue
        end = next(
            (i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines)
        )
        section = "\n".join(lines[start:end])
        assert f"${{CLAUDE_PLUGIN_ROOT}}/reference/{name}" in section, (
            f"{skill.name}: carries the '{heading}' section without deferring to "
            f"reference/{name} — the rule has two homes again (ADR 0036)"
        )


@pytest.mark.parametrize("skill", SKILLS, ids=lambda p: p.name)
def test_the_skill_says_what_each_write_is_for(skill: Path) -> None:
    """A permission prompt is a diff and nothing else.

    Phase 4's live adoption run produced a stream of them — `.pre-commit-config.yaml`,
    `setup.sh`, a workflow — with no control named, no step of how many, and no
    statement of what would check the result. The operator's words: *"nothing is
    explaining what test has passed or failed or why the update is needed"*.

    Nothing has failed at that point and nothing has passed: a gate deploys
    first and verifies last, which is the right order and means the approver is
    asked to accept a change on trust unless the reason comes first. The
    provenance stamp does name the control, and arrives buried in the middle of
    the change it is explaining.

    `register-adopt` is exempt: it writes no artefacts of its own, which is why
    it ships no templates either.

    This test lived in `test_plugin.py` and asserted the narration shape inside
    every SKILL.md, which is how seven copies of it came to be there. It asks
    the same question of a different place: the skill must reach the rule, and
    the rule must still carry the shape.
    """
    if skill.name == "register-adopt":
        return
    assert "${CLAUDE_PLUGIN_ROOT}/reference/write-narration.md" in _skill_text(skill), (
        f"{skill.name} may write files without saying why. Point at the narration "
        "rule — one line before every write, naming the control, the step, and "
        "what verifies it."
    )


def test_the_narration_rule_still_gives_the_shape() -> None:
    """The half of the test above that the skills no longer hold."""
    text = (REFERENCE / "write-narration.md").read_text(encoding="utf-8")
    for required in ("what it does:", "why now:", "verified by:"):
        assert required in text, f"the narration shape is missing `{required}`"


@pytest.mark.parametrize("skill", SKILLS, ids=lambda p: p.name)
def test_a_gate_that_writes_a_hook_makes_sure_something_runs_it(skill: Path) -> None:
    """A hook in the config is intent; the runner is whether anything happens.

    Five gates write into `.pre-commit-config.yaml`. Until Phase 4 none of them
    installed the thing that reads it, so the consumer repository finished its
    adoption with every gate reporting its `pre-commit` locus wired, no
    `pre-commit` in the project, no `.git/hooks/pre-commit`, and a deliberately
    malformed commit sailing through. The checker reported the locus wired the
    whole time, because it reads the config file — which is the right thing for
    it to read and not the same claim.
    """
    text = _skill_text(skill)
    if ".pre-commit-config" not in text or skill.name == "register-adopt":
        return
    assert "${CLAUDE_PLUGIN_ROOT}/reference/pre-commit-runner.md" in text, (
        f"{skill.name} writes a pre-commit hook without making sure the runner "
        "is a dependency and the git hook is installed"
    )


def test_the_runner_rule_still_gives_the_two_checks() -> None:
    """The half of the test above that the skills no longer hold."""
    text = (REFERENCE / "pre-commit-runner.md").read_text(encoding="utf-8")
    assert "add_dev_dependency" in text, "the runner rule does not say how to add pre-commit"
    assert ".git/hooks/pre-commit" in text, "the runner rule does not check the installed hook"
