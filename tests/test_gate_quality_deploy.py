"""`gate-quality` deploys onto a repo with none of its config, and it verifies.

The same criterion `tests/test_gate_secrets_deploy.py` closes for the reference
gate, applied to the first gate that owns more than one control. This repository
cannot be the subject: it has run a linter, a type checker and a test suite
since Phase 0.5, so "none of its config" is a state it has not been in. The
subject is a throwaway repository built here — Python source, a CI workflow that
gates and installs from a lockfile, a devcontainer, and nothing else.

**What this proves, and what it does not.** The artefacts come from the skill's
own shipped templates, rendered with the register's values, one copy of the
content. What is proved is that those artefacts, in a repository that had none,
are accepted by `standard-check` at every locus LNT-001, TYP-001 and TST-001
declare, and that removing any one of them is rejected. What is *not* proved is
that a model follows the prose in `SKILL.md` — no test can establish that, and
claiming otherwise would be the kind of tick this repository has re-opened seven
times.

The second half matters as much as the first. Phase 2 says a verify step that
has never been observed failing is not known to work, so every artefact this
gate writes is broken in turn below and the verdict checked — including the two
ways a gate can be present and not be a gate: a suppressed step, and a coverage
allow-list that leaves tracked files out.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

from conftest import REPO_ROOT, make_repo
from standard_check.cli import main
from standard_check.register import Gate, Register, load_register

SKILL = REPO_ROOT / "plugins/ee-standard/skills/gate-quality"
REGISTER_PATH = REPO_ROOT / "controls.yaml"
SKILL_VERSION = "0.1.0"
STACK = "python"

# The answer Step 1 asks for. The register bounds the set — `test_commands` for
# the ecosystem — and the repository picks the member and the form that reaches
# the artefact its lockfile pins. Asserted against the register below rather
# than trusted, because a spelling outside that set is a step the checker will
# not credit.
TEST_COMMAND = "uv run pytest"

# A repository an adopter might bring: some source, a devcontainer, a CI
# workflow that gates and installs from the lockfile, and no quality gate of any
# kind. `src/quiet.py` is tracked and imported by nothing — the shape that a
# coverage allow-list silently drops.
_ADOPTER = {
    "pyproject.toml": '[project]\nname = "adopter"\nversion = "0.1.0"\n',
    "uv.lock": 'version = 1\nrequires-python = ">=3.13"\n',
    "src/app.py": 'def main() -> None:\n    print("hello")\n',
    "src/quiet.py": "def unused() -> int:\n    return 1\n",
    ".devcontainer/devcontainer.json": '{\n  "name": "adopter",\n  "remoteUser": "vscode"\n}\n',
    ".github/workflows/ci.yml": (
        "name: CI\n\non:\n  push:\n    branches: [main]\n  pull_request:\n\n"
        "jobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - uses: actions/checkout@" + "a" * 40 + " # v7.0.1\n"
        "      - name: Install dependencies (frozen)\n        run: uv sync --frozen\n"
    ),
}

_CONTROLS = ("LNT-001", "TYP-001", "TST-001")


def _register() -> Register:
    register, errors = load_register(REGISTER_PATH)
    assert register is not None, errors
    return register


def _source_pattern(register: Register) -> str:
    """`source_globs` as one regex, which is the derivation Step 2 describes.

    Derived rather than chosen: `source_globs` is the set of tracked files this
    stack's gates are claimed to cover, and a hand-picked pre-commit `types:`
    tag would be a second statement of that set, free to name fewer files.
    """
    globs = register.stacks[STACK].source_globs
    return r"^.*(" + "|".join(re.escape(glob.lstrip("*")) for glob in globs) + r")$"


def _render(template: str, register: Register) -> str:
    """A template with every placeholder filled from the register.

    This is the substitution the skill performs, and the only place the values
    can come from. A placeholder left unfilled is a failure here rather than an
    artefact deployed with `{{LINT_TOOL}}` in it.
    """
    lint: Gate = register.stacks[STACK].gates["lint"]
    typecheck: Gate = register.stacks[STACK].gates["typecheck"]
    text = template
    for placeholder, value in {
        "{{STACK}}": STACK,
        "{{SOURCE_PATTERN}}": _source_pattern(register),
        "{{LINT_TOOL}}": lint.tool,
        "{{LINT_INVOCATION}}": lint.invocation,
        "{{LINT_HOOK_ID}}": lint.pre_commit or "",
        "{{EDITOR_EXTENSION}}": lint.editor_extension or "",
        "{{EDITOR_LANGUAGE}}": lint.editor_binding.language if lint.editor_binding else "",
        "{{EDITOR_BINDING_SETTING}}": (
            lint.editor_binding.setting if lint.editor_binding else ""
        ),
        "{{TYPECHECK_TOOL}}": typecheck.tool,
        "{{TYPECHECK_INVOCATION}}": typecheck.invocation,
        "{{TYPECHECK_HOOK_ID}}": typecheck.pre_commit or "",
        "{{COVERAGE_KEY}}": typecheck.coverage_key or "",
        "{{TEST_COMMAND}}": TEST_COMMAND,
        "{{SKILL_VERSION}}": SKILL_VERSION,
        "{{REGISTER_VERSION}}": register.version,
        "{{REGISTER_CONTRACT}}": str(register.register_contract),
    }.items():
        text = text.replace(placeholder, value)
    assert "{{" not in text, f"a placeholder was not filled: {text}"
    return text


def _body(template: str, marker: str | None = None, comment: str = "//") -> str:
    """The template's payload, without the comment block explaining it.

    Dropped before substitution, not after: the comments talk *about* the
    placeholders, so rendering them first would leave a `{{` behind and the
    unfilled-placeholder check would fire on prose. `marker` selects one of the
    two shapes in a template that ships more than one — the editor locus has a
    devcontainer shape and a `.vscode/` shape, and a gate writes one, never
    both.
    """
    if marker is not None:
        after = template.split(marker, 1)[1]
        template = after.split("\n" + comment + " ---", 1)[0].split("\n", 1)[1]
    lines = template.splitlines(keepends=True)
    start = next(i for i, line in enumerate(lines) if not line.startswith(comment))
    return "".join(lines[start:])


def _deploy(root: Path, register: Register) -> None:
    """Write every artefact, as Steps 2 to 5 of the skill describe.

    The *content* of the three loci is the shipped templates' and nothing else —
    that is the property worth holding. Step 2's configuration has no template
    because it is an edit to a file the repository already owns; the values it
    writes still come from the register.
    """
    typecheck = register.stacks[STACK].gates["typecheck"]
    lint = register.stacks[STACK].gates["lint"]

    # Step 2, first half — the pin. `invocation` reaches the artefact the
    # lockfile pins and reaches `PATH` instead when the tool is not in the
    # project at all (ADR 0020, case C), so from contract 13 the pin is part of
    # the control. The command is the register's, keyed by the lockfile that is
    # present; what it does to the lockfile is simulated here, because running a
    # real `uv add` would resolve from the network inside a unit test.
    ecosystem = register.ecosystems[register.stacks[STACK].ecosystem]
    lockfile = next(lock for lock in ecosystem.lockfiles if (root / lock).exists())
    assert ecosystem.add_dev_dependency[lockfile] == "uv add --dev {package}"
    lock = root / lockfile
    for gate in (lint, typecheck):
        package = gate.package or gate.tool
        lock.write_text(
            lock.read_text(encoding="utf-8")
            + f'\n[[package]]\nname = "{package}"\nversion = "0.0.0"\n',
            encoding="utf-8",
        )

    # Step 2, second half — an empty section is a real configuration: the tool's defaults,
    # stated where a reviewer can find them and a later commit can tighten.
    pyproject = root / "pyproject.toml"
    pyproject.write_text(
        pyproject.read_text(encoding="utf-8")
        + f"\n[tool.{lint.tool}]\n\n[tool.{typecheck.tool}]\n{typecheck.strict_key} = true\n",
        encoding="utf-8",
    )

    # Step 3 — the editor locus, merged into the devcontainer this repository
    # already has. Merged as text rather than reparsed and dumped: the stamp is
    # a `//` comment, and a round trip through `json` would drop it. The
    # checker reads this file with a JSONC reader, so the comment stays legal.
    devcontainer = root / ".devcontainer/devcontainer.json"
    fragment = _render(
        _body(
            (SKILL / "templates/editor-extensions.json").read_text(encoding="utf-8"),
            marker="// --- .devcontainer/devcontainer.json",
        ),
        register,
    )
    inner = fragment.strip().removeprefix("{").removesuffix("}").strip("\n")
    existing = devcontainer.read_text(encoding="utf-8").rstrip().removesuffix("}").rstrip()
    devcontainer.write_text(existing + ",\n" + inner + "\n}\n", encoding="utf-8")

    # Step 3b — the binding, at workspace scope and nowhere else. Installing the
    # extension above is a different claim from it being the tool that runs, and
    # the gap between them is what ADR 0029 point 4 closes. Written from the
    # template so the artefact under test is the one the skill ships, and only
    # where the register declares a binding for this gate.
    if lint.editor_binding is not None:
        settings = _render(
            _body(
                (SKILL / "templates/editor-settings.json").read_text(encoding="utf-8"),
                marker="// --- .vscode/settings.json",
            ),
            register,
        )
        (root / ".vscode").mkdir(exist_ok=True)
        (root / ".vscode/settings.json").write_text(settings, encoding="utf-8")

    # Step 4 — the pre-commit locus.
    hooks = _render(
        _body((SKILL / "templates/precommit-hooks.yaml").read_text(encoding="utf-8")), register
    )
    (root / ".pre-commit-config.yaml").write_text(
        "repos:\n  - repo: local\n    hooks:\n" + hooks, encoding="utf-8"
    )

    # Step 5 — the ci locus, appended to the job that already installs frozen.
    steps = _render(
        _body((SKILL / "templates/ci-steps.yaml").read_text(encoding="utf-8")), register
    )
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


def test_the_test_command_is_one_the_register_accepts(capsys: pytest.CaptureFixture[str]) -> None:
    """Step 1's constraint, checked rather than assumed.

    The gate asks which spelling a repository uses and writes the answer. An
    answer outside the register's set is a step the checker will not credit, and
    a bare runner is a locus that resolves from `PATH` (ADR 0020) — so both
    halves are held here, where the answer this test uses is decided.
    """
    accepted = _register().ecosystems["python"].test_commands
    assert any(
        re.match(rf"^(?:\S+\s+run\s+)?{re.escape(command)}(?![-\w])", TEST_COMMAND)
        for command in accepted
    ), f"{TEST_COMMAND!r} is not one of {accepted}"
    assert TEST_COMMAND not in accepted, (
        "the bare spelling resolves from PATH — the deployed command must reach "
        "the artefact the lockfile pins"
    )


def test_before_deploying_all_three_controls_fail(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The starting state, stated rather than assumed."""
    make_repo(tmp_path, _ADOPTER)
    code, out = _verdict(tmp_path, capsys)
    assert code == 1
    assert "editor locus" in out and "pre-commit locus" in out and "ci locus" in out
    assert "no CI step runs the test command" in out
    assert "no tracked file carries a provenance stamp" in out
    # The adopter's lockfile pins neither tool, so the invocations the gate is
    # about to write would resolve from PATH. Part of the starting state from
    # contract 13, and part of what the deployment has to change.
    assert "ruff is not pinned in uv.lock" in out
    assert "mypy is not pinned in uv.lock" in out


