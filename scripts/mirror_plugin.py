#!/usr/bin/env -S uv run python
"""Mirror a plugin published in `ee-skills` into `plugins/`, and record what was taken.

**The problem.** `lint-md` and `lint-yaml` deploy DOC-001 and YML-001, and they
are published only in `EqualExperts/ee-skills`, which is private. ADR 0060 has
this repository's public marketplace serve them as mirrors. A mirror is a copy
of someone else's plugin, and a copy with no record is the one ADR 0044 forbade.
Nobody can say which version it is, or whether it has been edited since.

**The record.** `docs/promotion/mirrored.json` holds, per plugin, the version and
commit it was mirrored at and a SHA-256 of every file as published.
`tests/test_mirrored_plugins.py` fails on a file in `plugins/<name>/` that
differs from it, or that is present on one side only. A mirror is never edited
here (ADR 0060 rule 1), so there is no `owed-upstream` stance. A mirror ahead of
its source is a fork.

**One difference is allowed, and it is declared.** Each published `plugin.json`
lists `"dependencies": ["ee-skills-contribute"]`, a plugin this marketplace does
not serve. So a `differences` entry names the file, says why, and gives `remove`
patterns. The mirror is the published file with every match deleted, and its
digest is recorded as `mirrored_sha256` beside the published one. A `remove`
that no longer matches what was published is reported stale. That is the day
upstream drops the key, and the declaration goes with it.

Unlike `published.json`, the digests sit in the JSON. Its keys are `path` and
`sha256`, and gitleaks (SEC-001) reads a digest as a secret only where the
assignment it follows names a keyword. `record_published.py` keys a digest by
its path, and one of those paths contains `credentials`.

**Two halves, as `record_published.py` has.** The test needs only the
repository, so CI runs it. Whether the mirror is behind needs the installed
`ee-skills` checkout, which CI cannot have. That is `--check`, and it exits `0`
over a mirror that is behind: behind is reported, never enforced (ADR 0038).

    uv run python scripts/mirror_plugin.py lint-md    # re-mirror one plugin
    uv run python scripts/mirror_plugin.py            # re-mirror every one recorded
    uv run python scripts/mirror_plugin.py --check    # is any mirror behind?

Re-mirror after `claude plugin marketplace update ee-skills`, when a release
lands upstream. Never edit `version`, `commit` or `files` by hand. They are a
reading. `differences` is the one part a person writes.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from record_published import digest, installed_checkout, tree

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGINS = REPO_ROOT / "plugins"
RECORD = REPO_ROOT / "docs" / "promotion" / "mirrored.json"
MARKETPLACE = "EqualExperts/ee-skills"


def load_record(path: Path = RECORD) -> dict[str, Any]:
    if not path.exists():
        return {"marketplace": MARKETPLACE, "plugins": {}}
    record: dict[str, Any] = json.loads(path.read_text())
    return record


def save_record(record: dict[str, Any], path: Path = RECORD) -> None:
    path.write_text(json.dumps(record, indent=2) + "\n")


def difference_for(entry: dict[str, Any], path: str) -> dict[str, Any] | None:
    """The one `differences` entry whose glob matches `path`, if any."""
    found = [d for g, d in entry.get("differences", {}).items() if fnmatch.fnmatchcase(path, g)]
    if len(found) > 1:
        raise ValueError(f"{path} matches {len(found)} differences")
    return found[0] if found else None


def mirrored(content: bytes, difference: dict[str, Any] | None) -> bytes:
    """What the mirror holds for a published file: it, less every `remove` match."""
    for pattern in (difference or {}).get("remove", []):
        content = re.sub(pattern.encode(), b"", content)
    return content


def read_upstream(
    checkout: Path, name: str, previous: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, bytes]]:
    """A fresh record entry for `name`, and the files its mirror should hold.

    Keeps the `differences` a person wrote. A JSON file the removal leaves
    unparseable is refused here rather than mirrored.
    """
    files = tree(checkout / "plugins" / name)
    manifest = json.loads(files[".claude-plugin/plugin.json"])
    commit = subprocess.run(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    entry: dict[str, Any] = {
        "version": manifest["version"],
        "commit": commit,
        "differences": previous.get("differences", {}),
        "files": [],
    }
    mirror: dict[str, bytes] = {}
    for path, content in files.items():
        ours = mirrored(content, difference_for(entry, path))
        if path.endswith(".json"):
            json.loads(ours)
        row = {"path": path, "sha256": digest(content)}
        if ours != content:
            row["mirrored_sha256"] = digest(ours)
        entry["files"].append(row)
        mirror[path] = ours
    return entry, mirror


def write_mirror(root: Path, files: dict[str, bytes], source: Path) -> None:
    """Replace `root` with exactly `files`, keeping each published file's mode."""
    if root.exists():
        shutil.rmtree(root)
    for path, content in files.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        shutil.copymode(source / path, target)


