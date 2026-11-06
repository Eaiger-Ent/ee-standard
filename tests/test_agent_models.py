"""AGT-001 (ADR 0023): sub-agent definitions are held to the register's floors.

The assert is run against this repository's own `agent_models:` block and
AGT-001's own `args:`, so a test here fails when the register and the checker
disagree, not only when the checker is wrong. Each of ADR 0023's four
properties is mutated once, and seen to fail.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any

import pytest

from conftest import REPO_ROOT, make_repo, minimal_register, write_register
from register_check.asserts_file import agent_definitions_declare_model_floor
from register_check.register import AgentClass, Register, load_register
from register_check.repo import Repo


def _register() -> Register:
    register, errors = load_register(REPO_ROOT / "controls.yaml")
    assert errors == [] and register is not None
    return register


REGISTER = _register()
ARGS: dict[str, Any] = next(
    block.args
    for control in REGISTER.controls
    if control.id == "AGT-001"
    for block in control.verify
    if block.assert_name == "agent_definitions_declare_model_floor"
)


def _definition(name: str, model: str | None, tools: str | None = "Read, Grep, Glob") -> str:
    lines = ["---", f"name: {name}", "description: a test agent"]
    if tools is not None:
        lines.append(f"tools: {tools}")
    if model is not None:
        lines.append(f"model: {model}")
    return "\n".join([*lines, "---", "", "Body."]) + "\n"


def _check(
    tmp_path: Path, files: dict[str, str], register: Register = REGISTER
) -> tuple[bool, str]:
    make_repo(tmp_path, files)
    result = agent_definitions_declare_model_floor(Repo(tmp_path), register, ARGS)
    return result.passed, result.message


GOOD = {
    ".claude/agents/reviewer.md": _definition("code-review", "opus"),
    ".claude/agents/author.md": _definition("author", "sonnet", tools="Read, Edit, Write"),
    ".claude/agents/Explore.md": _definition("Explore", "haiku"),
}


def test_definitions_at_their_floors_pass(tmp_path: Path) -> None:
    passed, message = _check(tmp_path, GOOD)
    assert passed, message
    assert "3 definition(s)" in message


# --- Property 1: every definition declares a model -------------------------


def test_a_definition_with_no_model_fails(tmp_path: Path) -> None:
    passed, message = _check(tmp_path, {".claude/agents/x.md": _definition("Explore", None)})
    assert not passed
    assert "declares no model:" in message


# --- Property 2: at or above the floor, and R at its ceiling ----------------


def test_review_below_its_floor_fails(tmp_path: Path) -> None:
    files = {".claude/agents/r.md": _definition("code-review", "sonnet")}
    passed, message = _check(tmp_path, files)
    assert not passed
    assert "class R and declares sonnet, below opus" in message


def test_authoring_below_its_floor_fails(tmp_path: Path) -> None:
    files = {".claude/agents/a.md": _definition("gate-build", "haiku", tools="Read, Write")}
    passed, message = _check(tmp_path, files)
    assert not passed
    assert "class C and declares haiku, below sonnet" in message


def test_a_ceiling_is_read_from_the_register(tmp_path: Path) -> None:
    """R's ceiling equals its floor here, so an over-ceiling model cannot be
    built from this register. Lower the ceiling's floor and it can."""
    models = REGISTER.agent_models
    assert models is not None
    classes = dict(models.classes, R=AgentClass("R", "review", "sonnet", "sonnet"))
    register = dataclasses.replace(
        REGISTER, agent_models=dataclasses.replace(models, classes=classes)
    )
    files = {".claude/agents/r.md": _definition("code-review", "opus")}
    passed, message = _check(tmp_path, files, register)
    assert not passed
    assert "declares opus, above sonnet" in message


def test_the_floors_are_the_registers_not_the_checkers(tmp_path: Path) -> None:
    """Raise S's floor in the register and the same definition changes verdict,
    with no checker change: the test ADR 0018's third pass introduced."""
    models = REGISTER.agent_models
    assert models is not None
    classes = dict(models.classes, S=AgentClass("S", "retrieval", "sonnet", None))
    register = dataclasses.replace(
        REGISTER, agent_models=dataclasses.replace(models, classes=classes)
    )
    files = {".claude/agents/e.md": _definition("Explore", "haiku")}
    assert _check(tmp_path / "before", files)[0]
    assert not _check(tmp_path / "after", files, register)[0]


# --- Property 3: no R or C definition declares a model the ladder does not place


@pytest.mark.parametrize("model", ["inherit", "fable", "claude-opus-5-5"])
def test_review_may_not_use_an_unplaced_model(tmp_path: Path, model: str) -> None:
    passed, message = _check(tmp_path, {".claude/agents/r.md": _definition("code-review", model)})
    assert not passed
    assert "does not place" in message


def test_retrieval_may_inherit(tmp_path: Path) -> None:
    """ADR 0023 forbids `inherit` for R and C only. S is the default class, and
    the default class is the one an unplaced model may satisfy."""
    passed, message = _check(tmp_path, {".claude/agents/e.md": _definition("Explore", "inherit")})
    assert passed, message


# --- The mechanical boundary: a definition that can write is authoring -----


@pytest.mark.parametrize(
    "tools",
    [None, "Read, Edit", "Bash, NotebookEdit", "Read, Write(docs/**)"],
    ids=["all-tools", "edit", "notebook", "scoped-write"],
)
def test_an_unlisted_definition_that_can_write_is_held_to_authorings_floor(
    tmp_path: Path, tools: str | None
) -> None:
    files = {".claude/agents/helper.md": _definition("helper", "haiku", tools=tools)}
    passed, message = _check(tmp_path, files)
    assert not passed
    assert "helper is class C" in message


