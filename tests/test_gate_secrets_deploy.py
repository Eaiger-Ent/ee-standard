"""`gate-secrets` deploys onto a repo with none of its config, and it verifies.

Phase 2's headline criterion. This repository cannot be the subject: it wired
`gitleaks` by hand long before there was a gate to do it, so "none of its
config" is a state it has not been in since Phase 0.5. The subject is a
throwaway repository built here with no secrets configuration at all.

**What this proves, and what it does not.** The artefacts come from the skill's
own shipped templates — `templates/precommit-hook.yaml` and
`templates/ci-steps.yaml`, rendered with the register's values, one copy of the
content. What is proved is that those artefacts, in a repository that had none,
are accepted by `register-check` at SEC-001's local loci, and that removing any
one of them is rejected. What is *not* proved is that a model follows the
prose in `SKILL.md` — no test can establish that, and claiming otherwise would
be the kind of tick this repository has re-opened seven times.

The second half matters as much as the first. Phase 2 says a verify step that
has never been observed failing is not known to work, so every artefact this
gate writes is deleted in turn below and the verdict checked.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

from conftest import REPO_ROOT, gate_contract, make_repo, requires_tool
from register_check.cli import main
from register_check.provenance import Stamp, stamps_in
from register_check.register import Register, load_register

SKILL = REPO_ROOT / "plugins/control-register/skills/gate-secrets"
REGISTER_PATH = REPO_ROOT / "controls.yaml"
SKILL_VERSION = "0.1.0"

# A repository an adopter might bring: some source, a CI workflow that gates,
# and nothing whatever to do with secrets.
_ADOPTER = {
    "src/app.py": 'def main() -> None:\n    print("hello")\n',
    ".github/workflows/ci.yml": (
        "name: CI\n\non:\n  push:\n    branches: [main]\n  pull_request:\n\n"
        "jobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - uses: actions/checkout@" + "a" * 40 + " # v7.0.1\n"
        "        with:\n          fetch-depth: 0\n"
        "      - run: echo build\n"
    ),
}


def _register() -> Register:
    register, errors = load_register(REGISTER_PATH)
    assert register is not None, errors
    return register


def _render(template: str, register: Register, tool: str) -> str:
    """A template with every placeholder filled from the register.

    This is the substitution the skill performs, and the only place the values
    can come from. A placeholder left unfilled is a failure here rather than an
    artefact deployed with `{{TOOL_VERSION}}` in it.
    """
    pinned = register.tools[tool]
    text = template
    for placeholder, value in {
        "{{TOOL}}": tool,
        "{{TOOL_VERSION}}": pinned.version or "",
        "{{TOOL_SHA256}}": pinned.sha256 or "",
        "{{TOOL_REPO}}": pinned.release_repo or "",
        "{{SKILL_VERSION}}": SKILL_VERSION,
        "{{GATE_CONTRACT}}": gate_contract("gate-secrets"),
        "{{REGISTER_VERSION}}": register.version,
        "{{REGISTER_CONTRACT}}": str(register.register_contract),
    }.items():
        text = text.replace(placeholder, value)
    assert "{{" not in text, f"a placeholder was not filled: {text}"
    return text


def _body(template: str) -> str:
    """The template's payload, without the leading comment block explaining it.

    Dropped before substitution, not after: the comment talks *about* the
    placeholders, so rendering it first would leave a `{{` behind and the
    unfilled-placeholder check would fire on prose.
    """
    lines = template.splitlines(keepends=True)
    start = next(i for i, line in enumerate(lines) if not line.startswith("#"))
    return "".join(lines[start:])


def _deploy(root: Path, register: Register, tool: str = "gitleaks") -> None:
    """Write both artefacts, as Steps 2 and 3 of the skill describe.

    The *content* is the shipped template's and nothing else — that is the
    property worth holding. Where the CI steps are placed is the skill's
    instruction to a reader, and the placement here is the simple case it
    describes: appended to a job that already runs on push and pull_request.
    """
    hook = _render(_body((SKILL / "templates/precommit-hook.yaml").read_text()), register, tool)
    (root / ".pre-commit-config.yaml").write_text(
        "repos:\n  - repo: local\n    hooks:\n" + hook, encoding="utf-8"
    )
    steps = _render(_body((SKILL / "templates/ci-steps.yaml").read_text()), register, tool)
    workflow = root / ".github/workflows/ci.yml"
    workflow.write_text(workflow.read_text(encoding="utf-8") + steps, encoding="utf-8")
    _ignore(root, register)


def _ignore(root: Path, register: Register) -> None:
    """Step 3.6, from register contract 18.

    One line per path and never a glob, because `.env.docker` is derived from
    `.env` and holds the same credentials — a glob that later misses a file
    gives no signal, and the per-path form makes a missing one visible. The
    paths are the register's `args.paths`; this function knows none of them.
    """
    paths = _secret_paths(register)
    stamp = (
        f"# ee-control: SEC-001  ee-skill: gate-secrets@{SKILL_VERSION}  "
        f"register: v{register.version}  register-contract: {register.register_contract}\n"
    )
    gitignore = root / ".gitignore"
    existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    gitignore.write_text(existing + stamp + "".join(f"{p}\n" for p in paths), encoding="utf-8")


def _secret_paths(register: Register) -> list[str]:
    """SEC-001's `secret_files_are_gitignored` block, `args.paths`."""
    control = next(c for c in register.controls if c.id == "SEC-001")
    block = next(b for b in control.verify if b.assert_name == "secret_files_are_gitignored")
    paths = block.args["paths"]
    assert isinstance(paths, list), "the register's `paths:` must be a list"
    return [str(entry) for entry in paths]


