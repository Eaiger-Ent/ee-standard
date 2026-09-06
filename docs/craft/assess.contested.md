# Craft — the contested classifications

Stage **S2** of [`plan.md`](plan.md), written for stage **S3**. Fifteen rows in
[`assess.rules.md`](assess.rules.md) are marked `contested`. This document sets
out two ways to resolve each, what each way costs, and which one the assessing
stage would pick.

**It resolves nothing.** `plan.md` § S3 gives contested classifications to a
second reader, and S2's exit criterion holds precisely because none of them was
resolved silently. Every one of the fifteen is still marked `contested` in the
register, every count that document publishes is unchanged, and four
recommendations below would change the register's *shape* — splitting an
identity, dropping one, treating two rows as one — and have deliberately not
been applied. A stage that prepared the options and then took them is not a
stage that had a second reader.

**The recommendations are S2's view, and they are marked as such** so a reader
knows what they are disagreeing with. They are an opinion formed while reading
the sources, which is worth writing down and is not worth mistaking for a
decision. Anchoring is the known cost: a second reader who arrives to fifteen
recommendations is a weaker check than one who arrives to fifteen neutral pairs.
The trade was made deliberately, in favour of the read being possible at all.

Written **2026-09-06**, against the register as it stands at that date.

## How to read a row

Each row gives the contest in one line, then **A** and **B**, then the view. The
options are alternatives, not a ranking: B is not "the better A". Where a row's
resolution depends on a measurement, the measurement is named and belongs to S3
rather than to whoever reads this.

Rows are numbered 1–15 for reference in review; the numbers are not identities
and nothing should ever cite them. The identity is the key, as it is everywhere
else in this workstream.

## Python

### 1. `python.no-silent-exception-swallow`

Ruff `S110`/`S112` forbid `try`/`except`/`pass`; ruff `SIM105` recommends
`contextlib.suppress`, which is the same swallow spelled differently. One tool,
two rules, opposite advice.

**A — select `S110`/`S112`, deselect `SIM105`.**
*For:* one voice, and it is the source's — `code-quality`'s "do not throw
away/ignore errors" is honoured without qualification. Every swallow is flagged.
*Against:* `contextlib.suppress` is idiomatic, readable, and the recommended
form in the standard library's own documentation. Deselecting the rule that
suggests it means the profile argues against the language.

**B — select all three; restate the property as "a swallow must be *explicit*".**
*For:* the rules stop disagreeing under that reading. `suppress(ValueError)` is a
decision recorded in code and reviewable; `except: pass` is a decision nobody
made. Nothing is deselected, so the profile stays a subset of the tool's own
advice.
*Against:* the Asserts column has to change, and the source's rule is then only
partly honoured — a deliberate swallow is still a swallow, and `code-quality`
did not carve it out.

**S2's view: B.** The contest is between a rule and a *phrasing* of the property,
not between two rules.

### 2. `python.exception-message-not-inline`

Ruff `EM101`/`EM102`/`TRY003` push messages out of the raise site;
`clean-code 202` asks for descriptive error messages.

**A — leave off, as registered.**
*For:* `EM` forces a local variable purely to satisfy the linter, with no benefit
to any reader; `TRY003` pushes toward a custom exception class per message, which
is an architectural commitment a lint profile should not make on a team's behalf.
*Against:* abandons message quality entirely — nothing else in the register
asserts it, and bad exception messages are a real and common defect.

**B — split the identity in two.** `EM101`/`EM102` are about *where the string
literal lives*, which is a traceback-formatting concern. `TRY003` is about *how
much the message says*, which is a design concern. They are different properties
that happen to fire on the same line.
*For:* the contest dissolves. `clean-code 202` conflicts with neither half; it
conflicts with the bundle. This is the shape the hand check already forced once,
on `python.naming-form` and `python.naming-intent`.
*Against:* one more identity, and both halves stay `off`, so the split buys
clarity rather than enforcement. **Structural — not applied.**

**S2's view: B**, on the strength of the precedent rather than of the outcome.

### 3. `python.function-length`

`clean-code 002` says under twenty **lines**. Ruff `PLR0915` counts statements
(default 50) and `C901` counts cyclomatic complexity. Neither is the assertion.

**A — accept the proxies, calibrate `PLR0915` against a corpus at S3, and rewrite
the assertion to what the tool measures.**
*For:* the register stops claiming a line count nothing enforces, which is
`plan.md`'s own prohibition on shipping a rule that claims enforcement it does
not have. A statement count is a defensible proxy and a measurable one.
*Against:* a twenty-statement function can be sixty lines. The source's intent —
*readable in one screen* — is not what survives.