def test_denying_the_authoring_tools_keeps_it_retrieval(tmp_path: Path) -> None:
    text = _definition("helper", "haiku", tools=None).replace(
        "model: haiku", "model: haiku\ndisallowedTools: Write, Edit, NotebookEdit"
    )
    passed, message = _check(tmp_path, {".claude/agents/helper.md": text})
    assert passed, message


def test_review_that_can_write_stays_review(tmp_path: Path) -> None:
    """`simplify` applies its fixes and is still R: raising is towards
    authoring's floor, never down from a higher one."""
    files = {".claude/agents/s.md": _definition("simplify", "opus", tools="Read, Edit")}
    passed, message = _check(tmp_path, files)
    assert passed, message


# --- Property 4: nothing tracked overrides the definitions ------------------


@pytest.mark.parametrize("name", ["CLAUDE_CODE_SUBAGENT_MODEL", "CLAUDE_CODE_SUBAGENT_MODEL_FORCE"])
def test_a_forbidden_variable_in_settings_fails(tmp_path: Path, name: str) -> None:
    settings = json.dumps({"env": {name: "haiku"}})
    passed, message = _check(tmp_path, {**GOOD, ".claude/settings.json": settings})
    assert not passed
    assert f".claude/settings.json: sets {name}" in message


def test_a_forbidden_variable_in_a_workflow_fails(tmp_path: Path) -> None:
    workflow = "jobs:\n  a:\n    env:\n      CLAUDE_CODE_SUBAGENT_MODEL: haiku\n"
    passed, message = _check(tmp_path, {**GOOD, ".github/workflows/ci.yml": workflow})
    assert not passed
    assert "ci.yml: sets CLAUDE_CODE_SUBAGENT_MODEL" in message


def test_a_shell_export_fails(tmp_path: Path) -> None:
    script = "#!/bin/sh\nexport CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1\n"
    passed, message = _check(tmp_path, {**GOOD, ".devcontainer/setup.sh": script})
    assert not passed
    assert "sets CLAUDE_CODE_SUBAGENT_MODEL_FORCE" in message


def test_naming_the_variable_in_prose_is_not_setting_it(tmp_path: Path) -> None:
    """CLAUDE.md and ADR 0023 both name it, to forbid it. Neither is an env
    surface, and naming a variable is not assigning it."""
    files = {
        **GOOD,
        "CLAUDE.md": "Never set `CLAUDE_CODE_SUBAGENT_MODEL`.\n",
        ".devcontainer/setup.sh": "# CLAUDE_CODE_SUBAGENT_MODEL is forbidden here\n",
    }
    passed, message = _check(tmp_path, files)
    assert passed, message


# --- What there is to read --------------------------------------------------


def test_no_definitions_fails(tmp_path: Path) -> None:
    passed, message = _check(tmp_path, {"README.md": "x\n"})
    assert not passed
    assert "no tracked definition under .claude/agents/" in message


def test_an_untracked_definition_is_not_read(tmp_path: Path) -> None:
    make_repo(tmp_path, GOOD)
    (tmp_path / ".claude/agents/local.md").write_text(_definition("code-review", "haiku"))
    result = agent_definitions_declare_model_floor(Repo(tmp_path), REGISTER, ARGS)
    assert result.passed, result.message


def test_no_agent_models_block_fails_rather_than_passing(tmp_path: Path) -> None:
    register = dataclasses.replace(REGISTER, agent_models=None)
    passed, message = _check(tmp_path, GOOD, register)
    assert not passed
    assert "no agent_models: block" in message


# --- The schema ---------------------------------------------------------------


def _with_agent_models(tmp_path: Path, **changes: Any) -> list[str]:
    document = minimal_register()
    block: dict[str, Any] = {
        "ladder": ["haiku", "sonnet", "opus"],
        "classes": {
            "R": {"does": "review", "floor": "opus", "ceiling": "opus"},
            "S": {"does": "retrieval", "floor": "haiku"},
        },
        "default_class": "S",
        "authoring_class": "R",
        "authoring_tools": ["Write"],
        "forbidden_env": ["CLAUDE_CODE_SUBAGENT_MODEL"],
        "members": {"Explore": "S"},
    }
    block.update(changes)
    document["agent_models"] = block
    _, errors = load_register(write_register(tmp_path, document))
    return [str(error) for error in errors]


def test_a_valid_block_loads(tmp_path: Path) -> None:
    assert _with_agent_models(tmp_path) == []


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        ({"classes": {"S": {"does": "x", "floor": "fable"}}}, "is not on the ladder"),
        (
            {"classes": {"S": {"does": "x", "floor": "opus", "ceiling": "haiku"}}},
            "at or above the floor",
        ),
        ({"default_class": "Q"}, "'Q' is not a class"),
        ({"members": {"Explore": "Q"}}, "'Q' is not a class"),
        ({"forbidden_env": []}, "non-empty list"),
        ({"ladder": ["haiku", "haiku"]}, "lists a name twice"),
        ({"floors": {}}, "unknown key(s): floors"),
    ],
    ids=["floor-off-ladder", "ceiling-below-floor", "default", "member", "env", "ladder", "key"],
)
def test_the_schema_rejects(tmp_path: Path, changes: dict[str, Any], expected: str) -> None:
    errors = _with_agent_models(tmp_path, **changes)
    assert any(expected in error for error in errors), errors
