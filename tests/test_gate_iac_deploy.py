"""`gate-iac` deploys onto a repo with none of its config, and it verifies.

The fifth gate, and the last of the four unread loci the contract-14 survey
listed. IAC-001 declared `locus: [pre-commit, ci]` from Phase 0 and verified
neither: its two `kind: command` blocks run the analysers over the files, which
is a different claim from *something enforces this before a commit lands and
before a merge does*.

This gate cannot be exercised against this repository at all — it has no `*.tf`,
so IAC-001 reports `SKIPPED (predicate)` and always will. The fixture below is a
throwaway repository with Terraform in it, which is the only way the predicate is
satisfied and therefore the only way any of this is checked. A gate whose tests
all ran against a repository the control skips would be a gate nothing had run.

`UNCLASSIFIED` is the verdict to watch here, and it is deliberate: this
register pins neither analyser, so the two command blocks report *cannot verify*
rather than passing (ADR 0016). The wiring blocks are what these tests are
about, and they are checked independently of it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from conftest import REPO_ROOT, make_repo
from standard_check.cli import main
from standard_check.register import Register, load_register

SKILL = REPO_ROOT / "plugins/ee-standard/skills/gate-iac"
REGISTER_PATH = REPO_ROOT / "controls.yaml"
SKILL_VERSION = "0.1.0"

# A repository an adopter might bring: some Terraform, a gating workflow, and no
# analysis of any kind. The `*.tf` is what satisfies IAC-001's predicate — the
# predicate is evaluated against files and never self-declared, so without it
# every test below would pass vacuously on a skip.
_ADOPTER = {
    "infra/main.tf": (
        'terraform {\n  required_version = ">= 1.6"\n}\n\n'
        'resource "null_resource" "example" {}\n'
    ),
    ".github/workflows/ci.yml": (
        "name: CI\n\non:\n  push:\n    branches: [main]\n  pull_request:\n\n"
        "jobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - uses: actions/checkout@" + "a" * 40 + " # v7.0.1\n"
    ),
}


def _register() -> Register:
    register, errors = load_register(REGISTER_PATH)
    assert register is not None, errors
    return register


def _render(template: str, register: Register) -> str:
    tool = "standard-check"
    text = template
    for placeholder, value in {
        "{{TOOL}}": tool,
        "{{TOOL_INVOCATION}}": register.tools[tool].invocation or "",
        "{{SKILL_VERSION}}": SKILL_VERSION,
        "{{REGISTER_VERSION}}": register.version,
        "{{REGISTER_CONTRACT}}": str(register.register_contract),
    }.items():
        text = text.replace(placeholder, value)
    assert "{{" not in text, f"a placeholder was not filled: {text}"
    return text


def _body(template: str) -> str:
    """The template's payload, without the comment block explaining it."""
    lines = template.splitlines(keepends=True)
    start = next(i for i, line in enumerate(lines) if not line.startswith("#"))
    return "".join(lines[start:])


def _deploy(root: Path, register: Register) -> None:
    """Write both artefacts, as Step 2 of the skill describes.

    Step 1 writes nothing: the register pins neither analyser, which is the
    skill's documented do-not-install path. Step 3 writes nothing either — this
    adopter has no predecessor tool and no suppression file.
    """
    hook = _render(_body((SKILL / "templates/precommit-hook.yaml").read_text()), register)
    (root / ".pre-commit-config.yaml").write_text(
        "repos:\n  - repo: local\n    hooks:\n" + hook, encoding="utf-8"
    )
    steps = _render(_body((SKILL / "templates/ci-steps.yaml").read_text()), register)
    workflow = root / ".github/workflows/ci.yml"
    workflow.write_text(workflow.read_text(encoding="utf-8") + steps, encoding="utf-8")


