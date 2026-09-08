# Craft — todo

The steps, by section, for the work set out in [`plan.md`](plan.md).

**The division between the two files is deliberate.** `plan.md` holds the
*criteria* — what each stage is for and when it is finished. This file holds the
*steps* — the discrete units of work. Neither restates the other, because two
copies of the same statement are free to drift, and a ticked box is not an exit
criterion: a stage is finished when `plan.md`'s criterion is met, however many
boxes are ticked.

Written 2026-09-05. S1, S2 and S3 are complete. S3 was rewritten 2026-09-06
after ADR 0052 named new codebases as the target and left its original premise
measuring a risk this workstream does not carry; it met its exit criterion on
2026-09-07, and `review.bench.md` § Does the exit criterion hold is the record.
S4 onwards is untouched apart from the boxes that premise reached.

## S1 — Survey

Its exit criterion is met — the check is in
[`survey.sources.md`](survey.sources.md) § Exit criterion, not restated here.
Every box below is closed. The last of them was open until 2026-09-06 and was
never part of that criterion.

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
      has no yes behind it, so the box stayed open on that route. **Closed
      2026-09-06 without it: no repository does.** Answered directly, which is
      why the search is not needed rather than still owed
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

## S3 — Bench the configuration

**Rewritten 2026-09-06.** The stage was written around running the default-on
set over real repositories and holding it to a findings-per-KLOC ceiling. ADR
0052 targets new codebases, where that measurement has nothing to measure.
`plan.md` § S3 records why; the boxes below are the replacement. Three of the
originals are struck rather than deleted — a silently removed step is
indistinguishable from a completed one.

- [x] Write the acceptance criteria **before** anything is run. They are about
      the configuration, not a corpus: it assembles, it runs, no two selected
      rules contradict, and every probed false-positive case is either clean or
      the rule is demoted with the case recorded. Done 2026-09-06:
      [`review.bench.md`](review.bench.md) § The acceptance criteria, C1 to C9,
      written with no scaffold in existence. Five of the nine are more than the
      exit criterion asks — that section says which, and why leaving them out
      would have left five deferred questions for somebody to rediscover
- [x] Build a minimal scaffold per stack — a new repository of the shape the
      profile is for, not a sample of an existing one. Done 2026-09-07:
      thirteen files — twelve, plus the `tests/__init__.py` C3 found `INP001`
      and pytest both want — written by
      [`scripts/craft_scaffold.py`](../../scripts/craft_scaffold.py) into
      gitignored `temp/` rather than tracked. **The first attempt was tracked
      and this repository rejected it** — a scaffold's `[tool.ruff]` is a second
      lint definition, and tracked Python that must fail a check cannot coexist
      with TYP-001's allow-list, which is what
      `test_h7_this_repository_declares_coverage_for_every_tracked_module`
      failed on. `review.bench.md` § The scaffolds is the record, including the
      two version ceilings the build surfaced
- [x] Build the candidate default-on configuration for each stack from the
      resolved register. Done 2026-09-07: 65 ruff selectors resolving to 141
      rules, and 89 ESLint rules named on over two preset bases, written by
      [`scripts/craft_profile.py`](../../scripts/craft_profile.py) into the same
      gitignored `temp/` the scaffolds go to. **A second script, not more of
      `craft_scaffold.py`** — the scaffold is the subject and this is the
      instrument, and S3 varies one while holding the other still.
      `review.bench.md` § The candidate configuration is the record, including
      the nine places a prose citation had to be read more closely than it was
      written, and three things it puts to C1, C4 and C9 without settling any of
      them. Nothing has been run
- [x] Confirm the React config assembles at all: six plugins, three presets, the
      two `disable-conflict` configs, and type-checked rules that need a
      `tsconfig`. Done 2026-09-07 with the Python half of C1 beside it, because
      half a criterion is not a verdict. It resolves for a component, a plain
      module and a test; **133 distinct rules, none unknown to its plugin**, and
      132 once C4 demoted one of them; the type-checked rules are bound,
      demonstrated by a floating promise drawing
      the rule that cannot fire without types. Three of this box's own words
      turned out to be wrong and `review.bench.md` § What ran says so: there are
      **two** rule-carrying presets rather than three, and **neither**
      `disable-conflict` config may be applied
