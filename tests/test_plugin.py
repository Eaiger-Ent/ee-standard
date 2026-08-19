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


def test_the_deploys_sidecar_names_controls_the_register_defines() -> None:
    """A sidecar naming DOC-002 would recommend redeploying a control nobody has."""
    sidecar = json.loads((PLUGIN / ".claude-plugin/deploys.json").read_text(encoding="utf-8"))
    known = {control.id for control in a_register().controls}
    assert set(sidecar["controls"]) <= known, set(sidecar["controls"]) - known
    assert isinstance(sidecar["contractVersion"], int)
    assert sidecar["artifacts"], "a plugin that deploys nothing needs no contract"


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
        "{{TOOL}}": "gitleaks",
        "{{SKILL_VERSION}}": "0.1.0",
        "{{REGISTER_VERSION}}": register.version,
        "{{REGISTER_CONTRACT}}": str(register.register_contract),
    }
    templates = sorted((skill / "templates").glob("*"))
    assert templates, f"{skill.name} references templates it does not ship"
    known = {control.id for control in register.controls}
    for template in templates:
        text = template.read_text(encoding="utf-8")
        assert MARKER in text, f"{template.name} writes an artefact it does not stamp"
        for placeholder, value in substitutions.items():
            text = text.replace(placeholder, value)
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
    sidecar = json.loads((PLUGIN / ".claude-plugin/deploys.json").read_text(encoding="utf-8"))
    verify = [line for line in text.splitlines() if "standard-check" in line and "run" in line]
    assert verify, f"{skill.name} has no verify step that calls the checker"
    joined = " ".join(verify)
    for control in sidecar["controls"]:
        assert f"--control {control}" in joined, (
            f"{skill.name} deploys {control} and does not verify it through the checker"
        )
