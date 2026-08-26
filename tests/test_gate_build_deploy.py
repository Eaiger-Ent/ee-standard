"""`gate-build` deploys onto a repo with none of its config, and it verifies.

The fourth gate, and the second whose controls were passing before it existed.
BLD-001 and DEV-001 declared `locus: [pre-commit, ci]` from Phase 0 and verified
only their *property* — the final `USER`, the declared container user, the lock
file's coverage — read out of the files on disk. A repository with no pre-commit
hook of any kind reported PASS on both. Same finding as SUP-003 at contract 14,
in the two controls the same survey listed beside it.

So the fixture below is a devcontainer that is **already correct**: a non-root
user, a digest-pinned image, a complete lock file. Every failure in this file is
about a locus or a stamp rather than about the property, which is the
distinction contract 15 drew.

Every artefact the gate writes is deleted or broken in turn, because a verify
step never observed failing is not known to work.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from conftest import REPO_ROOT, gate_contract, make_repo
from register_check.cli import main
from register_check.provenance import stamps_in
from register_check.register import Register, load_register

SKILL = REPO_ROOT / "plugins/control-register/skills/gate-build"
REGISTER_PATH = REPO_ROOT / "controls.yaml"
SKILL_VERSION = "0.1.0"
_CONTROLS = ("BLD-001", "DEV-001")

_IMAGE = "mcr.microsoft.com/devcontainers/base:trixie"
_DIGEST = "a" * 64
_FEATURE = "ghcr.io/devcontainers/features/github-cli:1"

# A repository an adopter might bring: a devcontainer whose *properties* are
# already right, a gating workflow, and no gate wiring of any kind. Chosen so
# that the three property blocks are green from the first line.
_ADOPTER = {
    ".devcontainer/devcontainer.json": json.dumps(
        {
            "name": "adopter",
            "image": f"{_IMAGE}@sha256:{_DIGEST}",
            "features": {_FEATURE: {}},
            "remoteUser": "vscode",
        },
        indent=2,
    )
    + "\n",
    ".devcontainer/devcontainer-lock.json": json.dumps(
        {"features": {_FEATURE: {"version": "1.0.0", "resolved": f"{_FEATURE}@sha256:{'b' * 64}"}}},
        indent=2,
    )
    + "\n",
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
    """A template with every placeholder filled from the register or the repo.

    A placeholder left unfilled is a failure here rather than an artefact
    deployed with `{{IMAGE_DIGEST}}` in it.
    """
    tool = "register-check"
    text = template
    for placeholder, value in {
        "{{TOOL}}": tool,
        "{{TOOL_INVOCATION}}": register.tools[tool].invocation or "",
        "{{CONTAINER_USER}}": "vscode",
        "{{IMAGE}}": _IMAGE,
        "{{IMAGE_DIGEST}}": _DIGEST,
        "{{SKILL_VERSION}}": SKILL_VERSION,
        "{{GATE_CONTRACT}}": gate_contract("gate-build"),
        "{{REGISTER_VERSION}}": register.version,
        "{{REGISTER_CONTRACT}}": str(register.register_contract),
    }.items():
        text = text.replace(placeholder, value)
    assert "{{" not in text, f"a placeholder was not filled: {text}"
    return text


def _body(template: str, comment: str = "#") -> str:
    """The template's payload, without the comment block explaining it.

    Dropped before substitution, not after: the comments talk *about* the
    placeholders, so rendering them first would leave a `{{` behind and the
    unfilled-placeholder check would fire on prose.
    """
    lines = template.splitlines(keepends=True)
    start = next(i for i, line in enumerate(lines) if not line.startswith(comment))
    return "".join(lines[start:])


def _deploy(root: Path, register: Register) -> None:
    """Write all three artefacts, as Steps 2 and 4 of the skill describe.

    Steps 1 and 3 write nothing here. The user is already non-root and the
    image already digest-pinned, which are the skill's documented adopt-and-
    stamp paths — and this repository has no `setup.sh` for Step 3 to create.
    """
    # Step 2 — merged into the devcontainer as text, not reparsed and dumped.
    # The stamps are `//` comments and a round trip through `json` would drop
    # them; the checker reads this file with a JSONC reader, so they stay legal.
    fragment = _render(
        _body((SKILL / "templates/devcontainer.json").read_text(), comment="//"),
        register,
    )
    inner = fragment.strip().removeprefix("{").removesuffix("}").strip("\n")
    devcontainer = root / ".devcontainer/devcontainer.json"
    existing = devcontainer.read_text(encoding="utf-8").rstrip().removesuffix("}").rstrip()
    devcontainer.write_text(existing + ",\n" + inner + "\n}\n", encoding="utf-8")

    # Step 4 — the pre-commit locus. One hook, two stamps.
    hook = _render(_body((SKILL / "templates/precommit-hook.yaml").read_text()), register)
    (root / ".pre-commit-config.yaml").write_text(
        "repos:\n  - repo: local\n    hooks:\n" + hook, encoding="utf-8"
    )

    # Step 4 — the ci locus. This adopter's workflow runs no audit at all, so
    # the step is written rather than skipped; the no-op path is exercised
    # separately below.
    steps = _render(_body((SKILL / "templates/ci-steps.yaml").read_text()), register)
    workflow = root / ".github/workflows/ci.yml"
    workflow.write_text(workflow.read_text(encoding="utf-8") + steps, encoding="utf-8")


def _verdict(root: Path, capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    argv = ["--repo", str(root), "--register", str(REGISTER_PATH), "run"]
    for control in _CONTROLS:
        argv += ["--control", control]
    code = main(argv)
    return code, capsys.readouterr().out


@pytest.fixture
def deployed(tmp_path: Path) -> Path:
    make_repo(tmp_path, _ADOPTER)
    _deploy(tmp_path, _register())
    make_repo(tmp_path, {})  # re-add and commit what the deployment wrote
    return tmp_path


def test_before_deploying_both_controls_fail_on_their_loci(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The starting state, and the one contract 15 made visible.

    Note what passes: the user is non-root, the image is digest-pinned and the
    lock file is complete. Both controls fail anyway, because neither of the two
    loci they declare is wired — precisely the claim that went unchecked from
    Phase 0 to contract 15.
    """
    make_repo(tmp_path, _ADOPTER)
    code, out = _verdict(tmp_path, capsys)
    assert code == 1
    assert "✓ file: devcontainer_user_is_non_root" in out
    assert "✓ file: devcontainer_image_digest_pinned" in out
    assert "✓ file: devcontainer_lock_covers_all_features" in out
    assert "pre-commit locus" in out and "ci locus" in out
    assert "no tracked file carries a provenance stamp" in out


