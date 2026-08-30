# gate-iac — Calibration Examples

## §Strong

IAC-001 deployed into a repository containing Terraform, with both declared loci
wired:

- every analyser the register names (for example `checkov`, `tflint`) is pinned
  at the version the register gives, and installed at that version
- `.pre-commit-config.yaml` has one `<tool>-iac` hook that runs the analysers
  over all Terraform, stamped with IAC-001, this skill and version, and the
  register's version and contract
- the ci locus is reached by the repository's existing full audit, and the skill
  reports that rather than adding a duplicate step
- what this replaces was migrated, not left alongside — a superseded ad-hoc
  `terraform validate` step is removed in the same run, not left to drift
- `register-check run --control IAC-001` was run afterwards and its verdict
  reported as given

Output matches the **Deployed** block in `SKILL.md` § Output.

Equally strong: the wiring verifies and the analysers then report findings in
the repository's own Terraform. That is the gate working on its first run, and
the **Findings rather than a failure** block is the correct report — the
findings are not this skill's failure and must not be presented as one.

## §Weak

- an analyser wired but unpinned, with the output still claiming IAC-001
  deployed — an invocation that reaches whatever is on `PATH` is not a pin
- only the pre-commit locus wired, ci silently skipped, while the output lists
  both
- analyser findings reported as a failed deployment, or a failed
  `register-check` reported as findings — the two blocks are not
  interchangeable, and conflating them hides a broken deployment
- an `UNCLASSIFIED` verdict from `register-check` smoothed into a pass instead
  of being reported as given
- the superseded configuration left in place beside the new hook, so two
  analysers disagree and the newer one is assumed authoritative
- values chosen here rather than read from the register
