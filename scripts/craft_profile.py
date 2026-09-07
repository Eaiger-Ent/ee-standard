#!/usr/bin/env -S uv run python
"""Materialise a Craft profile's configuration — S3's bench, at either level.

**Why this is a second script and not more of `craft_scaffold.py`.** The
scaffold is the *subject* — a new repository of the shape the profile is for.
This is the *instrument* — the configuration under test. S3 varies the
instrument (a demotion, `preview = true`, a probe flipped on) and leaves the
subject exactly as it was, and a bench whose instrument and subject share a file
cannot do that without rewriting the thing it is measuring.

**What this is not.** It is not the Craft register of [ADR
0053](../docs/adr/0053-the-craft-mapping-is-register-data.md). That register is
data with a schema, S4 designs it and S5 builds it; this is one concrete
configuration, written by hand from the resolved rows of
`docs/craft/assess.rules.md` so that S3 has something to assemble and run. Nor
is it the surface the installed profile writes — whether that is a `ruff.toml`
or a `[tool.ruff]` section is S4's, and `docs/craft/review.bench.md` records why
the bench chose the standalone file.

It writes into the same gitignored `temp/craft-bench/` that
[`craft_scaffold.py`](craft_scaffold.py) writes, for the reasons that script's
docstring gives, and it refuses to overwrite a file that has been edited.

**Two levels, and `strict` extends `standard` rather than restating it.** S4's
`design.profiles.md` § The strictness levels defines `strict` as `standard` plus
the rows the register proposes `off` that have an instrument, so the files this
writes say exactly that: `strict.toml` is `extend = "ruff.toml"` and the
selectors it adds. A second full selector list would be a second copy of the
first, free to drift from the level it is defined as a superset of.

Run it:

    uv run python scripts/craft_scaffold.py                  # the subject, first
    uv run python scripts/craft_profile.py                   # standard
    uv run python scripts/craft_profile.py --level strict    # and the level above it
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TARGET = REPO_ROOT / "temp" / "craft-bench"

#: The `standard` configuration, keyed by its path under the target directory.
#: Read the configuration here rather than anywhere else — every entry carries
#: the property identity it exists for, so the selection reads back against
#: `docs/craft/assess.rules.md` rather than being trusted.
FILES: dict[str, str] = {
    "python/ruff.toml": """\
# The Python candidate default-on configuration — stage S3 of
# `docs/craft/plan.md`, built from the resolved register in
# `docs/craft/assess.rules.md`.
#
# Every entry carries the property identity it exists for. Rules the register
# defaults `off` are simply absent: listing them here as exclusions would be a
# second copy of the register's negatives, and the register is the register.
#
# There is no `per-file-ignores` section, and that absence is deliberate rather
# than unfinished. `python.test-code-quality` asserts that the lint profile
# applies to test code too, and `python.no-assert-for-enforcement` was resolved
# as a rule *scoped to the source path* rather than one excused from `tests/` —
# so S101 is selected in `src/ruff.toml` and nothing anywhere is exempted.
#
# Nothing in this file has been run. Assembling it is the next step of S3.

# python.line-length. One key serves both `ruff format` and E501, which is the
# constraint the register's resolution puts on this property: a formatter and a
# limit cannot disagree when there is only one number. Provisional — C6 owes
# this number a rationale.
line-length = 88

# So I001 can tell first-party from third-party under a `src` layout. Not a
# property: a fact about the scaffold that the property needs in order to hold.
src = ["src"]

# `target-version` is deliberately absent, for the reason `CLAUDE.md` gives
# about this repository's own config: ruff derives it, and writing it out is a
# second copy of a floor that already exists in `requires-python`.

