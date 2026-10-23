#!/usr/bin/env -S uv run python
"""Record what the marketplace published of `control-register`, by digest.

**The problem.** `plugins/control-register/` here and `plugins/control-register/`
in `EqualExperts/ee-skills` are two copies of one plugin. Each submission goes
up through the incubator, comes back changed, and is taken back by hand — five
pull requests in a row (#235 to #242) did nothing else. What said the two
copies agreed was a sentence in `docs/05-promotion.md`, and a sentence is not
checked: when this script was written it said the copies matched "apart from
the docs link each `SKILL.md` names", and three further files differed.

**The record.** `docs/promotion/published.sha256` holds a SHA-256 of every
file the marketplace published, in the format `sha256sum -c` reads, so a
checkout can be verified without this script. `published.json` holds the
version and commit they were read at, and a `differences` map. Each difference
names files by glob, says whether the difference is `owed-upstream` (this
repository is ahead and a submission should carry it) or `by-design` (each copy
is right where it is), and says why. A difference may also give `normalise`
patterns. Every match is blanked on both sides before comparing, so the docs
link can differ and nothing else may. The published side's normalised digests
are in `published.normalised.sha256`.

The digests are not in the JSON because gitleaks (SEC-001) reads
`"templates/adopt/25-credentials.sh": "<64 hex>"` as a generic API key: a
keyword, an assignment, then a high-entropy value. In `sha256sum` order the
path follows the digest, so nothing matches. The alternative was an allow-list
in the scanner's configuration, which loosens a gate to suit a file format.

The idea is harness2's `dependencies/ASSETS.json` plus `check_provenance.py`:
a vendored file is held to a digest, not to a reviewer's memory. Theirs is run
by nothing. This one is run by `tests/test_published_copy.py` on every build.

**Two halves, as SUP-004 has two** (ADR 0041). The test compares this tree with
the record and needs no network, no token and no plugin inventory, so it runs in
CI. Whether the record still describes the marketplace needs the installed
checkout, which this container has and CI does not. That is `--check`, run here.

    uv run python scripts/record_published.py          # re-record from the checkout
    uv run python scripts/record_published.py --check  # does the record still hold?

Re-record after `claude plugin marketplace update ee-skills`, when a take-back
lands. Never edit `files`, `normalised`, `version` or `commit` by hand. They are
a reading, and a hand-written reading is the provenance-stamp failure under
another name. `differences` is the one part a person writes.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_NAME = "control-register"
MARKETPLACE = "ee-skills"
OURS = REPO_ROOT / "plugins" / PLUGIN_NAME
RECORD = REPO_ROOT / "docs" / "promotion" / "published.json"
SUMS = RECORD.with_suffix(".sha256")
NORMALISED_SUMS = RECORD.with_suffix(".normalised.sha256")
STANCES = ("owed-upstream", "by-design")

#: What blanks a `normalise` match. Not empty: two adjacent matches would then
#: collapse into one and a reordering would compare equal.
_BLANK = b"\0normalised\0"


def installed_checkout() -> Path:
    """Where the harness keeps the marketplace checkout, honouring `CLAUDE_CONFIG_DIR`."""
    config = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    return config / "plugins" / "marketplaces" / MARKETPLACE


def tree(root: Path) -> dict[str, bytes]:
    """Every file under `root`, keyed by its POSIX path relative to it.

    Interpreter byproducts are not part of a plugin, and `.git` belongs to the
    marketplace checkout rather than to anything it ships.
    """
    out: dict[str, bytes] = {}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if not path.is_file() or {"__pycache__", ".git"} & set(rel.parts):
            continue
        out[rel.as_posix()] = path.read_bytes()
    return out


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def normalised(content: bytes, patterns: list[str]) -> bytes:
    for pattern in patterns:
        content = re.sub(pattern.encode(), _BLANK, content)
    return content


def read_sums(path: Path) -> dict[str, str]:
    """A `sha256sum` file as path to digest. Two spaces: text mode, as the tool writes."""
    if not path.exists():
        return {}
    pairs = (line.split("  ", 1) for line in path.read_text().splitlines() if line)
    return {name: value for value, name in pairs}


def write_sums(path: Path, digests: dict[str, str]) -> None:
    path.write_text("".join(f"{value}  {name}\n" for name, value in sorted(digests.items())))


def load_record() -> dict[str, Any]:
    """The record as one mapping, whichever file each part is kept in."""
    if not RECORD.exists():
        return {}
    record: dict[str, Any] = json.loads(RECORD.read_text())
    record["files"] = read_sums(SUMS)
    record["normalised"] = read_sums(NORMALISED_SUMS)
    return record


def save_record(record: dict[str, Any]) -> None:
    head = {k: v for k, v in record.items() if k not in ("files", "normalised")}
    RECORD.write_text(json.dumps(head, indent=2) + "\n")
    write_sums(SUMS, record["files"])
    write_sums(NORMALISED_SUMS, record["normalised"])


def difference_for(record: dict[str, Any], path: str) -> tuple[str, dict[str, Any]] | None:
    """The one `differences` entry whose glob matches `path`, if any."""
    found = [(g, d) for g, d in record["differences"].items() if fnmatch.fnmatchcase(path, g)]
    if len(found) > 1:
        raise ValueError(f"{path} matches {len(found)} differences: {[g for g, _ in found]}")
    return found[0] if found else None


def reconcile(record: dict[str, Any], ours: dict[str, bytes]) -> list[str]:
    """Every way this tree departs from the record that the record does not declare.

    Empty is agreement. A declared difference that no longer differs is reported
    too: a `differences` entry outliving its reason is how the sentence this
    replaces went wrong.
    """
    problems: list[str] = []
    published: dict[str, str] = record["files"]
    used_globs: set[str] = set()
    for glob, difference in record["differences"].items():
        if difference.get("stance") not in STANCES:
            problems.append(f"{glob}: stance must be one of {STANCES}")
        if not str(difference.get("why", "")).strip():
            problems.append(f"{glob}: a difference says why")

    for path in sorted(set(published) | set(ours)):
        try:
            match = difference_for(record, path)
        except ValueError as exc:
            problems.append(str(exc))
            continue
        same = path in ours and path in published and digest(ours[path]) == published[path]
        if match is None:
            if not same:
                where = (
                    "here only"
                    if path not in published
                    else ("published only" if path not in ours else "content differs")
                )
                problems.append(f"{path}: {where}, and no difference declares it")
            continue
        glob, difference = match
        used_globs.add(glob)
        patterns = difference.get("normalise") or []
        if same:
            problems.append(f"{path}: identical to the published copy, so `{glob}` is stale")
        elif patterns:
            if path not in ours or path not in published:
                problems.append(f"{path}: `normalise` needs the file on both sides")
                continue
            if not any(re.search(p.encode(), ours[path]) for p in patterns):
                problems.append(f"{path}: no `normalise` pattern of `{glob}` matches it here")
            want = record.get("normalised", {}).get(path)
            if want is None:
                problems.append(f"{path}: no normalised digest recorded; re-record")
            elif digest(normalised(ours[path], patterns)) != want:
                problems.append(f"{path}: differs beyond what `{glob}` normalises")

    for glob in sorted(set(record["differences"]) - used_globs):
        problems.append(f"{glob}: matches no file on either side")
    return problems


def read_published(checkout: Path, previous: dict[str, Any]) -> dict[str, Any]:
    """A fresh record of the checkout, keeping the `differences` a person wrote."""
    plugin = checkout / "plugins" / PLUGIN_NAME
    files = tree(plugin)
    manifest = json.loads(files[".claude-plugin/plugin.json"])
    commit = subprocess.run(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    record: dict[str, Any] = {
        "plugin": PLUGIN_NAME,
        "marketplace": f"EqualExperts/{MARKETPLACE}",
        "version": manifest["version"],
        "commit": commit,
        "files": {path: digest(content) for path, content in files.items()},
        "differences": previous.get("differences", {}),
        "normalised": {},
    }
    for path, content in files.items():
        match = difference_for(record, path)
        if match and match[1].get("normalise"):
            record["normalised"][path] = digest(normalised(content, match[1]["normalise"]))
    return record


def drift(record: dict[str, Any], fresh: dict[str, Any]) -> list[str]:
    """How the record differs from a fresh reading. Empty means it still holds."""
    keys = ("version", "commit", "files", "normalised")
    lines = [f"{key}: recorded and published differ" for key in keys if record[key] != fresh[key]]
    if record["version"] != fresh["version"]:
        lines.insert(0, f"published {fresh['version']}, recorded {record['version']}")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="report drift; write nothing")
    parser.add_argument(
        "--checkout", type=Path, default=None, help="marketplace checkout (default: installed)"
    )
    args = parser.parse_args(argv)
    checkout = args.checkout or installed_checkout()
    previous = load_record()

    if not (checkout / "plugins" / PLUGIN_NAME).is_dir():
        # Exit 3, as register-check uses it: nothing found wrong, nothing verified.
        print(f"UNVERIFIED: no {PLUGIN_NAME} under {checkout}; is {MARKETPLACE} installed?")
        return 3
    fresh = read_published(checkout, previous)

    if args.check:
        lines = drift(previous, fresh) if previous else ["no record yet"]
        for line in lines:
            print(f"DRIFT: {line}")
        if not lines:
            print(f"PASS: the record matches {PLUGIN_NAME}@{fresh['version']} as installed")
        return 1 if lines else 0

    save_record(fresh)
    print(f"recorded {PLUGIN_NAME}@{fresh['version']} ({len(fresh['files'])} files)")
    problems = reconcile(fresh, tree(OURS))
    for problem in problems:
        print(f"  undeclared: {problem}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
