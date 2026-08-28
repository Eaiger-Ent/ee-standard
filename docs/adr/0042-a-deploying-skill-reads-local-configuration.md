# ADR 0042: A Deploying Skill Reads Local Configuration

**Status:** Accepted
**Date:** 2026-08-27
**Revision:** 2

## Background

`lint-md` owns DOC-001's whole lifecycle and is the one control this standard
does not deploy itself. It keeps shipping — which is the reason to depend on a
marketplace at all — and this repository has been unable to take a release since
1.0.6.

The deployed stamps read `lint-md@1.0.6`; 1.0.7 is installed and is the
marketplace latest. The deployment is not *at risk*, it is **unrefreshable**:
re-running the skill would write artefacts this register forbids, so the stamp
would claim 1.0.7 wrote what 1.0.7 would not be allowed to write.

Two rows are the whole disagreement, and both are about **values**, not about
what the skill does:

| What 1.0.7 writes | Why it cannot be deployed here |
| --- | --- |
| `npx --no-install markdownlint-cli2` at eight sites | [ADR 0020](0020-a-locus-reaches-the-pinned-artefact.md) measured `--no-install` falling through to `PATH`; the register pins `tools.markdownlint-cli2.invocation` to `node_modules/.bin/markdownlint-cli2` |
| `.claude/**` in `ignores` | Right intention, wrong mechanism — the memory files it aims at live outside the repository, and the entry hides anything this repository later authors under `.claude/`, which [ADR 0019](0019-exemptions-cannot-hide-tracked-files.md) forbids |

The plan's response was to argue both rows upstream. That works once and does not
generalise: the next release picks a value we disagree with somewhere else, and
we are back to a skill we cannot run. Arguing values one at a time is a standing
tax on both sides, and it makes every disagreement look like a defect in the
skill when most of them are legitimate differences between repositories.

## Decision

**We will propose, and adopt, a contract in which a skill that deploys artefacts
takes the values it writes as input rather than as constants.**

Four parts.

**1. A deploying skill declares the values it decides.** Not the artefacts —
those are the skill's — the *settings inside them* that a repository could
reasonably need to differ: an invocation, an exemption list, a threshold. This
is a list the skill already has implicitly, scattered through its steps.

**2. It reads them from a repository-local file if one is present**, keyed by
skill name, and uses what it finds **verbatim**:

```yaml
# .claude/skill-config.yaml
lint-md:
  invocation: node_modules/.bin/markdownlint-cli2
  ignores: []
```

**3. Absent file, absent key, absent value — today's behaviour.** The default
path does not change, nothing existing breaks, and a repository that has never
heard of this gets exactly what it gets now. That is what makes the change
proposable rather than a fork.

**4. A value taken from the file is reported as such.** "invocation:
`node_modules/.bin/markdownlint-cli2` (from `.claude/skill-config.yaml`)" is a
different fact from the skill's own default, and the person approving the write
has to be able to tell them apart.

**We do not generate that file from `controls.yaml`.** It is written once, by
hand, and it is a *second statement* of two values the register already holds —
which is exactly the duplication this repository exists to prevent, so it needs
a reason. The reason is that the alternative is worse: generating it at deploy
time would put a `controls.yaml` reader inside a plugin that must work for
repositories with no register at all. What keeps the copy honest is that
`markdown_gate_wired_at_all_loci` already reads the deployed artefacts against
`tools.markdownlint-cli2.invocation`, so a `skill-config.yaml` that drifted from
the register fails the build on the next run. The copy is checked, which is the
condition this repository has always put on the ones it keeps.

**Extended in revision 2: where a declination is recorded.** Revision 1 said
this ADR did not close the question of distinguishing *nobody redeployed* from
*the release would revert a narrowing*, and named it as the next criterion's.
The mechanism is the other half of this decision rather than a separate one, so
it is recorded here: **`deployment-decisions.yaml`, at the repository root.**

Three places it cannot go, and each exclusion is a rule already in force:

- **`controls.yaml`, or anything under `plugins/`.** A declination is this
  repository's posture, and [ADR 0022](0022-a-platform-token-ci-carries.md)
  requirement 6 keeps posture out of what an adopter installs.
  `tests/test_posture.py` enforces it.
- **`.claude-plugin/deploys.json`.** That is the *plugin's* sidecar, declaring
  what a gate writes. A declination is the consuming repository's record about a
  skill it did not run.
- **`.claude/skill-config.yaml`, the file this ADR proposes above.** Its name and
  location belong to `ee-skills` rather than to us, and writing our own records
  into someone else's contract is how that contract stops being one.

The root is right rather than merely available. This file is the counterpart to
the provenance stamps: a stamp is the repository-side record of what *was*
deployed, and this is the repository-side record of what deliberately was not.
Those belong at the same level of the tree. An adopter gets the same path, and
`register-check deployments` takes `--decisions` as it already takes `--plugin`.

Two properties matter more than the path, and both are decisions rather than
details:

**A declination names the version it declines.** Declining `lint-md@1.0.7` must
not silently cover 1.0.8. A new release re-opens the question, and that
re-opening *is* what distinguishes a chore from a decision — without it the file
is a permanent opt-out wearing a reason.

**A declination expires.** One with no `review_by` becomes permanent by neglect,
which is why `variance: justified` was removed at register contract 3: the
mechanism that was supposed to stop it becoming a loophole was unreachable. An
expired declination is reported as expired, the way GOV-003 reports a control
past its review date.

A malformed file **fails** rather than being ignored. Silently reverting to
*chore* reports the opposite of the truth, which is the one outcome this row
exists to prevent.

## Alternatives considered