[lint]
# Four entries are linter selectors rather than exact codes. Three of them —
# `DTZ`, `PTH` and `N` — are where the register cites a *range* that ruff 0.16.5
# has since overtaken: `DTZ001` to `DTZ012` leaves out `DTZ901`, `PTH100` to
# `PTH210` leaves out `PTH211`, and `N801` to `N818` leaves out `N999`. Each of
# the three asserts the property its range was cited for. `C4` is the fourth,
# and there the range and the linter coincide exactly.
#
# A range citation rots; a linter citation does not. That is a finding about how
# the Craft register should spell an instrument, and it is recorded in
# `docs/craft/review.bench.md` rather than fixed here.
select = [
  # --- Correctness and safety ---
  "B006", "RUF012",                                 # python.no-mutable-default-argument
  "B008",                                           # python.no-call-in-default-argument
  "B023",                                           # python.no-loop-variable-capture
  "F401",                                           # python.no-unused-import
  "F841",                                           # python.no-unused-variable
  "ARG001", "ARG002", "ARG003", "ARG004", "ARG005", # python.no-unused-argument
  "PLW0603",                                        # python.no-global-mutable-state
  "SLF001",                                         # python.no-private-member-access
  "DTZ",                                            # python.timezone-aware-datetimes
  "PLW2901",                                        # python.no-shadowed-loop-variable

  # --- Errors and exceptions ---
  "BLE001", "E722",                                 # python.no-blind-except
  "B904",                                           # python.exception-chaining
  "S110", "S112", "SIM105",                         # python.no-silent-exception-swallow

  # --- Structure and size ---
  "PLR0915", "C901",                                # python.function-length
  "PLR0913", "PLR0917",                             # python.function-parameter-count

  # --- Naming, style and layout ---
  "N",                                              # python.naming-form
  "E501",                                           # python.line-length
  "I001",                                           # python.import-order
  "TID252",                                         # python.no-relative-parent-imports
  "W291", "W293",                                   # python.no-trailing-whitespace
  "UP007", "UP045",                                 # python.pep604-unions
  "PTH",                                            # python.pathlib-over-os-path
  "PERF401", "C4",                                  # python.comprehension-over-manual-loop
  "FBT001", "FBT002",                               # python.no-boolean-trap

  # --- Documentation and comments ---
  "ERA001",                                         # python.no-commented-out-code
  "RUF100",                                         # python.no-unused-suppression

  # --- Typing ---
  # python.annotate-public-api cites "ANN001, ANN201, ANN2xx". ANN202 is the
  # *private* function's return type and is left out: the property says public.
  # ANN002 and ANN003 (`*args`, `**kwargs`) are not cited and are left out too.
  # Both departures are recorded in `docs/craft/review.bench.md`.
  "ANN001", "ANN201", "ANN204", "ANN205", "ANN206", # python.annotate-public-api
  "ANN401",                                         # python.no-any

  # --- Testing ---
  "INP001",                                         # python.test-layout
  "PT018",                                          # python.test-single-behaviour (proxy)
  "PT011", "PT012",                                 # python.narrow-raises
  "PT006", "PT007",                                 # python.parametrize-form

  # --- Security ---
  "S608",                                           # python.parameterised-sql
  "S105", "S106", "S107",                           # python.no-hardcoded-credentials
  "S324",                                           # python.no-insecure-hash
  "S501",                                           # python.tls-verification-on
  "S311",                                           # python.crypto-grade-randomness
  "G001", "G002", "G003", "G004", "LOG015",         # python.structured-logging
]

[lint.mccabe]
# python.function-length, the branching half. Ten is McCabe's own published
# recommendation and ruff's default, and no source in this register disputes it,
# so this number is cited rather than chosen. C6 § The four numbers.
max-complexity = 10

# python.function-length, the size half. **Not ruff's default of 50**, which
# leaves the property unenforced: a function under the complexity ceiling can
# still run to fifty straight-line statements, which is exactly what
# `clean-code 002` objects to and what `C901` will never see. Twenty-five admits
# a function of roughly thirty-five to forty physical lines once blanks,
# comments and a docstring are counted back in, which is a generous reading of
# the source's twenty lines rather than a strict one. Generous is the right side
# to err on for a number nothing has measured. C6 § The four numbers.
[lint.pylint]
max-statements = 25
# python.function-parameter-count. The register resolved a contest here: the
# sources were counting different things, so both numbers stand.
max-args = 5
max-positional-args = 3

[lint.flake8-tidy-imports]
# python.no-relative-parent-imports. TID252 bans what this names; "parents" is
# the setting that makes it the property rather than a ban on all relatives.
ban-relative-imports = "parents"
""",
    "python/src/ruff.toml": """\
