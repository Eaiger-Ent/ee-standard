"""The routed adoption scripts detect; `START-HERE.md` instructs.

`plugins/control-register/templates/adopt/` ships a chain of scripts an adopter
runs on their own machine. Each one reads state and prints the next script to
run, so the *order* of the adoption is executable rather than remembered.

**What they must never do is repeat an instruction.** A script that says
`brew install uv` is a second copy of § B, free to drift from it — the failure
this repository exists to prevent (theme T-2), and one it has already paid for
in `CLAUDE.md`. So a failing check prints the section that explains the fix and
nothing more, and this file holds the scripts to that:

* every section a script names resolves to a heading in `START-HERE.md`, so a
  renamed section fails the build instead of routing a reader nowhere;
* no *detector* restates a command the document already carries — `guided.sh`
  is the one exception, because acting is what it is for, and it is held to a
  different rule: it may not implement a check of its own;
* the route in `_lib.sh` and the files on disk agree, both ways, so a stage
  cannot be added without joining the route or removed while still named.
"""

from __future__ import annotations

import re
import stat
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
ADOPT = REPO_ROOT / "plugins" / "control-register" / "templates" / "adopt"
GUIDE = REPO_ROOT / "START-HERE.md"

# `## 4 — The container` and `### C2 — What has to be in the repository already`
# both count: the token is what a script names, the dash and title are prose.
HEADING = re.compile(r"^#{2,3} (?P<token>[^\n]+?)(?: — [^\n]*)?$", re.M)

# A reference reaches a script two ways: spelled `§ B` in prose it prints, or as
# the bare last argument of `bad`/`wait_on`, which `_lib.sh` prefixes with `§ `.
# A token is a letter (`B`), a letter and a digit (`C2`) or a number (`4`) —
# bounded, so prose after it ("§ 5 is how you get a shell") is not swallowed.
INLINE_REF = re.compile(r"§ (?P<ref>[A-Z]\d?|\d+)(?=[\s,.:)\"]|$)")
ARG_REF = re.compile(r"""(?:bad|wait_on) +"[^"]*" +"(?P<ref>[^"]+)\"""")

# Commands the guide already carries. A script needing one of these is
# instructing rather than detecting.
RESTATED = (
    "brew install",
    "npm i -g",
    "security add-generic-password",
    "gh repo create",
    "uv init",
    "devcontainer up",
    "claude plugin marketplace add",
    "register-adopt",
)


# `guided.sh` asks questions and creates things (ADR 0049 revision 2). Every
# other script here reads and reports.
ACTING = {"guided.sh"}


def _scripts() -> list[Path]:
    return sorted(p for p in ADOPT.glob("*.sh") if p.name != "_lib.sh")


def _detectors() -> list[Path]:
    return [p for p in _scripts() if p.name not in ACTING]


def _headings() -> set[str]:
    return {m.group("token").strip() for m in HEADING.finditer(GUIDE.read_text(encoding="utf-8"))}


def test_the_route_directory_exists_and_holds_scripts() -> None:
    """A guard that guards nothing is worse than no guard."""
    assert ADOPT.is_dir(), f"{ADOPT.relative_to(REPO_ROOT)} is missing"
    assert _scripts(), "no stage scripts found — the rest of this file would pass vacuously"
    assert (ADOPT / "_lib.sh").is_file(), "_lib.sh holds the vocabulary every stage sources"


@pytest.mark.parametrize("script", _scripts(), ids=lambda p: p.name)
def test_a_stage_script_is_executable(script: Path) -> None:
    """An adopter runs `./00-preflight.sh`, not `bash 00-preflight.sh`."""
    mode = script.stat().st_mode
    assert mode & stat.S_IXUSR, (
        f"{script.relative_to(REPO_ROOT)} is not executable. "
        "The route prints `./<script>`, which needs the bit set."
    )


@pytest.mark.parametrize("script", _scripts(), ids=lambda p: p.name)
def test_every_section_a_script_names_exists(script: Path) -> None:
    """A reference is a promise that the reader will find something there."""
    text = script.read_text(encoding="utf-8")
    refs = {m.group("ref").strip() for m in INLINE_REF.finditer(text)}
    refs |= {m.group("ref").strip() for m in ARG_REF.finditer(text)}
    headings = _headings()
    missing = sorted(r for r in refs if r not in headings)
    assert not missing, (
        f"{script.relative_to(REPO_ROOT)} points at {missing}, which is not a heading in "
        f"START-HERE.md. Either the section was renamed — in which case fix the reference — "
        f"or the reference was invented. Headings available: {sorted(headings)}"
    )


@pytest.mark.parametrize("script", _detectors(), ids=lambda p: p.name)
def test_a_detector_detects_rather_than_instructs(script: Path) -> None:
    """The document owns the words; the script owns the verdict.

    Scoped to what a script *prints*. A comment naming `/register-adopt` to say
    what a stage is for explains the code to whoever maintains it and reaches no
    adopter; a printed `brew install uv` is the second copy this bans.
    """
    printed = "\n".join(
        line for line in script.read_text(encoding="utf-8").splitlines()
        if not line.lstrip().startswith("#")
    )
    found = sorted(c for c in RESTATED if c in printed)
    assert not found, (
        f"{script.relative_to(REPO_ROOT)} contains {found}, which START-HERE.md already "
        "spells out. Print the section reference instead: two copies of a command drift, "
        "and the reader follows the stale one."
    )


