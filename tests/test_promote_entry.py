"""The consolidated `promote-config.json` entry is derived from the plugin.

`/skill-submit-new` writes `"<name>": {"skills": ["<name>"], …}` on every branch
it builds, so the default outcome of submitting nine skills is nine single-skill
plugins. The entry that says otherwise has to be carried, identically, on nine
branches — and until 2026-08-28 the only copy of it in this repository was an
ellipsis, `"control-register": {"skills": [ … ]}`, which is not text anyone can
paste.

Writing it out makes it a second copy of two things the plugin already states:
which skills it ships, and what it is. So neither is typed twice. The skill list
is read from `plugins/control-register/skills/` and the description from
`.claude-plugin/plugin.json`, and a tenth skill or a reworded description fails
here rather than being discovered as a wrong `promote-config.json` on someone
else's branch.

The **set** is compared, not the order. The document orders the skills as the
dispatcher, the six gates it dispatches, then the two on nobody's route, which is
presentation; a rule about it would fail a build over a preference.
"""

from __future__ import annotations

import json
import re
from typing import Any

from conftest import REPO_ROOT

DOC = REPO_ROOT / "docs/05-promotion.md"
PLUGIN = REPO_ROOT / "plugins/control-register"

#: The one fenced block in the document that opens with the entry's key. Anchored
#: on the key rather than on "the first json block", because the document holds a
#: second one — the `governance` category — and position is not identity.
_BLOCK = re.compile(
    r'```json\n(\s*"control-register":\s*\{.*?)\n```',
    re.DOTALL,
)


def _entry() -> dict[str, Any]:
    match = _BLOCK.search(DOC.read_text())
    assert match, "no `control-register` promote-config block in docs/05-promotion.md"
    # A JSON object *member*, which is what gets pasted under `plugins`. Braced
    # to parse; parsed rather than regexed so a malformed entry fails here and
    # not on a branch in the incubator.
    entry = json.loads("{" + match.group(1) + "}")["control-register"]
    assert isinstance(entry, dict), entry
    return entry


def _skills() -> list[str]:
    skills = _entry()["skills"]
    assert isinstance(skills, list) and all(isinstance(s, str) for s in skills), skills
    return skills


def test_the_entry_names_every_skill_the_plugin_ships() -> None:
    shipped = {p.name for p in (PLUGIN / "skills").iterdir() if p.is_dir()}
    assert shipped, "the plugin ships no skills; the comparison below would be vacuous"
    assert set(_skills()) == shipped


def test_the_entry_names_each_skill_once() -> None:
    skills = _skills()
    assert len(skills) == len(set(skills)), skills


def test_the_entry_carries_the_plugin_s_own_description() -> None:
    manifest = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text())
    assert _entry()["description"] == manifest["description"]