# python.no-assert-for-enforcement, and nothing else.
#
# The register's resolution was explicit: S101 is *scoped to the package source
# path*, not excused from `tests/`. Ruff has no way to select a rule for one
# path — it has `per-file-ignores`, which is the exemption the resolution
# rejected — so the scope is expressed the only way the tool allows, as a
# nested configuration that the source tree resolves against and the test tree
# does not.
#
# What that costs is a second file, and `docs/craft/review.bench.md` records it:
# an installer that writes this profile writes two configs for one property.

extend = "../ruff.toml"

[lint]
extend-select = ["S101"]
""",
    "react/eslint.config.js": """\
// The React candidate default-on configuration - stage S3 of
// `docs/craft/plan.md`, built from the resolved register in
// `docs/craft/assess.rules.md`.
//
// Two things about its shape, both of them the register's doing.
//
// **Presets are used where the register names a preset, and nowhere else.**
// `@eslint-react`'s `recommended` is the JSX-correctness base because the
// register resolved `react.no-legacy-proptypes` and `react.jsx-runtime-assumed`
// by choosing it, and `jsx-a11y`'s `recommended` is a base because the register
// counts five of its rules as inherited rather than keyed. Everything else is
// named rule by rule. Finding 3 is why: a recommended config says what a tool
// will flag, not what good code is, and `eslint-plugin-react`'s asserts two
// things that are wrong for this stack.
//
// **Every rule the register names is written out, even where the base already
// enables it.** That is not redundancy for its own sake. Finding 1 is a rule
// this workstream wants that its plugin ships `off`; the same mechanism can
// silently *remove* a rule from a preset in a later release, and a selection
// that reads back against the register cannot lose one that way.
//
// Nothing in this file has been run. Assembling it is the next step of S3.

import eslintReact from '@eslint-react/eslint-plugin'
import jsxA11y from 'eslint-plugin-jsx-a11y'
import react from 'eslint-plugin-react'
import reactHooks from 'eslint-plugin-react-hooks'
import testingLibrary from 'eslint-plugin-testing-library'
import globals from 'globals'
import tseslint from 'typescript-eslint'

/** Everything the profile lints. */
const SOURCE = ['src/**/*.ts', 'src/**/*.tsx']
/** Non-component modules - see `react.explicit-return-types` below. */
const MODULES = ['src/**/*.ts']
/** Tests, which `eslint-plugin-testing-library` is scoped to. */
const TESTS = ['src/**/*.test.ts', 'src/**/*.test.tsx']

