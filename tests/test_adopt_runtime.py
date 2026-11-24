"""Stage 0 and stage 3 accept either container runtime (ADR 0065).

An adopter may run the devcontainer on Apple `container` or on Docker. Stage 0
fails only when neither answers, and reports each one that does in the words
`guided.sh` reads back to ask which to use. Stage 3 asks each runtime that
answers whether this folder's container is running.

The scripts run against stub runtimes on a `PATH` built for the test, so a
runner's own Docker never answers. The test copies the route and replaces
`inside_container()`, because the suite itself runs inside a container, where
stage 0 refuses to run.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
ADOPT = REPO_ROOT / "plugins" / "control-register" / "templates" / "adopt"
TEMPLATE = REPO_ROOT / "plugins" / "control-register" / "templates" / "devcontainer"
GUIDE = REPO_ROOT / "START-HERE.md"

#: The real programs the stages need. Each is linked into the test's PATH by
#: name, so nothing else on the runner's PATH, such as its Docker, is visible.
REAL_TOOLS = (
    "bash", "basename", "cat", "dirname", "git", "grep", "head", "mktemp", "node",
    "rm", "sed", "sort", "tail", "tee", "tr",
)


def _lib_value(name: str) -> str:
    lib = (ADOPT / "_lib.sh").read_text(encoding="utf-8")
    found = re.search(rf'^{name}="([^"]+)"$', lib, re.M)
    assert found is not None, f"_lib.sh has no {name} line"
    return found.group(1)


RUNTIME_APPLE = _lib_value("RUNTIME_APPLE")
RUNTIME_DOCKER = _lib_value("RUNTIME_DOCKER")


def _stub(bin_dir: Path, name: str, body: str) -> None:
    path = bin_dir / name
    path.write_text(f"#!/usr/bin/env bash\n{body}\n", encoding="utf-8")
    path.chmod(0o755)


def _route(tmp_path: Path) -> Path:
    """A copy of the route that does not refuse to run inside a container."""
    route = tmp_path / "adopt"
    shutil.copytree(ADOPT, route)
    with (route / "_lib.sh").open("a", encoding="utf-8") as lib:
        lib.write("\ninside_container() { return 1; }\n")
    return route


def _host(
    tmp_path: Path,
    *,
    docker: str | None = None,
    apple: str | None = None,
    devcontainer: bool = True,
    running: list[dict[str, dict[str, str]]] | None = None,
) -> dict[str, str]:
    """A PATH with the tools stage 0 asks for, and the runtimes asked for.

    `docker` and `apple` are `"running"`, `"stopped"` or None for not installed.
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for tool in REAL_TOOLS:
        found = shutil.which(tool)
        assert found is not None, f"the test needs {tool} on PATH"
        (bin_dir / tool).symlink_to(found)
    for tool in ("brew", "claude", "npm", "uv"):
        _stub(bin_dir, tool, "exit 0")
    _stub(bin_dir, "gh", 'if [ "$1 $2" = "config get" ]; then echo https; fi\nexit 0')
    if devcontainer:
        _stub(bin_dir, "devcontainer", "exit 0")
    if docker is not None:
        answer = 0 if docker == "running" else 1
        _stub(
            bin_dir,
            "docker",
            f'if [ "$1" = info ]; then\n'
            f'  [ {answer} -eq 0 ] && [ "$2" = --format ] && echo 16000000000\n'
            f"  exit {answer}\n"
            f"fi\n"
            f"exit 0",
        )
    if apple is not None:
        answer = 0 if apple == "running" else 1
        listing = json.dumps(running or [])
        _stub(
            bin_dir,
            "container",
            f'if [ "$1 $2" = "system status" ]; then exit {answer}; fi\n'
            f"if [ \"$1\" = list ]; then echo '{listing}'; fi\n"
            f"exit 0",
        )
    home = tmp_path / "home"
    home.mkdir()
    return {"PATH": str(bin_dir), "HOME": str(home), "USER": "probe"}


def _run(script: Path, env: dict[str, str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(script)], cwd=cwd, env=env, capture_output=True, text=True, check=False
    )


# --- stage 0 ------------------------------------------------------------------


