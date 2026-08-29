"""The drafted submission answers stay in step with the skills they describe.

`/skill-submit-new` asks four questions per skill and commits two files built
from the answers onto the incubator branch. It never reads them from here — so
`docs/promotion/fixtures/` is a draft, and a draft is exactly the kind of thing
that goes quietly wrong: a tenth skill is added, nobody writes its answers, and
the gap is found at the one moment there is no iterate-in-review loop, with
eight other submissions already open.

So the set is derived from the plugin in both directions, the way
`tests/test_skill_links.py` derives the symlinks. A skill with no fixture set
cannot be submitted without writing its answers live; a fixture set naming no
skill is answers for something that no longer exists.

The per-file rules are **the tool's own**, read from `skill-submit-new-qa.md`
and its Step 3, not invented here: at least one slash entry in `should_activate`,
at least two `should_not_activate` entries including at least one slash command,
a Q4 rationale of at least ten words, and the bare slash command first. The one
rule that is this repository's rather than theirs is that `prompt.txt` must be
an entry `triggers.yaml` already lists — the tool derives it from the answers,
so a prompt that appears nowhere in the triggers is a draft that has drifted
from itself.

`disable-model-invocation` is read rather than assumed: Q2 is skipped entirely
for such a skill, so `register-adopt` legitimately carries no natural-language
entry and the other eight legitimately do.
"""

from __future__ import annotations

import re

import pytest

from conftest import REPO_ROOT

FIXTURES = REPO_ROOT / "docs/promotion/fixtures"
SKILLS_DIR = REPO_ROOT / "plugins/control-register/skills"

SKILL_NAMES = sorted(p.name for p in SKILLS_DIR.iterdir() if p.is_dir())

#: `- "…"` under one of the two keys. Parsed with a regex rather than a YAML
#: loader because what is checked is the file the tool will be handed, quoting
#: included, and a loader would silently accept a shape the tool's own reader
#: might not.
_ENTRY = re.compile(r'^  - "(.+)"$')


def _entries(name: str, key: str) -> list[str]:
    text = (FIXTURES / name / "triggers.yaml").read_text(encoding="utf-8")
    section = text.split(f"{key}:\n", 1)
    assert len(section) == 2, f"{name}/triggers.yaml has no {key}: block"
    out = []
    for line in section[1].splitlines():
        match = _ENTRY.match(line)
        if match is None:
            break
        out.append(match.group(1))
    return out


def _skill_body(name: str) -> str:
    return (SKILLS_DIR / name / "SKILL.md").read_text(encoding="utf-8")


def test_the_plugin_has_skills_to_draft_for() -> None:
    """A glob that matched nothing would pass every parametrised test vacuously."""
    assert len(SKILL_NAMES) >= 9, SKILL_NAMES


def test_no_fixture_set_names_a_skill_that_is_gone() -> None:
    drafted = {p.name for p in FIXTURES.iterdir() if p.is_dir()}
    assert drafted <= set(SKILL_NAMES), sorted(drafted - set(SKILL_NAMES))


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_every_skill_has_a_complete_fixture_set(name: str) -> None:
    for filename in ("triggers.yaml", "prompt.txt", "rationale.txt"):
        path = FIXTURES / name / filename
        assert path.is_file(), f"{name} has no drafted {filename}"
        assert path.read_text(encoding="utf-8").strip(), f"{name}/{filename} is empty"


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_the_bare_slash_command_is_the_first_entry(name: str) -> None:
    """The tool's Step 3: "bare slash command always first"."""
    activate = _entries(name, "should_activate")
    assert activate, f"{name} activates on nothing"
    assert activate[0] == f"/{name}", activate[0]


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_q3_offers_a_sibling_command_that_must_not_activate(name: str) -> None:
    """Q1 and Q3's validation, which the tool re-asks until it is satisfied."""
    negative = _entries(name, "should_not_activate")
    assert len(negative) >= 2, negative
    slashes = [entry for entry in negative if entry.startswith("/")]
    assert slashes, f"{name} names no other slash command that must not activate"
    assert f"/{name}" not in negative, f"{name} both must and must not activate"


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_natural_language_entries_track_the_invocation_flag(name: str) -> None:
    """Q2 is skipped entirely for a skill the model may not invoke."""
    prose = [e for e in _entries(name, "should_activate") if not e.startswith("/")]
    disabled = "disable-model-invocation: true" in _skill_body(name)
    if disabled:
        assert not prose, f"{name} may not be model-invoked, so Q2 is not asked: {prose}"
    else:
        assert len(prose) >= 2, f"{name} needs at least two natural-language triggers"


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_the_smoke_test_prompt_is_one_of_the_drafted_triggers(name: str) -> None:
    prompt = (FIXTURES / name / "prompt.txt").read_text(encoding="utf-8").strip()
    assert prompt in _entries(name, "should_activate"), prompt


@pytest.mark.parametrize("name", SKILL_NAMES)
def test_the_rationale_answers_q4(name: str) -> None:
    """Q4's validation is ten words; a one-liner is re-asked rather than accepted."""
    rationale = (FIXTURES / name / "rationale.txt").read_text(encoding="utf-8")
    assert len(rationale.split()) >= 10, rationale
