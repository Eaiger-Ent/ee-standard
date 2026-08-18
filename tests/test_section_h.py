"""One test per § H finding: the input that used to pass, and now does not.

`docs/09-phase-1.5-review.md` § H records four exit criteria that were ticked
and later found false. Each was the same shape — a rule about *this* repository's
own filenames or stacks, held in the checker and applied to every repository —
so each is guarded here the way § D's rows are guarded in `test_section_d.py`:
with an input that the code passed before the fix and fails after it.

§ H1's regression test lives beside the other GOV-001 tests in `test_meta.py`
(`test_gov_001_rejects_a_workflow_that_gates_no_merge`), because that is where a
reader looking at GOV-001 will find it. Its second half — the frozen-install
evidence — is here, because it belongs to SUP-001.

Every case that concerns the register/checker boundary edits **only**
`controls.yaml`, which is what distinguishes a rule that moved from a rule that
was copied: an assert still holding the value privately passes the happy path
and fails here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from conftest import REPO_ROOT, a_register, make_repo, register_with
from standard_check.asserts_command import (
    ci_installs_frozen,
    markdown_gate_wired_at_all_loci,
    no_static_cloud_keys,
)
from standard_check.asserts_file import lockfile_present_and_tracked, tool_versions_match_register
from standard_check.repo import Repo

_GATING = "on: [push, pull_request]\njobs:\n  job:\n    runs-on: ubuntu-latest\n    steps:\n"
_DISPATCH = "on:\n  workflow_dispatch:\njobs:\n  job:\n    runs-on: ubuntu-latest\n    steps:\n"


def _only_gitleaks(sites: list[str]) -> Any:
    """A register whose whole `tools:` table is gitleaks, pinned at `sites`.

    Narrowed so these cases speak about the loci and nothing else — with this
    repository's other two tools left in, every verdict would also carry their
    absence from a fixture repo that was never meant to have them.
    """

    def mutate(document: dict[str, Any]) -> None:
        tool = dict(document["tools"]["gitleaks"])
        tool["pinned_at"] = sites
        document["tools"] = {"gitleaks": tool}

    return mutate


# --- H2 — the loci a tool is pinned at are a register fact -------------------


def _pinning_repo(root: Path, version: str = "8.30.1", path: str = "ci/install.sh") -> Repo:
    return make_repo(root, {path: f"GITLEAKS_VERSION={version}\n"})


def test_h2_a_declared_site_that_does_not_exist_is_a_failure(tmp_path: Path) -> None:
    """The rename that used to pass.

    Moving `.github/workflows/standard-check.yml` to another name, and drifting
    both of its pins, left SUP-001 reporting PASS: the file was no longer one of
    the four the checker knew, so nothing compared it, and the § G fix — fail
    when a literal tool is pinned at *no* locus — could not see it, because the
    tool was still pinned at the sites that kept their names.
    """
    register = register_with(
        tmp_path, _only_gitleaks(["ci/install.sh", "ci/renamed.sh"])
    )
    repo = _pinning_repo(tmp_path / "repo")
    result = tool_versions_match_register(repo, register, {})
    assert not result.passed
    assert "ci/renamed.sh" in result.message
    assert "does not exist" in result.message


def test_h2_a_declared_site_holding_no_pin_is_a_failure(tmp_path: Path) -> None:
    """The same silence one level down: the file is there and the version is not."""
    register = register_with(tmp_path, _only_gitleaks(["ci/install.sh"]))
    repo = make_repo(tmp_path / "repo", {"ci/install.sh": "# installs gitleaks, somehow\n"})
    result = tool_versions_match_register(repo, register, {})
    assert not result.passed
    assert "no gitleaks version pin found" in result.message


def test_h2_drift_at_a_declared_site_is_a_failure(tmp_path: Path) -> None:
    register = register_with(tmp_path, _only_gitleaks(["ci/install.sh"]))
    repo = _pinning_repo(tmp_path / "repo", version="9.9.9")
    result = tool_versions_match_register(repo, register, {})
    assert not result.passed
    assert "9.9.9" in result.message


def test_h2_the_loci_come_from_the_register_not_the_checker(tmp_path: Path) -> None:
    """Only the register moves. A repository may pin wherever it pins.

    The list was four of this repository's own filenames, so an adopting
    repository that pinned the same tools in files of its own naming was told
    they were "pinned at no known locus" — this repo's paths quoted at it as
    though they were the standard.
    """
    register = register_with(
        tmp_path, _only_gitleaks(["tools/versions.env"])
    )
    repo = make_repo(tmp_path / "repo", {"tools/versions.env": "GITLEAKS_VERSION=8.30.1\n"})
    result = tool_versions_match_register(repo, register, {})
    assert result.passed, result.message


# --- H3 — the ecosystem map, and SUP-001's reach ----------------------------


def test_h3_a_go_repo_with_no_lockfile_is_verified_not_skipped() -> None:
    """SUP-001 applies wherever a package manager is, not to two named stacks.

    `applies_to: [python, typescript]` re-created in the register the exemption
    ADR 0018 moved out of the checker: a Go repository reported
    `SKIPPED (predicate)` and the run exited 0.
    """
    register = a_register()
    sup_001 = register.control("SUP-001")
    assert sup_001 is not None
    assert getattr(sup_001, "applies_to", ()) == ("always",)
    assert set(register.ecosystems) >= {"go", "rust", "java", "ruby"}


def test_h3_a_go_repo_with_no_go_sum_fails(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, {"go.mod": "module example.com/x\ngo 1.22\n"})
    result = lockfile_present_and_tracked(repo, a_register(), {})
    assert not result.passed
    assert "go.sum" in result.message


def test_h3_frozen_install_is_checked_for_every_ecosystem_present(tmp_path: Path) -> None:
    """The input that was told "every CI install is frozen or exact-pinned".

    `ci-installs-frozen` held a two-entry map — python and node — so a
    repository in any other ecosystem passed it with nothing checked.
    """
    repo = make_repo(
        tmp_path,
        {
            "Gemfile": "source 'https://rubygems.org'\n",
            "Gemfile.lock": "GEM\n",
            ".github/workflows/ci.yml": _GATING + "      - run: bundle install\n",
        },
    )
    result = ci_installs_frozen(repo, a_register(), {})
    assert not result.passed
    assert "ruby" in result.message


def test_h3_the_frozen_idiom_comes_from_the_register(tmp_path: Path) -> None:
    """Only the register moves: teach it an idiom and the verdict changes."""
    repo = make_repo(
        tmp_path,
        {
            "Gemfile": "source 'https://rubygems.org'\n",
            "Gemfile.lock": "GEM\n",
            ".github/workflows/ci.yml": _GATING + "      - run: bundle install --deployment\n",
        },
    )
    assert ci_installs_frozen(repo, a_register(), {}).passed

    def forget_the_idiom(document: dict[str, Any]) -> None:
        document["ecosystems"]["ruby"]["frozen_install"] = [r"\bnothing-like-this\b"]

    result = ci_installs_frozen(repo, register_with(tmp_path, forget_the_idiom), {})
    assert not result.passed


def test_h1_frozen_evidence_must_come_from_a_step_that_gates(tmp_path: Path) -> None:
    """§ H1's second half. A step a human clicks is not a merge gate.

    SUP-001 passed on a `uv sync --frozen` in a `workflow_dispatch`-only
    workflow, in the same run where GOV-001 said every control was reachable and
    TST-001 said the same file gated nothing.
    """
    files = {
        "pyproject.toml": "[project]\nname = 'x'\nversion = '0.1.0'\n",
        "uv.lock": "version = 1\n",
    }
    gating = make_repo(tmp_path / "gating", {**files, ".github/workflows/ci.yml": _GATING
                                             + "      - run: uv sync --frozen\n"})
    assert ci_installs_frozen(gating, a_register(), {}).passed

    dispatch = make_repo(tmp_path / "dispatch", {**files, ".github/workflows/ci.yml": _DISPATCH
                                                 + "      - run: uv sync --frozen\n"})
    result = ci_installs_frozen(dispatch, a_register(), {})
    assert not result.passed
    assert "python" in result.message


# --- H4 — the cloud credentials SEC-002 forbids ------------------------------


def test_h4_the_credential_names_come_from_the_register(tmp_path: Path) -> None:
    """The move ADR 0018 ratified and never made.

    The seven names were a tuple in the checker through three implementation
    passes, mentioned in none of them, while the criterion recording ADR 0018 as
    implemented was ticked. A repository on a cloud the list has not heard of is
    one where SEC-002 passes for want of a name.
    """
    repo = make_repo(
        tmp_path / "repo",
        {
            ".github/workflows/ci.yml": _GATING
            + "      - run: deploy\n        env:\n"
            + "          ORACLE_API_KEY: ${{ secrets.ORACLE_API_KEY }}\n"
        },
    )
    assert no_static_cloud_keys(repo, a_register(), {}).passed

    def add_the_name(document: dict[str, Any]) -> None:
        document["cloud_credentials"].append("ORACLE_API_KEY")

    result = no_static_cloud_keys(repo, register_with(tmp_path, add_the_name), {})
    assert not result.passed
    assert "ORACLE_API_KEY" in result.message


def test_h4_the_spelling_equivalence_stays_in_the_checker(tmp_path: Path) -> None:
    """Which names is the register's; that `-` and `_` are the same is not."""
    repo = make_repo(
        tmp_path,
        {
            ".github/workflows/ci.yml": _GATING
            + "      - uses: aws-actions/configure-aws-credentials@v4\n"
            + "        with:\n          aws-access-key-id: ${{ secrets.PROD_KEY }}\n"
        },
    )
    result = no_static_cloud_keys(repo, a_register(), {})
    assert not result.passed
    assert "AWS_ACCESS_KEY_ID" in result.message


