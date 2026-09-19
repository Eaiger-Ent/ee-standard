"""The shipped artefacts, placed as the skill says to place them, in a new repo.

S5's exit criterion is that a clean repository of each stack reaches a working,
pinned configuration in one run, and that a second run changes nothing. This is
the mechanical half of it: the bytes `plugins/craft/profiles/` ships, written
into a repository that has nothing, and then written again.

**The harness is not a second installer**, and the distinction matters because
it could become one. `plugins/craft/skills/craft-install/SKILL.md` is the source
for how a region is placed; what is encoded below is those rules, so that
something checks that the shipped artefacts *compose* into a repository whose
linter runs. If the two ever disagree, the skill is right and this is wrong —
and the alternative to keeping it is that nobody finds out a published region
does not parse until an adopter does.

The conversational half — inference, presentation, the yes — is not here. It is
prose a model follows, `tests/test_craft_plugin.py` holds the three rules that
govern it, and S6 is where it meets a team.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts"))

from craft_publish import PLUGIN

RUFF = shutil.which("ruff") or str(Path(sys.executable).parent / "ruff")

PYPROJECT = """\
[project]
name = "ledger"
version = "0.1.0"
requires-python = ">=3.14"
"""

SOURCE = """\
import os


def total(items, rate=[]):
    path = os.path.join("a", "b")
    assert items
    return path
