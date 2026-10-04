import { expect, test, type Locator, type Page, type TestInfo } from '@playwright/test'

import { startEditorServer, VESSEL_ROLE_OVERRIDE } from './support/editor-server'

/**
 * Browser E2E for the Engineering Editor critical workflow (Issue #82).
 *
 * These two tests are the only system/browser tests in the repository. They run
 * against the real product path a user receives today:
 *
 *     production SPA build (`apps/editor/dist`)
 *         -> real `deepplant ui --port 0` CLI
 *         -> FastAPI/Uvicorn on loopback
 *         -> real Chromium browser
 *         -> Vue -> Vue Flow -> real pointer interaction
 *
 * Nothing is mocked: no Vite dev/preview server, no `page.route()`, no injected
 * DTO, no stub of the Python projection. What the browser proves is what the
 * user gets.
 *
 * Scope is deliberately two critical workflows, not one test per behaviour:
 * component/integration behaviour is owned by the Vitest suites under
 * `apps/editor/tests/`.
 */

const PROCESS_STEP_GROUPS = /^Process step /
const PROCESS_STREAM_GROUPS = /^Process stream /
const NUM_PROCESS_STEPS = 7
const NUM_PROCESS_STREAMS = 7

/** The projected `ProcessStep` rendered inside the real Vue Flow graph. */
function processStepElement(page: Page, stepId: string): Locator {
  // Vue Flow renders a focusable node with an accessible name supplied by the
  // DeepPlant adapter, so the selector is a role + accessible name and never a
  // framework id or a generated class.
  return page.getByRole('group', { name: `Process step ${stepId}` })
}

/** The Inspector landmark (read-only semantic field list). */
function inspector(page: Page): Locator {
  return page.getByRole('complementary', { name: 'Inspector' })
}

/** Read the Inspector definition list as label -> value pairs. */
async function inspectorFields(inspectorPanel: Locator): Promise<Record<string, string>> {
  const terms = await inspectorPanel.getByRole('term').allTextContents()
  const definitions = await inspectorPanel.getByRole('definition').allTextContents()
  const fields: Record<string, string> = {}
  terms.forEach((term, index) => {
    fields[term.trim()] = (definitions[index] ?? '').trim()
  })
  return fields
}

/**
 * Select a projected `ProcessStream` through the real rendered Vue Flow edge.
 *
 * Vue Flow renders each edge as a focusable `group` whose accessible name is the
 * DeepPlant semantic identity (again supplied by the adapter), so the selector is
 * semantic. `force: true` bypasses only Playwright's CSS-box visibility gate: a
 * perfectly straight SVG edge path has an in-page `getBoundingClientRect()`
 * height of 0, so Playwright's `visible` heuristic (`width > 0 && height > 0`)
 * rejects a stroke that is genuinely hit-testable. The click itself is still a
 * real browser click dispatched at the framework element's own centre, and the
 * Inspector assertion in the test proves the click actually reached the edge.
 */
async function selectProcessStream(page: Page, streamId: string): Promise<void> {
  await page.getByRole('group', { name: `Process stream ${streamId}` }).click({ force: true })
}

/**
 * Collect browser problems; fail the test if the real application logged an
 * uncaught error or an unexpected console error.
 *
 * `allowedConsoleErrors` exists for legitimate, documented console noise. The
 * valid-but-unprojectable path deliberately receives HTTP 422 from
 * `/api/projection` (the boundary's signal for "semantically valid but not
 * projectable"), and the browser logs that non-2xx response as a resource-load
 * `console.error`. That one message is expected there and is allowed
 * explicitly; any other console error or page error still fails.
 */
function watchBrowserDiagnostics(page: Page, allowedConsoleErrors: readonly string[] = []): string[] {
  const problems: string[] = []
  page.on('pageerror', (error) => problems.push(`pageerror: ${error.message}`))
  page.on('console', (message) => {
    const expected = allowedConsoleErrors.some((allowed) => message.text().includes(allowed))
    if (message.type() === 'error' && !expected) {
      problems.push(`console.error: ${message.text()}`)
    }
  })
  return problems
}

/**
 * Run one scenario against a freshly started real editor, guaranteeing that the
 * CLI process tree is stopped even when the scenario fails or times out, and
 * attaching the captured server log for failed tests only.
 */
