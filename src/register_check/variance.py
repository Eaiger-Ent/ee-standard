"""Which way a change to a gated config moved: narrowing, loosening, or neither.

[ADR 0040](../../docs/adr/0040-a-declined-classification-is-a-verdict.md).
`00-concepts.md` § Variance has promised a direction since Phase 0 and
`01-register-schema.md` names three cases where the answer is `UNCLASSIFIED`
rather than a guess. Nothing computed either until register contract 33.

**Declining is a verdict here, not a fallthrough.** A classifier that answers
*narrowing* when it does not know launders a guess into a report, and the reader
has no way to tell the two apart. So every path that cannot decide returns
`UNCLASSIFIED` carrying the reason it could not, and the three cases the schema
names are three of those reasons rather than three special cases.
"""

from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass, field
from enum import Enum
from fnmatch import fnmatch
from pathlib import PurePosixPath
from typing import Any

import yaml

from register_check.repo import load_jsonc  # noqa: F401  (kept for parity of readers)


class Direction(Enum):
    """The four answers, ordered by which one a mixed delta reports.

    A change that tightens one key and relaxes another is **not** a wash: the
    relaxation is real, and averaging it away is how a weakening gets merged
    under a green line. So the report takes the strictest reading — loosening
    beats unclassified beats narrowing beats unchanged (ADR 0040 point 4), and
    the order is the enum's own rather than a comparison written at each use.
    """

    LOOSENING = 0
    UNCLASSIFIED = 1
    NARROWING = 2
    UNCHANGED = 3

    def __str__(self) -> str:
        return self.name


#: The reasons a classification declines, named so a reader can tell the case
#: the mechanism cannot decide from the one the register has not been told about.
#: The first three are `01-register-schema.md` § `variance`'s three, in order.
REPLACED = (
    "a member was removed and another added — whether the new one covers the "
    "old is not readable from the config"
)
NO_POLARITY = (
    "the register gives no polarity for this key, so which end is stricter is "
    "not knowable here"
)
NOT_DECLARATIVE = (
    "the config is executable code rather than declarative data, so no delta "
    "can be read from it"
)
UNREADABLE = "the config could not be parsed as data"
SHAPE_CHANGED = "the value changed shape, so there is no delta of one kind to read"


@dataclass(frozen=True)
class KeyDelta:
    """One key's move, and — where it declines — why."""

    key: str
    direction: Direction
    detail: str

    def __str__(self) -> str:
        return f"{self.key}: {self.direction} — {self.detail}"


@dataclass(frozen=True)
class FileDelta:
    """Every key that moved in one config file, and the file's own direction."""

    path: str
    keys: tuple[KeyDelta, ...] = ()
    #: Set when the file as a whole could not be read as data — the third of the
    #: schema's three cases. There are no key deltas to report in that state,
    #: and reporting none would read as "nothing changed".
    whole_file: KeyDelta | None = None

    @property
    def direction(self) -> Direction:
        if self.whole_file is not None:
            return self.whole_file.direction
        if not self.keys:
            return Direction.UNCHANGED
        return min((k.direction for k in self.keys), key=lambda d: d.value)


@dataclass
class Report:
    """Every gated config's delta, and the verdict over all of them."""

    files: list[FileDelta] = field(default_factory=list)
    #: Files the register names that could not be read at the base revision.
    #: An absent baseline and an identical baseline are different answers.
    missing_baseline: list[str] = field(default_factory=list)

    @property
    def direction(self) -> Direction:
        moved = [f.direction for f in self.files]
        if not moved:
            return Direction.UNCHANGED
        return min(moved, key=lambda d: d.value)


#: Suffixes whose config is a program. markdownlint, eslint and their kin all
#: accept one, and a program's effective settings are whatever it computes at
#: run time — the schema's third declining case, and the only one that is a
#: property of the file rather than of its contents.
_EXECUTABLE_SUFFIXES = (".js", ".cjs", ".mjs", ".ts", ".py")