- [x] Resolve what `@eslint-react`'s `disable-conflict-eslint-plugin-react` and
      `disable-conflict-eslint-plugin-react-hooks` configs contain, from an
      installed tree. S2 could not read them from the published bundle and
      recorded that rather than asserting it — and a React profile naming both
      plugins without one of these double-reports. Read 2026-09-07: 40 entries
      and 12 entries, **and both stand down the *other* plugin** so that
      `@eslint-react` owns the overlap, which is the opposite of what this
      register cites. The candidate configuration had applied one of them
      believing the reverse, and seven rules were resolving twice as a result.
      Neither is applied now and the copies are turned off by hand.
      `review.bench.md` § The defect C1 found is the record
- [x] Check `@eslint-react`'s coverage against the 104 rules
      `eslint-plugin-react` carries, which is what rows 10 and 11 were resolved
      contingent on. **103, not 104.** Done 2026-09-07 from the installed trees,
      and read from `disable-conflict-eslint-plugin-react` — which is the
      replacing plugin's own declaration of what it overlaps, rather than a name
      match, and a name match would have reported every counterpart as a gap
      because they are not named alike. **The contingency holds:** of the eight
      rules the register cites, seven are covered and the eighth,
      `jsx-no-duplicate-props`, is the one the configuration already takes
      directly. One rule is genuinely lost — `no-unescaped-entities`, which no
      register row asserts — and it is recorded rather than dropped quietly
- [x] Find every pair of selected rules that contradict. `python.return-count`
      is one and is already recorded as `incompatible`; the search is for the
      others. Done 2026-09-07, and **none found**. The method is the deliverable
      rather than the verdict: ruff's own formatter-conflict check, shown able to
      fire before its silence was believed; a construct partition taking 9,870
      pairs to 273; and a witness per group in
      [`scripts/craft_cases.py`](../../scripts/craft_cases.py) — code where every
      rule in a group applies and every rule holds, which clears the group's
      pairs at once. Seven pairs are named individually. **One thing did fight**:
      `INP001` against the layout pytest recommends, which is a property's two
      instruments disagreeing rather than a rule pair, and `touch
      tests/__init__.py` satisfied both with the tests still passing. The
      scaffold owes that file, which is C2's to clear
- [x] Probe the rules with a known false-positive reputation, one deliberate
      case each — `anchor-ambiguous-text` against a link with an `aria-label`,
      `S101` against a test, `explicit-module-boundary-types` against a
      component. Done 2026-09-07, **seven probes rather than the three named**,
      with `S311`, `S608`, `ANN401` and `ERA001` added. Five fired, one did not,
      and none is demoted — C5 allows a rule to survive a probe and requires the
      case either way. **The one that did not fire is the finding**:
      `anchor-ambiguous-text` reads the `aria-label`, so half of the register's
      stated reason for leaving `react.a11y-link-purpose` without an instrument
      is not true of 6.10.2, and a control with no label proves the rule was
      live. `ERA001` is the one to watch at S6: it flagged a comment documenting
      a data format
- [x] Record cost per finding from ruff's `fix_availability`, which needs no run:
      421 of 812 stable rules carry no fix. Done 2026-09-07, **both stacks**, by
      [`scripts/craft_cost.py`](../../scripts/craft_cost.py) rather than by hand,
      because S5 needs the answer for the versions it installs rather than the
      versions this bench read. 273 rules, 168 of them hand-work. The Python
      half is 51% against the taxonomy's own 52%, so the selection is
      representative rather than costly; the React half is 73%, and **every one
      of the 34 `jsx-a11y` rules the profile selects** is hand-work against
      `react-hooks`' 1 of 12.
      The reading also exposed that **the profile pins no tool version in
      anything it materialises**, which is S4's to fix
- [x] Settle the four numbers the resolutions left owed —
      `python.function-length`'s threshold, `python.line-length`'s default,
      `python.no-any`'s strict variant and `react.explicit-return-types`' scope.
      **Each is now a choice with a stated rationale, revisable at S6**, not a
      corpus calibration. Done 2026-09-07. Complexity stays at **10** and is
      *cited* — McCabe's own number — rather than chosen; `max-statements` moves
      off ruff's default to **25**, because at 50 a function can sit under the
      complexity ceiling and still run to fifty straight-line statements, which
      is the case the property exists for; **88** stands, with the note that the
      agreement is the property and this repository itself runs at 100. The
      third is **not taken**, and the reason is the prior question it uncovered:
      **the profile configures no type checker at all**, while the register
      cites mypy for two rows, so a strictness cannot be owed before a checker
      is. S4's
