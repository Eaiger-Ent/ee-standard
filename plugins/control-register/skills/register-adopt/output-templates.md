# register-adopt — output templates

Read by `SKILL.md` §Output. Emit the block whose trigger matches how the run ended.

## Adopted

Trigger: Step 5 exited `0` or `3` — or `1`, where every failing block is one
`SKILL.md` Step 6's exception names — and Step 6 committed.

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

Next, in this order — the adoption is not finished until these have run:
  0. <If gate-repo applied the ruleset:> main is protected. /exit, then
     `git switch -c adopt/lint`, which carries this commit, and start claude again
  1. /lint-md            deploys DOC-001, and its package-lock.json clears SUP-001
  2. /lint-yaml          deploys YML-001
  3. /gate-supply-chain  again: lint-md added a node ecosystem SUP-002 must cover
  4. node_modules/ into the root .gitignore, and DOC-001's editor extension into
     .devcontainer/devcontainer.json (docs/08-adopting.md § 3 items 4 and 7)
  5. uv run register-check, then commit and push <the branch, and open a pull
     request | main>
Then the platform acts above. START-HERE.md § 5, *Then, at the same prompt*, is
this list with the reasons.
```

**The Next block is not optional, and it goes last**, where the reader's eye ends.
Number only the steps this run still owes: drop a dispatch-elsewhere skill whose
control already passed, and drop step 3 if no `package.json` was added. When
nothing is owed, write `Next: nothing — every control this plugin can reach holds.`
If Step 5 exited `1`, list the failing blocks verbatim above `Next`, each with the
step that clears it, so a red result reads as expected rather than as a failure.

Omit the `Landed before gate-repo` line when `gate-repo` was not selected: nothing was
committed or pushed before Step 6.

## Failed

Trigger: a gate, or `register-install` at row 5a, reported a failure and the sequence
stopped; or Step 5 exited `2`, or `1` on a control that is not **dispatch elsewhere**
and names none.

```text
register-adopt stopped at <gate>: <the failing block, verbatim>.
<n> gates ran before it and their changes are in the working tree, uncommitted.
Nothing has been committed and nothing has been pushed.
Next: <the act that clears that block>, then /register-adopt --yes again.
START-HERE.md § Your first full report says what each failure means.
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

## Blocked

Trigger: a stop before Step 2 — `register-install` did not install the checker, the
register is missing or fails to load, `--repo` is not a git repository, or a stamp
claims a contract ahead of the installed gate.

```text
register-adopt stopped before planning: <the cause, and the checker's or loader's message verbatim>.
Nothing has been written, committed or pushed.
Next: <the act that clears it — install register-check, fix the register, run in a git repository, or report the AHEAD stamp>.
```
