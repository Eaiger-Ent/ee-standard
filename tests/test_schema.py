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


def test_literal_tool_requires_the_loci_that_repeat_its_version(tmp_path: Path) -> None:
    """§ H2. A literal tool with no loci is a tool nothing compares.

    Required rather than optional because an empty list and a missing one are
    indistinguishable from a tool nobody pins, and "nothing was compared"
    reading as a pass is the § A defect this field was moved out of the checker
    to stop.
    """
    document = minimal_register()
    document["tools"] = {"gitleaks": {"source": "literal", "version": "8.30.1"}}
    assert any("tools.gitleaks.pinned_at" in e for e in _errors_for(tmp_path, document))


def test_lockfile_sourced_tool_carries_no_loci(tmp_path: Path) -> None:
    """The mirror of the version rule: no repetitions, so nothing to list."""
    document = minimal_register()
    document["tools"] = {
        "markdownlint-cli2": {
            "source": "lockfile",
            "lockfile": "package-lock.json",
            "pinned_at": [".github/workflows/lint.yml"],
        }
    }
    errors = _errors_for(tmp_path, document)
    assert any("tools.markdownlint-cli2.pinned_at" in e for e in errors)


def test_toolchain_sourced_tool_carries_no_version(tmp_path: Path) -> None:
    """The lockfile rule, one source over: the file is the authority (ADR 0027).

    A number beside the file that owns it is the same second copy, and it is the
    one that would go stale silently — the loci would keep reading the file and
    agreeing with each other while the register disagreed with all of them.
    """
    document = minimal_register()
    document["tools"] = {
        "python": {
            "source": "toolchain",
            "toolchain": ".python-version",
            "invocation": "uv run",
            "version": "3.13",
        }
    }
    assert any("tools.python.version" in e for e in _errors_for(tmp_path, document))


def test_toolchain_sourced_tool_names_its_file(tmp_path: Path) -> None:
    """Without the path there is no authority, only a claim that one exists."""
    document = minimal_register()
    document["tools"] = {"python": {"source": "toolchain", "invocation": "uv run"}}
    assert any("tools.python.toolchain" in e for e in _errors_for(tmp_path, document))


def test_toolchain_sourced_tool_carries_no_loci(tmp_path: Path) -> None:
    """Nothing repeats the value — that is the whole reason for the source."""
    document = minimal_register()
    document["tools"] = {
        "python": {
            "source": "toolchain",
            "toolchain": ".python-version",
            "invocation": "uv run",
            "pinned_at": [".devcontainer/devcontainer.json"],
        }
    }
    assert any("tools.python.pinned_at" in e for e in _errors_for(tmp_path, document))


def test_toolchain_sourced_tool_records_how_a_locus_reaches_it(tmp_path: Path) -> None:
    """ADR 0020's requirement, carried across: an authority no invocation
    resolves to is not an authority. `.python-version` selects nothing on its
    own — uv is what reads it, and a locus running `python3` gets the system
    interpreter regardless of what the file says.
    """
    document = minimal_register()
    document["tools"] = {"python": {"source": "toolchain", "toolchain": ".python-version"}}
    assert any("tools.python.invocation" in e for e in _errors_for(tmp_path, document))


def test_only_a_toolchain_sourced_tool_names_a_toolchain_file(tmp_path: Path) -> None:
    document = minimal_register()
    document["tools"] = {
        "gitleaks": {
            "source": "literal",
            "version": "8.30.1",
            "pinned_at": [".devcontainer/setup.sh"],
            "toolchain": ".python-version",
        }
    }
    assert any("tools.gitleaks.toolchain" in e for e in _errors_for(tmp_path, document))


def test_a_toolchain_file_is_not_a_lockfile(tmp_path: Path) -> None:
    """The two are distinguished because no package manager produced the one —
    which is the fact that makes the third source value necessary rather than a
    synonym for the second.
    """
    document = minimal_register()
    document["tools"] = {
        "python": {
            "source": "toolchain",
            "toolchain": ".python-version",
            "lockfile": "uv.lock",
            "invocation": "uv run",
        }
    }
    assert any("tools.python.lockfile" in e for e in _errors_for(tmp_path, document))


