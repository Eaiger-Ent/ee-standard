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


def _managed() -> tuple[str, ...]:
    """Files Renovate's custom managers are pointed at, from the register.

    Documentation that merely discusses an annotation is not managed and must
    not be scanned — the prose in `04-build-plan.md` describes the mechanism
    rather than pinning anything.

    Derived from `tools.<tool>.pinned_at` plus the register itself, rather than
    listed here. It was a third copy of the same list — the checker had one, the
    register's loci were another — and a copy is what let a renamed workflow
    drop out of comparison unnoticed (§ H2). Now adding a locus to the register
    is what puts it under this test.
    """
    register = a_register()
    sites = {site for tool in register.tools.values() for site in tool.pinned_at}
    return ("controls.yaml", *sorted(sites))

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


def _pins(text: str, name: str, version: str) -> bool:
    """Whether this file pins this tool.

    Name and version are looked for independently rather than adjacently. The
    register spells the pin across two lines (`uv:` then `version: "0.12.5"`),
    a workflow spells it `uv==0.12.5`, and a shell script spells it
    `GITLEAKS_VERSION=8.30.1` — an adjacency regex has to be wrong about at
    least one of those, and being wrong here means under-counting the sites that
    need managing, which is the hole this file exists to close.
    """
    return bool(re.search(re.escape(name), text, re.IGNORECASE)) and version in text


def test_every_annotation_in_the_repository_is_matched_by_a_manager() -> None:
    """No annotation is decorative. This is the § G failure, generalised."""
    patterns = _patterns()
    for relative in _managed():
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
    for relative in _managed():
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

    This test used to ask only whether a *file* carried some annotation, and
    passed while `.devcontainer/setup.sh` annotated `uv` and not `gitleaks` —
    the file had an annotation, just not the one that mattered. Renovate's own
    dashboard found it, by listing five managed sites where the register implies
    six. It now asks per tool and per site, which is what Renovate actually
    requires: the annotation must sit immediately above the pin it manages.
    """
    register = a_register()
    literals = {name: tool for name, tool in register.tools.items() if tool.source == "literal"}
    assert literals, "the register pins no literal tools — this test has nothing to guard"
    patterns = _patterns()

    for name, tool in literals.items():
        assert tool.version is not None
        for relative in _managed():
            text = (REPO_ROOT / relative).read_text(encoding="utf-8")
            if not _pins(text, name, tool.version):
                continue
            managed = any(
                match.group("depName").split("/")[-1] == name
                for pattern in patterns
                for match in pattern.finditer(text)
            )
            assert managed, (
                f"{relative} pins {name} at {tool.version}, and no customManager in "
                f"renovate.json matches it — a proposal would bump the other sites and "
                f"leave this one behind, which `tool_versions_match_register` then rejects"
            )


def test_the_manager_count_matches_the_sites_the_register_implies() -> None:
    """Five detected sites where the register implies six is a hole, not a detail.

    Renovate's Dependency Dashboard reports how many sites its custom managers
    matched. That number is the only external check on whether the annotations
    are doing anything, so the same number is derived here from the register and
    compared — otherwise the next missing annotation is found the same way this
    one was, which is to say by luck.
    """
    register = a_register()
    literals = {name: tool for name, tool in register.tools.items() if tool.source == "literal"}
    patterns = _patterns()

    expected = 0
    for name, tool in literals.items():
        assert tool.version is not None
        for relative in _managed():
            text = (REPO_ROOT / relative).read_text(encoding="utf-8")
            if _pins(text, name, tool.version):
                expected += 1

    matched = sum(
        1
        for relative in _managed()
        for pattern in patterns
        for _ in pattern.finditer((REPO_ROOT / relative).read_text(encoding="utf-8"))
    )
    assert matched == expected, (
        f"renovate.json's managers match {matched} sites; the register's literal tools are "
        f"pinned at {expected}. Renovate's Dependency Dashboard reports the former — the "
        f"difference is the set of pins no bot will ever update"
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
