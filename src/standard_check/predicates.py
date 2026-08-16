"""Stack-predicate evaluation.

Predicates are evaluated against the repository's files, never self-declared
(docs/00-concepts.md). The grammar is deliberately closed: an expression the
evaluator does not recognise is a schema error, not a skipped predicate.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from standard_check.repo import Repo


class PredicateSyntaxError(ValueError):
    """An expression outside the closed predicate grammar."""


_ANY = re.compile(r"^any (\S+)(?: files?)? exists$")
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