def test_stage_0_fails_when_no_runtime_answers(tmp_path: Path) -> None:
    route = _route(tmp_path)
    result = _run(route / "00-tools.sh", _host(tmp_path), tmp_path)
    assert result.returncode == 1, result.stdout
    assert "no container runtime answers" in result.stdout
    assert RUNTIME_APPLE not in result.stdout
    assert RUNTIME_DOCKER not in result.stdout


def test_stage_0_fails_when_both_are_installed_and_neither_runs(tmp_path: Path) -> None:
    route = _route(tmp_path)
    env = _host(tmp_path, docker="stopped", apple="stopped")
    result = _run(route / "00-tools.sh", env, tmp_path)
    assert result.returncode == 1, result.stdout
    assert "no container runtime answers" in result.stdout
    assert "its services are not running" in result.stdout
    assert "Docker is not running" in result.stdout


def test_stage_0_passes_with_apple_container_alone(tmp_path: Path) -> None:
    """No Docker at all, and no devcontainer CLI on PATH: the Apple route needs neither."""
    route = _route(tmp_path)
    env = _host(tmp_path, apple="running", devcontainer=False)
    result = _run(route / "00-tools.sh", env, tmp_path)
    assert result.returncode == 0, result.stdout
    assert RUNTIME_APPLE in result.stdout
    assert RUNTIME_DOCKER not in result.stdout
    assert "✗" not in result.stdout


def test_stage_0_passes_with_docker_alone(tmp_path: Path) -> None:
    route = _route(tmp_path)
    result = _run(route / "00-tools.sh", _host(tmp_path, docker="running"), tmp_path)
    assert result.returncode == 0, result.stdout
    assert RUNTIME_DOCKER in result.stdout
    assert RUNTIME_APPLE not in result.stdout


def test_stage_0_reports_both_when_both_answer(tmp_path: Path) -> None:
    route = _route(tmp_path)
    env = _host(tmp_path, docker="running", apple="running")
    result = _run(route / "00-tools.sh", env, tmp_path)
    assert result.returncode == 0, result.stdout
    assert RUNTIME_APPLE in result.stdout
    assert RUNTIME_DOCKER in result.stdout


def test_stage_0_passes_with_apple_running_and_docker_stopped(tmp_path: Path) -> None:
    route = _route(tmp_path)
    env = _host(tmp_path, docker="stopped", apple="running")
    result = _run(route / "00-tools.sh", env, tmp_path)
    assert result.returncode == 0, result.stdout
    assert RUNTIME_APPLE in result.stdout
    assert RUNTIME_DOCKER not in result.stdout
    assert "Docker is not running" in result.stdout


def test_the_docker_route_still_needs_the_devcontainer_cli(tmp_path: Path) -> None:
    route = _route(tmp_path)
    env = _host(tmp_path, docker="running", devcontainer=False)
    result = _run(route / "00-tools.sh", env, tmp_path)
    assert result.returncode == 1, result.stdout
    assert "devcontainer CLI — not on PATH" in result.stdout


# --- stage 3 ------------------------------------------------------------------


def _substituted_project(tmp_path: Path) -> Path:
    project = tmp_path / "my-app"
    (project / ".devcontainer").mkdir(parents=True)
    (project / ".devcontainer" / "setup.sh").write_text(f"# {'a' * 64}\n", encoding="utf-8")
    (project / ".devcontainer" / "bin").mkdir()
    for name in ("bin/container-session.mjs", "package.json", "package-lock.json"):
        (project / ".devcontainer" / name).write_text("{}\n", encoding="utf-8")
    # The pinned CLI's own code carries `{{`, and it is installed, not substituted.
    modules = project / ".devcontainer" / "node_modules" / "cli"
    modules.mkdir(parents=True)
    (modules / "index.js").write_text("const t = '{{name}}';\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", "-b", "main", "."], cwd=project, check=True)
    return project


def test_stage_3_finds_the_container_on_apple(tmp_path: Path) -> None:
    project = _substituted_project(tmp_path)
    route = _route(tmp_path)
    running = [{"configuration": {"id": "my-app-dev"}, "status": {"state": "running"}}]
    env = _host(tmp_path, apple="running", running=running)
    result = _run(route / "30-container.sh", env, project)
    assert "my-app-dev is running on Apple container" in result.stdout, result.stdout
    assert "no {{PLACEHOLDER}} survives" in result.stdout
    assert result.returncode == 0, result.stdout


