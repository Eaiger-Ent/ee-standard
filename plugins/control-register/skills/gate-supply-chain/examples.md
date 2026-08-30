# gate-supply-chain — Calibration Examples

## §Strong

SUP-001 to SUP-004 deployed, with every locus each control declares wired — ci
for SUP-001 and SUP-002, pre-commit **and** ci for SUP-003:

- the ci install step is a frozen-lockfile install (`--frozen-lockfile`,
  `--locked`, `npm ci` — whichever the ecosystem spells), stamped against
  SUP-001
- `.github/dependabot.yml` (or the Renovate configuration) declares one entry
  per ecosystem actually present in the repository, stamped against SUP-002
- every third-party action reference in every workflow is rewritten to a full
  commit SHA; owner-owned actions are skipped and the count of each is reported
- the pre-commit and pre-push hooks for SUP-003 are stamped, and
  `${CLAUDE_PLUGIN_ROOT}/reference/pre-commit-runner.md` was consulted so
  something installs them
- what still needs a human is stated explicitly — enabling Dependabot or
  installing the Renovate app is a platform act this skill cannot perform, and
  the `Needs a human:` line says so
- pinned digests are checked against what was published (SUP-004), not assumed
- `register-check run --control SUP-001 … --control SUP-004` run afterwards

Output matches the **Deployed** block in `SKILL.md` § Output.

## §Weak

- an action left on a tag (`actions/checkout@v4`) and counted as pinned — a tag
  is mutable and SUP-003 is not met
- `dependabot.yml` written with ecosystems the repository does not use, or
  missing one it does
- the `Needs a human:` line omitted, so the output implies dependency updates
  are live when nobody has enabled them
- a non-frozen install (`npm install`, `uv sync` without `--locked`) reported as
  satisfying SUP-001 — it resolves fresh and the lockfile stops being the
  authority
- SUP-003's pre-commit locus wired and its ci locus skipped, while the output
  lists both
- SUP-004 reported without actually comparing the pinned digest to the published
  one
