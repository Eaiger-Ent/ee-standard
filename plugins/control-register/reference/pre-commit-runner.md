# Before you write a pre-commit hook, make sure something runs it

Read by every gate in this plugin that writes into `.pre-commit-config.yaml`.
It is held here, once, rather than repeated in each of them: five gates carried
byte-identical copies of it until the sixth copy pushed `gate-quality` past the
skill-preflight line ceiling
(ADR 0036, in the standard's own repository).

**A hook in `.pre-commit-config.yaml` is a statement of intent; the runner and
the installed git hook are whether anything happens.** Five gates write into
that file and, until Phase 4, none of them installed the thing that reads it —
so the consumer repository finished its adoption with every gate reporting its
`pre-commit` locus wired, `pre-commit` absent from the project, no
`.git/hooks/pre-commit`, and a deliberately malformed commit sailing straight
through. The checker reported the locus wired throughout, because it reads the
config file, which is the right thing for it to read and not the same claim.

So before writing your hook, and idempotently — whichever gate runs first does
it and the rest find it done:

1. **Is `pre-commit` a dev dependency of this repository?** Reach it the way its
   locus will: `uv run pre-commit --version`, or the equivalent for the lockfile
   present. If it is not there, add it with
   `ecosystems.<eco>.add_dev_dependency` — the register's spelling, never one
   you compose yourself.
2. **Is the git hook installed?** `test -x .git/hooks/pre-commit`. If not, run
   `pre-commit install` through the same package manager. `.git/hooks/` is
   untracked, so this is per clone and per container, and the devcontainer
   template's `setup.sh` does it at container-create for anyone who starts fresh.
3. **Say what you found**, in the write narration `write-narration.md`
   prescribes. "pre-commit was absent and has been added" is a different fact
   from "already present", and the second is worth one line rather than none.

No control verifies step 2, and that is a stated boundary rather than an
oversight: `.git/hooks/` is untracked and CI legitimately has no hooks
installed. Step 1 *is* tracked — it is a line in a lockfile — and the template's
`check-auth.sh` reports a missing hook on every container start.
