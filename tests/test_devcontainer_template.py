"""The shipped devcontainer template satisfies the controls that judge it.

Phase 2's criterion is *"the devcontainer template builds, and DEV-001 passes
against it"*, and the two halves are verified in different places. **Building it
is not verified here and cannot be**: this devcontainer has no Docker, so a test
claiming a successful build would be claiming something nothing ran. That half
is recorded in `docs/10-phase-2-review.md` from an operator's own build, and the
criterion stays open until it is.

What *is* verified here is everything a checker can decide from files: that
BLD-001 and DEV-001 pass against a repository whose `.devcontainer/` is a copy
of the template, and that the second exit criterion holds —

    The template pins no tool version by hand. Every tool it installs is either
    sourced from a lockfile the consumer repo already commits, or from a single
    toolchain file — never a literal inside `setup.sh`.

That one is worth a test rather than a review, because it is the criterion
[ADR 0020](../docs/adr/0020-a-locus-reaches-the-pinned-artefact.md) singled out
as *"met in letter"* by a template with a resolution hole in it. A grep is
harder to talk past than a reading.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from conftest import REPO_ROOT, make_repo
from register_check.cli import main
from register_check.repo import load_jsonc

TEMPLATE = REPO_ROOT / "plugins/control-register/templates/devcontainer"
REGISTER_PATH = REPO_ROOT / "controls.yaml"
PROJECT = "probe-app"


def _copied(root: Path) -> Path:
    """A repository whose `.devcontainer/` is the template, placeholders filled."""
    target = root / ".devcontainer"
    shutil.copytree(TEMPLATE, target)
    # The README ships with the template for a reader; it is not part of the
    # container, and a copy that carried it would have `{{PROJECT_NAME}}` in a
    # file nothing substitutes.
    (target / "README.md").unlink()
    for path in target.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            if "{{" in text:
                path.write_text(text.replace("{{PROJECT_NAME}}", PROJECT), encoding="utf-8")
    make_repo(root, {"README.md": f"# {PROJECT}\n"})
    return root


def _verdict(root: Path, capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    code = main(
        [
            "--repo",
            str(root),
            "--register",
            str(REGISTER_PATH),
            "run",
            "--control",
            "BLD-001",
            "--control",
            "DEV-001",
        ]
    )
    return code, capsys.readouterr().out


def test_every_placeholder_is_named_in_the_readme() -> None:
    """A placeholder nobody documents is one nobody replaces.

    `grep -rl '{{'` is the instruction the README gives, so what it finds has to
    be what the README explains.
    """
    placeholders = set()
    for path in TEMPLATE.rglob("*"):
        if path.is_file() and path.name != "README.md":
            placeholders |= set(re.findall(r"\{\{([A-Z_]+)\}\}", path.read_text(encoding="utf-8")))
    readme = (TEMPLATE / "README.md").read_text(encoding="utf-8")
    assert placeholders, "the template carries no placeholders at all"
    for name in placeholders:
        assert name in readme, f"{{{{{name}}}}} is not explained in the template README"


def test_the_copied_template_passes_the_controls_that_judge_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The half of the criterion a checker can decide.

    BLD-001 and DEV-001 both apply to a repository with a `.devcontainer/`, and
    both pass here on their *property* blocks. Their locus and stamp blocks fail,
    correctly and by design: this repository has not run `gate-build`, which is
    the next step the README tells an adopter to take. So the assertions below
    are per block rather than on the exit code.
    """
    root = _copied(tmp_path / "copied")
    _, out = _verdict(root, capsys)
    assert "✓ file: devcontainer_user_is_non_root" in out
    assert "✓ file: devcontainer_image_digest_pinned" in out
    assert "✓ file: devcontainer_lock_covers_all_features" in out
    # And what a fresh copy has not yet done, said rather than hidden.
    assert "pre-commit locus" in out
    assert "no tracked file carries a provenance stamp" in out


