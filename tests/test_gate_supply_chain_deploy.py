"""`gate-supply-chain` deploys onto a repo with none of its config, and it verifies.

The third gate, and the first whose controls were **passing before it existed**.
`gate-secrets` and `gate-quality` each deployed something a bare repository
plainly lacked; SUP-003 reported PASS in this repository with no pre-commit hook
of any kind, because `actions-pinned-to-sha` reads the property — every `uses:`
is a SHA — out of the files on disk and nothing read either declared locus. So
the starting state below is chosen to make that visible: the adopter's workflows
are already SHA-pinned, and SUP-003 still fails.

**What this proves, and what it does not.** The artefacts come from the skill's
own shipped templates, rendered with the register's values, one copy of the
content. What is proved is that those artefacts, in a repository that had none,
are accepted by `standard-check`, and that removing any one of them is rejected.
What is *not* proved is that a model follows the prose in `SKILL.md` — no test
can establish that.

Every artefact the gate writes is deleted or broken in turn below, because a
verify step never observed failing is not known to work.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from conftest import REPO_ROOT, make_repo
from standard_check.cli import main
from standard_check.register import Register, load_register

SKILL = REPO_ROOT / "plugins/ee-standard/skills/gate-supply-chain"
REGISTER_PATH = REPO_ROOT / "controls.yaml"
SKILL_VERSION = "0.1.0"
ECOSYSTEM = "python"
LOCKFILE = "uv.lock"
_CONTROLS = ("SUP-001", "SUP-002", "SUP-003")

# A repository an adopter might bring: a lockfile it commits, a gating workflow
# whose one action reference is *already* SHA-pinned, and nothing else. The
# pinning is deliberate — it makes `actions-pinned-to-sha` pass from the first
# line of the test, so every failure below is about a locus rather than about
# the property, which is the distinction contract 14 drew.
_ADOPTER = {
    "pyproject.toml": '[project]\nname = "adopter"\nversion = "0.1.0"\n',
    "uv.lock": 'version = 1\nrequires-python = ">=3.13"\n',
    "src/app.py": 'def main() -> None:\n    print("hello")\n',
    ".github/workflows/ci.yml": (
        "name: CI\n\non:\n  push:\n    branches: [main]\n  pull_request:\n\n"
        "jobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - uses: actions/checkout@" + "a" * 40 + " # v7.0.1\n"
    ),
}


def _adopter_register(root: Path) -> Path:
    """This register, with a `tools:` table that is the adopter's own.

    `08-adopting.md` § 3.3 — *your register records your own files* — is not a
    documentation nicety here, it is what makes SUP-001 checkable at all.
    `tool_versions_match_register` reads `tools.<tool>.pinned_at`, and this
    repository's entries name `.devcontainer/setup.sh` and its own workflow. A
    fixture repository judged against them is told its tools are pinned at files
    it has never had — which is the § H2 defect, quoted back at a test.

    So the fixture keeps `standard-check`, whose authority is the lockfile it
    does commit, and drops the three literal tools it does not install.
    """
    document = yaml.safe_load(REGISTER_PATH.read_text(encoding="utf-8"))
    document["tools"] = {"standard-check": document["tools"]["standard-check"]}
    target = root / "adopter-register.yaml"
    target.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    for control in document["controls"] + document.get("meta_controls", []):
        adr = control.get("rationale_adr")
        if adr:
            (root / adr).parent.mkdir(parents=True, exist_ok=True)
            (root / adr).write_text("# ADR\n", encoding="utf-8")
    return target


def _register() -> Register:
    register, errors = load_register(REGISTER_PATH)
    assert register is not None, errors
    return register


def _render(template: str, register: Register) -> str:
    """A template with every placeholder filled from the register.

    This is the substitution the skill performs, and the only place the values
    can come from. A placeholder left unfilled is a failure here rather than an
    artefact deployed with `{{FROZEN_INSTALL}}` in it.
    """
    ecosystem = register.ecosystems[ECOSYSTEM]
    tool = "standard-check"
    text = template
    for placeholder, value in {
        "{{ECOSYSTEM}}": ECOSYSTEM,
        "{{ECOSYSTEM_SPELLING}}": ecosystem.dependabot[0],
        "{{FROZEN_INSTALL}}": ecosystem.frozen_install_command[LOCKFILE],
        "{{TOOL}}": tool,
        "{{TOOL_INVOCATION}}": register.tools[tool].invocation or "",
        "{{SKILL_VERSION}}": SKILL_VERSION,
        "{{REGISTER_VERSION}}": register.version,
        "{{REGISTER_CONTRACT}}": str(register.register_contract),
    }.items():
        text = text.replace(placeholder, value)
    assert "{{" not in text, f"a placeholder was not filled: {text}"
    return text


def _body(template: str, marker: str | None = None) -> str:
    """The template's payload, without the leading comment block explaining it.

    Dropped before substitution, not after: the comment talks *about* the
    placeholders, so rendering it first would leave a `{{` behind and the
    unfilled-placeholder check would fire on prose. `marker` is needed where the
    payload itself opens with a comment — `.github/dependabot.yml` carries its
    stamp at the top of the file, which is the one artefact where a whole-file
    stamp is right, and dropping every leading `#` would drop the stamp with the
    prose.
    """
    if marker is not None:
        template = template.split(marker, 1)[1]
        return template
    lines = template.splitlines(keepends=True)
    start = next(i for i, line in enumerate(lines) if not line.startswith("#"))
    return "".join(lines[start:])


def _deploy(root: Path, register: Register) -> None:
    """Write all four artefacts, as Steps 1, 2 and 4 of the skill describe.

    Step 3 — rewriting unpinned `uses:` references — writes nothing here,
    because the adopter's one reference is already a SHA. That is the skill's
    documented no-op path, and it is what makes this fixture's remaining
    failures about the loci alone.
    """
    steps = _render(_body((SKILL / "templates/ci-steps.yaml").read_text()), register)
    workflow = root / ".github/workflows/ci.yml"
    workflow.write_text(workflow.read_text(encoding="utf-8") + steps, encoding="utf-8")

    dependabot = _render(
        _body(
            (SKILL / "templates/dependabot.yaml").read_text(),
            marker="# --- .github/dependabot.yml ---\n",
        ),
        register,
    )
    # `github-actions` is not a package ecosystem detected from a manifest — it
    # is a repository feature, and the checker requires an entry for it wherever
    # workflows exist. The skill writes one entry per ecosystem; the template
    # carries one, and the second is the same shape with another spelling.
    dependabot += (
        "  - package-ecosystem: github-actions\n"
        "    directory: /\n"
        "    schedule:\n      interval: weekly\n"
    )
    (root / ".github/dependabot.yml").write_text(dependabot, encoding="utf-8")

    hook = _render(_body((SKILL / "templates/precommit-hook.yaml").read_text()), register)
    (root / ".pre-commit-config.yaml").write_text(
        "repos:\n  - repo: local\n    hooks:\n" + hook, encoding="utf-8"
    )


def _verdict(root: Path, capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    argv = ["--repo", str(root), "--register", str(_adopter_register(root)), "run"]
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


def test_the_frozen_command_is_one_the_checker_credits() -> None:
    """The pairing, checked here as well as at schema time.

    `frozen_install_command` is what this gate writes and `frozen_install` is
    what `ci-installs-frozen` credits. If they could disagree, the gate would
    deploy a step its own verify step refuses — so the schema refuses the
    register instead, and this is that rule stated where a reader of the gate
    will meet it.
    """
    ecosystem = _register().ecosystems[ECOSYSTEM]
    for lockfile, command in ecosystem.frozen_install_command.items():
        assert any(
            re.search(pattern, command) for pattern in ecosystem.frozen_install
        ), f"{lockfile}: {command!r} matches no frozen_install pattern"


def test_before_deploying_all_three_controls_fail(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The starting state, and the one that needed contract 14 to be visible.

    Note what passes: every action reference in this repository is already a
    commit SHA, so `actions-pinned-to-sha` is green. SUP-003 fails anyway,
    because neither of the two loci it declares is wired — which is precisely
    the claim that went unchecked from Phase 0 to contract 14.
    """
    make_repo(tmp_path, _ADOPTER)
    code, out = _verdict(tmp_path, capsys)
    assert code == 1
    assert "✓ file: actions-pinned-to-sha" in out
    assert "pre-commit locus" in out and "ci locus" in out
    assert "no CI step installs from the lockfile" in out or "frozen" in out
    assert "no tracked file carries a provenance stamp" in out