def reconcile(entry: dict[str, Any], ours: dict[str, bytes]) -> list[str]:
    """Every way a mirror departs from its record. Empty is agreement."""
    problems: list[str] = []
    for glob, difference in entry.get("differences", {}).items():
        if difference.get("stance") != "by-design":
            problems.append(f"{glob}: a mirror's only stance is by-design (ADR 0060 rule 1)")
        if not str(difference.get("why", "")).strip():
            problems.append(f"{glob}: a difference says why")
        if not difference.get("remove"):
            problems.append(f"{glob}: a difference says what it removes")

    rows = {row["path"]: row for row in entry["files"]}
    used: set[str] = set()
    for path in sorted(set(rows) | set(ours)):
        if path not in rows:
            problems.append(f"{path}: here only, and not in what was published")
            continue
        if path not in ours:
            problems.append(f"{path}: published only, and missing from the mirror")
            continue
        try:
            difference = difference_for(entry, path)
        except ValueError as exc:
            problems.append(str(exc))
            continue
        row = rows[path]
        want = row.get("mirrored_sha256", row["sha256"])
        if difference is not None:
            used.update(g for g in entry["differences"] if fnmatch.fnmatchcase(path, g))
            if "mirrored_sha256" not in row:
                problems.append(f"{path}: nothing published matches its `remove`, so it is stale")
            if any(re.search(p.encode(), ours[path]) for p in difference.get("remove", [])):
                problems.append(f"{path}: still holds what its difference removes")
        elif "mirrored_sha256" in row:
            problems.append(f"{path}: recorded as changed, and no difference declares it")
        if digest(ours[path]) != want:
            problems.append(f"{path}: differs from the record")

    for glob in sorted(set(entry.get("differences", {})) - used):
        problems.append(f"{glob}: matches no file")
    return problems


def behind(entry: dict[str, Any], fresh: dict[str, Any]) -> list[str]:
    """How a recorded mirror differs from what is published now. Empty means current."""
    lines = []
    if entry["version"] != fresh["version"]:
        lines.append(f"published {fresh['version']}, mirrored {entry['version']}")
    if entry["files"] != fresh["files"]:
        lines.append("files: mirrored and published differ")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("plugins", nargs="*", help="plugins to mirror (default: every recorded)")
    parser.add_argument("--check", action="store_true", help="report what is behind; write nothing")
    parser.add_argument(
        "--checkout", type=Path, default=None, help="ee-skills checkout (default: installed)"
    )
    parser.add_argument("--plugins-dir", type=Path, default=PLUGINS, help=argparse.SUPPRESS)
    parser.add_argument("--record", type=Path, default=RECORD, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    checkout = args.checkout or installed_checkout()
    record = load_record(args.record)
    names = args.plugins or sorted(record["plugins"])
    missing = [n for n in names if not (checkout / "plugins" / n).is_dir()]
    if not names or missing:
        # Exit 3, as register-check uses it: nothing found wrong, nothing verified.
        print(f"UNVERIFIED: no {', '.join(missing) or 'plugin'} under {checkout}")
        return 3

    if args.check:
        for name in names:
            entry = record["plugins"].get(name)
            fresh, _ = read_upstream(checkout, name, entry or {})
            lines = behind(entry, fresh) if entry else ["not mirrored yet"]
            for line in lines:
                print(f"BEHIND: {name}: {line}")
            if not lines:
                print(f"CURRENT: {name}@{fresh['version']}")
        return 0

    problems: list[str] = []
    for name in names:
        fresh, files = read_upstream(checkout, name, record["plugins"].get(name, {}))
        write_mirror(args.plugins_dir / name, files, checkout / "plugins" / name)
        record["plugins"][name] = fresh
        print(f"mirrored {name}@{fresh['version']} ({len(files)} files)")
        problems += [f"{name}: {p}" for p in reconcile(fresh, tree(args.plugins_dir / name))]
    save_record(record, args.record)
    for problem in problems:
        print(f"  {problem}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