**Argue the two rows upstream and take 1.0.8.** This is what the plan said, and
it is not wrong — it is just not enough. It resolves two values and leaves the
mechanism that produced them in place. We should still raise both, because
`.claude/**` is a genuine defect by ADR 0019's reasoning rather than a
preference, and `--no-install` is a measured fallthrough rather than a taste.
But taking a release should not depend on winning an argument about every value.

**Fork `lint-md` into this plugin.** Rejected. It is the access-shaped single
point of failure `docs/08-adopting.md` § 3 already records, and a copy of
someone else's skill in this repository goes stale silently — the duplication
this standard exists to prevent, wearing a different hat.

**Keep copying the skill into `.claude/skills/` as Phase 4 did.** Same objection,
and Phase 4 recorded it as *"not a recommendation"* at the time.

**Have the skill read `controls.yaml` directly.** Rejected. It would make a
marketplace plugin depend on this standard's file format, which is precisely the
coupling that would stop anyone else adopting the skill.

## Consequences

**This is a proposal until it ships.** Writing it down fixes the contract so the
issue we raise and the amendment we submit describe the same thing, and so that a
future release can be judged against something citable rather than against
whatever we remembered wanting.

**Until it ships, `lint-md` stays at the 1.0.6 stamp**, and that state is now a
*decision with a reason* rather than a chore nobody got to — recorded in
`deployment-decisions.yaml` per revision 2, and read back by
`register-check deployments`.

**The two rows still need raising.** This contract would let us set `ignores: []`
locally, which stops `.claude/**` reaching this repository — it does not stop it
reaching everyone else's, and ADR 0019's argument is about anyone's repository,
not ours. A mechanism for expressing disagreement is not a substitute for saying
the thing is wrong.

**If it ships, the acceptance test is mechanical.** Re-run `/lint-md`, and the
artefacts it writes must be byte-identical to what is deployed here today, with
the stamp moving to the new version. Anything else is the contract not being
honoured, and it is checkable rather than arguable.

## Applied — pass 1: the contract shipped, 2026-08-28

`lint-md@1.0.8` ships it, one day after this ADR was written. `/skill-update`
moved this container from 1.0.7; the release carries
`skills/lint-md/local-config.md`, which is this decision's four parts in the
skill's own words:

| This ADR | 1.0.8 |
| --- | --- |
| A deploying skill declares the values it decides | `local-config.md` § What is read — a table of key, default and the loci each is used at |
| Read from a repository-local file keyed by skill name | `.claude/skill-config.yaml`, `lint-md:` key, read once at pre-flight |
| An absent file means today's behaviour | *"Absent file, absent key, absent value — behave exactly as this skill always has"* |
| The run reports which values came from configuration | § Report what you used |

One thing it settles that this ADR left implicit: a **present key replaces the
default entirely** rather than merging with it. That is what makes `ignores: []`
mean *ignore nothing* rather than *nothing to add*, and without it the row this
repository cares about would have been unexpressible.

**The defaults did not move**, and that is the contract working rather than
failing. 1.0.8 still writes `npx --no-install` and `.claude/**` where nothing
configures it; the disagreement was never that those values are wrong for every
repository, only that they are wrong for this one and that arguing them one at a
time does not generalise.

`.claude/skill-config.yaml` exists here and sets both.

## Applied — pass 2: the acceptance test, run 2026-08-28

`/lint-md` was re-run at 1.0.8. The test this ADR set was mechanical — *the
artefacts it writes must be byte-identical to what is deployed here today, with
the stamp moving to the new version* — and it is worth reporting that it
**passed at four loci and failed at one**, because a test that can only be
reported as passed is not a test.

| Artefact | Result |
| --- | --- |
| `.markdownlint.yaml` | Overwritten; byte-identical below the stamp |
| `.markdownlint-cli2.yaml` | Skipped — `ignores: []` read from configuration and already correct |
| `.pre-commit-config.yaml` | Skipped — `entry:` is the configured invocation |
| `.github/workflows/lint.yml` | Skipped — invocation configured; the checkout SHA and `npm ci` flags remain this repository's narrowings |
| `.claude/hooks/md-lint.py` | **Not honoured** |

The exception is the contract's own boundary showing itself. `local-config.md`
says `invocation` is used at *"every locus: the pre-commit hook, the CI step,
the DevContainer check, **the PostToolUse hook** and every verification
command"*, and Step 3a is a plain `cp` of a script carrying
`NPX_LINT = ("npx", "--no-install", "markdownlint-cli2")`. A configured value
that reaches four of the five sites the documentation names is the contract
being *stated* at a locus where it is not *applied* — the same shape as the rule
[ADR 0043](0043-a-declination-is-reconciled-against-the-installed-skill.md) was
written for, one layer up.

It cost nothing here, because Step 3a's own skip branch leaves an existing hook
alone. It is an amend owed upstream rather than a reason to decline 1.0.8: the
release is takeable, so the `lint-md@1.0.7` entry was **deleted** rather than
renewed, and `deployment-decisions.yaml` now reads `declined: []`.

## Revision History

| Rev | Date | What changed | Ratified by |
| --- | --- | --- | --- |
| 1 | 2026-08-27 | Original decision: a skill that deploys artefacts takes the values it writes as input, read from a repository-local file keyed by skill name, with an absent file meaning today's behaviour. | Nathan Carney |
| 2 | 2026-08-27 | § Decision extended with where a declination is recorded — `deployment-decisions.yaml` at the repository root — and the two properties that make it a record rather than an opt-out: it names the version it declines, and it expires. Revision 1 named this as the next criterion's; it is the other half of this decision. A stricter reading of ADR 0026 would have made it a new ADR. | Nathan Carney |
