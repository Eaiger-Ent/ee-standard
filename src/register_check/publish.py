"""The register an adopter fetches, derived from the one this repository uses.

`controls.yaml` is two documents (ADR 0048). Most of it is the same for every
repository; a few fields are facts about *this* one, and shipping those made an
adopter fail SUP-001 on files they were never going to have and made `gate-repo`
refuse a ruleset requiring a job their repository does not produce.

So an entry this repository owns carries a trailing `# local-only` marker, and
the published register is this file with those lines removed.

**Text in, text out, deliberately.** Parsing and re-dumping YAML would drop every
comment in `controls.yaml`, and that file is more comment than data — the
reasoning behind each control is the thing an adopter most needs. The same
argument `gate-build` makes for merging `devcontainer.json` as text.

The marker is a trailing comment rather than a line above the entry, which is
what ADR 0048's example showed. A preceding comment has to be bound to something,
and in a file where nearly every entry already carries explanatory comments above
it, that binding is ambiguous to a reader and fragile to an edit. A trailing
marker is on the line it governs.
"""

from __future__ import annotations

import re
from pathlib import Path

#: An entry this repository keeps and does not publish. Anchored to end-of-line
#: so it cannot match the word appearing inside prose.
LOCAL_ONLY = re.compile(r"\s+#\s*local-only\s*$")

#: The fields whose values may legitimately differ between repositories, and so
#: may carry a marker. ADR 0048 rule 1: everything else defines what conformant
#: *means*, and publishing a policy other than the one enforced here would be
#: indefensible. `docs/08-adopting.md` § 3.7 names the first four.
MARKABLE_FIELDS = frozenset(
    {"pinned_at", "ecosystems", "release_repo", "toolchain", "required_checks"}
)

PUBLISHED = "controls.published.yaml"

#: What the published file says about itself, so a reader who opens it knows it
#: is generated before they edit it.
HEADER = """# GENERATED — do not edit. Run `register-check publish` instead.
#
# The register an adopter fetches, derived from `controls.yaml` by removing the
# entries this repository marks `# local-only` (ADR 0048). Those are facts about
# this repository — the workflows it happens to have, the jobs it happens to
# run — and shipping them made an adopter fail on files they could not have.
#
# Everything else here is identical to `controls.yaml`, comments included.
"""


def local_only_lines(text: str) -> list[tuple[int, str]]:
    """Every marked line, with its 1-based number."""
    return [
        (n, line)
        for n, line in enumerate(text.splitlines(), 1)
        if LOCAL_ONLY.search(line)
    ]


def field_of(text: str, line_number: int) -> str | None:
    """The register field a marked list entry belongs to.

    Walks back to the nearest less-indented `key:` line, which is the field the
    entry is an item of. Enough for the shapes `controls.yaml` uses — a marked
    line is always an item of a list under a named key — and it fails closed by
    returning None rather than guessing.
    """
    lines = text.splitlines()
    entry = lines[line_number - 1]
    indent = len(entry) - len(entry.lstrip())
    for candidate in reversed(lines[: line_number - 1]):
        stripped = candidate.strip()
        if not stripped or stripped.startswith("#"):
            continue
        candidate_indent = len(candidate) - len(candidate.lstrip())
        if candidate_indent < indent and stripped.endswith(":"):
            return stripped.rstrip(":").lstrip("- ")
    return None


def derive(text: str) -> str:
    """`text` with every `# local-only` line removed, and a header explaining it."""
    kept = [line for line in text.splitlines() if not LOCAL_ONLY.search(line)]
    return HEADER + "\n".join(kept) + "\n"


def publish(repo_root: Path) -> Path:
    """Write the published register beside the source one. Returns its path."""
    source = repo_root / "controls.yaml"
    target = repo_root / PUBLISHED
    target.write_text(derive(source.read_text(encoding="utf-8")), encoding="utf-8")
    return target
