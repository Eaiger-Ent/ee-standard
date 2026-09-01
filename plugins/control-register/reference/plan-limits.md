# When the platform refuses on the plan, not the token

One home for this rule rather than a copy in each gate, which is
[ADR 0036](https://github.com/Eaiger-Ent/ee-standard/blob/main/docs/adr/0036-shared-skill-prose-has-one-home.md)'s
reason for this directory.

Shared by the gates whose controls verify **platform state a plan can withhold**:
`gate-repo` (CI-001's ruleset) and `gate-secrets` (SEC-001's push protection).
Repository rulesets and secret-scanning push protection are both things GitHub
**sells** for a private repository, and neither is reachable below a paid tier.

## Telling a plan limit from a scope problem

They arrive identically — `403` — and the body is what separates them:

```bash
gh api "repos/$OWNER/$NAME/rulesets" -i 2>&1 | grep -iE 'x-accepted|message'
```

* **`"Upgrade to GitHub Pro or make this repository public"`** — a plan limit.
* **`x-accepted-github-permissions`** names the permission the endpoint wanted.
  On the rulesets endpoints it is `metadata=read`, which every token holds and
  GitHub does not let you turn off, so a `403` carrying it is **never** about
  scope. This is the same header the permissions table in `docs/08-adopting.md`
  § 1 is derived from, read off a refusal rather than a success.

A checker that guessed here got it wrong in both directions once: it reported
every `403` as a missing `administration` permission, while the response it was
reading named `metadata=read` in a header.

## What a gate does about it

**Write the record, make no call, and say both things happened.** The file the
gate would have applied is still written and git-added; the API call is not
made; the report says *recorded, not applied*, and says the control does not
hold.

**Why this is not the half-state a gate must never create.** A missing
permission is fixable in a minute, so a record written under one claims
protection somebody was about to obtain anyway — that record is misleading and
the gate stops before writing it. A plan limit is not fixable without buying or
publishing, and
[ADR 0047](https://github.com/Eaiger-Ent/ee-standard/blob/main/docs/adr/0047-a-plan-limit-is-recorded-not-tolerated.md)
rule 2 requires the record regardless: what the gate writes is a **file** block,
a plan cannot stop a repository containing a file, and a recorded limit may name
a `kind: remote` block only. So an adopter who cannot apply must still be able to
record — *"the day the plan changes it is one API call rather than a fresh
decision"*.

**Point at the ADR for what the repository writes next.** It carries the key and
a worked example for `deployment-decisions.yaml`, after which the checker reports
that block as `UNAVAILABLE (plan)` on every run, with its review date. Do not
transcribe that entry into a skill: it is one repository's billing, and a skill
ships to everybody.

## What a gate never does

**Never offer "make the repository public" as the skill's choice to take.** It is
a disclosure decision about somebody's source code, it is outside any gate's
blast radius, and ADR 0047 refuses it in as many words. Name it as the operator's
to take elsewhere, and stop.
