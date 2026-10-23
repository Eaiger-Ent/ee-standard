# register-adopt — output templates

Read by `SKILL.md` §Output. Emit the block whose trigger matches how the run ended.

## Adopted

Trigger: Step 5 exited `0` or `3`, and Step 6 committed.

```text
register-adopt deployed <n> controls in <repo>.
  gate-build         BLD-001, DEV-001
  gate-supply-chain  SUP-001, SUP-002, SUP-003
  gate-secrets       SEC-001, SEC-002, SEC-003
  gate-quality       LNT-001, TYP-001, TST-001
  gate-repo          CI-001
  not applicable     IAC-001 (no *.tf)
  dispatch elsewhere DOC-001 (lint-md)
Verified: register-check → exit <code>
  local loci PASS; <remote blocks that could not answer, and why>.
Still owed by a human: <platform acts>.
Landed before gate-repo: <sha> — pushed, so the protected branch already holds it.
Committed: <sha> — not pushed.
```

Omit the `Landed before gate-repo` line when `gate-repo` was not selected: nothing was
committed or pushed before Step 6.

## Failed

Trigger: a gate, or `register-install` at row 5a, reported a failure and the sequence
stopped; or Step 5 exited `1` or `2`.

```text
register-adopt stopped at <gate>: <the failing block, verbatim>.
<n> gates ran before it and their changes are in the working tree, uncommitted.
Nothing has been committed and nothing has been pushed.
```

When the stop is at `gate-repo`, or at Step 5 after it, the earlier gates' work was
committed and pushed before `gate-repo` ran. Replace the last two lines with:

```text
<n> gates ran before gate-repo; their work landed as <sha>, pushed.
<what gate-repo applied before it stopped, or "no ruleset was applied">.
```

## Cancelled

Trigger: **Cancel** at Step 3.

```text
register-adopt showed the plan and wrote nothing.
```
