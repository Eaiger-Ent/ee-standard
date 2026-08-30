# register-adopt — Calibration Examples

## §Strong

A full adoption run over a repository that had none of the standard deployed:

- the checker was resolved first (Step 0) — every gate's verify step needs it,
  so a run that dispatches gates without it produces unverifiable deployments
- every applicable control appears in the plan, and every control that does not
  appear is reported with the predicate it failed — `IAC-001 (no *.tf)` is a
  reported exclusion, not a silent one
- controls that are not simply "deploy" are handled as themselves: DOC-001 is
  dispatched elsewhere (`lint-md`) and the plan says so
- the plan was shown and confirmed **once**, before anything was written
- gates were dispatched in dependency order, not in the order they happen to be
  listed
- `register-check` was run over the whole register afterwards, its output shown
  and its verdict reported as given — including remote blocks that could not
  answer, and why
- what is still owed by a human (platform acts) is listed
- the commit lists the control IDs deployed and was made only after the verify
  step; it is not pushed

Output matches the **Adopted** block in `SKILL.md` § Output.

The **Cancelled** block is equally strong when confirmation is declined: the
plan was shown and nothing was written.

## §Weak

- a gate dispatched before the plan was confirmed, so a decline leaves changes
  behind
- a control omitted from the plan with no predicate reported, so nobody can tell
  whether it was inapplicable or forgotten
- gates dispatched out of dependency order, so a later gate's verify step fails
  on state an earlier gate had not yet written
- committing before the verify step, or committing when `register-check` failed
- a failure in one gate reported as an overall success because other gates
  passed — the **Failed** block exists precisely to say how many gates ran, that
  their changes sit uncommitted in the working tree, and that nothing was
  committed or pushed
- pushing. This skill commits and stops; the push is a human's decision
