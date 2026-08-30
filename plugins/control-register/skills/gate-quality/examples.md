# gate-quality — Calibration Examples

## §Strong

LNT-001, TYP-001 and TST-001 deployed with every locus each control declares
actually wired — editor, pre-commit and ci for LNT-001; pre-commit and ci for
TYP-001; ci for TST-001:

- the linter, type checker and test runner are each pinned in a lockfile the
  repository tracks, not merely named in an invocation
- the editor locus is a written configuration file plus, where the register
  declares one, the file-type binding from Step 3b
- `.pre-commit-config.yaml` carries the lint and type-check hooks, and the
  pre-push `tests` hook for TST-001, each stamped with its own control
- the ci workflow runs lint, type check and tests as distinct steps, stamped
- the test invocation was confirmed against the repository (Step 1) rather than
  guessed from the ecosystem's convention
- coverage is reported: files newly brought under the linter's remit are counted
  in the `Coverage:` line, so a config that silently checks nothing is visible
- `register-check run --control LNT-001 --control TYP-001 --control TST-001` run
  afterwards, output shown

Output matches the **Deployed** block in `SKILL.md` § Output.

## §Weak

- a tool invoked as a bare command so it resolves off `PATH`, with the output
  claiming the register's pin — ADR 0020 case C, and the most common way this
  gate is wired but not deployed
- the editor locus skipped because the repository has no editor config yet, with
  LNT-001 still reported as fully deployed
- the test command inferred rather than confirmed, so the ci step runs a suite
  that does not exist and the job passes by running nothing
- the `Coverage:` line omitted, hiding a linter configuration whose include
  globs match no tracked file
- migration skipped: the superseded linter left configured alongside the new
  one, both running, disagreeing
- a failing `register-check` reported as partial. It is a failed deployment;
  the output must say so and nothing may be committed