def test_the_guided_script_owns_no_check_of_its_own() -> None:
    """It may create things. It may not decide whether something holds.

    The moment `guided.sh` re-implements a check, there are two copies of it and
    the one an adopter runs by hand can disagree with the one the guided route
    runs. So every verdict it reaches must come from a stage script it invokes.
    """
    guided = ADOPT / "guided.sh"
    assert guided.is_file(), "guided.sh is the acting route and is missing"
    text = guided.read_text(encoding="utf-8")

    invoked = {stage for stage in _route_scripts() if stage in text}
    assert invoked, (
        "guided.sh invokes no stage script, so whatever checking it does is a "
        "second copy. Call the stage and interpret its exit code."
    )

    printed = "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("#")
    )
    for verdict_helper in ("pass ", "fail "):
        assert f"\n  {verdict_helper}" not in printed, (
            f"guided.sh calls `{verdict_helper.strip()}` inside a check. Verdicts are the "
            "stage scripts' to give; guided.sh reports what they returned."
        )


def _route_scripts() -> list[str]:
    lib = (ADOPT / "_lib.sh").read_text(encoding="utf-8")
    declared = re.search(r'^ROUTE_SCRIPTS="([^"]+)"$', lib, re.M)
    assert declared is not None, "_lib.sh has no ROUTE_SCRIPTS line"
    return declared.group(1).split()


def test_the_route_and_the_files_agree() -> None:
    """Both directions. A stage off the route never runs; a stage on it must exist."""
    lib = (ADOPT / "_lib.sh").read_text(encoding="utf-8")
    route = _route_scripts()
    on_disk = {p.name for p in _scripts()} - {"status.sh"} - ACTING

    assert set(route) == on_disk, (
        f"the route names {sorted(route)} and the directory holds {sorted(on_disk)}. "
        "status.sh walks ROUTE_SCRIPTS and nothing else, so a stage missing from it "
        "is a stage nobody is sent to."
    )
    for stage in route:
        assert f"{stage})" in lib, (
            f"{stage} is on the route but has no route_title case in _lib.sh, "
            "so status.sh would print 'unknown stage' for it."
        )


def _run_against_lib(body: str) -> subprocess.CompletedProcess[str]:
    """Exercise the reporting vocabulary the way a stage script uses it."""
    return subprocess.run(
        ["bash", "-c", f"set -uo pipefail\n. ./_lib.sh\n{body}"],
        cwd=ADOPT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_an_optional_absence_stops_nothing() -> None:
    """A route that halts for something it just called optional is lying about one.

    The first person to run this had every tool installed and was stopped by
    VS Code — reported absent because `code` was not on PATH, which is a
    separate install from the editor. The stage exited 2, the guided route read
    any non-zero as fatal, and it printed "install what is missing" naming
    nothing, because nothing was.
    """
    result = _run_against_lib('optional "VS Code"\nverdict 00-tools.sh 10-repo.sh')
    assert result.returncode == 0, (
        "an optional absence reached a counter and stopped the route:\n"
        f"{result.stdout}{result.stderr}"
    )


def test_a_verdict_names_what_it_is_waiting_for() -> None:
    """A count is a puzzle. "1 manual act outstanding" does not say which."""
    result = _run_against_lib(
        'manual "Docker has 4 GB of memory" "B"\nverdict 00-tools.sh 10-repo.sh'
    )
    assert result.returncode == 2, f"expected the waiting verdict, got {result.returncode}"
    assert result.stdout.count("Docker has 4 GB of memory") >= 2, (
        "the summary counts the outstanding acts without naming them, so the reader "
        f"has to go and find which:\n{result.stdout}"
    )


def test_vs_code_is_not_detected_by_its_shell_command_alone() -> None:
    """`code` on PATH is a separate install from the editor, and optional itself."""
    tools = (ADOPT / "00-tools.sh").read_text(encoding="utf-8")
    assert "Visual Studio Code.app" in tools, (
        "00-tools.sh tests only for the `code` command, which reports VS Code missing "
        "on a Mac that is running it — as it did, inside a VS Code terminal."
    )


def test_a_stage_reads_the_repository_the_adopter_is_standing_in(tmp_path: Path) -> None:
    """Reported from a real run, and every green line before it was meaningless.

    The route ships inside a checkout of *this* repository, which is itself a
    git repository with a manifest, a lockfile, a `.python-version`, tests and a
    `controls.yaml`. A stage that `cd`s to its own directory before asking
    `git rev-parse --show-toplevel` therefore answers about `ee-standard` — and
    passes every check while telling the adopter nothing about their project.

    It reported `10-repo.sh` and `20-platform.sh` done for a repository the
    adopter had never touched, and then looked for a Keychain entry named after
    the cache directory the route was unpacked into.
    """
    project = tmp_path / "someone-elses-project"
    project.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", "."], cwd=project, check=True)

    result = subprocess.run(
        [str(ADOPT / "10-repo.sh")],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )

    assert str(project) in result.stdout, (
        "the stage did not report on the directory it was run from. It reported:\n"
        f"{result.stdout}"
    )
    assert str(REPO_ROOT) not in result.stdout, (
        "the stage reported on the route's own checkout rather than the adopter's "
        f"repository:\n{result.stdout}"
    )