def test_an_uncompilable_frozen_install_pattern_is_a_schema_error(tmp_path: Path) -> None:
    """Compiled at schema time, like `suppression`, and for the same reason.

    A pattern that does not parse would otherwise surface as a crash in the
    middle of a run, and one that parses but matches nothing is a control
    passing vacuously — which is § H3.
    """
    document = minimal_register()
    document["ecosystems"] = {
        "python": {
            "manifest": ["pyproject.toml"],
            "lockfiles": ["uv.lock"],
            "dependabot": ["uv"],
            "test_commands": ["pytest"],
            "frozen_install": ["uv sync ("],
        }
    }
    errors = _errors_for(tmp_path, document)
    assert any("ecosystems.python.frozen_install[0]" in e for e in errors)


def test_an_ecosystem_without_frozen_install_is_a_schema_error(tmp_path: Path) -> None:
    document = minimal_register()
    document["ecosystems"] = {
        "python": {
            "manifest": ["pyproject.toml"],
            "lockfiles": ["uv.lock"],
            "dependabot": ["uv"],
            "test_commands": ["pytest"],
        }
    }
    errors = _errors_for(tmp_path, document)
    assert any("ecosystems.python.frozen_install" in e for e in errors)


def test_an_empty_cloud_credential_list_is_a_schema_error(tmp_path: Path) -> None:
    """A control that looks for nothing passes everything (§ H4)."""
    document = minimal_register()
    document["cloud_credentials"] = []
    assert any("cloud_credentials" in e for e in _errors_for(tmp_path, document))


def test_a_control_may_not_verify_by_meta_self_invocation(tmp_path: Path) -> None:
    """§ H5. The exception is bounded, or it is a hole.

    `standard-check meta GOV-NNN` is the one in-process assertion the taxonomy
    admits as a command, because a meta-control's three-valued Verdict has no
    `kind: file` spelling. A *control* using it would be § E again — in the
    branch GOV-001 actually reads.
    """
    document = minimal_register(
        verify=[{"kind": "command", "run": "standard-check meta GOV-003"}]
    )
    errors = _errors_for(tmp_path, document)
    assert any("only a meta-control may verify itself" in e for e in errors), errors


def test_a_meta_control_may_not_run_another_meta_controls_check(tmp_path: Path) -> None:
    """Rendering GOV-002's verdict under GOV-003's name is a miscategorisation too."""
    document = minimal_register()
    document["meta_controls"][0]["verify"] = [
        {"kind": "command", "run": "standard-check meta GOV-002"}
    ]
    errors = _errors_for(tmp_path, document)
    assert any("a meta-control verifies itself" in e for e in errors), errors


def test_a_meta_control_may_verify_itself(tmp_path: Path) -> None:
    """The mirror: the register as it stands uses exactly this shape."""
    _register, errors = load_register(write_register(tmp_path, minimal_register()))
    assert errors == [], errors


def test_a_block_predicate_must_narrow_its_control_not_widen_it(tmp_path: Path) -> None:
    """A block naming a predicate its control lacks can never run.

    The control is skipped before the block is reached, so the verification is
    declared and unreachable — theme T-3 in the one file written to stop it.
    """
    document = minimal_register(
        applies_to=["always"],
        verify=[
            {
                "kind": "file",
                "assert": "precommit_hook_present",
                "args": {"id": "gitleaks"},
                "applies_to": ["python"],
            }
        ],
    )
    register, errors = load_register(write_register(tmp_path, document))
    assert register is None
    assert any("could never run" in e.message for e in errors), errors


def test_a_block_predicate_must_be_a_known_predicate(tmp_path: Path) -> None:
    document = minimal_register(
        verify=[
            {
                "kind": "file",
                "assert": "precommit_hook_present",
                "args": {"id": "gitleaks"},
                "applies_to": ["kotlin"],
            }
        ],
    )
    register, errors = load_register(write_register(tmp_path, document))
    assert register is None
    assert any("names no predicate" in e.message for e in errors), errors
