"""Every control's `rationale_adr` cites a real decision, at this repository.

The schema accepts a path or an `https://` citation, and the shipped register
uses the second. It has to: `rationale_adr` resolves against the register's own
directory, so a register fetched into a repository that did not author it
failed **every** control on a `docs/` directory it was never going to have.
Phase 4 met that at Step 1 of the first real adoption — fourteen controls,
fourteen `file does not exist`.

What a URL loses is the thing that check was worth: renaming or archiving an ADR
no longer breaks the build. So the check moves here rather than being dropped,
and it is stricter than the one it replaces, because a URL can be wrong in a way
a path cannot — it can name someone else's repository.

It is a test rather than a control for the reason ADR 0022 requirement 6 gives:
how this repository keeps its own records is not what a conformant repository
contains. An adopting register may cite whatever decisions it holds.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from conftest import REPO_ROOT

REGISTER = yaml.safe_load((REPO_ROOT / "controls.yaml").read_text(encoding="utf-8"))
CONTROLS = REGISTER["controls"]
#: The address the register itself names for this project. Read rather than
#: written, so a move to a fork or a mirror is one edit and not fifteen.
ADDRESS = REGISTER["tools"]["register-check"]["install"]["repository"]
PREFIX = f"{ADDRESS}/blob/main/"


def _ids(controls: list[dict[str, object]]) -> list[str]:
    return [str(control["id"]) for control in controls]


@pytest.mark.parametrize("control", CONTROLS, ids=_ids(CONTROLS))
def test_a_citation_names_this_repository(control: dict[str, object]) -> None:
    """A plausible URL to somewhere else would resolve and be wrong.

    The prefix is derived from `tools.register-check.install.repository`, so the
    address has one authority here as it does everywhere else — writing it out
    fourteen times is the second copy this register exists to prevent, and it
    would go on working while the register moved.
    """
    citation = str(control["rationale_adr"])
    assert citation.startswith(PREFIX), (
        f"{control['id']}: rationale_adr is {citation!r}, which does not begin "
        f"with {PREFIX!r} — the address the register names for this project"
    )


@pytest.mark.parametrize("control", CONTROLS, ids=_ids(CONTROLS))
def test_a_citation_resolves_to_a_file_in_this_tree(control: dict[str, object]) -> None:
    """The renamed-ADR check, kept where it can still run.

    A URL's existence is not decidable by the schema and is not pretended to be.
    It is decidable here, against the working tree the URL describes, which is
    the same thing the path form checked and the reason it was worth having:
    an ADR that moved to `archive/` or was renumbered leaves a citation that
    404s for every adopter, and nothing else would say so.
    """
    citation = str(control["rationale_adr"])
    relative = citation[len(PREFIX) :] if citation.startswith(PREFIX) else citation
    assert (REPO_ROOT / relative).is_file(), (
        f"{control['id']}: rationale_adr cites {relative}, which is not a file "
        "in this repository. An ADR that moved leaves a citation that 404s."
    )


def test_no_citation_pins_a_tag() -> None:
    """A version in fourteen URLs is fourteen copies of one release number.

    `blob/main` is deliberate: the tag lives once, in
    `tools.register-check.install.ref`, and a citation that repeated it would
    have to be rewritten at every release or silently point at an older
    decision than the register it ships in.
    """
    for control in CONTROLS:
        citation = str(control["rationale_adr"])
        assert not re.search(r"/blob/v\d+\.\d+\.\d+/", citation), (
            f"{control['id']}: {citation} pins a tag. The tag has one home, "
            "and it is tools.register-check.install.ref."
        )


def test_the_path_form_is_still_accepted(tmp_path: Path) -> None:
    """The schema change is a widening, not a swap.

    An adopting repository that keeps its ADRs beside its register should go on
    using a path, and this asserts the checker still lets it — a rule that
    quietly became URL-only would push every adopter onto a public URL they may
    not have.
    """
    from conftest import write_register
    from register_check.register import load_register

    path = write_register(tmp_path / "elsewhere")
    register, errors = load_register(path)
    assert register is not None, errors
    controls = register.controls
    assert controls, "the fixture register loaded no controls"
    assert all(
        not str(control.rationale_adr).startswith("http") for control in controls
    ), "the fixture register no longer exercises the path form"
