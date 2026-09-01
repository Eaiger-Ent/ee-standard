"""The authoring repository's credential posture must not ship.

[ADR 0022](../docs/adr/0022-a-platform-token-ci-carries.md) requirement 6. This
repository intends to carry its platform token as an ordinary repository secret
(its Option 1), because the accounts that could read it already hold admin here.
An adopter's contributors are not organisation owners, so the same arrangement
would be a real exfiltration path for them, and the standard asks them for the
deployment-environment gate instead (its Option 3).

That difference is defensible **only while it is recorded where an adopter does
not inherit it** — in that ADR and in the build plan, never in `controls.yaml`
and above all never under `plugins/`, which is what an adopter installs.

The requirement says of itself that it is the one most likely to be skipped,
because nothing breaks when it is. These tests are what breaks.

**What they do not catch**, stated rather than implied: the phrase tests below
find the posture written in this repository's own vocabulary. Somebody could
describe the same arrangement without the words and get past them — what would
catch that is the two derived tests beside them, which read the register and the
shipped templates rather than prose.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from conftest import REPO_ROOT, a_register

PLUGIN = REPO_ROOT / "plugins/control-register"
ADR = REPO_ROOT / "docs/adr/0022-a-platform-token-ci-carries.md"
BUILD_PLAN = REPO_ROOT / "docs/04-build-plan.md"

#: How this repository names its own arrangement. "Option 3" is deliberately not
#: here: that is the *adopter's* posture, so the register and the gates may say
#: it. Only the authoring repository's own choice is what must not travel.
OWN_POSTURE = "Option 1"

_SECRET_REFERENCE = re.compile(r"secrets\.([A-Za-z_][A-Za-z0-9_-]*)")
_DECLARES_CREDENTIALS = re.compile(r"^platform_credentials:", re.MULTILINE)


def _shipped_files() -> list[Path]:
    return [path for path in PLUGIN.rglob("*") if path.is_file()]


def test_the_difference_is_recorded_where_an_adopter_does_not_inherit_it() -> None:
    """Both halves of requirement 6's condition, and this is the first half.

    Deleting the record is as much a breach as shipping the posture: an
    undocumented divergence between what this repository does and what it asks
    of everyone else is indistinguishable from an oversight.
    """
    assert OWN_POSTURE in ADR.read_text(encoding="utf-8"), ADR
    assert OWN_POSTURE in BUILD_PLAN.read_text(encoding="utf-8"), BUILD_PLAN


def test_the_register_does_not_carry_it() -> None:
    """`controls.yaml` states rules, never this repository's own arrangement.

    It said the opposite at contract 22, which is how this test came to exist:
    the block introducing `platform_credentials:` explained that *ADR 0022 chose
    Option 1* — true of this repository, and read by every repository the
    register reaches.
    """
    register = (REPO_ROOT / "controls.yaml").read_text(encoding="utf-8")
    assert OWN_POSTURE not in register


@pytest.mark.parametrize("path", _shipped_files(), ids=lambda p: p.name)
def test_no_shipped_file_carries_it(path: Path) -> None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    assert OWN_POSTURE not in text, f"{path.relative_to(REPO_ROOT)} names this repo's posture"


def test_no_standing_credential_this_repository_holds_appears_under_plugins() -> None:
    """Derived from the register rather than from a list kept by hand.

    An entry whose `triggers` names events rather than `any` is a **standing**
    credential — the register's own distinction, since `any` is legitimate only
    for a token the platform mints per job. Today there is no such entry and
    this test passes over an empty set; it goes live the moment this repository
    names the token ADR 0022 chose, which is exactly when it is needed.
    """
    standing = [
        credential.name
        for credential in a_register().platform_credentials
        if credential.triggers is not None
    ]
    offenders = [
        f"{path.relative_to(REPO_ROOT)}: {name}"
        for name in standing
        for path in _shipped_files()
        if name in path.read_text(encoding="utf-8", errors="ignore")
    ]
    assert not offenders, "; ".join(offenders)


def test_a_shipped_workflow_that_reaches_a_secret_gates_it_by_environment() -> None:
    """A gate may deploy the environment gate; it may not deploy a bare secret.

    This is the structural half, and the one the requirement is actually about:
    *a gate cannot quietly deploy an authoring environment's convenience into a
    build project.* A workflow fragment that reads `${{ secrets.X }}` with no
    `environment:` on the job is Option 1 — the arrangement whose safety here
    rests on who the six readers are, which is a fact about this organisation
    and not about the repository the gate is deploying into.

    The platform-minted token is exempt: it is not a secret anybody stored, and
    a job cannot be given one that outlives it.
    """
    minted = {
        credential.name
        for credential in a_register().platform_credentials
        if credential.triggers is None
    }
    offenders = []
    for path in _shipped_files():
        if path.suffix not in (".yaml", ".yml"):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        reached = {
            name
            for name in _secret_names(text)
            if name not in minted
        }
        if reached and "environment:" not in text:
            offenders.append(f"{path.relative_to(REPO_ROOT)}: {', '.join(sorted(reached))}")
    assert not offenders, "; ".join(offenders)


def _secret_names(text: str) -> set[str]:
    return set(_SECRET_REFERENCE.findall(text))


def test_the_adopter_guide_asks_for_the_gate_this_repository_does_not_use() -> None:
    """The positive half: an adopter is told their posture, not shown ours.

    `08-adopting.md` is the file an adopter reads. It has to name the
    deployment-environment arrangement, because a reader who reaches for a
    personal access token and finds no steer will use the shape they saw here.
    """
    guide = (REPO_ROOT / "docs/08-adopting.md").read_text(encoding="utf-8")
    assert "deployment environment" in guide.lower()
    assert OWN_POSTURE not in guide


def test_no_shipped_file_declares_a_platform_credential_at_all() -> None:
    """Whatever a gate ships as a starting register names no standing secret.

    Nothing under `plugins/` declares `platform_credentials:` today, and a gate
    that shipped one would hand an adopter a credential name and a set of events
    they never chose — a decision arriving as a default.

    Read as text rather than parsed: the templates carry `{{PLACEHOLDER}}`
    substitutions and are not valid YAML until a gate fills them in, so a parser
    would fail on the files this most needs to read.
    """
    offenders = [
        str(path.relative_to(REPO_ROOT))
        for path in _shipped_files()
        if _DECLARES_CREDENTIALS.search(path.read_text(encoding="utf-8", errors="ignore"))
    ]
    assert not offenders, "; ".join(offenders)


def test_no_platform_limit_reaches_the_register_or_the_plugin() -> None:
    """A plan limit is posture — a fact about one repository's billing.

    ADR 0047 rule 6, and ADR 0022 requirement 6's rule applied to a new kind of
    entry. `platform_limits:` belongs in `deployment-decisions.yaml`, which an
    adopter owns; in `controls.yaml` or under `plugins/` it would ship one
    repository's invoice to everybody who installs the standard.
    """
    shipped = [REPO_ROOT / "controls.yaml", *(REPO_ROOT / "plugins").rglob("*")]
    for path in shipped:
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        assert "platform_limits" not in text, (
            f"{path.relative_to(REPO_ROOT)} mentions platform_limits — that is posture, "
            "and it must not reach the register or anything an adopter installs"
        )