def test_the_lock_file_covers_every_feature_declared(tmp_path: Path) -> None:
    """A lock file covering some features reads as solved and is not.

    Phase 0.5's own exit criterion was re-opened over a lock file pinning three
    of four features. Checked directly as well as through DEV-001, because this
    is the shipped artefact rather than a fixture.
    """
    config = load_jsonc(TEMPLATE / "devcontainer.json")
    assert isinstance(config, dict)
    declared = set(config.get("features", {}))
    locked = json.loads((TEMPLATE / "devcontainer-lock.json").read_text(encoding="utf-8"))
    assert declared, "the template declares no features"
    assert declared <= set(locked["features"])
    for entry in locked["features"].values():
        assert re.search(r"@sha256:[0-9a-f]{64}$", entry["resolved"]), entry


def test_the_image_is_pinned_by_digest(tmp_path: Path) -> None:
    config = load_jsonc(TEMPLATE / "devcontainer.json")
    assert isinstance(config, dict)
    assert re.search(r"@sha256:[0-9a-f]{64}$", config["image"]), config["image"]


def test_the_container_states_a_non_root_user() -> None:
    """Absent counts as root.

    A devcontainer naming neither `containerUser` nor `remoteUser` runs as
    whatever its base image uses, which may be root today and may become root on
    any digest bump. Non-root by luck is not the property BLD-001 states, and
    this was a JSON key nothing verified until register contract 7.
    """
    config = load_jsonc(TEMPLATE / "devcontainer.json")
    assert isinstance(config, dict)
    user = config.get("containerUser") or config.get("remoteUser")
    assert user and user != "root", config


# The exit criterion, as a grep. Each pattern is a version literal in one of the
# shapes a setup script actually uses.
_VERSION_LITERAL = re.compile(
    r"""
    (?:==|@|=v?|\s-v\s|:|/v?)\d+\.\d+\.\d+  # pip==1.2.3, tool@1.2.3, VER=1.2.3, /v1.2.3/
    | \b[A-Z_]*VERSION[A-Z_]*=\S           # any FOO_VERSION= assignment
    | sha256:[0-9a-f]{64}                  # a checksum, which pins an artefact
    | \b[0-9a-f]{64}\b                      # the same checksum, bare, as
                                           # `echo "<hex>  f" | sha256sum -c -`
                                           # writes it — the shape this repo's
                                           # own setup.sh uses
    """,
    re.VERBOSE,
)


def test_setup_pins_no_tool_version_by_hand() -> None:
    """Phase 2's second template criterion, checked rather than reviewed.

    ADR 0020 singled this criterion out as one a template could meet *in
    letter*: it is about the **source** of a version, and a template with a
    resolution hole satisfies it. A grep is harder to talk past than a reading,
    so the literal shapes are enumerated here and the file must contain none.

    Comments are stripped first. The file explains at length *why* it pins
    nothing, and a rule that fired on its own rationale would push the
    explanation out of the file — which is the opposite of what this is for.
    """
    lines = [
        line
        for line in (TEMPLATE / "setup.sh").read_text(encoding="utf-8").splitlines()
        if not line.lstrip().startswith("#")
    ]
    offences = [line for line in lines if _VERSION_LITERAL.search(line)]
    assert not offences, offences


def test_the_grep_would_catch_a_pin_if_one_appeared() -> None:
    """The half that makes the other half mean something.

    A pattern loose enough to match nothing would pass the test above while
    verifying nothing at all — the vacuous-pass shape this repository keeps
    finding. Each spelling a real setup script uses is checked to fail.
    """
    for line in (
        "pip install --quiet uv==0.12.5",
        "GITLEAKS_VERSION=8.30.1",
        "curl -o t.tgz https://example.test/tool/v1.2.3/tool.tgz",
        'echo "551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb  t"'
        " | sha256sum -c -",
        "npm install -g markdownlint-cli2@0.18.1",
    ):
        assert _VERSION_LITERAL.search(line), line


