"""Script-level shell variables are UPPER_SNAKE_CASE, at every locus.

The convention was already what six of seven tracked shell files did. The
seventh was the shipped devcontainer template's `setup.sh`, which spelled its
uv pin `uv_version="..."` — and that file is the one an adopter substitutes a
real version into, so the odd spelling was the one that mattered.

**Why a case convention earns a test at all.** Nothing in the checker cares:
`tool_versions_match_register` matches `re.IGNORECASE` and takes an optional
quote, so `uv_version="0.12.7"` and `UV_VERSION=0.12.7` reconcile identically.
The consumer that cares is **Renovate**, whose custom managers find a version
literal by regex, and a regex has to commit to a character class. This
repository's reads `[A-Z_]+=`, so a lowercase pin is invisible to the bot — the
pin does not drift, it simply never moves, which is the failure ADR 0041 and
`docs/17-adopter-onboarding-review.md` § J both describe.

So the rule is not aesthetic. One spelling is matched by the bot that keeps
these pins current, and the other is silently unmanaged.

**Quotes are deliberately not policed.** They are what `shellcheck` wants, both
checker patterns accept them, and the Renovate patterns were widened to accept
them alongside this. Case is the axis that carries meaning here; quoting is not.

Transient locals — a loop variable, a scratch value — stay lowercase, which is
ordinary shell style and is what `first`, `value` and `installed` already are.
The rule is scoped to assignments in column zero, which is where a script's
configuration lives and where a bot looks for it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from conftest import REPO_ROOT

#: An assignment at the start of a line — a script-level value, not an indented
#: local inside a function or a `case` arm. Renovate's managers read these.
_TOP_LEVEL_ASSIGNMENT = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=", re.MULTILINE)

#: Values a script exports or reads from the environment are named by whoever
#: owns them, and a few are conventionally lowercase.
_EXEMPT = frozenset({"first", "value", "installed"})


def _shell_files() -> list[Path]:
    roots = (
        REPO_ROOT / ".devcontainer",
        REPO_ROOT / "plugins/control-register/templates/devcontainer",
    )
    return sorted(p for root in roots for p in root.glob("*.sh"))


def test_there_are_shell_files_to_check() -> None:
    """A glob that matches nothing passes every test below it."""
    assert _shell_files(), "no shell scripts found — the globs have gone stale"


@pytest.mark.parametrize("path", _shell_files(), ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_script_level_variables_are_upper_snake_case(path: Path) -> None:
    names = set(_TOP_LEVEL_ASSIGNMENT.findall(path.read_text(encoding="utf-8"))) - _EXEMPT
    lower = sorted(n for n in names if n != n.upper())
    assert not lower, (
        f"{path.relative_to(REPO_ROOT)} assigns {', '.join(lower)} at the top level. "
        "Script-level shell variables are UPPER_SNAKE_CASE, because Renovate's custom "
        "managers match `[A-Z_]+=` and a lowercase pin is never proposed for upgrade."
    )


def test_the_template_annotates_its_uv_pin_for_renovate() -> None:
    """A pin no bot can see rots at the version it was adopted at.

    The adopter substitutes a real version into this file, so the annotation has
    to survive the copy — it is the only thing that makes their uv pin
    upgradeable. `docs/17-adopter-onboarding-review.md` § J is what happened
    while it was absent.
    """
    setup = REPO_ROOT / "plugins/control-register/templates/devcontainer/setup.sh"
    text = setup.read_text(encoding="utf-8")
    pin = text.index("UV_VERSION=")
    preceding = text[:pin].rsplit("\n", 2)[-2]
    assert preceding.strip() == "# renovate: datasource=pypi depName=uv", (
        "the template's UV_VERSION pin is not immediately preceded by its "
        f"`# renovate:` annotation (found {preceding.strip()!r})"
    )