def test_after_deploying_every_locus_verifies(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The criterion. Exit 0 — none of the three declares a `remote` locus."""
    code, out = _verdict(deployed, capsys)
    assert code == 0, out
    for control in _CONTROLS:
        assert f"{control}  PASS" in out
    assert "3 passed, 0 failed" in out
    assert "SKIPPED" not in out and "incomplete" not in out


def test_the_deployed_stamps_record_the_register_they_came_from(deployed: Path) -> None:
    """One stamp per control per artefact, each naming the control whose locus it is."""
    register = _register()
    stamped = {
        ".github/workflows/ci.yml": {"SUP-001", "SUP-003"},
        ".github/dependabot.yml": {"SUP-002"},
        ".pre-commit-config.yaml": {"SUP-003"},
    }
    for path, controls in stamped.items():
        text = (deployed / path).read_text(encoding="utf-8")
        found = re.findall(
            r"ee-control: (\S+)\s+ee-skill: (\S+)\s+register: v(\S+)\s+register-contract: (\d+)",
            text,
        )
        assert {control for control, _, _, _ in found} == controls, path
        for _, skill, version, contract in found:
            assert skill == f"gate-supply-chain@{SKILL_VERSION}"
            assert version == register.version
            assert contract == str(register.register_contract)


def test_the_deployed_workflow_is_valid_yaml_that_still_gates(deployed: Path) -> None:
    doc = yaml.safe_load((deployed / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    triggers = doc["on"] if "on" in doc else doc[True]
    assert set(triggers) == {"push", "pull_request"}
    names = [step.get("name") for step in doc["jobs"]["build"]["steps"]]
    assert "Install dependencies (frozen)" in names
    assert "Supply chain" in names


def test_deleting_the_pre_commit_hook_is_caught(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """SUP-003's pre-commit locus, watched failing."""
    (deployed / ".pre-commit-config.yaml").unlink()
    make_repo(deployed, {})
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "SUP-003  FAIL" in out
    assert "pre-commit locus" in out
    # The property is untouched and says so. The two halves are separable, which
    # is what makes the locus check worth having.
    assert "✓ file: actions-pinned-to-sha" in out


def test_deleting_the_frozen_install_is_caught(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workflow = deployed / ".github/workflows/ci.yml"
    text = workflow.read_text(encoding="utf-8")
    workflow.write_text(
        text.replace(_register().ecosystems[ECOSYSTEM].frozen_install_command[LOCKFILE], "true"),
        encoding="utf-8",
    )
    make_repo(deployed, {})
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "SUP-001  FAIL" in out


def test_deleting_the_update_config_is_caught(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (deployed / ".github/dependabot.yml").unlink()
    make_repo(deployed, {})
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "SUP-002  FAIL" in out


def test_an_unpinned_action_added_after_deployment_is_caught(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The gate deployed, then the property broken — the other half of SUP-003."""
    workflow = deployed / ".github/workflows/ci.yml"
    workflow.write_text(
        workflow.read_text(encoding="utf-8").replace(
            "actions/checkout@" + "a" * 40, "actions/checkout@v4"
        ),
        encoding="utf-8",
    )
    make_repo(deployed, {})
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "SUP-003  FAIL" in out
    assert "actions/checkout@v4" in out
    # The loci are still wired, and say so.
    assert "✓ file: supply_chain_gate_wired_at_all_loci" in out


def test_a_hook_that_audits_another_control_is_not_this_locus(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Running the checker is not the same as gating on this control."""
    config = deployed / ".pre-commit-config.yaml"
    config.write_text(
        config.read_text(encoding="utf-8").replace("--control SUP-003", "--control SEC-001"),
        encoding="utf-8",
    )
    make_repo(deployed, {})
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "pre-commit locus" in out


def test_a_non_auditing_subcommand_is_not_this_locus(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`standard-check schema` validates the register and reads no control.

    This repository's own pre-commit config runs exactly that, and without this
    distinction it would have been credited with a SUP-003 gate that could never
    have failed it.
    """
    config = deployed / ".pre-commit-config.yaml"
    config.write_text(
        config.read_text(encoding="utf-8").replace("run --control SUP-003", "schema"),
        encoding="utf-8",
    )
    make_repo(deployed, {})
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "pre-commit locus" in out


def test_a_full_audit_reaches_the_control_without_a_selective_step(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The no-op path the skill documents, checked rather than asserted.

    A gating step running the checker with no `--control` audits every
    applicable control, so a repository that already has one needs no SUP-003
    step. That is why this repository's own workflow carries a stamp and no
    extra step — and if the checker did not credit it, the gate's instruction to
    write nothing would leave the control failing.
    """
    workflow = deployed / ".github/workflows/ci.yml"
    invocation = _register().tools["standard-check"].invocation
    workflow.write_text(
        workflow.read_text(encoding="utf-8").replace(
            f"{invocation} run --control SUP-003", f"{invocation}"
        ),
        encoding="utf-8",
    )
    make_repo(deployed, {})
    code, out = _verdict(deployed, capsys)
    assert code == 0, out
    assert "SUP-003  PASS" in out


def test_removing_the_stamps_is_caught(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A deployment whose provenance was stripped is not a deployment on record."""
    for name in (".pre-commit-config.yaml", ".github/workflows/ci.yml", ".github/dependabot.yml"):
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


def test_stamping_one_control_and_forgetting_the_others_is_caught(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Per control, not per gate — the distinction contract 12 drew, inherited.

    A gate owning three controls that stamped only one would otherwise be
    credited for all three: the read-back matches on the control being
    evaluated, so SUP-002's artefact going unstamped fails SUP-002 while the
    other two still pass.
    """
    path = deployed / ".github/dependabot.yml"
    kept = [
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if "ee-control:" not in line
    ]
    path.write_text("\n".join(kept) + "\n", encoding="utf-8")
    make_repo(deployed, {})
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "SUP-002  FAIL" in out
    assert "SUP-001  PASS" in out and "SUP-003  PASS" in out