- [x] Measure what ruff's `preview = true` costs, since two Python properties are
      reachable only by enabling all 140 preview rules at once. Done 2026-09-07,
      and **the premise does not hold for this configuration**: preview arrives
      wholesale against a *family* selector, and this selection is spelled in
      exact codes, so it picks up **zero** preview rules. The two properties cost
      `preview = true` and two extra selectors and nothing else, proven by a
      case that is silent under the profile and draws both findings under
      preview. They are recorded as **reachable** — neither unreachable nor
      declined, since declining is S4's. One risk is named rather than
      dismissed: preview also gates behaviour changes to stable rules, and a
      clean diff over the scaffold and witnesses is not a guarantee
- [x] Show the configuration running in both directions, and every rule the
      profile enables against its own plugin's default firing on a case written
      for it — C2. **Added by the stage**: the criterion had no box, and the
      evidence it asks for is more than a document section. Done 2026-09-07.
      Clean in both stacks, and non-zero on `cases/violations`, where **all 26
      selected ruff families fire from 37 rules**. The React checklist is
      derived rather than taken from the register's ten: **33 rules**, twenty
      enabled where the plugin ships them off or absent and **thirteen whose
      severity is raised**, all 33 demonstrated. Eleven of the thirteen are
      `@eslint-react` rules shipped at `warn`, which in a merge gate is a rule
      that looks enabled and blocks nothing — finding 1's shape a second time.
      **The scaffold was not clean when the configuration met it**: five
      findings, including three `E501`s at this repository's 100 columns rather
      than the profile's 88
- [x] Show that one defect draws one diagnostic — C4. **Added by the stage**, on
      the same reasoning as the C2 box. Done 2026-09-07 from
      `violations/Shared.tsx`: one deliberate defect per rule name both plugins
      ship, and a count. Six draw exactly one. **One draws two**, and it is not
      the kind the conflict configs exist for — `react-hooks/static-components`
      and `@eslint-react/no-nested-component-definitions` are one property under
      **two different names**, which no name-keyed configuration can ever match.
      Four of the twelve could not be tripped at all, which is recorded as a gap
      in the count rather than a pass
- [x] Demote what fails, recording the case that demoted it. Done 2026-09-07,
      and **one demotion**, from C4: `@eslint-react/no-nested-component-definitions`
      is off and `react-hooks/static-components` carries the property alone. The
      case is the nested component that drew both. Nothing else was demoted —
      C5's five fired probes each kept their rule with the reasoning recorded,
      which C5 permits and requires
- [x] Have a second reader resolve S2's contested classifications. Done
      2026-09-06: every recommendation in
      [`assess.contested.md`](assess.contested.md) was taken. Fourteen of the
      fifteen rows moved — two splits, one drop, one `contested` → `incompatible`
      — and `assess.rules.md` § Resolved is the record. **`react.barrel-exports`
      is still marked `contested` because its resolution was that it should be**,
      and `react.no-class-components` was resolved by ADR 0052 rather than by the
      recommendation, which proposed an axis that ADR has since ruled out. The
      register is 182 rows and the shares are re-derived: 71% Python, 76% React,
      21% stack-neutral
- [x] Write `review.bench.md`. Done 2026-09-07. The acceptance criteria were
      written on 2026-09-06 before a scaffold existed; everything after them is
      the result, and the document ends with a verdict against **`plan.md`'s**
      exit criterion rather than against its own heading count. **The criterion
      holds**, over a set of stated residues rather than unstated ones — four
      shared rule names nobody could trip, a contradiction partition that is a
      judgement rather than a proof, and a preview behaviour risk unmeasured
      over anything larger than five hundred lines. § What S3 hands forward is
      the eight things the later stages need
- [x] ~~Choose the trial repositories — at least two Python, at least two React —
      and record why each is representative~~ — struck 2026-09-06. Representative
      of an existing codebase, which is not the target
- [x] ~~Run it unmodified and capture the raw counts~~ — struck 2026-09-06. There
      is nothing to count on a new repository
