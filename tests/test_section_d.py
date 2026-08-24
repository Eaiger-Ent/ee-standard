"""One test per row of `docs/09-phase-1.5-review.md` § D — assert precision.

Every test here encodes an input the checker got wrong: a **false negative**
where an assert passed while the control's `enforces` did not hold, or a **false
positive** where a conformant repository failed. Each fails on the code as it
stood before Phase 1.5 and passes after, which is what the § D exit criterion
asks for.

They are collected in one file on purpose. § D is the criterion the build plan
calls "the real gate this time", because Phase 1's suite passed 48 checks while
GOV-002 could not fail and a non-git directory reported clean — it exercised the
paths the author had in mind rather than the paths an adversary would take.
"""

from __future__ import annotations

import json
from pathlib import Path

from conftest import a_register, editor_settings, make_repo
from standard_check.asserts_command import (
    actions_pinned_to_sha,
    ci_installs_frozen,
    linter_wired_at_all_loci,
    no_failure_suppression,
    no_static_cloud_keys,
    typecheck_strict_and_blocking,
)
from standard_check.asserts_command import (
    tests_run_and_block as check_tests_run_and_block,
)
from standard_check.asserts_file import (
    dependency_update_config_covers_all_ecosystems,
    devcontainer_image_digest_pinned,
    dockerfile_final_user_is_non_root,
)
from standard_check.predicates import compile_predicate

_DIGEST = "sha256:" + "a" * 64
_SHA40 = "d" * 40


def _wf(body: str, *, on: str = "[push, pull_request]") -> str:
    return f"on: {on}\njobs:\n  job:\n    runs-on: ubuntu-latest\n    steps:\n{body}"


# --------------------------------------------------------------------------
# False negatives — the assert passed while the control did not hold.
# --------------------------------------------------------------------------


def test_sec_002_lowercase_hyphenated_cloud_key(tmp_path: Path) -> None:
    """`aws-access-key-id:` is the same credential as `AWS_ACCESS_KEY_ID`.

    The scan was a case-sensitive substring match over seven uppercase names, so
    the commonest spelling — an action input — went unseen.
    """
    repo = make_repo(
        tmp_path / "r",
        {
            ".github/workflows/ci.yml": _wf(
                "      - uses: aws-actions/configure-aws-credentials@v4\n"
                "        with:\n"
                "          aws-access-key-id: ${{ secrets.PROD_KEY }}\n"
            )
        },
    )
    result = no_static_cloud_keys(repo, a_register(), {})
    assert not result.passed
    assert "AWS_ACCESS_KEY_ID" in result.message


def test_tst_001_installing_pytest_is_not_running_it(tmp_path: Path) -> None:
    """`pip install pytest==8.0.0` mentions pytest and runs no tests."""
    repo = make_repo(
        tmp_path / "r",
        {".github/workflows/ci.yml": _wf("      - run: pip install pytest==8.0.0\n")},
    )
    assert not check_tests_run_and_block(repo, a_register(), {}).passed


def test_tst_001_workflow_dispatch_only_is_not_a_gate(tmp_path: Path) -> None:
    """`on:` was never read, so a click-to-run workflow counted as CI.

    Theme T-3 in its purest form: declared, and unreachable from the event that
    decides a merge.
    """
    repo = make_repo(
        tmp_path / "r",
        {
            ".github/workflows/ci.yml": _wf(
                "      - run: uv run pytest\n", on="workflow_dispatch"
            )
        },
    )
    result = check_tests_run_and_block(repo, a_register(), {})
    assert not result.passed
    assert "gates nothing" in result.message


def test_sup_003_job_level_reusable_workflow(tmp_path: Path) -> None:
    """Only `jobs.*.steps` was walked, so a job-level `uses:` was invisible."""
    repo = make_repo(
        tmp_path / "r",
        {
            ".github/workflows/ci.yml": (
                "on: [push]\njobs:\n  call:\n"
                "    uses: other/repo/.github/workflows/x.yml@main\n"
            )
        },
    )
    result = actions_pinned_to_sha(repo, a_register(), {})
    assert not result.passed
    assert "other/repo" in result.message


def test_quoted_continue_on_error_suppresses(tmp_path: Path) -> None:
    """`continue-on-error: "true"` is honoured by GitHub; `is True` was not."""
    repo = make_repo(
        tmp_path / "r",
        {
            ".github/workflows/ci.yml": _wf(
                '      - run: uv run pytest\n        continue-on-error: "true"\n'
            )
        },
    )
    assert not no_failure_suppression(repo, a_register(), {}).passed
    assert not check_tests_run_and_block(repo, a_register(), {}).passed


