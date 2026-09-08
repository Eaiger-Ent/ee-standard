"""The Craft register's schema, checked by a test rather than by a checker.

[ADR 0053](../docs/adr/0053-the-craft-mapping-is-register-data.md) puts the
Craft mapping in data and says in terms that `register-check` must not validate
it: that checker is the **control** register's, and
[ADR 0018](../docs/adr/0018-register-checker-boundary.md) lets it hold a rule
only where the rule is a property of *that* register's format.
`docs/craft/design.profiles.md` § What checks it — a test, not a second checker
records why a `craft-check` CLI was considered and rejected: an adopter never
reads `craft/`, and the thing an adopter runs is the installer.

So this is the check, and `tests/test_posture.py` is the precedent — that one
fails the build if a *document* stops saying something, which is a larger ask
than a register.

**One test per schema rule**, so a failure names the rule rather than the file.
The last one is the superset test against `docs/craft/assess.rules.md`: it is
what lets that document become a stage record instead of a second source, and
it reads identities out of a markdown table, which is exactly as fragile as it
sounds. That is the point. When somebody edits the table and this breaks, the
register is what they should have edited.
"""

from __future__ import annotations

import re
from typing import Any

import pytest
import yaml

from conftest import REPO_ROOT

CRAFT = REPO_ROOT / "craft"
ASSESS = REPO_ROOT / "docs/craft/assess.rules.md"
CONTROLS = REPO_ROOT / "controls.yaml"

#: A property identity: a scope, a dot, and a lowercase-hyphenated name.
#: `docs/craft/plan.md`'s naming standard, which mints property-first and never
#: keys a row on an upstream rule ID.
IDENTITY = re.compile(r"^(python|react|any)\.[a-z0-9]+(-[a-z0-9]+)*$")

#: The four states a property can be in, and it must be in exactly one. Three of
#: them are ways of having no instrument, and they are not the same thing: a
#: judgement nothing can assert, a property that holds because of a choice made
#: elsewhere, and a property somebody else's surface owns.
NO_INSTRUMENT = ("unenforced", "satisfied_by", "out_of_scope")

#: Who owns a property this register does not write. `profile` is platform state
#: a gate applies through an API; `control` is conformance the register already
#: requires, where writing it here would be Craft claiming credit for it.
OWNERS = ("profile", "control")

#: A single rule code: letters then digits, or a plugin-qualified ESLint name.
#: Anything with a dash in it is a range, which is the spelling the schema
#: forbids because it rots — `DTZ001`-`DTZ012` had already missed `DTZ901`.
RULE_CODE = re.compile(r"^(?:[A-Z]+[0-9]+|[@a-z0-9/.-]+/[a-z0-9-]+)$")

#: The scopes that have a file. A scope with no file yet is outstanding work and
#: `docs/craft/todo.md` is where outstanding work is tracked — never a marker
#: here, which would be a second copy of that list.
SCOPES = ("python", "react", "any")


def _load(name: str) -> dict[str, Any]:
    path = CRAFT / f"{name}.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def _meta() -> dict[str, Any]:
    return _load("meta")


def _present_scopes() -> list[str]:
    return [scope for scope in SCOPES if (CRAFT / f"{scope}.yaml").is_file()]


