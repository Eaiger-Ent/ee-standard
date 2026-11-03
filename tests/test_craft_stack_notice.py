"""Craft's SessionStart notice: a stack that arrives after the install is reported.

The trial found React arriving three weeks after `craft-install` ran, with
nothing saying so (`docs/craft/review.trial.md` § React arrived, and Craft did
not notice). The hook asks the assistant to check, every session, and does not
check itself: Craft's stack conditions are a sentence `craft-install`
implements, and a shell copy of them would be a second implementation. So these
tests hold the hook to the three things it does own: silence where nothing was
installed, the pin carried verbatim, and a pointer that still resolves.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from conftest import REPO_ROOT

PLUGIN = REPO_ROOT / "plugins/craft"
SCRIPT = PLUGIN / "hooks/stack-notice.sh"
SKILL = PLUGIN / "skills/craft-install/SKILL.md"

#: The heading the notice tells the assistant to apply. If `craft-install`
#: renames it, the notice points at nothing, and this is what says so.
TABLE = "Read the repository, and never a self-declaration"


def _notice(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT)],
        cwd=root,
        env={"PATH": "/usr/bin:/bin", "CLAUDE_PLUGIN_ROOT": str(PLUGIN)},
        capture_output=True,
        text=True,
        check=False,
    )


def _config(root: Path, text: str) -> None:
    (root / ".claude").mkdir(parents=True, exist_ok=True)
    (root / ".claude/skill-config.yaml").write_text(text, encoding="utf-8")


@pytest.mark.parametrize(
    "config",
    [None, "lint-md:\n  ignores: []\n"],
    ids=["no-config-file", "no-craft-install-key"],
)
def test_a_repository_that_never_installed_craft_hears_nothing(
    tmp_path: Path, config: str | None
) -> None:
    if config is not None:
        _config(tmp_path, config)
    result = _notice(tmp_path)
    assert result.returncode == 0
    assert result.stdout == ""


def test_the_pin_is_carried_verbatim_and_stops_at_the_next_key(tmp_path: Path) -> None:
    _config(
        tmp_path,
        "lint-md:\n  ignores: []\n"
        "craft-install:\n  profiles:\n    python/strict: 3\n  residue: CLAUDE.md\n"
        "lint-yaml:\n  invocation: uv run yamllint\n",
    )
    result = _notice(tmp_path)
    assert result.returncode == 0
    assert (
        "craft-install:\n  profiles:\n    python/strict: 3\n  residue: CLAUDE.md" in result.stdout
    )
    assert "lint-yaml" not in result.stdout
    assert "lint-md" not in result.stdout
    assert "/craft-install" in result.stdout


def test_the_notice_points_at_a_table_the_skill_still_has(tmp_path: Path) -> None:
    _config(tmp_path, "craft-install:\n  profiles:\n    react/standard: 4\n")
    out = _notice(tmp_path).stdout
    assert TABLE in out
    assert str(SKILL) in out
    assert TABLE in SKILL.read_text(encoding="utf-8")


def test_the_hook_evaluates_no_stack_condition_itself() -> None:
    """A stack condition spelled here would be the second copy the design refuses."""
    body = SCRIPT.read_text(encoding="utf-8")
    code = "\n".join(line for line in body.splitlines() if not line.lstrip().startswith("#"))
    for fact in ("package.json", "pyproject.toml", "tsconfig.json", "react"):
        assert fact not in code, f"stack-notice.sh reads {fact!r}: craft-install's table owns that"


def test_the_plugin_runs_the_script_at_session_start() -> None:
    hooks = json.loads((PLUGIN / "hooks/hooks.json").read_text(encoding="utf-8"))
    commands = [
        hook["command"] for group in hooks["hooks"]["SessionStart"] for hook in group["hooks"]
    ]
    assert commands == ['bash "${CLAUDE_PLUGIN_ROOT}/hooks/stack-notice.sh"']
