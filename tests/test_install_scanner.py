"""`gate-secrets`' scanner installer fetches the build for the processor it runs on.

Found on Phase 15 Run D. Until plugin 0.6.3 `install-scanner.sh` always fetched
`<tool>_<version>_linux_x64.tar.gz` and checked it against the x64 checksum, so
on an Apple silicon container the check passed and the binary it installed
could not run there. The adopter's session noticed and installed the arm64
build by hand; the register already recorded that build's checksum.

`curl`, `uname` and `sudo` are stubs on `PATH`, so nothing is downloaded or
installed: what is checked is which archive the script asks for, and that it
holds that archive to that archive's checksum.
"""

from __future__ import annotations

import functools
import hashlib
import io
import os
import subprocess
import tarfile
from pathlib import Path

import pytest

from conftest import REPO_ROOT

SCRIPT = REPO_ROOT / "plugins/control-register/skills/gate-secrets/scripts/install-scanner.sh"


@functools.cache  # gzip stamps the time, so one archive serves the whole module
def _archive(tool: str) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        payload = b"#!/bin/sh\n"
        info = tarfile.TarInfo(tool)
        info.size = len(payload)
        info.mode = 0o755
        archive.addfile(info, io.BytesIO(payload))
    return buffer.getvalue()


def _stub(bin_dir: Path, name: str, body: str) -> None:
    path = bin_dir / name
    path.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
    path.chmod(0o755)


def _run(tmp_path: Path, machine: str, x64_sha: str, arm64_sha: str) -> tuple[int, str, str]:
    archive = tmp_path / "scanner.tgz"
    archive.write_bytes(_archive("gitleaks"))
    requested = tmp_path / "requested"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    # curl -sSfL -o <file> <url>: record the URL, hand back the archive.
    _stub(bin_dir, "curl", f'echo "$4" > "{requested}"; cp "{archive}" "$3"')
    _stub(bin_dir, "uname", f"echo {machine}")
    _stub(bin_dir, "sudo", "exit 0")
    env = {**os.environ, "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}"}
    result = subprocess.run(
        ["bash", str(SCRIPT), "gitleaks", "gitleaks/gitleaks", "8.30.1", x64_sha, arm64_sha],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    url = requested.read_text(encoding="utf-8").strip() if requested.exists() else ""
    return result.returncode, url, result.stdout + result.stderr


def _digest() -> str:
    return hashlib.sha256(_archive("gitleaks")).hexdigest()


@pytest.mark.parametrize(
    ("machine", "arch"),
    [("x86_64", "x64"), ("aarch64", "arm64"), ("arm64", "arm64")],
)
def test_it_fetches_and_verifies_the_build_for_this_processor(
    tmp_path: Path, machine: str, arch: str
) -> None:
    good, wrong = _digest(), "0" * 64
    x64, arm64 = (good, wrong) if arch == "x64" else (wrong, good)
    code, url, output = _run(tmp_path, machine, x64, arm64)
    assert url.endswith(f"/v8.30.1/gitleaks_8.30.1_linux_{arch}.tar.gz"), url
    assert code == 0, output
    assert f"({arch})" in output


def test_the_other_processors_checksum_is_refused(tmp_path: Path) -> None:
    """The Run D failure, inverted: an arm64 machine never accepts the x64 digest."""
    code, _, output = _run(tmp_path, "aarch64", _digest(), "0" * 64)
    assert code == 1, output
    assert "does not match" in output


def test_an_unknown_processor_installs_nothing(tmp_path: Path) -> None:
    code, url, output = _run(tmp_path, "riscv64", _digest(), _digest())
    assert code == 1, output
    assert url == "", "it downloaded something for a processor the register records no build for"


def test_the_skill_passes_the_arm64_checksum() -> None:
    skill = (SCRIPT.parent.parent / "SKILL.md").read_text(encoding="utf-8")
    assert '"$TOOL_SHA256" "$TOOL_SHA256_ARM64"' in skill
    assert "`TOOL_SHA256_ARM64` |" in skill
