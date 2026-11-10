"""`ee-skills-submit` hands one write-capable PAT to one command, and nothing else.

The wrapper exists because the incubator's submit scripts call `gh` and
`git push` themselves, so the token has to cover a whole command. It must not
leak into anything else, and it must not shadow with the Eaiger-Ent token.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WRAPPER = REPO_ROOT / ".devcontainer/bin/ee-skills-submit"
FAKE = "not-a-real-token"


def _run(args: list[str], env_extra: dict[str, str]) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if k not in {"GITHUB_TOKEN", "GH_TOKEN"}}
    env.pop("EE_SKILLS_INCUBATOR_AMEND_TOKEN", None)
    env.update(env_extra)
    return subprocess.run(
        [str(WRAPPER), *args], capture_output=True, text=True, env=env, check=False
    )


def test_wrapper_is_executable_and_parses() -> None:
    assert WRAPPER.stat().st_mode & 0o111
    result = subprocess.run(
        ["bash", "-n", str(WRAPPER)], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr


def test_it_refuses_without_the_token() -> None:
    result = _run(["true"], {})
    assert result.returncode == 1
    assert "EE_SKILLS_INCUBATOR_AMEND_TOKEN" in result.stderr


def test_it_refuses_without_a_command() -> None:
    result = _run([], {"EE_SKILLS_INCUBATOR_AMEND_TOKEN": FAKE})
    assert result.returncode == 2


def test_the_command_sees_the_token_as_gh_token_and_not_github_token() -> None:
    result = _run(
        ["sh", "-c", 'printf "%s|%s" "${GH_TOKEN-}" "${GITHUB_TOKEN-unset}"'],
        {"EE_SKILLS_INCUBATOR_AMEND_TOKEN": FAKE, "GITHUB_TOKEN": "eaiger-ent-token"},
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == f"{FAKE}|unset"


def test_it_does_not_read_the_read_only_token() -> None:
    result = _run(
        ["sh", "-c", 'printf "%s" "${GH_TOKEN-}"'],
        {"EE_SKILLS_GITHUB_TOKEN": "read-only", "EE_SKILLS_INCUBATOR_AMEND_TOKEN": FAKE},
    )
    assert result.stdout == FAKE


def test_setup_installs_it_and_fetch_secrets_carries_the_token() -> None:
    setup = (REPO_ROOT / ".devcontainer/setup.sh").read_text(encoding="utf-8")
    fetch = (REPO_ROOT / ".devcontainer/fetch-secrets.sh").read_text(encoding="utf-8")
    assert "bin/ee-skills-submit /usr/local/bin/ee-skills-submit" in setup
    assert 'fetch_secret EE_SKILLS_INCUBATOR_AMEND_TOKEN "EE_SKILLS_INCUBATOR_AMEND_TOKEN"' in fetch
