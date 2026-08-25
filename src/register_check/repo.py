"""The repository under audit, as the checker sees it.

Predicates and asserts evaluate against files git knows about — tracked files
plus untracked-but-not-ignored ones — never against self-declared state.
"""

from __future__ import annotations

import fnmatch
import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


class NotAGitRepository(RuntimeError):
    """The target cannot be evaluated, so no verdict about it would be honest."""


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run a git command against `root`, surfacing a missing git binary clearly."""
    try:
        return subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, text=True, check=False
        )
    except FileNotFoundError as exc:  # git absent from PATH
        raise NotAGitRepository("git is not installed or not on PATH") from exc


def require_git_repo(root: Path) -> None:
    """Raise unless `root` is inside a git work tree.

    Predicates are evaluated against git-visible files, so on a non-repository
    every predicate is unsatisfied and every control reports SKIPPED — a clean
    report over a directory the checker never actually examined. Refusing is the
    only honest answer.
    """
    if not root.is_dir():
        raise NotAGitRepository(f"{root} is not a directory")
    result = git(root, "rev-parse", "--is-inside-work-tree")
    if result.returncode != 0 or result.stdout.strip() != "true":
        raise NotAGitRepository(
            f"{root} is not a git repository — predicates are evaluated against "
            "git-visible files, so any report here would describe nothing"
        )


def _git_ls(root: Path, *flags: str) -> set[str]:
    result = git(root, "ls-files", "-z", *flags)
    if result.returncode != 0:
        raise NotAGitRepository(
            f"git ls-files failed in {root}: {result.stderr.strip() or 'unknown error'}"
        )
    return {p for p in result.stdout.split("\0") if p}


@dataclass
class Repo:
    """File-level view of the repository being checked."""

    root: Path
    _tracked: set[str] | None = field(default=None, repr=False)
    _present: set[str] | None = field(default=None, repr=False)

    @property
    def tracked(self) -> set[str]:
        """Paths committed or staged in git."""
        if self._tracked is None:
            self._tracked = _git_ls(self.root)
        return self._tracked

    @property
    def present(self) -> set[str]:
        """Tracked plus untracked-but-not-ignored paths."""
        if self._present is None:
            self._present = _git_ls(self.root, "-co", "--exclude-standard")
        return self._present

    def exists(self, rel: str) -> bool:
        if rel.endswith("/"):
            return any(p.startswith(rel) for p in self.present)
        return rel in self.present

    def glob_basename(self, pattern: str) -> list[str]:
        """Paths whose basename matches the fnmatch pattern."""
        return sorted(p for p in self.present if fnmatch.fnmatch(Path(p).name, pattern))

    def read(self, rel: str) -> str:
        return (self.root / rel).read_text(encoding="utf-8")

    def workflow_files(self) -> list[str]:
        return sorted(
            p
            for p in self.present
            if p.startswith(".github/workflows/") and p.endswith((".yml", ".yaml"))
        )

    def dockerfiles(self) -> list[str]:
        return sorted(
            p
            for p in self.present
            if Path(p).name == "Dockerfile"
            or Path(p).name.startswith("Dockerfile.")
            or p.endswith(".Dockerfile")
        )

    def is_git_repo(self) -> bool:
        try:
            require_git_repo(self.root)
        except NotAGitRepository:
            return False
        return True

    def github_slug(self) -> str | None:
        """`owner/name` per the origin remote, if it is a GitHub URL.

        Where a repository lives is something git already records, so the
        remote asserts read it from there rather than from configuration a
        repository would have to keep in step with reality (ADR 0018). Both
        URL spellings are accepted, and a trailing `.git` is not part of the
        name GitHub's API answers to.
        """
        result = git(self.root, "remote", "get-url", "origin")
        if result.returncode != 0:
            return None
        match = re.search(
            r"github\.com[:/]([A-Za-z0-9._-]+)/([A-Za-z0-9._-]+?)(?:\.git)?/?$",
            result.stdout.strip(),
        )
        return f"{match.group(1)}/{match.group(2)}" if match else None

    def owner(self) -> str | None:
        """The repository owner per the origin remote, if resolvable."""
        slug = self.github_slug()
        return slug.split("/")[0] if slug else None


def strip_jsonc(text: str) -> str:
    """Make JSONC parseable as JSON.

    Strips `//` and `/* */` comments and trailing commas before `}` or `]`,
    preserving string contents. Trailing commas are legal JSONC and `tsc`
    accepts them, so a `tsconfig.json` carrying one must not be a parse error.
    """
    out: list[str] = []
    i, n = 0, len(text)
    in_string = False
    while i < n:
        ch = text[i]
        if in_string:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 1
            elif ch == '"':
                in_string = False
        elif ch == '"':
            in_string = True
            out.append(ch)
        elif ch == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
            continue
        elif ch == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 1
        elif ch == "," and _next_significant(text, i + 1) in "}]":
            pass  # trailing comma — drop it
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def _next_significant(text: str, start: int) -> str:
    """The next character that is neither whitespace nor a comment."""
    i, n = start, len(text)
    while i < n:
        ch = text[i]
        if ch.isspace():
            i += 1
        elif ch == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
        elif ch == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
        else:
            return ch
    return ""


def load_jsonc(path: Path) -> object:
    return json.loads(strip_jsonc(path.read_text(encoding="utf-8")))