# --- H7 — an exemption may not hide a file the repository tracks -------------


_DOC_ARGS = {
    "max_line_length": 250,
    "tool": "markdownlint-cli2",
    "editor_extension": "DavidAnson.vscode-markdownlint",
}


def _doc_repo(root: Path, cli2: str) -> Repo:
    """A repository wired for DOC-001 at all three loci, plus the given runner config."""
    return make_repo(
        root,
        {
            "README.md": "# Title\n\nBody.\n",
            "docs/guide.md": "# Guide\n\nBody.\n",
            ".markdownlint.yaml": "default: true\nMD013:\n  line_length: 250\n",
            ".markdownlint-cli2.yaml": cli2,
            ".devcontainer/devcontainer.json": (
                '{"customizations": {"vscode": {"extensions": '
                '["DavidAnson.vscode-markdownlint"]}}}\n'
            ),
            ".pre-commit-config.yaml": (
                "repos:\n  - repo: local\n    hooks:\n      - id: markdownlint-cli2\n"
                "        entry: npx --no-install markdownlint-cli2\n"
            ),
            ".github/workflows/ci.yml": _GATING
            + '      - run: npx --no-install markdownlint-cli2 "**/*.md"\n',
        },
    )


def test_h7_an_exemption_hiding_a_tracked_file_fails(tmp_path: Path) -> None:
    """ADR 0019. The `.claude/**` case, which a person found and no check did.

    The rule was "no ignore path", which this repository broke on its first day
    and which still could not tell `node_modules` from authored content.
    """
    repo = _doc_repo(tmp_path / "hidden", 'ignores:\n  - "docs/**"\n')
    result = markdown_gate_wired_at_all_loci(repo, a_register(), _DOC_ARGS)
    assert not result.passed
    assert "docs/**" in result.message
    assert "docs/guide.md" in result.message


def test_h7_an_exemption_over_untracked_content_is_not_a_weakening(tmp_path: Path) -> None:
    """The mirror. Excluding what git does not track scopes the tool, not the control."""
    repo = _doc_repo(tmp_path / "scoped", 'ignores:\n  - "**/node_modules/**"\n')
    result = markdown_gate_wired_at_all_loci(repo, a_register(), _DOC_ARGS)
    assert result.passed, result.message


def test_h7_this_repository_carries_no_exemption_at_all() -> None:
    """The derived list, in place: `gitignore: true` and nothing to review."""
    config = yaml.safe_load((REPO_ROOT / ".markdownlint-cli2.yaml").read_text(encoding="utf-8"))
    assert config.get("gitignore") is True, "the exemption list must be derived, not kept"
    assert not config.get("ignores"), (
        "an entry here is a real exemption and needs a reason in the register"
    )
