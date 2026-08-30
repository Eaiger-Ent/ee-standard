# gate-repo — Calibration Examples

## §Strong

CI-001 deployed against a GitHub repository, with the record written first and
the platform changed only after an explicit confirmation:

- `.github/rulesets/default-branch.json` records exactly the ruleset the
  register requires, stamped with CI-001, this skill and version, and the
  register's version and contract
- every rule carries the `parameters` GitHub's schema requires for its type — a
  rule type accepted by the API with an empty parameter block enforces nothing
- every name in `REQUIRED_CHECKS` is a job in a gating workflow that does not
  suppress its own failure (no `continue-on-error`, no `|| true`) — a required
  check that cannot fail is protection in name only
- the blast radius was stated and confirmed before the API call: this changes
  what every contributor can push to the default branch
- the API response was shown verbatim, including the status code and ruleset id
- `register-check run --control CI-001` was run afterwards, and where no
  credentials were available the remote block was reported as
  `SKIPPED (no credentials)` — never as a pass

Output matches the **Deployed** block in `SKILL.md` § Output.

The **Recorded only** block is also a strong outcome when confirmation is
declined: it states plainly that nothing on the platform changed, the default
branch is unprotected, and CI-001 is *not* deployed.

## §Weak

- the API call made without an explicit confirmation of blast radius
- a `SKIPPED (no credentials)` remote block reported as a pass, so the output
  claims GitHub enforces a ruleset that was never verified — the single most
  damaging failure this skill can produce
- a required check named that is not a job in any gating workflow, or that is a
  job which suppresses its own failure
- a rule written without the `parameters` its type requires
- the record written and the ruleset applied, but the two allowed to differ,
  so the tracked file no longer describes what is enforced
- a pre-existing ruleset of the same name overwritten without reading it first
  (Step 2b), silently dropping rules a human added
