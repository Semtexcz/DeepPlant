import UnoCSS from '@unocss/vite'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vitest/config'

// The editor is served locally by the Python application boundary
// (`deepplant ui`), which reads the production build from `apps/editor/dist`.
// During development `vite` proxies the DeepPlant routes to that same boundary,
// so the browser never parses YAML or re-implements the semantic model, the
// projection, or the symbol-role policy.
//
// `UnoCSS()` loads `uno.config.ts` and generates the canonical utility layer
// imported by `src/main.ts` as `virtual:uno.css`.
export default defineConfig({
  plugins: [vue(), UnoCSS()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8765',
    },
  },
  test: {
    // Default environment stays `node` so the pure suites keep running without
    // a DOM. Component and feature-integration tests opt into the DOM with a
    // `@vitest-environment happy-dom` docblock (see docs/dev/frontend/testing.md).
    environment: 'node',
    include: ['src/**/*.test.ts'],
  },
})
