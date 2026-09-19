// >>> ee-craft react/strict@2
// ee-craft: react/strict@2  gates: none (no any. property binds an instrument)  craft-contract: 2
// Written by craft-install from the Craft register. Re-run it rather
// than editing here: a hand edit is what the next run reports.

import eslintReact from '@eslint-react/eslint-plugin'
import globals from 'globals'
import jsxA11y from 'eslint-plugin-jsx-a11y'
import react from 'eslint-plugin-react'
import reactHooks from 'eslint-plugin-react-hooks'
import testingLibrary from 'eslint-plugin-testing-library'
import typescriptEslint from 'typescript-eslint'

const SOURCE = ['src/**/*.ts', 'src/**/*.tsx']
const MODULES = ['src/**/*.ts']
const TESTS = ['**/*.test.ts', '**/*.test.tsx', '**/*.spec.ts', '**/*.spec.tsx', '**/__tests__/**']

export default [
  { ignores: ['node_modules/**', 'dist/**', 'coverage/**'] },

  // The parser, and the project service the type-checked rules need. No preset
  // rules are attached here: what is enabled is enabled by name below, or by a
  // base the register names in `bases:`.
  {
    ...typescriptEslint.configs.base,
    files: SOURCE,
    languageOptions: {
      ...typescriptEslint.configs.base.languageOptions,
      parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname },
      globals: { ...globals.browser },
    },
  },

  { ...eslintReact.configs.recommended, files: SOURCE },
  { ...jsxA11y.flatConfigs.recommended, files: SOURCE },

  {
    files: SOURCE,
    plugins: { react, 'react-hooks': reactHooks },
    rules: {
      // react.a11y-aria-validity
      'jsx-a11y/aria-props': 'error',
      'jsx-a11y/aria-proptypes': 'error',
      'jsx-a11y/aria-role': 'error',
      'jsx-a11y/aria-unsupported-elements': 'error',
      'jsx-a11y/role-has-required-aria-props': 'error',
      'jsx-a11y/role-supports-aria-props': 'error',
      // react.a11y-document-language
      'jsx-a11y/html-has-lang': 'error',
      'jsx-a11y/lang': 'error',
      // react.a11y-focus-order
      'jsx-a11y/tabindex-no-positive': 'error',
      'jsx-a11y/no-noninteractive-tabindex': 'error',
      'jsx-a11y/aria-activedescendant-has-tabindex': 'error',
      // react.a11y-form-labels
      'jsx-a11y/label-has-associated-control': 'error',
      'jsx-a11y/control-has-associated-label': 'error',
      // react.a11y-keyboard-parity
      'jsx-a11y/click-events-have-key-events': 'error',
      'jsx-a11y/mouse-events-have-key-events': 'error',
      'jsx-a11y/interactive-supports-focus': 'error',
      'jsx-a11y/no-static-element-interactions': 'error',
      // react.a11y-link-has-content
      'jsx-a11y/anchor-has-content': 'error',
      'jsx-a11y/anchor-is-valid': 'error',
      // react.a11y-media-captions
      'jsx-a11y/media-has-caption': 'error',
      // react.a11y-no-unexpected-focus
      'jsx-a11y/no-autofocus': 'error',
      'jsx-a11y/no-distracting-elements': 'error',
      // react.a11y-semantic-elements
      'jsx-a11y/no-redundant-roles': 'error',
      'jsx-a11y/no-interactive-element-to-noninteractive-role': 'error',
      'jsx-a11y/no-noninteractive-element-to-interactive-role': 'error',
      'jsx-a11y/prefer-tag-over-role': 'error',
      // react.a11y-text-alternatives
      'jsx-a11y/alt-text': 'error',
      'jsx-a11y/img-redundant-alt': 'error',
      'jsx-a11y/iframe-has-title': 'error',
      // react.components-are-idempotent
      '@eslint-react/purity': 'off',
      // react.components-are-idempotent, react.no-side-effects-in-render
      'react-hooks/purity': 'error',
      // react.context-value-stability
      '@eslint-react/no-unstable-context-value': 'error',
      // react.effect-dependencies-complete
      '@eslint-react/exhaustive-deps': 'off',
      'react-hooks/exhaustive-deps': 'error',
      // react.effect-dependencies-exhaustive
      'react-hooks/exhaustive-effect-dependencies': ['error', { environment: { validateExhaustiveEffectDependencies: 'all' } }],
      // react.hook-values-immutable, react.jsx-values-immutable, react.props-and-state-immutable
      'react-hooks/immutability': 'error',
      // react.hooks-at-top-level
      '@eslint-react/rules-of-hooks': 'off',
      // react.hooks-at-top-level, react.hooks-only-from-react-functions
      'react-hooks/rules-of-hooks': 'error',
      // react.list-keys
      '@eslint-react/no-missing-key': 'error',
      '@eslint-react/no-duplicate-key': 'error',
      '@eslint-react/jsx-no-key-after-spread': 'error',
      // react.memoization-preserved
      '@eslint-react/use-memo': 'off',
      'react-hooks/preserve-manual-memoization': 'error',
      'react-hooks/use-memo': 'error',
      // react.no-array-index-key
      '@eslint-react/no-array-index-key': 'error',
      // react.no-class-components
      '@eslint-react/no-class-component': 'error',
      // react.no-comment-textnodes
      '@eslint-react/jsx-no-comment-textnodes': 'error',
      // react.no-dangerous-html
      '@eslint-react/dom-no-dangerously-set-innerhtml': 'error',
      // react.no-deprecated-api
      '@eslint-react/no-component-will-mount': 'error',
      '@eslint-react/no-component-will-receive-props': 'error',
      '@eslint-react/no-component-will-update': 'error',
      '@eslint-react/no-create-ref': 'error',
      '@eslint-react/no-forward-ref': 'error',
      '@eslint-react/no-use-context': 'error',
      // react.no-derived-state-in-effect
      'react-hooks/no-deriving-state-in-effects': 'error',
      // react.no-duplicate-props
      'react/jsx-no-duplicate-props': 'error',
      // react.no-explicit-any
      '@typescript-eslint/no-explicit-any': 'error',
      // react.no-floating-promises
      '@typescript-eslint/no-floating-promises': 'error',
      // react.no-leaked-conditional-render
      '@eslint-react/no-leaked-conditional-rendering': 'error',
      // react.no-leaked-subscriptions
      '@eslint-react/web-api-no-leaked-event-listener': 'error',
      '@eslint-react/web-api-no-leaked-fetch': 'error',
      '@eslint-react/web-api-no-leaked-intersection-observer': 'error',
      '@eslint-react/web-api-no-leaked-interval': 'error',
      '@eslint-react/web-api-no-leaked-resize-observer': 'error',
      '@eslint-react/web-api-no-leaked-timeout': 'error',
      // react.no-misused-promises
      '@typescript-eslint/no-misused-promises': 'error',
      // react.no-nested-component-definitions
      '@eslint-react/no-nested-component-definitions': 'off',
      '@eslint-react/static-components': 'off',
      'react-hooks/static-components': 'error',
      // react.no-non-null-assertion
      '@typescript-eslint/no-non-null-assertion': 'error',
      // react.no-set-state-in-effect
      '@eslint-react/set-state-in-effect': 'off',
      'react-hooks/set-state-in-effect': 'error',
      // react.no-set-state-in-render
      '@eslint-react/set-state-in-render': 'off',
      'react-hooks/set-state-in-render': 'error',
      // react.no-side-effects-in-render
      'react-hooks/globals': 'error',
      // react.no-unknown-dom-property
      '@eslint-react/dom-no-unknown-property': 'error',
      // react.no-unsafe-any-flow
      '@typescript-eslint/no-unsafe-argument': 'error',
      '@typescript-eslint/no-unsafe-assignment': 'error',
      '@typescript-eslint/no-unsafe-call': 'error',
      '@typescript-eslint/no-unsafe-member-access': 'error',
      '@typescript-eslint/no-unsafe-return': 'error',
      // react.props-and-state-immutable
      '@eslint-react/no-direct-mutation-state': 'error',
      // react.refs-not-read-in-render
      'react-hooks/refs': 'error',
      // react.safe-external-links
      '@eslint-react/dom-no-unsafe-target-blank': 'error',
      // react.throw-error-objects
      '@typescript-eslint/only-throw-error': 'error',
    },
  },
  {
    files: MODULES,
    rules: {
      // react.explicit-return-types
      '@typescript-eslint/explicit-module-boundary-types': ['error', { allowTypedFunctionExpressions: true }],
    },
  },
  {
    files: TESTS,
    plugins: { 'testing-library': testingLibrary },
    rules: {
      // react.test-async-awaited
      'testing-library/await-async-queries': 'error',
      'testing-library/await-async-events': 'error',
      'testing-library/await-async-utils': 'error',
      'testing-library/no-await-sync-queries': 'error',
      // react.test-find-over-wait
      'testing-library/prefer-find-by': 'error',
      // react.test-no-debug-residue
      'testing-library/no-debugging-utils': 'error',
      // react.test-no-implementation-access
      'testing-library/no-container': 'error',
      'testing-library/no-node-access': 'error',
      // react.test-user-visible-queries
      'testing-library/prefer-screen-queries': 'error',
      'testing-library/prefer-presence-queries': 'error',
      'testing-library/prefer-query-by-disappearance': 'error',
    },
  },
]
// <<< ee-craft
