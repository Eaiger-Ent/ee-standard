"""`renovate.json`'s custom managers match the literals they claim to manage.

§ G of the build plan records the failure this file exists to prevent: the
`# renovate:` annotations were written, were syntactically correct, and were
**inert**, because the bot that reads them was never installed. Nothing in the
repository noticed, because nothing checked.

Installing Renovate fixes the missing bot. It does not fix the missing check —
a manager whose regex matches no line is inert in exactly the same way, and
fails just as quietly. So the annotations, the manager patterns and the
register's own `tools:` table are compared here against each other:

- every annotation in the repository is matched by some manager,
- every match extracts the version the register records, and
- every `source: literal` tool is annotated at every site that pins it.

The regexes are JavaScript-flavoured, as Renovate reads them; the only
translation needed for Python is the named-group spelling.
"""

from __future__ import annotations

import json
import re

from conftest import REPO_ROOT, a_register
from standard_check.asserts_file import _VERSION_SITES

# Files Renovate's custom managers are pointed at. Documentation that merely
# discusses an annotation is not managed and must not be scanned — the prose in
# `04-build-plan.md` describes the mechanism rather than pinning anything.
_MANAGED = ("controls.yaml", ".devcontainer/setup.sh", ".github/workflows/standard-check.yml")

# The annotation may be indented — it sits inside a YAML mapping in the
# register and at column zero in the shell script. The group starts at the `#`
# so a manager pattern can be anchored to it.
_ANNOTATION = re.compile(r"^[ \t]*(?P<hash>#[ \t]*renovate:[ \t]*datasource=)", re.MULTILINE)


def _config() -> dict[str, object]:
    config = json.loads((REPO_ROOT / "renovate.json").read_text(encoding="utf-8"))
    assert isinstance(config, dict), "renovate.json is not a JSON object"
    return config


def _patterns() -> list[re.Pattern[str]]:
    managers = _config()["customManagers"]
    assert isinstance(managers, list)
    return [
        re.compile(str(match_string).replace("(?<", "(?P<"))
        for manager in managers
        if isinstance(manager, dict)
        for match_string in manager.get("matchStrings", [])
    ]


def test_every_annotation_in_the_repository_is_matched_by_a_manager() -> None:
    """No annotation is decorative. This is the § G failure, generalised."""
    patterns = _patterns()
    for relative in _MANAGED:
        text = (REPO_ROOT / relative).read_text(encoding="utf-8")
        for annotation in _ANNOTATION.finditer(text):
            tail = text[annotation.start("hash") :]
            assert any(pattern.match(tail) for pattern in patterns), (
                f"{relative}: {tail.splitlines()[0]!r} is matched by no customManager "
                f"in renovate.json — it would be silently ignored"
            )


def test_every_match_extracts_the_version_the_register_records() -> None:
    """A manager that extracted the wrong value would propose the wrong bump."""
    register = a_register()
    by_dep = {
        "uv": register.tools["uv"],
        "gitleaks/gitleaks": register.tools["gitleaks"],
    }
    patterns = _patterns()
    seen: set[tuple[str, str]] = set()
    for relative in _MANAGED:
        text = (REPO_ROOT / relative).read_text(encoding="utf-8")
        for pattern in patterns:
            for match in pattern.finditer(text):
                dep = match.group("depName")
                assert dep in by_dep, f"{relative}: annotation names unknown dependency {dep!r}"
                assert match.group("currentValue") == by_dep[dep].version, (
                    f"{relative}: manager extracts {match.group('currentValue')} for {dep}, "
                    f"register records {by_dep[dep].version}"
                )
                seen.add((dep, relative))
    assert seen, "no customManager matched anything in this repository"


def test_every_literal_tool_is_annotated_at_the_register_and_at_every_locus() -> None:
    """The register is the authority, so it must be in the same proposal.

    A bump that moved the loci and left `controls.yaml` behind is a bump
    `tool_versions_match_register` rejects; a bump that moved the register and
    left a locus behind is the drift the register exists to stop. Both halves
    have to be annotated for the proposal to be mergeable at all.
    """
    register = a_register()
    literals = {name: tool for name, tool in register.tools.items() if tool.source == "literal"}
    assert literals, "the register pins no literal tools — this test has nothing to guard"

    for name, tool in literals.items():
        assert tool.version is not None
        register_text = (REPO_ROOT / "controls.yaml").read_text(encoding="utf-8")
        assert re.search(
            rf"#[ \t]*renovate:[^\n]*depName=\S*{re.escape(name)}\S*\s+version:\s*"
            rf'"{re.escape(tool.version)}"',
            register_text,
        ), f"controls.yaml: tools.{name} carries no `# renovate:` annotation above its version"

        for site in _VERSION_SITES:
            path = REPO_ROOT / site
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            pins = re.findall(rf"{re.escape(name)}[^\n]*?[@=:\s]v?{re.escape(tool.version)}", text)
            if not pins:
                continue
            assert _ANNOTATION.search(text), (
                f"{site} pins {name} at {tool.version} with no `# renovate:` annotation, "
                "so a proposal would update the register and leave this locus behind"
            )


def test_renovate_is_narrowed_so_the_two_bots_do_not_overlap() -> None:
    """Renovate covers what Dependabot cannot, and nothing Dependabot can.

    Both bots run here. Widening `enabledManagers` would duplicate every
    ecosystem proposal Dependabot already makes; narrowing Dependabot instead
    would mean trusting a bot nobody had confirmed was installed, which is the
    trap § G is about.
    """
    assert _config()["enabledManagers"] == ["custom.regex"]
    dependabot = REPO_ROOT / ".github/dependabot.yml"
    assert dependabot.exists(), (
        "renovate.json manages custom regex literals only, so removing the Dependabot "
        "configuration would leave every package ecosystem unproposed"
    )
