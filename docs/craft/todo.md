# Craft — todo

The steps, by section, for the work set out in [`plan.md`](plan.md).

**The division between the two files is deliberate.** `plan.md` holds the
*criteria* — what each stage is for and when it is finished. This file holds the
*steps* — the discrete units of work. Neither restates the other, because two
copies of the same statement are free to drift, and a ticked box is not an exit
criterion: a stage is finished when `plan.md`'s criterion is met, however many
boxes are ticked.

Written 2026-09-05. S1 and S2 are complete; S3 onwards is untouched.

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
      after Airbnb was rejected on a 2021-12-25 last publish. The stage's own
      review added `eslint-plugin-react` and `@eslint-react/eslint-plugin`: the
      first pass had no source for JSX correctness at all, and registered the
      antfu config in place of the plugin it delegates React to
- [x] Register the transferable `llm-toolkit` files against a pinned commit —
      `a46825d`, which is still `main`'s head. **Seven, not six:**
      `rules/platform/security.md` is language-neutral despite its path and is
      registered with the other six
- [x] Record a licence answer for every registered source — blank is a finding,
      not an omission. Three were wrong as GitHub reported them and were
      corrected by reading the licence file
- [x] Record a maintenance signal (last release or commit) for every source, and
      the commands that produced it — see `survey.sources.md` § How to re-run
      this sweep. Every signal there rots, and one nobody can re-derive is a
      claim rather than a measurement
- [x] Read `docs/control-planes/` in the toolkit before either repository's use
      of the word "control" is borrowed — their control plane is a docs
      repository an assistant loads, so it is enforcement *by* context and
      shares nothing with a control here but the word. Neither vocabulary
      travels
- [x] Find out whether any Equal Experts repository already consumes these rules,
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

Its exit criterion is met — the check is in
[`assess.rules.md`](assess.rules.md) § Exit criterion, not restated here. Three
boxes below were added by the stage itself and are not part of that criterion.

