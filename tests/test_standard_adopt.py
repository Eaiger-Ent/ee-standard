"""`standard-adopt` end to end: plan → deploy → verify, on a scratch repository.

Phase 2's last criterion reads *"plan → confirm → deploy → verify → commit, with
the verify step genuinely able to fail"*, and the last clause is the one that
matters: **a verify step that has never been observed failing is not known to
work**, so a deployed config is deliberately broken below and the run is checked.

**What this proves, and what it does not.** It drives the sequence the skill
describes — every gate, in the skill's own dispatch order, using each gate's
shipped templates and no other copy of their content — against a repository that
starts with none of it. What is proved is that the pipeline works: that the six
gates compose, that their artefacts do not overwrite each other, that the order
matters in the way the skill says, and that the whole-register verify catches a
break. What is **not** proved is that a model follows the prose in `SKILL.md`;
no test can establish that, and claiming otherwise would be the kind of tick
this repository has re-opened seven times.

The composition is the part no per-gate test could reach. Each gate's own test
deploys it alone into a clean repository. Here all six write into the same
`.pre-commit-config.yaml`, the same workflow and the same `setup.sh`, which is
where "grouped by the artefact they write" is either true or discovered not to
be.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from conftest import REPO_ROOT, make_repo
from standard_check.cli import main
from standard_check.register import Register, load_register

PLUGIN = REPO_ROOT / "plugins/ee-standard"
SKILL = PLUGIN / "skills/standard-adopt"
TEMPLATE = PLUGIN / "templates/devcontainer"
REGISTER_PATH = REPO_ROOT / "controls.yaml"
SKILL_VERSION = "0.1.0"

#: The dispatch order Step 4 states. Read from the skill rather than restated,
#: so a reordering there fails here rather than drifting silently.
_ORDER_ROW = re.compile(r"^\|\s*(\d)\s*\|\s*`(gate-[a-z-]+)`\s*\|", re.MULTILINE)

# A repository an adopter might plausibly bring to the front door: a Python
# project with a lockfile, one already-pinned workflow that gates, and no
# conformance wiring of any kind.
_ADOPTER = {
    "pyproject.toml": '[project]\nname = "adopter"\nversion = "0.1.0"\n',
    "uv.lock": (
        'version = 1\nrequires-python = ">=3.13"\n\n'
        '[[package]]\nname = "ruff"\nversion = "0.0.0"\n\n'
        '[[package]]\nname = "mypy"\nversion = "0.0.0"\n'
    ),
    "src/app.py": 'def main() -> None:\n    print("hello")\n',
    ".github/workflows/ci.yml": (
        "name: CI\n\non:\n  push:\n    branches: [main]\n  pull_request:\n\n"
        "jobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - uses: actions/checkout@" + "a" * 40 + " # v7.0.1\n"
        "        with:\n          fetch-depth: 0\n"
    ),
}

# Controls this adoption is expected to reach. DOC-001 belongs to `lint-md` in
# another plugin and IAC-001 has no Terraform to analyse — both are planned
# rather than deployed, which is what the plan-completeness test below is about.
_DEPLOYED = (
    "BLD-001",
    "DEV-001",
    "SUP-001",
    "SUP-002",
    "SUP-003",
    "SEC-001",
    "SEC-002",
    "LNT-001",
    "TYP-001",
    "TST-001",
    "CI-001",
)


def _register() -> Register:
    register, errors = load_register(REGISTER_PATH)
    assert register is not None, errors
    return register


def _adopter_register(root: Path) -> Path:
    """This register, with a `tools:` table that is the adopter's own.

    `08-adopting.md` § 3.6 — *your register records your own files*. This
    repository's `tools:` entries name `.devcontainer/setup.sh` and its own
    workflow as sites that repeat a literal version, and a scratch repository
    judged against them is told its tools are pinned at files it never had.

    `standard-check` stays, whose authority is the lockfile the adopter commits.
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