def test_stage_3_waits_for_a_container_apple_has_not_started(tmp_path: Path) -> None:
    project = _substituted_project(tmp_path)
    route = _route(tmp_path)
    stopped = [{"configuration": {"id": "my-app-dev"}, "status": {"state": "stopped"}}]
    env = _host(tmp_path, apple="running", running=stopped)
    result = _run(route / "30-container.sh", env, project)
    assert result.returncode == 2, result.stdout
    assert "no running container for this folder" in result.stdout


def test_stage_3_fails_a_template_older_than_the_launcher(tmp_path: Path) -> None:
    """Reported on Run D: a cache left at 0.1.0 by an install that does not update.

    § 4 copied its template, which has no launcher, and nothing said so until
    § 5's `shell` failed with `Cannot find module`. Contract 39 needs the three
    files on either runtime, so this stage names the gap where it happens.
    """
    project = _substituted_project(tmp_path)
    (project / ".devcontainer" / "bin" / "container-session.mjs").unlink()
    route = _route(tmp_path)
    result = _run(route / "30-container.sh", _host(tmp_path), project)
    assert result.returncode == 1, result.stdout
    assert "the template predates the launcher" in result.stdout
    assert "bin/container-session.mjs" in result.stdout


def test_stage_3_says_when_no_runtime_can_be_asked(tmp_path: Path) -> None:
    project = _substituted_project(tmp_path)
    route = _route(tmp_path)
    result = _run(route / "30-container.sh", _host(tmp_path), project)
    assert "No container runtime is answering" in result.stdout, result.stdout


# --- guided.sh and the template ----------------------------------------------


def test_guided_reads_back_the_words_stage_0_prints() -> None:
    guided = (ADOPT / "guided.sh").read_text(encoding="utf-8")
    assert '"$RUNTIME_APPLE"' in guided
    assert '"$RUNTIME_DOCKER"' in guided


def test_guided_builds_with_the_runtime_it_was_given() -> None:
    guided = (ADOPT / "guided.sh").read_text(encoding="utf-8")
    assert "node .devcontainer/bin/container-session.mjs up" in guided
    assert "devcontainer up --workspace-folder . --remove-existing-container" in guided


def test_the_template_launcher_is_the_tested_one() -> None:
    """ADR 0065: the adopter's copy is held to the tested launcher by being identical."""
    shipped = (TEMPLATE / "bin" / "container-session.mjs").read_bytes()
    tested = (REPO_ROOT / ".devcontainer" / "bin" / "container-session.mjs").read_bytes()
    assert shipped == tested, (
        "the template's container-session.mjs differs from .devcontainer/bin/, which "
        "tests/test_container_session.py tests. Copy the tested one into the template."
    )


def test_the_template_pins_the_cli_this_repository_pins() -> None:
    def pinned(manifest: Path) -> str:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        version: str = data["devDependencies"]["@devcontainers/cli"]
        return version

    def locked(lock: Path) -> str:
        data = json.loads(lock.read_text(encoding="utf-8"))
        entry = data["packages"]["node_modules/@devcontainers/cli"]
        return f"{entry['version']} {entry['integrity']}"

    here = REPO_ROOT / ".devcontainer"
    assert pinned(TEMPLATE / "package.json") == pinned(here / "package.json")
    assert locked(TEMPLATE / "package-lock.json") == locked(here / "package-lock.json")


def test_the_template_ignores_the_installed_cli() -> None:
    ignore = (TEMPLATE / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "node_modules/" in ignore


@pytest.mark.parametrize(
    "command",
    (
        "container system start",
        "npm ci --prefix .devcontainer --no-audit --no-fund",
        "node .devcontainer/bin/container-session.mjs up",
        "node .devcontainer/bin/container-session.mjs shell",
    ),
)
def test_the_guide_gives_the_apple_container_commands(command: str) -> None:
    assert command in GUIDE.read_text(encoding="utf-8"), (
        f"START-HERE.md does not give {command!r}, which the Apple container route needs"
    )


def test_no_test_host_leaks_the_runners_docker(tmp_path: Path) -> None:
    """The PATH these tests build holds no runtime unless a test asks for one."""
    env = _host(tmp_path)
    for runtime in ("docker", "container"):
        assert shutil.which(runtime, path=env["PATH"]) is None
