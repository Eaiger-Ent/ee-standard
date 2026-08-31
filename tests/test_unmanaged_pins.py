"""A pin no bot is configured to move is reported, not failed.

`docs/17-adopter-onboarding-review.md` § J: the shipped devcontainer template
puts `UV_VERSION="..."` into a shell script, which is precisely the case
Dependabot has no manager for. So every adopter of that template holds at least
one literal pin, and unless they configure Renovate *and* annotate the site,
nothing will ever propose moving it — while SUP-001 and SUP-004 both pass,
because a pin that never moves is not a pin that has drifted.

Decision 2 of that review chose to **report** this rather than fail SUP-002. The
property is real, but the check needs a `renovate.json` parser and a Tier-1
`blocking` control is a hard place to put one before anybody knows how often it
fires. This report is what produces that evidence.

Four states, and the two middle ones are the finding.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import REPO_ROOT, a_register, make_repo
from register_check.deployments import unmanaged_literal_pins
from register_check.repo import Repo

ANNOTATION = "# renovate: datasource=github-releases depName=owner/tool\n"


def _literal_sites() -> list[str]:
    return [
        rel
        for tool in a_register().tools.values()
        if tool.source == "literal"
        for rel in tool.pinned_at
    ]


@pytest.fixture
def repo_with_pin(tmp_path: Path) -> Repo:
    """A repository holding every `pinned_at` site the register declares."""
    sites = _literal_sites()
    assert sites, "the register pins no literal tool — this test has nothing to check"
    return make_repo(tmp_path, {rel: 'TOOL_VERSION="1.2.3"\n' for rel in sites})


def test_no_config_and_no_annotation_is_reported(repo_with_pin: Repo) -> None:
    """The state an adopter lands in by following the template and stopping."""
    findings = unmanaged_literal_pins(repo_with_pin, a_register())
    assert findings, "a repository with literal pins and no Renovate config reported nothing"
    assert all("no Renovate configuration" in f for f in findings)


def test_config_without_an_annotation_is_still_reported(repo_with_pin: Repo) -> None:
    """The subtler half: configured, and the pin still matches no manager.

    This is the state § J found in the shipped template — a repository can copy
    a correct `renovate.json` and still have an invisible pin, because the
    manager anchors on the annotation.
    """
    (repo_with_pin.root / "renovate.json").write_text("{}", encoding="utf-8")
    findings = unmanaged_literal_pins(repo_with_pin, a_register())
    assert findings, "an unannotated pin under a present config reported nothing"
    assert all("no `# renovate:` annotation" in f for f in findings)


def test_config_and_annotation_together_report_nothing(repo_with_pin: Repo) -> None:
    """Both halves present is the only passing state, and this repository is in it."""
    (repo_with_pin.root / "renovate.json").write_text("{}", encoding="utf-8")
    for rel in _literal_sites():
        path = repo_with_pin.root / rel
        path.write_text(ANNOTATION + path.read_text(encoding="utf-8"), encoding="utf-8")
    assert unmanaged_literal_pins(repo_with_pin, a_register()) == ()


def test_this_repository_reports_nothing() -> None:
    """The report must be quiet where the work has been done.

    A check that fires on the repository that authored it is one people learn to
    ignore, which is the failure the sweep's own design notes warn about.
    """
    assert unmanaged_literal_pins(Repo(REPO_ROOT), a_register()) == ()


def test_an_absent_declared_site_is_not_this_checks_finding(tmp_path: Path) -> None:
    """A `pinned_at` path that does not exist is SUP-004's verdict, not this one.

    Reporting it here too would give one defect two voices in one run, and the
    one with the exit code should own it.
    """
    repo = make_repo(tmp_path, {"renovate.json": "{}"})
    assert unmanaged_literal_pins(repo, a_register()) == ()