def _fill(text: str, register: Register, gate: str, **extra: str) -> str:
    """A shipped template with every placeholder filled from the register.

    One substitution map for all six gates. A placeholder no gate fills is a
    template shipped with `{{` in it, which is a deployment nobody could use.
    """
    ecosystem = register.ecosystems["python"]
    stack = register.stacks["python"]
    values = {
        "{{TOOL}}": "standard-check",
        "{{TOOL_INVOCATION}}": register.tools["standard-check"].invocation or "",
        "{{ECOSYSTEM}}": "python",
        "{{ECOSYSTEM_SPELLING}}": ecosystem.dependabot[0],
        "{{FROZEN_INSTALL}}": ecosystem.frozen_install_command["uv.lock"],
        "{{STACK}}": "python",
        "{{SOURCE_PATTERN}}": r"\.pyi?$",
        "{{LINT_TOOL}}": stack.gates["lint"].tool,
        "{{LINT_HOOK_ID}}": stack.gates["lint"].pre_commit or "",
        "{{LINT_INVOCATION}}": stack.gates["lint"].invocation,
        "{{EDITOR_EXTENSION}}": stack.gates["lint"].editor_extension or "",
        "{{TYPECHECK_TOOL}}": stack.gates["typecheck"].tool,
        "{{TYPECHECK_HOOK_ID}}": stack.gates["typecheck"].pre_commit or "",
        "{{TYPECHECK_INVOCATION}}": stack.gates["typecheck"].invocation,
        "{{COVERAGE_KEY}}": stack.gates["typecheck"].coverage_key or "",
        "{{TEST_COMMAND}}": "uv run pytest",
        "{{SKILL_VERSION}}": SKILL_VERSION,
        "{{REGISTER_VERSION}}": register.version,
        "{{REGISTER_CONTRACT}}": str(register.register_contract),
        **extra,
    }
    for placeholder, value in values.items():
        text = text.replace(placeholder, value)
    assert "{{" not in text, f"{gate}: a placeholder was not filled: {text[:200]}"
    return text


def _payload(path: Path, comment: str = "#", marker: str | None = None) -> str:
    """A template's payload, without the comment block explaining it.

    `marker` selects one shape from a template that ships more than one — the
    editor locus has a devcontainer shape and a `.vscode/` shape, and a gate
    writes one, never both. Everything from the marker line to the next
    `--- ` section is that shape.
    """
    text = path.read_text(encoding="utf-8")
    if marker is not None:
        after = text.split(marker, 1)[1]
        return after.split("\n" + comment + " ---", 1)[0].split("\n", 1)[1]
    lines = text.splitlines(keepends=True)
    start = next(i for i, line in enumerate(lines) if not line.startswith(comment))
    return "".join(lines[start:])


def _hooks(root: Path, block: str) -> None:
    """Append hooks to the one `.pre-commit-config.yaml`, creating it if absent.

    Every gate is told to do exactly this and to preserve what is already there.
    Doing it here in one helper is what makes the composition real: four gates
    write into this file, and if any of them replaced it the later ones would
    silently drop the earlier ones' hooks.
    """
    path = root / ".pre-commit-config.yaml"
    if not path.exists():
        path.write_text("repos:\n  - repo: local\n    hooks:\n", encoding="utf-8")
    path.write_text(path.read_text(encoding="utf-8") + block, encoding="utf-8")


def _steps(root: Path, block: str) -> None:
    """Append steps to the one gating workflow."""
    path = root / ".github/workflows/ci.yml"
    path.write_text(path.read_text(encoding="utf-8") + block, encoding="utf-8")


def _gate(name: str) -> Path:
    return PLUGIN / "skills" / name / "templates"


