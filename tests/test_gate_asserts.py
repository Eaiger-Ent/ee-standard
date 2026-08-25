"""The two asserts `gate-secrets` is verified by, and the register rule tying them.

`secrets_gate_wired_at_all_loci` exists because SEC-001 declared three loci and
had one read. Deleting the pre-commit hook was caught; deleting the CI job was
not, and a control checked at one of the loci it names is § A's defect — the
same shape § H found in GOV-001, which passed a workflow that ran on neither
push nor pull_request.

`provenance_stamp_present` exists because a stamp nothing reads back records a
claim rather than establishing one. Three of the four `lint-md` artefacts
carried no stamp while `CLAUDE.md` stated as fact that they did (§ F), and a
person found that, not a check.

Each test below deletes exactly one thing from a conformant fixture. A check
that has never been observed failing is not known to work.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from conftest import REPO_ROOT, a_register, make_repo, register_with, write_register
from register_check.asserts_command import secrets_gate_wired_at_all_loci
from register_check.asserts_file import provenance_stamp_present
from register_check.register import load_register

_HOOK = """repos:
  - repo: local
    hooks:
      - id: gitleaks
        name: gitleaks (SEC-001)
        entry: gitleaks protect --staged --no-banner --redact
        language: system
        pass_filenames: false
"""

_CI = """on: [push, pull_request]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - run: gitleaks detect --no-banner --redact
"""

_WIRED = {".pre-commit-config.yaml": _HOOK, ".github/workflows/register-check.yml": _CI}

_ARGS: dict[str, object] = {"tool": "gitleaks", "ignore_file": ".gitleaksignore"}


def test_both_local_loci_wired_passes(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, _WIRED)
    result = secrets_gate_wired_at_all_loci(repo, a_register(), _ARGS)
    assert result.passed, result.message
    assert "pre-commit and ci" in result.message


def test_deleting_the_ci_job_fails_the_control(tmp_path: Path) -> None:
    """The locus nothing used to read.

    Before contract 11 this fixture passed SEC-001: the hook is present, the
    remote block defers to Phase 3, and no assert looked at CI at all.
    """
    repo = make_repo(tmp_path, {".pre-commit-config.yaml": _HOOK})
    result = secrets_gate_wired_at_all_loci(repo, a_register(), _ARGS)
    assert not result.passed
    assert "ci locus" in result.message
    assert "pre-commit locus" not in result.message


def test_deleting_the_pre_commit_hook_fails_the_control(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, {".github/workflows/register-check.yml": _CI})
    result = secrets_gate_wired_at_all_loci(repo, a_register(), _ARGS)
    assert not result.passed
    assert "pre-commit locus" in result.message


def test_a_workflow_that_gates_nothing_is_not_the_ci_locus(tmp_path: Path) -> None:
    """`on: workflow_dispatch` runs when a human clicks it — theme T-3.

    Reusing `_ci_run_mentions` is what makes this hold without restating it:
    the gating rule lives in one place and every gate inherits it.
    """
    repo = make_repo(
        tmp_path,
        {
            ".pre-commit-config.yaml": _HOOK,
            ".github/workflows/register-check.yml": _CI.replace(
                "on: [push, pull_request]", "on: [workflow_dispatch]"
            ),
        },
    )
    result = secrets_gate_wired_at_all_loci(repo, a_register(), _ARGS)
    assert not result.passed
    assert "ci locus" in result.message


def test_a_ci_step_running_the_whole_hook_suite_reaches_the_gate(tmp_path: Path) -> None:
    """`pre-commit run --all-files` runs every hook, gitleaks among them."""
    repo = make_repo(
        tmp_path,
        {
            ".pre-commit-config.yaml": _HOOK,
            ".github/workflows/register-check.yml": _CI.replace(
                "gitleaks detect --no-banner --redact", "pre-commit run --all-files"
            ),
        },
    )
    assert secrets_gate_wired_at_all_loci(repo, a_register(), _ARGS).passed


def test_an_ignore_entry_naming_a_tracked_file_is_a_weakening(tmp_path: Path) -> None:
    """ADR 0019, at the one exemption list this gate has.

    SEC-001 is `variance: forbidden` with `baseline: null`. Suppressing a
    finding in a file git tracks hides authored content from a control that
    admits no tolerated violations.
    """
    repo = make_repo(
        tmp_path,
        {
            **_WIRED,
            "app/config.py": "TOKEN = 'x'\n",
            ".gitleaksignore": "# a false positive\nabc123:app/config.py:generic-api-key:1\n",
        },
    )
    result = secrets_gate_wired_at_all_loci(repo, a_register(), _ARGS)
    assert not result.passed
    assert "app/config.py" in result.message
    assert "ADR 0019" in result.message


def test_an_ignore_entry_naming_nothing_tracked_scopes_the_tool(tmp_path: Path) -> None:
    """The other half of ADR 0019, which a blanket "no exemptions" rule breaks.

    A fingerprint for a vendored path git does not track suppresses a finding
    about content this repository does not author.
    """
    repo = make_repo(
        tmp_path,
        {
            **_WIRED,
            ".gitleaksignore": "abc123:node_modules/pkg/fixture.js:generic-api-key:12\n",
        },
    )
    assert secrets_gate_wired_at_all_loci(repo, a_register(), _ARGS).passed


def test_the_tool_name_comes_from_the_register_not_the_checker(tmp_path: Path) -> None:
    """ADR 0018's test, applied: the scanner is a register fact.

    A repository standardising on a different scanner changes `args.tool` and
    nothing else. An assert still holding "gitleaks" privately passes the happy
    path and fails here.
    """
    repo = make_repo(
        tmp_path,
        {
            ".pre-commit-config.yaml": _HOOK.replace("gitleaks", "trufflehog"),
            ".github/workflows/register-check.yml": _CI.replace("gitleaks", "trufflehog"),
        },
    )
    assert secrets_gate_wired_at_all_loci(repo, a_register(), {"tool": "trufflehog"}).passed
    assert not secrets_gate_wired_at_all_loci(repo, a_register(), _ARGS).passed


def test_an_absent_tool_argument_fails_rather_than_passing_vacuously(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, _WIRED)
    result = secrets_gate_wired_at_all_loci(repo, a_register(), {})
    assert not result.passed
    assert "'tool' argument" in result.message


def test_a_lockfile_tool_is_looked_for_by_its_pinned_invocation(tmp_path: Path) -> None:
    """ADR 0020: the locus must reach the pinned artefact, not a name.

    `markdownlint-cli2` is the register's one tool with an `invocation`, so it
    is the available fixture for the branch — a hook naming the bare tool does
    not satisfy a control whose register entry says how the pin is reached.
    """
    repo = make_repo(
        tmp_path,
        {
            ".pre-commit-config.yaml": _HOOK.replace("gitleaks", "markdownlint-cli2"),
            ".github/workflows/register-check.yml": _CI.replace(
                "gitleaks detect --no-banner --redact", "markdownlint-cli2 ."
            ),
        },
    )
    result = secrets_gate_wired_at_all_loci(repo, a_register(), {"tool": "markdownlint-cli2"})
    assert not result.passed
    assert "node_modules/.bin/markdownlint-cli2" in result.message


_STAMP = (
    "# ee-control: SEC-001  ee-skill: gate-secrets@0.1.0  "
    "register: v0.11.0  register-contract: 11\n"
)

# The control whose verify block is running. The runner supplies it — the block
# sits inside the control that answers it — so an assert evaluated here has to
# be handed the same thing, or it is being asked a question the register never
# asks. `_STAMP` above names SEC-001, which is what makes these two agree.
_SEC = {"skill": "gate-secrets", "control": "SEC-001"}


def test_a_stamp_the_gate_wrote_is_read_back(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, {".pre-commit-config.yaml": _STAMP + _HOOK})
    result = provenance_stamp_present(repo, a_register(), _SEC)
    assert result.passed, result.message
    assert ".pre-commit-config.yaml" in result.message


def test_no_stamp_at_all_fails(tmp_path: Path) -> None:
    """The § F state: artefacts deployed, and no record that they were."""
    repo = make_repo(tmp_path, _WIRED)
    result = provenance_stamp_present(repo, a_register(), _SEC)
    assert not result.passed
    assert "gate-secrets" in result.message


def test_another_gates_stamp_does_not_answer_for_this_one(tmp_path: Path) -> None:
    repo = make_repo(
        tmp_path, {".pre-commit-config.yaml": _STAMP.replace("gate-secrets", "lint-md") + _HOOK}
    )
    assert not provenance_stamp_present(repo, a_register(), _SEC).passed


def test_a_stamp_naming_an_unknown_control_is_a_defect(tmp_path: Path) -> None:
    repo = make_repo(
        tmp_path, {".pre-commit-config.yaml": _STAMP.replace("SEC-001", "SEC-999") + _HOOK}
    )
    result = provenance_stamp_present(repo, a_register(), _SEC)
    assert not result.passed
    assert "SEC-999" in result.message


def test_a_stamp_ahead_of_the_register_is_a_defect(tmp_path: Path) -> None:
    """Behind is staleness and reported; ahead cannot be explained at all."""
    register = a_register()
    ahead = register.register_contract + 1
    repo = make_repo(
        tmp_path,
        {
            ".pre-commit-config.yaml": _STAMP.replace(
                "register-contract: 11", f"register-contract: {ahead}"
            )
            + _HOOK
        },
    )
    result = provenance_stamp_present(repo, register, _SEC)
    assert not result.passed
    assert str(ahead) in result.message


def test_a_stamp_behind_the_register_is_staleness_and_passes(tmp_path: Path) -> None:
    """"Notify, never redeploy" — failing a build on a stale stamp enforces one."""
    repo = make_repo(
        tmp_path,
        {
            ".pre-commit-config.yaml": _STAMP.replace(
                "register-contract: 11", "register-contract: 1"
            )
            + _HOOK
        },
    )
    assert provenance_stamp_present(repo, a_register(), _SEC).passed


def test_an_untracked_artefact_carries_no_evidence(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, _WIRED)
    (tmp_path / "scratch.yaml").write_text(_STAMP, encoding="utf-8")
    assert not provenance_stamp_present(repo, a_register(), _SEC).passed


def test_the_schema_rejects_a_stamp_that_reads_back_a_different_gate(tmp_path: Path) -> None:
    """The two fields naming a deploying gate cannot drift apart."""

    def mutate(document: dict[str, Any]) -> None:
        for control in document["controls"]:
            if control["id"] == "SEC-001":
                for block in control["verify"]:
                    if block.get("assert") == "provenance_stamp_present":
                        block["args"]["skill"] = "gate-quality"

    with pytest.raises(AssertionError):
        register_with(tmp_path, mutate)


def test_the_schema_rejects_a_stamp_block_with_no_deployed_by(tmp_path: Path) -> None:
    document = yaml.safe_load((REPO_ROOT / "controls.yaml").read_text(encoding="utf-8"))
    for control in document["controls"]:
        if control["id"] == "SEC-001":
            del control["deployed_by"]
    root = tmp_path / "register"
    write_register(root, document)
    for control in document["controls"]:
        adr = root / control["rationale_adr"]
        adr.parent.mkdir(parents=True, exist_ok=True)
        adr.write_text("# ADR\n", encoding="utf-8")

    register, errors = load_register(root / "controls.yaml")
    assert register is None
    assert any("deployed_by" in str(error) for error in errors), errors


def test_a_stamp_for_a_sibling_control_does_not_satisfy_this_one(tmp_path: Path) -> None:
    """The hole per-gate matching left, closed.

    `gate-quality` deploys three controls. Matching on the skill alone credited
    any of them for any stamp the gate had written anywhere, so a gate that
    stamped its CI steps and forgot the editor locus passed all three. Here the
    only stamp names TST-001, and LNT-001 — which the gate also deploys — has
    nothing of its own to read back.
    """
    stamp = _STAMP.replace("SEC-001", "TST-001").replace("gate-secrets", "gate-quality")
    repo = make_repo(tmp_path, {".pre-commit-config.yaml": stamp + _HOOK})
    args = {"skill": "gate-quality", "control": "LNT-001"}
    result = provenance_stamp_present(repo, a_register(), args)
    assert not result.passed
    assert "no stamp names LNT-001" in result.message
    # And the sibling it *did* stamp still passes, so this is about which
    # control was recorded rather than about the file being unreadable.
    assert provenance_stamp_present(
        repo, a_register(), {"skill": "gate-quality", "control": "TST-001"}
    ).passed


def test_the_assert_says_so_when_run_outside_a_control(tmp_path: Path) -> None:
    """`register-check assert <name>` evaluates an assert with no control.

    A verdict invented for a question nobody asked is worse than the refusal:
    this assert's whole subject is *which* control's deployment was recorded.
    """
    repo = make_repo(tmp_path, {".pre-commit-config.yaml": _STAMP + _HOOK})
    result = provenance_stamp_present(repo, a_register(), {"skill": "gate-secrets"})
    assert not result.passed
    assert "run --control" in result.message


def test_the_schema_rejects_a_register_that_supplies_the_control_itself(
    tmp_path: Path,
) -> None:
    """A control's own id, written into its own entry, is a second copy of it.

    Free to name a different control from the one it sits under — which would
    make a stamp read-back report on somebody else's deployment. The checker
    supplies it instead, from the block's own position.
    """

    def mutate(document: dict[str, Any]) -> None:
        for control in document["controls"]:
            if control["id"] == "SEC-001":
                for block in control["verify"]:
                    if block.get("assert") == "provenance_stamp_present":
                        block["args"]["control"] = "SEC-001"

    with pytest.raises(AssertionError):
        register_with(tmp_path, mutate)


def test_a_stamp_is_found_without_reading_the_whole_tree(tmp_path: Path) -> None:
    """The lookup is `git grep`, and it agrees with reading every file.

    Reading the whole tracked tree on every run is correct and does not scale.
    What this holds is that the faster path returns the same answer: a stamp in
    one file among many is found, and files without the marker are not consulted.
    """
    files = {f"pkg/mod{i}.py": f"VALUE = {i}\n" for i in range(50)}
    files[".pre-commit-config.yaml"] = _STAMP + _HOOK
    repo = make_repo(tmp_path, files)
    result = provenance_stamp_present(repo, a_register(), _SEC)
    assert result.passed, result.message
    assert ".pre-commit-config.yaml" in result.message
    assert "pkg/mod0.py" not in result.message