**B — keep the assertion and demote to bucket 3**, citing the rules as related
but not the property.
*For:* preserves the intent exactly; a reviewer still has `PLR0915` to lean on
without the register pretending it is the rule.
*Against:* bucket 3 means nothing runs, and "this function is too long" is the
single most common review complaint. Losing all enforcement for definitional
purity is a poor trade.

**S2's view: A**, with the number set by S3's measurement rather than by either
source.

### 4. `python.function-parameter-count`

`clean-code 101` says no more than three. Ruff `PLR0913` defaults to five.

**A — take ruff's five.**
*For:* the tool's default, so nothing is configured and nothing drifts; S3 can
measure it at no cost.
*Against:* silently overrides a registered source with a linter's compromise
number. Five is where a tool lands to avoid arguments, not a considered position.

**B — `PLR0917` (positional) at three, `PLR0913` (total) at five.**
*For:* honours both. The toolkit's real concern is positional argument soup at
the call site, which is exactly what `PLR0917` measures; keyword-only parameters
do not damage readability the same way, so five is right for the total. Under
this reading the sources were never disagreeing — they were counting different
things.
*Against:* two numbers to explain, and `PLR0917` is much less familiar than
`PLR0913`, so the profile is harder to read.

**S2's view: B.**

### 5. `python.return-count`

Ruff `PLR0911` limits exit points; `clean-code 102` recommends early returns to
avoid deep nesting. Each early return increments the count.

**A — leave off permanently, recorded as a genuine incompatibility.**
*For:* it cannot be resolved by configuration. Early returns are the recommended
fix for nesting, and both rules on means two rules fighting over the same
function, with the developer caught between them. Recording it as incompatible is
more useful than recording it as untuned.
*Against:* nothing then constrains a function with fifteen exits, which is a real
shape and a hard one to read.

**B — on with a high ceiling, eight to ten.**
*For:* keeps a guard on the pathological case; the two rules only collide at low
ceilings, so a high one buys the guard without penalising the good pattern.
*Against:* the number is chosen to avoid a fight rather than to assert anything.
At eight to ten it will almost never fire on real code, so the profile carries a
rule that costs a line of configuration, an entry in whatever S5 hands back, and
never catches anything — which is a rule kept for the look of it.

**S2's view: A**, and the incompatibility is worth recording in its own right —
it is the only row here where two rules from the same tool cannot both be on.

### 6. `python.line-length`

`pep8` says 79, `google` says 80, ruff defaults to 88, this repository uses 100.
Four sources, four numbers.

**A — adopt ruff's 88 as the profile's fixed value.**
*For:* it matches `ruff format`'s default, so formatter and `E501` never
disagree — which is the failure that actually costs a team time, far more than
the number itself.
*Against:* contradicts both prose sources outright, and this repository uses 100,
so the profile would differ from its own author's repository on the day it ships.

**B — make it a profile parameter, default 88, constrained to equal
`ruff format`'s configured line length.**
*For:* the number is a preference with no correctness content, and the property
that *is* assertable is "a limit exists and the formatter agrees with it".
Constraining the two to match enforces the part that matters and leaves the part
that does not to the team.
*Against:* a parameter is a knob, and every knob is a question S5's installer has
to ask. It also lets a team set 200, which meets the letter and abandons the
property.

**S2's view: B**, with the formatter-agreement constraint doing the real work.

### 7. `python.no-any`

Ruff `ANN401` sees annotations only. mypy `strict` does **not** ban `Any`;
`disallow_any_explicit` does, and is not part of `strict`.

**A — add `disallow_any_explicit` on top of strict.**
*For:* the only setting that asserts the property. `ANN401` misses every
`cast(Any, ...)`, every untyped decorator and every `Any` in a local binding.
*Against:* brutal on real code. Any dependency without stubs forces a
`# type: ignore`, and a profile that generates ignore comments is a profile that
teaches suppression — which is the opposite of what LNT-001 and TYP-001 exist to
prevent. S3 will most likely measure it as unusable.

**B — keep `ANN401` and narrow the property to "`Any` does not appear in a public
signature".**
*For:* enforceable, measurable, and aimed at the case that damages callers rather
than the case that annoys the author.
*Against:* a narrower promise than `typescript 002` made. Internal `Any` still
spreads, and it spreads into public signatures eventually.

**S2's view: B** for the default profile, with **A** kept as a strict-profile
variant for S3 to measure rather than discarded.

### 8. `python.no-assert-for-enforcement`

