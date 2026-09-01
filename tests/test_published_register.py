"""The register an adopter fetches does not describe this repository (ADR 0048).

`controls.yaml` is two documents. The first `/register-adopt` on a repository
nobody here owns found the seam: `tools.uv.pinned_at` shipped two of *our*
workflow paths, so SUP-001 failed on files that repository was never going to
have, and `CI-001.required_checks` shipped *our* job ids, so `gate-repo` refused
to create a ruleset requiring a `lint-md` check nothing there produces.

Refusing was right — GitHub waits forever for a check nothing reports — which is
what makes this a register defect rather than a gate one.

The three rules below are ADR 0048's, and the third is the one that would have
caught `support-floor.yml` the day it was added rather than at somebody else's
adoption.
"""

from __future__ import annotations

import json

import pytest
import yaml

from conftest import REPO_ROOT
from register_check.publish import (
    MARKABLE_FIELDS,
    PUBLISHED,
    derive,
    field_of,
    local_only_lines,
)

SOURCE_TEXT = (REPO_ROOT / "controls.yaml").read_text(encoding="utf-8")
PUBLISHED_PATH = REPO_ROOT / PUBLISHED


def test_the_published_register_is_current() -> None:
    """Generated and committed, like a lock file — so a reader of the tag gets
    what the source says, and a stale one is a build failure rather than a
    surprise at somebody's first adoption."""
    assert PUBLISHED_PATH.is_file(), f"{PUBLISHED} has never been generated"
    assert PUBLISHED_PATH.read_text(encoding="utf-8") == derive(SOURCE_TEXT), (
        f"{PUBLISHED} is stale — run `register-check publish` and commit the result"
    )


def test_the_published_register_is_valid_yaml_and_still_a_register() -> None:
    """ADR 0048 rule 2. A derivation that removes a required value produces a
    file that loads and means something else."""
    published = yaml.safe_load(PUBLISHED_PATH.read_text(encoding="utf-8"))
    source = yaml.safe_load(SOURCE_TEXT)
    assert published["version"] == source["version"]
    assert len(published["controls"]) == len(source["controls"])
    assert published["meta"]["register_contract"] == source["meta"]["register_contract"]


def test_no_required_checks_list_became_empty() -> None:
    """Rule 2's sharp edge. A `required_status_checks` rule naming no context
    requires no check, so a pull request merges with CI red while the control
    reports satisfied — register contract 19 added the field for exactly that.
    """
    published = yaml.safe_load(PUBLISHED_PATH.read_text(encoding="utf-8"))
    for control in published["controls"]:
        for block in control.get("verify", []):
            checks = block.get("args", {}).get("required_checks")
            if checks is not None:
                assert checks, (
                    f"{control['id']}: publishing emptied required_checks — a ruleset "
                    "requiring nothing is worse than no ruleset, because it reports as one"
                )


@pytest.mark.parametrize(
    ("line_number", "line"), local_only_lines(SOURCE_TEXT), ids=lambda v: str(v)[:40]
)
def test_a_marker_only_appears_on_a_repository_specific_field(
    line_number: int, line: str
) -> None:
    """ADR 0048 rule 1.

    `rung`, `verify`, `variance`, `applies_to` and `tier` are what conformant
    *means*. A marker on one of them would publish a policy other than the one
    enforced here, which is the one thing this mechanism must never be able to do.
    """
    field = field_of(SOURCE_TEXT, line_number)
    assert field in MARKABLE_FIELDS, (
        f"line {line_number} is marked local-only under {field!r}, which is not a "
        f"repository-specific field. Markable: {sorted(MARKABLE_FIELDS)}"
    )


def _creatable_paths() -> set[str]:
    """Every path the standard's own artefacts put in an adopter's repository."""
    plugin = REPO_ROOT / "plugins/control-register"
    gates = json.loads((plugin / ".claude-plugin/deploys.json").read_text())["gates"]
    from_gates = {
        artefact.split("#")[0]
        for gate in gates.values()
        for artefact in gate["artifacts"]
    }
    from_template = {
        f".devcontainer/{p.name}"
        for p in (plugin / "templates/devcontainer").iterdir()
        if p.is_file() and p.name != "README.md"
    }
    return from_gates | from_template


def test_every_published_pinned_path_is_one_the_standard_creates() -> None:
    """ADR 0048 rule 3, and the one that closes the hole rather than patching it.

    A published `pinned_at` path must be a file the shipped template writes or a
    path a gate declares in `deploys.json`. Anything else exists only because
    somebody here made it, and an adopter fails on its absence.

    Both lists are already in the repository, so this is a check rather than a
    judgement — and it would have failed the day `support-floor.yml` was added.
    """
    published = yaml.safe_load(PUBLISHED_PATH.read_text(encoding="utf-8"))
    creatable = _creatable_paths()
    strays = {
        f"{name}: {path}"
        for name, tool in (published.get("tools") or {}).items()
        for path in (tool.get("pinned_at") or [])
        if path not in creatable
    }
    assert not strays, (
        f"the published register pins tools at paths nothing in this standard creates: "
        f"{sorted(strays)}. Either a gate should write that file, or the entry is this "
        "repository's and needs a `# local-only` marker (ADR 0048)."
    )


def test_this_repository_still_compares_everything_it_did_before() -> None:
    """The cost the ADR refused to pay.

    Deleting the two workflow paths outright would have fixed the adopter and
    stopped comparing two sites here that genuinely repeat the pin. The marker
    exists so both hold at once, and this is the half that would go quiet first.
    """
    source = yaml.safe_load(SOURCE_TEXT)
    ours = set(source["tools"]["uv"]["pinned_at"])
    for path in (
        ".github/workflows/support-floor.yml",
        ".github/workflows/conformance-sweep.yml",
    ):
        assert path in ours, (
            f"{path} left this repository's own pinned_at — it installs uv at a pinned "
            "version, so dropping it stops a real site being compared"
        )
        assert (REPO_ROOT / path).is_file(), f"{path} is pinned here but does not exist"


def test_a_lockfile_failure_names_the_control_that_wants_the_tool() -> None:
    """An absent lockfile reads as a broken supply chain and usually is not.

    Measured on the first adoption outside this repository: SUP-001 reported
    `markdownlint-cli2 is sourced from package-lock.json, which is not tracked`,
    and the fix was to deploy DOC-001. One message, two very different
    situations.
    """
    from conftest import a_register
    from register_check.asserts_file import _who_needs

    register = a_register()
    said = _who_needs("markdownlint-cli2", register)
    assert "DOC-001" in said, "the message does not name the control that wants the tool"
    assert "lint-md" in said, "nor who deploys it, which is where the reader goes next"
    assert _who_needs("not-a-tool-any-control-names", register) == "", (
        "a tool no control names should add nothing rather than guess"
    )
