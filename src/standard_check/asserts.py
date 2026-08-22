"""The one namespace of in-process assertions.

Both `asserts_file` and `asserts_command` define functions of the same shape —
`(Repo, args) -> AssertResult` — that read repository files and return a
verdict. Nothing about them runs an external process. The split into two
modules is organisational: which files each group reads.

The register previously declared one group as `kind: file` and the other as
`kind: command`, via `standard-check assert <name>` strings. That was theme
**T-2** inside the register: all eight of the second group are file-shape
assertions wearing a command's clothes, and the miscategorisation decided
GOV-001's verdict, because GOV-001 derived reachability from `kind: command`
blocks and ignored `kind: file` ones.

One namespace, resolved by name, is what lets `kind:` mean what it says:

- `kind: file`    — an assertion over repository files, run in-process
- `kind: command` — an external tool, whose exit code is the verdict
- `kind: remote`  — platform API state, in `asserts_remote`
"""

from __future__ import annotations

from standard_check.asserts_command import COMMAND_ASSERTS
from standard_check.asserts_file import FILE_ASSERTS, AssertFn
from standard_check.asserts_remote import REMOTE_ASSERTS

_DUPLICATES = set(FILE_ASSERTS) & set(COMMAND_ASSERTS)
if _DUPLICATES:  # pragma: no cover — a name collision is a programming error
    raise RuntimeError(f"assert name defined in both modules: {sorted(_DUPLICATES)}")

#: Every in-process assertion, by name. The closed set the schema validates
#: `kind: file` blocks against, and the set `standard-check assert <name>`
#: resolves — so an unknown name is a schema error, never a skipped check.
ASSERTS: dict[str, AssertFn] = {**FILE_ASSERTS, **COMMAND_ASSERTS}

__all__ = ["ASSERTS", "REMOTE_ASSERTS", "AssertFn"]
