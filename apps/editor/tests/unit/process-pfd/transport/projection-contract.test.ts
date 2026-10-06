import { describe, expect, it } from 'vitest'

import {
  parseProjectionEnvelope,
  ProjectionContractError,
} from '../../../../src/process-pfd/transport/projection-contract'
import {
  EMPTY_WORKSPACE,
  LOADED_WORKSPACE,
  PROJECTION_FIXTURE,
  PUMP_STEP,
} from '../../../fixtures/process-pfd'

function plain(value: unknown): unknown {
  return JSON.parse(JSON.stringify(value)) as unknown
}

describe('DeepPlant projection contract narrowing', () => {
  it('accepts the projection envelope produced by the Python boundary', () => {
    const envelope = parseProjectionEnvelope(
      plain({
        workspace: LOADED_WORKSPACE,
        validation: { valid: true, message: 'Valid' },
        projection: PROJECTION_FIXTURE,
      }),
    )

    expect(envelope.workspace.state).toBe('loaded')
    expect(envelope.workspace.document?.name).toBe('plant.yaml')
    expect(envelope.validation).toEqual({ valid: true, message: 'Valid' })
    expect(envelope.error).toBeNull()
    expect(envelope.projection?.steps).toHaveLength(2)
    expect(envelope.projection?.steps[0]?.id).toBe('PS-pump')
    expect(envelope.projection?.streams[0]?.id).toBe('S-004')
  })

  it('accepts an empty workspace as an ordinary state with no model', () => {
    const envelope = parseProjectionEnvelope(
      plain({ workspace: EMPTY_WORKSPACE, validation: null, projection: null }),
    )

    expect(envelope.workspace).toEqual({ state: 'empty', document: null })
    expect(envelope.validation).toBeNull()
    expect(envelope.projection).toBeNull()
    expect(envelope.error).toBeNull()
  })

  it('accepts a loaded project whose current view cannot be produced', () => {
    const envelope = parseProjectionEnvelope({
      workspace: LOADED_WORKSPACE,
      validation: { valid: true, message: 'Valid' },
      projection: null,
      error: 'no process model to project',
    })

    expect(envelope.workspace.state).toBe('loaded')
    expect(envelope.projection).toBeNull()
    expect(envelope.validation).toEqual({ valid: true, message: 'Valid' })
    expect(envelope.error).toBe('no process model to project')
  })
})

describe('workspace state narrowing', () => {
  it('rejects an unknown workspace state', () => {
    expect(() =>
      parseProjectionEnvelope({ workspace: { state: 'broken', document: null } }),
    ).toThrow(/workspace\.state must be 'empty' or 'loaded'/)
  })

  it('rejects an empty workspace that carries a document', () => {
    expect(() =>
      parseProjectionEnvelope({
        workspace: { state: 'empty', document: LOADED_WORKSPACE.document },
      }),
    ).toThrow(/workspace\.document must be null/)
  })

  it('rejects a loaded workspace with no document identity', () => {
    expect(() =>
      parseProjectionEnvelope({ workspace: { state: 'loaded', document: null } }),
    ).toThrow(/workspace\.document must be present/)
  })
})

describe('projection payload narrowing', () => {
  it('fails clearly when the payload is not an object', () => {
    expect(() => parseProjectionEnvelope([1, 2, 3])).toThrow(ProjectionContractError)
  })

  it('fails clearly when a required field has the wrong type', () => {
    expect(() =>
      parseProjectionEnvelope({
        workspace: LOADED_WORKSPACE,
        validation: { valid: 'yes', message: 'x' },
      }),
    ).toThrow(/validation\.valid must be a boolean/)
  })

  it('fails clearly when a projected object has an unexpected kind', () => {
    const payload = plain({
      workspace: LOADED_WORKSPACE,
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
      workspace: LOADED_WORKSPACE,
      validation: { valid: true, message: 'Valid' },
      projection: { ...PROJECTION_FIXTURE, steps: [brokenStep] },
    })

    expect(() => parseProjectionEnvelope(payload)).toThrow(/in_anchors must be an array/)
  })

  it('does not trust a partially shaped projection', () => {
    expect(() =>
      parseProjectionEnvelope({
        workspace: LOADED_WORKSPACE,
        validation: { valid: true, message: 'Valid' },
        projection: { symbol_pack: 'basic' },
      }),
    ).toThrow(ProjectionContractError)
  })
})
