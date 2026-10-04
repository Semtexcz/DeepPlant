import { describe, expect, it } from 'vitest'

import {
  inspectorForSelection,
  selectProcessStep,
  selectProcessStream,
} from '../../../../src/process-pfd/view-models/inspector'
import { PROJECTION_FIXTURE } from '../../../fixtures/process-pfd'

/** Labels that would indicate framework state leaking into the Inspector. */
const FRAMEWORK_LABELS = [
  'x',
  'y',
  'width',
  'height',
  'position',
  'sourceHandle',
  'targetHandle',
  'Node type',
  'Selected',
  'Dragging',
  'Dimensions',
]

function labelsOf(selection: Parameters<typeof inspectorForSelection>[0]): string[] {
  const view = inspectorForSelection(selection)
  expect(view).not.toBeNull()
  return view === null ? [] : view.fields.map((field) => field.label)
}

function valueOf(
  selection: Parameters<typeof inspectorForSelection>[0],
  label: string,
): string | undefined {
  const view = inspectorForSelection(selection)
  return view?.fields.find((field) => field.label === label)?.value
}

describe('selection -> Inspector mapping', () => {
  it('shows nothing until an object is selected', () => {
    expect(inspectorForSelection(null)).toBeNull()
  })

  it('describes a selected ProcessStep with semantic fields', () => {
    const selection = selectProcessStep(PROJECTION_FIXTURE, 'PS-pump')

    expect(labelsOf(selection)).toEqual(['Type', 'ID', 'Name', 'Function', 'Ports'])
    expect(valueOf(selection, 'Type')).toBe('Process step')
    expect(valueOf(selection, 'ID')).toBe('PS-pump')
    expect(valueOf(selection, 'Name')).toBe('Feed Pumping')
    expect(valueOf(selection, 'Function')).toBe('pumping')
    expect(valueOf(selection, 'Ports')).toBe('suction, discharge')
  })

  it('describes a selected ProcessStream with its semantic endpoints', () => {
    const selection = selectProcessStream(PROJECTION_FIXTURE, 'S-004')

    expect(labelsOf(selection)).toEqual([
      'Type',
      'ID',
      'Name',
      'Source step',
      'Source port',
      'Target step',
      'Target port',
    ])
    expect(valueOf(selection, 'Type')).toBe('Process stream')
    expect(valueOf(selection, 'ID')).toBe('S-004')
    expect(valueOf(selection, 'Name')).toBe('Pump Discharge')
    expect(valueOf(selection, 'Source step')).toBe('PS-pump')
    expect(valueOf(selection, 'Source port')).toBe('discharge')
    expect(valueOf(selection, 'Target step')).toBe('PS-mix')
    expect(valueOf(selection, 'Target port')).toBe('in_recycle')
  })

  it('never exposes framework-only properties as engineering fields', () => {
    for (const selection of [
      selectProcessStep(PROJECTION_FIXTURE, 'PS-pump'),
      selectProcessStream(PROJECTION_FIXTURE, 'S-004'),
    ]) {
      const labels = labelsOf(selection)
      for (const forbidden of FRAMEWORK_LABELS) {
        expect(labels).not.toContain(forbidden)
      }
    }
  })

  it('resolves selection by semantic identity, not by order or label', () => {
    // The second stream resolves without relying on its array index.
    const byId = selectProcessStream(PROJECTION_FIXTURE, 'S-002')
    expect(inspectorForSelection(byId)?.title).toBe('S-002')
    // A label is not an identity.
    expect(selectProcessStream(PROJECTION_FIXTURE, 'Recycle')).toBeNull()
    expect(selectProcessStep(PROJECTION_FIXTURE, 'Feed Pumping')).toBeNull()
  })

  it('returns nothing for an unknown DeepPlant identity', () => {
    expect(selectProcessStep(PROJECTION_FIXTURE, 'V-101')).toBeNull()
    expect(selectProcessStream(PROJECTION_FIXTURE, 'C-001')).toBeNull()
  })

  it('renders a placeholder for a missing name', () => {
    const selection = selectProcessStep(PROJECTION_FIXTURE, 'PS-mix')

    expect(valueOf(selection, 'Name')).toBe('—')
  })
})
