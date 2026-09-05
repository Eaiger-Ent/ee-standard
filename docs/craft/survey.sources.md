# Craft — the source register

Stage **S1** of [`plan.md`](plan.md). One row per source, assessed **as a
source** before a single rule is read from it, so that a stale blog post and a
language's own documentation are never weighed the same.

Every column was established on **2026-09-05** by reading the thing itself —
`gh api` for repository metadata and licence files, the npm registry for publish
dates, `curl` for the cited URL, and the pinned clone for `llm-toolkit`. Where
GitHub's licence detection and the repository's own licence file disagree, the
file wins and the row says so.

**A blank licence is a finding, not an omission.** One source has no licence at
all; it is registered with that stated, because a source we may not copy from is
a different kind of source, not a missing one.

## How to read a row

| Column | What it holds |
| --- | --- |
| Source | What the thing is, not what we intend to do with it |
| Licence | The answer, and how it was established where detection was wrong or absent |
| Maintenance | The most recent *published* signal — a release where the source releases, a commit where it does not. A repository push is the weakest of these and is labelled as such |
| Authority | One of **first-party** (the thing defines its own rules), **first-party tool** (built by the people who build the thing it checks), **standards body**, **community**, **internal** |
| Covers | What it claims to cover — its claim, not our assessment of it. Assessment is S2 |

## Python

| Source | URL | Licence | Maintenance | Authority | Covers |
| --- | --- | --- | --- | --- | --- |
| ruff's rule taxonomy | <https://docs.astral.sh/ruff/rules/> | MIT | 0.16.6, released 2026-09-03 | first-party tool | 969 rules across 59 linters at the 0.16.5 this repository pins — pycodestyle, pyflakes, pylint, bugbear, pyupgrade, isort and more, under stable codes with fix availability declared per rule |
| PEP 8 — Style Guide for Python Code | <https://peps.python.org/pep-0008/> | **Public domain**, stated in the document's own Copyright section. GitHub reports `NONE` for `python/peps`, which is detection failing rather than an absent grant | Repository last pushed 2026-09-03; the PEP itself is stable by design | first-party | Layout, naming, comments, and the explicit instruction that a style rule may be broken when applying it hurts readability |
| PEP 20 — The Zen of Python | <https://peps.python.org/pep-0020/> | **Public domain**, stated in the document's own Copyright section | Stable; unchanged for years by design | first-party | Nineteen aphorisms. Judgment-only in every line — registered because it is the reference other sources appeal to, not because a machine can hold it |
| Google Python Style Guide | <https://google.github.io/styleguide/pyguide.html> | **CC BY 3.0**, read from `google/styleguide`'s `LICENSE`. GitHub reports `NOASSERTION` | Repository last pushed 2026-06-03 | community, widely adopted | An opinionated superset of PEP 8 — imports, exceptions, type annotations, docstrings, with a stated rationale per rule |
| pytest good practices | <https://docs.pytest.org/en/stable/explanation/goodpractices.html> | MIT | 9.1.1, released 2026-06-19 | first-party tool | Test layout, `conftest` scope, fixture use and import modes |
| OWASP ASVS | <https://owasp.org/www-project-application-security-verification-standard/> | CC BY-SA 4.0 | v5.0.0, released 2025-05-30; repository pushed 2026-09-03 | standards body | Application security verification requirements at three levels. **Share-alike**, which constrains reuse differently from every other row here |

## React

