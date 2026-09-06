# Craft — the property register

Stage **S2** of [`plan.md`](plan.md). One register, property-keyed, covering both
stacks: what each property asserts, which sources assert it, whether they agree,
which enforceability bucket it falls in, the exact tool and rule ID where one
exists, and a proposed default.

It is one register presented in four sections — Python, React, stack-neutral, and
the bucket-4 residue — because a single 150-row markdown table is unreadable and
a reader looking for a Python property should not scroll past React's. The
columns are identical throughout; the sections are a rendering, not four
registers.

The buckets are defined in [`plan.md`](plan.md) § S2 and are not restated here.
What *is* here is how the boundary between them was applied, because that is
where the judgment lives: see [How a bucket was
decided](#how-a-bucket-was-decided).

Taken **2026-09-06**, against the sweep re-run recorded below.

## The sweep, re-run

`survey.sources.md` § How to re-run this sweep names the trigger — *before S2
begins* — and this is that run. Every command in that section was re-executed on
2026-09-06.

**One row moved.** `@eslint-react/eslint-plugin` published **5.18.9** on
2026-09-06, one patch on from the 5.18.8 the survey recorded the day before.
Nothing else changed: no licence answer differs, no repository is archived, every
cited URL resolves, and `llm-toolkit`'s `main` is still `a46825d`. The survey's
rows stand as taken.

**Six sources were missing, and this stage's own pass is what found them.**
`survey.sources.md` registers the Testing Library *guiding principles* — the
prose — and nothing that enforces them; the enforceable instrument is
`eslint-plugin-testing-library`, a separate package under a different
organisation, and it is what every testing row in the React section below cites.
Registering a principle without its instrument is the mirror of finding 8, where
a wrapper was registered in place of the plugin it wrapped. The stack-neutral
half was worse: it had no instruments at all, because the survey was built by
asking which sources *describe* good code and a commit convention is described by
a tool. `commitlint`, `spectral`, `eslint-plugin-promise` and the two standards
the first two approximate — Conventional Commits and the OpenAPI Specification —
are now registered too. All six rows are in `survey.sources.md`, marked as S2
additions, with the reasoning as its findings 10 and 11.

**One row was wrong rather than missing.** The survey recorded ruff as "969 rules
across 59 linters". Read as JSON, the taxonomy is 969 rules of which 812 are
stable, 140 preview and 17 removed, across 58 stable linters — the 59th was a
rule with neither a code nor a linter, `pytest-fixture-autouse`, which is preview
and unaddressable. Corrected in place.

## How to read a row

| Column | What it holds |
| --- | --- |
| Identity | The property, lowercase and dotted, per `plan.md`'s naming standard. Never an upstream ID |
| Asserts | The property itself, in one line — what would be true of code that holds it |
| Sources | Which registered sources assert it, by the short keys below |
| Agree | `—` where one source asserts it; `agree` where several say the same thing; **`contested`** where they do not, or where a source and its own tooling do not |
| B | The bucket: 1 already a lint rule, 2 a check could hold it, 3 judgment only, 4 assistant behaviour |
| Instrument | The exact tool and rule ID, where one exists. `preview` marks a ruff rule not in the stable set; `off` marks a rule its own plugin ships disabled |
| Default | The proposed default for bucket 1 and 2 rows: `on`, `off`, or `n/a` where nothing can be switched. **A proposal, not a decision** — S3 measures it and may demote it |

### Source keys

| Key | Source | Key | Source |
| --- | --- | --- | --- |
| `ruff` | ruff's rule taxonomy | `ror` | Rules of React |
| `pep8` | PEP 8 | `ymnnae` | You Might Not Need an Effect |
| `pep20` | PEP 20 | `hooks` | `eslint-plugin-react-hooks` |
| `pep257` | PEP 257 | `tse` | `typescript-eslint` |
| `google` | Google Python Style Guide | `a11y` | `eslint-plugin-jsx-a11y` |
| `pytest` | pytest good practices | `wcag` | WCAG 2.2 |
| `asvs` | OWASP ASVS | `tl` | Testing Library principles |
| | | `tl+` | `eslint-plugin-testing-library` |
| | | `rp` | `eslint-plugin-react` |
| | | `xr` | `@eslint-react/eslint-plugin` |
| | | `antfu` | `@antfu/eslint-config` |

`llm-toolkit` files are cited by filename: `clean-code`, `solid`, `testing`,
`api`, `git`, `code-quality`, `security`, `typescript`. Rule numbers are quoted
where they narrow the citation — `clean-code 002` — and, per the naming standard,
they are cited **against** an identity and never used as one.

## How a bucket was decided

The four buckets are `plan.md`'s. Three boundary calls were made repeatedly
enough to be worth stating, because they are where this register could most
easily have flattered itself.

**Bucket 1 means a rule that exists and is reachable, not one that exists.** A
ruff rule in `preview` is not reachable without `preview = true`, which turns on
140 rules at once and cannot be enabled for one of them. Preview rules are
recorded as bucket 1 with the `preview` marker and a default of `off`, and the
count below states how many bucket-1 rows depend on preview so the share can be
read without them.

**A rule that only approximates the property is bucket 2, not bucket 1.** The
temptation throughout was to accept a nearby rule as the property. `clean-code
002` says functions should be under twenty *lines*; ruff's `PLR0915` counts
*statements* and `C901` counts cyclomatic complexity. Neither is the assertion.
Where the nearby rule is genuinely a proxy the row says so and stays in bucket 2
with the rule cited; where it is the assertion, bucket 1.

**Coverage by a control is recorded, not re-derived.** Several stack-neutral
properties are already enforced in this organisation's register — secrets in
version control, direct pushes to the default branch. Those rows carry the
control ID and are excluded from the bucket shares, because counting them would
be Craft claiming credit for gates the register already runs. The boundary
itself — whether a craft rule may ever *become* a control — is S4's ADR and is
not settled here.

## Python

Seventy-one properties. Ruff is the bulk instrument, and the section is ordered by
what the property is about rather than by rule family, because a family is the
tool's organising idea and not the code's.

### Correctness and safety

| Identity | Asserts | Sources | Agree | B | Instrument | Default |
| --- | --- | --- | --- | --- | --- | --- |
| `python.no-mutable-default-argument` | A default argument is never a mutable literal | `ruff` | — | 1 | ruff `B006`, `RUF012` | on |
| `python.no-call-in-default-argument` | A default argument is not the result of a call evaluated once at definition | `ruff` | — | 1 | ruff `B008` | on |
| `python.no-loop-variable-capture` | A closure defined in a loop does not silently bind the loop variable | `ruff` | — | 1 | ruff `B023` | on |
| `python.no-unused-import` | Every import is used | `ruff`, `pep8` | agree | 1 | ruff `F401` | on |
| `python.no-unused-variable` | Every local binding is read | `ruff` | — | 1 | ruff `F841` | on |
| `python.no-unused-argument` | A parameter that is never read is removed or marked | `ruff` | — | 1 | ruff `ARG001`–`ARG005` | on |
| `python.no-global-mutable-state` | Module state is not rebound through `global` | `ruff`, `solid 102` | agree | 1 | ruff `PLW0603` | on |
| `python.no-private-member-access` | A module does not reach into another object's private members | `ruff`, `solid 004` | agree | 1 | ruff `SLF001` | on |
| `python.no-import-inside-function` | Imports are at module top level | `ruff`, `pep8` | agree | 1 | ruff `PLC0415` | off |
| `python.timezone-aware-datetimes` | Every datetime carries a timezone | `ruff` | — | 1 | ruff `DTZ001`–`DTZ012` | on |
| `python.no-shadowed-loop-variable` | An inner binding does not overwrite the loop variable | `ruff` | — | 1 | ruff `PLW2901` | on |

### Errors and exceptions

| Identity | Asserts | Sources | Agree | B | Instrument | Default |
| --- | --- | --- | --- | --- | --- | --- |
| `python.no-blind-except` | `except` names the exceptions it handles, except in a deliberate catch-all | `ruff`, `code-quality` | agree | 1 | ruff `BLE001`, `E722` | on |
| `python.exception-chaining` | An exception raised inside `except` chains from the original | `ruff`, `code-quality` | agree | 1 | ruff `B904` | on |
| `python.no-silent-exception-swallow` | An exception is never discarded without a decision | `ruff`, `code-quality` | **contested** | 1 | ruff `S110`, `S112` — but ruff `SIM105` *recommends* `contextlib.suppress`, which is a swallow | on |
| `python.no-log-and-reraise` | An error is logged **or** re-raised, not both | `code-quality` | — | 2 | Nothing asserts it. ruff `TRY400`/`TRY401` are adjacent and cover a different mistake | on |
| `python.exception-carries-context` | An error type or message adds information the caller did not have | `code-quality`, `clean-code 202` | agree | 3 | — | n/a |
| `python.exception-message-not-inline` | An exception message is not a long literal at the raise site | `ruff` | **contested** | 1 | ruff `EM101`, `EM102`, `TRY003` — which pull against `clean-code 202`'s *descriptive error messages* | off |

### Structure and size

| Identity | Asserts | Sources | Agree | B | Instrument | Default |
| --- | --- | --- | --- | --- | --- | --- |
| `python.function-length` | A function is short enough to read at once | `clean-code 002`, `google` | **contested** | 2 | `clean-code` says under 20 **lines**; ruff `PLR0915` counts statements and `C901` counts complexity. Both are proxies | on (as proxies) |
| `python.function-parameter-count` | A function takes few parameters | `clean-code 101`, `ruff` | **contested** | 1 | ruff `PLR0913`, `PLR0917` — but `clean-code` says 3 and ruff defaults to 5 | on |
| `python.nesting-depth` | Control flow does not nest deeply | `clean-code 102` | — | 1 | ruff `PLR1702` — **preview** | off |
| `python.class-size` | A class stays small and focused | `clean-code 105`, `solid 001` | agree | 1 | ruff `PLR0904` — **preview**; counts public methods, which is a proxy for focus | off |
| `python.class-dependency-count` | A class depends on few collaborators | `solid 101` | — | 2 | Nothing asserts it. Countable from `__init__` parameters, which is `PLR0913` at a different site | off |
| `python.shallow-inheritance` | Inheritance hierarchies stay shallow | `solid 105` | — | 2 | Nothing asserts it. Depth is mechanically countable | off |
| `python.return-count` | A function has few exit points | `ruff` | **contested** | 1 | ruff `PLR0911` — which pulls against `clean-code 102`'s *use early returns* | off |
| `python.no-redundant-assign-before-return` | A value is returned rather than parked in a name first | `ruff` | — | 1 | ruff `RET504` | off |
| `python.abstraction-ordering` | Functions read high-level first, details after | `clean-code 203` | — | 3 | — | n/a |
| `python.single-responsibility` | A unit has one reason to change | `solid 001`, `clean-code 105`, `pep20` | agree | 3 | — | n/a |
| `python.depend-on-abstractions` | Cross-module dependencies are on abstractions | `solid 002` | — | 3 | — | n/a |
| `python.dependency-injection` | Dependencies are provided, not constructed in place | `solid 102` | — | 3 | — | n/a |
| `python.composition-over-inheritance` | Behaviour is extended by composition unless the relation is genuinely *is-a* | `solid 104`, `solid 201`, `clean-code 201` | agree | 3 | — | n/a |
| `python.no-duplication` | The same logic is not written twice | `clean-code 003`, `pep20` | agree | 2 | Nothing in ruff. A clone detector could hold it, at the cost of a second tool and a threshold nobody agrees on | off |

### Naming, style and layout

| Identity | Asserts | Sources | Agree | B | Instrument | Default |
| --- | --- | --- | --- | --- | --- | --- |
| `python.naming-form` | Names follow the language's casing conventions | `pep8`, `google`, `ruff` | agree | 1 | ruff `N801`–`N818` (pep8-naming) | on |
| `python.naming-intent` | A name says what the thing is for | `clean-code 001`, `clean-code 104`, `clean-code 205`, `pep20` | agree | 3 | — . ruff `E741` catches three ambiguous single letters and nothing else | n/a |
| `python.line-length` | Lines are short enough to read side by side | `pep8`, `google`, `ruff` | **contested** | 1 | ruff `E501` — `pep8` says 79, `google` says 80, ruff defaults to 88, this repository uses 100 | on |
| `python.import-order` | Imports are grouped and ordered | `pep8`, `google`, `ruff` | agree | 1 | ruff `I001` (isort) | on |
| `python.no-relative-parent-imports` | A module does not import from its parent by relative path | `google` | — | 1 | ruff `TID252` | on |
| `python.consistent-formatting` | Formatting is not a per-author choice | `clean-code 005`, `pep8` | agree | 1 | `ruff format`. A formatter, not a lint rule — cited because the property is met by running it | on |
| `python.no-trailing-whitespace` | No trailing or stray whitespace | `pep8` | — | 1 | ruff `W291`, `W293` | on |
| `python.pep604-unions` | Unions and optionals use PEP 604 syntax rather than `typing.Union` | `ruff` | — | 1 | ruff `UP007`, `UP045` | on |
| `python.pathlib-over-os-path` | Filesystem paths go through `pathlib` | `ruff` | — | 1 | ruff `PTH100`–`PTH210` | on |
| `python.comprehension-over-manual-loop` | A transformation is a comprehension, not an append loop | `ruff` | — | 1 | ruff `PERF401`, `C400`–`C420` | on |
| `python.no-boolean-trap` | A boolean is not passed positionally into a call whose meaning it flips | `ruff` | — | 1 | ruff `FBT001`, `FBT002` | on |

### Documentation and comments

| Identity | Asserts | Sources | Agree | B | Instrument | Default |
| --- | --- | --- | --- | --- | --- | --- |
| `python.docstring-presence` | Public modules, classes and functions carry a docstring | `pep257`, `google` | agree | 1 | ruff `D100`–`D107` | off |
| `python.docstring-form` | A docstring has a one-line summary in the imperative | `pep257` | — | 1 | ruff `D205`, `D401`, `D2xx`, `D4xx` | off |
| `python.no-commented-out-code` | Dead code is deleted, not commented | `clean-code 004` | — | 1 | ruff `ERA001` | on |
| `python.self-documenting-code` | Code needs few comments because it reads clearly | `clean-code 103`, `code-quality` | agree | 3 | — | n/a |
| `python.no-untracked-todo` | A `TODO` names an owner or an issue | `git 004` | — | 1 | ruff `TD001`–`TD007`, `FIX001`–`FIX004` | off |
| `python.no-unused-suppression` | A `noqa` that suppresses nothing is removed | `ruff` | — | 1 | ruff `RUF100` | on |

### Typing

| Identity | Asserts | Sources | Agree | B | Instrument | Default |
| --- | --- | --- | --- | --- | --- | --- |
| `python.annotate-public-api` | Public functions annotate parameters and returns | `google`, `typescript 003` (by analogy) | agree | 1 | ruff `ANN001`, `ANN201`, `ANN2xx`; mypy `disallow_untyped_defs` | on |
| `python.no-any` | `Any` is not the answer to an unknown type | `typescript 002` (by analogy) | **contested** | 1 | ruff `ANN401` covers annotations only; mypy `strict` does **not** ban `Any`. `disallow_any_explicit` does, and is not in `strict` | off |
| `python.typing-only-imports` | Imports needed only for types are in a type-checking block | `ruff` | — | 1 | ruff `TC001`–`TC003` | off |

### Testing

| Identity | Asserts | Sources | Agree | B | Instrument | Default |
| --- | --- | --- | --- | --- | --- | --- |
| `python.test-layout` | Tests live where the runner and the packaging both expect | `pytest` | — | 1 | ruff `INP001`; `pytest` importmode configuration | on |
| `python.test-naming` | A test name states the scenario and the expected outcome | `testing 003` | — | 3 | — . `pytest`'s `test_` prefix is collection, not naming quality | n/a |
| `python.test-single-behaviour` | A test asserts one behaviour | `testing 001` | — | 2 | ruff `PT018` splits composite assertions, which is a proxy and not the property | on (as proxy) |
| `python.test-independence` | Tests do not depend on order or shared mutable state | `testing 002` | — | 2 | Nothing asserts it. A randomised-order run detects violations empirically | on |
| `python.test-arrange-act-assert` | A test's setup, action and assertion are visually distinct | `testing 004` | — | 3 | — | n/a |
| `python.no-flaky-tests` | A test that does not pass consistently is fixed or deleted | `testing 005` | — | 2 | Nothing asserts it. Repeated runs detect it; nothing prevents it | on |
| `python.narrow-raises` | `pytest.raises` names the exception and matches the message | `pytest`, `testing 001` | agree | 1 | ruff `PT011`, `PT012` | on |
| `python.parametrize-form` | Parametrised cases are declared in the conventional shape | `pytest` | — | 1 | ruff `PT006`, `PT007` | on |
| `python.minimal-test-setup` | Fixtures and setup stay small | `testing 103`, `pytest` | agree | 3 | — | n/a |
| `python.no-mocking-domain-logic` | Test doubles stand in for external dependencies, not for the code under test | `testing 102` | — | 3 | — | n/a |
| `python.test-code-quality` | Test code is held to the same standard as production code | `testing 105`, `clean-code` | agree | 2 | Configuration, not a rule: whether the lint profile applies to `tests/` at all | on |

### Security

Every row here overlaps `asvs`, which asserts the same properties at a different
altitude. The overlap is the point of the `security` file being read *against*
ASVS rather than alongside it, and where they differ ASVS is the standing
authority.

| Identity | Asserts | Sources | Agree | B | Instrument | Default |
| --- | --- | --- | --- | --- | --- | --- |
| `python.parameterised-sql` | User input never reaches SQL by concatenation | `security 103`, `asvs`, `ruff` | agree | 1 | ruff `S608` | on |
| `python.no-hardcoded-credentials` | No password, token or key is a literal in source | `security 001`, `asvs`, `ruff` | agree | 1 | ruff `S105`–`S107`. Overlaps SEC-001, which scans the repository for the same class at a different locus | on |
| `python.no-insecure-hash` | Passwords are not hashed with MD5 or SHA-1 | `security 104`, `asvs` | agree | 1 | ruff `S324` | on |
| `python.tls-verification-on` | Certificate verification is never disabled | `security 002`, `asvs` | agree | 1 | ruff `S501` | on |
| `python.crypto-grade-randomness` | Secrets are not drawn from the standard PRNG | `asvs`, `ruff` | agree | 1 | ruff `S311` | on |
| `python.no-bind-all-interfaces` | A service does not bind `0.0.0.0` by default | `asvs`, `ruff` | agree | 1 | ruff `S104` | off |
| `python.no-assert-for-enforcement` | Runtime enforcement does not rely on `assert` | `asvs`, `ruff` | **contested** | 1 | ruff `S101` — which fires on every test, so the property is only reachable with a per-path exclusion | on (excluding `tests/`) |
| `python.structured-logging` | Logs are key-value, not prose | `code-quality` | — | 1 | ruff `G001`–`G004`, `LOG015` — these constrain the *call*, not the format. The format is bucket 2 | on |
| `python.no-sensitive-data-in-logs` | Secrets and PII never reach a log | `security 006`, `asvs` | agree | 2 | Nothing asserts it. A denylist over log call arguments could | off |

## React

Sixty-eight properties. Unlike Python, the enforceable half is spread over six
plugins that overlap each other, and the overlap is itself the finding — see
[Findings](#findings).

### The Rules of React

The nine rules the library's own documentation states, and what enforces each.

| Identity | Asserts | Sources | Agree | B | Instrument | Default |
| --- | --- | --- | --- | --- | --- | --- |
| `react.hooks-at-top-level` | Hooks are not called in loops, conditions or nested functions | `ror`, `hooks`, `xr` | agree | 1 | `react-hooks/rules-of-hooks`; `@eslint-react/rules-of-hooks` | on |
| `react.hooks-only-from-react-functions` | Hooks are called only from components and other hooks | `ror`, `hooks`, `xr` | agree | 1 | `react-hooks/rules-of-hooks` | on |
| `react.components-are-idempotent` | The same props, state and context produce the same output | `ror`, `hooks` | agree | 1 | `react-hooks/purity` | on |
| `react.no-side-effects-in-render` | Side effects run outside render | `ror`, `hooks` | agree | 1 | `react-hooks/purity`, `react-hooks/globals` | on |
| `react.props-and-state-immutable` | Props and state are not mutated | `ror`, `hooks`, `rp`, `xr` | agree | 1 | `react-hooks/immutability`; `react/no-direct-mutation-state` | on |
| `react.hook-values-immutable` | Values passed to or returned from a hook are not then mutated | `ror`, `hooks` | agree | 1 | `react-hooks/immutability` | on |
| `react.jsx-values-immutable` | A value is not mutated after being passed to JSX | `ror`, `hooks` | agree | 1 | `react-hooks/immutability` | on |
| `react.no-direct-component-calls` | A component is used in JSX, never called as a function | `ror` | — | 2 | Nothing names it directly. `react-hooks/rules-of-hooks` catches the hook consequence, not the call | on |
| `react.no-hooks-as-values` | A hook is not passed around as a value | `ror` | — | 2 | Nothing asserts it | on |
| `react.no-set-state-in-render` | State is not set during render | `ror`, `hooks`, `xr` | agree | 1 | `react-hooks/set-state-in-render` | on |
| `react.refs-not-read-in-render` | A ref is not read or written during render | `ror`, `hooks` | agree | 1 | `react-hooks/refs` | on |

### Effects

The stage's sharpest finding lives in this table: the anti-pattern React's own
documentation devotes a whole page to has a lint rule, and the rule ships
**off**.

| Identity | Asserts | Sources | Agree | B | Instrument | Default |
| --- | --- | --- | --- | --- | --- | --- |
| `react.no-derived-state-in-effect` | State that can be computed during render is not synchronised in an effect | `ymnnae`, `hooks` | agree | 1 | `react-hooks/no-deriving-state-in-effects` — **shipped `off`** in every preset | on |
| `react.no-set-state-in-effect` | An effect does not set state that triggers another render pass | `ymnnae`, `hooks`, `xr` | agree | 1 | `react-hooks/set-state-in-effect` | on |
| `react.effect-dependencies-complete` | An effect declares every reactive value it reads | `hooks` | — | 1 | `react-hooks/exhaustive-deps` — recommended at `warn`, not `error` | on (`error`) |
| `react.effect-dependencies-exhaustive` | The stricter, compiler-backed dependency analysis | `hooks` | — | 1 | `react-hooks/exhaustive-effect-dependencies` — **shipped `off`**, and undocumented on `react.dev` | off |
| `react.no-effect-chains` | One effect does not exist to react to another effect's state write | `ymnnae` | — | 3 | — . The consequence is caught by `set-state-in-effect`; the shape is not | n/a |
| `react.no-event-logic-in-effect` | Logic belonging to an event handler is not moved into an effect | `ymnnae` | — | 3 | — | n/a |
| `react.no-fetch-in-effect` | Data fetching goes through a framework or a library, not a bare effect | `ymnnae` | — | 3 | — . `ymnnae` itself stops short of a rule here and recommends a mechanism | n/a |
| `react.state-reset-by-key` | State is reset by remounting on a `key`, not by an effect watching a prop | `ymnnae` | — | 3 | — | n/a |
| `react.external-store-subscription` | An external store is read through `useSyncExternalStore` | `ymnnae` | — | 2 | Nothing asserts it. A check could find `useEffect` + `subscribe` | off |
| `react.no-leaked-subscriptions` | Timers, listeners and observers are cleaned up | `xr` | — | 1 | `@eslint-react/web-api-no-leaked-*` — six rules; **no equivalent in `hooks`** | on |
| `react.memoization-preserved` | A manual `useMemo`/`useCallback` is not silently invalidated | `hooks` | — | 1 | `react-hooks/preserve-manual-memoization`, `react-hooks/use-memo` | on |

### JSX correctness

| Identity | Asserts | Sources | Agree | B | Instrument | Default |
| --- | --- | --- | --- | --- | --- | --- |
| `react.list-keys` | Every element in a list carries a stable key | `rp`, `xr` | agree | 1 | `react/jsx-key`; `@eslint-react/no-missing-key`, `no-duplicate-key`, `jsx-no-key-after-spread` | on |
| `react.no-array-index-key` | A list key is not the array index | `xr` | — | 1 | `@eslint-react/no-array-index-key`. `react/no-array-index-key` exists but is **not** in that plugin's `recommended` | on |
| `react.no-duplicate-props` | A JSX element does not set the same prop twice | `rp` | — | 1 | `react/jsx-no-duplicate-props` | on |
| `react.no-dangerous-html` | `dangerouslySetInnerHTML` is not used | `xr`, `rp`, `asvs`, `security 005` | agree | 1 | `@eslint-react/dom-no-dangerously-set-innerhtml`; `react/no-danger` (not in `recommended`) | on |
| `react.safe-external-links` | `target="_blank"` carries `rel="noreferrer"` | `rp`, `xr`, `asvs` | agree | 1 | `react/jsx-no-target-blank`; `@eslint-react/dom-no-unsafe-target-blank` (**strict only**) | on |
| `react.no-unknown-dom-property` | A DOM element is not given a property React will drop | `rp`, `xr` | agree | 1 | `react/no-unknown-property`; `@eslint-react/dom-no-unknown-property` | on |
| `react.no-comment-textnodes` | A `//` comment is not rendered as text | `rp`, `xr` | agree | 1 | `react/jsx-no-comment-textnodes` | on |
| `react.no-leaked-conditional-render` | `&&` on a non-boolean does not render `0` or an empty string | `xr` | — | 1 | `@eslint-react/no-leaked-conditional-rendering` — **`off` in `recommended`**, on in `recommended-type-checked` | on |
| `react.no-nested-component-definitions` | A component is not defined inside another component's body | `hooks`, `xr` | agree | 1 | `react-hooks/static-components`; `@eslint-react/no-nested-component-definitions` | on |
| `react.context-value-stability` | A context value is not a fresh object on every render | `xr` | — | 1 | `@eslint-react/no-unstable-context-value` — **strict only** | on |
| `react.no-deprecated-api` | Deprecated lifecycle and API surface is not used | `rp`, `xr` | agree | 1 | `react/no-deprecated`; `@eslint-react/no-component-will-*`, `no-create-ref`, `no-forward-ref`, `no-use-context` | on |
| `react.no-class-components` | New components are functions | `xr` | **contested** | 1 | `@eslint-react/no-class-component` — **strict only**, and the property is a migration position rather than a correctness one | off |
| `react.no-legacy-proptypes` | Prop types are types, not runtime `propTypes` | `rp` | **contested** | 1 | `react/prop-types` is **in** `eslint-plugin-react`'s `recommended` and asserts the opposite for a TypeScript codebase | off |
| `react.jsx-runtime-assumed` | `React` need not be in scope for JSX | `rp` | **contested** | 1 | `react/react-in-jsx-scope` is **in** `recommended` and is wrong for React 17 and later; the `jsx-runtime` config turns it off | off (via `jsx-runtime`) |

### TypeScript

`rules/platform/typescript.rules.md` is read here rather than as a neutral file,
per `survey.sources.md` § What is not registered — it is a stack source for
React. All thirteen of its rules appear below.

| Identity | Asserts | Sources | Agree | B | Instrument | Default |
| --- | --- | --- | --- | --- | --- | --- |
| `react.strict-type-checking` | `tsconfig` enables the strict family | `typescript 001`, `tse` | agree | 2 | `tsc` itself, read from `tsconfig.json`. No lint rule asserts a compiler flag | on |
| `react.no-explicit-any` | `unknown` or a real type, never `any` | `typescript 002`, `tse` | agree | 1 | `@typescript-eslint/no-explicit-any` (in `recommended`) | on |
| `react.no-unsafe-any-flow` | A value typed `any` does not flow into a call, member access or return | `typescript 002`, `tse` | agree | 1 | `@typescript-eslint/no-unsafe-{argument,assignment,call,member-access,return}` — **type-checked only** | on |
| `react.explicit-return-types` | Public functions and methods declare their return type | `typescript 003` | **contested** | 1 | `@typescript-eslint/explicit-module-boundary-types` — exists, and is **not** in any recommended preset | off |
| `react.no-non-null-assertion` | `!` is not used to silence the null check | `typescript 004`, `tse` | agree | 1 | `@typescript-eslint/no-non-null-assertion` — in `strict`, not `recommended` | on |
| `react.no-floating-promises` | Every promise is awaited, returned or explicitly ignored | `tse` | — | 1 | `@typescript-eslint/no-floating-promises` — type-checked | on |
| `react.no-misused-promises` | An async function is not passed where a void callback is expected | `tse` | — | 1 | `@typescript-eslint/no-misused-promises` — type-checked | on |
| `react.throw-error-objects` | Only `Error` subclasses are thrown | `typescript 103`, `tse` | agree | 1 | `@typescript-eslint/only-throw-error` — type-checked | on |
| `react.domain-error-types` | Domain failures have their own error types | `typescript 103`, `code-quality` | agree | 3 | — | n/a |
| `react.interface-over-type` | Object shapes are declared as interfaces | `typescript 101` | **contested** | 1 | `@typescript-eslint/consistent-type-definitions` — a style choice with no correctness argument, and `antfu` takes the opposite default | off |
| `react.naming-form` | PascalCase for types and components, camelCase for values | `typescript 102`, `typescript 201`, `typescript 202` | agree | 1 | `@typescript-eslint/naming-convention` — not in any recommended preset, and requires a written selector list | off |
| `react.readonly-immutability` | Properties and arrays that should not change are `readonly` | `typescript 104` | — | 3 | — . No recommended rule; `prefer-readonly` covers private class fields only | n/a |
| `react.discriminated-unions` | State and API responses are modelled as discriminated unions | `typescript 105` | — | 3 | — | n/a |
| `react.barrel-exports` | Modules are re-exported through an `index.ts` | `typescript 203` | **contested** | 3 | — . Widely argued against on bundle and circular-import grounds; registered because the source asserts it, not because this stage endorses it | n/a |
| `react.async-await-over-chains` | `async`/`await` rather than `.then()` chains | `typescript 204` | — | 2 | Nothing in the registered plugins. `eslint-plugin-promise` has `prefer-await-to-then`, which is a source this survey has not registered | off |

### Accessibility

Eleven properties. WCAG is cited as the requirement; the plugin is cited as the
approximation, and the two are not the same thing — `jsx-a11y`'s `recommended`
config has thirty-four entries of which thirty-one are on, and it can see
markup but not a rendered page.

Five of the thirty-one are on by default and not separately keyed below —
`autocomplete-valid`, `heading-has-content`, `no-access-key`,
`no-noninteractive-element-interactions` and `scope`. Each is a lone rule with no
second rule and no other source to share a property with, and inventing one
identity per rule would be keying on the tool rather than on the property.
They are enabled by every row below that turns the config on; they are named here
so the omission is deliberate rather than invisible.

| Identity | Asserts | Sources | Agree | B | Instrument | Default |
| --- | --- | --- | --- | --- | --- | --- |
| `react.a11y-text-alternatives` | Every non-text element has a text alternative | `wcag` 1.1.1, `a11y` | agree | 1 | `jsx-a11y/alt-text`, `img-redundant-alt`, `iframe-has-title` | on |
| `react.a11y-form-labels` | Every control has a programmatically associated label | `wcag` 3.3.2, `a11y` | agree | 1 | `jsx-a11y/label-has-associated-control`, `control-has-associated-label` (**`off` in `recommended`**) | on |
| `react.a11y-aria-validity` | ARIA attributes and roles are real and correctly applied | `wcag` 4.1.2, `a11y` | agree | 1 | `jsx-a11y/aria-props`, `aria-proptypes`, `aria-role`, `role-has-required-aria-props`, `role-supports-aria-props`, `aria-unsupported-elements` | on |
| `react.a11y-keyboard-parity` | Anything usable with a mouse is usable with a keyboard | `wcag` 2.1.1, `a11y` | agree | 1 | `jsx-a11y/click-events-have-key-events`, `mouse-events-have-key-events`, `interactive-supports-focus`, `no-static-element-interactions` | on |
| `react.a11y-focus-order` | Focus order follows meaning; no positive `tabindex` | `wcag` 2.4.3, `a11y` | agree | 1 | `jsx-a11y/tabindex-no-positive`, `no-noninteractive-tabindex`, `aria-activedescendant-has-tabindex` | on |
| `react.a11y-document-language` | The document declares its language | `wcag` 3.1.1, `a11y` | agree | 1 | `jsx-a11y/html-has-lang`; `lang` extends it to any element and is **not in `recommended`** | on |
| `react.a11y-media-captions` | Time-based media carries captions | `wcag` 1.2.2, `a11y` | agree | 1 | `jsx-a11y/media-has-caption` | on |
| `react.a11y-link-purpose` | A link's purpose is clear from its text | `wcag` 2.4.4, `a11y` | **contested** | 1 | `jsx-a11y/anchor-has-content`, `anchor-is-valid`; `anchor-ambiguous-text` is **`off` in `recommended`** and is the one that actually asserts the property | on |
| `react.a11y-semantic-elements` | A native element is used before a role is added to a `div` | `wcag` 4.1.2, `a11y` | agree | 1 | `jsx-a11y/no-redundant-roles`, `no-interactive-element-to-noninteractive-role`, `no-noninteractive-element-to-interactive-role`; `prefer-tag-over-role` asserts the property most directly and is **not in `recommended`** | on |
| `react.a11y-no-unexpected-focus` | Focus is not seized on load | `wcag` 3.2.1, `a11y` | agree | 1 | `jsx-a11y/no-autofocus`, `no-distracting-elements` | on |
| `react.a11y-contrast` | Text meets the contrast minimum | `wcag` 1.4.3 | — | 2 | **Nothing static asserts it.** Contrast is a rendered-pixel property; it needs an axe run in a browser, which is a different instrument at a different locus | off |

### Testing

| Identity | Asserts | Sources | Agree | B | Instrument | Default |
| --- | --- | --- | --- | --- | --- | --- |
| `react.test-user-visible-queries` | A test finds elements the way a user would | `tl`, `tl+` | agree | 1 | `testing-library/prefer-screen-queries`, `prefer-presence-queries`, `prefer-query-by-disappearance` | on |
| `react.test-no-implementation-access` | A test does not reach into the DOM tree or the container | `tl`, `tl+` | agree | 1 | `testing-library/no-container`, `no-node-access` | on |
| `react.test-async-awaited` | Async queries and events are awaited | `tl+` | — | 1 | `testing-library/await-async-queries`, `await-async-events`, `await-async-utils`, `no-await-sync-queries` | on |
| `react.test-find-over-wait` | `findBy` replaces a `waitFor` around a `getBy` | `tl+` | — | 1 | `testing-library/prefer-find-by` | on |
| `react.test-no-debug-residue` | Debug helpers do not survive into a committed test | `tl+` | — | 1 | `testing-library/no-debugging-utils` | on |
| `react.test-behaviour-not-implementation` | A test asserts what the user experiences, not how it is built | `tl`, `testing 001` | agree | 3 | — . The plugin enforces the mechanics; the principle is judgment | n/a |

## Stack-neutral

Forty-two properties that belong to neither stack. **This is a gap in the
naming standard, not a category this stage invented**: `plan.md` says identities
are *stack-scoped*, and a commit-message convention has no stack. They are minted
under `any.` and the standard needs the row — recorded in
[Findings](#findings) and in `todo.md`.

Rows marked with a control ID are **already enforced by this organisation's
register**. They are listed so the overlap is visible and excluded from the
bucket counts, per [How a bucket was
decided](#how-a-bucket-was-decided).

### Version control

| Identity | Asserts | Sources | Agree | B | Instrument | Default |
| --- | --- | --- | --- | --- | --- | --- |
| `any.conventional-commits` | Commit subjects follow `type(scope): description` | `git 001` | — | 1 | `commitlint` with `@commitlint/config-conventional`. **Not a registered source** — the instrument exists, the source register has no row for it | on |
| `any.imperative-commit-subject` | A commit subject is imperative present tense | `git 002` | — | 2 | Nothing asserts it reliably. A word-list check would be a heuristic | off |
| `any.commit-subject-length` | A subject fits in 72 characters | `git 003` | — | 1 | `commitlint` `header-max-length` | on |
| `any.commit-references-work-item` | A commit body or footer names the work item | `git 004` | — | 1 | `commitlint` `references-empty` | off |
| `any.no-direct-push-to-default` | Nothing lands on the default branch outside a pull request | `git 005` | — | 1 | **Already gated: CI-001** | n/a |
| `any.ci-green-before-merge` | Every check passes before merge | `git 006` | — | 1 | **Already gated: CI-001** | n/a |
| `any.branch-naming` | Branches read `type/short-description` | `git 101` | — | 1 | A GitHub ruleset branch-name pattern | off |
| `any.small-pull-requests` | A pull request is reviewable in under thirty minutes | `git 102` | — | 2 | A diff-size threshold could hold it; the number is arbitrary and would need S3 | off |
| `any.linear-merged-history` | Merged history contains only logical commits | `git 103` | — | 1 | A GitHub ruleset merge-method restriction | off |
| `any.pull-request-description` | A pull request says what changed, why, and how to verify | `git 104` | — | 2 | A template exists; a check that it was filled in does not | off |
| `any.delete-merged-branches` | Branches are deleted after merge | `git 105` | — | 1 | A repository setting, not a rule | on |
| `any.signed-commits` | Commits are signed where policy requires | `git 201` | — | 1 | A GitHub ruleset signature requirement. **CI-001 adjacent** | off |
| `any.semver-release-tags` | Releases are tagged `vMAJOR.MINOR.PATCH` | `git 202` | — | 1 | A GitHub ruleset tag pattern | off |
| `any.changelog-maintained` | A changelog is updated as part of release | `git 203` | — | 2 | A check that the file moved with the tag could hold it | off |

### API design

Every row here needs an OpenAPI document to check against. Where a repository
has none, the whole group is bucket 3 by default — that is a condition on the
bucket, not a property of the rule, and S4 has to decide whether a profile may
assert something the repository cannot produce evidence for.

| Identity | Asserts | Sources | Agree | B | Instrument | Default |
| --- | --- | --- | --- | --- | --- | --- |
| `any.rest-resource-nouns` | Paths name resources, not actions | `api 001` | — | 2 | `spectral` over an OpenAPI document. **Not a registered source** | on |
| `any.plural-collections` | Collections are plural, items are addressed by id | `api 101` | — | 2 | `spectral` | on |
| `any.http-method-semantics` | Methods carry their standard meanings and idempotency | `api 002` | — | 3 | — . The spelling is checkable; the semantics are not | n/a |
| `any.standard-status-codes` | Responses use the conventional status codes | `api 003` | — | 2 | `spectral`, against a declared set | on |
| `any.structured-error-body` | Errors carry a code, a message and a correlation id | `api 004` | — | 2 | `spectral`, against a shared error schema | on |
| `any.explicit-api-version` | The API version is explicit from the first release | `api 005` | — | 2 | `spectral` | on |
| `any.paginated-collections` | No collection endpoint returns an unbounded list | `api 006` | — | 2 | `spectral` | on |
| `any.documented-endpoints` | Every endpoint has request and response schemas and examples | `api 104` | — | 2 | `spectral` | on |
| `any.iso8601-datetimes` | Date and time fields are ISO 8601 strings | `api 106` | — | 2 | `spectral`, against a format assertion | on |
| `any.location-header-on-created` | A 201 carries a `Location` | `api 105` | — | 2 | `spectral` | off |
| `any.filter-and-sort-documented` | Collection query parameters are documented | `api 102` | — | 2 | `spectral` | off |
| `any.correlation-id-propagated` | A request id is present in every response and traced through | `api 103` | — | 3 | — . The header is checkable; propagation is not | n/a |
| `any.health-endpoint` | A health endpoint reports service and dependency state | `api 202` | — | 2 | `spectral` for its presence; not for its truthfulness | off |
| `any.conditional-requests` | Frequently polled resources support `ETag` | `api 203` | — | 3 | — | n/a |
| `any.json-merge-patch` | Partial updates use RFC 7396 | `api 201` | — | 3 | — | n/a |

### Security

| Identity | Asserts | Sources | Agree | B | Instrument | Default |
| --- | --- | --- | --- | --- | --- | --- |
| `any.no-secrets-in-vcs` | No credential is committed | `security 001`, `asvs` | agree | 1 | **Already gated: SEC-001, SEC-002** | n/a |
| `any.dependency-vulnerability-scanning` | Known CVEs in dependencies are surfaced | `security 202`, `asvs` | agree | 1 | **Already gated: SUP-002** for update proposals; CVE surfacing is adjacent and not identical | n/a |
| `any.https-everywhere` | HTTP is rejected or redirected; HSTS is set | `security 002`, `asvs` | agree | 2 | Deployment configuration, checkable in IaC. **IAC-001 adjacent** | off |
| `any.security-response-headers` | CSP, `nosniff`, frame options and referrer policy are set | `security 101`, `asvs` | agree | 2 | Checkable in IaC or in a response test | off |
| `any.authenticate-non-public-endpoints` | Every non-public endpoint authenticates | `security 003`, `asvs` | agree | 3 | — | n/a |
| `any.authorise-separately-from-authenticate` | Permission is checked as well as identity | `security 004`, `asvs` | agree | 3 | — . The single most consequential property in this register and the least checkable | n/a |
| `any.validate-at-boundaries` | Input is validated at the system boundary | `security 005`, `asvs` | agree | 3 | — | n/a |
| `any.rate-limit-sensitive-endpoints` | Authentication and sensitive writes are rate limited | `security 102`, `asvs` | agree | 2 | Checkable in IaC where the limit is declared there | off |
| `any.adaptive-password-hashing` | Passwords use bcrypt, Argon2 or scrypt | `security 104`, `asvs` | agree | 2 | Per-stack: `python.no-insecure-hash` catches the negative, nothing asserts the positive | off |
| `any.explicit-cors` | CORS origins are explicit, never `*` with credentials | `security 105`, `asvs` | agree | 2 | Checkable in IaC or in configuration | off |
| `any.secret-rotation` | Secrets rotate on a schedule and on compromise | `security 106`, `asvs` | agree | 3 | — . A process, not a code property | n/a |
| `any.security-audit-logging` | Security-relevant events are logged | `security 201`, `asvs` | agree | 3 | — | n/a |
| `any.threat-modelling` | New features handling sensitive data are threat modelled | `security 203`, `asvs` | agree | 3 | — . Arguably not a code rule at all, and a candidate for removal at S4 | n/a |

## Bucket 4 — assistant behaviour

`rules/code-quality.md` § Verify Information is thirteen bullets, none of which
is about code. **They are tracked, not discarded**, and they are tracked *here*
rather than in the register above so that no count includes them.

The recommendation is that Craft **does not carry them**. They are instructions
to an assistant about how to respond — how to present edits, what not to
apologise for, when not to ask for confirmation — and Craft's judgment-only
residue is prose about *code* that an assistant loads. Mixing the two would put
"never use apologies" in the same artefact as "props and state are immutable",
which is the category error the fourth bucket exists to prevent. Where they
belong is whatever governs assistant instructions in a repository — in this
repository, `CLAUDE.md` — and that is not this workstream's to define.

| Statement | Why it is bucket 4 |
| --- | --- |
| Verify information before presenting it | About the assistant's confidence, not the code |
| Change file by file and allow review between | About the interaction, not the code |
| Never use apologies | About tone |
| Avoid feedback about understanding in comments | Half about comments, half about tone; the code half duplicates `python.self-documenting-code` |
| Do not suggest whitespace changes | About the diff the assistant proposes |
| Do not invent changes beyond what was asked | About scope |
| Do not ask for confirmation of what is already in context | About the interaction |
| Do not remove unrelated code | About scope, and the one statement here with a real code consequence — it is a review property, not a rule |
| Provide edits in a single chunk | About presentation |
| Do not ask the user to verify what is visible in context | About the interaction |
| Do not show the current implementation unless asked | About presentation |
| Do not suggest changes where none are needed | About the interaction |
| Always link to real files | About presentation |

Two further sections of the same file — § Errors and § Logging, ten bullets — are
**not** bucket 4. They are about code, and they are assessed above as
`python.no-blind-except`, `python.exception-chaining`,
`python.no-silent-exception-swallow`, `python.no-log-and-reraise`,
`python.exception-carries-context` and `python.structured-logging`. Reading the
file as a whole and routing it to one bucket would have lost all six.

## The hand check

One file's classification was re-read by hand against the machine pass, per
`plan.md` § S2. The file is `rules/clean-code.md` — chosen because it is the file
whose rules *sound* the most enforceable, and therefore the one where an
over-claim was most likely.

The machine pass was a text match from each rule to a ruff rule whose summary
covers the same ground. It proposed bucket 1 for eight of the fifteen rules. The
hand read changed the classification of **five** of those eight: two moved out of
bucket 1 entirely, one was split across two buckets, and two stayed in bucket 1
but gained a qualification that changes what installing them costs.

| Rule | Machine proposed | Hand read | Why it moved |
| --- | --- | --- | --- |
| `RULE-002` functions under 20 lines | 1, via `PLR0915` | **2** | `PLR0915` counts statements, not lines, and its default is 50. The rule and the tool are measuring different things; the tool is a proxy and the row now says so |
| `RULE-003` eliminate duplication | 1, via `SIM` family | **2** | Nothing in `SIM` detects duplication. The match was on the word *simplify* |
| `RULE-101` no more than 3 parameters | 1, via `PLR0913` | 1, **contested** | The rule is real, but `clean-code` says 3 and ruff defaults to 5. Left in bucket 1 with the disagreement recorded rather than silently resolved to one number |
| `RULE-001`, `RULE-104`, `RULE-205` naming | 1, via `N8xx` | **split** | `N8xx` asserts casing. None of the three rules is about casing — they are about whether the name means anything. Split into `python.naming-form` (1) and `python.naming-intent` (3) |
| `RULE-102` avoid deep nesting | 1, via `PLR1702` | 1, **preview** | The rule exists but is not in ruff's stable set. Reachable only by enabling 140 preview rules at once |

Five of the eight bucket-1 proposals — five of fifteen rules in the file — were
classified in a way a person had to correct. Applied to the register as a whole
that is not a proportion to extrapolate, because the other files were then read
with these five corrections already in mind; it is the reason the correction pass
happened at all.

**What the check says about the method.** A text match from a prose rule to a
tool's rule summary agrees far too readily. Every bucket-1 claim in this register
was re-read against what the tool actually asserts, and the three failure shapes
the hand check found — a proxy accepted as the property, a family matched on a
word, and a rule that exists but is unreachable — are why the Instrument column
carries `preview` and `off` markers rather than a bare rule ID.

## Bucket shares

The exit criterion asks for bucket 1's share of buckets 1–3, per stack. Bucket 4
is excluded because `plan.md` excludes it, and the rows carrying a control ID are
excluded because they are already enforced.

| Stack | 1 | 2 | 3 | Total | Bucket 1's share |
| --- | --- | --- | --- | --- | --- |
| Python | 49 | 10 | 12 | 71 | **69%** |
| React | 53 | 6 | 9 | 68 | **78%** |
| Stack-neutral | 8 | 20 | 10 | 38 | **21%** |

The counts were derived from this file rather than kept alongside it:

```bash
# Rows in one section, by bucket. The bucket is the fifth cell of every
# property row; the four rows carrying a control ID are the ones excluded.
awk '/^## Python/,/^## React/' docs/craft/assess.rules.md \
  | grep '^| `python\.' | awk -F'|' '{print $6}' | sort | uniq -c
```

Three qualifications, without which the shares flatter the work.

**Python's 69% is not 69% of the value.** Three of the forty-nine bucket-1 rows
are unreachable as they stand — `python.nesting-depth` and `python.class-size`
are ruff `preview`, and `python.no-assert-for-enforcement` needs a per-path
exclusion before it can be switched on at all. Against that, the twelve
judgment-only rows — single responsibility, dependency direction, naming intent,
abstraction ordering — are the ones a reviewer actually spends time on. A share
counts rows, not weight.

**React's 78% rests on rules six different plugins ship in six different
presets, and it is the least trustworthy number here.** Fourteen of the
fifty-three bucket-1 rows are `off`, `strict`-only, `type-checked`-only or in no
preset at all — counted by hand from the Instrument column, which is why those
markers are there. Two more, `react.no-legacy-proptypes` and
`react.jsx-runtime-assumed`, are in a recommended preset and assert the *wrong*
thing for this stack. The number of rules that exist and the number a team gets
by installing the recommended configs are not the same number, and the gap is
this register's main practical finding.

**The stack-neutral 21% is the honest one.** Commit conventions and API shape
have real instruments; authorisation, validation and threat modelling do not, and
saying so is worth more than a profile that pretends otherwise.

## Findings

**1. React's most-documented anti-pattern ships with its lint rule disabled.**
`react-hooks` 7.1.1 contains `no-deriving-state-in-effects` and its preset is
`Off`. *You Might Not Need an Effect* opens with exactly that anti-pattern. The
same is true of `exhaustive-effect-dependencies`, which is `Off` and has no page
on `react.dev` at all. Read from the plugin's own bundle: eleven of its
twenty-six rules are `Off`, fourteen are `Recommended`, one is
`RecommendedLatest`. A profile that installs `recommended` and stops has not
installed the thing the documentation is about.

**2. The React enforceable set is covered twice, by two plugins that know it.**
`react-hooks` 7.x and `@eslint-react` 5.x both ship `rules-of-hooks`,
`exhaustive-deps`, `set-state-in-effect`, `set-state-in-render`, `purity`,
`static-components`, `use-memo`, `error-boundaries` and `unsupported-syntax`
under those names. `@eslint-react` ships `disable-conflict-eslint-plugin-react`
and `disable-conflict-eslint-plugin-react-hooks` configs precisely because of it;
what those configs contain delegates to `eslint-plugin-react-x` and was not
resolved from the published bundle, so S3 reads it from an installed tree rather
than this register asserting it. **A profile that names both plugins without
naming a conflict config double-reports**, and double-reporting is exactly the
noise S3 exists to measure.

**3. `eslint-plugin-react`'s recommended config asserts two things that are wrong
for the stack this workstream targets.** `react/prop-types` and
`react/react-in-jsx-scope` are both in `recommended`, and both are wrong for
TypeScript on React 17+. The plugin is not at fault — it supports old codebases —
but it means *installing a recommended config* is not a defensible default here,
and the `jsx-runtime` config exists to undo half of it. This is the concrete form
of the survey's finding 9: a tool source says what the tool will flag, not what
good code is.

**4. WCAG's largest failure class has no static rule.** Contrast, 1.4.3, is a
rendered-pixel property. `jsx-a11y` has thirty-nine rules and none of them can
see a colour. Registering `react.a11y-contrast` as bucket 2 with *no* instrument
is the honest entry; quietly leaving it out would have let the accessibility
group read as complete.

**5. Five sources this register needs were not registered, and S1 has them now.**
`commitlint` carries four `any.` rows and `spectral` carries nine; neither
appeared in `survey.sources.md`, nor did `eslint-plugin-promise`, which carries
one React row. Nor did the two standards the first two approximate —
Conventional Commits and the OpenAPI Specification — which belong there for the
same reason WCAG sits beside `jsx-a11y`. They were reached by asking *what would
enforce this* rather than *what did we register*, which is the right direction
and means a survey built only from what *describes* good code will always be one
pass behind an assessment that asks what *enforces* it. All five are now
registered, with findings 10 and 11 recording why they were missing.

**6. Identities have a third scope, and the naming standard has two.**
`plan.md` says identities are stack-scoped. Forty-two properties here belong to
neither stack — commit messages, API shape, authorisation — and are minted under
`any.`. The alternative was minting `python.conventional-commits` and
`react.conventional-commits` for the same property, which is the duplication the
standard exists to prevent. `plan.md`'s naming standard needs the row.

**7. Four properties are already controls, and one of the four is not quite.**
`any.no-secrets-in-vcs` is SEC-001 and SEC-002; `any.no-direct-push-to-default`
and `any.ci-green-before-merge` are CI-001. The fourth,
`any.dependency-vulnerability-scanning`, is the one that is *not* quite: SUP-002
governs update proposals per ecosystem, which surfaces CVEs as a side effect
rather than asserting the property. A fifth,
`python.no-hardcoded-credentials`, overlaps SEC-001 without being it — ruff reads
the source, SEC-001 scans the repository — so it stays counted as a craft
property. Whether the SUP-002 gap is Craft's to close, or the register's, is
decision 1 and is S4's.

**8. The security overlap resolved cleanly, and in ASVS's favour.**
`platform/security.md`'s twenty-one rules were read against ASVS rather than
alongside it. Every one of them is an ASVS requirement at a coarser grain; none
asserts anything ASVS does not. Where they are cited together the agreement is
real, and where a profile has to choose an authority it is ASVS — a standards
body with a versioned document — rather than an unlicensed internal file. That
is a finding in the toolkit's favour as a *source of ideas* and against it as a
*source of prose*, which is exactly what the licence finding predicted.

**9. Ruff's taxonomy is smaller than it looks, in the way that matters.** 969
rules, but 812 stable, 140 preview and 17 removed; 58 stable linters, not 59 —
the survey's number counted a rule with no code and no linter,
`pytest-fixture-autouse`, which is preview and unaddressable. Of the 812 stable
rules, 421 carry no fix at all. The Python work is still selection rather than
rule-writing, as the survey said; it is selection from 812, and roughly half of
what gets selected will be a finding somebody has to fix by hand.

## What this stage did not settle

- **Whether "archetype" is a real axis.** Deferred to S4 by `plan.md`, and this
  register does not resolve it. What it offers as evidence: the properties that
  would vary are almost all `any.` — a library has no API surface to shape and no
  endpoints to authorise — while `python.` and `react.` rows vary hardly at all.
  That is an argument that archetype is real but narrow, and S4 has it.
- **The `preview` question.** Two Python properties — `python.nesting-depth`
  and `python.class-size` — are reachable only by enabling all 140 of ruff's
  preview rules. Whether a profile may do that is a
  real decision with a measurable cost, and it is S3's to measure.
- **What `disable-conflict-eslint-plugin-react*` actually contains.** Read from
  an installed tree at S3, not asserted here.
- **Contested rows.** Fifteen are marked `contested`. `plan.md` gives them to
  S3's second reader, and none of them has been quietly resolved to one side
  here.

## Exit criterion

> Every property carries a bucket, contested classifications are marked as
> contested rather than resolved silently, and bucket 1's share of buckets 1–3 is
> stated for each stack.

**Met.** 181 properties: 71 Python, 68 React and 42 stack-neutral, each carrying
a bucket; plus 13 bucket-4 statements tracked separately and counted nowhere.
Four of the 181 carry a control ID and are excluded from the shares, which is why
the shares total 177. Fifteen rows are marked `contested` and none is resolved.
Bucket 1's share is stated per stack above, with the three qualifications that
stop the number being read as more than it is.

The criterion says nothing about the sweep, the hand check or the two unregistered
instruments, and this document does not tick those. A stage is finished when its
criterion is met, not when its boxes run out.
