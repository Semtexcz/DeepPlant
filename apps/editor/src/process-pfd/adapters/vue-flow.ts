import type { Edge, Node } from '@vue-flow/core'

import type { ProcessPfdProjectionDto, ProcessStepDto, ProcessStreamDto } from '../transport/dto'

/**
 * Frontend adapter between the DeepPlant projection DTOs and Vue Flow.
 *
 * This is the only place where the framework's object shapes appear. Vue Flow
 * stays replaceable: `Node`/`Edge` never leak into the Python transport DTOs,
 * and every framework object carries the explicit DeepPlant identity (kind +
 * semantic id) in its `data`. Framework ids, positions, handles, dimensions,
 * and selection remain framework state and never become engineering truth.
 */

export const DEEPLANT_STEP_NODE_TYPE = 'deeplantProcessStep'

export type AnchorDirection = 'in' | 'out'

export interface DeepPlantNodeData {
  readonly kind: 'process-step'
  /** Explicit DeepPlant semantic identity; never the framework id. */
  readonly deeplantId: string
  readonly symbolSize: number
  readonly step: ProcessStepDto
}

export interface DeepPlantEdgeData {
  readonly kind: 'process-stream'
  /** Explicit DeepPlant semantic identity; never the framework id. */
  readonly deeplantId: string
  readonly stream: ProcessStreamDto
}

/**
 * A DeepPlant node inside the Vue Flow view: a framework node that always
 * carries its DeepPlant projection data. `Node` is a framework type; the
 * DeepPlant identity stays in `data.deeplantId`.
 */
export type DeepPlantNode = Node<DeepPlantNodeData> & { data: DeepPlantNodeData }

/** A DeepPlant edge inside the Vue Flow view, always carrying its projection. */
export type DeepPlantEdge = Edge<DeepPlantEdgeData> & { data: DeepPlantEdgeData }

export interface ProcessPfdView {
  readonly nodes: DeepPlantNode[]
  readonly edges: DeepPlantEdge[]
  readonly symbolSize: number
}

/** Id of the Vue Flow handle that carries one DeepPlant presentation anchor. */
export function stepHandleId(direction: AnchorDirection, anchorIndex: number): string {
  return `deeplant-${direction}-anchor-${anchorIndex}`
}

/** Framework node id. Deliberately distinct from the semantic step id. */
export function frameworkNodeId(stepId: string): string {
  return `vue-flow-node:${stepId}`
}

/** Framework edge id. Deliberately distinct from the semantic stream id. */
export function frameworkEdgeId(streamId: string): string {
  return `vue-flow-edge:${streamId}`
}

/**
 * Accessible name of a projected `ProcessStep` in the canvas.
 *
 * The prefix is DeepPlant-owned vocabulary and deliberately uses the semantic
 * step id; the framework id never appears in an accessible name.
 */
export function stepLabel(stepId: string): string {
  return `Process step ${stepId}`
}

/** Accessible name of a projected `ProcessStream` in the canvas (same contract). */
export function streamLabel(streamId: string): string {
  return `Process stream ${streamId}`
}

/**
 * Read the explicit DeepPlant semantic identity carried in a Vue Flow node or
 * edge `data` payload.
 *
 * Framework event payloads are untrusted at this boundary, so the id is narrowed
 * at runtime rather than cast to a DeepPlant type.
 */
export function deepPlantIdOf(data: unknown): string | null {
  if (typeof data !== 'object' || data === null || !('deeplantId' in data)) {
    return null
  }
  const candidate: unknown = data.deeplantId
  return typeof candidate === 'string' ? candidate : null
}

export function toVueFlowNode(step: ProcessStepDto, symbolSize: number): DeepPlantNode {
  return {
    id: frameworkNodeId(step.id),
    type: DEEPLANT_STEP_NODE_TYPE,
    position: { x: step.x, y: step.y },
    draggable: false,
    connectable: false,
    selectable: true,
    // DeepPlant-owned accessible name. Vue Flow renders focusable nodes with a
    // `group` role, so the element needs a name: this states the semantic
    // identity (never the framework id) and gives the browser/E2E layer one
    // stable, framework-independent handle on the projected `ProcessStep`.
    ariaLabel: stepLabel(step.id),
    data: {
      kind: 'process-step',
      deeplantId: step.id,
      symbolSize,
      step,
    },
  }
}

export function toVueFlowEdge(stream: ProcessStreamDto): DeepPlantEdge {
  return {
    id: frameworkEdgeId(stream.id),
    source: frameworkNodeId(stream.source.step),
    target: frameworkNodeId(stream.target.step),
    sourceHandle: stepHandleId('out', stream.source.anchor),
    targetHandle: stepHandleId('in', stream.target.anchor),
    type: 'smoothstep',
    selectable: true,
    // DeepPlant-owned accessible name. A `ProcessStream` has no visible label,
    // and Vue Flow's default edge name would leak the framework node ids
    // (`vue-flow-node:...`) instead of the semantic stream identity. This states
    // the semantic identity and gives the browser/E2E layer one stable,
    // framework-independent handle on the projected `ProcessStream`.
    ariaLabel: streamLabel(stream.id),
    data: {
      kind: 'process-stream',
      deeplantId: stream.id,
      stream,
    },
  }
}

/** Map the whole DeepPlant projection into Vue Flow nodes and edges. */
export function toProcessPfdView(projection: ProcessPfdProjectionDto): ProcessPfdView {
  return {
    nodes: projection.steps.map((step) => toVueFlowNode(step, projection.symbol_size)),
    edges: projection.streams.map((stream) => toVueFlowEdge(stream)),
    symbolSize: projection.symbol_size,
  }
}
