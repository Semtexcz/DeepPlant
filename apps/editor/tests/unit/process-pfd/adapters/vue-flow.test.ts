import { describe, expect, it } from 'vitest'

import {
  MIX_STEP,
  PROJECTION_FIXTURE,
  PUMP_DISCHARGE_STREAM,
  PUMP_STEP,
  SYMBOL_SIZE,
} from '../../../fixtures/process-pfd'
import {
  DEEPLANT_STEP_NODE_TYPE,
  deepPlantIdOf,
  frameworkEdgeId,
  frameworkNodeId,
  stepHandleId,
  toProcessPfdView,
  toVueFlowEdge,
  toVueFlowNode,
} from '../../../../src/process-pfd/adapters/vue-flow'

/** Framework-only concepts that must never appear on a DeepPlant DTO. */
const FRAMEWORK_ONLY_KEYS = [
  'sourceHandle',
  'targetHandle',
  'nodeType',
  'type',
  'position',
  'selected',
  'dragging',
  'dimensions',
  'width',
  'height',
]

describe('DeepPlant projection -> Vue Flow adapter', () => {
  it('maps every projected step and stream into the framework view', () => {
    const view = toProcessPfdView(PROJECTION_FIXTURE)

    expect(view.nodes).toHaveLength(PROJECTION_FIXTURE.steps.length)
    expect(view.edges).toHaveLength(PROJECTION_FIXTURE.streams.length)
    expect(view.symbolSize).toBe(SYMBOL_SIZE)
  })

  it('keeps DeepPlant identity explicit and separate from the framework id', () => {
    const node = toVueFlowNode(PUMP_STEP, SYMBOL_SIZE)

    expect(node.data.kind).toBe('process-step')
    expect(node.data.deeplantId).toBe('PS-pump')
    // The framework chooses its own id; it never replaces the semantic id.
    expect(node.id).toBe(frameworkNodeId('PS-pump'))
    expect(node.id).not.toBe(node.data.deeplantId)
  })

  it('produces read-only, non-connectable nodes', () => {
    const node = toVueFlowNode(PUMP_STEP, SYMBOL_SIZE)

    expect(node.draggable).toBe(false)
    expect(node.connectable).toBe(false)
    expect(node.type).toBe(DEEPLANT_STEP_NODE_TYPE)
    expect(node.position).toEqual({ x: PUMP_STEP.x, y: PUMP_STEP.y })
  })

  it('connects edges to the framework endpoints through DeepPlant anchors', () => {
    const edge = toVueFlowEdge(PUMP_DISCHARGE_STREAM)

    expect(edge.id).toBe(frameworkEdgeId('S-004'))
    expect(edge.source).toBe(frameworkNodeId('PS-pump'))
    expect(edge.target).toBe(frameworkNodeId('PS-mix'))
    expect(edge.sourceHandle).toBe(stepHandleId('out', 0))
    expect(edge.targetHandle).toBe(stepHandleId('in', 1))
    expect(edge.data?.kind).toBe('process-stream')
    expect(edge.data?.deeplantId).toBe('S-004')
  })

  it('derives handle ids from anchor slots, not streams', () => {
    expect(stepHandleId('in', 0)).not.toBe(stepHandleId('in', 1))
    expect(stepHandleId('in', 0)).not.toBe(stepHandleId('out', 0))
  })

  it('never puts framework-only properties on the DeepPlant DTOs', () => {
    for (const step of PROJECTION_FIXTURE.steps) {
      const keys = new Set(Object.keys(step))
      for (const forbidden of FRAMEWORK_ONLY_KEYS) {
        expect(keys.has(forbidden)).toBe(false)
      }
    }
    for (const stream of PROJECTION_FIXTURE.streams) {
      const keys = new Set(Object.keys(stream))
      for (const forbidden of FRAMEWORK_ONLY_KEYS) {
        expect(keys.has(forbidden)).toBe(false)
      }
    }
  })

  it('carries the projected anchor slots onto the node data', () => {
    const node = toVueFlowNode(MIX_STEP, SYMBOL_SIZE)

    expect(node.data.step.in_anchors.map((anchor) => anchor.index)).toEqual([0, 1])
    expect(node.data.symbolSize).toBe(SYMBOL_SIZE)
  })
})

describe('DeepPlant identity narrowing from framework data', () => {
  it('reads the explicit semantic id carried by a node or edge', () => {
    expect(deepPlantIdOf(toVueFlowNode(PUMP_STEP, SYMBOL_SIZE).data)).toBe('PS-pump')
    expect(deepPlantIdOf(toVueFlowEdge(PUMP_DISCHARGE_STREAM).data)).toBe('S-004')
  })

  it('never infers identity from the framework id or an unknown payload', () => {
    expect(deepPlantIdOf(undefined)).toBeNull()
    expect(deepPlantIdOf(null)).toBeNull()
    expect(deepPlantIdOf('PS-pump')).toBeNull()
    expect(deepPlantIdOf({ id: frameworkNodeId('PS-pump') })).toBeNull()
    expect(deepPlantIdOf({ deeplantId: 42 })).toBeNull()
  })
})
