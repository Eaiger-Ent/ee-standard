# gate-secrets — Calibration Examples

## §Strong

SEC-001 deployed and SEC-002 and SEC-003 checked, with both local loci running
the scanner at the version the register pins:

- the scanner is installed at the register's version, and every site in
  `PINNED_AT` repeats that same version — one site left behind is a pin that
  drifts
- `.pre-commit-config.yaml` carries the scanner hook, stamped
- the ci workflow installs and runs the scanner as its own step, stamped
- the developer environment locus is wired where the repository has one
  (Step 3.5)
- every path in `SECRET_PATHS` is ignored by a rule git tracks, and none of
  those paths is itself tracked — an ignore rule added while the file is already
  tracked ignores nothing
- push protection is **not** claimed: it is a platform act, and the output says
  `remote not deployed` rather than reporting it as done
- `register-check run --control SEC-001 --control SEC-002 --control SEC-003` was
  run and its verdict reported as given, including `exit 3` with the remote
  block `SKIPPED (no credentials)`

Output matches the **Deployed** block in `SKILL.md` § Output.

## §Weak

- the scanner version repeated inconsistently across `PINNED_AT` sites, so
  pre-commit and CI scan with different rule sets
- a path added to `.gitignore` while the file is still tracked, reported as
  ignored
- push protection reported as deployed when no platform call was made
- an `exit 3` with a skipped remote block reported as a clean pass
- the pre-commit hook added to a repository where nothing installs pre-commit,
  so the local locus never runs
- migration skipped, leaving a superseded scanner configured alongside the new
  one
- a failing `register-check` reported as a partial deployment rather than a
  failed one