- [x] ~~Sample the findings for false positives, at a stated sample size~~ —
      struck 2026-09-06, and replaced rather than dropped: a false positive still
      matters and matters more, so it is **probed deliberately** above rather
      than sampled from a corpus that does not exist

## S4 — Design

`design.profiles.md` is written in slices, and its § What this document still
owes is the list of what has not been written — not restated here.

- [x] Decide from S2's evidence whether "archetype" is a real axis or whether
      stack alone carries it — **stack alone**, with the `any.` rows gating on
      evidence rather than on a declared archetype. ADR 0052
- [x] Specify the profile: its axes, its naming, its versioning. **The levels
      are done** — [`design.profiles.md`](design.profiles.md) § The strictness
      levels, 2026-09-07: two per stack, nested, drawn from the register's own
      `Default` column rather than from a fresh opinion. `standard` is exactly
      what S3 benched; `strict` adds eleven Python properties and **one** React
      one. Three findings came with it — the widest reading of
      `python.docstring-form` brings in **`D203` against `D211` and `D212`
      against `D213`**, which ruff warns about and then silently resolves by
      dropping one; **nothing has run `strict`**, so ADR 0051's third
      precondition bars every strict-only rule from ever becoming a control; and
      the axis is asymmetric enough to be suspect, since React's `standard`
      already carries the `Any` appetite Python's `strict` is defined by, for no
      reason but which preset each ecosystem ships. **Naming and versioning
      done 2026-09-07**, `design.profiles.md` § Naming, versioning, and what a
      re-run does: a profile is `<stack>/<level>` and nothing more, and its
      version is a **counter rather than semver** — semver's major position
      means *this will break you*, and for a lint profile the breaking change is
      the added rule semver calls minor, so one number cannot carry both notions
      of significance. Direction is recorded per version instead, in
      `register-variance`'s own three words with its mixed-delta rule unchanged
- [x] Specify what happens when a profile changes under a repository that has
      already installed it. Done 2026-09-07, same section. A re-run compares
      **three** things rather than one: the pinned version against the current,
      the stamp against the file as it stands (which is what detects a hand edit
      made since), and the evidence gates now against the gates at install —
      ADR 0052's named worst moment. **And the installer never writes a
      loosening**: removing selectors is a loosening of LNT-001, which is
      `narrowing-only`, so performing it would knowingly leave a repository
      non-conformant. This **corrects the strictness slice**, which said the
      installer reports a downgrade rather than refusing it
- [x] Specify the config surface per stack, and confirm it introduces no new
      format. Done 2026-09-07:
      [`design.profiles.md`](design.profiles.md) § The config surface. **The
      answer was mostly already written** — `controls.yaml`'s `stacks:` block
      names the tool and the ordered config locations per stack, so Craft
      chooses what goes in a configuration and not where it lives. Writing the
      files again would have been theme T-2 by the most ordinary route
      available. Two of S3's six hand-forwards close here rather than in a later
      slice: **the lockfile is the version pin** and a version in `ruff.toml`
      would be a second copy of it, with the provenance question S3 was actually
      reaching for handed to the register schema in ADR 0038's shape; and **the
      profile was never missing a type checker** — TYP-001 already requires mypy
      and `tsc` at `strict`, which covers two of the register's three
      type-checker rows outright, so Craft's whole contribution across both
      stacks is the one mypy key `--strict` does not set. The section also
      settles which ruff surface the installer writes, on a precedence the bench
      had backwards: a `ruff.toml` **overrides** a sibling `[tool.ruff]` while
      the checker reads the sibling first, so a profile writing the bench's file
      would leave LNT-001 auditing a section ruff no longer applies, and nothing
      warns
- [x] Draft the ADR on the craft/register boundary — when, if ever, a craft rule
      becomes a control. **ADR 0051**, Accepted 2026-09-06
- [x] Draft the ADR on the profile model — **ADR 0052**, Accepted 2026-09-06
- [x] Draft the ADR on attribution and licence posture, per source — **ADR
      0054**, Accepted 2026-09-06
