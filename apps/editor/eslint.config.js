// @ts-check
import js from '@eslint/js'
import pluginVue from 'eslint-plugin-vue'
import globals from 'globals'
import tseslint from 'typescript-eslint'

/**
 * Canonical frontend lint gate for the DeepPlant Engineering Editor.
 *
 * This gate covers the real editor source (`src/**`, `env.d.ts`) and the
 * frontend configuration files. It deliberately uses maintained ecosystem
 * tooling (ESLint flat config, `typescript-eslint`, `eslint-plugin-vue`) and
 * high-signal correctness rules only - not a large stylistic rule collection -
 * so lint does not become a second formatter or a style war.
 *
 * It is one of four independent frontend gates:
 *
 *   lint + typecheck (vue-tsc) + tests (vitest) + production build (vite)
 *
 * No gate replaces another. `vue-tsc` still owns type checking.
 *
 * Hard size limits are enforced here with the standard `max-lines` and
 * `max-lines-per-function` rules over *logical* lines (blank lines and comments
 * are not cohesion), matching the size/cohesion policy in
 * `docs/dev/frontend/architecture.md`. Soft limits are review signals only and
 * are deliberately not automated. Limit changes belong in this file, not in
 * per-file suppressions.
 */

// Logical lines: blank lines and comments do not express cohesion.
const LOGICAL_LINES = { skipBlankLines: true, skipComments: true }

const HARD_LIMITS = {
  typescriptModule: 500,
  vueSfc: 600,
  composable: 250,
  function: 80,
  testModule: 800,
}

export default tseslint.config(
  {
    ignores: ['dist/**', 'node_modules/**', 'coverage/**', '.vite/**', '*.local'],
  },
  {
    // A stale eslint-disable is a correctness defect, not a warning.
    linterOptions: { reportUnusedDisableDirectives: 'error' },
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  // Vue 3 correctness rules (`flat/essential`): parser setup plus rules that
  // prevent errors and unintended behavior. Subjective formatting rules are
  // intentionally not enabled.
  ...pluginVue.configs['flat/essential'],
  {
    files: ['**/*.vue'],
    languageOptions: {
      // TypeScript inside `<script setup lang="ts">`: Vue owns the SFC parse and
      // typescript-eslint parses the script block.
      parserOptions: { parser: tseslint.parser },
    },
  },
  {
    files: ['**/*.{ts,vue}'],
    languageOptions: { globals: { ...globals.browser } },
    rules: {
      '@typescript-eslint/no-explicit-any': 'error',
      'max-lines': ['error', { max: HARD_LIMITS.typescriptModule, ...LOGICAL_LINES }],
      'max-lines-per-function': ['error', { max: HARD_LIMITS.function, ...LOGICAL_LINES }],
    },
  },
  {
    files: ['**/*.vue'],
    rules: {
      'max-lines': ['error', { max: HARD_LIMITS.vueSfc, ...LOGICAL_LINES }],
    },
  },
  {
    files: ['**/*.test.ts'],
    rules: {
      'max-lines': ['error', { max: HARD_LIMITS.testModule, ...LOGICAL_LINES }],
    },
  },
  {
    // A composable is a narrower unit than a general module.
    files: ['src/**/use*.ts', 'src/**/composables/**/*.ts'],
    rules: {
      'max-lines': ['error', { max: HARD_LIMITS.composable, ...LOGICAL_LINES }],
    },
  },
  {
    files: ['eslint.config.js', 'vite.config.ts'],
    languageOptions: { globals: { ...globals.node } },
  },
)