export default [
  { ignores: ['node_modules/**', 'dist/**', 'coverage/**'] },

  // The parser and the plugin registration, with no preset rules attached.
  // `react.strict-type-checking` is asserted by `tsconfig.json` rather than
  // here - no lint rule can assert a compiler flag - and the type-checked rules
  // below need the project service to read the types it turns on.
  {
    ...tseslint.configs.base,
    files: SOURCE,
    languageOptions: {
      ...tseslint.configs.base.languageOptions,
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
      globals: { ...globals.browser },
    },
  },

  // JSX correctness. The base the register chose, then the rules it names.
  { ...eslintReact.configs.recommended, files: SOURCE },
  {
    files: SOURCE,
    rules: {
      // react.list-keys
      '@eslint-react/no-missing-key': 'error',
      '@eslint-react/no-duplicate-key': 'error',
      '@eslint-react/jsx-no-key-after-spread': 'error',
      // react.no-array-index-key
      '@eslint-react/no-array-index-key': 'error',
      // react.no-dangerous-html
      '@eslint-react/dom-no-dangerously-set-innerhtml': 'error',
      // react.safe-external-links - strict only
      '@eslint-react/dom-no-unsafe-target-blank': 'error',
      // react.no-unknown-dom-property
      '@eslint-react/dom-no-unknown-property': 'error',
      // react.no-comment-textnodes
      '@eslint-react/jsx-no-comment-textnodes': 'error',
      // react.no-leaked-conditional-render - type-checked only
      '@eslint-react/no-leaked-conditional-rendering': 'error',
      // react.no-nested-component-definitions is instrumented by
      // `react-hooks/static-components` below, and **not** by this rule.
      // C4 demoted it: one nested component drew both, from two plugins under
      // two different names, so no name-keyed `disable-conflict` config can
      // ever separate them. `review.bench.md` § No defect reported twice has
      // the case.
      '@eslint-react/no-nested-component-definitions': 'off',
      // react.context-value-stability - strict only
      '@eslint-react/no-unstable-context-value': 'error',
      // react.no-class-components - strict only
      '@eslint-react/no-class-component': 'error',
      // react.props-and-state-immutable
      '@eslint-react/no-direct-mutation-state': 'error',
      // react.no-deprecated-api
      '@eslint-react/no-component-will-mount': 'error',
      '@eslint-react/no-component-will-receive-props': 'error',
      '@eslint-react/no-component-will-update': 'error',
      '@eslint-react/no-create-ref': 'error',
      '@eslint-react/no-forward-ref': 'error',
      '@eslint-react/no-use-context': 'error',
      // react.no-leaked-subscriptions - six rules, and `react-hooks` has no
      // equivalent for any of them.
      '@eslint-react/web-api-no-leaked-event-listener': 'error',
      '@eslint-react/web-api-no-leaked-fetch': 'error',
      '@eslint-react/web-api-no-leaked-intersection-observer': 'error',
      '@eslint-react/web-api-no-leaked-interval': 'error',
      '@eslint-react/web-api-no-leaked-resize-observer': 'error',
      '@eslint-react/web-api-no-leaked-timeout': 'error',
    },
  },

  // The Rules of React and the effects rules. No preset: finding 1 is that
  // installing `recommended` and stopping leaves off the rule the React
  // documentation opens with.
  //
  // **This block also stands `@eslint-react`'s copies down**, by hand, because
  // the shipped `disable-conflict-eslint-plugin-react-hooks` config stands down
  // the *other* plugin: it turns twelve `react-hooks/*` rules off so that
  // `@eslint-react` owns them. That is the opposite of what the register cites
  // - most Rules-of-React rows name a `react-hooks` rule, and two of the rules
  // this profile most wants, `no-deriving-state-in-effects` and
  // `preserve-manual-memoization`, have no `@eslint-react` equivalent at all.
  // So neither shipped conflict config is applied and the seven names that were
  // resolving twice are turned off on the `@eslint-react` side here, next to the
  // ownership claim they qualify. C1 found this; `review.bench.md` records it.
  {
    files: SOURCE,
    plugins: { 'react-hooks': reactHooks },
    rules: {
      // `@eslint-react`'s copies of what this block owns.
      '@eslint-react/rules-of-hooks': 'off',
      '@eslint-react/purity': 'off',
      '@eslint-react/set-state-in-render': 'off',
      '@eslint-react/set-state-in-effect': 'off',
      '@eslint-react/exhaustive-deps': 'off',
      '@eslint-react/use-memo': 'off',
      '@eslint-react/static-components': 'off',
      // react.hooks-at-top-level, react.hooks-only-from-react-functions
      'react-hooks/rules-of-hooks': 'error',
      // react.components-are-idempotent, react.no-side-effects-in-render
      'react-hooks/purity': 'error',
      'react-hooks/globals': 'error',
      // react.props-and-state-immutable, react.hook-values-immutable,
      // react.jsx-values-immutable
      'react-hooks/immutability': 'error',
      // react.no-set-state-in-render
      'react-hooks/set-state-in-render': 'error',
      // react.refs-not-read-in-render
      'react-hooks/refs': 'error',
      // react.no-derived-state-in-effect - the plugin ships this `off`
      'react-hooks/no-deriving-state-in-effects': 'error',
      // react.no-set-state-in-effect
      'react-hooks/set-state-in-effect': 'error',
      // react.effect-dependencies-complete - recommended at `warn`
      'react-hooks/exhaustive-deps': 'error',
      // react.memoization-preserved
      'react-hooks/preserve-manual-memoization': 'error',
      'react-hooks/use-memo': 'error',
      // react.no-nested-component-definitions
      'react-hooks/static-components': 'error',
    },
  },

  // One rule, and its presets deliberately not installed. Five of the six
  // properties the register cites this plugin for have an `@eslint-react`
  // instrument that is taken above; this is the sixth, which does not.
  // `disable-conflict-eslint-plugin-react` is not applied either: it turns off
  // forty `react/*` rules, and this profile enables one, which is not among
  // them. Reading it was how that was settled rather than assumed.
  {
    files: SOURCE,
    plugins: { react },
    rules: {
      // react.no-duplicate-props
      'react/jsx-no-duplicate-props': 'error',
    },
  },

  // TypeScript. Named rule by rule rather than by preset, for the same reason
  // as the React half.
  {
    files: SOURCE,
    rules: {
      // react.no-explicit-any
      '@typescript-eslint/no-explicit-any': 'error',
      // react.no-unsafe-any-flow
      '@typescript-eslint/no-unsafe-argument': 'error',
      '@typescript-eslint/no-unsafe-assignment': 'error',
      '@typescript-eslint/no-unsafe-call': 'error',
      '@typescript-eslint/no-unsafe-member-access': 'error',
      '@typescript-eslint/no-unsafe-return': 'error',
      // react.no-non-null-assertion
      '@typescript-eslint/no-non-null-assertion': 'error',
      // react.no-floating-promises
      '@typescript-eslint/no-floating-promises': 'error',
      // react.no-misused-promises
      '@typescript-eslint/no-misused-promises': 'error',
      // react.throw-error-objects
      '@typescript-eslint/only-throw-error': 'error',
    },
  },
  // react.explicit-return-types, scoped to exported non-component functions.
  // The scope is expressed as *not a `.tsx` file*, which is the closest a file
  // pattern gets to "not a component". Provisional - C6 owes this scope a
  // rationale, and a component in a `.ts` file would defeat it.
  {
    files: MODULES,
    rules: {
      '@typescript-eslint/explicit-module-boundary-types': [
        'error',
        { allowTypedFunctionExpressions: true },
      ],
    },
  },

  // Accessibility. `recommended` is a base here because the register counts
  // five of its rules - autocomplete-valid, heading-has-content, no-access-key,
  // no-noninteractive-element-interactions and scope - as inherited rather than
  // keyed to a property of their own.
  { ...jsxA11y.flatConfigs.recommended, files: SOURCE },
  {
    files: SOURCE,
    rules: {
      // react.a11y-text-alternatives
      'jsx-a11y/alt-text': 'error',
      'jsx-a11y/img-redundant-alt': 'error',
      'jsx-a11y/iframe-has-title': 'error',
      // react.a11y-form-labels - the second is `off` in `recommended`
      'jsx-a11y/label-has-associated-control': 'error',
      'jsx-a11y/control-has-associated-label': 'error',
      // react.a11y-aria-validity
      'jsx-a11y/aria-props': 'error',
      'jsx-a11y/aria-proptypes': 'error',
      'jsx-a11y/aria-role': 'error',
      'jsx-a11y/aria-unsupported-elements': 'error',
      'jsx-a11y/role-has-required-aria-props': 'error',
      'jsx-a11y/role-supports-aria-props': 'error',
      // react.a11y-keyboard-parity
      'jsx-a11y/click-events-have-key-events': 'error',
      'jsx-a11y/mouse-events-have-key-events': 'error',
      'jsx-a11y/interactive-supports-focus': 'error',
      'jsx-a11y/no-static-element-interactions': 'error',
      // react.a11y-focus-order
      'jsx-a11y/tabindex-no-positive': 'error',
      'jsx-a11y/no-noninteractive-tabindex': 'error',
      'jsx-a11y/aria-activedescendant-has-tabindex': 'error',
      // react.a11y-document-language - `lang` is not in `recommended`
      'jsx-a11y/html-has-lang': 'error',
      'jsx-a11y/lang': 'error',
      // react.a11y-media-captions
      'jsx-a11y/media-has-caption': 'error',
      // react.a11y-link-has-content
      'jsx-a11y/anchor-has-content': 'error',
      'jsx-a11y/anchor-is-valid': 'error',
      // react.a11y-semantic-elements - the last is not in `recommended`
      'jsx-a11y/no-redundant-roles': 'error',
      'jsx-a11y/no-interactive-element-to-noninteractive-role': 'error',
      'jsx-a11y/no-noninteractive-element-to-interactive-role': 'error',
      'jsx-a11y/prefer-tag-over-role': 'error',
      // react.a11y-no-unexpected-focus
      'jsx-a11y/no-autofocus': 'error',
      'jsx-a11y/no-distracting-elements': 'error',
      // react.a11y-link-purpose is bucket 3 and has no instrument: this rule
      // cannot see an `aria-label` and is the register's named false-positive
      // case. Off here, and turned on by hand for C5's probe.
      'jsx-a11y/anchor-ambiguous-text': 'off',
    },
  },

  // Testing, scoped to tests. `react.test-behaviour-not-implementation` is
  // bucket 3 and has nothing here; the plugin enforces the mechanics only.
  {
    files: TESTS,
    plugins: { 'testing-library': testingLibrary },
    rules: {
      // react.test-user-visible-queries
      'testing-library/prefer-screen-queries': 'error',
      'testing-library/prefer-presence-queries': 'error',
      'testing-library/prefer-query-by-disappearance': 'error',
      // react.test-no-implementation-access
      'testing-library/no-container': 'error',
      'testing-library/no-node-access': 'error',
      // react.test-async-awaited
      'testing-library/await-async-queries': 'error',
      'testing-library/await-async-events': 'error',
      'testing-library/await-async-utils': 'error',
      'testing-library/no-await-sync-queries': 'error',
      // react.test-find-over-wait
      'testing-library/prefer-find-by': 'error',
      // react.test-no-debug-residue
      'testing-library/no-debugging-utils': 'error',
    },
  },
]
""",
}


#: The `strict` addition, keyed the same way. Every entry **extends** its
#: `standard` counterpart rather than restating it, because S4 defines the level
#: as a superset and two selector lists would be free to disagree about that.
STRICT_FILES: dict[str, str] = {
    "python/strict.toml": """\
