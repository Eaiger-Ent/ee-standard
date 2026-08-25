"""Running a meta-control's verification blocks.

Meta-control verify blocks are commands like `register-check meta GOV-001`.
When a block is exactly that self-referential shape it runs in-process; any
other command runs through the ordinary block runner.

**This is the one in-process assertion the `kind:` taxonomy admits as a
command**, and the schema bounds it to meta-controls naming themselves. The
shape is forced rather than chosen: a meta-control carries a three-valued
`Verdict` (ADR 0016) so that GOV-002 can report "no comparison point" instead of
fabricating a violation, and a `kind: file` assert returns a boolean, which
cannot express it. The miscategorisation that decided verdicts in § E cannot
happen here either — GOV-001 reads `register.controls`, never `meta_controls`.
See `docs/01-register-schema.md` § The one exception.
"""

from __future__ import annotations

import re

from register_check.meta import META_CHECKS
from register_check.register import MetaControl, Register
from register_check.remote import GitHub, NoCredentials, Unresolvable
from register_check.repo import NotAGitRepository, Repo
from register_check.runner import Verdict, run_block, worst

_SELF_META = re.compile(r"^register-check meta (\S+)$")


def run_meta_control(
    meta: MetaControl,
    register: Register,
    repo: Repo,
    remote: GitHub | NoCredentials | Unresolvable | None = None,
) -> tuple[str, str, Verdict, str]:
    """Returns (id, title, verdict, message).

    A meta-control carries a verdict rather than a boolean because "could not
    verify" is a third answer (ADR 0016) — GOV-002 with no comparison point has
    no evidence in either direction, and flattening that to False would report a
    violation the run never observed.

    `remote` is the resolved platform target, handed in rather than resolved
    here for the reason the control runner is handed one: two verdicts in a
    report that described different repositories would be evidence about
    neither. GOV-001 reads it from contract 26; the other two ignore it.
    """
    verdicts: list[Verdict] = []
    messages: list[str] = []
    for block in meta.verify:
        match = _SELF_META.match(block.run or "")
        if match and match.group(1) in META_CHECKS:
            try:
                verdict, message = META_CHECKS[match.group(1)](register, repo, remote)
            except NotAGitRepository:
                raise
            except Exception as exc:
                verdict = Verdict.FAIL
                message = f"could not evaluate: {type(exc).__name__}: {exc}"
        else:
            result = run_block(block, register, repo)
            verdict, message = result.verdict, result.message
        verdicts.append(verdict)
        messages.append(message)
    return meta.id, meta.title, worst(verdicts) if verdicts else Verdict.PASS, "; ".join(messages)
