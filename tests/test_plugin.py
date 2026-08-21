"""The plugin's structural invariants — the ones this repository owns.

P1-P11 are the marketplace's gates and are run by `preflight-check.sh`, which
ships in `ee-skills` rather than here; the evidence for that run lives in
`docs/10-phase-2-review.md`. What is checked below is what only this repository
can check: that the plugin's declarations agree with the register it deploys.

The one that matters most is the last. A gate skill carrying a pinned version of
its own would be a second source of truth for it, free to drift from the
register the checker audits against — the failure this repository exists to
prevent, reproduced inside the tool meant to prevent it. It is a grep, not a
convention.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest
import yaml

from conftest import REPO_ROOT, a_register
from standard_check.provenance import MARKER, stamps_in

PLUGIN = REPO_ROOT / "plugins/ee-standard"
SKILLS = sorted(p for p in (PLUGIN / "skills").iterdir() if p.is_dir())


def _frontmatter(skill: Path) -> dict[str, object]:
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{skill.name}: SKILL.md has no frontmatter"
    block = text.split("---\n", 2)[1]
    loaded = yaml.safe_load(block)
    assert isinstance(loaded, dict)
    return loaded


def test_the_plugin_declares_itself() -> None:
    manifest = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
    assert manifest["name"] == "ee-standard"
    assert re.fullmatch(r"\d+\.\d+\.\d+", manifest["version"])
    # P7 is about dependencies being declared in JSON rather than in prose. An
    # empty list is a declaration; an absent key is not.
    assert isinstance(manifest["dependencies"], list)


def _sidecar() -> dict[str, Any]:
    loaded = json.loads((PLUGIN / ".claude-plugin/deploys.json").read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def test_the_deploys_sidecar_names_controls_the_register_defines() -> None:
    """A sidecar naming DOC-002 would recommend redeploying a control nobody has."""
    known = {control.id for control in a_register().controls}
    for gate, entry in _sidecar()["gates"].items():
        assert set(entry["controls"]) <= known, set(entry["controls"]) - known
        assert isinstance(entry["contractVersion"], int)
        assert entry["artifacts"], f"{gate} deploys nothing and needs no contract"


def test_each_gate_carries_its_own_contract_version() -> None:
    """One contract per thing that can change, which is the gate and not the plugin.

    With six gates in one plugin, a single plugin-wide `contractVersion` makes
    changing what `gate-quality` writes recommend redeploying `gate-secrets`.
    Phase 5's first two exit criteria are exactly *a version bump produces no
    recommendation, a contract bump does*, so a contract that fires for gates
    whose output did not change fails the second one while appearing to pass it.
    Recorded as a decision the second gate forces in `10-phase-2-review.md`.
    """
    sidecar = _sidecar()
    assert sidecar["schemaVersion"] == 2
    assert "contractVersion" not in sidecar, (
        "a plugin-wide contract version is what this shape exists to remove"
    )
    directories = {skill.name for skill in SKILLS}
    assert set(sidecar["gates"]) <= directories, set(sidecar["gates"]) - directories
    gates = {name for name in directories if name.startswith("gate-")}
    assert gates <= set(sidecar["gates"]), gates - set(sidecar["gates"])


def test_the_sidecar_agrees_with_the_register_about_who_deploys_what() -> None:
    """`deployed_by` and the sidecar are two records of one fact.

    The register says which gate writes a control's artefacts; the sidecar says
    which controls a gate writes. Left unchecked they are theme T-2 across two
    files — and the one that drifts is the sidecar, because nothing consumes it
    until Phase 5's sweep, by which point the disagreement is a year old.

    Checked in the direction that can be wrong: a control the register assigns
    to a gate this plugin ships must appear in that gate's list. SEC-002 sits in
    `gate-secrets`' list without a `deployed_by` of its own, which is correct —
    the gate checks it and writes nothing for it.
    """
    sidecar = _sidecar()["gates"]
    for control in a_register().controls:
        gate = control.deployed_by
        if gate is None or gate not in sidecar:
            continue
        assert control.id in sidecar[gate]["controls"], (
            f"{control.id} is deployed_by {gate}, which does not list it"
        )


@pytest.mark.parametrize("skill", SKILLS, ids=lambda p: p.name)
def test_the_skill_name_matches_its_directory(skill: Path) -> None:
    assert _frontmatter(skill)["name"] == skill.name


@pytest.mark.parametrize("skill", SKILLS, ids=lambda p: p.name)
def test_every_control_the_skill_claims_is_in_the_register(skill: Path) -> None:
    """A gate for SEC-999 would deploy artefacts for a control nobody defined."""
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    known = {control.id for control in a_register().controls}
    claimed = set(re.findall(r"\b[A-Z]{3}-\d{3}\b", text))
    assert claimed <= known, claimed - known


@pytest.mark.parametrize("skill", SKILLS, ids=lambda p: p.name)
def test_the_templates_stamp_what_they_write(skill: Path) -> None:
    """Every template carries a stamp, and it parses once the register fills it.

    A placeholder that never gets substituted, or a stamp with a field missing,
    produces an artefact whose provenance cannot be read — and `lint-md`'s
    unstamped artefacts are what that looks like in practice (§ F).
    """
    register = a_register()
    substitutions = {
        "{{SKILL_VERSION}}": "0.1.0",
        "{{REGISTER_VERSION}}": register.version,
        "{{REGISTER_CONTRACT}}": str(register.register_contract),
    }
    templates = sorted((skill / "templates").glob("*"))
    if not templates:
        # A skill that ships no templates must be one that writes no artefacts.
        # `standard-adopt` is the only such skill and it is so by design: every
        # artefact is written by the gate that owns the control, which is what
        # keeps one control's config in one place. A *gate* with no templates
        # would be a gate whose deployment has no reviewable source.
        assert skill.name not in _sidecar()["gates"], (
            f"{skill.name} deploys controls and ships no template to write them from"
        )
        pytest.skip(f"{skill.name} writes no artefacts of its own")
    known = {control.id for control in register.controls}
    for template in templates:
        text = template.read_text(encoding="utf-8")
        assert MARKER in text, f"{template.name} writes an artefact it does not stamp"
        for placeholder, value in substitutions.items():
            text = text.replace(placeholder, value)
        # Whatever else a template parameterises — a tool name, a version, an
        # invocation — is a value only the register supplies at deploy time.
        # Filling the rest generically keeps this test about the stamp rather
        # than about any one gate's vocabulary, which is what tied it to
        # `gitleaks` while `gate-secrets` was the only gate.
        text = re.sub(r"\{\{[A-Z_]+\}\}", "supplied-by-the-register", text)
        stamps = stamps_in(text)
        assert len(stamps) == text.count(MARKER), (
            f"{template.name}: a stamp does not parse once the register fills it"
        )
        for stamp in stamps:
            assert stamp.control in known
            assert stamp.skill == skill.name


def _register_literals() -> dict[str, str]:
    """Every literal the register pins, by the field that pins it."""
    document = yaml.safe_load((REPO_ROOT / "controls.yaml").read_text(encoding="utf-8"))
    found: dict[str, str] = {}
    for name, tool in (document.get("tools") or {}).items():
        for field in ("version", "sha256"):
            if tool.get(field):
                found[f"tools.{name}.{field}"] = str(tool[field])
    return found


@pytest.mark.parametrize("field,literal", sorted(_register_literals().items()))
def test_no_skill_repeats_a_version_the_register_pins(field: str, literal: str) -> None:
    """The rule that keeps a gate from becoming a second register.

    A skill that hard-coded `8.30.1` would deploy that version after the
    register moved on, and `tool_versions_match_register` would report drift in
    a repository whose owner changed nothing. The templates carry
    `{{TOOL_VERSION}}`; the value arrives at deploy time or not at all.
    """
    offenders = [
        str(path.relative_to(REPO_ROOT))
        for path in PLUGIN.rglob("*")
        if path.is_file() and literal in path.read_text(encoding="utf-8", errors="ignore")
    ]
    assert not offenders, f"{field} ({literal}) is repeated in: {', '.join(offenders)}"


@pytest.mark.parametrize("skill", SKILLS, ids=lambda p: p.name)
def test_the_gate_verifies_through_the_checker_and_not_otherwise(skill: Path) -> None:
    """One assert implementation, established rather than asserted.

    Phase 2's criterion is "verified by there being one copy, not by comparing
    two". The one copy is `standard_check.asserts`; the only way a skill reaches
    it is `standard-check run --control <ID>`, which evaluates the control's own
    verify blocks through the same `run_control` the full audit calls.

    So what is checked here is that every control the skill claims to deploy is
    named on that command line. A gate that verified itself by reading its files
    back would pass every other test in this file and disagree with the auditor
    the first time the register moved.
    """
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    entry = _sidecar()["gates"].get(skill.name)
    if entry is None:
        pytest.skip(f"{skill.name} deploys nothing — there is no verify step to check")
    verify = [line for line in text.splitlines() if "standard-check" in line and "run" in line]
    assert verify, f"{skill.name} has no verify step that calls the checker"
    joined = " ".join(verify)
    for control in entry["controls"]:
        assert f"--control {control}" in joined, (
            f"{skill.name} deploys {control} and does not verify it through the checker"
        )