# Craft `python/strict` — `python/standard` plus the rows the register proposes
# `off` that have an instrument to turn on. `docs/craft/design.profiles.md`
# § What `strict` adds, per stack is the list; this is that list as ruff reads
# it, and nothing here restates a selector `ruff.toml` already carries.

extend = "ruff.toml"

# Two of the selectors below are preview rules, and C8 measured what that costs
# for a selection spelled in exact codes: nothing. `preview = true` against a
# *family* selector picks up preview rules wholesale; against exact codes it
# picks up only the codes named. This selection names codes.
preview = true

[lint]
extend-select = [
  "PLC0415",                                        # python.no-import-inside-function
  "EM101", "EM102",                                 # python.exception-message-not-a-literal
  "TRY003",                                         # python.exception-type-carries-its-message
  "RET504",                                         # python.no-redundant-assign-before-return
  "TC001", "TC002", "TC003",                        # python.typing-only-imports
  "S104",                                           # python.no-bind-all-interfaces
  "D100", "D101", "D102", "D103",                   # python.docstring-presence
  "D104", "D105", "D106", "D107",                   # (the same property, D1xx entire)

  # python.docstring-form, and **exact codes rather than `D2xx`, `D4xx`**.
  # S4's schema slice made this the rule rather than a preference: the wide
  # reading brings in `D203` against `D211` and `D212` against `D213`, which
  # ruff warns about and then silently resolves by dropping one — a docstring
  # convention nobody chose. The narrow reading has no such pair.
  "D205", "D401",

  "TD001", "TD002", "TD003", "TD004",               # python.no-untracked-todo
  "TD005", "TD006", "TD007",
  "FIX001", "FIX002", "FIX003", "FIX004",           # (the same property)
  "PLR1702",                                        # python.nesting-depth — preview
  "PLR0904",                                        # python.class-size — preview
]

