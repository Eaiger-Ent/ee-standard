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


def test_an_assertion_declared_as_a_command_is_rejected(tmp_path: Path) -> None:
    """The `kind:` taxonomy means what it says, from contract 3.

    An in-process assertion declared `kind: command` is what let GOV-001 read it
    as a reachable CI step while the `kind: file` blocks beside it were
    invisible — six controls collapsed to the token `standard-check`, and two
    verified only by file asserts had no token at all.
    """
    document = minimal_register(
        verify=[{"kind": "command", "run": "standard-check assert no-static-cloud-keys"}]
    )
    errors = _errors_for(tmp_path, document)
    assert any("is `kind: file` with an `assert:` name" in e for e in errors)


def test_unknown_assert_name_is_a_schema_error_not_a_skipped_check(tmp_path: Path) -> None:
    """The namespace is closed, and it is one namespace.

    Names from both assert modules resolve, so moving an assertion between them
    is not a register change.
    """
    document = minimal_register(verify=[{"kind": "file", "assert": "not-a-thing"}])
    errors = _errors_for(tmp_path, document)
    assert any("unknown assert name 'not-a-thing'" in e for e in errors)
    # A name that used to be reachable only as a command still resolves.
    _register, ok = load_register(
        write_register(
            tmp_path, minimal_register(verify=[{"kind": "file", "assert": "actions-pinned-to-sha"}])
        )
    )
    assert ok == []


def test_unknown_key_is_rejected(tmp_path: Path) -> None:
    """02-skill-family.md's `pinned`/`floating-minor`/`latest` field is the case.

    It is described in a document, exists in neither the schema nor the
    register, and — while unknown keys were accepted — adding it would have been
    silently ignored rather than rejected.
    """
    errors = _errors_for(tmp_path, minimal_register(version_policy="pinned"))
    assert any("(SEC-001).version_policy" in e and "unknown key" in e for e in errors)


def test_unknown_key_in_a_verify_block_is_rejected(tmp_path: Path) -> None:
    document = minimal_register(
        verify=[{"kind": "file", "assert": "precommit_hook_present", "argz": {"id": "gitleaks"}}]
    )
    errors = _errors_for(tmp_path, document)
    assert any("verify[0].argz" in e and "unknown key" in e for e in errors)


def test_shell_operator_in_run_is_rejected(tmp_path: Path) -> None:
    """`run:` is executed without a shell, so an operator is not an operator.

    `true && false` became `['true', '&&', 'false']` and exited 0, which would
    have let a future `pytest && mypy` silently check only pytest.
    """
    errors = _errors_for(
        tmp_path, minimal_register(verify=[{"kind": "command", "run": "pytest && mypy"}])
    )
    assert any("verify[0].run" in e and "without a shell" in e for e in errors)


def test_justified_variance_is_no_longer_in_the_vocabulary(tmp_path: Path) -> None:
    """Removed at contract 3 as unimplementable.

    00-concepts.md said a justified weakening *is* a baseline entry, and the
    validator rejects any Tier-1 baseline — so the mechanism that stopped it
    becoming a loophole was structurally unreachable for both controls that
    used it.
    """
    errors = _errors_for(tmp_path, minimal_register(variance="justified"))
    assert any("(SEC-001).variance" in e for e in errors)


def test_partial_declaration_requires_an_expiry_and_a_named_gap(tmp_path: Path) -> None:
    """ADR 0017. Without an expiry, "partial" becomes permanent."""
    no_expiry = minimal_register(
        verify=[
            {
                "kind": "file",
                "assert": "precommit_hook_present",
                "args": {"id": "gitleaks"},
                "partial": {"unverified": "the remote half"},
            }
        ]
    )
    assert any("requires an expiry" in e for e in _errors_for(tmp_path, no_expiry))
    no_gap = minimal_register(
        verify=[
            {
                "kind": "file",
                "assert": "precommit_hook_present",
                "args": {"id": "gitleaks"},
                "partial": {"expires": "2027-01-01"},
            }
        ]
    )
    assert any("must name the property" in e for e in _errors_for(tmp_path, no_gap))


def test_also_see_urls_are_validated(tmp_path: Path) -> None:
    """It carried external URLs and was validated by nothing before contract 3."""
    errors = _errors_for(
        tmp_path, minimal_register(also_see=[{"name": "Something", "url": "not-a-url"}])
    )
    assert any("also_see[0].url" in e for e in errors)


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


def test_lockfile_sourced_tool_carries_no_version(tmp_path: Path) -> None:
    """A version beside the lockfile that owns it is the drift being prevented.

    `source: lockfile` means the loci invoke the tool through a package manager,
    so there is no version at any locus to disagree with. Recording one here
    would recreate the copy the source field exists to remove.
    """
    document = minimal_register()
    document["tools"] = {
        "markdownlint-cli2": {
            "source": "lockfile",
            "lockfile": "package-lock.json",
            "version": "0.23.2",
        }
    }
    errors = _errors_for(tmp_path, document)
    assert any("tools.markdownlint-cli2.version" in e for e in errors)


def test_literal_tool_requires_a_version(tmp_path: Path) -> None:
    document = minimal_register()
    document["tools"] = {"gitleaks": {"source": "literal"}}
    assert any("tools.gitleaks.version" in e for e in _errors_for(tmp_path, document))


def test_tool_source_is_a_closed_set(tmp_path: Path) -> None:
    document = minimal_register()
    document["tools"] = {"uv": {"source": "wherever", "version": "1.0.0"}}
    assert any("tools.uv.source" in e for e in _errors_for(tmp_path, document))
