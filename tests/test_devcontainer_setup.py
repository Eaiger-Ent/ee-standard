"""`setup.sh` installs nothing unpinned and nothing unverified.

The Phase 0.5 criterion was originally *"short enough not to need sectioning —
anything longer is doing work that belongs in a feature"*, and the carried-debt
note named `uv` and `gitleaks` as the work to move. Measurement contradicted the
premise: **neither** available community feature verifies what it downloads.
Both `curl` a GitHub release tarball and extract it, with no checksum, no
signature and no attestation — so moving either would have replaced a
checksum-verified install with an unverified one while *appearing* to strengthen
provenance, because `devcontainer-lock.json` would then pin the feature. The
lock file pins the installer, not the artefact it fetches.

So the criterion was restated as the property it was protecting, and this file is
what makes the restatement mechanical rather than prose. A criterion that reads
well and is checked by nothing is the failure this repository exists to prevent;
swapping an unachievable criterion for an unverified one would be that failure
wearing a better sentence.

The pinning rules are not restated here — `_install_offences` is the same
implementation `ci_installs_frozen` uses for SUP-001, applied to a shell script
instead of a workflow step.
"""

from __future__ import annotations

import re

from conftest import REPO_ROOT
from standard_check.asserts_command import _install_offences, _logical_lines

_SETUP = REPO_ROOT / ".devcontainer/setup.sh"

# A download of an archive or binary, captured so the message can name it.
_DOWNLOAD = re.compile(r"\bcurl\b[^\n]*?-o\s+(?P<target>\S+)")
_VERIFY = re.compile(r"\bsha256sum\b[^\n]*-c|\bcosign\s+verify|\bgpg\s+--verify")


def _script() -> str:
    return _SETUP.read_text(encoding="utf-8")


def test_no_unpinned_package_install() -> None:
    """Every package manager invocation resolves from a pin or a lockfile."""
    offences = list(_install_offences(_script()))
    assert not offences, "; ".join(offences)


def test_every_downloaded_artefact_is_checksum_verified() -> None:
    """A `curl` of a release artefact must be followed by a verification.

    This is the rule that made moving `gitleaks` to a community feature a
    downgrade rather than an upgrade, so it is the rule most worth holding: drop
    it and the difference between this script and the feature disappears, along
    with the reason for keeping the install here.
    """
    text = _script()
    for match in _DOWNLOAD.finditer(text):
        target = match.group("target")
        # The verification must appear after the download and before the file is
        # consumed — in practice, anywhere in the remainder of the script that
        # still mentions the artefact.
        remainder = text[match.end() :]
        assert _VERIFY.search(remainder), (
            f"{_SETUP.name} downloads {target} and never verifies it — a curl "
            "with no checksum is the bottom of the preference ladder in "
            "docs/03-devcontainer.md, whatever it is wrapped in"
        )


def test_the_recorded_checksums_are_the_ones_verified() -> None:
    """Both architectures are covered, not just the one this machine runs.

    The x64 digest is recorded in the register and compared by
    `tool_versions_match_register`. The arm64 digest is compared by nothing —
    recorded as debt rather than left implicit, because a checksum nobody checks
    is the shape of problem this whole phase keeps finding.
    """
    text = _script()
    digests = re.findall(r"GL_SHA=([0-9a-f]{64})", text)
    assert len(digests) == 2, f"expected an x64 and an arm64 digest, found {len(digests)}"
    assert len(set(digests)) == 2, (
        "the two architecture digests are identical, which is a copy-paste"
    )


def test_setup_installs_only_wiring_and_verified_artefacts() -> None:
    """No `curl | sh`, the bottom of the ladder, under any spelling."""
    piped = [
        line.strip()
        for line in _logical_lines(_script())
        if re.search(r"\b(curl|wget)\b[^\n]*\|\s*(sudo\s+)?(ba)?sh\b", line)
    ]
    assert not piped, f"pipe-to-shell install in setup.sh: {piped}"
