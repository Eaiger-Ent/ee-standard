# ADR 0042: A Deploying Skill Reads Local Configuration

**Status:** Accepted
**Date:** 2026-08-27
**Revision:** 1

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
*decision with a reason* rather than a chore nobody got to. Distinguishing those
two in the deployment report is Phase 5's next criterion and is not closed by
this ADR — what this gives it is the reason to record.

**The two rows still need raising.** This contract would let us set `ignores: []`
locally, which stops `.claude/**` reaching this repository — it does not stop it
reaching everyone else's, and ADR 0019's argument is about anyone's repository,
not ours. A mechanism for expressing disagreement is not a substitute for saying
the thing is wrong.

**If it ships, the acceptance test is mechanical.** Re-run `/lint-md`, and the
artefacts it writes must be byte-identical to what is deployed here today, with
the stamp moving to the new version. Anything else is the contract not being
honoured, and it is checkable rather than arguable.