def parse_config(path: str, text: str | None) -> tuple[Any, str | None]:
    """A config file's data, or the reason there is none to read.

    Returns `(document, problem)`. `problem` is set when the file is executable
    code or will not parse — both of which are answers rather than errors, so
    the caller reports them instead of raising.
    """
    if text is None:
        return None, None
    suffix = PurePosixPath(path).suffix
    if suffix in _EXECUTABLE_SUFFIXES:
        return None, NOT_DECLARATIVE
    try:
        if suffix == ".toml":
            return tomllib.loads(text), None
        if suffix == ".json":
            return json.loads(text), None
        return yaml.safe_load(text), None
    except (yaml.YAMLError, tomllib.TOMLDecodeError, json.JSONDecodeError):
        return None, UNREADABLE


def classify_file(
    path: str,
    before: str | None,
    after: str | None,
    polarity: dict[str, str],
    section: str | None = None,
) -> FileDelta:
    """One config file's delta, keyed by the settings inside it.

    `section` narrows to a table within the file — `[tool.ruff]` in a
    `pyproject.toml` that also holds everything else — because a file existing
    is not the same as the tool being configured in it.
    """
    old, old_problem = parse_config(path, before)
    new, new_problem = parse_config(path, after)
    problem = new_problem or old_problem
    if problem is not None:
        return FileDelta(path, whole_file=KeyDelta(path, Direction.UNCLASSIFIED, problem))
    old = _section(old, section)
    new = _section(new, section)
    if old == new:
        return FileDelta(path)
    return FileDelta(path, keys=tuple(_classify(old, new, polarity, prefix="")))


def _section(document: Any, section: str | None) -> Any:
    if section is None or not isinstance(document, dict):
        return document
    cursor: Any = document
    for part in section.split("."):
        if not isinstance(cursor, dict) or part not in cursor:
            return None
        cursor = cursor[part]
    return cursor


def _classify(old: Any, new: Any, polarity: dict[str, str], prefix: str) -> list[KeyDelta]:
    """The deltas between two config values, recursing into mappings.

    A mapping is read as membership *and* as its members' own moves: adding a
    rule narrows, removing one loosens, and doing both is the schema's first
    declining case — whether the new member covers the old is a question about
    the tool's rules, not about the file.
    """
    if isinstance(old, dict) and isinstance(new, dict):
        return _classify_mapping(old, new, polarity, prefix)
    if isinstance(old, list) and isinstance(new, list):
        return _classify_membership(set(map(_hashable, old)), set(map(_hashable, new)), prefix)
    return [_classify_scalar(prefix or "(the whole config)", old, new, polarity)]


def _classify_mapping(
    old: dict[str, Any], new: dict[str, Any], polarity: dict[str, str], prefix: str
) -> list[KeyDelta]:
    deltas: list[KeyDelta] = []
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    if added and removed:
        deltas.append(
            KeyDelta(
                _name(prefix, "members"),
                Direction.UNCLASSIFIED,
                f"{REPLACED} (added {', '.join(added)}; removed {', '.join(removed)})",
            )
        )
    else:
        deltas.extend(_classify_membership(set(old), set(new), prefix))
    for key in sorted(set(old) & set(new)):
        if old[key] == new[key]:
            continue
        deltas.extend(_classify(old[key], new[key], polarity, _name(prefix, key)))
    return deltas


def _classify_membership(old: set[Any], new: set[Any], prefix: str) -> list[KeyDelta]:
    added = sorted(str(x) for x in new - old)
    removed = sorted(str(x) for x in old - new)
    name = _name(prefix, "members")
    if added and removed:
        return [
            KeyDelta(
                name,
                Direction.UNCLASSIFIED,
                f"{REPLACED} (added {', '.join(added)}; removed {', '.join(removed)})",
            )
        ]
    if added:
        return [KeyDelta(name, Direction.NARROWING, f"added {', '.join(added)}")]
    if removed:
        return [KeyDelta(name, Direction.LOOSENING, f"removed {', '.join(removed)}")]
    return []


def _classify_scalar(key: str, old: Any, new: Any, polarity: dict[str, str]) -> KeyDelta:
    """A single setting's move, decided by the polarity the register declares.

    The leaf key is what the register names, not the dotted path: a tool's
    `line_length` is that tool's setting wherever it is nested, and requiring
    the path would make the register repeat the file's shape.
    """
    stricter = polarity.get(key.rsplit(".", 1)[-1])
    if stricter is None:
        return KeyDelta(key, Direction.UNCLASSIFIED, f"{NO_POLARITY} ({old!r} → {new!r})")
    if stricter in ("lower", "higher"):
        if not _numeric(old) or not _numeric(new):
            return KeyDelta(key, Direction.UNCLASSIFIED, f"{SHAPE_CHANGED} ({old!r} → {new!r})")
        tighter = new < old if stricter == "lower" else new > old
    else:
        wanted = stricter == "true"
        if not isinstance(old, bool) or not isinstance(new, bool):
            return KeyDelta(key, Direction.UNCLASSIFIED, f"{SHAPE_CHANGED} ({old!r} → {new!r})")
        tighter = new is wanted
    direction = Direction.NARROWING if tighter else Direction.LOOSENING
    return KeyDelta(key, direction, f"{old!r} → {new!r} (stricter is {stricter})")