def test_or_colon_idiom_suppresses(tmp_path: Path) -> None:
    """`|| :` is `|| true` spelled with the shell's no-op builtin."""
    repo = make_repo(
        tmp_path / "r",
        {".github/workflows/ci.yml": _wf('      - run: "uv run pytest || :"\n')},
    )
    assert not no_failure_suppression(repo, a_register(), {}).passed


def test_typ_001_blanket_override_switches_strict_off(tmp_path: Path) -> None:
    """`strict = true` plus an override ignoring every module is not strict."""
    repo = make_repo(
        tmp_path / "r",
        {
            "pyproject.toml": (
                "[tool.mypy]\nstrict = true\n\n"
                '[[tool.mypy.overrides]]\nmodule = ["*"]\nignore_errors = true\n'
            ),
            ".pre-commit-config.yaml": (
                "repos:\n  - repo: local\n    hooks:\n      - id: mypy\n"
            ),
            ".github/workflows/ci.yml": _wf("      - run: uv run mypy\n"),
        },
    )
    result = typecheck_strict_and_blocking(repo, a_register(), {"role": "typecheck"})
    assert not result.passed
    assert "every module" in result.message


def test_sup_002_disabled_renovate_config(tmp_path: Path) -> None:
    """Any renovate filename was accepted unparsed, `enabled: false` included."""
    repo = make_repo(
        tmp_path / "r",
        {"pyproject.toml": "[project]\n", "renovate.json": json.dumps({"enabled": False})},
    )
    result = dependency_update_config_covers_all_ecosystems(repo, a_register(), {})
    assert not result.passed
    assert "enabled: false" in result.message


def test_sup_001_typescript_repo_with_no_workflows(tmp_path: Path) -> None:
    """Only python was ever required, so a node repo passed vacuously."""
    repo = make_repo(tmp_path / "r", {"package.json": "{}\n"})
    result = ci_installs_frozen(repo, a_register(), {})
    assert not result.passed
    assert "node" in result.message


def test_sup_001_poetry_and_pip3_installs(tmp_path: Path) -> None:
    """`pip3`, `poetry` and `pdm` were unmatched, so they re-resolved freely.

    Each fixture also performs a *frozen* install, so the "no frozen install for
    python" branch cannot be what fails it. Without that, the test passed before
    the fix for a reason unrelated to the row it claims to cover — which is the
    kind of test the § D criterion exists to rule out.
    """
    for name, command in (("poetry", "poetry install"), ("pip3", "pip3 install flask")):
        repo = make_repo(
            tmp_path / name,
            {
                "pyproject.toml": "[project]\n",
                ".github/workflows/ci.yml": _wf(
                    "      - run: uv sync --frozen\n" f"      - run: {command}\n"
                ),
            },
        )
        result = ci_installs_frozen(repo, a_register(), {})
        assert not result.passed, name
        assert "re-resolves" in result.message or "unpinned" in result.message


def test_bld_001_arg_expands_to_root(tmp_path: Path) -> None:
    """`ARG USERNAME=root` + `USER ${USERNAME}` — the literal token was compared."""
    repo = make_repo(
        tmp_path / "r",
        {"Dockerfile": "FROM base\nARG USERNAME=root\nUSER ${USERNAME}\n"},
    )
    result = dockerfile_final_user_is_non_root(repo, a_register(), {})
    assert not result.passed
    assert "runs as root" in result.message


# --------------------------------------------------------------------------
# False positives — a conformant repository failed.
# --------------------------------------------------------------------------


def test_pip_install_across_a_continuation_line(tmp_path: Path) -> None:
    """Physical lines were iterated, splitting the command from its pin."""
    repo = make_repo(
        tmp_path / "r",
        {
            "pyproject.toml": "[project]\n",
            ".github/workflows/ci.yml": _wf(
                "      - run: |\n"
                "          pip install \\\n"
                "            ruff==0.14.5\n"
                "          pip install -r requirements.txt\n"
            ),
        },
    )
    assert ci_installs_frozen(repo, a_register(), {}).passed


def test_lint_via_pre_commit_run_all_files(tmp_path: Path) -> None:
    """A step running the whole suite runs every hook the config wires."""
    repo = make_repo(
        tmp_path / "r",
        {
            "pyproject.toml": "[tool.ruff]\nline-length = 100\n",
            ".pre-commit-config.yaml": (
                "repos:\n  - repo: local\n    hooks:\n      - id: ruff\n"
            ),
            ".vscode/extensions.json": json.dumps({"recommendations": ["charliermarsh.ruff"]}),
            ".vscode/settings.json": editor_settings("charliermarsh.ruff"),
            ".github/workflows/ci.yml": _wf("      - run: pre-commit run --all-files\n"),
        },
    )
    result = linter_wired_at_all_loci(repo, a_register(), {"role": "lint"})
    assert result.passed, result.message