[lint.pylint]
# python.class-size. Ruff's own default for PLR0904 is 20 public methods; the
# property is about focus rather than about a number, and no source in the
# register proposes one. The default is taken rather than chosen, and this
# comment is the record that it was not measured.
max-public-methods = 20
""",
    "python/src/strict.toml": """\
# The `strict` counterpart of `src/ruff.toml`: the same S101 scoping, over the
# strict selection instead of the standard one. `python.no-assert-for-enforcement`
# is a `standard` property and does not change at this level — what changes is
# the file it has to extend.

extend = "../strict.toml"

[lint]
extend-select = ["S101"]
""",
    "python/mypy-strict.ini": """\
; Craft `python/strict`'s one type-checker key, and the whole of Craft's
; type-checking contribution across both stacks.
;
; `docs/craft/design.profiles.md` § The type checker: TYP-001 already requires
; mypy at `strict`, which covers `python.annotate-public-api` outright, so the
; only key Craft adds is the one `--strict` does not set.
; ADR 0055 cleared it — `disallow_any_explicit` is not a key TYP-001 asserts.
;
; **This is a bench file, not the surface an installed profile writes.** The
; design says the profile writes `pyproject.toml [tool.mypy]`; the bench keeps
; instrument and subject in separate files for the same reason it writes
; `ruff.toml` rather than `[tool.ruff]`, and because the scaffold's
; `pyproject.toml` belongs to `craft_scaffold.py`.