async function withRealEditor(
  testInfo: TestInfo,
  symbolRoles: readonly string[],
  scenario: (baseUrl: string) => Promise<void>,
): Promise<void> {
  const server = await startEditorServer({ symbolRoles })
  try {
    await scenario(server.baseUrl)
  } catch (error) {
    await testInfo.attach('deepplant-ui-server-log', {
      body: server.logs(),
      contentType: 'text/plain',
    })
    throw error
  } finally {
    await server.stop()
  }
}

test('renders the realistic process fragment and selects a step and a stream', async ({
  page,
}, testInfo) => {
  const browserProblems = watchBrowserDiagnostics(page)

  await withRealEditor(testInfo, VESSEL_ROLE_OVERRIDE, async (baseUrl) => {
    await page.goto(baseUrl)

    // Guard against accidentally exercising a Vite dev server: the served
    // document must reference the built bundle, never the dev entry module.
    expect(await page.content()).not.toContain('/src/main.ts')

    // The DeepPlant shell and the Process/PFD view are visible.
    await expect(page.getByRole('banner')).toContainText('Process / PFD')
    await expect(page.getByRole('button', { name: 'Fit view' })).toBeVisible()
    await expect(page.getByRole('region', { name: 'Process PFD canvas' })).toBeVisible()

    // Semantic validation is Valid and the real projection is rendered: these
    // counts come from the browser graph, not from an API response.
    await expect(page.getByRole('status')).toHaveText('Valid')
    await expect(page.getByRole('group', { name: PROCESS_STEP_GROUPS })).toHaveCount(
      NUM_PROCESS_STEPS,
    )
    await expect(page.getByRole('group', { name: PROCESS_STREAM_GROUPS })).toHaveCount(
      NUM_PROCESS_STREAMS,
    )

    // Exercise the real viewport action; the application must stay usable.
    await page.getByRole('button', { name: 'Fit view' }).click()

    // Select a real ProcessStep through the rendered graph.
    await processStepElement(page, 'PS-pump').click()
    await expect(inspector(page).getByRole('heading', { level: 2 })).toHaveText('PS-pump')
    expect(await inspectorFields(inspector(page))).toMatchObject({
      ID: 'PS-pump',
      Name: 'Feed Pumping',
      Function: 'pumping',
      Ports: 'suction, discharge',
    })

    // Select a real ProcessStream through the rendered Vue Flow edge.
    await selectProcessStream(page, 'S-004')
    await expect(inspector(page).getByRole('heading', { level: 2 })).toHaveText('S-004')
    expect(await inspectorFields(inspector(page))).toMatchObject({
      ID: 'S-004',
      'Source step': 'PS-pump',
      'Source port': 'discharge',
      'Target step': 'PS-hx',
      'Target port': 'in_side_A',
    })
  })

  expect(browserProblems.join('\n')).toBe('')
})

test('keeps a valid model with an unprojectable presentation separate from invalidity', async ({
  page,
}, testInfo) => {
  // The boundary answers `/api/projection` with HTTP 422 on this path, which the
  // browser logs as a resource-load console error; that specific message is the
  // expected, documented noise here.
  const browserProblems = watchBrowserDiagnostics(page, [
    'Failed to load resource: the server responded with a status of 422',
  ])

  // The same real project and the same real YAML, deliberately without the
  // `PS-vessel=vessel` presentation override the happy path needs. The semantic
  // model stays valid; only the Process/PFD presentation role is unresolvable.
  await withRealEditor(testInfo, [], async (baseUrl) => {
    await page.goto(baseUrl)

    // Semantic validation is still Valid, and no projection is rendered.
    await expect(page.getByRole('status')).toHaveText('Valid')
    await expect(page.getByRole('group', { name: PROCESS_STEP_GROUPS })).toHaveCount(0)

    // The projection failure is surfaced as its own visible alert, tied to the
    // real step whose presentation role cannot be resolved.
    const alert = page.getByRole('alert')
    await expect(alert).toBeVisible()
    await expect(alert).toContainText('PS-vessel')
  })

  expect(browserProblems.join('\n')).toBe('')
})
