"""Every placeholder the template carries resolves from the register.

`tests/test_devcontainer_template.py` holds the two halves a file test can
decide about the shipped template: that it pins no tool version by hand, and
that BLD-001 and DEV-001 pass against a copy of it. Neither reaches the step
between them. Its `_copied()` helper substitutes `{{PROJECT_NAME}}` and
**leaves the three uv placeholders in**, so nothing there exercises the
substitution at all — and `test_every_placeholder_is_named_in_the_readme`
checks only that the template's own README mentions each name.

What was unverified is the join: that each placeholder has a value in the
register, and that the commands `docs/08-adopting.md` § 2.0 gives for reading
those values still find them. That join has already failed once, and the guide
records it in as many words:

    The first version of these commands used `grep -A4`, which never reached
    `version:` because the register comments that block — so they returned
    empty, `sed` substituted nothing, and the placeholders survived into a
    container that then failed at `sha256sum -c`.

An extraction that quietly yields nothing is worse than one that errors, and
the failure surfaces at container create in someone else's repository. Renaming
`tools.uv.sha256`, or adding a placeholder no register field backs, has the
same shape and the same distance between cause and symptom.

**This is a test rather than a control** for ADR 0022 requirement 6's reason: it
governs the artefact *this* repository ships, not what a conformant repository
contains. An adopter's substituted `setup.sh` is judged by
`tool_versions_match_register`, which is the register's job and already done.

**It does not build anything and cannot.** Whether the substituted values
produce a container that creates is the Phase 6 criterion that needs a Docker
host, with the runbook at `docs/16-marketplace-readoption.md` § Building the
shipped template. This closes the layer below it: the values are there, and the
documented route reaches them.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

from conftest import REPO_ROOT, a_register
from register_check.register import Register

TEMPLATE = REPO_ROOT / "plugins/control-register/templates/devcontainer"
ADOPTING_GUIDE = REPO_ROOT / "docs/08-adopting.md"

#: The same class the sibling test uses. `[A-Z0-9_]` rather than `[A-Z_]`,
#: because the narrower one silently skipped `{{UV_SHA256_X86_64}}` and
#: `{{UV_SHA256_AARCH64}}` — the two placeholders most likely to be left
#: unsubstituted were the two it could not see.
PLACEHOLDER = re.compile(r"\{\{([A-Z0-9_]+)\}\}")

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _uv(register: Register) -> object:
    tool = register.tools.get("uv")
    assert tool is not None, "the register no longer pins uv"
    return tool


def _aarch64_digest(register: Register) -> str | None:
    """The second architecture's digest, from `tools.uv.checksums.also`.

    It lived only in `setup.sh` and was compared by nothing until contract 34
    (ADR 0041). Keyed by asset name rather than by architecture, because the
    asset name is what the release publishes and what `setup.sh` reconstructs.
    """
    tool = register.tools.get("uv")
    if tool is None or tool.checksums is None:
        return None
    for asset, digest in tool.checksums.also.items():
        if "aarch64" in asset:
            return digest
    return None


#: Placeholder to what the register must hold for it, and the shape that value
#: takes. Declared rather than derived from the name: `{{UV_VERSION}}` reading
#: as *the `version` of the tool called `uv`* is a naming convention nobody has
#: written down, and a test that inferred it would pass a template whose
#: placeholder is a typo by inventing a tool to match.
REGISTER_SOURCED: dict[str, tuple[str, Callable[[Register], str | None], re.Pattern[str]]] = {
    "UV_VERSION": (
        "tools.uv.version",
        lambda r: getattr(_uv(r), "version", None),
        SEMVER,
    ),
    "UV_SHA256_X86_64": (
        "tools.uv.sha256",
        lambda r: getattr(_uv(r), "sha256", None),
        SHA256,
    ),
    "UV_SHA256_AARCH64": (
        "tools.uv.checksums.also[…aarch64…]",
        _aarch64_digest,
        SHA256,
    ),
}

#: Placeholders the adopter supplies, which by definition have no register
#: source. Enumerated rather than treated as a fallback: an unrecognised
#: placeholder must fail this test, and a silent "not in the register, so it
#: must be the adopter's" default is exactly the shape that would let a typo
#: through.
ADOPTER_SUPPLIED = {"PROJECT_NAME"}


def _template_placeholders() -> set[str]:
    """Every placeholder in the shipped template, README excluded.

    The README documents the pattern and would therefore match it for ever —
    the reason § 2.0 tells an adopter to delete it *before* running the grep.
    """
    found: set[str] = set()
    for path in TEMPLATE.rglob("*"):
        if path.is_file() and path.name != "README.md":
            found |= set(PLACEHOLDER.findall(path.read_text(encoding="utf-8")))
    return found


def test_the_template_and_the_source_table_agree_in_both_directions() -> None:
    """A placeholder with no source, and a source with no placeholder.

    Both directions, for the reason `tests/test_skill_links.py` gives about the
    ninth skill: a new placeholder added without a register field behind it must
    fail here rather than at `sha256sum -c` in an adopter's container, and a
    source left in this table after its placeholder is deleted is a rule that
    has quietly stopped being about anything.
    """
    found = _template_placeholders()
    declared = set(REGISTER_SOURCED) | ADOPTER_SUPPLIED
    assert found, "the template carries no placeholders at all"
    assert found - declared == set(), f"placeholder with no declared source: {found - declared}"
    assert declared - found == set(), f"declared source with no placeholder: {declared - found}"


@pytest.mark.parametrize("name", sorted(REGISTER_SOURCED))
def test_every_register_sourced_placeholder_has_a_value(name: str) -> None:
    """The field is there, and holds something of the right shape.

    Shape as well as presence, because the failure this guards against is a
    value that reads as present and substitutes to nonsense. A `version:` that
    has become `0.12` still fills the placeholder, and `sha256sum -c` is where
    it is noticed.
    """
    where, resolve, shape = REGISTER_SOURCED[name]
    value = resolve(a_register())
    assert value, f"{{{{{name}}}}} is sourced from {where}, which the register does not hold"
    assert shape.match(value), f"{where} is {value!r}, which is not the shape {{{{{name}}}}} needs"


def _guide_extraction_script() -> str:
    """§ 2.0's own extraction commands, with the two that need the network cut.

    Running the guide's text rather than a re-typing of it is the whole point:
    a reimplementation here would be a second copy of the commands, free to keep
    working after the ones an adopter actually runs have stopped. Same shape as
    `tests/test_conformance_step.py`, which runs the workflow step's own script.

    The aarch64 digest is fetched from the release and is therefore out of reach
    of a test that must not depend on the network — the register's copy of it is
    checked by SUP-004, and the fetch itself by the operator run sheet. What is
    covered here is the pair the register holds.
    """
    text = ADOPTING_GUIDE.read_text(encoding="utf-8")
    blocks = [
        block
        for block in re.findall(r"```bash\n(.*?)```", text, re.DOTALL)
        if "uv_block()" in block
    ]
    assert len(blocks) == 1, (
        f"expected exactly one § 2.0 bash block defining uv_block(), found {len(blocks)}"
    )
    lines = [
        line
        for line in blocks[0].splitlines()
        # `curl` is the network, and `uv_sha_arm` is the variable it sets — the
        # guide's own `echo` dereferences it with `:?`, so dropping one without
        # the other turns this into a test of `set -u`.
        if "curl" not in line and "uv_sha_arm" not in line
    ]
    echo = 'printf "%s\\n%s\\n" "$uv_version" "$uv_sha_x86"'
    return "\n".join(["set -euo pipefail", *lines, echo])


def test_the_guides_own_extraction_commands_still_find_the_values(tmp_path: Path) -> None:
    """§ 2.0, run against the real register.

    The `grep -A4` failure this reproduces returned empty and exited zero, so an
    assertion on the exit code alone would have passed it. The values are
    compared against the register's own, which is the only thing that
    distinguishes *found* from *found something*.
    """
    register = a_register()
    shutil.copy(REPO_ROOT / "controls.yaml", tmp_path / "controls.yaml")
    result = subprocess.run(
        ["bash", "-c", _guide_extraction_script()],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    version, sha_x86 = result.stdout.splitlines()
    assert version == getattr(_uv(register), "version", None), result.stdout
    assert sha_x86 == getattr(_uv(register), "sha256", None), result.stdout


def test_substituting_from_the_register_leaves_no_placeholder(tmp_path: Path) -> None:
    """The end state § 2.0 tells an adopter to check: `grep -rl '{{'` is silent.

    Substituted here from the register rather than from the guide's shell, so
    that this fails when a *value* has gone missing even if the extraction
    commands were also broken — the two tests would otherwise fail together and
    say only that something in the chain moved.
    """
    register = a_register()
    values: dict[str, str] = {}
    for name, (where, resolve, _) in REGISTER_SOURCED.items():
        value = resolve(register)
        assert value is not None, f"{where} is not in the register"
        values[name] = value
    values["PROJECT_NAME"] = "probe-app"

    target = tmp_path / ".devcontainer"
    shutil.copytree(TEMPLATE, target)
    (target / "README.md").unlink()
    for path in target.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for name, value in values.items():
            text = text.replace(f"{{{{{name}}}}}", value)
        path.write_text(text, encoding="utf-8")

    left = [
        str(path.relative_to(target))
        for path in target.rglob("*")
        if path.is_file() and "{{" in path.read_text(encoding="utf-8")
    ]
    assert not left, left

    # And the values landed where `setup.sh` reads them, rather than merely
    # somewhere in the tree. The version is quoted from 2026-08-29, which the
    # register's own assert learned to read at the same time (an upstream
    # `shellcheck-clean` commit quoted the placeholders in the published copy).
    #
    # The name is asserted in UPPER_SNAKE_CASE, and that is load-bearing rather
    # than tidy: Renovate's custom manager matches `[A-Z_]+=`, so a lowercase
    # pin here is one no bot ever proposes an upgrade for. The checker accepts
    # either — `tool_versions_match_register` is case-insensitive — which is
    # exactly why the case needs a test of its own. See
    # `tests/test_shell_conventions.py`.
    setup = (target / "setup.sh").read_text(encoding="utf-8")
    assert f'UV_VERSION="{values["UV_VERSION"]}"' in setup
    assert values["UV_SHA256_X86_64"] in setup
    assert values["UV_SHA256_AARCH64"] in setup
