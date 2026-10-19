"""The states a deployment can be in, held apart from each other.

Phase 5's first two exit criteria are one sentence in two halves — *bumping a
gate's version without changing its output produces no redeployment
recommendation*, and *bumping its contract version does* — and they are the
whole noise argument. A mechanism that fires on every release is ignored within
a month; one that fires on nothing is invisible.

They are tested here rather than demonstrated against this repository, because
on the day ADR 0038 landed every gate here reports the same state
(`UNRECORDED`), and a report whose every row agrees is no evidence that the rows
can differ. Each state below is built from a fixture that differs from the next
in exactly the field that is supposed to decide it.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from conftest import a_register, make_repo, register_with
from register_check.cli import main
from register_check.deployments import (
    NoPlugin,
    Report,
    State,
    build,
    find_plugin,
    load_gates,
    render,
)
from register_check.register import Register
from register_check.repo import Repo

REGISTER = a_register()

#: One gate, one control that applies to any repository, one artefact.
_ONE_GATE = {
    "schemaVersion": 2,
    "gates": {
        "gate-secrets": {
            "contractVersion": 5,
            "controls": ["SEC-001"],
            "artifacts": [".pre-commit-config.yaml#gitleaks"],
        }
    },
}


def _plugin(root: Path, sidecar: dict[str, object] | None = None) -> Path:
    plugin = root / "plugin"
    (plugin / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    (plugin / ".claude-plugin/deploys.json").write_text(
        json.dumps(sidecar if sidecar is not None else _ONE_GATE), encoding="utf-8"
    )
    return plugin


def _stamp(gate_contract: int | None = 5, skill_version: str = "0.1.0") -> str:
    contract = "" if gate_contract is None else f"gate-contract: {gate_contract}  "
    return (
        "repos:\n  - repo: local\n    hooks:\n"
        f"      # ee-control: SEC-001  ee-skill: gate-secrets@{skill_version}  "
        f"{contract}register: v0.24.0  register-contract: 30\n"
        "      - id: gitleaks\n"
    )


def _report(
    tmp_path: Path, files: dict[str, str], sidecar: dict[str, object] | None = None
) -> Report:
    repo = make_repo(tmp_path / "repo", files or {"README.md": "#\n"})
    return build(repo, _plugin(tmp_path, sidecar), REGISTER)


def _state(
    tmp_path: Path, files: dict[str, str], sidecar: dict[str, object] | None = None
) -> State:
    state: State = _report(tmp_path, files, sidecar).gates[0].state
    return state


def test_no_stamp_is_never_deployed(tmp_path: Path) -> None:
    assert _state(tmp_path, {".pre-commit-config.yaml": "repos: []\n"}) is State.NEVER_DEPLOYED


def test_stamp_at_the_installed_contract_is_current(tmp_path: Path) -> None:
    assert _state(tmp_path, {".pre-commit-config.yaml": _stamp(5)}) is State.CURRENT


def test_a_version_bump_alone_recommends_nothing(tmp_path: Path) -> None:
    """Phase 5, criterion 1. The gate shipped again; its output did not move.

    The stamp names an older skill version and the contract the installed gate
    still declares. Nothing is owed, and a mechanism that said otherwise here
    would fire on every documentation release of the plugin.
    """
    report = _report(tmp_path, {".pre-commit-config.yaml": _stamp(5, skill_version="0.0.1")})
    assert report.gates[0].state is State.CURRENT
    assert report.owed == []


def test_a_contract_bump_recommends_a_redeployment(tmp_path: Path) -> None:
    """Phase 5, criterion 2. The same repository, one number higher upstream."""
    sidecar = json.loads(json.dumps(_ONE_GATE))
    sidecar["gates"]["gate-secrets"]["contractVersion"] = 6
    report = _report(tmp_path, {".pre-commit-config.yaml": _stamp(5)}, sidecar)
    assert report.gates[0].state is State.STALE
    assert report.gates[0].behind == [5]
    assert [g.gate.name for g in report.owed] == ["gate-secrets"]


def test_the_two_criteria_differ_only_in_the_contract(tmp_path: Path) -> None:
    """The pair, as one assertion: same repository, one field apart."""
    files = {".pre-commit-config.yaml": _stamp(5, skill_version="0.0.1")}
    bumped = json.loads(json.dumps(_ONE_GATE))
    bumped["gates"]["gate-secrets"]["contractVersion"] = 6
    assert _state(tmp_path / "a", files) is State.CURRENT
    assert _state(tmp_path / "b", files, bumped) is State.STALE


def test_a_stamp_without_the_field_is_unrecorded(tmp_path: Path) -> None:
    """ADR 0038's optional field: absent is a state, not a default of zero.

    Reporting it as stale would claim the deployment is behind, which nobody
    knows; reporting it as current would claim it is not, which nobody knows
    either. It is owed because a deployment that cannot be dated cannot be
    shown to be current.
    """
    report = _report(tmp_path, {".pre-commit-config.yaml": _stamp(None)})
    assert report.gates[0].state is State.UNRECORDED
    assert report.owed


def test_a_stamp_ahead_of_the_installed_gate_is_a_defect(tmp_path: Path) -> None:
    report = _report(tmp_path, {".pre-commit-config.yaml": _stamp(9)})
    assert report.gates[0].state is State.AHEAD
    assert report.defective
    # A defect outranks a currency question: it is not reported as an act owed.
    assert report.owed == []


def test_a_gate_whose_controls_do_not_apply_is_owed_nothing(tmp_path: Path) -> None:
    """A predicate skip is not a gap (`00-concepts.md` § Predicates).

    `gate-iac` carries IAC-001 alone, whose predicate is `terraform`. In a
    repository with no Terraform, planning its deployment would invent work —
    which is the noise the whole mechanism exists to avoid, arriving from the
    other direction.
    """
    sidecar = {
        "schemaVersion": 2,
        "gates": {
            "gate-iac": {
                "contractVersion": 3,
                "controls": ["IAC-001"],
                "artifacts": [".pre-commit-config.yaml#iac"],
            }
        },
    }
    report = _report(tmp_path, {"README.md": "#\n"}, sidecar)
    assert report.gates[0].state is State.NOT_APPLICABLE
    assert report.owed == []
    # And it *is* owed once the predicate holds, or the state above would be
    # indistinguishable from "this gate is never reported".
    with_tf = _report(tmp_path / "tf", {"main.tf": 'resource "null_resource" "a" {}\n'}, sidecar)
    assert with_tf.gates[0].state is State.NEVER_DEPLOYED


def test_any_applicable_control_makes_the_gate_applicable(tmp_path: Path) -> None:
    """`gate-quality` carries three controls; one applying is enough."""
    sidecar = {
        "schemaVersion": 2,
        "gates": {
            "gate-quality": {
                "contractVersion": 5,
                "controls": ["LNT-001", "TYP-001", "TST-001"],
                "artifacts": [".pre-commit-config.yaml#lint"],
            }
        },
    }
    # No Python and no TypeScript, so LNT-001 and TYP-001 do not apply — but
    # TST-001 applies always.
    report = _report(tmp_path, {"README.md": "#\n"}, sidecar)
    assert report.gates[0].state is State.NEVER_DEPLOYED


def test_a_missing_artefact_is_reported(tmp_path: Path) -> None:
    report = _report(tmp_path, {"README.md": "#\n"})
    assert report.gates[0].absent_paths == (".pre-commit-config.yaml",)


def test_a_stamp_from_another_plugin_is_reported_and_not_a_defect(tmp_path: Path) -> None:
    """DOC-001 is `lint-md`'s. Dropping it would understate the deployment."""
    files = {
        ".markdownlint.yaml": (
            "# ee-control: DOC-001  ee-skill: lint-md@1.0.6  "
            "register: v0.5.0  register-contract: 5\n"
        )
    }
    report = _report(tmp_path, files)
    assert report.foreign == (("lint-md", "DOC-001"),)
    assert report.defective == []