- [x] Check anything a machine will read against ADR 0018 before it enters code
      — **ADR 0053** applies 0018's test to the mapping and answers *data*. The
      test still applies per rule as Craft's code is written, and 0053 requires
      each exception to carry its reason there. **Four exceptions are now named
      and reasoned** — [`design.profiles.md`](design.profiles.md) § What may
      live in Craft's Python: the identity grammar, the level ordering, the
      closed set of instrument shapes, and the rule that a linter citation owes
      a `coextensive:` reason
- [x] Design the Craft register's schema — ADR 0053 left it to this stage. Done
      2026-09-07, `design.profiles.md` § The Craft register's schema, and it
      closes **both** of S3's remaining hand-forwards by making each measured
      mistake unspellable rather than discouraged. One instrument per property,
      alternatives recorded with the reason that stops somebody re-enabling
      them; and an instrument is a **closed set of codes or a linter, never a
      range** — a range rots (`DTZ001`–`DTZ012` missed `DTZ901`) and, read
      widely, over-reaches into contradiction (`D2xx` brings `D203` against
      `D211`). `linter:` requires a `coextensive:` reason and its absence is a
      schema error: the four linters `standard` spells that way all pass the
      test at 0 preview rules, and `pydocstyle` — 48 rules carrying both sides
      of two conventions — fails it. `level` sits on the **binding** rather than
      the property, which is what the strictness slice's third finding asked
      for. **ADR 0053's open question is answered**: the register *replaces*
      `assess.rules.md`, which becomes a stage record like `survey.sources.md`
      beside it, with a superset test rather than a promise holding them
      together
- [x] Design the evidence gates for the 42 stack-neutral rows — ADR 0052's one
      binding consequence. Done 2026-09-07, `design.profiles.md` § The evidence
      gates. **The gate is a `controls.yaml` predicate, not a new mechanism**:
      `terraform: any *.tf file exists` is the infrastructure group's gate
      already written and already read, so a group names a predicate rather than
      describing one, and a name defined in both registers is a schema error.
      The one predicate that does not exist — `openapi-document` — belongs in
      the Craft register and is keyed on the document's own top-level `openapi`
      key rather than on a filename, because a glob both misses and over-matches
      where the tool's own resolution does neither. **The model fits 15 of the
      42**, and the other four groups needed answers about scope: the commit
      group has no artefact and is simply on (its problem is that `commitlint`
      is Node-only and no Python instrument is registered); and the five
      platform rows are **out of scope for a profile** — two cannot even go in
      `gate-repo`'s recorded ruleset, which fails anything not targeting
      `~DEFAULT_BRANCH` — making them candidates for ADR 0051's crossing route
      alongside the one that ADR already names
- [x] Draft the ADR on writing into a control's gated configuration — **ADR
      0055**, Accepted 2026-09-07. **Not anticipated by the four**: the config
      surface slice found that a craft rule installed into a mandated tool
      blocks a merge under a control's name while appearing in neither register,
      which is true of every ruff selector and not only of the mypy key that
      made it visible. Craft may write a gated section, may never write a key
      that control asserts, and records what it wrote
- [x] Get every ADR this stage names to Accepted — the five above are, and the
      box stayed open because the slices still owed might name one they did not
      anticipate. **None did.** Closed 2026-09-08: the last design slice took
      four decisions and the two verdicts the second bench handed S4, all within
      the frame ADRs 0051 to 0055 already set. `plan.md`'s exit criterion for S4
      is met
- [x] Settle whether `craft_contract` gates anything — **it does**, and it is
      not the profile version. The installer is versioned and pinned by a
      consumer, so a repository can hold an old installer reading a new
      register; `craft_contract` moves when the **schema** changes and a
      profile's version when the **rules** do, and conflating them would make
      every rule change look like a format change
- [x] Write `design.profiles.md` — **six sections, and no design question
      outstanding.** The last was written 2026-09-08, § Where the register lives,
      and what checks it, and it closed four of the six rows in the document's
      own § What this document still owes: the register is **`craft/` with one
      file per scope** — `meta.yaml`, `python.yaml`, `react.yaml`, `any.yaml` —
      because a property's identity already carries its scope, so the file it
      belongs in is derivable and a row in the wrong file is a schema error
      rather than a matter of taste; a profile's `changes` entries go in
      **`meta.yaml`**, because a profile spans the per-scope files and per-file
      entries would split one profile's history across two; validation is
      **`tests/test_craft_register.py`** rather than a second checker, because
      an adopter never reads `craft/` and the thing they do run is the
      installer; and the five platform properties are **recorded out of scope
      and nothing is minted**, with ADR 0051's route left open. Two rows remain
      and both are work: the migration, and one source to register