[mypy]
; TYP-001's requirement, reproduced here because a bench file is not the
; repository's config and mypy has no default strict mode.
strict = True

; Craft's addition, and the row S3's C6 could not measure because the bench
; configured no type checker at all.
disallow_any_explicit = True
""",
    "react/strict.config.js": """\
// Craft `react/strict` — `react/standard` plus the one row the register
// proposes `off` that has an instrument to turn on.
//
// One rule. `docs/craft/design.profiles.md` § What `strict` adds records the
// asymmetry and does not explain it away: Python's strict level adds up to 68
// rules and React's adds this.

import standard from './eslint.config.js'

export default [
  ...standard,
  {
    files: ['src/**/*.{ts,tsx}'],
    rules: {
      // react.effect-dependencies-exhaustive. `react-hooks` ships it off and
      // `react.dev` does not document it, which is `assess.rules.md` finding 1
      // a third time: the rule this stack most needs is the one its own plugin
      // leaves disabled.
      //
      // **The option is not decoration, and `'error'` alone is inert.** The
      // rule is a view onto the compiler's own analysis, and that analysis is
      // gated by `validateExhaustiveEffectDependencies`, which the published
      // bundle defaults to `'off'`. Set to `'error'` and nothing else, the rule
      // resolves, prints at severity 2 under `--print-config`, and cannot
      // report anything — C2's third clause exactly, on the only rule this
      // level has. `docs/craft/review.strict.md` § C2 records the run.
      'react-hooks/exhaustive-effect-dependencies': [
        'error',
        { environment: { validateExhaustiveEffectDependencies: 'all' } },
      ],
    },
  },
]
""",
}


#: What each level materialises. `strict` writes `standard` too, because it is
#: defined as a superset and its files extend the ones below it — a `strict.toml`
#: whose `extend = "ruff.toml"` has no `ruff.toml` beside it is not a level, it
#: is a broken config.
LEVELS: dict[str, dict[str, str]] = {
    "standard": FILES,
    "strict": {**FILES, **STRICT_FILES},
}


def write(target: Path, *, level: str = "standard", force: bool = False) -> int:
    """Write one level's configuration under `target`. Returns the number written."""
    written = 0
    for relative, contents in LEVELS[level].items():
        path = target / relative
        if path.exists() and path.read_text(encoding="utf-8") != contents and not force:
            print(f"refusing to overwrite an edited file: {path}", file=sys.stderr)
            return -1
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")
        written += 1
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        type=Path,
        default=DEFAULT_TARGET,
        help=f"where to write the configuration (default: {DEFAULT_TARGET})",
    )
    parser.add_argument(
        "--level",
        choices=sorted(LEVELS),
        default="standard",
        help="which profile level to materialise (default: standard)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite files that differ from the candidate rather than stopping",
    )
    args = parser.parse_args()

    written = write(args.target, level=args.level, force=args.force)
    if written < 0:
        print("nothing was written. Re-run with --force to discard those edits.", file=sys.stderr)
        return 1
    print(f"wrote {written} files to {args.target} for {args.level}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
