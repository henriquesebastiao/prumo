/**
 * Appearance lives in tokens. Outside src/design/ no literal color, font, shadow or radius is
 * allowed: use the semantic custom properties (var(--color-*), var(--radius-*), …).
 */
const KEYWORDS = [
  'transparent',
  'currentcolor',
  'currentColor',
  'inherit',
  'initial',
  'unset',
  'revert',
  'none',
  '0',
  '50%',
  '100%',
  '/^[\\d.]+em$/',
]

export default {
  extends: ['stylelint-config-standard', 'stylelint-config-recommended-vue'],
  plugins: ['stylelint-declaration-strict-value'],
  rules: {
    'color-no-hex': true,
    'color-named': 'never',
    'function-disallowed-list': [
      'rgb',
      'rgba',
      'hsl',
      'hsla',
      'hwb',
      'lab',
      'lch',
      'oklab',
      'oklch',
    ],
    'scale-unlimited/declaration-strict-value': [
      [
        '/color$/',
        'fill',
        'stroke',
        'box-shadow',
        'font-family',
        'font-size',
        'font-weight',
        '/radius$/',
      ],
      { ignoreValues: KEYWORDS, expandShorthand: true, disableFix: true },
    ],
    'selector-class-pattern': null,
    'custom-property-pattern': null,
    'keyframes-name-pattern': null,
    'value-keyword-case': ['lower', { camelCaseSvgKeywords: true }],
  },
  overrides: [
    {
      files: ['src/design/**/*.css'],
      rules: {
        'color-no-hex': null,
        'function-disallowed-list': null,
        'scale-unlimited/declaration-strict-value': null,
      },
    },
  ],
}
