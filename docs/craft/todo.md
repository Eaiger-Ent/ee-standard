# Craft — todo

The steps, by section, for the work set out in [`plan.md`](plan.md).

**The division between the two files is deliberate.** `plan.md` holds the
*criteria* — what each stage is for and when it is finished. This file holds the
*steps* — the discrete units of work. Neither restates the other, because two
copies of the same statement are free to drift, and a ticked box is not an exit
criterion: a stage is finished when `plan.md`'s criterion is met, however many
boxes are ticked.

Written 2026-09-05. S1 is under way; every other section is untouched.

## S1 — Survey

Its exit criterion is met — the check is in
[`survey.sources.md`](survey.sources.md) § Exit criterion, not restated here.
One box below is still open; it is not part of that criterion.

- [x] Settle the workstream name — **Craft**, settled 2026-09-05 against
      *Practice*, *Idiom* and *Workmanship*. `docs/practice/` became
      `docs/craft/` before the first commit, so no file, skill or identity ever
      carried the earlier word. The reasoning is the naming standard in
      [`plan.md`](plan.md)
- [x] Create `survey.sources.md` with one row per source: source, URL, licence,
      maintenance signal, authority, and what it claims to cover
- [x] Register the Python sources: ruff's rule taxonomy, PEP 8, PEP 20, Google's
      Python style guide, `pytest` practice, OWASP ASVS
- [x] Register the React sources: the React docs' Rules of React and *You Might
      Not Need an Effect*, `eslint-plugin-react-hooks` including the compiler
      rules, `typescript-eslint` recommended-type-checked,
      `eslint-plugin-jsx-a11y` with WCAG, Testing Library's guiding principles,
      and one opinionated style config read as a source — `@antfu/eslint-config`,
      after Airbnb was rejected on a 2021-12-25 last publish
- [x] Register the six transferable `llm-toolkit` files against a pinned commit —
      `a46825d`, which is still `main`'s head
- [x] Record a licence answer for every registered source — blank is a finding,
      not an omission. Three were wrong as GitHub reported them and were
      corrected by reading the licence file
- [x] Record a maintenance signal (last release or commit) for every source
- [x] Read `docs/control-planes/` in the toolkit before either repository's use
      of the word "control" is borrowed — their control plane is a docs
      repository an assistant loads, so it is enforcement *by* context and
      shares nothing with a control here but the word. Neither vocabulary
      travels
- [ ] Find out whether any Equal Experts repository already consumes these rules,
      and how. **Not authorised as asked** — the obvious route is a code search
      across the EqualExperts org, which is a scan of company repositories and
      has no yes behind it. Open until that yes or a narrower route
- [x] ~~**Blocked — needs a named yes.** Ask the `llm-toolkit` codeowners whether
      they hold a view on machine enforcement, and resolve the missing licence~~
      Closed 2026-09-05 **without contact**, which is why it is struck rather
      than done: Equal Experts owns `llm-toolkit` and this work is Equal
      Experts', so the ideas may be used and nobody needs asking. The absent
      licence file is unchanged — the survey records it as a finding, and it
      still constrains copying prose rather than citing rules

## S2 — Assess

- [ ] Fix the table shape: identity, what it asserts, which sources assert it,
      whether they agree, bucket, exact tool and rule ID, default-on proposal
- [ ] Mint identities property-first (`python.*`, `react.*`) and cite sources
      against them — never key a row on an upstream ID
- [ ] Pass over ruff's taxonomy, the bulk source for Python's bucket 1
- [ ] Pass over each React source in turn
- [ ] Pass over each of the six neutral toolkit files, per file rather than in
      one sweep
- [ ] Route bucket 4 (assistant behaviour, not code) to its own list or discard
      it, recording which and why
- [ ] Mark contested classifications as contested rather than resolving them
      silently
- [ ] Hand-check one file's machine pass against a person's read
- [ ] State bucket 1's share of buckets 1–3, per stack

## S3 — Review, empirically

- [ ] Write the acceptance criteria **before** any run: a findings-per-KLOC
      ceiling and a tolerable false-positive rate
- [ ] Choose the trial repositories — at least two Python, at least two React —
      and record why each is representative
- [ ] Build the candidate default-on configuration for each stack
- [ ] Run it unmodified and capture the raw counts
- [ ] Sample the findings for false positives, at a stated sample size
- [ ] Demote what fails, recording the measurement that demoted each one
- [ ] Have a second reader resolve S2's contested classifications
- [ ] Re-run until the criteria clear, or record why they cannot be met
- [ ] Write `review.noise.md`

## S4 — Design

- [ ] Decide from S2's evidence whether "archetype" is a real axis or whether
      stack alone carries it
- [ ] Specify the profile: its axes, its naming, its versioning
- [ ] Specify what happens when a profile changes under a repository that has
      already installed it
- [ ] Specify the config surface per stack, and confirm it introduces no new
      format
- [ ] Draft the ADR on the craft/register boundary — when, if ever, a craft rule
      becomes a control
- [ ] Draft the ADR on the profile model
- [ ] Draft the ADR on attribution and licence posture, per source
- [ ] Check anything a machine will read against ADR 0018 before it enters code
- [ ] Get every ADR this stage names to Accepted
- [ ] Write `design.profiles.md`

## S5 — Build the chooser and the installer

- [ ] Specify the skill's configuration contract, in the shape
      `.claude/skill-config.yaml` already uses
- [ ] Infer stack and archetype from the repository
- [ ] Present each applicable profile with what it enables **and** what S3
      measured it will cost
- [ ] Require an explicit confirmation before anything is written
- [ ] Write the pinned configuration at every locus the profile declares
- [ ] Record what was written
- [ ] Emit the judgment-only residue as prose an assistant loads, labelled
      unenforced
- [ ] Make a second run over its own output change nothing
- [ ] Version and publish it so a consumer repository can pin it
- [ ] Write `build.installer.md`

## S6 — Trial and review

- [ ] Choose the trial repository and agree the period before installing
- [ ] Install through the skill rather than by hand — an installer nobody used is
      an installer nobody tested
- [ ] Collect what the team reports, not what the plan predicted
- [ ] Compare against S3's criteria as they hold in use
- [ ] Revise the profile, or record the gap
- [ ] Write `review.trial.md`

## Decisions owed an ADR

Tracked here so each is taken deliberately. The wording of each is in
[`plan.md`](plan.md).

- [ ] Whether a craft rule may ever become a control, and what it needs first
- [ ] What a profile is, and whether archetype is an axis — deferred until S2
- [ ] Where the enforceable mapping lives, given ADR 0018
- [ ] Attribution and licence, per source

## Open questions

- [x] ~~Is "Practice" the right name for the workstream~~ — settled 2026-09-05:
      **Craft**
- [ ] Does any Equal Experts repository already consume these rules — open, and
      the org-wide search that would answer it is not authorised
- [x] ~~**Blocked — outward-facing.** The `llm-toolkit` licence and its owners'
      view on machine enforcement~~ — closed 2026-09-05: Equal Experts owns the
      repository, so the ideas are ours to use. The missing licence is recorded
      as a survey finding

## Working agreement

- One box is one unit of work, small enough to finish and review in a sitting.
- Tick a box only when the work is done and reviewed — never in advance, and
  never because a stage moved on without it.
- Each slice lands as a pull request with its rationale in the commit.
- A box that turns out to be wrong is struck through with the reason, not
  deleted. A silently removed step is indistinguishable from a completed one.