def _verdict(root: Path, capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    code = main(
        ["--repo", str(root), "--register", str(REGISTER_PATH), "run", "--control", "SEC-001"]
    )
    return code, capsys.readouterr().out


@pytest.fixture
def deployed(tmp_path: Path) -> Path:
    make_repo(tmp_path, _ADOPTER)
    _deploy(tmp_path, _register())
    make_repo(tmp_path, {})  # re-add and commit what the deployment wrote
    return tmp_path


def test_before_deploying_the_control_fails_at_both_local_loci(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The starting state, stated rather than assumed."""
    make_repo(tmp_path, _ADOPTER)
    code, out = _verdict(tmp_path, capsys)
    assert code == 1
    assert "pre-commit locus" in out and "ci locus" in out
    assert "no tracked file carries a provenance stamp" in out


@requires_tool("gitleaks")
def test_after_deploying_both_local_loci_verify(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The criterion. Exit 3, not 0, and the difference is the point.

    Both local blocks pass. SEC-001's remote block — GitHub push protection —
    reports `SKIPPED (no credentials)` until Phase 3, so the run is incomplete
    rather than clean. Reporting this as a pass would claim a locus the gate has
    not touched (ADR 0016).
    """
    code, out = _verdict(deployed, capsys)
    assert code == 3, out
    assert "✓ file: secrets_gate_wired_at_all_loci" in out
    assert "✓ file: provenance_stamp_present" in out
    assert "SKIPPED (no credentials)" in out
    assert "incomplete" in out


def test_the_deployed_stamp_records_the_register_it_came_from(deployed: Path) -> None:
    register = _register()
    text = (deployed / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    found = stamps_in(text)
    assert len(found) == 1, found
    assert found[0] == Stamp(
        control="SEC-001",
        skill="gate-secrets",
        skill_version=SKILL_VERSION,
        register_version=register.version,
        register_contract=register.register_contract,
        gate_contract=int(gate_contract("gate-secrets")),
    )


def test_the_deployed_workflow_is_valid_yaml_that_still_gates(deployed: Path) -> None:
    """Appending steps must not break the file it appends to."""
    doc = yaml.safe_load((deployed / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    triggers = doc["on"] if "on" in doc else doc[True]
    assert set(triggers) == {"push", "pull_request"}
    names = [step.get("name") for step in doc["jobs"]["build"]["steps"]]
    assert "Secret scan" in names


def test_deleting_the_ci_steps_is_caught(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workflow = deployed / ".github/workflows/ci.yml"
    text = workflow.read_text(encoding="utf-8")
    workflow.write_text(text[: text.index("      - name: Install gitleaks")], encoding="utf-8")
    make_repo(deployed, {})
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "ci locus" in out


def test_deleting_the_pre_commit_hook_is_caught(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (deployed / ".pre-commit-config.yaml").unlink()
    make_repo(deployed, {})
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "pre-commit locus" in out


def test_installing_the_scanner_is_not_running_it(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Found while building `gate-iac`, and it is this gate's own template.

    Before register contract 16 the ci-locus check was a substring search over a
    step's whole `run:` text — and `templates/ci-steps.yaml` mentions the tool
    six times in its *install* step: in a URL, in a tarball name, and as an
    argument to `tar`, `install` and `rm`. So a workflow that installed the
    scanner and never ran it satisfied SEC-001's ci locus, and deleting the
    secret-scan step left the control green.

    Contract 11 added that check to close a locus nothing read. This is the same
    defect one level in: a locus read by something that could not tell running a
    tool from mentioning it.
    """
    workflow = deployed / ".github/workflows/ci.yml"
    text = workflow.read_text(encoding="utf-8")
    # Delete the scan step and keep the install step — the state that used to
    # pass.
    workflow.write_text(text[: text.index("      - name: Secret scan")], encoding="utf-8")
    make_repo(deployed, {})
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "ci locus" in out
    # The install step is still there, and is still not the locus.
    assert "Install gitleaks" in workflow.read_text(encoding="utf-8")


def test_a_suppressed_ci_step_is_not_the_ci_locus(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Found while building `gate-iac`, and it applies here too.

    SEC-001 has no `no-failure-suppression` block of its own, so before register
    contract 16 a secret-scan step carrying `continue-on-error: true` counted as
    the ci locus being wired. The scanner ran, the job succeeded whatever it
    found, and the control reported PASS — *declared and unreachable* one level
    in from the `workflow_dispatch` case § D caught.
    """
    workflow = deployed / ".github/workflows/ci.yml"
    workflow.write_text(
        workflow.read_text(encoding="utf-8").replace(
            "      - name: Secret scan",
            "      - name: Secret scan\n        continue-on-error: true",
        ),
        encoding="utf-8",
    )
    make_repo(deployed, {})
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "ci locus" in out


def test_removing_the_stamps_is_caught(deployed: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A deployment whose provenance was stripped is not a deployment on record.

    Three files, not two: register contract 18 added the ignore rule, and this
    test caught the omission itself — stripping two of three stamps still left
    one, and `provenance_stamp_present` passed on it. Which is the assert
    behaving correctly and the test having gone stale.
    """
    for name in (".pre-commit-config.yaml", ".github/workflows/ci.yml", ".gitignore"):
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


def test_an_ignore_file_hiding_a_tracked_source_file_is_caught(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The gate deployed, then weakened — ADR 0019, end to end."""
    (deployed / ".gitleaksignore").write_text(
        "deadbeef:src/app.py:generic-api-key:1\n", encoding="utf-8"
    )
    make_repo(deployed, {})
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "src/app.py" in out


# --- Step 3.6, the rule that acts before a credential is a git object -------


def test_the_deployment_ignores_the_files_that_hold_credentials(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Register contract 18's block, passing after a deployment.

    Before contract 18 this repository's `.gitignore` and the shipped
    devcontainer template both carried a comment saying *SEC-001 depends on
    these two lines*, and nothing read either. A dependency stated in prose is
    the second copy the register exists to prevent.
    """
    _, out = _verdict(deployed, capsys)
    assert "✓ file: secret_files_are_gitignored" in out


def test_deleting_the_ignore_rule_is_caught(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A verify step never observed failing is not known to work."""
    (deployed / ".gitignore").unlink()
    make_repo(deployed, {})
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "is not ignored" in out


def test_an_ignore_rule_the_deployment_did_not_commit_is_caught(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The quiet failure: it protects this clone and no other.

    `git check-ignore` exits 0 either way, so a check that stopped at the exit
    code would report the same pass for a rule nobody else will ever have.
    """
    rules = (deployed / ".gitignore").read_text(encoding="utf-8")
    (deployed / ".gitignore").unlink()
    exclude = deployed / ".git/info/exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    exclude.write_text(rules, encoding="utf-8")
    make_repo(deployed, {})
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "does not track" in out


def test_a_credential_file_already_in_git_is_reported_as_tracked(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The case an ignore rule cannot fix, told apart from the case it can.

    The remedies differ — a rule fixes "not ignored", and only a history rewrite
    and a rotated credential fix this — so a checker that conflated them would
    recommend the wrong one.
    """
    register = _register()
    leaked = deployed / _secret_paths(register)[0]
    leaked.parent.mkdir(parents=True, exist_ok=True)
    leaked.write_text("GITHUB_TOKEN=ghp_real\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(deployed), "add", "-f", str(leaked)], check=True)
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "is tracked" in out
