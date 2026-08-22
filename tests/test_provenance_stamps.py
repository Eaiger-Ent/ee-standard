"""Every `ee-control:` stamp in this repository is well-formed.

`docs/00-concepts.md` § The provenance stamp makes "deployed but stale"
computable. It was not computable here: three of the four `lint-md`-deployed
artefacts carried no stamp at all, and the one that did read `register: v0.1.0`
against a register four versions further on, while `CLAUDE.md` stated as fact
that they all carried one (§ F).

What is checked here is **well-formedness**, deliberately, and not currency. A
stale stamp is a recommendation to redeploy — "notify, never redeploy" — so a
test that failed the build on one would be enforcing redeployment, which is the
behaviour this design rules out. A stamp that does not parse, or that names a
control the register does not define, or that claims a contract the register has
not reached, is a defect in the deployment rather than a staleness signal, and
those are what fail here.

Reporting the stale-but-valid case is Phase 5's sweep.
"""

from __future__ import annotations

import subprocess

import pytest

from conftest import REPO_ROOT, a_register
from standard_check.provenance import EXPECTED, MARKER, stamps_in


def _stamped_files() -> list[str]:
    """Tracked files containing the marker, however the stamp is spelled.

    Searching for the bare marker rather than the full pattern is the point: a
    stamp that is present but malformed must be found and failed, not missed.
    """
    found = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "grep", "-l", MARKER],
        capture_output=True,
        text=True,
        check=False,
    )
    # A stamp is evidence only where it sits in an artefact deployed *into this
    # repository*. Four kinds of file carry the marker without being one, and
    # each is excluded for its own reason rather than by accumulation:
    #
    #   docs/, CLAUDE.md  prose that defines or discusses the format
    #   src/              the parser's own docstring, which shows an example
    #   tests/            fixtures, including the malformed ones on purpose
    #   plugins/          templates a gate writes into *other* repositories,
    #                     whose placeholders are unfilled here — that they parse
    #                     once the register fills them is tests/test_plugin.py's
    #
    # Anything else holding the marker is a deployed artefact and is checked.
    excluded = ("docs/", "CLAUDE.md", "src/", "tests/", "plugins/")
    return [p for p in found.stdout.split() if not p.startswith(excluded)]


def test_the_deployed_artefacts_are_the_ones_that_carry_stamps() -> None:
    """Every artefact a gate deployed, and no other.

    Five are `lint-md`'s, where only one used to be stamped. § F counted four;
    the fifth, `.claude/hooks/md-lint.py`, was invisible to that count because
    it sat behind a ruff exclusion — the same exclusion that hid eleven LNT-001
    violations in it.

    The sixth is SEC-001's CI locus, stamped in Phase 2. `.pre-commit-config.yaml`
    is on both lists: it holds a hook for each control, stamped at the hook.

    The seventh is LNT-001's editor locus, stamped when `gate-quality` was
    built. Its three controls added five more stamps to the two files already
    here, which is the point of grouping a gate by the artefact it writes: three
    controls, two shared files, one skill that owns its own sections of each.

    The ninth is `.devcontainer/setup.sh`, and it is the one file whose stamps
    all belong to gates other than the one that owns the file.

    The tenth is `.github/rulesets/default-branch.json`, and it is the one
    artefact that enforces nothing by existing — a record of what the platform
    is asked to enforce, not the enforcement.

    The eighth is `.github/dependabot.yml`, SUP-002's, and it is the one file
    where a whole-file stamp is right rather than wrong: every line of it
    belongs to one control. `gate-supply-chain`'s other three stamps land in
    the workflow and the pre-commit config already listed — so the file count
    grows by one while the stamp count grows by four.
    """
    assert set(_stamped_files()) == {
        ".markdownlint.yaml",
        ".markdownlint-cli2.yaml",
        ".pre-commit-config.yaml",
        ".github/workflows/lint.yml",
        ".claude/hooks/md-lint.py",
        # SEC-001's two, from Phase 2. Both were hand-wired in Phase 0.5 and
        # adopted by `gate-secrets` rather than deployed from nothing — the
        # stamps say so, which is what keeps them from claiming otherwise.
        ".github/workflows/standard-check.yml",
        # `gate-quality`'s editor locus. The workflow and the pre-commit config
        # above hold its other five stamps; this is the seventh file, and the
        # only artefact any gate writes that is neither a hook nor a CI step.
        ".devcontainer/devcontainer.json",
        # SUP-002's, from `gate-supply-chain`. The only artefact any gate writes
        # that belongs to exactly one control end to end, which is why its stamp
        # sits at the top of the file rather than at a section of it.
        ".github/dependabot.yml",
        # `gate-build` owns this file and stamps nothing in it — neither BLD-001
        # nor DEV-001 has a locus here. The two stamps it carries are other
        # gates': SEC-001's scanner install and SUP-001's package manager, each
        # a site `tools.<tool>.pinned_at` names and no gate claimed until
        # register contract 15. Shared file, per-region stamps, as
        # `.pre-commit-config.yaml` has been since Phase 2's first slice.
        ".devcontainer/setup.sh",
        # CI-001's, from `gate-repo`. The only artefact any gate writes that
        # enforces nothing by existing: GitHub does not read a path in this
        # repository to decide what protects `main`. It is a record, verified as
        # intent, with the platform's own state left to the remote block and to
        # Phase 3.
        ".github/rulesets/default-branch.json",
    }


@pytest.mark.parametrize("path", _stamped_files())
def test_stamp_is_well_formed_and_names_a_real_control(path: str) -> None:
    text = (REPO_ROOT / path).read_text(encoding="utf-8")
    # One parser, shared with the assert that reads a stamp back and with
    # Phase 5's sweep. A regex copied into a test is a second definition of the
    # format, free to accept what the checker rejects.
    stamps = stamps_in(text)
    assert stamps, (
        f"{path} carries an `{MARKER}` marker that does not parse as a stamp — "
        f"expected `{EXPECTED}` (docs/00-concepts.md)"
    )
    # Every marker in the file parsed, not merely the first: a partly-owned file
    # carries one stamp per section, and a malformed second one would hide
    # behind a well-formed first.
    assert len(stamps) == text.count(MARKER), (
        f"{path} carries {text.count(MARKER)} `{MARKER}` markers but only "
        f"{len(stamps)} parse as stamps — expected `{EXPECTED}`"
    )

    register = a_register()
    known = {control.id for control in register.controls} | {
        control.id for control in register.meta_controls
    }
    for stamp in stamps:
        assert stamp.control in known, (
            f"{path}: stamp names {stamp.control}, which the register does not define"
        )
        # Ahead of the register is a defect; behind it is staleness, which is
        # reported rather than failed.
        assert stamp.register_contract <= register.register_contract, (
            f"{path}: stamp claims register contract {stamp.register_contract}, "
            f"but the register is at {register.register_contract}"
        )
