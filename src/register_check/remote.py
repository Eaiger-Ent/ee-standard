"""Reading platform state, and refusing to guess when it cannot be read.

A `kind: remote` block asks GitHub a question no file can answer: not what the
repository *records*, but what the platform *enforces*. Everything specific to
getting that answer lives here, so the asserts beside it read an API response
rather than a transport.

Three refusals are distinguished, because they call for different acts by
different people (ADR 0021):

- **No token at all.** Nobody asked, so nothing is known. The block reports
  SKIPPED (no credentials), which is what the operator sees when remote
  verification was never configured.
- **A token that was rejected, or an answer that does not settle the
  question.** Somebody asked and did not get an answer. That is UNCLASSIFIED —
  a distinct fact, and one an operator has to act on rather than configure.
- **An answer.** PASS or FAIL, and only then.

Both refusals deny the run a `0` exit (ADR 0016), so neither can be mistaken
for a pass. The distinction is for the reader, not for the exit code.

Transport is the standard library against a bearer token, not `gh`: an adopter's
CI runner has `GITHUB_TOKEN` in the environment, and requiring a binary as well
would make Tier-1 verification unanswerable on a machine that could answer it.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from register_check.repo import Repo

GITHUB_API = "https://api.github.com"

#: Where a token is looked for, in order. `GITHUB_TOKEN` is what GitHub Actions
#: injects and what `gh` exports; `GH_TOKEN` is the other spelling `gh` accepts.
#: Reading both means an adopter authenticated either way needs no extra step.
TOKEN_VARIABLES = ("GITHUB_TOKEN", "GH_TOKEN")

#: How long to wait for the API before treating silence as unreadable. A remote
#: block that hangs would stall an audit that has verdicts for everything else.
TIMEOUT_SECONDS = 15

#: The endpoint asked when the question is about the **credential** rather than
#: about the repository. `/rate_limit` answers for any valid token, is exempt
#: from rate limiting itself, and needs no permission on the repository — so a
#: token that cannot see this repository can still be asked when it expires,
#: which is a fact about the token and not about what it may read.
CREDENTIAL_PROBE_PATH = "/rate_limit"

#: When the presented token expires, as GitHub reports it. Absent when the
#: credential does not expire at all — which is a fact about the credential
#: only when the instrument is one that would otherwise say (see
#: `OAUTH_SCOPES_HEADER`).
TOKEN_EXPIRY_HEADER = "github-authentication-token-expiration"

#: Present on responses to a **classic** personal access token, and absent for
#: fine-grained tokens and app installation tokens. The header's presence
#: therefore identifies the instrument (ADR 0022 requirement 4).
OAUTH_SCOPES_HEADER = "x-oauth-scopes"

#: How GitHub Actions announces itself to everything running in a job. Read
#: rather than inferred: SEC-003 is a `locus: [ci]` control, and the credential
#: a developer's shell holds is not the credential CI carries — answering the
#: control from it would report on the wrong token (ADR 0018: a platform's own
#: variable is not a rule a repository could reasonably need to differ).
CI_VARIABLE = "GITHUB_ACTIONS"


def runs_in_github_actions(environ: Mapping[str, str] | None = None) -> bool:
    environ = os.environ if environ is None else environ
    return environ.get(CI_VARIABLE, "").strip().lower() == "true"


class Unreadable(RuntimeError):
    """The platform was asked and did not settle the question.

    Raised for a rejected token, an invisible repository, a network failure, and
    for an answer that is well-formed but says nothing about the control — a
    repository whose `security_and_analysis` is `null` because the caller is not
    an administrator has not told us push protection is off. Reporting FAIL
    there would assert a violation on the strength of not having looked.
    """


@dataclass(frozen=True)
class NoCredentials:
    """No token was offered, so no remote question was asked."""

    message: str


@dataclass(frozen=True)
class Unresolvable:
    """A token was offered, and there is no repository to ask it about.

    Distinct from `NoCredentials` because the remedy differs: this one needs a
    repository named, not a token supplied. It is UNCLASSIFIED rather than a
    skip, for the same reason `Unreadable` is — somebody asked.
    """

    message: str


@dataclass(frozen=True)
class GitHub:
    """One repository's platform state, as the API will answer for it."""

    slug: str
    token: str
    api: str = GITHUB_API

    def get(self, path: str) -> Any:
        """A GET against the API, or `Unreadable` if it does not answer.

        Every failure mode collapses here rather than at the call sites: an
        assert's job is to decide a control, and it can only do that once there
        is something to decide from.
        """
        return self._fetch(path)[0]

    def headers(self, path: str) -> Mapping[str, str]:
        """The response headers of a GET, keyed in lower case.

        A few of GitHub's answers are about the **credential** rather than about
        the repository, and they arrive in headers rather than in the body:
        when the token expires, and whether it is a classic personal access
        token. The body is discarded here for the same reason `get` discards
        the headers — a caller should read one thing.

        HTTP header names are case-insensitive and GitHub has shipped more than
        one casing of the expiry header, so they are lower-cased on the way in
        rather than matched as sent.
        """
        return self._fetch(path)[1]

    def _fetch(self, path: str) -> tuple[Any, Mapping[str, str]]:
        request = urllib.request.Request(
            f"{self.api}{path}",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "register-check",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                body = response.read().decode("utf-8")
                received = {str(k).lower(): str(v) for k, v in response.headers.items()}
        except urllib.error.HTTPError as exc:
            raise Unreadable(_http_explanation(exc.code, path, self.slug)) from exc
        except urllib.error.URLError as exc:
            raise Unreadable(f"could not reach {self.api}{path}: {exc.reason}") from exc
        except TimeoutError as exc:
            raise Unreadable(
                f"{self.api}{path} did not answer within {TIMEOUT_SECONDS}s"
            ) from exc
        try:
            return json.loads(body), received
        except ValueError as exc:
            raise Unreadable(f"{path} returned a body that is not JSON: {exc}") from exc


def fetch_text(url: str) -> str:
    """A public URL's body, or `Unreadable` if it does not answer.

    No `Authorization` header, because the thing this reads is public: a
    project's release checksum manifest (ADR 0041). Presenting a credential to
    fetch it would make the answer depend on whether one was available, which is
    exactly the distinction `NoCredentials` exists to keep — a check that *can*
    answer without a token must not report SKIPPED for want of one.

    Failure is `Unreadable` rather than an empty string for the reason every
    other reader here uses it: not reaching the network teaches nothing about
    the repository, and a verdict from it would be invented.
    """
    request = urllib.request.Request(url, headers={"User-Agent": "register-check"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            body: str = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise Unreadable(f"{url} answered {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise Unreadable(f"could not reach {url}: {exc.reason}") from exc
    except TimeoutError as exc:
        raise Unreadable(f"{url} did not answer within {TIMEOUT_SECONDS}s") from exc
    return body


def _http_explanation(code: int, path: str, slug: str) -> str:
    """What an operator has to do about this status, not merely what it was.

    401 and 403 are UNCLASSIFIED rather than SKIPPED (no credentials) on
    purpose. A token that was presented and rejected is a different fact from no
    token: the first needs the token fixed, the second needs one supplied, and
    collapsing them tells the operator to do the wrong thing.
    """
    if code == 401:
        return (
            f"the token was rejected for {path} (401) — it is invalid or expired; "
            "this is a token to fix rather than one to supply"
        )
    if code == 403:
        return (
            f"the token lacks the scope for {path} (403) — reading {slug}'s protection "
            "state needs a token with repository administration read access"
        )
    if code == 404:
        return (
            f"{path} is not visible to this token (404) — either {slug} does not exist "
            "or the token cannot see it, and neither says anything about the control"
        )
    return f"{path} returned HTTP {code}"


def resolve(
    repo: Repo,
    override: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> GitHub | NoCredentials | Unresolvable:
    """The GitHub repository a remote block asks about, and the token to ask with.

    Identity comes from the origin remote, because git already holds it and a
    second copy in configuration would drift the day a repository moves
    (ADR 0018). `--github-repo` overrides it for the cases inference cannot
    serve: a fork, a mirror, and a checkout being audited on behalf of another
    repository.
    """
    environ = os.environ if environ is None else environ
    slug = override or repo.github_slug()
    token = next((environ[name] for name in TOKEN_VARIABLES if environ.get(name)), None)
    if token is None:
        return NoCredentials(
            "no GitHub token in the environment (looked for "
            + ", ".join(TOKEN_VARIABLES)
            + ") — platform state was not read, and nothing here claims it was"
        )
    if slug is None:
        # A token with nothing to ask about. Not "no credentials": credentials
        # were offered, and the question could not be formed.
        return Unresolvable(
            "cannot tell which GitHub repository to ask about — the origin remote is "
            "absent or is not a GitHub URL; name one with --github-repo owner/name"
        )
    if not valid_slug(slug):
        return Unresolvable(
            f"{slug!r} is not a GitHub owner/name — a malformed target would send this "
            "repository's question to some other URL"
        )
    return GitHub(slug=slug, token=token)


SLUG = re.compile(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")


def valid_slug(value: str) -> bool:
    return bool(SLUG.match(value))
