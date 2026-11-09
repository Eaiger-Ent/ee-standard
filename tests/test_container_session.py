"""The Apple `container` launcher refuses what it cannot reproduce.

ADR 0063 accepted a host launcher that maps the `devcontainer` CLI's resolved
output to `container` flags. Its one safety property is that the mapping is a
closed set: a key, flag, mount type or runtime call it does not handle is
refused by name. Silently dropping one would run a container that differs from
the one Docker runs, which is the declared-but-unreachable shape this register
exists to catch.

These tests drive the launcher's `check` subcommand, which applies the same
validation `up` does to files instead of live CLI output. They need `node`,
which every locus that runs pytest already has for markdownlint-cli2. They do
not need Apple `container` or macOS. The end-to-end run on a Mac is recorded in
`docs/20-apple-container-spike.md`.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from conftest import REPO_ROOT

LAUNCHER = REPO_ROOT / ".devcontainer" / "bin" / "container-session.mjs"
CLI = REPO_ROOT / "node_modules" / ".bin" / "devcontainer"

NODE = shutil.which("node")


def _config(**overrides: Any) -> dict[str, Any]:
    """A `read-configuration` output shaped like this repository's own."""
    configuration: dict[str, Any] = {
        "name": "probe",
        "image": "mcr.microsoft.com/devcontainers/base:trixie@sha256:" + "0" * 64,
        "features": {},
        "containerEnv": {"A": "1"},
        "initializeCommand": "bash .devcontainer/fetch-secrets.sh",
        "runArgs": ["--env-file", ".devcontainer/.env.docker", "--cpus", "8", "--memory", "8g"],
        "postCreateCommand": "bash .devcontainer/setup.sh",
        "postStartCommand": "bash .devcontainer/check-auth.sh",
        "remoteUser": "vscode",
        "mounts": ["source=probe-home,target=/home/vscode/.claude,type=volume"],
        "customizations": {"vscode": {}},
        "configFilePath": {"path": "/x/.devcontainer/devcontainer.json"},
    }
    configuration.update(overrides)
    return {
        "configuration": configuration,
        "workspace": {"workspaceFolder": "/workspaces/probe"},
    }


def _label(config: dict[str, Any], **last_overrides: Any) -> list[dict[str, Any]]:
    """A metadata label whose last entry is the config's build-time snapshot."""
    c = config["configuration"]
    last = {
        key: c[key]
        for key in ("postCreateCommand", "postStartCommand", "mounts", "containerEnv", "remoteUser")
    }
    last["customizations"] = {"vscode": {}}
    last.update(last_overrides)
    return [
        {"id": "ghcr.io/devcontainers/features/common-utils:2"},
        {"remoteUser": "vscode"},
        {"id": "ghcr.io/devcontainers/features/node:2", "customizations": {}},
        last,
    ]


_BASE = "mcr.microsoft.com/devcontainers/base:trixie@sha256:" + "0" * 64
_CALLS = [
    ["buildx", "version"],
    ["-v"],
    ["version", "--format", "{{.Server.Version}}"],
    ["inspect", "--type", "image", _BASE],
    ["build", "-t", "dev_container_feature_content_temp", "-f", "/c/Dockerfile.buildContent", "/c"],
    [
        "buildx",
        "build",
        "--platform",
        "linux/arm64",
        "--load",
        "--build-arg",
        "BUILDKIT_INLINE_CACHE=1",
        "--build-arg",
        f"_DEV_CONTAINERS_BASE_IMAGE={_BASE}",
        "--target",
        "dev_containers_target_stage",
        "-f",
        "/c/Dockerfile.extended",
        "-t",
        "probe-dev:local",
        "/c/empty-folder",
    ],
]


def _check(
    tmp_path: Path,
    config: dict[str, Any],
    label: list[dict[str, Any]] | None = None,
    calls: list[list[str]] | None = None,
) -> subprocess.CompletedProcess[str]:
    assert NODE, "node is not on PATH; every locus that runs pytest installs it"
    args = [NODE, str(LAUNCHER), "check", "--config", str(_write(tmp_path / "config.json", config))]
    if label is not None:
        args += ["--label", str(_write(tmp_path / "label.json", label))]
    if calls is not None:
        args += ["--calls", str(_write(tmp_path / "calls.json", calls))]
    return subprocess.run(args, capture_output=True, text=True, check=False)


def _write(path: Path, data: object) -> Path:
    path.write_text(json.dumps(data))
    return path


def _refused(result: subprocess.CompletedProcess[str], *names: str) -> None:
    assert result.returncode == 2, (
        f"expected a refusal (exit 2), got {result.returncode}\n{result.stdout}{result.stderr}"
    )
    for name in names:
        assert name in result.stderr, f"the refusal does not name {name!r}:\n{result.stderr}"


def test_the_shape_this_repository_uses_is_accepted(tmp_path: Path) -> None:
    config = _config()
    result = _check(tmp_path, config, _label(config), _CALLS)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("key", ["forwardPorts", "remoteEnv", "overrideCommand", "workspaceMount"])
def test_an_unhandled_config_key_is_refused_by_name(tmp_path: Path, key: str) -> None:
    _refused(_check(tmp_path, _config(**{key: "x"})), key)


def test_a_dockerfile_configuration_is_refused(tmp_path: Path) -> None:
    config = _config()
    del config["configuration"]["image"]
    _refused(_check(tmp_path, config), "image")