def test_the_report_names_every_state_it_gives(tmp_path: Path) -> None:
    """Rendering covers each state, so no branch is reachable only in prose."""
    report = _report(tmp_path, {".pre-commit-config.yaml": _stamp(5)})
    text = render(report, REGISTER)
    assert "gate-secrets" in text
    assert "CURRENT" in text
    assert "Summary:" in text


def _two_gates() -> dict[str, object]:
    return {
        "schemaVersion": 2,
        "gates": {
            "gate-quality": {
                "contractVersion": 1,
                "controls": ["TST-001"],
                "artifacts": [".pre-commit-config.yaml#lint"],
            },
            "gate-secrets": {
                "contractVersion": 5,
                "controls": ["SEC-001"],
                "artifacts": [".pre-commit-config.yaml#gitleaks"],
            },
        },
    }


def _rows(report: Report, register: Register) -> list[str]:
    return [line for line in render(report, register).splitlines() if line.startswith("  gate-")]


def test_loudness_comes_from_the_register_and_not_from_this_module(tmp_path: Path) -> None:
    """`02-skill-family.md` § Loudness: order is the tier and rung of what a
    gate carries. Every control in this register is Tier 1 and blocking today,
    so the ordering is shown by moving one in the register and watching the
    report move with it — a severity field invented here would not budge.
    """
    repo = make_repo(tmp_path / "repo", {"README.md": "#\n"})
    plugin = _plugin(tmp_path, _two_gates())
    # As the register stands the two gates tie on tier and rung, and the tie is
    # broken by name — `gate-quality` first.
    assert _rows(build(repo, plugin, REGISTER), REGISTER)[0].split()[0] == "gate-quality"
    # One edit to the register, nothing to this module, and the order inverts.
    demoted = register_with(tmp_path, lambda d: _retier(d, "TST-001", tier=3, rung="advisory"))
    assert _rows(build(repo, plugin, demoted), demoted)[0].split()[0] == "gate-secrets"


