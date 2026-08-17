"""Every `ee-control:` stamp in this repository is well-formed.

`docs/00-concepts.md` § The provenance stamp makes "deployed but stale"
computable. It was not computable here: three of the four `lint-md`-deployed
artefacts carried no stamp at all, and the one that did read `register: v0.1.0`
against a register four versions further on, while `CLAUDE.md` stated as fact
that they all carried one (§ F).

What is checked here is **well-formedness**, deliberately, and not currency. A
stale stamp is a recommendation to redeploy — "notify, never redeploy" — so a
test that failed the build on one would be enforcing redeployment, which is the
behaviour this design rules out. A stamp that does not parse, or that names a
control the register does not define, or that claims a contract the register has
not reached, is a defect in the deployment rather than a staleness signal, and
those are what fail here.

Reporting the stale-but-valid case is Phase 5's sweep.
"""

from __future__ import annotations

import re
import subprocess

import pytest

from conftest import REPO_ROOT, a_register

_STAMP = re.compile(
    r"ee-control:\s*(?P<control>\S+)\s+"
    r"ee-skill:\s*(?P<skill>\S+)\s+"
    r"register:\s*v(?P<version>\d+\.\d+\.\d+)\s+"
    r"register-contract:\s*(?P<contract>\d+)"
)


def _stamped_files() -> list[str]:
    """Tracked files containing the marker, however the stamp is spelled.

    Searching for the bare marker rather than the full pattern is the point: a
    stamp that is present but malformed must be found and failed, not missed.
    """
    found = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "grep", "-l", "ee-control:"],
        capture_output=True,
        text=True,
        check=False,
    )
    # Prose that defines or discusses the format is not a deployed artefact. No
    # document is, so the whole of `docs/` is out along with the two files that
    # quote the marker: this repository's guide, and this test.
    excluded = ("docs/", "CLAUDE.md", "tests/test_provenance_stamps.py")
    return [p for p in found.stdout.split() if not p.startswith(excluded)]


def test_the_deployed_artefacts_are_the_ones_that_carry_stamps() -> None:
    """All five `lint-md` artefacts, where only one used to be stamped.

    § F counted four. The fifth, `.claude/hooks/md-lint.py`, was invisible to
    that count because it sat behind a ruff exclusion — which is the same
    exclusion that hid eleven LNT-001 violations in it.
    """
    assert set(_stamped_files()) == {
        ".markdownlint.yaml",
        ".markdownlint-cli2.yaml",
        ".pre-commit-config.yaml",
        ".github/workflows/lint.yml",
        ".claude/hooks/md-lint.py",
    }


@pytest.mark.parametrize("path", _stamped_files())
def test_stamp_is_well_formed_and_names_a_real_control(path: str) -> None:
    text = (REPO_ROOT / path).read_text(encoding="utf-8")
    stamp = _STAMP.search(text)
    assert stamp is not None, (
        f"{path} carries an `ee-control:` marker that does not parse as a stamp — "
        "expected `ee-control: ID  ee-skill: name@version  register: vX.Y.Z  "
        "register-contract: N` (docs/00-concepts.md)"
    )

    register = a_register()
    known = {control.id for control in register.controls} | {
        control.id for control in register.meta_controls
    }
    assert stamp.group("control") in known, (
        f"{path}: stamp names {stamp.group('control')}, which the register does not define"
    )

    # Ahead of the register is a defect; behind it is staleness, which is
    # reported rather than failed.
    assert int(stamp.group("contract")) <= register.register_contract, (
        f"{path}: stamp claims register contract {stamp.group('contract')}, "
        f"but the register is at {register.register_contract}"
    )
