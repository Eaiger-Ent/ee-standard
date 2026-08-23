"""The interpreter's authority is a file, and the assert reads it (ADR 0027).

The failure this covers had no second copy to catch. `requires-python` was a
floor, a floor selects nothing, and the two loci resolved independently — the
devcontainer on 3.13.15 and CI on 3.14.7, from the same three files. So these
cases are about the two silences that would put it back: a toolchain file the
register names and git does not track, and one that is tracked and names no
version. Both leave every locus resolving exactly as it did before, which is
why neither can be allowed to read as agreement.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from conftest import a_register, make_repo, register_with
from standard_check.asserts_file import tool_versions_match_register, toolchain_version


def _only_python(toolchain: str = ".python-version") -> Any:
    """A register whose whole `tools:` table is the interpreter.

    Narrowed for the same reason `_only_gitleaks` is in `test_section_h`: with
    the other tools left in, every verdict would also carry their absence from a
    fixture repository that was never meant to have them.
    """

    def mutate(document: dict[str, Any]) -> None:
        document["tools"] = {
            "python": {
                "source": "toolchain",
                "toolchain": toolchain,
                "invocation": "uv run",
            }
        }

    return mutate


def test_an_untracked_toolchain_file_is_a_failure(tmp_path: Path) -> None:
    """Untracked is worse than drifted: every locus falls back to what it would
    have resolved anyway, which is the state the ADR was written from.
    """
    register = register_with(tmp_path, _only_python())
    repo = make_repo(tmp_path / "repo", {"README.md": "# x\n"})
    result = tool_versions_match_register(repo, register, {})
    assert not result.passed
    assert ".python-version" in result.message
    assert "not tracked" in result.message


def test_a_toolchain_file_naming_no_version_is_a_failure(tmp_path: Path) -> None:
    """The same silence one level down — the file is there and the value is not."""
    register = register_with(tmp_path, _only_python())
    repo = make_repo(tmp_path / "repo", {".python-version": "# the interpreter, one day\n"})
    result = tool_versions_match_register(repo, register, {})
    assert not result.passed
    assert "names no version" in result.message


def test_a_tracked_toolchain_file_naming_a_version_passes(tmp_path: Path) -> None:
    register = register_with(tmp_path, _only_python())
    repo = make_repo(tmp_path / "repo", {".python-version": "3.13\n"})
    result = tool_versions_match_register(repo, register, {})
    assert result.passed, result.message


def test_the_file_comes_from_the_register_not_the_checker(tmp_path: Path) -> None:
    """`.python-version` is uv's spelling, not the standard's. A repository on
    another toolchain manager names its own file, and only the register moves.
    """
    register = register_with(tmp_path, _only_python(toolchain=".tool-versions"))
    repo = make_repo(tmp_path / "repo", {".tool-versions": "3.13\n"})
    result = tool_versions_match_register(repo, register, {})
    assert result.passed, result.message


def test_this_repository_pins_its_interpreter(tmp_path: Path) -> None:
    """The register records the interpreter at all — the gap ADR 0027 closed."""
    register = a_register()
    python = register.tools.get("python")
    assert python is not None, "the interpreter is not in `tools:`"
    assert python.source == "toolchain"
    assert python.toolchain == ".python-version"
    assert python.version is None, "the file is the authority; a copy here would drift from it"


def test_comments_do_not_answer_for_the_version() -> None:
    """The annotation a bot reads lives in a comment, and `# renovate: … 3.14`
    must not be mistaken for the pin — it names a datasource, not a value.
    """
    annotated = "# renovate: datasource=python-version depName=python\n3.13\n"
    assert toolchain_version(annotated) == "3.13"
    assert toolchain_version("#3.14\n") is None
    assert toolchain_version("3.13\n") == "3.13"