def _retier(document: dict[str, Any], control_id: str, *, tier: int, rung: str) -> None:
    for control in document["controls"]:
        if control["id"] == control_id:
            control["tier"] = tier
            control["rung"] = rung
            control["baseline"] = None


def test_a_defect_sorts_above_every_currency_question(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "repo", {".pre-commit-config.yaml": _stamp(9)})
    report = build(repo, _plugin(tmp_path, _two_gates()), REGISTER)
    assert _rows(report, REGISTER)[0].split()[0] == "gate-secrets"
    assert report.defective


def test_an_unknown_sidecar_schema_is_an_error_not_an_empty_report(tmp_path: Path) -> None:
    """Guessing at an unknown layout would report a deployed repo as bare."""
    plugin = _plugin(tmp_path, {"schemaVersion": 99, "gates": {}})
    with pytest.raises(NoPlugin, match="schemaVersion"):
        load_gates(plugin)


def test_the_plugin_is_found_explicitly_then_by_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = make_repo(tmp_path / "repo", {"README.md": "#\n"})
    plugin = _plugin(tmp_path)
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
    assert find_plugin(repo, plugin) == plugin
    with pytest.raises(NoPlugin):
        find_plugin(repo)
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(plugin))
    assert find_plugin(repo) == plugin


def test_an_explicit_plugin_without_a_sidecar_raises_rather_than_falling_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The answer to "which plugin did you mean" is never "some other one"."""
    repo = make_repo(tmp_path / "repo", {"README.md": "#\n"})
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(_plugin(tmp_path)))
    with pytest.raises(NoPlugin, match="ships no"):
        find_plugin(repo, tmp_path / "elsewhere")


def _cli(repo: Repo, plugin: Path) -> int:
    return main(
        [
            "--repo",
            str(repo.root),
            "--register",
            "controls.yaml",
            "deployments",
            "--plugin",
            str(plugin),
        ]
    )


def test_staleness_does_not_change_the_exit_code(tmp_path: Path) -> None:
    """ "Reported, never enforced", said as an exit code.

    A command that failed over an owed deployment would be enforcing
    redeployment through the back door, which is the one thing the design rules
    out.
    """
    repo = make_repo(tmp_path / "repo", {".pre-commit-config.yaml": _stamp(None)})
    assert _cli(repo, _plugin(tmp_path)) == 0


def test_a_defect_does_change_the_exit_code(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "repo", {".pre-commit-config.yaml": _stamp(9)})
    assert _cli(repo, _plugin(tmp_path)) == 1


def test_no_plugin_is_a_usage_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = make_repo(tmp_path / "repo", {"README.md": "#\n"})
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
    assert main(["--repo", str(repo.root), "--register", "controls.yaml", "deployments"]) == 2


# --- A stack that arrives after the gate ran (Phase 8) ------------------------

#: gate-quality as the plugin declares it, at the contract the stamps below carry.
_QUALITY = {
    "schemaVersion": 2,
    "gates": {
        "gate-quality": {
            "contractVersion": 6,
            "controls": ["LNT-001", "TYP-001", "TST-001"],
            "artifacts": [".pre-commit-config.yaml#lint"],
        }
    },
}


def _hook(hook: str, *, stamped: bool, gap: bool = False) -> str:
    stamp = (
        "      # ee-control: LNT-001  ee-skill: gate-quality@0.2.4  gate-contract: 6  "
        "register: v0.29.0  register-contract: 35\n"
        if stamped
        else "      # hand-deployed, so no stamp\n"
    )
    return stamp + ("\n" if gap else "") + f"      - id: {hook}\n        entry: x\n"


def _quality_report(tmp_path: Path, hooks: str, *, typescript: bool = True) -> Report:
    from conftest import REPO_ROOT
    from register_check.register import load_register

    register, errors = load_register(REPO_ROOT / "controls.yaml")
    assert register is not None and not errors, errors
    files = {
        "pyproject.toml": "[project]\nname = 'x'\n",
        ".pre-commit-config.yaml": "repos:\n  - repo: local\n    hooks:\n" + hooks,
    }
    if typescript:
        files["tsconfig.json"] = '{"compilerOptions": {"strict": true}}\n'
    repo = make_repo(tmp_path / "repo", files)
    return build(repo, _plugin(tmp_path, _QUALITY), register)


_PYTHON_HOOKS = _hook("ruff", stamped=True) + _hook("mypy", stamped=True)


def test_a_stack_wired_by_hand_is_reported_and_owed(tmp_path: Path) -> None:
    """The trial repository's state: every stamp current, TypeScript wired by hand.

    The gate keeps its state, because no stamp is behind. It is owed a run all
    the same, which is what the report said nothing about before.
    """
    hooks = _PYTHON_HOOKS + _hook("eslint", stamped=False) + _hook("tsc", stamped=False)
    report = _quality_report(tmp_path, hooks)
    gate = report.gates[0]
    assert gate.state is State.CURRENT
    assert [line.split(":")[0] for line in gate.stacks_not_covered] == ["typescript"] * 2
    assert all("no gate-quality stamp" in line for line in gate.stacks_not_covered)
    assert [g.gate.name for g in report.owed] == ["gate-quality"]


def test_a_stack_the_gate_wired_is_not_reported(tmp_path: Path) -> None:
    hooks = _PYTHON_HOOKS + _hook("eslint", stamped=True) + _hook("tsc", stamped=True)
    report = _quality_report(tmp_path, hooks)
    assert report.gates[0].stacks_not_covered == ()
    assert report.owed == []


def test_a_stack_with_no_hook_at_all_is_reported(tmp_path: Path) -> None:
    report = _quality_report(tmp_path, _PYTHON_HOOKS)
    assert report.gates[0].stacks_not_covered == (
        "typescript: no eslint hook — gate-quality has not wired it",
        "typescript: no tsc hook — gate-quality has not wired it",
    )


def test_a_stack_that_does_not_apply_is_owed_nothing(tmp_path: Path) -> None:
    """No `tsconfig.json`, so no TypeScript gate is owed — a predicate skip is not a gap."""
    report = _quality_report(tmp_path, _PYTHON_HOOKS, typescript=False)
    assert report.gates[0].stacks_not_covered == ()


def test_a_stamp_is_credited_only_to_the_hook_directly_below_it(tmp_path: Path) -> None:
    """A blank line ends a stamp's block, so a stamp near a hook is not its stamp.

    Otherwise a hand-written hook added under a gate's would be credited to the
    gate by sitting close to it, which is the false CURRENT this exists to end.
    """
    hooks = (
        _PYTHON_HOOKS
        + _hook("eslint", stamped=True, gap=True)
        + _hook("tsc", stamped=True)
    )
    report = _quality_report(tmp_path, hooks)
    assert report.gates[0].stacks_not_covered == (
        "typescript: the eslint hook carries no gate-quality stamp — "
        "wired by hand, or arrived after gate-quality last ran",
    )


def test_the_report_says_which_stack_and_what_to_do(tmp_path: Path) -> None:
    from conftest import REPO_ROOT
    from register_check.register import load_register

    register, _ = load_register(REPO_ROOT / "controls.yaml")
    assert register is not None
    report = _quality_report(tmp_path, _PYTHON_HOOKS)
    text = render(report, register)
    assert "a stack applies that this gate has not wired — run it again" in text
    assert "1 owed a deployment" in text