| Source | URL | Licence | Maintenance | Authority | Covers |
| --- | --- | --- | --- | --- | --- |
| Rules of React | <https://react.dev/reference/rules> | CC BY 4.0 (`reactjs/react.dev`) | Repository last pushed 2026-09-03 | first-party | Purity of components and hooks, the rules of hooks, and what React may assume — the constraints the compiler relies on |
| You Might Not Need an Effect | <https://react.dev/learn/you-might-not-need-an-effect> | CC BY 4.0 | Repository last pushed 2026-09-03 | first-party | The single richest source of React anti-patterns: derived state, effect chains, and event logic misplaced into effects |
| `eslint-plugin-react-hooks` | <https://github.com/facebook/react/tree/main/packages/eslint-plugin-react-hooks> | MIT | 7.1.1, published to npm 2026-04-17; React itself released 19.2.8 on 2026-07-21 | first-party tool | The enforceable half of the Rules of React, including the compiler-backed rules added in 6.x and 7.x |
| `typescript-eslint` | <https://typescript-eslint.io/users/configs> | MIT | v8.69.0, released 2026-08-31 | first-party tool | Typed lint rules; `recommended-type-checked` is the configuration this stage registers as a source, not as an adoption |
| `eslint-plugin-jsx-a11y` | <https://github.com/jsx-eslint/eslint-plugin-jsx-a11y> | MIT | v6.10.2, published to npm **2024-10-26**; repository last pushed 2026-01-06 | community | Static accessibility rules over JSX. The quietest source registered — see findings |
| WCAG 2.2 | <https://www.w3.org/TR/WCAG22/> | W3C Document License, read from `w3c/wcag`'s `LICENSE.md`. GitHub reports `NOASSERTION` | Repository last pushed 2026-09-04; the Recommendation itself is stable | standards body | The accessibility requirements the lint plugin above approximates, and the durable authority behind them |
| Testing Library guiding principles | <https://testing-library.com/docs/guiding-principles/> | MIT | `@testing-library/react` 16.3.3, published 2026-08-27; `dom-testing-library` v10.4.1, 2025-07-27 | first-party tool | What to query, what not to assert, and the principle the query priority encodes |
| `@antfu/eslint-config` | <https://github.com/antfu/eslint-config> | MIT | v9.5.1, released 2026-09-02 | community, opinionated | One opinionated flat config, **read as a source and not adopted** — registered to see which rules an opinionated author turns on, and why |

## Neutral — `llm-toolkit`

`https://github.com/EqualExperts/llm-toolkit`, pinned at **`a46825d`**
(2026-04-22, and still `main`'s head when checked). Cloned to `temp/`,
gitignored. **No `LICENCE` file** — see findings. All six rows share that
answer and that maintenance signal, so neither is repeated per row.

| File | Covers | Numbered IDs |
| --- | --- | --- |
| `rules/clean-code.md` | Naming, function size, comments, duplication | Yes, file-local |
| `rules/solid-principles.md` | The five principles, with per-principle rules | Yes, file-local |
| `rules/testing-principles.md` | Test structure, doubles, what to assert | Yes, file-local |
| `rules/api-design.md` | Resource naming, status codes, versioning, errors | Yes, file-local |
| `rules/git-rules.md` | Commit and branch conventions | Yes, file-local |
| `rules/code-quality.md` | Mixed — the enforceable half only. The rest is assistant behaviour and is bucket 4 at S2 | Partly |

`RULE-001` exists in ten of that repository's files, so an upstream ID is
file-local and cannot be our key. This register cites sources **against** an
identity; it never uses one as an identity.

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

## What is not registered, and why

- `rules/platform/angular-ts.rules.md`, `bicep.rules.md`, `dotnet.rules.md` and
  `likec4.md` — out of scope per `plan.md`. `typescript.rules.md` is generic TS
  and transfers, but it is a **stack** source rather than a neutral one; it is
  registered at S2 against the React stack if its rules survive a read.
- `rules/platform/security.md` — not one of the six neutral files this stage
  named, and the security slice already has ASVS. A candidate for S2, recorded
  here so that skipping it is visible rather than silent.
- No Equal Experts consumer of any of these rulesets is registered, because the
  question is **not answered**: finding out means a code search across the
  EqualExperts organisation, which is a scan of company repositories and has no
  authorisation behind it. That S1 box stays open with the reason attached.

## Exit criterion

> Every source carries a licence answer and a maintenance signal, and each of the
> two stacks has at least one source of first-party authority.

**Met.** Fifteen sources: six Python, eight React, and `llm-toolkit` as one
source across six files. Every row carries both answers, including the row whose
licence answer is *none*. Python's first-party authority is PEP 8 and PEP 20;
React's is `react.dev` and `eslint-plugin-react-hooks`.

The criterion says nothing about the consumer question, and this document does
not tick it. A stage is finished when its criterion is met, not when its boxes
run out.
