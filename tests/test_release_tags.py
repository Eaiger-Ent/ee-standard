"""The tag an adopter pins the checker to is one this repository cannot move.

ADR 0032 pins the checker to a tag and, from revision 3, says what makes the tag
a pin: `.github/rulesets/release-tags.json`, applied as a ruleset with no
bypass. This holds the record's shape. It cannot see the platform, for the
reason `default-branch.json`'s header gives. What it can catch is the record
and the register drifting apart: a tag form the register adopts that the
ruleset's pattern does not cover would be a pin nothing protects, and every
check here would otherwise still pass.

Not a register control, for the reason the ruleset file gives: the property
belongs to this repository as the checker's publisher.
"""

from __future__ import annotations

import fnmatch
from typing import Any

import yaml

from conftest import REPO_ROOT
from register_check.repo import load_jsonc

RULESET = REPO_ROOT / ".github/rulesets/release-tags.json"


def _ruleset() -> dict[str, Any]:
    loaded = load_jsonc(RULESET)
    assert isinstance(loaded, dict), loaded
    return loaded


def _install_ref() -> str:
    register = yaml.safe_load((REPO_ROOT / "controls.yaml").read_text())
    ref = register["tools"]["register-check"]["install"]["ref"]
    assert isinstance(ref, str)
    return ref


def test_the_ruleset_covers_the_tag_the_register_sends_adopters_to() -> None:
    include = _ruleset()["conditions"]["ref_name"]["include"]
    exclude = _ruleset()["conditions"]["ref_name"]["exclude"]
    ref = f"refs/tags/{_install_ref()}"
    assert any(fnmatch.fnmatchcase(ref, p) for p in include), (ref, include)
    assert not any(fnmatch.fnmatchcase(ref, p) for p in exclude), (ref, exclude)


def test_a_covered_tag_can_be_neither_moved_nor_deleted() -> None:
    ruleset = _ruleset()
    assert ruleset["target"] == "tag"
    assert ruleset["enforcement"] == "active", "evaluate mode records and enforces nothing"
    assert {"update", "deletion"} <= {rule["type"] for rule in ruleset["rules"]}


def test_nobody_bypasses_it() -> None:
    # A bypass for admins would leave the pin as strong as the least careful
    # admin token. ADR 0032 revision 3 records why the cost of none is accepted.
    assert _ruleset()["bypass_actors"] == []


def test_the_record_is_a_payload_github_accepts() -> None:
    # Comments are stripped before it is POSTed, as gate-repo does for the
    # branch ruleset. What remains must be the keys the endpoint takes.
    assert set(_ruleset()) == {
        "name",
        "target",
        "enforcement",
        "conditions",
        "rules",
        "bypass_actors",
    }
