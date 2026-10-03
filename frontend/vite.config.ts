import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vitest/config'

// The editor is served locally by the Python application boundary
// (`deepplant ui`), which reads the production build from `frontend/dist`.
// During development `vite` proxies the DeepPlant routes to that same boundary,
// so the browser never parses YAML or re-implements the semantic model, the
// projection, or the symbol-role policy.
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8765',
    },
  },
  test: {
    environment: 'node',
    include: ['src/**/*.test.ts'],
  },
})