@pytest.mark.parametrize("flag", ["--privileged", "--cap-add", "-e", "--network"])
def test_an_unhandled_run_arg_is_refused_by_name(tmp_path: Path, flag: str) -> None:
    config = _config(runArgs=["--env-file", ".devcontainer/.env.docker", flag, "x"])
    _refused(_check(tmp_path, config), flag)


def test_a_run_arg_given_twice_is_refused(tmp_path: Path) -> None:
    _refused(_check(tmp_path, _config(runArgs=["--cpus", "8", "--cpus=4"])), "--cpus")


def test_a_bind_mount_is_refused(tmp_path: Path) -> None:
    config = _config(mounts=["source=/Users/x,target=/x,type=bind"])
    _refused(_check(tmp_path, config), "type=volume")


def test_a_mount_field_beyond_type_source_target_is_refused(tmp_path: Path) -> None:
    config = _config(mounts=["source=v,target=/x,type=volume,readonly"])
    _refused(_check(tmp_path, config), "readonly")


def test_an_object_form_lifecycle_command_is_refused(tmp_path: Path) -> None:
    config = _config(postCreateCommand={"a": "x", "b": "y"})
    _refused(_check(tmp_path, config), "postCreateCommand")


def test_a_workspace_not_directly_under_workspaces_is_refused(tmp_path: Path) -> None:
    """F5: the launcher mounts the checkout's parent at /workspaces."""
    config = _config()
    config["workspace"]["workspaceFolder"] = "/src/probe"
    _refused(_check(tmp_path, config), "/workspaces/<name>")


@pytest.mark.parametrize("key", ["entrypoint", "privileged", "init", "capAdd", "securityOpt"])
def test_an_unhandled_label_key_is_refused_by_name(tmp_path: Path, key: str) -> None:
    """A feature can contribute these. A launcher that ignored them would run
    a feature whose entrypoint never starts, or without the capability it
    declared."""
    config = _config()
    label = _label(config)
    label[2][key] = True
    _refused(_check(tmp_path, config, label), key)


def test_a_stale_image_is_refused(tmp_path: Path) -> None:
    config = _config()
    label = _label(config, postCreateCommand="bash an-older-setup.sh")
    _refused(_check(tmp_path, config, label), "stale", "--rebuild")


def test_an_unknown_runtime_call_is_refused(tmp_path: Path) -> None:
    """The CLI should only probe and build. Anything else means its call
    pattern moved, and replaying around the gap would be guessing."""
    calls = [*_CALLS, ["run", "-d", "probe-dev:local"]]
    _refused(_check(tmp_path, _config(), calls=calls), '"run"')


def test_an_unhandled_build_flag_is_refused(tmp_path: Path) -> None:
    calls = [["buildx", "build", "--secret", "id=x", "-t", "probe-dev:local", "/c"]]
    _refused(_check(tmp_path, _config(), calls=calls), "--secret")


def test_builds_are_replayed_with_only_the_docker_tokens_removed(tmp_path: Path) -> None:
    """F4: exactly `buildx` and `--load` are dropped. Everything else is kept
    as the CLI logged it, so the base image digest has one source."""
    result = _check(tmp_path, _config(), calls=_CALLS)
    assert result.returncode == 0, result.stderr
    builds = json.loads(result.stdout)["builds"]
    assert builds[0] == ["build", *_CALLS[4][1:]]
    expected = [token for token in _CALLS[5][1:] if token != "--load"]
    assert builds[1] == expected
    assert all("buildx" not in b and "--load" not in b for b in builds)


def test_no_build_call_is_refused(tmp_path: Path) -> None:
    _refused(_check(tmp_path, _config(), calls=_CALLS[:4]), "no build call")


def test_this_repositorys_devcontainer_is_within_the_handled_set(tmp_path: Path) -> None:
    """The refusals above are only half the property. The other half is that
    the configuration this repository actually ships passes, read by the pinned
    CLI exactly as the launcher reads it."""
    assert CLI.exists(), f"{CLI} is missing; `npm ci` installs the pinned CLI"
    stub = tmp_path / "docker"
    stub.write_text("#!/bin/sh\nexit 0\n")
    stub.chmod(0o755)
    read = subprocess.run(
        [
            str(CLI),
            "read-configuration",
            "--workspace-folder",
            str(REPO_ROOT),
            "--docker-path",
            str(stub),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert read.returncode == 0, read.stderr
    output = json.loads(read.stdout)
    # The launcher validates the folder's shape, not this checkout's name.
    output["workspace"]["workspaceFolder"] = "/workspaces/probe"
    result = _check(tmp_path, output)
    assert result.returncode == 0, result.stderr


def test_the_launcher_invokes_the_cli_the_lock_file_pins() -> None:
    """ADR 0020 and ADR 0063: the CLI is reached by the path its lock file
    owns, at an exact version no older than 0.90.0 (F1)."""
    source = LAUNCHER.read_text()
    assert '"node_modules", ".bin", "devcontainer"' in source
    pinned = json.loads((REPO_ROOT / "package.json").read_text())["devDependencies"][
        "@devcontainers/cli"
    ]
    assert pinned[0].isdigit(), f"@devcontainers/cli is {pinned!r}, not an exact version"
    major, minor = (int(part) for part in pinned.split(".")[:2])
    assert (major, minor) >= (0, 90), f"@devcontainers/cli {pinned} is below 0.90.0 (ADR 0063 F1)"
