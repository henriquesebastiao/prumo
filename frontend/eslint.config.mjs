import { globalIgnores } from 'eslint/config'
import { defineConfigWithVueTs, vueTsConfigs } from '@vue/eslint-config-typescript'
import pluginVue from 'eslint-plugin-vue'
import skipFormatting from '@vue/eslint-config-prettier/skip-formatting'

export default defineConfigWithVueTs(
  { name: 'app/files-to-lint', files: ['**/*.{ts,mts,vue}'] },
  globalIgnores([
    '**/dist/**',
    'src/lib/api/schema.d.ts',
    'playwright-report/**',
    'test-results/**',
    'e2e/output/**',
  ]),
  pluginVue.configs['flat/recommended'],
  vueTsConfigs.recommended,
  {
    name: 'app/rules',
    rules: {
      // Every visible text comes from i18n.
      'vue/no-bare-strings-in-template': [
        'error',
        { allowlist: ['·', '—', '–', '−', '+', '-', '/', ':', '%', '×', '›', '‹', '(', ')', '…'] },
      ],
      'vue/multi-word-component-names': 'off',
      'vue/component-api-style': ['error', ['script-setup']],
      'vue/block-lang': ['error', { script: { lang: 'ts' } }],
      '@typescript-eslint/consistent-type-imports': 'error',
    },
  },
  {
    // Icons only through <PIcon>, primitives only through src/ui.
    name: 'app/ui-boundary',
    files: ['src/**/*.{ts,vue}'],
    ignores: ['src/ui/**'],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          patterns: [
            { group: ['@lucide/*'], message: 'Use <PIcon> from @/ui.' },
            { group: ['reka-ui', 'reka-ui/*'], message: 'Use the P* components from @/ui.' },
          ],
        },
      ],
    },
  },
  {
    // Tests and the /dev/ui showcase (development only, never shipped) may use literal text.
    name: 'app/tests-and-showcase',
    files: ['src/**/*.test.ts', 'e2e/**/*.ts', 'src/system/dev-ui/**'],
    rules: { 'vue/no-bare-strings-in-template': 'off' },
  },
  skipFormatting,
)
