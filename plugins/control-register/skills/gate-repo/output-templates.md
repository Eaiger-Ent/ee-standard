# gate-repo — output templates

Read by `SKILL.md` §Output. Emit the block whose trigger matches how the run ended.

## Deployed

Trigger: Step 2 applied the ruleset, and Step 4 verified it.

```text
gate-repo deployed CI-001 in <owner>/<name>.
  recorded  .github/rulesets/default-branch.json (stamped)
  applied   POST /repos/<owner>/<name>/rulesets → 201, ruleset id <id>
            ~DEFAULT_BRANCH: pull request required, checks required,
            force-push forbidden, enforcement active
Verified: register-check run --control CI-001 → exit 0
  the recorded ruleset matches the register, and the ruleset GitHub enforces
  on <default branch> satisfies it.
  (Without credentials: exit 3 — the record matches, and whether GitHub
  enforces it is SKIPPED (no credentials) and is not claimed here.)
```

## Recorded only

Trigger: The operator answered **Record only, do not apply** at Step 2.

```text
gate-repo recorded CI-001's ruleset and did not apply it.
Nothing on the platform has changed. The default branch is unprotected.
CI-001 is not deployed.
```

## Recorded, not applied (plan limit)

Trigger: `PLAN_LIMIT` was set, and §2P ran instead of the rest of Step 2.

```text
gate-repo recorded CI-001's ruleset and did not apply it: GitHub refuses
rulesets on this repository's plan (<the refusal's message, verbatim>).
  recorded  .github/rulesets/default-branch.json (stamped, git-added)
  applied   nothing — no API call was made
CI-001 does not hold. ADR 0047 is how the repository records the limit.
Upgrading the plan or making the repository public is yours to decide, not
this skill's.
```

## Aborted

Trigger: A pre-flight stop: no register, or no `administration: write` without a plan limit.

```text
gate-repo stopped at <phase>: <reason>. Nothing was written and nothing
was called.
```
