"""File-shaped assertions against fixture repositories."""

from __future__ import annotations

import json
from pathlib import Path

from conftest import a_register, make_repo
from standard_check.asserts_file import (
    dependency_update_config_covers_all_ecosystems,
    devcontainer_image_digest_pinned,
    devcontainer_lock_covers_all_features,
    dockerfile_final_user_is_non_root,
    lockfile_present_and_tracked,
    markdownlint_config_present,
    precommit_hook_present,
)

_DIGEST = "sha256:" + "a" * 64


def test_precommit_hook_present(tmp_path: Path) -> None:
    repo = make_repo(
        tmp_path / "r",
        {".pre-commit-config.yaml": "repos:\n  - repo: local\n    hooks:\n      - id: gitleaks\n"},
    )
    assert precommit_hook_present(repo, a_register(), {"id": "gitleaks"}).passed
    assert not precommit_hook_present(repo, a_register(), {"id": "ruff"}).passed
    empty = make_repo(tmp_path / "empty", {})
    assert not precommit_hook_present(empty, a_register(), {"id": "gitleaks"}).passed


def test_lockfile_present_and_tracked(tmp_path: Path) -> None:
    with_lock = make_repo(tmp_path / "a", {"pyproject.toml": "[project]\n", "uv.lock": "# lock\n"})
    assert lockfile_present_and_tracked(with_lock, a_register(), {}).passed
    without = make_repo(tmp_path / "b", {"pyproject.toml": "[project]\n"})
    result = lockfile_present_and_tracked(without, a_register(), {})
    assert not result.passed
    assert "python" in result.message


def test_lockfile_must_be_tracked_not_just_present(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "r", {"pyproject.toml": "[project]\n"})
    (repo.root / "uv.lock").write_text("# lock\n", encoding="utf-8")
    # Present on disk, never `git add`ed after the commit — still not tracked.
    assert not lockfile_present_and_tracked(repo, a_register(), {}).passed


def test_dependency_update_config_coverage(tmp_path: Path) -> None:
    covered = make_repo(
        tmp_path / "a",
        {
            "pyproject.toml": "[project]\n",
            ".github/workflows/ci.yml": "jobs: {}\n",
            ".github/dependabot.yml": (
                "version: 2\nupdates:\n"
                "  - package-ecosystem: uv\n    directory: /\n"
                "  - package-ecosystem: github-actions\n    directory: /\n"
            ),
        },
    )
    assert dependency_update_config_covers_all_ecosystems(covered, a_register(), {}).passed
    partial = make_repo(
        tmp_path / "b",
        {
            "pyproject.toml": "[project]\n",
            ".github/workflows/ci.yml": "jobs: {}\n",
            ".github/dependabot.yml": (
                "version: 2\nupdates:\n  - package-ecosystem: github-actions\n    directory: /\n"
            ),
        },
    )
    result = dependency_update_config_covers_all_ecosystems(partial, a_register(), {})
    assert not result.passed
    assert "python" in result.message


def test_devcontainer_lock_coverage(tmp_path: Path) -> None:
    feature = "ghcr.io/devcontainers/features/python"
    lock = json.dumps(
        {"features": {f"{feature}:1": {"version": "1.0.0", "resolved": f"{feature}@{_DIGEST}"}}}
    )
    complete = make_repo(
        tmp_path / "a",
        {
            ".devcontainer/devcontainer.json": (
                "{\n  // pinned\n"
                + json.dumps({"image": f"base@{_DIGEST}", "features": {f"{feature}:1": {}}})[1:]
            ),
            ".devcontainer/devcontainer-lock.json": lock,
        },
    )
    assert devcontainer_lock_covers_all_features(complete, a_register(), {}).passed
    missing = make_repo(
        tmp_path / "b",
        {
            ".devcontainer/devcontainer.json": json.dumps(
                {
                    "image": f"base@{_DIGEST}",
                    "features": {f"{feature}:1": {}, "ghcr.io/x/y:1": {}},
                }
            ),
            ".devcontainer/devcontainer-lock.json": lock,
        },
    )
    result = devcontainer_lock_covers_all_features(missing, a_register(), {})
    assert not result.passed
    assert "ghcr.io/x/y is not in the lock file" in result.message


def test_devcontainer_image_digest(tmp_path: Path) -> None:
    pinned = make_repo(
        tmp_path / "a",
        {
            ".devcontainer/devcontainer.json": json.dumps(
                {"image": f"mcr.example/base:tag@{_DIGEST}"}
            )
        },
    )
    assert devcontainer_image_digest_pinned(pinned, a_register(), {}).passed
    floating = make_repo(
        tmp_path / "b",
        {".devcontainer/devcontainer.json": '{"image": "mcr.example/base:trixie"}\n'},
    )
    assert not devcontainer_image_digest_pinned(floating, a_register(), {}).passed


def test_dockerfile_final_user(tmp_path: Path) -> None:
    good = make_repo(
        tmp_path / "a",
        {"Dockerfile": "FROM base AS build\nUSER root\nFROM base\nUSER app\n"},
    )
    assert dockerfile_final_user_is_non_root(good, a_register(), {}).passed
    bad = make_repo(tmp_path / "b", {"Dockerfile": "FROM base\nUSER root\n"})
    assert not dockerfile_final_user_is_non_root(bad, a_register(), {}).passed
    absent = make_repo(tmp_path / "c", {"Dockerfile": "FROM base\n"})
    result = dockerfile_final_user_is_non_root(absent, a_register(), {})
    assert not result.passed
    assert "declares no USER" in result.message


def test_markdownlint_config_present(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "a", {".markdownlint.yaml": "default: true\n"})
    assert markdownlint_config_present(repo, a_register(), {}).passed
    assert not markdownlint_config_present(make_repo(tmp_path / "b", {}), a_register(), {}).passed


def test_go_rust_java_repos_need_a_lockfile(tmp_path: Path) -> None:
    """ADR 0018's measured harm.

    The ecosystem map lived in the checker and knew Python and Node, so a Go,
    Rust or Java repository with no lockfile at all passed SUP-001. Nobody
    decided that exemption — it was which dictionary keys someone wrote — and
    because the register did not record it, no review and no `review_by` could
    ever have surfaced it.
    """
    register = a_register()
    for name, manifest, lockfile in [
        ("go", "go.mod", "go.sum"),
        ("rust", "Cargo.toml", "Cargo.lock"),
        ("java", "build.gradle", "gradle.lockfile"),
    ]:
        unlocked = make_repo(tmp_path / f"{name}-unlocked", {manifest: "x\n"})
        result = lockfile_present_and_tracked(unlocked, register, {})
        assert not result.passed, f"{name} passed with no lockfile"
        assert name in result.message
        locked = make_repo(tmp_path / f"{name}-locked", {manifest: "x\n", lockfile: "y\n"})
        assert lockfile_present_and_tracked(locked, register, {}).passed


def test_requirements_txt_is_not_a_lockfile(tmp_path: Path) -> None:
    """§ D: an unpinned requirements.txt counted as a lockfile."""
    repo = make_repo(
        tmp_path / "r", {"pyproject.toml": "[project]\n", "requirements.txt": "flask\n"}
    )
    assert not lockfile_present_and_tracked(repo, a_register(), {}).passed
