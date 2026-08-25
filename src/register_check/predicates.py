"""Stack-predicate evaluation.

Predicates are evaluated against the repository's files, never self-declared
(docs/00-concepts.md). The grammar is deliberately closed: an expression the
evaluator does not recognise is a schema error, not a skipped predicate.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from register_check.repo import Repo


class PredicateSyntaxError(ValueError):
    """An expression outside the closed predicate grammar."""


_ANY = re.compile(r"^any (\S+)(?: files?)? exists$")
# `any Dockerfile exists` means whatever BLD-001's assert means by a Dockerfile,
# by construction rather than by coincidence. Compiled as an exact basename
# match, it disagreed with `Repo.dockerfiles()` — which also accepts
# `Dockerfile.*` and `*.Dockerfile` — so a repo whose only container file was
# `Dockerfile.prod` reported BLD-001 SKIPPED (predicate) while the assert called
# directly returned FAIL. A skip that hides a violation the checker can already
# detect is the worst of the verdicts.
_ANY_DOCKERFILE = re.compile(r"^any Dockerfile(?: files?)? exists$")
_DIR = re.compile(r"^(\S+/) exists$")
_FILE = re.compile(r"^(\S+) exists$")


def compile_predicate(expr: bool | str) -> Callable[[Repo], bool]:
    """Compile a register predicate expression into a check over a Repo."""
    if isinstance(expr, bool):
        return lambda _repo: expr
    text = expr.strip()
    if text in {"true", "false"}:
        value = text == "true"
        return lambda _repo: value
    if _ANY_DOCKERFILE.match(text):
        return lambda repo: bool(repo.dockerfiles())
    if match := _ANY.match(text):
        pattern = match.group(1)
        return lambda repo: bool(repo.glob_basename(pattern))
    if match := _DIR.match(text):
        prefix = match.group(1)
        return lambda repo: repo.exists(prefix)
    if match := _FILE.match(text):
        rel = match.group(1)
        return lambda repo: repo.exists(rel)
    raise PredicateSyntaxError(
        f"unrecognised predicate expression {expr!r} — "
        "expected true/false, '<path> exists', '<dir>/ exists', or 'any <glob> exists'"
    )
