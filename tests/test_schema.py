"""Schema validation: a malformed register fails naming the field."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from conftest import REPO_ROOT, minimal_register, write_register
from standard_check.register import load_register


def test_real_register_passes_schema() -> None:
    register, errors = load_register(REPO_ROOT / "controls.yaml")
    assert errors == []
    assert register is not None
    assert len(register.controls) == 13
    assert len(register.meta_controls) == 3


def test_minimal_register_passes(tmp_path: Path) -> None:
    register, errors = load_register(write_register(tmp_path))
    assert errors == []
    assert register is not None


def _errors_for(tmp_path: Path, document: dict[str, Any]) -> list[str]:
    _register, errors = load_register(write_register(tmp_path, document))
    assert errors, "expected schema errors"
    return [str(e) for e in errors]


def test_unknown_file_assert_is_a_schema_error(tmp_path: Path) -> None:
    document = minimal_register(verify=[{"kind": "file", "assert": "definitely_not_real"}])
    errors = _errors_for(tmp_path, document)
    assert any("unknown assert name 'definitely_not_real'" in e for e in errors)
    assert any("verify[0].assert" in e for e in errors)


def test_unknown_command_assert_is_a_schema_error(tmp_path: Path) -> None:
    document = minimal_register(
        verify=[{"kind": "command", "run": "standard-check assert not-a-thing"}]
    )
    errors = _errors_for(tmp_path, document)
    assert any("unknown assert name 'not-a-thing'" in e for e in errors)


def test_missing_required_field_names_the_field(tmp_path: Path) -> None:
    document = minimal_register()
    del document["controls"][0]["owner"]
    errors = _errors_for(tmp_path, document)
    assert any("(SEC-001).owner" in e and "missing" in e for e in errors)


def test_bad_rung_names_the_field(tmp_path: Path) -> None:
    errors = _errors_for(tmp_path, minimal_register(rung="mandatory"))
    assert any("(SEC-001).rung" in e for e in errors)


def test_tier1_with_baseline_path_is_rejected(tmp_path: Path) -> None:
    errors = _errors_for(tmp_path, minimal_register(baseline="baselines/sec.txt"))
    assert any("baseline: null by design" in e for e in errors)


def test_unknown_predicate_reference_is_rejected(tmp_path: Path) -> None:
    errors = _errors_for(tmp_path, minimal_register(applies_to=["rust"]))
    assert any("unknown predicate 'rust'" in e for e in errors)


def test_bad_predicate_expression_is_rejected(tmp_path: Path) -> None:
    document = minimal_register()
    document["predicates"]["weird"] = "the vibes are good"
    errors = _errors_for(tmp_path, document)
    assert any("predicates.weird" in e for e in errors)


def test_missing_adr_file_is_rejected(tmp_path: Path) -> None:
    errors = _errors_for(tmp_path, minimal_register(rationale_adr="docs/adr/none.md"))
    assert any("rationale_adr" in e and "does not exist" in e for e in errors)


def test_non_https_standard_url_is_rejected(tmp_path: Path) -> None:
    errors = _errors_for(
        tmp_path, minimal_register(standard={"name": "X", "url": "ftp://example.com"})
    )
    assert any("standard.url" in e for e in errors)


def test_meta_control_with_rung_is_rejected(tmp_path: Path) -> None:
    document = minimal_register()
    document["meta_controls"][0]["rung"] = "blocking"
    errors = _errors_for(tmp_path, document)
    assert any("meta_controls[0] (GOV-003).rung" in e for e in errors)


def test_duplicate_ids_are_rejected(tmp_path: Path) -> None:
    document = minimal_register()
    document["controls"].append(dict(document["controls"][0]))
    errors = _errors_for(tmp_path, document)
    assert any("duplicate control id 'SEC-001'" in e for e in errors)


def test_unparseable_yaml_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "controls.yaml"
    path.write_text("version: [unclosed", encoding="utf-8")
    register, errors = load_register(path)
    assert register is None
    assert any("not parseable as YAML" in str(e) for e in errors)