def test_after_deploying_every_locus_verifies(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The criterion. Exit 0 — neither control declares a `remote` locus."""
    code, out = _verdict(deployed, capsys)
    assert code == 0, out
    for control in _CONTROLS:
        assert f"{control}  PASS" in out
    assert "2 passed, 0 failed" in out
    assert "SKIPPED" not in out and "incomplete" not in out


def test_hadolint_is_not_installed_by_this_gate(deployed: Path) -> None:
    """A tool the register does not pin is not a tool this gate installs.

    BLD-001's container half runs `hadolint`, and this fixture has no Dockerfile
    so that block skips. What matters is that the skill does not paper over the
    absent-tool case by installing something the register never pinned — an
    absent tool is UNCLASSIFIED (ADR 0016), which is a verdict rather than a
    thing to fix in a skill.
    """
    # Whitespace-normalised: the assertion is about what the skill says, not
    # about where a line happens to wrap.
    text = " ".join((SKILL / "SKILL.md").read_text(encoding="utf-8").split())
    assert "UNCLASSIFIED" in text
    assert "Do not install a tool the register does not pin" in text
    assert "hadolint" not in _register().tools


def test_one_hook_carries_a_stamp_for_each_control(deployed: Path) -> None:
    """Two controls, one command, two stamps — and the second is not decoration.

    The read-back matches on the control being evaluated, so a hook stamped for
    BLD-001 alone leaves DEV-001's pre-commit locus unrecorded even though the
    same command enforces it.
    """
    register = _register()
    stamped = {
        ".pre-commit-config.yaml": {"BLD-001", "DEV-001"},
        ".devcontainer/devcontainer.json": {"BLD-001", "DEV-001"},
        ".github/workflows/ci.yml": {"BLD-001", "DEV-001"},
    }
    for path, controls in stamped.items():
        text = (deployed / path).read_text(encoding="utf-8")
        found = stamps_in(text)
        assert {stamp.control for stamp in found} == controls, path
        for stamp in found:
            assert (stamp.skill, stamp.skill_version) == ("gate-build", SKILL_VERSION)
            assert stamp.register_version == register.version
            assert stamp.register_contract == register.register_contract
            assert stamp.gate_contract == int(gate_contract("gate-build"))


def test_the_deployed_devcontainer_is_still_readable(deployed: Path) -> None:
    """Merging as text must not break the file it merges into.

    The stamps are `//` comments, so the file is JSONC and the checker reads it
    with a JSONC reader. A round trip through a JSON writer would drop them —
    which is why the skill merges rather than reparses.
    """
    from register_check.repo import load_jsonc

    doc = load_jsonc(deployed / ".devcontainer/devcontainer.json")
    assert isinstance(doc, dict)
    assert doc["remoteUser"] == "vscode"
    assert doc["image"].endswith(f"@sha256:{_DIGEST}")


def test_deleting_the_pre_commit_hook_is_caught(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (deployed / ".pre-commit-config.yaml").unlink()
    make_repo(deployed, {})
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "BLD-001  FAIL" in out and "DEV-001  FAIL" in out
    assert "pre-commit locus" in out
    # The properties are untouched and say so. The two halves are separable,
    # which is what makes the locus check worth having.
    assert "✓ file: devcontainer_user_is_non_root" in out


def test_stamping_one_control_and_forgetting_the_other_is_caught(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """One command enforces both, and one stamp records only one."""
    for name in (
        ".pre-commit-config.yaml",
        ".devcontainer/devcontainer.json",
        ".github/workflows/ci.yml",
    ):
        path = deployed / name
        kept = [
            line
            for line in path.read_text(encoding="utf-8").splitlines()
            if "ee-control: DEV-001" not in line
        ]
        path.write_text("\n".join(kept) + "\n", encoding="utf-8")
    make_repo(deployed, {})
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "DEV-001  FAIL" in out
    assert "BLD-001  PASS" in out


def test_a_root_user_added_after_deployment_is_caught(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The gate deployed, then the property broken — the other half of BLD-001."""
    devcontainer = deployed / ".devcontainer/devcontainer.json"
    devcontainer.write_text(
        devcontainer.read_text(encoding="utf-8").replace(
            '"remoteUser": "vscode"', '"remoteUser": "root"'
        ),
        encoding="utf-8",
    )
    make_repo(deployed, {})
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "BLD-001  FAIL" in out
    # The loci are still wired, and say so.
    assert "✓ file: gate_wired_at_declared_loci" in out


def test_a_floating_image_tag_is_caught(deployed: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A complete lock file over a floating tag reads as solved and is not."""
    devcontainer = deployed / ".devcontainer/devcontainer.json"
    devcontainer.write_text(
        devcontainer.read_text(encoding="utf-8").replace(f"@sha256:{_DIGEST}", ""),
        encoding="utf-8",
    )
    make_repo(deployed, {})
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "DEV-001  FAIL" in out


def test_a_partial_lock_file_is_caught(deployed: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Phase 0.5's re-opened criterion, as a test.

    A lock file covering some features reads as solved and is not — the state
    that put a tick on an exit criterion and had it taken back.
    """
    devcontainer = deployed / ".devcontainer/devcontainer.json"
    doc = devcontainer.read_text(encoding="utf-8")
    devcontainer.write_text(
        doc.replace(
            f'"{_FEATURE}": {{}}',
            f'"{_FEATURE}": {{}},\n    "ghcr.io/devcontainers/features/node:1": {{}}',
        ),
        encoding="utf-8",
    )
    make_repo(deployed, {})
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "DEV-001  FAIL" in out
    assert "node" in out


def test_a_full_audit_reaches_both_controls_without_a_selective_step(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The no-op path the skill documents, checked rather than asserted.

    A gating step running the checker with no `--control` audits every
    applicable control, so a repository that already has one needs no step of
    its own — which is why this repository's own workflow carries stamps and no
    extra step. If the checker did not credit it, the skill's instruction to
    write nothing would leave both controls failing.
    """
    invocation = _register().tools["register-check"].invocation
    for name in (".pre-commit-config.yaml", ".github/workflows/ci.yml"):
        path = deployed / name
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                f"{invocation} run --control BLD-001 --control DEV-001", f"{invocation}"
            ),
            encoding="utf-8",
        )
    make_repo(deployed, {})
    code, out = _verdict(deployed, capsys)
    assert code == 0, out


def test_the_deployed_workflow_is_valid_yaml_that_still_gates(deployed: Path) -> None:
    """Appending a step must not break the file it appends to."""
    doc = yaml.safe_load((deployed / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    triggers = doc["on"] if "on" in doc else doc[True]
    assert set(triggers) == {"push", "pull_request"}
    names = [step.get("name") for step in doc["jobs"]["build"]["steps"]]
    assert "Build and environment" in names