def _numeric(value: Any) -> bool:
    """A number, and not a boolean wearing one's clothes.

    `isinstance(False, int)` is `True` in Python, so a ceiling changed from
    `100` to `off` — which YAML reads as `False` — compared as `False < 100` and
    was reported as a **narrowing**. A relaxation reported as a tightening is
    the one outcome ADR 0040 exists to prevent, and it arrived through the
    language rather than through the design.
    """
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _name(prefix: str, key: str) -> str:
    return f"{prefix}.{key}" if prefix else key


def _hashable(value: Any) -> Any:
    """List members compared by identity of content, so unhashable ones survive."""
    return value if isinstance(value, (str, int, float, bool, type(None))) else repr(value)


def gated_configs(register: Any, present: set[str]) -> list[tuple[str, str | None]]:
    """Every config file the register names, with the section that gates it.

    The register's own list rather than a walk of the tree: a file is gated
    config because a control's gate says so, and anything else in the repository
    is a file whose direction this command has no standing to judge.

    **A `config.file` may be a glob** — eslint's is `.eslintrc*`, because the
    tool accepts several spellings — and a glob is not a path. It is expanded
    against the files git can see, so a pattern matching nothing contributes
    nothing. Passing the pattern through as a filename was the first thing this
    command did wrong: `git show <ref>:.eslintrc*` does not fail, it falls back
    to showing the commit, and the report classified two commit messages.
    """
    seen: dict[tuple[str, str | None], None] = {}
    for stack in register.stacks.values():
        for gate in stack.gates.values():
            for location in gate.config:
                for path in _expand(location.file, present):
                    seen[(path, location.section)] = None
    return list(seen)


def _expand(pattern: str, present: set[str]) -> list[str]:
    if not any(ch in pattern for ch in "*?["):
        return [pattern]
    return sorted(p for p in present if fnmatch(p, pattern))


def build_variance(
    read_before: Any,
    read_after: Any,
    register: Any,
    paths: list[tuple[str, str | None]],
) -> Report:
    """Classify each named config's move between two revisions.

    `read_before` and `read_after` return a file's text or `None`. Kept as
    callables so the classifier never learns how to run git, and so a test can
    hand it two strings.
    """
    report = Report()
    for path, section in sorted(paths):
        before = read_before(path)
        after = read_after(path)
        if before is None and after is None:
            continue
        if before is None:
            # An absent baseline and an identical baseline are different
            # answers, and reporting the second for the first would call a whole
            # new config file "unchanged".
            report.missing_baseline.append(path)
            continue
        report.files.append(
            classify_file(path, before, after, register.variance_polarity, section)
        )
    return report


def render_variance(report: Report, against: str) -> str:
    """The report, with every declined key saying why it was declined."""
    lines = [f"variance report — working tree against {against}", ""]
    moved = [f for f in report.files if f.direction is not Direction.UNCHANGED]
    if not moved and not report.missing_baseline:
        lines.append("  no gated configuration moved")
    for file_delta in moved:
        lines.append(f"  {file_delta.path}  {file_delta.direction}")
        entries = [file_delta.whole_file] if file_delta.whole_file else list(file_delta.keys)
        for key in entries:
            if key is None:  # pragma: no cover — guarded by the branch above
                continue
            lines.append(f"      {key}")
    for path in report.missing_baseline:
        lines.append(f"  {path}  NEW — absent at {against}, so there is no delta to classify")
    lines.append("")
    lines.append(f"Overall: {report.direction}")
    if report.direction is Direction.LOOSENING:
        lines.append(
            "A loosening is only a violation where the control's variance is "
            "narrowing-only; this command reports the direction and the "
            "control's own asserts decide."
        )
    return "\n".join(lines)
