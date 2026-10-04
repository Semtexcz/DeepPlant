import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright configuration for the Engineering Editor browser E2E suite.
 *
 * These are the system/browser tests: real Python CLI, real HTTP, the real
 * production SPA build, and a real Chromium browser. They deliberately live
 * outside the Vitest tree (`tests/`) because they own a whole-process lifecycle
 * that unit/component/integration tests must not have.
 *
 * There is no Playwright `webServer` block: the editor is started by the actual
 * `deepplant ui --port 0` CLI, whose dynamic loopback URL is awaited by
 * `e2e/support/editor-server.ts`. A `webServer` entry could not express that
 * lifecycle without forcing a fixed port.
 *
 * One browser only (Chromium). This suite is system evidence, not a browser
 * compatibility matrix, and there is no visual-regression or golden-image scope.
 */
export default defineConfig({
  testDir: './e2e',
  testMatch: '**/*.spec.ts',
  // The suite starts and stops a real server per test, so it stays serial and
  // deterministic rather than parallelising across workers.
  fullyParallel: false,
  workers: 1,
  forbidOnly: !!process.env['CI'],
  retries: 0,
  timeout: 60_000,
  expect: { timeout: 10_000 },
  // `list` locally and `github` annotations in CI, plus an HTML report so a
  // failing run leaves a browsable report that CI uploads as an artifact.
  reporter: [[process.env['CI'] ? 'github' : 'list'], ['html', { open: 'never' }]],
  use: {
    ...devices['Desktop Chrome'],
    // Diagnose failures with a trace and a screenshot; keep successful runs free
    // of large artifacts and never record video.
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'off',
  },
  projects: [{ name: 'chromium', use: { browserName: 'chromium' } }],
})
