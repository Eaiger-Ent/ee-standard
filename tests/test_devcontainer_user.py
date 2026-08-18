"""BLD-001's property, verified for a devcontainer as well as a Dockerfile.

The Phase 0.5 criterion "the container's final user is not root, stated
explicitly rather than inherited from the base image" was ticked on
`remoteUser` being present in `devcontainer.json`. Nothing read it. BLD-001
applied only to `container`, a predicate this repository does not satisfy
because it builds from an `image:` rather than a Dockerfile — so the control
skipped, and a JSON key nobody verified stood in for a verdict.

Two things are tested here: the assert itself, and the block narrowing that lets
one control hold both mechanisms without running either against the shape it
cannot read.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from conftest import a_register, make_repo
from standard_check.asserts_file import devcontainer_user_is_non_root
from standard_check.register import load_register
from standard_check.repo import Repo
from standard_check.runner import Verdict, run_control

_IMAGE = "mcr.example/base:trixie@sha256:" + "a" * 64


def _devcontainer(root: Path, **keys: Any) -> Repo:
    config: dict[str, Any] = {"image": _IMAGE}
    config.update(keys)
    return make_repo(root, {".devcontainer/devcontainer.json": json.dumps(config)})


def test_a_stated_non_root_user_passes(tmp_path: Path) -> None:
    repo = _devcontainer(tmp_path / "a", remoteUser="vscode")
    result = devcontainer_user_is_non_root(repo, a_register(), {})
    assert result.passed, result.message
    assert "vscode" in result.message


def test_an_unstated_user_is_inherited_and_fails(tmp_path: Path) -> None:
    """The box this criterion was originally ticked on.

    A devcontainer naming no user runs as whatever the base image happens to
    use — which may be root today, and may become root on any digest bump.
    Non-root by luck is not the property BLD-001 states.
    """
    repo = _devcontainer(tmp_path / "b")
    result = devcontainer_user_is_non_root(repo, a_register(), {})
    assert not result.passed
    assert "inherited from the image" in result.message


@pytest.mark.parametrize(
    ("keys", "expected"),
    [
        ({"remoteUser": "root"}, "remoteUser: root"),
        ({"containerUser": "root", "remoteUser": "vscode"}, "containerUser: root"),
        ({"remoteUser": "0"}, "remoteUser: 0"),
        ({"containerUser": "root:root"}, "containerUser: root:root"),
    ],
)
def test_root_in_either_key_fails(tmp_path: Path, keys: dict[str, str], expected: str) -> None:
    """`containerUser: root` beside `remoteUser: vscode` is still a root container."""
    repo = _devcontainer(tmp_path / expected.replace(":", "-").replace(" ", ""), **keys)
    result = devcontainer_user_is_non_root(repo, a_register(), {})
    assert not result.passed
    assert expected in result.message


def test_a_missing_or_malformed_devcontainer_is_a_verdict(tmp_path: Path) -> None:
    """Never an abort: a read failure is a FAIL naming the file (§ B)."""
    absent = make_repo(tmp_path / "absent", {"README.md": "# x\n"})
    assert not devcontainer_user_is_non_root(absent, a_register(), {}).passed
    malformed = make_repo(tmp_path / "bad", {".devcontainer/devcontainer.json": "[1, 2]\n"})
    result = devcontainer_user_is_non_root(malformed, a_register(), {})
    assert not result.passed
    assert "not a mapping" in result.message


def _bld_001() -> Any:
    register, errors = load_register(Path("controls.yaml"))
    assert register is not None, errors
    control = register.control("BLD-001")
    assert control is not None
    return register, control


def test_hadolint_does_not_run_against_a_repo_with_no_dockerfile(tmp_path: Path) -> None:
    """The reason each block names the shape it can read.

    Widening BLD-001 to devcontainers without narrowing its blocks would run
    `hadolint` against a repository holding no Dockerfile. That is not a
    finding, it is a category error — and with the tool absent it would report
    UNCLASSIFIED, which reads as "could not verify" over a control that was in
    fact fully verified by the block beside it.
    """
    register, control = _bld_001()
    repo = _devcontainer(tmp_path / "dc", remoteUser="vscode")
    result = run_control(control, register, repo)
    assert result.verdict is Verdict.PASS, result
    ran = [b.block.run or b.block.assert_name or "" for b in result.blocks]
    assert not any("hadolint" in name for name in ran), ran
    assert ran == ["devcontainer_user_is_non_root"], ran


def test_a_devcontainer_running_as_root_fails_the_control(tmp_path: Path) -> None:
    register, control = _bld_001()
    repo = _devcontainer(tmp_path / "root", remoteUser="root")
    assert run_control(control, register, repo).verdict is Verdict.FAIL


def test_a_repo_with_neither_shape_still_skips(tmp_path: Path) -> None:
    """No Dockerfile and no devcontainer means the control does not apply."""
    register, control = _bld_001()
    repo = make_repo(tmp_path / "plain", {"README.md": "# x\n"})
    assert run_control(control, register, repo).verdict is Verdict.SKIPPED_PREDICATE
