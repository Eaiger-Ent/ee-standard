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


def _git_ls(root: Path, *flags: str) -> set[str]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", *flags],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return set()
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

    def owner(self) -> str | None:
        """The repository owner per the origin remote, if resolvable."""
        result = subprocess.run(
            ["git", "-C", str(self.root), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return None
        match = re.search(r"github\.com[:/]([^/]+)/", result.stdout.strip())
        return match.group(1) if match else None


def strip_jsonc(text: str) -> str:
    """Strip // and /* */ comments from JSONC, preserving string contents."""
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
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def load_jsonc(path: Path) -> object:
    return json.loads(strip_jsonc(path.read_text(encoding="utf-8")))