def _properties() -> dict[str, dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for scope in _present_scopes():
        merged.update(_load(scope)["properties"])
    return merged


def _scope_of(identity: str) -> str:
    return identity.split(".", 1)[0]


def _assess_identities() -> set[str]:
    """Every property `assess.rules.md` names, read from its own tables.

    Bounded to the three stack sections: § Resolved and § Corrected by
    measurement repeat identities, and § Bucket 4 names statements that are
    deliberately not properties.
    """
    text = ASSESS.read_text(encoding="utf-8")
    body = text[text.index("\n## Python\n") : text.index("\n## Bucket 4")]
    return set(re.findall(r"^\| `((?:python|react|any)\.[a-z0-9-]+)` \|", body, re.M))


def test_every_scope_file_parses_and_holds_only_its_own_scope() -> None:
    """The whole reason the register is four files rather than one."""
    for scope in _present_scopes():
        for identity in _load(scope)["properties"]:
            assert _scope_of(identity) == scope, f"{identity} is in {scope}.yaml"


def test_every_identity_matches_the_naming_standard() -> None:
    for identity in _properties():
        assert IDENTITY.match(identity), identity


def test_exactly_one_instrument_per_property() -> None:
    """S3's first hand-forward. C4 measured the double report a second name causes."""
    for identity, prop in _properties().items():
        instrument = prop.get("instrument")
        if instrument is None:
            continue
        assert isinstance(instrument, dict), identity
        assert "tool" in instrument, identity
        # `formatter: true` is the one instrument that names nothing, because
        # running the tool *is* the enforcement — there is no rule to select.
        named = [
            key
            for key in ("codes", "rules", "linter", "setting", "formatter")
            if key in instrument
        ]
        assert named, f"{identity}'s instrument names nothing to enforce"


def test_a_property_is_in_exactly_one_state() -> None:
    """An instrument, or one of the three ways of not having one — never two, never none."""
    for identity, prop in _properties().items():
        states = [key for key in ("instrument", *NO_INSTRUMENT) if key in prop]
        assert len(states) == 1, f"{identity} is in {len(states)} states: {states}"
        if "out_of_scope" in prop:
            assert prop["out_of_scope"] in OWNERS, f"{identity}: {prop['out_of_scope']}"
            assert prop.get("why"), f"{identity} is out of scope and does not say why"
        for key in NO_INSTRUMENT:
            if key in prop:
                assert isinstance(prop[key], str) and prop[key].strip(), f"{identity}: empty {key}"


def test_an_instrument_is_a_closed_set_or_a_linter_and_never_a_range() -> None:
    """S3's second. A range rots, and read widely it over-reaches into contradiction."""
    for identity, prop in _properties().items():
        instrument = prop.get("instrument", {})
        for code in instrument.get("codes", []):
            # A range is spelled with either dash, and the en dash is the one
            # `assess.rules.md` used, so both are rejected by the same pattern.
            assert RULE_CODE.match(code), f"{identity} cites {code!r}, which is not a single code"


def test_a_linter_citation_carries_a_coextensive_reason() -> None:
    """The schema slice's test: an open set needs a reason to be trusted."""
    for identity, prop in _properties().items():
        instrument = prop.get("instrument", {})
        if "linter" in instrument:
            assert instrument.get("coextensive"), f"{identity} cites a linter with no reason"


def test_every_level_is_one_the_meta_file_declares() -> None:
    levels = _meta()["levels"]
    for identity, prop in _properties().items():
        if "level" in prop:
            assert prop["level"] in levels, f"{identity}: {prop['level']}"
        else:
            reasoned = any(key in prop for key in NO_INSTRUMENT)
            assert reasoned, f"{identity} binds no level and gives no reason"


def test_a_property_with_a_level_has_an_instrument_to_carry_it() -> None:
    """A level is a binding, and a binding with nothing to bind is a claim."""
    for identity, prop in _properties().items():
        if "level" in prop:
            assert prop.get("instrument"), f"{identity} binds a level with no instrument"


def test_every_cited_source_resolves_to_a_key_in_meta() -> None:
    """ADR 0054: cite every source. A key that resolves only into prose is not a citation."""
    known = set(_meta()["sources"])
    for identity, prop in _properties().items():
        for citation in prop.get("sources", []):
            key = citation.split()[0]
            assert key in known, f"{identity} cites {key!r}, which meta.yaml does not define"


def test_every_profile_names_a_stack_and_a_level_that_exist() -> None:
    meta = _meta()
    for name, profile in meta["profiles"].items():
        stack, _, level = name.partition("/")
        assert stack in SCOPES and stack != "any", name
        assert level in meta["levels"], name
        assert profile["version"] == max(entry["version"] for entry in profile["changes"])
        for entry in profile["changes"]:
            assert entry["moved"] in {"narrowing", "loosening", "neither"}, name


def test_a_gate_names_a_predicate_defined_in_exactly_one_register() -> None:
    """ADR 0052's evidence gate, and the duplication the design made illegal.

    Two definitions of *is there Terraform here* would eventually disagree about
    a repository and nobody would know which one the profile used.
    """
    control_predicates = set(yaml.safe_load(CONTROLS.read_text(encoding="utf-8"))["predicates"])
    craft_predicates = set(_meta().get("predicates", {}))
    both = control_predicates & craft_predicates
    assert not both, f"predicates defined in both registers: {sorted(both)}"
    known = control_predicates | craft_predicates
    for identity, prop in _properties().items():
        if "gated_on" in prop:
            assert prop["gated_on"] in known, f"{identity} gates on an undefined predicate"


def test_a_candidate_names_a_tool_and_why_it_is_not_bound() -> None:
    """A property with a candidate instrument is unbound *for a stated reason*.

    ADR 0051's third precondition is that S3 has measured it. Nothing
    stack-neutral has been measured, so `candidate:` is how the register says
    what would assert a property without claiming that anything does.
    """
    for identity, prop in _properties().items():
        candidate = prop.get("candidate")
        if candidate is None:
            continue
        assert "instrument" not in prop, f"{identity} has both a candidate and an instrument"
        assert prop.get("unenforced"), f"{identity} has a candidate and no reason it is unbound"
        assert candidate.get("tool"), identity
        assert candidate.get("why_not"), f"{identity}'s candidate does not say why not"


def test_every_row_in_assess_rules_has_a_property_here() -> None:
    """The superset test ADR 0053's open question was closed on.

    One direction only. The register may hold a property `assess.rules.md` does
    not — `python.no-any-anywhere` was minted by S4's strictness slice and has
    no row there — but it may never *lose* one.
    """
    covered = set(_properties())
    scopes = set(_present_scopes())
    owed = {i for i in _assess_identities() if _scope_of(i) in scopes}
    missing = sorted(owed - covered)
    assert not missing, f"{len(missing)} rows have no property in craft/: {missing[:10]}"


@pytest.mark.parametrize("scope", SCOPES)
def test_the_register_is_migrated_scope_by_scope(scope: str) -> None:
    """Which scopes have landed. A scope still owed skips rather than fails.

    `docs/craft/todo.md` is the single list of outstanding work and this is not
    a second copy of it: the test reports what is here, and the todo says what
    is coming.
    """
    if not (CRAFT / f"{scope}.yaml").is_file():
        pytest.skip(f"craft/{scope}.yaml is not migrated yet — see docs/craft/todo.md")
    assert _load(scope)["properties"]