def test_after_deploying_every_locus_verifies(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The criterion. Exit 0, and the difference from `gate-secrets` is the point.

    All three controls verify from files and none declares a `remote` locus, so
    there is nothing Phase 3 is holding back and nothing to round up. A `3` here
    would mean a block declared itself partial.
    """
    code, out = _verdict(deployed, capsys)
    assert code == 0, out
    for control in _CONTROLS:
        assert f"{control}  PASS" in out
    # A clean control prints no block detail — the report expands only what did
    # not simply pass. So the evidence that each block ran is the exit code and
    # the summary, and the evidence that each block *can* fail is every test
    # below this one.
    assert "3 passed, 0 failed" in out
    assert "SKIPPED" not in out and "incomplete" not in out


def test_the_deployed_stamps_record_the_register_they_came_from(deployed: Path) -> None:
    """One stamp per control per locus, each naming the control whose locus it is."""
    register = _register()
    stamped = {
        ".pre-commit-config.yaml": {"LNT-001", "TYP-001"},
        ".github/workflows/ci.yml": {"LNT-001", "TYP-001", "TST-001"},
        ".devcontainer/devcontainer.json": {"LNT-001"},
    }
    for path, controls in stamped.items():
        text = (deployed / path).read_text(encoding="utf-8")
        found = re.findall(
            r"ee-control: (\S+)\s+ee-skill: (\S+)\s+register: v(\S+)\s+register-contract: (\d+)",
            text,
        )
        assert {control for control, _, _, _ in found} == controls, path
        for _, skill, version, contract in found:
            assert skill == f"gate-quality@{SKILL_VERSION}"
            assert version == register.version
            assert contract == str(register.register_contract)


def test_the_deployed_workflow_is_valid_yaml_that_still_gates(deployed: Path) -> None:
    """Appending steps must not break the file it appends to."""
    doc = yaml.safe_load((deployed / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    triggers = doc["on"] if "on" in doc else doc[True]
    assert set(triggers) == {"push", "pull_request"}
    steps = doc["jobs"]["build"]["steps"]
    names = [step.get("name") for step in steps]
    assert "Tests" in names
    # The three steps run the tools the frozen install placed. Before it, they
    # would run against nothing.
    assert names.index("Install dependencies (frozen)") < min(
        names.index(name) for name in names if name and name.startswith(("Lint", "Type check"))
    )


def test_the_deployed_hooks_cover_the_files_the_register_names(deployed: Path) -> None:
    """The hooks' filter is the register's `source_globs`, not a chosen tag."""
    register = _register()
    config = yaml.safe_load((deployed / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    hooks = config["repos"][0]["hooks"]
    assert len(hooks) == 2
    for hook in hooks:
        assert hook["files"] == _source_pattern(register)
        assert re.match(hook["files"], "src/app.py")
        assert not re.match(hook["files"], "README.md")


def _also_bind_in_devcontainer(root: Path) -> None:
    """Repeat the workspace binding inside `devcontainer.json`, verbatim."""
    path = root / ".devcontainer/devcontainer.json"
    document = json.loads(re.sub(r"^\s*//.*$", "", path.read_text(encoding="utf-8"), flags=re.M))
    vscode = document.setdefault("customizations", {}).setdefault("vscode", {})
    vscode.setdefault("settings", {})["[python]"] = {
        "editor.defaultFormatter": "charliermarsh.ruff"
    }
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


@pytest.mark.parametrize(
    "control,locus,break_it",
    [
        (
            "LNT-001",
            "editor locus",
            lambda root: (root / ".devcontainer/devcontainer.json").write_text(
                '{"name": "adopter", "remoteUser": "vscode"}\n', encoding="utf-8"
            ),
        ),
        (
            "LNT-001",
            "pre-commit locus",
            lambda root: (root / ".pre-commit-config.yaml").unlink(),
        ),
        # The state that passed for as long as it existed: the pinned extension
        # installed, and another one holding the file type. Presence never
        # excluded, which is why the assert stopped asking about presence alone.
        (
            "LNT-001",
            "are bound to ms-python.autopep8",
            lambda root: (root / ".vscode/settings.json").write_text(
                '{"[python]": {"editor.defaultFormatter": "ms-python.autopep8"}}\n',
                encoding="utf-8",
            ),
        ),
        # And the state it actually occurred in: nothing tracked says anything,
        # so whatever a feature contributes decides. An assert that only
        # objected to a wrong value would pass this.
        (
            "LNT-001",
            "does not set",
            lambda root: (root / ".vscode/settings.json").unlink(),
        ),
        # The binding restated where the merge rule is undefined. Wrong even
        # though it agrees — agreement here is luck, not a rule (ADR 0029).
        (
            "LNT-001",
            "belongs at workspace scope alone",
            lambda root: _also_bind_in_devcontainer(root),
        ),
        (
            "TST-001",
            "no CI step runs the test command",
            lambda root: _rewrite_workflow(root, lambda text: text.replace(TEST_COMMAND, "echo")),
        ),
    ],
)
def test_removing_an_artefact_is_caught(
    deployed: Path,
    capsys: pytest.CaptureFixture[str],
    control: str,
    locus: str,
    break_it: object,
) -> None:
    """A verify step never observed failing is not known to work."""
    break_it(deployed)  # type: ignore[operator]
    make_repo(deployed, {})
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert f"{control}  FAIL" in out
    assert locus in out


def test_removing_the_pin_is_caught(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """ADR 0020 case C, on a fully deployed repository.

    Every artefact is in place and every locus still reads `uv run ruff check`.
    What changed is that ruff is no longer in the project, so that invocation
    resolves from `PATH` — the condition ADR 0020 measured passing, and the one
    the invocation itself cannot close.
    """
    lock = deployed / "uv.lock"
    lock.write_text(
        lock.read_text(encoding="utf-8").replace('name = "ruff"', 'name = "not-ruff"'),
        encoding="utf-8",
    )
    make_repo(deployed, {})
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "LNT-001  FAIL" in out
    assert "ruff is not pinned in uv.lock" in out
    assert "resolves from PATH" in out
    # The wiring is untouched, and says so — the two halves are separable and
    # this test is the evidence that the second one is doing work.
    assert "ruff wired at every declared locus" in out


def _rewrite_workflow(root: Path, edit: object) -> None:
    workflow = root / ".github/workflows/ci.yml"
    workflow.write_text(edit(workflow.read_text(encoding="utf-8")), encoding="utf-8")  # type: ignore[operator]


def test_a_suppressed_step_is_not_a_gate(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The artefact is present, and the control fails anyway.

    `|| true` on the lint step fails LNT-001 and TST-001 at once, because both
    verify through `no-failure-suppression` over the whole workflow. A gate that
    reports rather than blocks is the shape this register calls theme T-3.
    """
    _rewrite_workflow(deployed, lambda text: text.replace("check .", "check . || true"))
    make_repo(deployed, {})
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "LNT-001  FAIL" in out and "TST-001  FAIL" in out
    assert "'|| true' in run" in out


def test_a_coverage_allow_list_that_leaves_a_tracked_file_out_is_caught(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Every artefact is in place, strictness is on, and TYP-001 still fails.

    `files = ["src/app.py"]` excludes `src/quiet.py` by not naming it — an
    exclusion that is an *absence*, with no line to read and no diff when
    coverage shrinks. mypy would still check a file something imported; nothing
    imports this one, so the control's claim of all first-party source is false
    (ADR 0019 applied to an allow-list, § H).
    """
    typecheck = _register().stacks[STACK].gates["typecheck"]
    key = (typecheck.coverage_key or "").rsplit(".", 1)[-1]
    pyproject = deployed / "pyproject.toml"
    pyproject.write_text(
        pyproject.read_text(encoding="utf-8") + f'{key} = ["src/app.py"]\n', encoding="utf-8"
    )
    make_repo(deployed, {})
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "TYP-001  FAIL" in out
    assert "src/quiet.py" in out


def test_stamping_one_locus_and_forgetting_the_others_is_caught(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The gate wrote every artefact and recorded only one of them.

    This is the shape a gate owning three controls makes possible and a gate
    owning one does not: every file is in place, the deployment worked, and the
    only stamp names TST-001. Matching stamps by skill credited LNT-001 and
    TYP-001 for it. Matching by control does not.
    """
    for path in (
        ".pre-commit-config.yaml",
        ".devcontainer/devcontainer.json",
        ".vscode/settings.json",
    ):
        target = deployed / path
        target.write_text(
            re.sub(r"^.*ee-control:.*\n", "", target.read_text(encoding="utf-8"), flags=re.M),
            encoding="utf-8",
        )
    workflow = deployed / ".github/workflows/ci.yml"
    workflow.write_text(
        re.sub(
            r"^.*ee-control: (?:LNT|TYP)-001.*\n",
            "",
            workflow.read_text(encoding="utf-8"),
            flags=re.M,
        ),
        encoding="utf-8",
    )
    make_repo(deployed, {})
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "LNT-001  FAIL" in out and "TYP-001  FAIL" in out
    assert "no stamp names LNT-001" in out
    # TST-001 keeps its own stamp and passes, which is what makes the failure
    # above about the record rather than about the file.
    assert "TST-001  PASS" in out


def test_removing_the_stamps_is_caught(
    deployed: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The artefacts stay; only the record of who wrote them goes.

    A stamp nothing reads back records a claim rather than establishing one, and
    reading it back is what makes the deployment auditable at all (§ F).
    """
    for path in (
        ".pre-commit-config.yaml",
        ".github/workflows/ci.yml",
        ".devcontainer/devcontainer.json",
        ".vscode/settings.json",
    ):
        target = deployed / path
        target.write_text(
            re.sub(r"^.*ee-control:.*\n", "", target.read_text(encoding="utf-8"), flags=re.M),
            encoding="utf-8",
        )
    make_repo(deployed, {})
    code, out = _verdict(deployed, capsys)
    assert code == 1
    assert "no tracked file carries a provenance stamp naming 'gate-quality'" in out
