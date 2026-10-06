import { afterEach, describe, expect, it, vi } from 'vitest'

import { fetchProjection, PROJECTION_ROUTE, symbolUrl } from '../../../../src/process-pfd/transport/api'
import { ProjectionContractError } from '../../../../src/process-pfd/transport/projection-contract'
import {
  EMPTY_WORKSPACE,
  LOADED_WORKSPACE,
  PROJECTION_FIXTURE,
} from '../../../fixtures/process-pfd'

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('DeepPlant boundary transport', () => {
  it('requests the projection route from the local boundary', async () => {
    const fetchMock = vi.fn(async () =>
      jsonResponse({
        workspace: LOADED_WORKSPACE,
        validation: { valid: true, message: 'Valid' },
        projection: PROJECTION_FIXTURE,
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    const envelope = await fetchProjection()

    expect(fetchMock).toHaveBeenCalledWith(PROJECTION_ROUTE, {
      headers: { Accept: 'application/json' },
    })
    expect(envelope.workspace.state).toBe('loaded')
    expect(envelope.projection?.steps).toHaveLength(2)
    expect(envelope.projection?.streams).toHaveLength(2)
    expect(envelope.error).toBeNull()
  })

  it('reports an empty workspace without fabricating a model', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        jsonResponse({ workspace: EMPTY_WORKSPACE, validation: null, projection: null }),
      ),
    )

    const envelope = await fetchProjection()

    expect(envelope.workspace).toEqual({ state: 'empty', document: null })
    expect(envelope.validation).toBeNull()
    expect(envelope.projection).toBeNull()
    expect(envelope.error).toBeNull()
  })

  it('keeps a projection failure separate from semantic validation', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        jsonResponse(
          {
            workspace: LOADED_WORKSPACE,
            validation: { valid: true, message: 'Valid' },
            projection: null,
            error: 'no process model to project',
          },
          422,
        ),
      ),
    )

    const envelope = await fetchProjection()

    expect(envelope.projection).toBeNull()
    expect(envelope.validation).toEqual({ valid: true, message: 'Valid' })
    expect(envelope.error).toBe('no process model to project')
  })
})

describe('DeepPlant boundary failures', () => {
  it('reports an unreachable boundary clearly', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        throw new Error('connection refused')
      }),
    )

    await expect(fetchProjection()).rejects.toThrow(
      /cannot reach the local DeepPlant editor boundary: connection refused/,
    )
  })

  it('reports a non-JSON boundary response clearly', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response('<html>nope</html>', { status: 502 })),
    )

    await expect(fetchProjection()).rejects.toThrow(/returned non-JSON \(HTTP 502\)/)
  })

  it('narrows the boundary payload through the runtime contract', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        jsonResponse({
          workspace: LOADED_WORKSPACE,
          validation: { valid: true, message: 'Valid' },
          projection: { ...PROJECTION_FIXTURE, symbol_size: 'big' },
        }),
      ),
    )

    await expect(fetchProjection()).rejects.toThrow(ProjectionContractError)
  })
})

describe('canonical symbol asset URL', () => {
  it('points at the DeepPlant boundary symbol route', () => {
    expect(symbolUrl('pump')).toBe('/api/symbols/pump.svg')
  })

  it('escapes a role so it cannot form a path', () => {
    expect(symbolUrl('../pump')).toBe('/api/symbols/..%2Fpump.svg')
  })
})
