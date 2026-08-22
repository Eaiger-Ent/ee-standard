"""File-shaped assertions against fixture repositories."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from conftest import a_register, make_repo
from standard_check.asserts_file import (
    dependency_update_config_covers_all_ecosystems,
    devcontainer_image_digest_pinned,
    devcontainer_lock_covers_all_features,
    dockerfile_final_user_is_non_root,
    lockfile_present_and_tracked,
    precommit_hook_present,
    secret_files_are_gitignored,
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


def test_renovate_narrowed_to_custom_managers_is_not_blanket_coverage(tmp_path: Path) -> None:
    """`enabledManagers: [custom.regex]` proposes literals, not ecosystems.

    A renovate config used to be read as covering everything on the strength of
    its filename. This repository narrows it on purpose — Renovate updates the
    two version literals Dependabot cannot see, and Dependabot keeps the
    ecosystems — so reading the file as blanket coverage would report a
    coverage switched off two lines further down.
    """
    narrowed = json.dumps({"enabledManagers": ["custom.regex"]})
    alone = make_repo(
        tmp_path / "a",
        {"pyproject.toml": "[project]\n", "renovate.json": narrowed},
    )
    result = dependency_update_config_covers_all_ecosystems(alone, a_register(), {})
    assert not result.passed
    assert "custom managers only" in result.message

    # The same config alongside a Dependabot file that does cover the
    # ecosystems is the shape this repository actually ships.
    paired = make_repo(
        tmp_path / "b",
        {
            "pyproject.toml": "[project]\n",
            "renovate.json": narrowed,
            ".github/dependabot.yml": (
                "version: 2\nupdates:\n  - package-ecosystem: uv\n    directory: /\n"
            ),
        },
    )
    assert dependency_update_config_covers_all_ecosystems(paired, a_register(), {}).passed

    # An unnarrowed renovate config still covers everything by default.
    default = make_repo(
        tmp_path / "c",
        {
            "pyproject.toml": "[project]\n",
            "renovate.json": json.dumps({"extends": ["config:base"]}),
        },
    )
    assert dependency_update_config_covers_all_ecosystems(default, a_register(), {}).passed


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


# --- SEC-001's ignore rule, added at register contract 18 -------------------

_SECRETS = [".devcontainer/.env", ".devcontainer/.env.docker"]
_ARGS: Mapping[str, object] = {"paths": _SECRETS}


def test_secret_files_are_gitignored(tmp_path: Path) -> None:
    """The passing shape: ignored, untracked, by a rule git carries."""
    repo = make_repo(
        tmp_path / "r",
        {".gitignore": ".devcontainer/.env\n.devcontainer/.env.docker\n", "src/app.py": "x = 1\n"},
    )
    (repo.root / ".devcontainer").mkdir()
    (repo.root / ".devcontainer/.env").write_text("GITHUB_TOKEN=ghp_real\n", encoding="utf-8")
    result = secret_files_are_gitignored(repo, a_register(), _ARGS)
    assert result.passed, result.message
    assert ".gitignore" in result.message


def test_an_unignored_secret_file_fails(tmp_path: Path) -> None:
    """The case the prose was guarding, and the one nothing checked until 18."""
    repo = make_repo(tmp_path / "r", {".gitignore": "__pycache__/\n"})
    result = secret_files_are_gitignored(repo, a_register(), _ARGS)
    assert not result.passed
    assert "is not ignored" in result.message
    # Both are named, not just the first: a repository that ignored one of the
    # two would otherwise be told about half its exposure.
    assert ".devcontainer/.env" in result.message
    assert ".devcontainer/.env.docker" in result.message


def test_one_ignored_and_one_not_still_fails(tmp_path: Path) -> None:
    """`.env.docker` is derived from `.env` and holds the same credentials.

    A glob that catches the first and misses the second is the reason
    `.gitignore` here lists both in their own right rather than leaving the
    second to `.env*`.
    """
    repo = make_repo(tmp_path / "r", {".gitignore": ".devcontainer/.env\n"})
    result = secret_files_are_gitignored(repo, a_register(), _ARGS)
    assert not result.passed
    assert ".devcontainer/.env.docker is not ignored" in result.message


def test_a_tracked_secret_file_fails_and_says_why(tmp_path: Path) -> None:
    """Ignoring a file git already carries changes nothing about it.

    Reported separately from "not ignored" because the remedy is different: an
    ignore rule fixes that one, and only a history rewrite and a rotated
    credential fix this one.
    """
    repo = make_repo(
        tmp_path / "r",
        {".gitignore": "__pycache__/\n", ".devcontainer/.env": "GITHUB_TOKEN=ghp_real\n"},
    )
    result = secret_files_are_gitignored(repo, a_register(), _ARGS)
    assert not result.passed
    assert "is tracked" in result.message


def test_an_ignore_rule_git_does_not_carry_fails(tmp_path: Path) -> None:
    """The quiet one: it works here and nowhere else.

    `.git/info/exclude` is not committed, so the file is ignored on the author's
    machine and unignored in every clone — a pass that would mean nothing.
    """
    repo = make_repo(tmp_path / "r", {"src/app.py": "x = 1\n"})
    exclude = repo.root / ".git/info/exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    exclude.write_text(".devcontainer/.env\n.devcontainer/.env.docker\n", encoding="utf-8")
    result = secret_files_are_gitignored(repo, a_register(), _ARGS)
    assert not result.passed
    assert "does not track" in result.message


def test_an_untracked_gitignore_fails_for_the_same_reason(tmp_path: Path) -> None:
    """The shipped template's `.devcontainer/.gitignore`, if the copy is not committed."""
    repo = make_repo(tmp_path / "r", {"src/app.py": "x = 1\n"})
    (repo.root / ".devcontainer").mkdir()
    (repo.root / ".devcontainer/.gitignore").write_text(".env\n.env.docker\n", encoding="utf-8")
    result = secret_files_are_gitignored(repo, a_register(), _ARGS)
    assert not result.passed
    assert "does not track" in result.message


def test_a_tracked_nested_gitignore_passes(tmp_path: Path) -> None:
    """The template's own shape, once committed: rules relative to their directory."""
    repo = make_repo(
        tmp_path / "r",
        {".devcontainer/.gitignore": ".env\n.env.docker\n", "src/app.py": "x = 1\n"},
    )
    result = secret_files_are_gitignored(repo, a_register(), _ARGS)
    assert result.passed, result.message
    assert ".devcontainer/.gitignore" in result.message


def test_an_empty_paths_list_is_not_a_pass(tmp_path: Path) -> None:
    """An assert that checks nothing must not report that nothing is wrong."""
    repo = make_repo(tmp_path / "r", {".gitignore": "__pycache__/\n"})
    empty: tuple[Mapping[str, object], ...] = ({}, {"paths": []}, {"paths": "not-a-list"})
    for args in empty:
        result = secret_files_are_gitignored(repo, a_register(), args)
        assert not result.passed, args
        assert "non-empty" in result.message