- [x] Migrate the **Python** rows into `craft/python.yaml`, with `craft/meta.yaml`
      and the check beside them. Done 2026-09-08: **73 properties** — the
      register's 72 plus `python.no-any-anywhere`, which S4's strictness slice
      minted and `assess.rules.md` therefore has no row for — 40 bound at
      `standard`, 11 at `strict` and 22 with no binding and a stated reason.
      Every range the register cited is now a closed set or a `linter:` with a
      coextensive reason, which is the S3 finding applied rather than recorded.
      `tests/test_craft_register.py` is the check ADR 0053 said `register-check`
      must not be, and **both its sharpest assertions are shown able to fire** —
      a range in a `codes:` list and a lost row each fail it
- [x] Migrate the **React** rows into `craft/react.yaml` — 68. Done 2026-09-08:
      **48 at `standard`, one at `strict`** and 19 with no instrument. The
      schema gained the distinction the React rows forced: three ways of having
      no instrument rather than one, because *nothing can assert this*,
      *this holds because of a choice made elsewhere* and *somebody else's
      surface owns this* are different claims. `react.no-legacy-proptypes` and
      `react.jsx-runtime-assumed` are the second — satisfied by taking
      `@eslint-react`'s `recommended` as the base — and
      `react.strict-type-checking` is the third, because TYP-001 already gates
      `tsc` in strict mode. `alternatives:` earns its keep here: every
      two-plugin overlap C1 resolved by hand is recorded with the reason that
      stops somebody re-enabling the losing rule
- [ ] Migrate the **stack-neutral** rows into `craft/any.yaml` — 42, including
      the five platform rows, which carry `out_of_scope: profile` and a reason
      in place of an instrument
- [ ] Register a Python-ecosystem instrument for the commit group, so it is not
      Node-only. Survey work under the schema slice's `sources:` — `commitlint`
      is the registered instrument and it needs Node

## The second bench — `strict`

**Not a stage.** S3 benched `standard` and met its exit criterion; S4 then
defined a level above it, and ADR 0051's third precondition means no strict-only
rule is eligible to become a control until somebody measures it.
[`review.strict.md`](review.strict.md) is that measurement, and its § What has
not run is the list — not restated here, for the reason `plan.md` and this file
are two documents. **Finished 2026-09-08**, and that section records the
verdict: every rule the level adds has been measured, so ADR 0051's third
precondition no longer bars any of them.

- [x] Parameterise `craft_profile.py` on the level, and materialise `strict`.
      Done 2026-09-07, `--level strict`. Every file **extends** its `standard`
      counterpart rather than restating it, because S4 defines the level as a
      superset and two selector lists would be free to disagree with that
- [x] C1 — the strict configuration assembles. Done 2026-09-07: **172 rules**
      against `standard`'s 140, **32 added and none removed**, which is the
      design's own narrow-reading number; `preview = true` enabled exactly the
      two rules it was asked for; React's 121 against 120 is the one-rule
      asymmetry as configuration
- [x] C3 pass 1 — the formatter-conflict check, **and shown able to fire**.
      Silent over the narrow reading; both `D203`/`D211` and `D212`/`D213` warn
      under the wide reading S4's schema slice rejected, with ruff dropping one
      side of each. The schema rule run rather than reasoned
- [x] C2, the clean direction. **The scaffold was not clean.** `D401` was the
      scaffold's own defect — PEP 257 asks for imperative mood and no `standard`
      rule reads docstring prose, so nothing had ever looked; corrected in
      `craft_scaffold.py`, with `standard`'s runs re-verified untouched
- [x] Resolve the demotion candidates the clean and violation runs left
      standing. Done 2026-09-07, C5. **`TRY003` is demoted** — it is satisfied
      by `EM101`'s own remedy while the message stays outside the exception
      class, which is a rule claiming enforcement it does not have, and
      `plan.md` says this workstream will not ship one. It costs no verdict:
      every defect it reported is still reported by `EM101` or `EM102`.
      **`TC003` is kept and the profile was missing a key** — the probe showed
      the remedy raising `NameError` where `get_type_hints` resolves the
      annotation, and ruff's `runtime-evaluated-decorators` clears exactly that
      shape, so nothing needs splitting after all. **`D103` on tests is not
      C5's to take**: it is a selection question, and the mechanism that fits is
      the one `S101` already uses
