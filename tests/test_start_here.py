"""`START-HERE.md` stays runnable, and stays free of values it does not own.

The quickstart's whole value is that a junior can paste its blocks and have them
work. That makes it the same class of artefact as `docs/08-adopting.md` § 2.0,
and it earns the same treatment: the commands are **executed** here rather than
reimplemented, because a reimplementation is a second copy free to keep working
after the documented ones have stopped.

`docs/17-adopter-onboarding-review.md` § E is why the extraction check comes
first — a `grep -A4` that returned empty and exited zero survived for months in
a shipped file, and an assertion on the exit code alone would have passed it.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

from conftest import REPO_ROOT, a_register

START_HERE = REPO_ROOT / "START-HERE.md"
HOW_IT_WORKS = REPO_ROOT / "HOW-IT-WORKS.md"
TEXT = START_HERE.read_text(encoding="utf-8")

_FENCED_BASH = re.compile(r"```bash\n(.*?)```", re.DOTALL)
_TABLE_ROW = re.compile(r"^\|(?!\s*[-: ]+\|)(.+)\|\s*$", re.MULTILINE)

#: A literal this document must not carry. The register owns every one of them,
#: and `tests/test_plugin.py` holds the same rule for `plugins/`.
_VERSION_LITERAL = re.compile(r"\b\d+\.\d+\.\d+\b")
_DIGEST_LITERAL = re.compile(r"\b[0-9a-f]{64}\b")


def test_both_root_documents_exist_and_link_each_other() -> None:
    """Neither is reachable without the other: one routes, one explains."""
    assert START_HERE.is_file() and HOW_IT_WORKS.is_file()
    assert "HOW-IT-WORKS.md" in TEXT, "START-HERE.md does not link the explanation"
    assert "START-HERE.md" in HOW_IT_WORKS.read_text(encoding="utf-8"), (
        "HOW-IT-WORKS.md does not route a reader who wants to adopt"
    )


def test_the_register_extraction_still_finds_its_values(tmp_path: Path) -> None:
    """Step 4's own commands, run against the real register.

    The network lines are cut the way `tests/test_devcontainer_placeholders.py`
    cuts them — the aarch64 digest is fetched from the release, and the pair the
    register holds is what a file test can settle.
    """
    blocks = [b for b in _FENCED_BASH.findall(TEXT) if "uv_block()" in b]
    assert len(blocks) == 1, f"expected one block defining uv_block(), found {len(blocks)}"
    lines = [
        line
        for line in blocks[0].splitlines()
        # The aarch64 digest is fetched from the release; a file test must not
        # depend on the network. Its `echo` dereferences the variable with `:?`,
        # so the line that sets it and the line that reads it go together.
        if "curl" not in line and "uv_sha_arm" not in line
    ]
    script = "\n".join(
        ["set -euo pipefail", *lines, 'printf "%s\\n%s\\n" "$uv_version" "$uv_sha_x86"']
    )
    shutil.copy(REPO_ROOT / "controls.yaml", tmp_path / "controls.yaml")
    result = subprocess.run(
        ["bash", "-c", script], cwd=tmp_path, capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    version, sha = result.stdout.splitlines()
    uv = a_register().tools["uv"]
    assert version == uv.version, f"extracted {version!r}, register holds {uv.version!r}"
    assert sha == uv.sha256, "the extracted x86_64 digest is not the register's"


def test_no_block_reaches_the_checker_off_path() -> None:
    """ADR 0020, held for this file as `test_adopter_guide.py` holds it for the guide.

    A bare `register-check` resolves against `PATH` and would report success
    against some other copy entirely — the exact failure this standard describes
    for `npx --no-install`.
    """
    offenders = [
        line.strip()
        for block in _FENCED_BASH.findall(TEXT)
        for line in block.splitlines()
        if re.match(r"^\s*register-check\b", line)
    ]
    assert not offenders, f"reaches the checker off PATH: {offenders}"


def test_every_prerequisite_row_has_an_install_and_a_check() -> None:
    """A blank cell is how the gap this document exists to close happened.

    `docs/17-adopter-onboarding-review.md` § A: the route named seven tools and
    gave an install command for none of them.
    """
    section = TEXT.split("### Install these", 1)[1].split("###", 1)[0]
    rows = [
        [c.strip() for c in row.split("|")]
        for row in _TABLE_ROW.findall(section)
    ]
    body = [r for r in rows if r and r[0] not in ("Tool", "")]
    assert len(body) >= 5, f"the prerequisites table has only {len(body)} rows"
    for row in body:
        tool, install, check = row[0], row[1], row[2]
        assert install, f"{tool} has no install cell"
        assert check, f"{tool} has no verification cell"


@pytest.mark.parametrize(
    ("pattern", "what"),
    [(_VERSION_LITERAL, "a version"), (_DIGEST_LITERAL, "a digest")],
)
def test_the_document_owns_no_value_another_file_owns(pattern: re.Pattern[str], what: str) -> None:
    """Rule 3 of the template: derive it or link to it, never copy it.

    The memory figure is deliberately exempt — 8 GB is a Docker Desktop setting
    this document is entitled to state, not a value the register pins.
    """
    hits = {m.group(0) for m in pattern.finditer(TEXT)}
    hits -= {"0.0", "1.1", "2.0", "4.2", "4.3"}  # section references
    assert not hits, f"START-HERE.md carries {what} it does not own: {sorted(hits)}"