def _deploy_all(root: Path, register: Register) -> None:
    """Every gate, in the dispatch order Step 4 states.

    The order is asserted against the skill separately; this is it being *used*,
    which is the only way the first two positions are load-bearing rather than
    decorative.
    """
    # 1 — gate-build. Owns `.devcontainer/`, and what it copies is the shipped
    # template. The template's user and image are already correct, so this is
    # the skill's documented adopt-and-stamp path: the two stamps go in and
    # nothing else moves.
    shutil.copytree(TEMPLATE, root / ".devcontainer")
    (root / ".devcontainer/README.md").unlink()
    for path in (root / ".devcontainer").rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            if "{{PROJECT_NAME}}" in text:
                path.write_text(text.replace("{{PROJECT_NAME}}", "adopter"), encoding="utf-8")

    fragment = _fill(
        _payload(
            _gate("gate-build") / "devcontainer.json",
            comment="//",
            marker="// --- .devcontainer/devcontainer.json — merged into what is already there ---",
        ),
        register,
        "gate-build",
        **{"{{CONTAINER_USER}}": "vscode", "{{IMAGE}}": "x", "{{IMAGE_DIGEST}}": "y"},
    )
    devcontainer = root / ".devcontainer/devcontainer.json"
    text = devcontainer.read_text(encoding="utf-8")
    for control, key in (("BLD-001", '"remoteUser"'), ("DEV-001", '"image"')):
        stamp = next(
            line.strip() for line in fragment.splitlines() if f"ee-control: {control}" in line
        )
        text = text.replace(f"  {key}", f"  {stamp}\n  {key}", 1)
    devcontainer.write_text(text, encoding="utf-8")
    _hooks(
        root, _fill(_payload(_gate("gate-build") / "precommit-hook.yaml"), register, "gate-build")
    )
    _steps(root, _fill(_payload(_gate("gate-build") / "ci-steps.yaml"), register, "gate-build"))

    # 2 — gate-supply-chain. The frozen install first, so later steps run after it.
    supply = _gate("gate-supply-chain")
    _steps(root, _fill(_payload(supply / "ci-steps.yaml"), register, "gate-supply-chain"))
    dependabot = _fill(
        _payload(
            supply / "dependabot.yaml",
            marker="# --- .github/dependabot.yml ---",
        ),
        register,
        "gate-supply-chain",
    ) + (
        "  - package-ecosystem: github-actions\n    directory: /\n"
        "    schedule:\n      interval: weekly\n"
        "  - package-ecosystem: devcontainers\n    directory: /\n"
        "    schedule:\n      interval: weekly\n"
    )
    (root / ".github/dependabot.yml").write_text(dependabot, encoding="utf-8")
    _hooks(
        root,
        _fill(_payload(supply / "precommit-hook.yaml"), register, "gate-supply-chain"),
    )

    # 3 — gate-secrets.
    secrets = _gate("gate-secrets")
    scanner = {
        "{{TOOL}}": "gitleaks",
        "{{TOOL_VERSION}}": "0.0.0",
        "{{TOOL_SHA256}}": "0" * 64,
        "{{TOOL_REPO}}": "example/gitleaks",
    }
    _hooks(
        root, _fill(_payload(secrets / "precommit-hook.yaml"), register, "gate-secrets", **scanner)
    )
    _steps(root, _fill(_payload(secrets / "ci-steps.yaml"), register, "gate-secrets", **scanner))

    # 4 — gate-quality. Configuration first, then its three loci.
    pyproject = root / "pyproject.toml"
    pyproject.write_text(
        pyproject.read_text(encoding="utf-8")
        + '\n[tool.ruff]\n\n[tool.mypy]\nstrict = true\nfiles = ["src"]\n',
        encoding="utf-8",
    )
    # The editor locus, merged into the list the template deliberately left
    # empty rather than appended as a second `customizations` block. Two lists
    # of extensions is the second copy this standard exists to prevent, and the
    # template's comment says so at the empty list.
    editor = _fill(
        _payload(
            _gate("gate-quality") / "editor-extensions.json",
            comment="//",
            marker="// --- .devcontainer/devcontainer.json",
        ),
        register,
        "gate-quality",
    )
    extension = re.search(r'"extensions": \[([^\]]*)\]', editor)
    assert extension is not None, editor
    stamp = next(line.strip() for line in editor.splitlines() if "ee-control:" in line)
    devcontainer.write_text(
        devcontainer.read_text(encoding="utf-8").replace(
            '"extensions": []',
            f"{stamp}\n      \"extensions\": [{extension.group(1)}]",
            1,
        ),
        encoding="utf-8",
    )
    _hooks(
        root,
        _fill(_payload(_gate("gate-quality") / "precommit-hooks.yaml"), register, "gate-quality"),
    )
    _steps(
        root, _fill(_payload(_gate("gate-quality") / "ci-steps.yaml"), register, "gate-quality")
    )

    # 5 — gate-iac. Not applicable here: no `*.tf`, so the gate writes nothing.

    # 6 — gate-repo. Last, and its artefact is a record rather than a file that
    # enforces.
    ruleset = root / ".github/rulesets/default-branch.json"
    ruleset.parent.mkdir(parents=True, exist_ok=True)
    ruleset.write_text(
        _fill(
            _payload(
                _gate("gate-repo") / "default-branch.json",
                comment="//",
                marker="// --- .github/rulesets/default-branch.json ---",
            ),
            register,
            "gate-repo",
            **{"{{RULESET_NAME}}": "default-branch-protection"},
        ),
        encoding="utf-8",
    )