- [x] C2's other half — one deliberate defect per new rule. Done 2026-09-07:
      `cases/strict/` is the 32, split by what a defect has to *be* rather than
      by property, with the two preview rules keeping the cases C8 wrote for
      them; `react/violations/Effects.tsx` is the React half. **The check is a
      command** — `craft_cost.py --fires` derives the additions by resolving the
      strict selection against the standard one and compares them against a run,
      and it is shown able to fire. **Two findings, and the second is the one
      C2 exists for.** `TRY003` fires only inside `EM101`/`EM102`, above; and
      **React's one added rule was inert** — `'error'` alone resolves at
      severity 2 and reports nothing, because the rule is a view onto the
      compiler analysis that `validateExhaustiveEffectDependencies` gates `off`,
      reachable from the rule's options and not from its severity. Corrected in
      `craft_profile.py`. C1's count of 121 against 120 was true before the
      correction and after it, which is what a count cannot see
- [x] C4 at `strict`, which was recorded as not applicable and is not. Done
      2026-09-07: one duplicated defect per stack — React's added rule against
      `exhaustive-deps` on a missing dependency, where the added rule's whole
      margin is the *extra*-dependency direction, and `TRY003` against `EM101`
      in Python. `'extra-only'` would remove the React duplicate and is **not
      taken**: narrowing an instrument to dodge a duplicate leaves the register
      asserting a property its configuration no longer enforces, so the
      alternative and its reason go in the Craft register's `alternatives:`
      field, which is the mechanism S4's schema slice built for it
- [x] The scaffold's second defect, found the same way as the first. `D205` on
      `tests/__init__.py` — a docstring written during the *first* bench, to
      explain the file `INP001` asks for, wrong since the day it was written
      because no `standard` rule reads a docstring's shape. Corrected in
      `craft_scaffold.py`, `standard`'s runs re-verified untouched
- [x] C3's construct partition and witnesses, over the 32 new rules. Done
      2026-09-07: **5,008 new pairs down to 125 candidates**, six witnesses
      clean at both levels, and **no contradicting pair**. The sharpest
      candidate the additions brought — `TC`'s `if TYPE_CHECKING:` remedy
      against `PLC0415`'s *no import below the top level* — was cleared by
      running it rather than arguing it. The witnesses are the first bench's
      **extended**, so one set has to be clean at both levels rather than two
      sets free to disagree. Two findings about the witnesses themselves: the
      React one had no `useEffect` in it at all, so the rule that group gained
      cleared nothing until an effect was added and shown to fire when broken;
      and the test witness got the docstrings the scaffold did not, because a
      case exists to satisfy the instrument and a subject does not
- [x] Resolve `python.no-untracked-todo`, whose eleven codes could not all be
      satisfied by a file containing a TODO. Done 2026-09-07, C5's second
      demotion: **`FIX001`-`FIX004` are dropped**, because the property's text
      is *a TODO names an owner or an issue* and `FIX002` asserts *no TODO at
      all* — a stronger claim than any source in the register proposes, and one
      that made seven of the eleven codes unreachable. The demotion pays for
      itself in the same run: the marker-comment group now has the clean witness
      C3 could not write
- [x] C5 — probes for the rules with a false-positive reputation. Done
      2026-09-07: six probes, three fired, **two did not and each has a control
      beside it** — `RET504` skips an annotated assignment and `D401` exempts a
      property, so two of the six were written against a version of the rule
      that no longer exists. `S104`, `PLC0415` and `EM101` are kept with the
      reason each; `PLC0415` is this level's `ERA001`, the one to put to S6
