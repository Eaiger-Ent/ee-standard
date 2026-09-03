"""A block an adopter pastes carries no trailing `#` comment.

An adopter follows these documents on a Mac, where the login shell is `zsh` and
`interactive_comments` is **off by default**. A `#` pasted into an interactive
`zsh` is not a comment: it is a word, handed to the command as an argument. So
this line, which is correct shell and correct in a script,

    git rev-parse --show-toplevel   # the repository root; cd here if it differs

reported `fatal: ambiguous argument '#'` in a real adoption — and then the `;`
inside the comment ended the command, so `cd here if it differs` ran as a second
one and answered `cd: too many arguments`. The reader is told the instruction is
broken at the first step that checks a precondition, which is the worst place to
lose them.

**The annotation is not the problem; its position is.** A comment on its own
line fails loudly and harmlessly — `zsh: command not found: #` — and leaves the
commands around it intact, which is why standalone lines are allowed here and
are how the shipped file content (a `# renovate:` marker, for one) is written.
A *trailing* comment corrupts the command it annotates, so it is the one this
test bans. Where an annotation is worth keeping, it belongs in the prose above
the block or a table below it, where nothing can paste it.

**Scope is the paste path**, not every fence in the repository. Phase records
and ADRs are write-once history and are read rather than run; the documents
below are the ones an adopter is told to copy from, plus what ships to them
under `plugins/`.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from conftest import REPO_ROOT

#: Documents an adopter pastes out of, relative to the repository root.
_PASTE_PATH = (
    "START-HERE.md",
    "HOW-IT-WORKS.md",
    "README.md",
    "docs/06-devcontainer-setup.md",
    "docs/08-adopting.md",
    "plugins/control-register/templates/devcontainer/README.md",
)

#: Only shell fences. A `#` in YAML or Python is that language's comment and is
#: never pasted into a prompt.
_SHELL_FENCE = re.compile(r"^```(bash|sh|shell|console)\s*$")
_FENCE_END = re.compile(r"^```\s*$")

#: A quoted span, removed before looking for a comment: `grep "#"` is a command
#: that contains a `#`, not a command that is followed by one.
_QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"")


def _paste_path_files() -> list[Path]:
    return [REPO_ROOT / name for name in _PASTE_PATH]


def _shell_lines(text: str) -> list[tuple[int, str]]:
    """Every line inside a shell fence, with its 1-based line number."""
    lines: list[tuple[int, str]] = []
    in_fence = False
    for number, line in enumerate(text.splitlines(), start=1):
        if in_fence:
            if _FENCE_END.match(line):
                in_fence = False
            else:
                lines.append((number, line))
        elif _SHELL_FENCE.match(line):
            in_fence = True
    return lines


def _trailing_comment(line: str) -> bool:
    """A `#` with a command in front of it on the same line."""
    stripped = _QUOTED.sub("", line)
    index = stripped.find("#")
    return index > 0 and bool(stripped[:index].strip())


@pytest.mark.parametrize("path", _paste_path_files(), ids=_PASTE_PATH)
def test_the_document_exists(path: Path) -> None:
    """A path that has moved would exempt itself from the test below."""
    assert path.is_file(), f"{path} is on the paste path and is not there"


@pytest.mark.parametrize("path", _paste_path_files(), ids=_PASTE_PATH)
def test_no_trailing_comment_in_a_shell_block(path: Path) -> None:
    offenders = [
        f"{path.relative_to(REPO_ROOT)}:{number}: {line.strip()}"
        for number, line in _shell_lines(path.read_text(encoding="utf-8"))
        if _trailing_comment(line)
    ]
    assert not offenders, (
        "a trailing `#` comment becomes an argument when pasted into macOS "
        "zsh, which does not set `interactive_comments`. Move the annotation "
        "above the block:\n" + "\n".join(offenders)
    )


#: A command that prints something the reader must then paste, and the command
#: that consumes it. In one fence they are a trap: the consumer runs first.
_PRODUCES_A_VALUE = "claude setup-token"
_CONSUMES_A_VALUE = "add-generic-password"


@pytest.mark.parametrize("path", _paste_path_files(), ids=_PASTE_PATH)
def test_a_block_never_consumes_a_value_it_also_produces(path: Path) -> None:
    """The third command cannot run before the first has printed its input.

    `claude setup-token` opens a browser, waits, and prints a token. The
    `add-generic-password` below it wants that token. In one fence a reader
    pastes all of it, the store command runs with the literal `<paste it here>`
    still in place, and the container fails to start much later with nothing
    pointing back here.

    Splitting them is the whole fix: two fences cannot be pasted as one.
    """
    text = path.read_text(encoding="utf-8")
    offenders = []

    in_fence = False
    fence_start = 0
    body: list[str] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if in_fence:
            if _FENCE_END.match(line):
                joined = "\n".join(body)
                if _PRODUCES_A_VALUE in joined and _CONSUMES_A_VALUE in joined:
                    offenders.append(f"{path.name}:{fence_start}")
                in_fence = False
            else:
                body.append(line)
        elif _SHELL_FENCE.match(line):
            in_fence, fence_start, body = True, number, []

    assert not offenders, (
        f"a shell block at {offenders} runs `{_PRODUCES_A_VALUE}` and "
        f"`{_CONSUMES_A_VALUE}` together. One prints what the other needs, so a "
        "single paste stores the placeholder. Put them in separate fences with "
        "the instruction between them."
    )
