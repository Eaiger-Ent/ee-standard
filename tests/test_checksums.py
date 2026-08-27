"""SUP-004 — a pinned digest is the one the project published.

[ADR 0041](../docs/adr/0041-a-pinned-digest-is-checked-against-what-was-published.md).
Renovate's uv bump ([#74](https://github.com/Eaiger-Ent/ee-standard/pull/74))
moved the version at all four sites the register names and left all three sha256
digests at the previous release's values. Every check passed, and what it would
have merged is a container that cannot build.

**Neither half catches that alone**, which is why there are two. #74's two sites
agreed with each other, so the offline reconciliation passes it; only the
comparison against what the project published fails it. The offline half catches
the opposite mistake — one site edited and not the other — which the network
half would pass whenever the edited site happened to be right.

The network here is stubbed. `tests/conftest.py` strips ambient tokens and a
test that reached github.com would be reporting on the internet.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from conftest import REPO_ROOT, a_register, make_repo, register_with
from register_check.asserts_command import tool_digests_match_register
from register_check.asserts_remote import (
    PUBLIC_REMOTE_ASSERTS,
    release_checksums_match_register,
)
from register_check.repo import Repo

UV_X86 = "8681d8921e7d520fb368991dcf5f9c1905b80f5bf2a265a0ed085c8d8e342477"
UV_ARM = "d58030acd26159499ac82f32da12d1b3c12a3a1bfc414232d9082070c03e128d"
#: uv 0.12.5's x86_64 digest — the value #74 left behind.
UV_X86_PREVIOUS = "68a509da24b06b4223a1c0175fb5eb5bc79342b76cbeff0cfe51ac3f5b17b6b2"


def _manifest(**digests: str) -> str:
    """A `sha256sum`-style manifest, in uv's spelling (the binary `*` marker)."""
    return "".join(f"{digest} *{asset}\n" for asset, digest in digests.items())