def test_editor_locus_via_vscode_extensions(tmp_path: Path) -> None:
    """Demanding a devcontainer entry invented an LNT-001 dependency on DEV-001."""
    repo = make_repo(
        tmp_path / "r",
        {
            "pyproject.toml": "[tool.ruff]\nline-length = 100\n",
            ".pre-commit-config.yaml": (
                "repos:\n  - repo: local\n    hooks:\n      - id: ruff\n"
            ),
            ".vscode/extensions.json": json.dumps({"recommendations": ["charliermarsh.ruff"]}),
            ".vscode/settings.json": editor_settings("charliermarsh.ruff"),
            ".github/workflows/ci.yml": _wf("      - run: uv run ruff check .\n"),
        },
    )
    assert linter_wired_at_all_loci(repo, a_register(), {"role": "lint"}).passed


def test_mypy_configured_in_its_own_file(tmp_path: Path) -> None:
    """Only `[tool.mypy]` was read; mypy supports `mypy.ini` and `setup.cfg`."""
    repo = make_repo(
        tmp_path / "r",
        {
            "pyproject.toml": "[project]\nname = 'x'\n",
            "mypy.ini": "[mypy]\nstrict = True\n",
            ".pre-commit-config.yaml": (
                "repos:\n  - repo: local\n    hooks:\n      - id: mypy\n"
            ),
            ".github/workflows/ci.yml": _wf("      - run: uv run mypy\n"),
        },
    )
    result = typecheck_strict_and_blocking(repo, a_register(), {"role": "typecheck"})
    assert result.passed, result.message


def test_other_test_command_spellings(tmp_path: Path) -> None:
    """The regex listed six spellings; real repos use many more."""
    register = a_register()
    for command in ("npm run test", "make test", "tox", "gradle test", "rspec"):
        repo = make_repo(
            tmp_path / command.replace(" ", "-"),
            {".github/workflows/ci.yml": _wf(f"      - run: {command}\n")},
        )
        assert check_tests_run_and_block(repo, register, {}).passed, command


def test_devcontainer_that_builds_from_a_dockerfile(tmp_path: Path) -> None:
    """DEV-001 demanded `image:`; the Dockerfile's own FROM pin was never read."""
    repo = make_repo(
        tmp_path / "r",
        {
            ".devcontainer/devcontainer.json": json.dumps(
                {"build": {"dockerfile": "Dockerfile"}}
            ),
            ".devcontainer/Dockerfile": f"FROM debian@{_DIGEST}\nUSER app\n",
        },
    )
    assert devcontainer_image_digest_pinned(repo, a_register(), {}).passed
    floating = make_repo(
        tmp_path / "f",
        {
            ".devcontainer/devcontainer.json": json.dumps(
                {"build": {"dockerfile": "Dockerfile"}}
            ),
            ".devcontainer/Dockerfile": "FROM debian:trixie\nUSER app\n",
        },
    )
    assert not devcontainer_image_digest_pinned(floating, a_register(), {}).passed


def test_container_action_pinned_by_image_digest(tmp_path: Path) -> None:
    """`docker://alpine@sha256:<64 hex>` is pinned as hard as a commit SHA."""
    repo = make_repo(
        tmp_path / "r",
        {
            ".github/workflows/ci.yml": _wf(
                f"      - uses: docker://alpine@{_DIGEST}\n"
                f"      - uses: other/action@{_SHA40}\n"
            )
        },
    )
    result = actions_pinned_to_sha(repo, a_register(), {})
    assert result.passed, result.message


def test_container_predicate_agrees_with_the_assert(tmp_path: Path) -> None:
    """§ C: a skip that hides a violation the checker can already detect.

    `any Dockerfile exists` was an exact basename match while BLD-001's assert
    also accepts `Dockerfile.*` and `*.Dockerfile`, so a repo whose only
    container file was `Dockerfile.prod` ending in `USER root` reported
    `SKIPPED (predicate)` — while the assert called directly returned FAIL.
    """
    register = a_register()
    predicate = compile_predicate(register.predicates["container"])
    for filename in ("Dockerfile", "Dockerfile.prod", "service.Dockerfile"):
        repo = make_repo(tmp_path / filename, {filename: "FROM base\nUSER root\n"})
        assert predicate(repo), filename
        assert not dockerfile_final_user_is_non_root(repo, register, {}).passed, filename
    clean = make_repo(tmp_path / "none", {"README.md": "# x\n"})
    assert not predicate(clean)
