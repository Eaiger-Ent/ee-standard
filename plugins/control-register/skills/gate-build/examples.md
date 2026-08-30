# gate-build — Calibration Examples

## §Strong

BLD-001 and DEV-001 deployed into a repository that already had a devcontainer,
with every value taken from the register and none chosen by the skill:

- `.devcontainer/devcontainer.json` carries `remoteUser` naming a non-root user,
  and the key is stamped with BLD-001, this skill and version, and the
  register's version and contract
- the `image` key is a digest reference (`…@sha256:…`), not a tag, stamped
  against DEV-001
- `.devcontainer/devcontainer-lock.json` exists and pins every feature the
  devcontainer declares — a lock file missing one feature is not complete
- `.pre-commit-config.yaml` has the `<tool>-build` hook, stamped once per
  control, and `${CLAUDE_PLUGIN_ROOT}/reference/pre-commit-runner.md` was
  consulted first so something actually runs the hook
- the ci locus is satisfied by the repository's existing full audit, and the
  skill says so rather than adding a second step that runs the same checker
- every write was narrated in the shape
  `${CLAUDE_PLUGIN_ROOT}/reference/write-narration.md` gives, one line before
  the write
- `register-check run --control BLD-001 --control DEV-001` was run afterwards
  and its output shown

Output matches the **Deployed** block in `SKILL.md` § Output.

A run where the repository already declares a non-root `remoteUser` is equally
strong: Step 1 writes nothing, stamps the key that is there, and reports it as
adopted rather than deployed.

## §Weak

A weak run is one where the artefacts exist but the deployment is not what the
output claims:

- `image` left on a floating tag (`mcr.microsoft.com/devcontainers/python:3.12`)
  while the output reports DEV-001 deployed — a tag is not a digest, and the
  control is not met
- `devcontainer-lock.json` written but missing a feature the devcontainer
  declares, so the next rebuild resolves it differently
- a `remoteUser` value invented here rather than read from the register or the
  repository, breaking success criterion 1
- a pre-commit hook added to a repository where nothing installs pre-commit, so
  the hook never runs and the locus is wired in name only
- stamps omitted, or naming the skill without the register's version and
  contract — a later run cannot then tell its own writes from a human's
- `register-check` not run, or run and its failure reported as a partial
  success. A failed verification is a **failed** deployment: the output must say
  so verbatim and claim nothing
- writes made outside the target repository
