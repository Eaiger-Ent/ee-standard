"""Running a meta-control's verification blocks.

Meta-control verify blocks are commands like `standard-check meta GOV-001`.
When a block is exactly that self-referential shape it runs in-process; any
other command runs through the ordinary block runner.
"""

from __future__ import annotations

import re

from standard_check.meta import META_CHECKS
from standard_check.register import MetaControl, Register
from standard_check.repo import Repo
from standard_check.runner import Verdict, run_block

_SELF_META = re.compile(r"^standard-check meta (\S+)$")


def run_meta_control(
    meta: MetaControl, register: Register, repo: Repo
) -> tuple[str, str, bool, str]:
    """Returns (id, title, passed, message)."""
    passed = True
    messages: list[str] = []
    for block in meta.verify:
        match = _SELF_META.match(block.run or "")
        if match and match.group(1) in META_CHECKS:
            block_passed, message = META_CHECKS[match.group(1)](register, repo)
        else:
            result = run_block(block, repo)
            block_passed = result.verdict is Verdict.PASS
            message = result.message
        passed = passed and block_passed
        messages.append(message)
    return meta.id, meta.title, passed, "; ".join(messages)
