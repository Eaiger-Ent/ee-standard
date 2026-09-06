# Craft — the source register

Stage **S1** of [`plan.md`](plan.md). One row per source, assessed **as a
source** before a single rule is read from it, so that a stale blog post and a
language's own documentation are never weighed the same.

Every column was established by reading the thing itself — `gh api` for
repository metadata and licence files, the npm registry for publish dates,
`curl` for the cited URL, and the pinned clone for `llm-toolkit`. Where GitHub's
licence detection and the repository's own licence file disagree, the file wins
and the row says so. Rows were taken on **2026-09-05**; the rows and corrections
this stage's own review added were taken on **2026-09-06**, as were the six rows
S2's pass found missing — see findings 10 and 11. The commands are in
[How to re-run this sweep](#how-to-re-run-this-sweep), because a maintenance
signal nobody can re-derive is a claim rather than a measurement.

**A blank licence is a finding, not an omission.** One source has no licence at
all; it is registered with that stated, because a source we may not copy from is
a different kind of source, not a missing one.

## How to read a row

| Column | What it holds |
| --- | --- |
| Source | What the thing is, not what we intend to do with it |
| Licence | The answer, and how it was established where detection was wrong or absent |
| Maintenance | The most recent *published* signal — a release where the source releases, a commit where it does not. A repository push is the weakest of these and is labelled as such |
| Authority | What the source has standing to say, which is not the same as who publishes it. One of **stack** (published by the people who define the language or library, so it can say what good code *is*), **tool** (authoritative about what that tool will flag, and about nothing beyond it), **standards body**, **community**, **internal**. A source can be both, and the two rows that are say so |
| Covers | What it claims to cover — its claim, not our assessment of it. Assessment is S2 |

## Python

| Source | URL | Licence | Maintenance | Authority | Covers |
| --- | --- | --- | --- | --- | --- |
| ruff's rule taxonomy | <https://docs.astral.sh/ruff/rules/> | MIT | 0.16.6, released 2026-09-03 | tool | 969 rules at the 0.16.5 this repository pins — 812 stable, 140 preview, 17 removed — across 58 stable linters. **Corrected 2026-09-06 by S2**, which read the taxonomy as JSON: the 59 counted a rule with no code and no linter — pycodestyle, pyflakes, pylint, bugbear, pyupgrade, isort and more, under stable codes with fix availability declared per rule |
| PEP 8 — Style Guide for Python Code | <https://peps.python.org/pep-0008/> | **Public domain**, stated in the document's own Copyright section. GitHub reports `NONE` for `python/peps`, which is detection failing rather than an absent grant | Repository last pushed 2026-09-03; the PEP itself is stable by design | stack | Layout, naming, comments, and the explicit instruction that a style rule may be broken when applying it hurts readability |
| PEP 20 — The Zen of Python | <https://peps.python.org/pep-0020/> | **Public domain**, stated in the document's own Copyright section | Stable; unchanged for years by design | stack | Nineteen aphorisms. Judgment-only in every line — registered because it is the reference other sources appeal to, not because a machine can hold it |
| PEP 257 — Docstring Conventions | <https://peps.python.org/pep-0257/> | **Public domain**, stated in the document's own Copyright section | Repository last pushed 2026-09-03; the PEP is stable | stack | What a docstring is for, and the one-line and multi-line forms. ruff's entire `D` family implements it through pydocstyle, so this is the authority behind a block of rules the taxonomy alone would leave unexplained |
| Google Python Style Guide | <https://google.github.io/styleguide/pyguide.html> | **CC BY 3.0**, read from `google/styleguide`'s `LICENSE`. GitHub reports `NOASSERTION` | Repository last pushed 2026-06-03 | community, widely adopted | An opinionated superset of PEP 8 — imports, exceptions, type annotations, docstrings, with a stated rationale per rule |
| pytest good practices | <https://docs.pytest.org/en/stable/explanation/goodpractices.html> | MIT | 9.1.1, released 2026-06-19 | stack + tool | Test layout, `conftest` scope, fixture use and import modes |
| OWASP ASVS | <https://owasp.org/www-project-application-security-verification-standard/> | CC BY-SA 4.0 | v5.0.0, released 2025-05-30; repository pushed 2026-09-03 | standards body | Application security verification requirements at three levels. **Share-alike**, which constrains reuse differently from every other row here |

## React

| Source | URL | Licence | Maintenance | Authority | Covers |
| --- | --- | --- | --- | --- | --- |
| Rules of React | <https://react.dev/reference/rules> | CC BY 4.0, from `reactjs/react.dev`'s `LICENSE-DOCS.md` | Repository last pushed 2026-09-03 | stack | Purity of components and hooks, the rules of hooks, and what React may assume — the constraints the compiler relies on |
| You Might Not Need an Effect | <https://react.dev/learn/you-might-not-need-an-effect> | CC BY 4.0 | Repository last pushed 2026-09-03 | stack | The single richest source of React anti-patterns: derived state, effect chains, and event logic misplaced into effects |
| `eslint-plugin-react-hooks` | <https://github.com/facebook/react/tree/main/packages/eslint-plugin-react-hooks> | MIT | 7.1.1, published to npm 2026-04-17; React itself released 19.2.8 on 2026-07-21 | stack + tool | The enforceable half of the Rules of React, including the compiler-backed rules added in 6.x and 7.x |
| `typescript-eslint` | <https://typescript-eslint.io/users/configs> | MIT | v8.69.0, released 2026-08-31 | tool | Typed lint rules; `recommended-type-checked` is the configuration this stage registers as a source, not as an adoption |
| `eslint-plugin-jsx-a11y` | <https://github.com/jsx-eslint/eslint-plugin-jsx-a11y> | MIT | v6.10.2, published to npm **2024-10-26**; repository last pushed 2026-01-06 | tool | Static accessibility rules over JSX. The quietest source registered — see findings |
| WCAG 2.2 | <https://www.w3.org/TR/WCAG22/> | W3C Document License, read from `w3c/wcag`'s `LICENSE.md`. GitHub reports `NOASSERTION` | Repository last pushed 2026-09-04; the Recommendation itself is stable | standards body | The accessibility requirements the lint plugin above approximates, and the durable authority behind them |
| Testing Library guiding principles | <https://testing-library.com/docs/guiding-principles/> | MIT | `@testing-library/react` 16.3.3, published 2026-08-27; `dom-testing-library` v10.4.1, 2025-07-27 | tool | What to query, what not to assert, and the principle the query priority encodes |
| `eslint-plugin-testing-library` | <https://github.com/testing-library/eslint-plugin-testing-library> | MIT | 7.16.2, published to npm 2026-03-24; repository pushed 2026-09-06 | tool | The enforceable half of the row above — query priority, awaiting async utilities, and reaching into the DOM. **Added 2026-09-06 by S2**, which found the principles registered without an instrument |
| `eslint-plugin-react` | <https://github.com/jsx-eslint/eslint-plugin-react> | MIT | v7.37.5, published to npm 2025-04-03; repository pushed 2026-07-30 | tool | JSX correctness — keys, index-as-key, dangerous props, prop handling. The long-standing plugin, and slowing: no release in seventeen months |
| `@eslint-react/eslint-plugin` | <https://eslint-react.xyz/docs/rules/overview> | MIT | **5.18.9, published to npm 2026-09-06** — 5.18.8 the day before, which is the one row S2's re-run moved | tool | The same ground rewritten for flat config and typed rules. The active successor to the row above, and the plugin `@antfu/eslint-config` actually delegates React to |
| `@antfu/eslint-config` | <https://github.com/antfu/eslint-config> | MIT | v9.5.1, released 2026-09-02 | community, opinionated | One opinionated flat config, **read as a source and not adopted** — registered to see which rules an opinionated author turns on, and why. Its React coverage is not its own: it delegates to `@eslint-react/eslint-plugin` and `eslint-plugin-react-refresh` (0.5.6, 2026-09-02) through optional peers, both registered or named here rather than left behind the wrapper |

## Stack-neutral instruments and the standards behind them

**Added 2026-09-06 by S2.** These were reached by asking *what would enforce
this* rather than *what did we register*, which is the right direction and means
the survey was one pass behind the assessment. Five rows: two instruments the
assessment's stack-neutral properties cite, one instrument a single React
property cites, and the two standards the first two approximate — registered alongside
them for the same reason WCAG is registered alongside `jsx-a11y`. If the tool
stops, the requirement does not.

| Source | URL | Licence | Maintenance | Authority | Covers |
| --- | --- | --- | --- | --- | --- |
| Conventional Commits 1.0.0 | <https://www.conventionalcommits.org/en/v1.0.0/> | MIT, read from `conventional-commits/conventionalcommits.org` | Repository last pushed 2026-03-11; the specification is at 1.0.0 and stable by design | community, widely adopted | The commit message grammar — type, optional scope, description, body and footers, and what a breaking change looks like |
| `commitlint` | <https://commitlint.js.org/> | MIT | `@commitlint/cli` and `@commitlint/config-conventional` both 21.2.2, published to npm 2026-08-13 | tool | Commit message linting against a configurable rule set; `config-conventional` is the row above expressed as rules |
| OpenAPI Specification | <https://spec.openapis.org/oas/v3.2.0.html> | Apache-2.0 | 3.2.0, released 2025-09-19; repository pushed 2026-09-01 | standards body | The description format every API row's evidence is written in. Not a source of rules — a source of the artefact the rules are checked against |
| `spectral` | <https://docs.stoplight.io/docs/spectral/674b27b261c3c-overview> | Apache-2.0 | `@stoplight/spectral-cli` 6.16.3, published to npm 2026-08-03; repository pushed 2026-09-05 | tool | Linting an OpenAPI or AsyncAPI document against a rule set. The instrument behind nine `any.` rows, and it can say nothing about an API with no description document |
| `eslint-plugin-promise` | <https://github.com/eslint-community/eslint-plugin-promise> | ISC | 7.3.0, published to npm 2026-04-27; repository pushed 2026-09-04 | tool | Promise usage rules. Registered for one property — `prefer-await-to-then` — and the smallest source here; recorded rather than cited informally |

## Neutral — `llm-toolkit`

`https://github.com/EqualExperts/llm-toolkit`, pinned at **`a46825d`**
(2026-04-22, and still `main`'s head when checked). Cloned to `temp/`,
gitignored. **No `LICENCE` file** — see findings. All seven rows share that
answer and that maintenance signal, so neither is repeated per row.

| File | Covers | Numbered IDs |
| --- | --- | --- |
| `rules/clean-code.md` | Naming, function size, comments, duplication | Yes, file-local |
| `rules/solid-principles.md` | The five principles, with per-principle rules | Yes, file-local |
| `rules/testing-principles.md` | Test structure, doubles, what to assert | Yes, file-local |
| `rules/api-design.md` | Resource naming, status codes, versioning, errors | Yes, file-local |
| `rules/git-rules.md` | Commit and branch conventions | Yes, file-local |
| `rules/code-quality.md` | Mixed — the enforceable half only. The rest is assistant behaviour and is bucket 4 at S2 | Partly |
| `rules/platform/security.md` | Backend and API security — the common vulnerabilities rather than a compliance checklist. Language-neutral despite its `platform/` path, which is why it is registered here and not skipped as a stack file. 21 numbered rules, to be read **against** OWASP ASVS at S2 rather than alongside it | Yes, file-local |

`plan.md` records that `RULE-001` exists in ten different files. Re-verified for
this register on 2026-09-06 rather than repeated on trust — `grep -rl RULE-001
temp/llm-toolkit/rules` returns exactly ten paths. An upstream ID is therefore
file-local and cannot be our key: this register cites sources **against** an
identity and never uses one as an identity.

## Findings

**1. `llm-toolkit` has no licence, and that is now a narrower problem than it
looked.** Equal Experts owns the repository and this work is Equal Experts', so
the **ideas** are ours to use — settled 2026-09-05, which is what closed S1's
blocked box without anyone being contacted. The absent file still means there is
nothing to point at when **copying prose**, so citing rule IDs and writing our
own tool bindings remains the work, and the attribution posture is S4's.

**2. "Control plane" in that repository means something else entirely.**
`docs/control-planes/` describes a repository holding architecture, conventions
and context that an assistant loads — enforcement *by* context. This repository's
control is a register entry with a locus, a pinned tool and a verdict, and its
first rule is that enforcement is never Claude. The two words overlap and nothing
else does. Neither vocabulary may be borrowed into the other.

**3. Licence detection is not a licence answer.** Three of the fifteen rows were
wrong as GitHub reported them: `python/peps` as `NONE` (the PEPs place
themselves in the public domain), `google/styleguide` as `NOASSERTION` (CC BY
3.0), and `w3c/wcag` as `NOASSERTION` (W3C Document License). Each was corrected
by reading the file. A register built from the API alone would have recorded a
grant we hold as a grant we do not.

**4. Airbnb was considered and rejected on maintenance.** `eslint-config-airbnb`
was last published to npm on **2021-12-25** — it predates flat config and React
19. It remains the most cited opinionated config, and citing it would have been
citing something that has not moved in four years. `@antfu/eslint-config` is
registered in its place, on the strength of a release three days before this
survey.

**5. The accessibility slice rests on a quiet plugin and a stable standard.**
`eslint-plugin-jsx-a11y`'s last npm release is 2024-10-26. It is the enforceable
instrument for accessibility and it is barely moving, so WCAG 2.2 is registered
alongside it rather than behind it: if the plugin stops, the requirement does
not.

**6. Python's bucket 1 is large and already written.** ruff carries 969 rules
across 59 linters at the version this repository pins. Whatever S2 concludes,
the Python work is overwhelmingly **selection and pinning**, not rule-writing —
which is exactly the gap the register leaves open, since LNT-001 verifies that
ruff is wired and says nothing about which of those 969 are selected.

**7. Both stacks have first-party authority, and they are asymmetric.** Python's
is prose that predates the tooling (PEP 8, PEP 20) with the tooling built to
match; React's is documentation and a lint plugin published from the same
repository as the library, moving together. The two stacks will not be surveyed,
assessed or defaulted the same way, and pretending otherwise would be the first
mistake available here.

**8. React's enforceable half had a hole, and a wrapper was hiding it.** The
first pass of this register listed hooks, types and accessibility and nothing
that covers JSX itself — keys, index-as-key, dangerous props. It also registered
`@antfu/eslint-config` as the opinionated React source when that config delegates
React entirely to `@eslint-react/eslint-plugin` and `eslint-plugin-react-refresh`.
Registering a wrapper in place of what it wraps is the same failure this
repository names as a second copy, one level up. Both plugins are now registered
in their own right, and the succession between them — `eslint-plugin-react`
seventeen months without a release, `@eslint-react` published the day of the
survey — is itself a fact S2 needs.

**9. The authority column was wrong on its first pass, and the definition was
the reason.** It read *first-party tool: built by the people who build the thing
it checks*, and was then applied to ruff (Astral, not CPython), `typescript-eslint`
(not the TypeScript team) and Testing Library (not React's team) — none of which
satisfy it. The column now asks what a source has **standing to say**: a *stack*
source can say what good code is, a *tool* source can only say what that tool
will flag. Under the old wording the two are indistinguishable, which would have
let a tool's default set be read at S2 as though a language had blessed it.

**10. A principle was registered without its instrument.** This register listed
the Testing Library *guiding principles* and nothing that enforces them.
`eslint-plugin-testing-library` is the enforceable half, it lives under a
different package and a different organisation, and six React rows in
`assess.rules.md` cite it across eleven of its rules. This is finding 8 in a second shape: there, a wrapper
was registered in place of what it wrapped; here, a principle was registered in
place of what enforces it. Both are the same mistake — registering the thing that
is easiest to name rather than the thing that does the work. Added 2026-09-06.

**11. The stack-neutral half had no instruments at all.** Nothing in the first
pass could enforce a commit convention or an API shape, because the survey was
built by asking *which sources describe good code* and those two questions are
answered by tools rather than by prose. `commitlint`, `spectral` and
`eslint-plugin-promise` now carry rows, and so do Conventional Commits 1.0.0 and
the OpenAPI Specification — the standards they approximate — registered on the
same reasoning that put WCAG beside `jsx-a11y`. Added 2026-09-06. The general
lesson is in the section that names them: a survey built only from *what
describes* will always be one pass behind an assessment that asks *what
enforces*.

## What is not registered, and why

- `rules/platform/angular-ts.rules.md`, `bicep.rules.md`, `dotnet.rules.md` and
  `likec4.md` — out of scope per `plan.md`.
- `rules/platform/typescript.rules.md` — **deferred, with a condition.**
  `plan.md` has already judged it generic TypeScript that transfers, so the open
  question is not whether to read it but where it belongs: it is a stack source
  for React, not a neutral one. S2's React pass reads it, and a React pass that
  completes without it is a defect rather than a decision. `todo.md` carries the
  box that makes that fail loudly.
- No Equal Experts consumer of any of these rulesets is registered, because the
  question is **not answered**: finding out means a code search across the
  EqualExperts organisation, which is a scan of company repositories and has no
  authorisation behind it. That S1 box stays open with the reason attached.

## How to re-run this sweep

Every maintenance signal here rots, and a licence can change under a source
without anyone announcing it. These are the commands that produced the columns,
so a later reader diffs rather than re-researches.

```bash
# Licence, last push and archived state, per repository.
gh api repos/<owner>/<repo> \
  --jq '[(.license.spdx_id // "NONE"), .pushed_at, (.archived|tostring)] | @tsv'

# The licence file itself, wherever detection says NONE or NOASSERTION.
gh api repos/<owner>/<repo>/contents/LICENSE --jq '.content' | base64 -d | head -3

# Latest release, where the source releases.
gh api repos/<owner>/<repo>/releases/latest --jq '[.tag_name, .published_at] | @tsv'

# Latest npm publish, which is the honest signal for a plugin.
curl -s https://registry.npmjs.org/<package> | python3 -c \
  'import json,sys; d=json.load(sys.stdin); l=d["dist-tags"]["latest"]; print(l, d["time"][l])'

# Every cited URL still resolves.
curl -sL -o /dev/null -w '%{http_code}\n' --max-time 20 <url>
```

**When to re-run it.** Before S2 begins, so the assessment is not built on stale
rows; and again before any rule from a source is proposed default-on at S4,
because a default-on rule from an abandoned plugin is a commitment this
workstream would be making on a team's behalf. Neither is a control and nothing
enforces them — this section is the whole mechanism, which is why it names the
trigger rather than only the commands.

## Exit criterion

> Every source carries a licence answer and a maintenance signal, and each of the
> two stacks has at least one source of first-party authority.

**Met.** Twenty-four sources: seven Python, eleven React, five stack-neutral, and
`llm-toolkit` as one source across seven files. Every row carries both answers,
including the row whose licence answer is *none*. Stack authority exists for
both: PEP 8, PEP 20 and PEP 257 for Python; `react.dev` and
`eslint-plugin-react-hooks` for React. The criterion survives finding 9 — the
rows that were reclassified were tool rows either way, and no stack row moved —
and it survives findings 10 and 11, which added six sources rather than
invalidating any: the criterion was met by the eighteen and is met by the
twenty-four.

The criterion says nothing about the consumer question, and this document does
not tick it. A stage is finished when its criterion is met, not when its boxes
run out.