@pytest.fixture
def published(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """What the projects publish, keyed by URL, replacing the network."""
    served: dict[str, str] = {}

    def fetch(url: str) -> str:
        if url not in served:
            from register_check.remote import Unreadable

            raise Unreadable(f"{url} answered 404")
        return served[url]

    monkeypatch.setattr("register_check.asserts_remote.fetch_text", fetch)
    return served


def _uv_url(version: str = "0.12.6") -> str:
    return f"https://github.com/astral-sh/uv/releases/download/{version}/sha256.sum"


def _gitleaks_url(version: str = "8.30.1") -> str:
    return (
        f"https://github.com/gitleaks/gitleaks/releases/download/v{version}/"
        f"gitleaks_{version}_checksums.txt"
    )


def _serve(served: dict[str, str], register: Any, name: str, url: str) -> None:
    tool = register.tools[name]
    served[url] = _manifest(**tool.checksums.digests(str(tool.version), tool.sha256))


def _serve_both(served: dict[str, str], register: Any) -> None:
    """Both projects' real manifests, for the digests the register pins."""
    _serve(served, register, "uv", _uv_url(str(register.tools["uv"].version)))
    _serve(
        served,
        register,
        "gitleaks",
        _gitleaks_url(str(register.tools["gitleaks"].version)),
    )


# --- the network half ------------------------------------------------------


def test_matching_digests_pass(published: dict[str, str]) -> None:
    register = a_register()
    _serve_both(published, register)
    result = release_checksums_match_register(None, register, {})
    assert result.passed, result.message
    assert "4 pinned digest(s) match" in result.message


def test_the_renovate_case_fails(published: dict[str, str], tmp_path: Path) -> None:
    """#74's exact shape: the version moved and the digest did not.

    The register and every locus agree with each other — which is why the
    offline half passes it, and why this half has to exist.
    """
    def leave_the_digest(document: dict[str, Any]) -> None:
        document["tools"]["uv"]["sha256"] = UV_X86_PREVIOUS

    register = register_with(tmp_path, leave_the_digest)
    _serve_both(published, a_register())  # the release publishes the *current* digest
    result = release_checksums_match_register(None, register, {})
    assert not result.passed
    assert "names a different artefact" in result.message
    assert UV_X86_PREVIOUS[:12] in result.message and UV_X86[:12] in result.message


def test_a_digest_the_release_does_not_have_is_named(
    published: dict[str, str], tmp_path: Path
) -> None:
    """The register naming an asset that release never shipped."""
    register = a_register()
    published[_uv_url()] = _manifest(**{"uv-some-other-target.tar.gz": UV_X86})
    published[_gitleaks_url()] = _manifest()
    result = release_checksums_match_register(None, register, {})
    assert not result.passed
    assert "publishes no digest for" in result.message


def test_an_unreachable_manifest_declines_rather_than_failing(
    published: dict[str, str],
) -> None:
    """No network is not a violation — it is a check that could not be made.

    `Unreadable` propagates to the runner, which reports UNCLASSIFIED. Returning
    `False` here would assert a mismatch the run never observed, which is the
    substitution ADR 0016 refuses.

    The `published` fixture is taken and left empty on purpose: without it this
    test reached github.com and passed for the wrong reason, which is the whole
    hazard the module docstring names.
    """
    from register_check.remote import Unreadable

    assert published == {}
    with pytest.raises(Unreadable):
        release_checksums_match_register(None, a_register(), {})


def test_a_tool_with_no_manifest_passes_and_says_so(
    published: dict[str, str], tmp_path: Path
) -> None:
    """Whether a project publishes checksums is a fact about that project.

    gitleaks publishes a manifest and uv publishes both forms, but a register
    could reasonably pin a tool that publishes neither — and failing the
    conformance run for someone else's release process would make it unpassable
    for a reason nobody in it could fix.
    """
    def drop_the_manifest(document: dict[str, Any]) -> None:
        del document["tools"]["gitleaks"]["checksums"]

    register = register_with(tmp_path, drop_the_manifest)
    published[_uv_url()] = _manifest(
        **{"uv-x86_64-unknown-linux-gnu.tar.gz": UV_X86,
           "uv-aarch64-unknown-linux-gnu.tar.gz": UV_ARM}
    )
    result = release_checksums_match_register(None, register, {})
    assert result.passed, result.message
    assert "publish no manifest and were not compared" in result.message


def test_both_manifest_spellings_are_read(published: dict[str, str]) -> None:
    """gitleaks writes `<digest>  <file>`; uv writes `<digest> *<file>`.

    Reading only one spelling would have covered one pinned tool of two, which
    is the failure mode this whole design was chosen to avoid.
    """
    register = a_register()
    uv, gitleaks = register.tools["uv"], register.tools["gitleaks"]
    assert uv.checksums is not None and gitleaks.checksums is not None
    published[_uv_url()] = "".join(
        f"{d} *{a}\n" for a, d in uv.checksums.digests(str(uv.version), uv.sha256).items()
    )
    published[_gitleaks_url()] = "".join(
        f"{d}  {a}\n"
        for a, d in gitleaks.checksums.digests(
            str(gitleaks.version), gitleaks.sha256
        ).items()
    )
    assert release_checksums_match_register(None, register, {}).passed


def test_the_assert_needs_no_credential() -> None:
    """Declared, so the runner does not short-circuit it to SKIPPED.

    Every other remote assert reads a repository's own platform state and cannot
    answer without a token. This one reads something the platform serves to
    anyone, and reporting SKIPPED (no credentials) over it would be the checker
    declining a question it could have answered.
    """
    assert "release_checksums_match_register" in PUBLIC_REMOTE_ASSERTS


# --- the offline half ------------------------------------------------------


def _repo_with(tmp_path: Path, setup: str) -> Repo:
    return make_repo(tmp_path, {".devcontainer/setup.sh": setup})


def test_this_repository_reconciles() -> None:
    result = tool_digests_match_register(Repo(REPO_ROOT), a_register(), {})
    assert result.passed, result.message
    assert "4 pinned digest(s) reconcile" in result.message


def test_a_digest_no_locus_repeats_is_caught(tmp_path: Path) -> None:
    """The register edited without its loci."""
    result = tool_digests_match_register(
        _repo_with(tmp_path, "# nothing here\n"), a_register(), {}
    )
    assert not result.passed
    assert "no locus repeats" in result.message


def test_a_digest_the_register_does_not_name_is_caught(tmp_path: Path) -> None:
    """A locus edited without the register — the half that catches a bot.

    Both directions are reported in one verdict rather than the first found, so
    fixing one does not reveal the other as a fresh failure.
    """
    stray = "1" * 64
    result = tool_digests_match_register(
        _repo_with(tmp_path, f"UV_SHA={stray}\n"), a_register(), {}
    )
    assert not result.passed
    assert "does not name" in result.message and stray[:12] in result.message
    assert "no locus repeats" in result.message


def test_a_register_pinning_no_manifest_has_nothing_to_reconcile(tmp_path: Path) -> None:
    def drop_them_all(document: dict[str, Any]) -> None:
        for tool in document["tools"].values():
            tool.pop("checksums", None)

    register = register_with(tmp_path, drop_them_all)
    result = tool_digests_match_register(Repo(REPO_ROOT), register, {})
    assert result.passed
    assert "no digest to reconcile" in result.message
