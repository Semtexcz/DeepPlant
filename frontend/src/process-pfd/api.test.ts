import { describe, expect, it } from 'vitest'

import { parseProjectionEnvelope, ProjectionContractError, symbolUrl } from './api'
import { PROJECTION_FIXTURE, PUMP_STEP } from './test-fixtures'

function plain(value: unknown): unknown {
  return JSON.parse(JSON.stringify(value)) as unknown
}

describe('DeepPlant boundary payload parsing', () => {
  it('accepts the projection envelope produced by the Python boundary', () => {
    const envelope = parseProjectionEnvelope(
      plain({ validation: { valid: true, message: 'Valid' }, projection: PROJECTION_FIXTURE }),
    )

    expect(envelope.validation).toEqual({ valid: true, message: 'Valid' })
    expect(envelope.error).toBeNull()
    expect(envelope.projection?.steps).toHaveLength(2)
    expect(envelope.projection?.steps[0]?.id).toBe('PS-pump')
    expect(envelope.projection?.streams[0]?.id).toBe('S-004')
  })

  it('accepts an honest failure payload with no projection', () => {
    const envelope = parseProjectionEnvelope({
      validation: { valid: false, message: 'no process model to project' },
      error: 'no process model to project',
    })

    expect(envelope.projection).toBeNull()
    expect(envelope.validation.valid).toBe(false)
    expect(envelope.error).toBe('no process model to project')
  })

  it('fails clearly when the payload is not an object', () => {
    expect(() => parseProjectionEnvelope([1, 2, 3])).toThrow(ProjectionContractError)
  })

  it('fails clearly when a required field has the wrong type', () => {
    expect(() => parseProjectionEnvelope({ validation: { valid: 'yes', message: 'x' } })).toThrow(
      /validation\.valid must be a boolean/,
    )
  })

  it('fails clearly when a projected object has an unexpected kind', () => {
    const payload = plain({
      validation: { valid: true, message: 'Valid' },
      projection: {
        ...PROJECTION_FIXTURE,
        steps: [{ ...PUMP_STEP, kind: 'equipment' }],
      },
    })

    expect(() => parseProjectionEnvelope(payload)).toThrow(/must be 'process-step'/)
  })

  it('fails clearly when a projected step is missing an anchor array', () => {
    const brokenStep: Record<string, unknown> = { ...PUMP_STEP }
    delete brokenStep['in_anchors']
    const payload = plain({
      validation: { valid: true, message: 'Valid' },
      projection: { ...PROJECTION_FIXTURE, steps: [brokenStep] },
    })

    expect(() => parseProjectionEnvelope(payload)).toThrow(/in_anchors must be an array/)
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