"""


def _place(repo: Path, profile: str) -> list[str]:
    """Write a profile's artefacts the way `SKILL.md` Step 4 says to.

    The Python region is a sequence of table headers and marked spans. In a
    repository with none of those tables — which is what a new repository is —
    placement is an append, and the header comes with the span.
    """
    slug = profile.replace("/", "-")
    written = []
    region = (PLUGIN / f"profiles/{slug}/pyproject-region.toml").read_text(encoding="utf-8")
    target = repo / "pyproject.toml"
    body = target.read_text(encoding="utf-8")
    if "ee-craft" in body:
        head, _, _ = body.partition("[tool.ruff]")
        body = head
    target.write_text(body.rstrip("\n") + "\n\n" + region, encoding="utf-8")
    written.append("pyproject.toml")

    nested = PLUGIN / f"profiles/{slug}/src-ruff.toml"
    if nested.is_file():
        (repo / "src").mkdir(exist_ok=True)
        (repo / "src/ruff.toml").write_text(nested.read_text(encoding="utf-8"), encoding="utf-8")
        written.append("src/ruff.toml")
    return written


def _ruff(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [RUFF, "check", "--no-cache", "--output-format", "concise", *args],
        cwd=repo,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src/ledger.py").write_text(SOURCE, encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/test_ledger.py").write_text(
        "def test_it():\n    assert True\n", encoding="utf-8"
    )
    return tmp_path


@pytest.mark.parametrize("profile", ["python/standard", "python/strict"])
def test_a_clean_repository_reaches_a_configuration_ruff_resolves(
    repo: Path, profile: str
) -> None:
    """The bytes compose. A region that does not parse fails here, not at an adopter.

    Findings are the point rather than a problem: this is a new repository with
    a deliberately poor module in it, and the profile is what reports on it. A
    configuration error is what would fail — ruff exits 2 and says so.
    """
    _place(repo, profile)
    result = _ruff(repo, "src", "tests")
    assert result.returncode == 1, result.stderr or result.stdout
    assert "error:" not in result.stderr.lower(), result.stderr
    assert result.stdout.count("\n") >= 5, result.stdout


def test_the_source_scope_reaches_the_source_and_not_the_tests(repo: Path) -> None:
    """The nested configuration, doing the thing it exists for.

    `S101` is selected for the package source and not for tests, which is the
    register's resolution rather than a convenience: `per-file-ignores` is the
    exemption it rejected, and a nested configuration is the only other way ruff
    can express a scope.
    """
    _place(repo, "python/strict")
    findings = _ruff(repo, "src", "tests").stdout
    assert "src/ledger.py" in findings
    asserts = [line for line in findings.splitlines() if "assert:" in line]
    assert asserts and all(line.startswith("src/") for line in asserts), findings


@pytest.mark.parametrize("profile", ["python/standard", "python/strict"])
def test_a_second_run_over_its_own_output_changes_nothing(repo: Path, profile: str) -> None:
    """S5's exit criterion, on the half a test can hold.

    The skill compares the file against the shipped artefact byte-for-byte
    inside the markers; this places twice and compares the whole file, which is
    the stronger claim of the two.
    """
    _place(repo, profile)
    after_first = {
        path: (repo / path).read_text(encoding="utf-8")
        for path in ("pyproject.toml", "src/ruff.toml")
        if (repo / path).is_file()
    }
    _place(repo, profile)
    for path, body in after_first.items():
        assert (repo / path).read_text(encoding="utf-8") == body, path


def test_the_region_keeps_what_the_repository_already_had(repo: Path) -> None:
    """Craft writes its span and touches nothing else.

    The `[project]` table is the repository's, and a placement that rewrote the
    file rather than appending to it would take it. This is the narrow version
    of the rule that stops the installer clobbering a person's configuration.
    """
    _place(repo, "python/standard")
    body = (repo / "pyproject.toml").read_text(encoding="utf-8")
    assert body.startswith(PYPROJECT.rstrip("\n"))
    assert 'name = "ledger"' in body


def test_what_was_installed_can_be_read_back_off_the_repository(repo: Path) -> None:
    """The stamp answers *whose rule is this* at a failing build.

    A developer who hits `PLR0915` has the code and nothing else. The stamp is
    what turns that into a profile, a version and a place to ask.
    """
    _place(repo, "python/strict")
    body = (repo / "pyproject.toml").read_text(encoding="utf-8")
    version = json.loads((PLUGIN / "profiles/manifest.json").read_text(encoding="utf-8"))[
        "profiles"
    ]["python/strict"]["version"]
    assert f"# ee-craft: python/strict@{version}" in body


#: The one tree on this machine with the six plugins resolved. It is
#: `scripts/craft_scaffold.py`'s output plus an `npm install`, gitignored like
#: everything else under `temp/`, and absent in CI — so this skips there and
#: says why, rather than reporting a pass nobody ran.
BENCH = REPO_ROOT / "temp/craft-bench/react"


@pytest.mark.parametrize("profile", ["react/standard", "react/strict"])
def test_the_react_config_resolves_where_the_plugins_exist(profile: str) -> None:
    """ESLint loads what Craft publishes, and enables what the manifest claims.

    The flat config is written whole, so *does it load* is the whole of its
    placement — and a config that imports a plugin the tree does not have fails
    at load with an error about a module, not about the code.
    """
    if not (BENCH / "node_modules").is_dir():
        pytest.skip(
            "no node_modules with the six plugins: run scripts/craft_scaffold.py "
            "and `npm install` in temp/craft-bench/react to exercise this"
        )
    slug = profile.replace("/", "-")
    published = (PLUGIN / f"profiles/{slug}/eslint.config.mjs").read_text(encoding="utf-8")
    # Inside the tree, not in `tmp_path`: a flat config's bare imports resolve
    # from the **config file's own directory**, so a config anywhere else cannot
    # find the plugins however it is invoked. That is also why the real install
    # writes the config at the repository root and nowhere else.
    config = BENCH / "craft-dry-run.config.mjs"
    config.write_text(published, encoding="utf-8")

    def enabled(target: str) -> set[str]:
        result = subprocess.run(
            ["npx", "eslint", "--config", str(config), "--print-config", target],
            cwd=BENCH,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr[-2000:]
        return {
            rule
            for rule, setting in json.loads(result.stdout)["rules"].items()
            if (setting[0] if isinstance(setting, list) else setting) not in (0, "off")
        }

    try:
        component = enabled("src/components/Basket.tsx")
        test = enabled("src/components/Basket.test.tsx")
    finally:
        config.unlink()

    named = {
        line.split("'")[1]
        for line in published.splitlines()
        if line.strip().startswith("'") and "': 'error'" in line
    }
    assert named <= component | test, sorted(named - (component | test))
    assert len(component) > len(named), "the preset bases are not contributing anything"

    # The scope, seen from the tool rather than from the file that asked for it.
    scoped = {rule for rule in named if rule.startswith("testing-library/")}
    assert scoped <= test and not scoped & component, sorted(scoped & component)