def _verdict(root: Path, capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    code = main(
        ["--repo", str(root), "--register", str(REGISTER_PATH), "run", "--control", "IAC-001"]
    )
    return code, capsys.readouterr().out


@pytest.fixture
def deployed(tmp_path: Path) -> Path:
    make_repo(tmp_path, _ADOPTER)
    _deploy(tmp_path, _register())
    make_repo(tmp_path, {})  # re-add and commit what the deployment wrote
    return tmp_path


def test_a_repo_with_no_terraform_is_skipped_not_deployed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The predicate, which is why this gate needs a fixture at all.

    This repository is in exactly this state, permanently. A gate deployed here
    would be a hook that can only ever be noise, and the skill says so rather
    than writing one.
    """
    make_repo(tmp_path, {"README.md": "# no infrastructure here\n"})
    code, out = _verdict(tmp_path, capsys)
    assert code == 0
    assert "SKIPPED (predicate)" in out
    assert "terraform" in out


def test_before_deploying_both_loci_fail(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The starting state, and the one contract 16 made visible."""
    make_repo(tmp_path, _ADOPTER)
    code, out = _verdict(tmp_path, capsys)
    assert code == 1
    assert "pre-commit locus" in out and "ci locus" in out
    assert "no tracked file carries a provenance stamp" in out
    assert "SKIPPED (predicate)" not in out


def test_after_deploying_the_wiring_verifies(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The criterion, and the verdict it honestly produces.

    Both wiring blocks pass. The two analyser blocks report `UNCLASSIFIED`,
    because this register pins neither `checkov` nor `tflint` and an absent tool
    is *cannot verify* rather than a pass (ADR 0016). Reporting this run as a
    clean deployment would be exactly the green-over-nothing this repository
    exists to prevent — so the exit code is not `0`, and that is correct.
    """
    code, out = _verdict(deployed, capsys)
    assert "✓ file: gate_wired_at_declared_loci" in out
    assert "✓ file: provenance_stamp_present" in out
    assert "UNCLASSIFIED" in out
    assert code != 0
    assert "pre-commit locus" not in out and "ci locus" not in out


def test_the_deployed_stamps_record_the_register_they_came_from(deployed: Path) -> None:
    register = _register()
    for path in (".pre-commit-config.yaml", ".github/workflows/ci.yml"):
        text = (deployed / path).read_text(encoding="utf-8")
        found = re.findall(
            r"ee-control: (\S+)\s+ee-skill: (\S+)\s+register: v(\S+)\s+register-contract: (\d+)",
            text,
        )
        assert {control for control, _, _, _ in found} == {"IAC-001"}, path
        for _, skill, version, contract in found:
            assert skill == f"gate-iac@{SKILL_VERSION}"
            assert version == register.version
            assert contract == str(register.register_contract)


def test_the_deployed_workflow_is_valid_yaml_that_still_gates(deployed: Path) -> None:
    doc = yaml.safe_load((deployed / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    triggers = doc["on"] if "on" in doc else doc[True]
    assert set(triggers) == {"push", "pull_request"}
    names = [step.get("name") for step in doc["jobs"]["build"]["steps"]]
    assert "Infrastructure analysis" in names


def test_one_hook_runs_the_control_and_the_control_runs_both_analysers() -> None:
    """Why there is one hook rather than two.

    Two hooks each invoking one analyser would be two statements of what
    "analysed" means, free to drift from each other and from the register. The
    template names neither analyser, and the register names both — this is that
    property, checked rather than described.
    """
    template = (SKILL / "templates/precommit-hook.yaml").read_text(encoding="utf-8")
    entry = next(line for line in _body(template).splitlines() if "entry:" in line)
    assert "--control IAC-001" in entry
    analysers = [
        block.run
        for block in next(c for c in _register().controls if c.id == "IAC-001").verify
        if block.run
    ]
    assert len(analysers) == 2
    for run in analysers:
        assert run.split()[0] not in entry


def test_the_register_owns_the_analyser_arguments() -> None:
    """A control whose arguments a skill chooses is a control nobody can review.

    The skill reads `run:` strings verbatim and never rewrites them, so the
    arguments appear in `controls.yaml` and nowhere under `plugins/`.
    """
    runs = [
        block.run
        for block in next(c for c in _register().controls if c.id == "IAC-001").verify
        if block.run
    ]
    skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    for run in runs:
        # The flags may be *quoted* in the prose that explains why they are the
        # register's; what must not exist is the whole invocation, which would
        # be a second copy of it.
        assert run not in skill_text, run


def test_deleting_the_pre_commit_hook_is_caught(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (deployed / ".pre-commit-config.yaml").unlink()
    make_repo(deployed, {})
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "pre-commit locus" in out


def test_deleting_the_ci_step_is_caught(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workflow = deployed / ".github/workflows/ci.yml"
    text = workflow.read_text(encoding="utf-8")
    workflow.write_text(text[: text.index("      # ee-control: IAC-001")], encoding="utf-8")
    make_repo(deployed, {})
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "ci locus" in out


def test_a_suppressed_ci_step_is_not_a_gate(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A step that reports findings without blocking is a gate that is not one."""
    workflow = deployed / ".github/workflows/ci.yml"
    workflow.write_text(
        workflow.read_text(encoding="utf-8").replace(
            "      - name: Infrastructure analysis",
            "      - name: Infrastructure analysis\n        continue-on-error: true",
        ),
        encoding="utf-8",
    )
    make_repo(deployed, {})
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "ci locus" in out


def test_removing_the_stamps_is_caught(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    for name in (".pre-commit-config.yaml", ".github/workflows/ci.yml"):
        path = deployed / name
        kept = [
            line
            for line in path.read_text(encoding="utf-8").splitlines()
            if "ee-control:" not in line
        ]
        path.write_text("\n".join(kept) + "\n", encoding="utf-8")
    make_repo(deployed, {})
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "provenance stamp" in out


def test_a_full_audit_reaches_the_control_without_a_selective_step(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The no-op path the skill documents, checked rather than asserted."""
    invocation = _register().tools["standard-check"].invocation
    for name in (".pre-commit-config.yaml", ".github/workflows/ci.yml"):
        path = deployed / name
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                f"{invocation} run --control IAC-001", f"{invocation}"
            ),
            encoding="utf-8",
        )
    make_repo(deployed, {})
    _, out = _verdict(deployed, capsys)
    assert "✓ file: gate_wired_at_declared_loci" in out
    assert "pre-commit locus" not in out and "ci locus" not in out
