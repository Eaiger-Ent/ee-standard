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

import os
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

    # The verdict names the route's own path, deliberately — it is the command to
    # re-run. What must not name it is the line reporting which repository was
    # read, so that is the line this asserts about.
    reported = [line for line in result.stdout.splitlines() if "git repository —" in line]
    assert reported, f"the stage reported no repository at all:\n{result.stdout}"

    assert str(project) in reported[0], (
        f"the stage did not report on the directory it was run from: {reported[0]!r}"
    )
    assert str(REPO_ROOT) not in reported[0], (
        "the stage reported on the route's own checkout rather than the adopter's "
        f"repository: {reported[0]!r}"
    )


def test_a_printed_command_runs_from_where_the_reader_is(tmp_path: Path) -> None:
    """`./10-repo.sh` is correct in one directory, and it is not the reader's.

    Reported from a real run: the route printed `Run this for the detail:
    ./10-repo.sh`, and the reader — standing in the directory the route had just
    reported on, which is the right place to be — got
    `zsh: no such file or directory`. The scripts live in a cache directory
    nobody stands in, and a stage reads the repository you are standing in, so
    the command is two lines: where to be, and what to run.
    """
    project = tmp_path / "a-project"
    project.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", "."], cwd=project, check=True)

    result = subprocess.run(
        [str(ADOPT / "10-repo.sh")], cwd=project, capture_output=True, text=True, check=False
    )

    assert "./10-repo.sh" not in result.stdout, (
        "a bare relative path was printed as the command to run:\n" f"{result.stdout}"
    )
    assert str(ADOPT / "10-repo.sh") in result.stdout, (
        "the printed command is not an absolute path, so it only works from the "
        f"route's own directory:\n{result.stdout}"
    )
    assert f"cd {project}" in result.stdout, (
        "the printed command does not say where to stand, and a stage reads the "
        f"repository it is run from:\n{result.stdout}"
    )


@pytest.mark.parametrize("script", _scripts(), ids=lambda p: p.name)
def test_no_script_offers_a_bare_relative_command(script: Path) -> None:
    """The static half: `run_hint` exists so nothing hand-rolls the hint again."""
    printed = "\n".join(
        line for line in script.read_text(encoding="utf-8").splitlines()
        if not line.lstrip().startswith("#")
    )
    offenders = re.findall(r"\./\d\d-[a-z-]+\.sh|\./status\.sh|\./guided\.sh", printed)
    assert not offenders, (
        f"{script.relative_to(REPO_ROOT)} prints {sorted(set(offenders))}, which resolves "
        "only inside the route's own directory. Use `run_hint <stage>`, which prints the "
        "`cd` and the absolute path."
    )


def test_the_guided_substitution_matches_the_template_it_substitutes() -> None:
    """Two files, one set of placeholders, and nothing else holding them together.

    `guided.sh` performs § 4's substitution, so it names each `{{PLACEHOLDER}}`
    the devcontainer template carries. Add one to the template and it ships
    unsubstituted — a build that fails at `sha256sum -c` with nothing pointing
    back. Remove one and the `sed` is dead code that looks live.
    """
    template_dir = REPO_ROOT / "plugins" / "control-register" / "templates" / "devcontainer"
    placeholder = re.compile(r"\{\{[A-Z0-9_]+\}\}")

    in_template = set()
    for path in template_dir.rglob("*"):
        if path.is_file() and path.name != "README.md":
            body = path.read_text(encoding="utf-8", errors="ignore")
            in_template |= set(placeholder.findall(body))

    guided = (ADOPT / "guided.sh").read_text(encoding="utf-8")
    substituted = set(placeholder.findall(guided))

    assert in_template, "the template carries no placeholders — this test guards nothing"
    assert substituted == in_template, (
        f"guided.sh substitutes {sorted(substituted)} and the template carries "
        f"{sorted(in_template)}. Unsubstituted: {sorted(in_template - substituted)}. "
        f"Substituted but absent: {sorted(substituted - in_template)}."
    )


#: The § 5 commands `guided.sh` prints at its handover. Printing them means
#: holding a second copy, so each must still be the one the guide gives.
HANDOVER_COMMANDS = (
    "devcontainer exec --workspace-folder . bash",
    "claude plugin marketplace add Eaiger-Ent/ee-standard",
    "claude plugin install control-register@ee-standard",
    "claude plugin install lint-md@ee-standard",
    "claude plugin install lint-yaml@ee-standard",
    "claude --permission-mode acceptEdits",
    "/tui default",
    "/register-adopt --repo . --register ./controls.yaml",
)


