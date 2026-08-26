# Say what each write is for, before you make it

Read by every skill in this plugin that writes a file into the target
repository. It is held here, once, rather than repeated in each of them: seven
skills carried byte-identical copies of it
(ADR 0036, in the standard's own repository).

**One line before every file write, and no write without one.** The person
approving it sees a diff and nothing else: not which control it serves, not
which step of how many, not what will check it. The provenance stamp names the
control, but it arrives buried in the middle of the change it is explaining.
Nothing has failed at that point and nothing has passed — a gate deploys
first and verifies last, which is right, and it means the approver is being
asked to accept a change on trust unless you give them the reason first.

Use exactly this shape:

```text
<CONTROL-ID> · step <n>/<total> · <path>
  what it does:  <one clause>
  why now:       <what is absent or wrong without it>
  verified by:   register-check run --control <CONTROL-ID>, at the verify step
```

If a write serves more than one control, name them all. If it is a re-run and
the file already carries this gate's region, say that instead — *"already
deployed at contract N, replacing this gate's own block"* — because
"idempotent" is a claim the approver cannot check from a diff either.
