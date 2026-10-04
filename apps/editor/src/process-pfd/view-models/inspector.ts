import type { ProcessPfdProjectionDto, ProcessStepDto, ProcessStreamDto } from '../transport/dto'

/**
 * Selection-to-Inspector mapping.
 *
 * Selection is transient UI state: the user selects a Vue Flow node or edge, the
 * adapter resolves the explicit DeepPlant identity, and this module turns the
 * matching *projected* engineering object into read-only Inspector fields.
 *
 * It takes only DeepPlant projection DTOs and semantic ids. It never inspects
 * Vue Flow objects, never parses labels or SVG elements, and never exposes
 * framework-only properties (position, dimensions, handles, selection, drag
 * state) as engineering facts.
 */

export type SelectedEngineeringObject =
  | { readonly kind: 'process-step'; readonly step: ProcessStepDto }
  | { readonly kind: 'process-stream'; readonly stream: ProcessStreamDto }

export interface InspectorField {
  readonly label: string
  readonly value: string
}

export interface InspectorView {
  readonly title: string
  readonly typeLabel: string
  readonly fields: readonly InspectorField[]
}

const EMPTY_VALUE = '—'

function text(value: string | null | undefined): string {
  return value !== null && value !== undefined && value.length > 0 ? value : EMPTY_VALUE
}

function joined(values: readonly string[]): string {
  return values.length > 0 ? values.join(', ') : EMPTY_VALUE
}

/** Resolve a selected Vue Flow node's DeepPlant identity to a projected step. */
export function selectProcessStep(
  projection: ProcessPfdProjectionDto,
  stepId: string,
): SelectedEngineeringObject | null {
  const step = projection.steps.find((candidate) => candidate.id === stepId)
  return step === undefined ? null : { kind: 'process-step', step }
}

/** Resolve a selected Vue Flow edge's DeepPlant identity to a projected stream. */
export function selectProcessStream(
  projection: ProcessPfdProjectionDto,
  streamId: string,
): SelectedEngineeringObject | null {
  const stream = projection.streams.find((candidate) => candidate.id === streamId)
  return stream === undefined ? null : { kind: 'process-stream', stream }
}

export function inspectorForSelection(
  selection: SelectedEngineeringObject | null,
): InspectorView | null {
  if (selection === null) {
    return null
  }
  if (selection.kind === 'process-step') {
    return inspectorForStep(selection.step)
  }
  return inspectorForStream(selection.stream)
}

function inspectorForStep(step: ProcessStepDto): InspectorView {
  return {
    title: step.id,
    typeLabel: 'Process step',
    fields: [
      { label: 'Type', value: 'Process step' },
      { label: 'ID', value: step.id },
      { label: 'Name', value: text(step.name) },
      { label: 'Function', value: step.function },
      { label: 'Ports', value: joined(step.ports) },
    ],
  }
}

function inspectorForStream(stream: ProcessStreamDto): InspectorView {
  return {
    title: stream.id,
    typeLabel: 'Process stream',
    fields: [
      { label: 'Type', value: 'Process stream' },
      { label: 'ID', value: stream.id },
      { label: 'Name', value: text(stream.name) },
      { label: 'Source step', value: stream.source.step },
      { label: 'Source port', value: stream.source.port },
      { label: 'Target step', value: stream.target.step },
      { label: 'Target port', value: stream.target.port },
    ],
  }
}
