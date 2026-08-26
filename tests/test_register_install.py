"""The checker's route into a repository that is not this one.

[ADR 0032](../docs/adr/0032-the-checker-is-installed-from-a-tagged-ref.md)
decided that an adopter installs `register-check` as a dependency pinned to a
tagged ref of this repository, placed by a skill that owns nothing else. Two
halves of that fail separately, so they are checked separately.

**The address must resolve.** The register names a repository and a tag, and the
tag is the whole of the pin — `v0.1.0` meaning nothing, or naming a tag nobody
cut, is a pin an adopter discovers is broken at install time rather than here.
The ADR records this as the part most likely to be skipped, "because the first
install will work against a tag cut by hand and nothing will complain until the
second one is needed". This is what complains.

**The skill must not restate the register.** The one failure mode a reader
cannot see in a diff is a plausible URL or a plausible `v…` written into the
skill: it would work, and it would go on working while the register moved. So
the address, the tag and the composed requirement are each checked absent from
everything under the skill's directory — the same rule
`test_no_skill_repeats_a_version_the_register_pins` holds for tool versions,
applied to the one value that is not a version.

What is deliberately **not** checked is that the skill's steps happen in the
order it describes. `test_register_adopt.py` drives the dispatcher's sequence
because that sequence is the thing being claimed; here the claim is about where
values come from, which is a property of the text rather than of a run.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest
import yaml

from conftest import REPO_ROOT, a_register
from register_check.cli import main
from register_check.provenance import stamps_in

SKILL = REPO_ROOT / "plugins/control-register/skills/register-install"
SKILL_TEXT = (SKILL / "SKILL.md").read_text(encoding="utf-8")

#: The ecosystem that has a spelling for a git dependency. ADR 0032 § The
#: non-Python adopter is not solved records that it is the only one, so the
#: absence elsewhere is a decision rather than an omission to be filled in.
ECOSYSTEM_WITH_A_SPELLING = "python"


def _install() -> object:
    tool = a_register().tools.get("register-check")
    assert tool is not None, "the register does not describe its own checker"
    return tool.install


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", f"safe.directory={REPO_ROOT}", "-C", str(REPO_ROOT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_the_register_says_where_the_checker_comes_from() -> None:
    """Before contract 29 it described the shape of an answer and named no artefact."""
    install = _install()
    assert install is not None, (
        "tools.register-check has no `install:` — an adopter following "
        "docs/08-adopting.md reaches 'run the checker' with nothing to run"
    )
    assert install.repository.startswith("https://")  # type: ignore[attr-defined]
    assert re.fullmatch(r"v\d+\.\d+\.\d+", install.ref)  # type: ignore[attr-defined]


def test_the_tag_the_register_names_exists() -> None:
    """The ADR's own prediction, made into a build failure.

    A tag is what an adopter pins, so a register naming one nobody cut hands
    them an install that fails — and it fails in *their* repository, at the
    step after which nothing else in the guide can be followed.
    """
    ref = _install().ref  # type: ignore[attr-defined]
    found = _git("tag", "--list", ref).stdout.strip()
    assert found == ref, (
        f"the register pins the checker to {ref} and this repository has no such tag "
        f"(tags: {_git('tag', '--list').stdout.split() or 'none'}). Cut it on the commit "
        "whose pyproject version matches, and push it — a tag that exists only locally "
        "is one no adopter can resolve."
    )


def test_the_tag_names_the_version_it_claims() -> None:
    """What makes a tag mean something rather than be cut when someone remembers.

    Checked at the tagged commit rather than in the working tree, because those
    legitimately differ: `install.ref` is the last *released* checker, and
    `pyproject.toml`'s version is what the next release will be. Comparing the
    two would fail every version bump for being one.
    """
    ref = _install().ref  # type: ignore[attr-defined]
    result = _git("show", f"{ref}:pyproject.toml")
    assert result.returncode == 0, f"cannot read pyproject.toml at {ref}: {result.stderr.strip()}"
    version = re.search(r'(?m)^version = "([^"]+)"$', result.stdout)
    assert version is not None, f"pyproject.toml at {ref} declares no version"
    assert version.group(1) == ref.removeprefix("v"), (
        f"{ref} points at a commit whose version is {version.group(1)}. A tag that does "
        "not name the version it carries is a pin whose number means nothing."
    )


def test_the_ecosystem_supplies_the_grammar_and_the_register_supplies_the_address() -> None:
    """Two sections, and the split is the point.

    PEP 440's direct reference is a fact about Python; the repository and tag
    are facts about this project. Composed in one field, an adopter pointing at
    an internal mirror would have to restate the grammar to change the host.
    """
    ecosystem = a_register().ecosystems[ECOSYSTEM_WITH_A_SPELLING]
    template = ecosystem.git_dependency
    assert template is not None, f"{ECOSYSTEM_WITH_A_SPELLING} has no git_dependency spelling"
    assert {"{package}", "{repository}", "{ref}"} <= set(re.findall(r"\{\w+\}", template))
    install = _install()
    composed = template.format(
        package="register-check",
        repository=install.repository,  # type: ignore[attr-defined]
        ref=install.ref,  # type: ignore[attr-defined]
    )
    assert composed.startswith("register-check @ git+https://")


def _skill_files() -> list[Path]:
    return sorted(p for p in SKILL.rglob("*") if p.is_file())


@pytest.mark.parametrize(
    "field",
    ["repository", "ref"],
)
def test_the_skill_writes_no_address_of_its_own(field: str) -> None:
    """The failure a diff cannot show: a plausible URL that works, and goes on working.

    A hard-coded address survives a fork, a mirror move and a release, and
    reports success the whole time. It is the same defect as a gate repeating a
    version the register pins, in the one value that is not a version.
    """
    literal = getattr(_install(), field)
    offenders = [
        str(path.relative_to(REPO_ROOT))
        for path in _skill_files()
        if literal in path.read_text(encoding="utf-8", errors="ignore")
    ]
    assert not offenders, (
        f"install.{field} ({literal}) is written into: {', '.join(offenders)}. "
        "It comes from the register at run time or not at all."
    )


def test_the_skill_writes_no_composed_requirement_either() -> None:
    """Splitting the string is not a way round the rule above."""
    ecosystem = a_register().ecosystems[ECOSYSTEM_WITH_A_SPELLING]
    install = _install()
    composed = ecosystem.git_dependency.format(  # type: ignore[union-attr]
        package="register-check",
        repository=install.repository,  # type: ignore[attr-defined]
        ref=install.ref,  # type: ignore[attr-defined]
    )
    for path in _skill_files():
        assert composed not in path.read_text(encoding="utf-8", errors="ignore"), (
            f"{path.name} spells the whole requirement out"
        )


def test_the_skill_reads_both_halves_from_the_register() -> None:
    """Named rather than paraphrased: a skill that says 'the register' and reads
    one field is the half-done version of this."""
    text = " ".join(SKILL_TEXT.split())
    # The skill reads the address with `yq`, which spells the key
    # `.tools["register-check"].install`; the dotted form is what the prose and
    # the error table use. Either spelling is the field being named.
    assert "register-check\"].install" in text or "tools.register-check.install" in text
    assert "git_dependency" in text
    assert "add_dev_dependency" in text


def test_the_skill_stops_rather_than_inventing_a_spelling() -> None:
    """An ecosystem with no `git_dependency` gets a verdict, not a guess.

    The wrong grammar fails at install time in the adopter's repository rather
    than here, which is the worst place for it — and ADR 0032 accepts the
    non-Python adopter as unsolved rather than approximately solved.
    """
    text = " ".join(SKILL_TEXT.split())
    assert "If `git_dependency` is absent, stop and say so" in text
    assert "inventing one is worse than not having one" in text


def test_the_skill_deploys_no_control_and_stamps_nothing() -> None:
    """The one unstamped thing in the plugin, and why that is the decision.

    Every other deployed artefact carries an `ee-control:` stamp naming the
    control and the gate. There is no control here to name, so a stamp would
    have to invent one — and an unstamped artefact that *should* carry one is
    what `lint-md`'s deployment looked like (§ F). Stating the reason is what
    keeps the two apart.
    """
    for path in _skill_files():
        stamps = stamps_in(path.read_text(encoding="utf-8", errors="ignore"))
        assert not stamps, f"{path.name} writes a stamp naming {stamps[0].control}"
    assert not (SKILL / "templates").exists(), "there is no artefact for a template to carry"
    text = " ".join(SKILL_TEXT.split())
    assert "No control names this" in text
    sidecar = yaml.safe_load(
        (REPO_ROOT / "plugins/control-register/.claude-plugin/deploys.json").read_text()
    )
    assert "register-install" not in sidecar["gates"], "it is not a gate and deploys nothing"


def test_the_dispatcher_dispatches_it_first_and_does_not_install_anything_itself() -> None:
    """ADR 0032's reason for a skill of its own, held to the dispatcher.

    `register-adopt` verifies *through* the checker — every gate it dispatches
    ends with `register-check run --control <ID>`, and its own pre-flight runs
    the checker before any of them. A pre-flight that verifies through an
    instrument it does not have verifies nothing.
    """
    adopt = REPO_ROOT / "plugins/control-register/skills/register-adopt/SKILL.md"
    body = adopt.read_text(encoding="utf-8")
    text = " ".join(body.split())
    assert "/register-install" in text
    assert body.index("register-install") < body.index("## Step 1"), (
        "the checker has to be there before the pre-flight that runs it"
    )
    assert "Do not install the checker here" in text


def test_the_probe_both_skills_run_is_a_command_the_checker_accepts(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`register-adopt` Step 0 and `register-install` Step 4 both run
    `uv run register-check --version` as their liveness probe, and until Phase 4
    the checker did not implement it. Both skills stopped there, in a repository
    where the install had *worked*: the right artefact, at the right tag,
    recorded in the lockfile, and no way to ask whether it was there.

    The probe is read out of the skill rather than retyped, so a skill that
    changes its probe fails here rather than in an adopter's repository.
    """
    probe = re.search(r"register-check (--[a-z-]+)\b", SKILL_TEXT)
    assert probe is not None, "the skill names no `register-check` probe at all"
    flag = probe.group(1)
    with pytest.raises(SystemExit) as exit_info:
        main([flag])
    assert exit_info.value.code == 0, f"`register-check {flag}` is not a command the CLI accepts"
    assert capsys.readouterr().out.strip().startswith("register-check ")
