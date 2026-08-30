# register-install — Calibration Examples

## §Strong

The checker installed into a repository at the ref the register names:

- the requirement was composed from the register's
  `tools.register-check.install` and the ecosystem's own spelling — no address,
  tag or grammar was written from the skill itself
- the ecosystem was worked out from files present in the repository, not asked
  for or assumed
- the manifest records the pin **and** the lockfile records the resolved
  version — a manifest edit no lockfile followed is a pin that resolves
  differently on the next machine, which is the failure this criterion exists
  to prevent
- the plan was shown and confirmed before anything was written
- `register-check --version` was run through the package manager's runner (for
  example `uv run`, `npx`), not off `PATH`, and its output shown
- nothing was committed

Output matches the **Installed** block in `SKILL.md` § Output.

Two other strong outcomes: **Already present** — the pin is already the
register's ref, nothing is written, and the version is still verified;
**Upgraded** — the old and new refs are both named, so the change is legible.

## §Weak

- a version verified by running `register-check --version` off `PATH`, which may
  be a globally installed copy at an entirely different version to the pin just
  written
- the manifest edited and the lockfile not regenerated
- an install address, tag or requirement grammar written from this skill rather
  than composed from the register
- the ecosystem guessed rather than derived from files, so the pin lands in a
  manifest the repository does not use
- writing before the plan was confirmed
- reporting **Installed** when the pin was already present, hiding that nothing
  changed
- running in the standard's own repository, which Step 1 excludes