- [x] Re-run the source sweep before assessing anything — the commands and the
      trigger are in `survey.sources.md` § How to re-run this sweep. Nothing
      enforces this; that section is the whole mechanism. Run 2026-09-06: one
      row moved (`@eslint-react` 5.18.8 → 5.18.9) and one was wrong rather than
      stale (ruff's linter count), corrected in place
- [x] Fix the table shape: identity, what it asserts, which sources assert it,
      whether they agree, bucket, exact tool and rule ID, default-on proposal.
      Seven columns, defined in `assess.rules.md` § How to read a row
- [x] Mint identities property-first (`python.*`, `react.*`) and cite sources
      against them — never key a row on an upstream ID
- [x] Pass over ruff's taxonomy, the bulk source for Python's bucket 1 — read as
      JSON from the pinned 0.16.5 rather than from the documentation site, which
      is why the linter count came back corrected
- [x] Pass over each React source in turn — including
      `rules/platform/typescript.rules.md`, which S1 deferred here rather than
      registering as neutral. **A React pass that finishes without it is a
      defect, not a decision.** All thirteen of its rules are in the register;
      every plugin's preset was read from its published bundle rather than from
      its documentation, which is what surfaced findings 1 to 3
- [x] Pass over each of the seven neutral toolkit files, per file rather than in
      one sweep — `security.md` read **against** OWASP ASVS. It resolved in
      ASVS's favour: every one of its twenty-one rules is an ASVS requirement at
      a coarser grain, and none asserts anything ASVS does not
- [x] Route bucket 4 (assistant behaviour, not code) to its own list or discard
      it, recording which and why. **Tracked, not discarded** — thirteen
      statements listed in `assess.rules.md` § Bucket 4, with the recommendation
      that Craft does not carry them. Reading `code-quality.md` as one file and
      routing it whole would have lost the six code properties in its § Errors
      and § Logging sections
- [x] Mark contested classifications as contested rather than resolving them
      silently — fifteen rows, none resolved
- [x] Hand-check one file's machine pass against a person's read —
      `rules/clean-code.md`. Five of eight bucket-1 proposals were wrong, in
      three distinct shapes, and the shapes are why the Instrument column carries
      `preview` and `off` markers
- [x] State bucket 1's share of buckets 1–3, per stack — 69% Python, 78% React,
      21% stack-neutral, with the three qualifications that stop those being
      read as more than they are
- [x] Add the `any.` scope to `plan.md`'s naming standard — forty-two properties
      belong to neither stack, and minting them twice is the duplication the
      standard exists to prevent. **Added by the stage**, not planned by it
- [x] Register the six sources the assessment needed and the survey did not
      have — `eslint-plugin-testing-library`, `commitlint`, `spectral`,
      `eslint-plugin-promise`, Conventional Commits and the OpenAPI
      Specification. **Added by the stage**; `survey.sources.md` findings 10 and
      11 record why they were missing
- [x] Set out two ways to resolve each contested row, with what each costs —
      [`assess.contested.md`](assess.contested.md). **Prepared, not resolved**:
      `plan.md` § S3 gives these to a second reader, and a stage that took its
      own options is a stage that had none. The four structural recommendations
      are deliberately unapplied, so every count `assess.rules.md` publishes
      still holds. **Added by the stage**, not planned by it

## S3 — Review, empirically

- [ ] Write the acceptance criteria **before** any run: a findings-per-KLOC
      ceiling and a tolerable false-positive rate
- [ ] Choose the trial repositories — at least two Python, at least two React —
      and record why each is representative
- [ ] Build the candidate default-on configuration for each stack
- [ ] Run it unmodified and capture the raw counts
- [ ] Sample the findings for false positives, at a stated sample size
- [ ] Demote what fails, recording the measurement that demoted each one
- [ ] Have a second reader resolve S2's contested classifications. Its input is
      [`assess.contested.md`](assess.contested.md) — two options and their costs
      per row, with S2's own view marked as a view. **Reading it is not
      resolving them:** all fifteen are still marked `contested` in the register,
      and four of the recommendations would change its shape and its stated
      shares, so re-derive those after this reading rather than treating them as
      settled
- [ ] Re-run until the criteria clear, or record why they cannot be met
- [ ] Resolve what `@eslint-react`'s `disable-conflict-eslint-plugin-react` and
      `disable-conflict-eslint-plugin-react-hooks` configs contain, from an
      installed tree. S2 could not read them from the published bundle and
      recorded that rather than asserting it — and a React profile naming both
      plugins without one of these double-reports
- [ ] Measure what ruff's `preview = true` costs, since two Python properties are
      reachable only by enabling all 140 preview rules at once
- [ ] Write `review.noise.md`

## S4 — Design

- [x] Decide from S2's evidence whether "archetype" is a real axis or whether
      stack alone carries it — **stack alone**, with the `any.` rows gating on
      evidence rather than on a declared archetype. ADR 0052
- [ ] Specify the profile: its axes, its naming, its versioning
- [ ] Specify what happens when a profile changes under a repository that has
      already installed it
- [ ] Specify the config surface per stack, and confirm it introduces no new
      format
- [x] Draft the ADR on the craft/register boundary — when, if ever, a craft rule
      becomes a control. **ADR 0051**, Accepted 2026-09-06
- [x] Draft the ADR on the profile model — **ADR 0052**, Accepted 2026-09-06
- [x] Draft the ADR on attribution and licence posture, per source — **ADR
      0054**, Accepted 2026-09-06
- [x] Check anything a machine will read against ADR 0018 before it enters code
      — **ADR 0053** applies 0018's test to the mapping and answers *data*. The
      test still applies per rule as Craft's code is written, and 0053 requires
      each exception to carry its reason there
- [ ] Get every ADR this stage names to Accepted — the four above are, and the
      box stays open because `design.profiles.md` may name one they did not
      anticipate
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

All four taken 2026-09-06. `plan.md` § Decisions this workstream owed an ADR
names the record for each; the ADR is the record and nothing is summarised here.

- [x] Whether a craft rule may ever become a control, and what it needs first —
      **ADR 0051.** It becomes one by being installed as one, and Craft's
      installer mints the entry. Three preconditions, one of which is that S3
      has measured it. `any.dependency-vulnerability-scanning` is Craft's to
      close by this route rather than by widening SUP-002
- [x] What a profile is, and whether archetype is an axis — deferred until S2,
      then decided on S2's evidence. **ADR 0052.** Stack and strictness; no
      archetype axis and no codebase-age axis; the 42 `any.` rows gate on the
      artefact they read being present
- [x] Where the enforceable mapping lives, given ADR 0018 — **ADR 0053.**
      Register data, in a Craft register of its own: not `controls.yaml`, not
      Python
- [x] Attribution and licence, per source — **ADR 0054.** Cite every source,
      copy none. One rule for all twenty-four, which removes ASVS's share-alike
      and WCAG's document licence from the picture rather than managing them

## Open questions

- [x] ~~Is "Practice" the right name for the workstream~~ — settled 2026-09-05:
      **Craft**
- [x] ~~Does any Equal Experts repository already consume these rules~~ —
      **closed 2026-09-06: no.** Answered directly, so the org-wide code search
      that was never authorised is no longer needed. `survey.sources.md` records
      no consumer, and the reason is now that there is none
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