def _verdict(root: Path, capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    """The whole register, as Step 5 runs it — not only what was deployed."""
    code = main(["--repo", str(root), "--register", str(_adopter_register(root)), "run"])
    return code, capsys.readouterr().out


@pytest.fixture
def adopted(tmp_path: Path) -> Path:
    make_repo(tmp_path, _ADOPTER)
    _deploy_all(tmp_path, _register())
    make_repo(tmp_path, {})
    return tmp_path


def test_the_dispatch_order_is_the_one_the_skill_states() -> None:
    """The order is load-bearing in its first two positions, and stated once.

    `gate-build` creates `.devcontainer/setup.sh`, which two later gates write
    their own regions into. `gate-supply-chain` writes the frozen install every
    other gate's CI steps run after. Read from the skill so a reordering there
    fails here rather than drifting from what this test exercises.
    """
    rows = _ORDER_ROW.findall((SKILL / "SKILL.md").read_text(encoding="utf-8"))
    order = [gate for _, gate in sorted(rows, key=lambda row: int(row[0]))]
    assert order[:2] == ["gate-build", "gate-supply-chain"], order
    assert order[-1] == "gate-repo", order
    declared = set(json.loads((PLUGIN / ".claude-plugin/deploys.json").read_text())["gates"])
    assert set(order) == declared, declared.symmetric_difference(order)


def test_the_plan_can_name_every_control_in_the_register() -> None:
    """No control may be absent from the plan — absent reads as not applicable.

    Every control resolves to one of the skill's four plan rows. A control
    matching none of them would be one this skill silently drops, and a reader
    would take its absence for *not applicable*.

    The third row is the interesting one. SEC-002 is satisfied by a workflow
    **not** referencing a static credential — there is no artefact and so no
    `deployed_by`, and `02-skill-family.md` records that as correct rather than
    as a gap. It is still planned, as *checked, not deployed*, because a control
    satisfied by an absence has to be distinguishable from one nobody has got to.
    """
    register = _register()
    sidecar = json.loads((PLUGIN / ".claude-plugin/deploys.json").read_text())["gates"]
    verified_by = {
        control: gate for gate, entry in sidecar.items() for control in entry["controls"]
    }
    deploy, elsewhere, checked, manual = set(), set(), set(), set()
    for control in register.controls:
        gate = getattr(control, "deployed_by", None)
        if gate in sidecar:
            deploy.add(control.id)
        elif gate:
            elsewhere.add(control.id)
        elif control.id in verified_by:
            checked.add(control.id)
        else:
            manual.add(control.id)
    assert deploy == set(_DEPLOYED) - {"SEC-002"} | {"IAC-001"}, deploy
    assert elsewhere == {"DOC-001"}, elsewhere
    assert checked == {"SEC-002"}, checked
    assert not manual, f"controls in no plan row at all: {sorted(manual)}"
    # And the skill names all four rows, so none of this is a category the
    # implementation invented.
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    for row in ("deploy", "dispatch elsewhere", "checked, not deployed", "manual"):
        assert f"**{row}**" in text, row


def test_before_adopting_the_register_is_mostly_failing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The starting state Step 1 records, so Step 5 has something to compare to."""
    make_repo(tmp_path, _ADOPTER)
    code, out = _verdict(tmp_path, capsys)
    assert code == 1
    # BLD-001 and DEV-001 skip rather than fail: this adopter has no
    # `.devcontainer/` at all, and a predicate is evaluated against files. The
    # plan says *not applicable* for them until `gate-build` copies the
    # template — which is the step that makes them apply.
    for control in ("BLD-001", "DEV-001"):
        assert re.search(rf"^  {control}\s+SKIPPED \(predicate\)", out, re.MULTILINE), control
    for control in set(_DEPLOYED) - {"BLD-001", "DEV-001", "SEC-002", "CI-001"}:
        assert re.search(rf"^  {control}\s+FAIL", out, re.MULTILINE), control


def test_after_adopting_every_local_locus_verifies(
    adopted: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The criterion. Exit 3, and every part of that said rather than rounded up.

    `3` rather than `0` because SEC-001's and CI-001's remote blocks report
    `SKIPPED (no credentials)` until Phase 3. Reporting it as a clean pass would
    claim two loci no code has touched.

    DOC-001 fails on purpose and is not counted: it is `lint-md`'s, in another
    plugin, and this adoption plans it as *dispatch elsewhere*. A test that
    deployed it here would be testing a skill this repository does not ship.
    """
    code, out = _verdict(adopted, capsys)
    # The report pads control ids to a common width, so match on the id plus a
    # run of spaces rather than on a fixed gap.
    def verdict(control: str) -> str:
        found = re.search(rf"^  {re.escape(control)}\s+(\S+(?: \([a-z ]+\))?)", out, re.MULTILINE)
        assert found is not None, f"{control} is absent from the report\n{out}"
        return found.group(1)

    for control in _DEPLOYED:
        assert verdict(control) in ("PASS", "SKIPPED (no credentials)"), (
            f"{control}: {verdict(control)}\n{out}"
        )
    assert verdict("SEC-001") == "SKIPPED (no credentials)"
    assert verdict("CI-001") == "SKIPPED (no credentials)"
    assert verdict("IAC-001") == "SKIPPED (predicate)"
    assert "incomplete" in out
    assert code in (1, 3), out  # 1 only because DOC-001 is another plugin's


def test_four_gates_share_one_pre_commit_config_without_overwriting_each_other(
    adopted: Path,
) -> None:
    """The composition no per-gate test can reach.

    Each gate's own test deploys it alone. Here four write into one file, and
    "grouped by the artefact they write" is either true or discovered not to be.
    """
    hooks = yaml.safe_load((adopted / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    ids = {hook["id"] for block in hooks["repos"] for hook in block["hooks"]}
    assert ids == {
        "standard-check-build",
        "standard-check-supply-chain",
        "gitleaks",
        "ruff",
        "mypy",
    }, ids


def test_every_deployed_control_carries_its_own_stamp(adopted: Path) -> None:
    """Per control, not per gate — inherited from contract 12, across six gates."""
    register = _register()
    stamped: set[str] = set()
    for path in subprocess.run(
        ["git", "-C", str(adopted), "grep", "-l", "ee-control:"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.split():
        text = (adopted / path).read_text(encoding="utf-8")
        for control, skill, version, contract in re.findall(
            r"ee-control: (\S+)\s+ee-skill: (\S+)\s+register: v(\S+)\s+register-contract: (\d+)",
            text,
        ):
            stamped.add(control)
            assert version == register.version, (path, skill)
            assert contract == str(register.register_contract), (path, skill)
    # SEC-002 has no artefact of its own — it is verified from the workflows
    # SEC-001's gate writes — and IAC-001 does not apply here.
    assert stamped == set(_DEPLOYED) - {"SEC-002"}, stamped


def test_the_verify_step_can_genuinely_fail(
    adopted: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The clause the criterion turns on.

    *A verify step that has never been observed failing is not known to work.*
    So a deployed config is broken here — the lint step suppressed with
    `|| true`, which is a gate that reports rather than blocks — and the run is
    checked. It fails two controls at once, because both verify through
    `no-failure-suppression` over the whole workflow.
    """
    workflow = adopted / ".github/workflows/ci.yml"
    workflow.write_text(
        workflow.read_text(encoding="utf-8").replace("ruff check .", "ruff check . || true"),
        encoding="utf-8",
    )
    make_repo(adopted, {})
    code, out = _verdict(adopted, capsys)
    assert code == 1
    assert re.search(r"^  LNT-001\s+FAIL", out, re.MULTILINE)
    assert re.search(r"^  TST-001\s+FAIL", out, re.MULTILINE)
    assert "'|| true' in run" in out


def test_a_gate_that_broke_another_gates_control_is_caught(
    adopted: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Why Step 5 runs the whole register rather than what was just deployed.

    A gate that wired its own control and broke another's CI step is exactly
    what a per-gate verify cannot see. Here the frozen install `gate-supply-chain`
    wrote is removed: SUP-001 fails, and so does nothing else — which is the
    point. Only a whole-register run reports it at all.
    """
    workflow = adopted / ".github/workflows/ci.yml"
    workflow.write_text(
        workflow.read_text(encoding="utf-8").replace("uv sync --frozen", "true"),
        encoding="utf-8",
    )
    make_repo(adopted, {})
    code, out = _verdict(adopted, capsys)
    assert code == 1
    assert re.search(r"^  SUP-001\s+FAIL", out, re.MULTILINE)
    assert re.search(r"^  LNT-001\s+PASS", out, re.MULTILINE)


def test_the_skill_will_not_commit_on_a_failed_verify() -> None:
    """The ordering that makes Step 6 worth having, stated where it is checkable.

    A commit made before the verify step records an adoption that may not have
    happened — and it is the artefact everyone reads afterwards.
    """
    text = " ".join((SKILL / "SKILL.md").read_text(encoding="utf-8").split())
    assert "Only after Step 5, and only if it did not exit `1` or `2`" in text
    assert "Never report `3` as a clean pass" in text
    # And the one confirmation this plan does not cover.
    assert "This confirmation does not cover `gate-repo`" in text
