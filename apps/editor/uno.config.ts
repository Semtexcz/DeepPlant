import { defineConfig, presetWind3 } from 'unocss'

/**
 * Canonical UnoCSS configuration for the DeepPlant Engineering Editor.
 *
 * UnoCSS owns ordinary application presentation (layout, spacing, typography,
 * borders, backgrounds, interaction states). It is deliberately one preset with
 * no additions:
 *
 * - no reset preset: genuinely global base rules live in `src/styles.css`,
 * - no transformer/directive layer: component-specific CSS stays scoped CSS,
 * - no second utility framework.
 *
 * DeepPlant colour meaning is expressed with semantic CSS custom properties
 * (see `src/styles.css`); utilities reference them with bracket values such as
 * `bg-[var(--dp-surface)]` instead of hard-coded colours.
 */
export default defineConfig({
  presets: [presetWind3()],
})