Ruff `S101` asserts the property and fires on every test in the repository.

**A — select `S101` globally with a `per-file-ignores` entry for `tests/`.**
*For:* one line of configuration, and it is what essentially every published
ruff config does.
*Against:* a path-based exemption is a **weakening** by `docs/00-concepts.md`'s
own definition, and this repository's `narrowing-only` controls admit none. The
profile would ship, to other teams, a pattern its author's register forbids in
its own configuration — and `[tool.ruff]`'s own comment records the eleven
violations the last such exclusion hid.

**B — scope the rule to the package source path**, so tests are never in scope
rather than being excused from it.
*For:* no exemption exists, so none can drift or hide anything. The rule's scope
then matches the property's scope, which is what the property already says:
*runtime* enforcement.
*Against:* the profile has to know the repository's source layout, which pushes
work into S5's inference step and makes the generated config less portable.

**S2's view: B** — and this row should go to S4 regardless of which is chosen. It
is the first place a craft profile would otherwise import a pattern the register
treats as a weakening, and that is a boundary question, not a configuration one.

## React

### 9. `react.no-class-components`

`@eslint-react/no-class-component` exists, is `strict`-only, and asserts a
migration position rather than a correctness one.

**A — drop the identity at S4.**
*For:* a working class component is not bad code. A rule that fires on every
legacy file on install is precisely the day-one noise S3 exists to prevent, and
it teaches a team to ignore the tool.
*Against:* loses the signal on *new* class components, which is the only case
anyone actually cares about.

**B — keep, default off, and mark it as a profile axis** — on for a greenfield
profile, off for an existing codebase.
*For:* the disagreement is entirely about *when*, and "when" is what a profile
axis is for. The property is real for new code and indefensible for old.
*Against:* it is evidence for an axis about **codebase age**, which is a third
dimension neither `plan.md` nor S2 has considered, and adding axes is how a
profile model becomes unusable.

**S2's view: B**, with the axis observation handed to S4's decision 2 — where
`plan.md` deferred the archetype question pending exactly this kind of evidence.

### 10 + 11. `react.no-legacy-proptypes` and `react.jsx-runtime-assumed`

**These are one contest, not two.** Both rows exist because
`eslint-plugin-react`'s `recommended` config asserts something wrong for React 17
and later with TypeScript: `react/prop-types` duplicates what the compiler
already checks, and `react/react-in-jsx-scope` is obsolete. Registering them as
two contested rows describes the symptom twice.

**A — install `recommended` plus the `jsx-runtime` config, and deselect
`react/prop-types`.**
*For:* the plugin ships half the fix itself. Seventeen years of institutional
history, broad familiarity, and the widest rule coverage of any React plugin.
*Against:* a config whose only job is to undo two rules from the config above it
is a second copy inside one file, and a reader has to know both to know what is
on. The other half is a documented deviation S5's installer must explain on every
run.

**B — take `@eslint-react`'s `recommended` as the JSX-correctness base instead.**
It ships neither `prop-types` nor `react-in-jsx-scope`, so neither question
arises.
*For:* removes the deviation rather than documenting it, and settles finding 2's
double-reporting in the same move — one plugin, one answer to *which rules are
on*.
*Against:* it is one maintainer's plugin against the long-standing one, and the
succession finding 2 records — `eslint-plugin-react` seventeen months without a
release, `@eslint-react` published the day of the survey — is exactly what makes
this a bet rather than a choice.

**S2's view: B**, contingent on S3 confirming rule coverage against the 104 rules
`eslint-plugin-react` carries. **Structural — not applied:** merging the two rows
would change the register's React count and its stated shares, and the merge is
an argument rather than a correction.

### 12. `react.explicit-return-types`

`@typescript-eslint/explicit-module-boundary-types` asserts `typescript 003`
exactly, and is in no recommended preset.

**A — turn it on.**
*For:* it is the property, without a proxy in sight. Cross-module inference is
where TypeScript's error messages are worst and where an explicit annotation buys
the most.
*Against:* no preset ships it, for a reason. On React components the return type
is always the same and writing it adds nothing, so the count will be high and the
value per finding low.

**B — on with `allowTypedFunctionExpressions`, component files out of scope** —
asserting it for exported non-component functions only.
*For:* keeps the value at library boundaries and drops the noise in the UI layer,
which is where the rule's reputation comes from.
*Against:* "component" is a naming heuristic, so the scope is approximate and
will be wrong somewhere; and the split needs S3 to confirm it is worth the extra
configuration.

**S2's view: B**, measured at S3.