@pytest.mark.parametrize("command", HANDOVER_COMMANDS)
def test_the_handover_gives_the_command_the_guide_gives(command: str) -> None:
    """Two copies of a command, and only this holding them together.

    `guided.sh` ends by printing § 5 rather than naming it — a reader given
    commands at every step and a section number at the last one is being
    stopped, not handed over. The cost is a second copy of those commands, so
    each is checked against `START-HERE.md`: change one there and this fails
    rather than leaving the route quietly telling people something else.
    """
    guided = (ADOPT / "guided.sh").read_text(encoding="utf-8")
    guide = (REPO_ROOT / "START-HERE.md").read_text(encoding="utf-8")

    assert command in guided, f"guided.sh no longer prints {command!r}"
    assert command in guide, (
        f"guided.sh prints {command!r} and START-HERE.md does not carry it. "
        "One of the two has drifted, and the reader follows whichever they met first."
    )


# --- § E: a missing PAT is met with what to make, and an offer to store it --


def _fake_security(tmp_path: Path) -> dict[str, str]:
    """A `security` that holds nothing, so the Keychain reads empty off macOS."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "security"
    fake.write_text("#!/bin/sh\nexit 44\n")
    fake.chmod(0o755)

    return {**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}"}


@pytest.mark.parametrize("colour", ["", "1"], ids=["plain", "coloured"])
def test_guided_recognises_the_report_of_a_missing_pat(tmp_path: Path, colour: str) -> None:
    """guided.sh offers to store a PAT when 25-credentials.sh's report carries
    `$PAT_MISSING`. Both read the one string from `_lib.sh`; this holds that the
    stage still prints it whole, colours included, where `grep -F` will find it."""
    project = tmp_path / "my-app"
    project.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", "."], cwd=project, check=True)
    env = {**_fake_security(tmp_path), "ADOPT_COLOUR": colour}

    result = subprocess.run(
        [str(ADOPT / "25-credentials.sh")],
        cwd=project, env=env, capture_output=True, text=True, check=False,
    )
    missing = _run_against_lib('printf %s "$PAT_MISSING"').stdout
    assert missing, "_lib.sh no longer defines PAT_MISSING"
    assert missing in result.stdout, (
        f"25-credentials.sh did not report {missing!r} whole, so guided.sh would never "
        f"offer to store a token:\n{result.stdout}"
    )
    assert "$PAT_MISSING" in (ADOPT / "guided.sh").read_text(encoding="utf-8")


def test_the_project_prefix_is_the_one_fetch_secrets_looks_up(tmp_path: Path) -> None:
    """guided.sh stores the token under the name; fetch-secrets.sh finds it by it."""
    project = tmp_path / "my-app"
    project.mkdir()
    result = subprocess.run(
        ["bash", "-c", f'. "{ADOPT}/_lib.sh"; project_prefix'],
        cwd=project, capture_output=True, text=True, check=True,
    )
    assert result.stdout.strip() == "MY_APP"
    fetch = REPO_ROOT / "plugins/control-register/templates/devcontainer/fetch-secrets.sh"
    lib = (ADOPT / "_lib.sh").read_text(encoding="utf-8")
    transform = "tr '[:lower:]-' '[:upper:]_'"
    assert transform in fetch.read_text(encoding="utf-8") and transform in lib


def test_the_permissions_guided_prints_are_read_from_the_guide() -> None:
    """No copy of the permissions lives in guided.sh. It prints a span of
    START-HERE.md, and this runs the very `sed` it runs, so a renamed heading
    or a moved paragraph fails here rather than printing nothing to an adopter."""
    guided = (ADOPT / "guided.sh").read_text(encoding="utf-8")
    extract = re.search(r"(sed -n '[^']+') \"\$GUIDE\" \\\n\s*\| (sed '[^']+')", guided)
    assert extract, "guided.sh no longer extracts § E's token section from the guide"
    root = subprocess.run(
        ["git", "-C", str(ADOPT), "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert Path(root) / "START-HERE.md" == GUIDE, (
        "guided.sh finds the guide at the checkout's git root, which is no longer where it is"
    )
    assert 'rev-parse --show-toplevel' in guided and "../" not in guided, (
        "guided.sh climbs to the guide with `..`, which the incubator's path-hygiene gate fails"
    )
    printed = subprocess.run(
        ["bash", "-c", f'{extract.group(1)} "{GUIDE}" | {extract.group(2)}'],
        capture_output=True, text=True, check=True,
    ).stdout
    guide = GUIDE.read_text(encoding="utf-8")
    table = guide[guide.index("| Permission | Level | What it lets you do |"):]
    table = table[: table.index("\n\n")]
    assert table in printed, f"the permissions table is not in what guided.sh prints:\n{printed}"
    assert "| Token name |" in printed
    assert "security add-generic-password" not in printed, "the span ran past § E's token section"


def test_the_store_command_guided_gives_is_the_guides() -> None:
    """guided.sh both prints and runs the command that stores the token, so it
    is a second copy, held to START-HERE.md as the § 5 handover commands are."""
    guided = (ADOPT / "guided.sh").read_text(encoding="utf-8")
    command = 'security add-generic-password -a "$USER" -s "'
    assert command in guided
    assert command in GUIDE.read_text(encoding="utf-8")
    assert 'security add-generic-password -a "$USER" -s "$name" -w "$token"' in guided