def test_setup_installs_only_from_a_lockfile_the_repo_commits() -> None:
    """Every install in the template is guarded by a lockfile's presence.

    Not a restatement of the grep above: a script could pin nothing and still
    install something unpinned — `pip install uv`, `npm install -g` — which is
    worse, because the version is then whatever the registry served that day.
    """
    text = (TEMPLATE / "setup.sh").read_text(encoding="utf-8")
    body = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
    installs = re.findall(
        r"^\s*(?:npm|uv|poetry|pip3?|pnpm|yarn)\s+(?:\S+\s+)*?(?:ci|sync|install|add)\b[^\n]*",
        body,
        re.MULTILINE,
    )
    assert installs, "the template installs nothing at all — check this test still applies"
    for install in installs:
        # `uv run pre-commit install` installs a git hook, not a package, and is
        # the one shape that reads like a package install and is not.
        if "pre-commit install" in install:
            continue
        assert re.search(r"(npm ci|--frozen|--sync|--frozen-lockfile)", install), install
    # And each is frozen: nothing here may re-resolve.
    assert "npm ci" in body
    assert "uv sync --frozen" in body
    assert not re.search(r"^\s*npm install\b", body, re.MULTILINE)
    assert not re.search(r"^\s*pip3? install\b", body, re.MULTILINE)


@pytest.mark.parametrize("script", ["setup.sh", "fetch-secrets.sh", "check-auth.sh"])
def test_every_shipped_script_parses(script: str) -> None:
    """A template whose scripts do not parse fails at container-create time.

    That is the worst place to find it: the container is half-built, and the
    error arrives without the file in front of you.
    """
    result = subprocess.run(
        ["bash", "-n", str(TEMPLATE / script)], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("script", ["setup.sh", "fetch-secrets.sh", "check-auth.sh"])
def test_every_shipped_script_is_executable(script: str) -> None:
    assert (TEMPLATE / script).stat().st_mode & 0o111, script


def test_the_secrets_files_are_gitignored_by_the_template_itself() -> None:
    """SEC-001 depends on these two lines, so they travel with the directory.

    A `.gitignore` the adopter has to remember to add is one that gets added
    after the first commit — which is one commit too late, and a secret that
    reaches a remote is not undone by removing it.
    """
    ignored = (TEMPLATE / ".gitignore").read_text(encoding="utf-8").split()
    assert ".env" in ignored
    assert ".env.docker" in ignored


def test_a_copied_template_does_not_track_the_secrets_files(tmp_path: Path) -> None:
    """The line above, exercised by git rather than read.

    `.gitignore` semantics are subtle enough — a nested file, a leading slash,
    a negation — that asserting the file's contents is not the same as asserting
    the behaviour.
    """
    root = _copied(tmp_path / "secrets")
    (root / ".devcontainer/.env").write_text("TOKEN=sk-not-a-real-secret\n", encoding="utf-8")
    (root / ".devcontainer/.env.docker").write_text(
        "TOKEN=sk-not-a-real-secret\n", encoding="utf-8"
    )
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    tracked = subprocess.run(
        ["git", "-C", str(root), "ls-files"], capture_output=True, text=True, check=True
    ).stdout.split()
    assert ".devcontainer/.env" not in tracked
    assert ".devcontainer/.env.docker" not in tracked


def test_the_template_carries_no_value_the_register_pins() -> None:
    """The same rule `tests/test_plugin.py` holds over the skills.

    A template repeating a version the register owns would be a second source of
    truth for it, free to drift — the failure this repository exists to prevent,
    reproduced in the artefact meant to spread the prevention.
    """
    from conftest import a_register

    register = a_register()
    pinned = {tool.version for tool in register.tools.values() if tool.version}
    assert pinned, "the register pins no versions — check this test still applies"
    for path in TEMPLATE.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for version in pinned:
            assert version not in text, f"{path.name} repeats the register's pin {version}"
