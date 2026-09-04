"""A volume at `~/.claude` does not keep you signed in on its own.

Claude Code writes its OAuth *account* record to `~/.claude.json` — a sibling of
`~/.claude`, not a file inside it. So a devcontainer that mounts a named volume
at `~/.claude` and stops there discards that record on every rebuild, and the
engineer meets the login menu again. Anthropic's own guidance is to set
`CLAUDE_CONFIG_DIR` to the same path so the file lands in the volume:
<https://code.claude.com/docs/en/devcontainer>.

Found the way these things are found: an adopter set the Keychain token, built
the container, ran `claude`, and was asked to choose a login method.

The two facts are in different keys of the same file and nothing but this test
holds them together — mount without the variable and the volume is decoration.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from conftest import REPO_ROOT

#: Every devcontainer this repository owns: its own, and the one it ships.
_DEVCONTAINERS = (
    ".devcontainer/devcontainer.json",
    "plugins/control-register/templates/devcontainer/devcontainer.json",
)

_LINE_COMMENT = re.compile(r"^\s*//.*$", re.M)


def _load(path: Path) -> dict[str, object]:
    """devcontainer.json is JSON with comments, and both of ours use them."""
    parsed: dict[str, object] = json.loads(
        _LINE_COMMENT.sub("", path.read_text(encoding="utf-8"))
    )
    return parsed


@pytest.mark.parametrize("relative", _DEVCONTAINERS)
def test_a_claude_volume_carries_the_config_dir_with_it(relative: str) -> None:
    config = _load(REPO_ROOT / relative)

    mounts = config.get("mounts", [])
    assert isinstance(mounts, list)

    targets = [
        part.removeprefix("target=")
        for mount in mounts
        if isinstance(mount, str)
        for part in mount.split(",")
        if part.startswith("target=") and part.endswith("/.claude")
    ]
    if not targets:
        pytest.skip(f"{relative} mounts no volume at ~/.claude")

    container_env = config.get("containerEnv", {})
    assert isinstance(container_env, dict), f"{relative} has no containerEnv"

    declared = container_env.get("CLAUDE_CONFIG_DIR")
    assert declared == targets[0], (
        f"{relative} mounts a volume at {targets[0]} but sets CLAUDE_CONFIG_DIR to "
        f"{declared!r}. Claude Code keeps its OAuth account in ~/.claude.json, a "
        "sibling of that directory rather than a file in it, so without the variable "
        "the record stays in the ephemeral home and every rebuild ends at the login "
        "menu. The volume is decoration until the two agree."
    )
