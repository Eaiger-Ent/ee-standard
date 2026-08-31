"""The `ee-control:` stamp: one parser, for everything that reads one.

`docs/00-concepts.md` § The provenance stamp makes "deployed but stale"
computable, and the format is the join between four readers: the gate skill that
writes a stamp, the assert that reads it back, the test that checks every stamp
in this repository is well-formed, and Phase 5's sweep. Four readers is four
chances for a regex to drift, and a stamp format that means something slightly
different to the writer than to the reader is the failure this repository
exists to prevent — so the pattern is defined once, here.

What a stamp records, and why each field:

    # ee-control: SEC-001  ee-skill: gate-secrets@0.1.0  gate-contract: 5
    #   register: v0.23.0  register-contract: 30            (one line in the file)

`register` moves for any change including a typo in a comment; `register-contract`
moves only when a control's `rung`, `verify`, `variance` or `applies_to` changes
— that is, only when what gets deployed could differ. A reader comparing
versions alone cannot tell whether anything they hold is affected; with the
contract they can.

`gate-contract` is the same argument about the *gate* rather than the register
(ADR 0038): `gates.<gate>.contractVersion` from the plugin's `deploys.json`,
read by the gate as it writes. It moves only when what that gate writes changes,
so a documentation release of the plugin recommends nothing. The skill version
beside it cannot serve: eight skills share one `plugin.json` version, so it is
not a per-gate fact at all.

It is **optional**, and its absence is a state rather than a default. Every
stamp written before ADR 0038 lacks it, and those deployments are *unrecorded* —
neither current nor stale — until the gate next deploys. Filling one in by hand
would record a redeployment that did not happen.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from register_check.repo import Repo, git

#: The bare marker. Searched for on its own where a stamp that is *present but
#: malformed* must be found rather than missed — a defect in the deployment, not
#: a staleness signal.
MARKER = "ee-control:"

_STAMP = re.compile(
    r"ee-control:\s*(?P<control>\S+)\s+"
    r"ee-skill:\s*(?P<skill>\S+?)@(?P<skill_version>\S+)\s+"
    r"(?:gate-contract:\s*(?P<gate_contract>\d+)\s+)?"
    r"register:\s*v(?P<register_version>\d+\.\d+\.\d+)\s+"
    r"register-contract:\s*(?P<register_contract>\d+)"
)

#: What a well-formed stamp looks like, for error messages that show rather than
#: describe. Kept beside the pattern so the two cannot disagree.
EXPECTED = (
    "ee-control: ID  ee-skill: name@version  [gate-contract: N]  "
    "register: vX.Y.Z  register-contract: N"
)


@dataclass(frozen=True)
class Stamp:
    control: str
    skill: str
    skill_version: str
    register_version: str
    register_contract: int
    #: The gate's deployment contract at the moment it wrote this artefact, or
    #: `None` for a stamp written before ADR 0038 added the field. `None` is
    #: "nobody recorded it", never "contract zero" — the two are reported
    #: differently and a default would erase the distinction.
    gate_contract: int | None = None


def stamps_in(text: str) -> list[Stamp]:
    """Every well-formed stamp in a file's contents.

    A file may carry more than one: `.pre-commit-config.yaml` holds hooks for
    five controls, and a skill that owns one of them stamps its own hook rather
    than the top of the file, which would claim the other four.
    """
    return [
        Stamp(
            control=match.group("control"),
            skill=match.group("skill"),
            skill_version=match.group("skill_version"),
            register_version=match.group("register_version"),
            register_contract=int(match.group("register_contract")),
            gate_contract=(
                int(match.group("gate_contract"))
                if match.group("gate_contract") is not None
                else None
            ),
        )
        for match in _STAMP.finditer(text)
    ]


#: A Markdown code-fence delimiter: three or more backticks or tildes, indented
#: by at most three spaces. CommonMark's rule, and the whole basis of ADR 0046 —
#: a fence is how Markdown says *display this text* rather than *this text is in
#: force*.
_FENCE = re.compile(r"^ {0,3}(?P<char>`{3,}|~{3,})(?P<info>.*)$")

#: Documents this repository writes. A stamp quoted in one of these is an
#: example when it sits inside a fence; anywhere else it is a live comment in an
#: artefact. ADR 0046 § What this does not do records why the rule stops here.
_MARKDOWN_SUFFIXES = (".md", ".markdown")


def _closes(match: re.Match[str], opening: str) -> bool:
    """Whether this fence closes `opening`.

    Same character, at least as long, and no info string — the third is what
    makes ```` ```bash ```` an opening rather than a close.
    """
    fence = match.group("char")
    return (
        not match.group("info").strip()
        and fence[0] == opening[0]
        and len(fence) >= len(opening)
    )


def without_fenced_blocks(text: str) -> str:
    """`text` with every fenced code block blanked, lines preserved.

    Blanked rather than deleted so a caller reporting a line number still gets
    the right one. The opening fence closes only on a fence of the same
    character and at least the same length, which is what keeps a ``` inside a
    ```` block from ending it early — `docs/17-adopter-onboarding-review.md`
    nests them exactly that way.

    An unclosed fence runs to the end of the file. That is the conservative
    direction: the alternative reads a truncated document's example as a
    deployed artefact, which is the failure ADR 0046 exists to stop.
    """
    out: list[str] = []
    closing: str | None = None
    for line in text.splitlines():
        match = _FENCE.match(line)
        if closing is None:
            # An opening fence may carry an info string; a closing one may not.
            if match:
                closing = match.group("char")
                out.append("")
                continue
            out.append(line)
        else:
            if match and _closes(match, closing):
                closing = None
            out.append("")
    return "\n".join(out)


def _files_with_marker(repo: Repo) -> list[str]:
    """Tracked files containing the marker, found by git rather than by reading.

    `git grep` is the whole repository in one subprocess. Reading every tracked
    file instead is correct and does not scale: a monorepo would pay a full-tree
    read on every conformance run, for a marker that appears in a handful of
    files. Falling back to the read is deliberate — a grep that fails for a
    reason this code cannot anticipate must not turn into "no artefact was
    stamped", which is a verdict rather than an error.
    """
    result = git(repo.root, "grep", "-l", "-I", "--cached", "-e", MARKER)
    if result.returncode not in (0, 1):  # 1 is "no matches", not a failure
        return sorted(repo.tracked)
    return [path for path in result.stdout.split("\n") if path]


def stamps_by_file(repo: Repo) -> dict[str, list[Stamp]]:
    """Well-formed stamps in the repository's tracked files, by path.

    Tracked only. An artefact git does not track was not deployed into this
    repository in any sense a reader can act on, and a stamp in an untracked
    scratch file is not evidence of anything.
    """
    found: dict[str, list[Stamp]] = {}
    for path in sorted(_files_with_marker(repo)):
        try:
            text = repo.read(path)
        except OSError, UnicodeDecodeError:
            continue  # a binary or unreadable file carries no stamp
        if path.endswith(_MARKDOWN_SUFFIXES):
            # A document explaining the stamp format is not a deployment
            # (ADR 0046). This repository's own ADR 0038 must show a stamp
            # without a `gate-contract` to explain the field it adds, and
            # counting it kept `gate-secrets` at UNRECORDED for ever — and let
            # SEC-001's read-back pass on prose alone, which was the worse half.
            text = without_fenced_blocks(text)
        stamps = stamps_in(text)
        if stamps:
            found[path] = stamps
    return found