- [x] C7 — cost per finding for the 27, from `fix_availability`. Done
      2026-09-08, and it went past the criterion: **the metadata was read and
      then checked against a run**, which C7 was defined as not needing and
      which is exactly why nobody had checked it. The declared answer is that
      the additions are the expensive end — **70% carry no fix** against the
      level's 54% and `standard`'s 51%, concentrated in writing English
      (`D1xx`, `D401`) and supplying information (`TD002`, `TD003`). The run
      disagrees with the declaration: across both levels **30 rules fired
      declaring a fix and five applied one**. Ruff's `fix_availability` is a
      property of the rule while applicability is a property of the diagnostic,
      so six of the additions' eight fixes need `--unsafe-fixes` — including
      `RET504`, which the taxonomy calls `always`. **Fourteen React rules
      declare `meta.fixable` and fix nothing**, nine of them `react-hooks`,
      which corrects the first bench's *cheapest group in either stack* row in
      `review.bench.md` § What each rule costs. `--fix-applies` is the mode, and
      it is shown able to fire before its silence is read
- [x] Run the mypy half at all. Done 2026-09-08 at **mypy 2.3.1**, and it is
      the row ADR 0051's precondition is really about. **The margin is none
      against ten**: `strict = True` alone reports nothing on a file writing an
      explicit `Any` in every place one can be written, and the key reports ten
      findings over nine sites — so Craft's one type-checker contribution across
      both stacks is not redundant with TYP-001, which the design had answered
      from `--strict`'s flag list rather than from a run. **A hazard came
      first**: mypy walks up from the bench and finds this repository's own
      `[tool.mypy]` three levels above a gitignored directory, and a comparison
      run without `--config-file` reported that nine of `--strict`'s flags were
      already default — entirely an artefact of reading `strict = true` from
      here. **C4 fires twice more.** An `Any` on a dataclass field reports at
      the field *and* at the class, because the plugin synthesises an `__init__`
      carrying it; and `ANN401`'s findings are a **strict subset** of the key's,
      so every one is reported twice under two property names — which the
      profile model *guarantees* rather than overlooks, because the levels nest
      and the installer never writes a loosening. **C5's four probes are
      clean**: `ParamSpec`, a `TypedDict` and `object` remove every shape the
      rule's reputation is built on, which is a reputation about an older Python
- [x] Reword `python.no-any`, or record that its instrument over-reaches it.
      Done 2026-09-08, **and the wording stands**. Rewording a property to match
      whatever its instrument happens to do would make the register a
      description of ruff rather than a statement of what Equal Experts asks of
      code, and the next time the tool changed the property would change with
      it. `assess.rules.md` § Corrected by measurement is the record — a new
      section, because a finding made *while assessing* and a finding made
      afterwards by a stage that ran the tool are different things
- [x] Take the `D103`-on-tests verdict the second bench handed S4. Done
      2026-09-08: `D100`-`D107` are selected in **`src/strict.toml`**, the
      mechanism `S101` already uses, rather than `per-file-ignores`, which the
      register's own resolution rejected. The property is scoped, not weakened —
      a test's name is its documentation and `python.docstring-form` stays at
      the root, because a docstring that exists should be well formed wherever
      it is. **159 rules now resolve under `tests` against 168 under `src`**,
      the scaffold's four `D103`s are gone and nothing else on it moved. It also
      moved a check that would have gone quiet: `craft_cost.py --fires` read the
      root config, where eight of the level's own rules would have reported as
      never having fired

## S5 — Build the chooser and the installer

- [ ] Specify the skill's configuration contract, in the shape
      `.claude/skill-config.yaml` already uses
- [ ] Infer the stack from the repository. **Not an archetype** — ADR 0052
      ruled it out as an axis, and the stack-neutral groups gate on the artefact
      they read being present instead
- [ ] Present each applicable profile with what it enables **and** what S3 found
      each rule costs to satisfy
- [ ] Require an explicit confirmation before anything is written
- [ ] Write the pinned configuration at every locus the profile declares
- [ ] Record what was written, **including which stack-neutral groups the
      evidence gates switched on and what switched them** — ADR 0052 requires it,
      because a gate nobody can see is the invisible suppression it rejected.
      **The gates are designed** — [`design.profiles.md`](design.profiles.md)
      § The evidence gates, 2026-09-07 — and the stamp line is specified there;
      writing it is this box
- [ ] Emit the judgment-only residue as prose an assistant loads, labelled
      unenforced
- [ ] Make a second run over its own output change nothing
- [ ] Version and publish it so a consumer repository can pin it
- [ ] Write `build.installer.md`

## S6 — Trial and review

- [ ] Choose the trial repository — a **new** one, at its start — and agree the
      period before installing
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
