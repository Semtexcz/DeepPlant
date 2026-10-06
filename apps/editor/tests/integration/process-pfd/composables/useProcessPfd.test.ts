import { afterEach, describe, expect, it, vi } from 'vitest'

import { useProcessPfd } from '../../../../src/process-pfd/composables/useProcessPfd'
import {
  EMPTY_WORKSPACE,
  LOADED_WORKSPACE,
  PROJECTION_FIXTURE,
  PUMP_STEP,
} from '../../../fixtures/process-pfd'

/**
 * Feature-integration tests for the Process/PFD workspace state (Issue #97).
 *
 * Only the network is replaced (a stubbed `fetch`); the transport, the runtime
 * contract narrowing, the feature state, the status mapping and selection
 * resolution stay real. These run the composable directly - it owns no DOM and no
 * lifecycle hook - so the workspace transitions the desktop host triggers by
 * reloading the shared SPA are exercised without a browser.
 */

function envelope(workspace: unknown, projection: unknown): Record<string, unknown> {
  const loaded = (workspace as { state?: string }).state === 'loaded'
  return {
    workspace,
    validation: loaded ? { valid: true, message: 'Valid' } : null,
    projection,
  }
}

function jsonResponse(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  })
}

function deferred<T>(): { promise: Promise<T>; resolve: (value: T) => void } {
  let resolve!: (value: T) => void
  const promise = new Promise<T>((resolvePromise) => {
    resolve = resolvePromise
  })
  return { promise, resolve }
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('Process/PFD feature state across workspace changes', () => {
  it('settles an empty workspace into the neutral no-project state', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => jsonResponse(envelope(EMPTY_WORKSPACE, null))),
    )

    const state = useProcessPfd()
    expect(state.loading.value).toBe(true)

    await state.load()

    expect(state.loading.value).toBe(false)
    expect(state.hasProject.value).toBe(false)
    expect(state.canFitView.value).toBe(false)
    expect(state.projection.value).toBeNull()
    expect(state.validation.value).toBeNull()
    expect(state.projectionError.value).toBeNull()
    expect(state.status.value).toEqual({ text: 'No project open', tone: 'neutral' })
  })

  it('moves from no project to a loaded project', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(envelope(EMPTY_WORKSPACE, null)))
      .mockResolvedValueOnce(jsonResponse(envelope(LOADED_WORKSPACE, PROJECTION_FIXTURE)))
    vi.stubGlobal('fetch', fetchMock)

    const state = useProcessPfd()
    await state.load()
    expect(state.hasProject.value).toBe(false)
    expect(state.canFitView.value).toBe(false)

    await state.load()

    expect(state.hasProject.value).toBe(true)
    expect(state.canFitView.value).toBe(true)
    expect(state.projection.value?.steps).toHaveLength(2)
    expect(state.status.value).toEqual({ text: 'Valid', tone: 'valid' })
  })
})

describe('Process/PFD workspace replacement', () => {
  it('replaces a project cleanly and resets the previous selection', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(envelope(LOADED_WORKSPACE, PROJECTION_FIXTURE)))
      .mockResolvedValueOnce(
        jsonResponse(
          envelope(
            {
              state: 'loaded',
              document: { name: 'other.yaml', plant_id: 'other', plant_name: null },
            },
            { ...PROJECTION_FIXTURE, steps: [PUMP_STEP], streams: [] },
          ),
        ),
      )
    vi.stubGlobal('fetch', fetchMock)

    const state = useProcessPfd()
    await state.load()
    state.selectStep('PS-pump')
    expect(state.inspector.value?.title).toBe('PS-pump')

    await state.load()

    expect(state.selection.value).toBeNull()
    expect(state.inspector.value).toBeNull()
    expect(state.projection.value?.steps).toHaveLength(1)
    expect(state.status.value.tone).toBe('valid')
  })

  it('ignores a stale response from a replaced project', async () => {
    const first = deferred<Response>()
    const second = deferred<Response>()
    vi.stubGlobal(
      'fetch',
      vi.fn().mockReturnValueOnce(first.promise).mockReturnValueOnce(second.promise),
    )

    const state = useProcessPfd()
    const firstLoad = state.load()
    const secondLoad = state.load()

    second.resolve(jsonResponse(envelope(LOADED_WORKSPACE, PROJECTION_FIXTURE)))
    await secondLoad
    expect(state.projection.value?.steps).toHaveLength(2)

    // The slow first response arrives late; it must not overwrite the newer one.
    first.resolve(jsonResponse(envelope(EMPTY_WORKSPACE, null)))
    await firstLoad

    expect(state.hasProject.value).toBe(true)
    expect(state.projection.value?.steps).toHaveLength(2)
    expect(state.status.value.tone).toBe('valid')
  })

  it('surfaces a transport error instead of claiming an empty workspace', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        throw new Error('connection refused')
      }),
    )

    const state = useProcessPfd()
    await state.load()

    expect(state.projectionError.value).toContain(
      'cannot reach the local DeepPlant editor boundary',
    )
    expect(state.hasProject.value).toBe(false)
    expect(state.status.value.tone).toBe('invalid')
    expect(state.status.value.text).toContain('cannot reach')
  })
})