### 13. `react.interface-over-type`

`@typescript-eslint/consistent-type-definitions` is a style choice with no
correctness argument, and `@antfu/eslint-config` takes the opposite default.

**A — drop the identity.**
*For:* no correctness, accessibility or performance content. A source asserting a
preference is not a property, and keeping the row invites S5's installer to ask a
question that has no right answer.
*Against:* discards one small genuine argument — declaration merging works on
`interface` and not on `type` — and it is the only technical content the rule
has.

**B — keep, default off, stating that the value is *consistency* rather than
either choice.**
*For:* honest about why the row exists. Consistency is a real property even when
neither option is better.
*Against:* the register then holds a row whose assertion is "pick one", which is
not what the Asserts column is for, and which no instrument can check without
first being told which one.

**S2's view: A. Structural — not applied.** Of the fifteen this is the one that
most reads like a rule written because a style guide needed a section.

### 14. `react.barrel-exports`

`typescript 203` asserts barrel exports. Current practice argues against them on
bundle-size and circular-import grounds.

**A — invert it.** Register `react.no-barrel-exports` and cite the source as
asserting the opposite.
*For:* the evidence has moved. A register that carries a position because a 2024
file stated it is carrying a stale claim, and stale claims are what the
maintenance column exists to catch.
*Against:* inverting a registered source on our own judgment is exactly what S1
refused to do. We would be asserting against a source with no source of our own,
which is worse than carrying the disagreement.

**B — keep as registered, marked contested and unendorsed**, and require S4's
attribution decision to cite a source *for* the inversion before it moves.
*For:* the register cites; it does not opine. The discipline that produced
findings 3 and 9 in the survey is the same discipline here.
*Against:* leaves a row in the register that nobody intends to ship, which is its
own kind of noise.

**S2's view: B. Structural — not applied.** This is the clearest case where
`llm-toolkit` is a source of ideas and not of positions, which is finding 8's
conclusion applied to a second file.

### 15. `react.a11y-link-purpose`

WCAG 2.4.4 is the requirement. `jsx-a11y/anchor-ambiguous-text` is the only rule
that asserts it, and it is `off` in `recommended`.

**A — enable `anchor-ambiguous-text` with the default word list.**
*For:* the only instrument that asserts the property. `anchor-has-content` and
`anchor-is-valid` check that an anchor has *any* content, which is a much weaker
claim than that its purpose is clear.
*Against:* it is off by default because it false-positives on legitimate copy,
and it cannot see `aria-label`, so it will flag links that are in fact
accessible. A rule that penalises correct work is worse than no rule.

**B — leave off; demote the property to bucket 3 citing WCAG 2.4.4**, and keep
`anchor-has-content`/`anchor-is-valid` under a narrower
`react.a11y-link-has-content`.
*For:* stops the register claiming enforcement it does not have, which is
`plan.md`'s own prohibition, and keeps the two rules that do work.
*Against:* 2.4.4 is a real requirement, and the profile then offers nothing for
it beyond prose.

**S2's view: B** for the default, with **A** as a targeted false-positive
measurement at S3. This is the accessibility twin of the contrast finding: the
requirement is real and the instrument is not equal to it.

## Two things the fifteen have in common

**Three of them are not contests between sources at all.** Rows 1, 2 and 15
resolve the same way — by splitting or restating a property that was bundling two
assertions. Row 1's sources agree once "swallow" is distinguished from "silent
swallow"; row 2's conflict is with the *bundle* of `EM` and `TRY003`, not with
either; row 15's property is two claims wearing one identity. That is the same
failure the hand check found in `clean-code.md`, arriving from the other
direction: there a machine bundled a tool's rules into a property, here a property
was minted over rules that were never one thing.

**Four of the fifteen argue for editing the register rather than picking a
side** — rows 2, 10+11, 13 and 14. None has been applied. If S3's reader accepts
even two of them, `assess.rules.md`'s row count and its stated bucket shares
move, so the shares should be re-derived after that reading rather than treated
as settled. The command that derives them is in that document.

## What this document does not do

- **It does not resolve anything.** All fifteen rows remain `contested` in
  `assess.rules.md`, and its exit criterion is unaffected.
- **It does not apply the four structural recommendations**, which would change
  the register's shape and every count published with it.
- **It does not measure.** Rows 3, 6, 7, 10+11, 12 and 15 name a measurement, and
  every one of those belongs to S3.
- **It does not add work.** `todo.md`'s existing second-reader box under S3 is
  the box this document is written for; no new open item was invented to hold it.
