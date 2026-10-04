// @vitest-environment happy-dom
import { mount, type VueWrapper } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import InspectorPanel from '../../../../src/process-pfd/components/InspectorPanel.vue'
import {
  inspectorForSelection,
  selectProcessStep,
  selectProcessStream,
} from '../../../../src/process-pfd/view-models/inspector'
import { PROJECTION_FIXTURE } from '../../../fixtures/process-pfd'

/** Read the rendered definition list as label/value pairs. */
function fieldsOf(wrapper: VueWrapper): Array<[string, string]> {
  const labels = wrapper.findAll('dt').map((node) => node.text())
  const values = wrapper.findAll('dd').map((node) => node.text())
  return labels.map((label, index) => [label, values[index] ?? ''])
}

describe('InspectorPanel', () => {
  it('is a named Inspector landmark that prompts for a selection when empty', () => {
    const wrapper = mount(InspectorPanel, { props: { view: null } })

    expect(wrapper.get('aside').attributes('aria-label')).toBe('Inspector')
    expect(wrapper.get('h2').text()).toBe('Inspector')
    expect(wrapper.text()).toContain('Select a process step or process stream.')
    expect(wrapper.find('dl').exists()).toBe(false)
  })

  it('renders the semantic fields of a selected ProcessStep', () => {
    const view = inspectorForSelection(selectProcessStep(PROJECTION_FIXTURE, 'PS-pump'))
    const wrapper = mount(InspectorPanel, { props: { view } })

    expect(wrapper.get('h2').text()).toBe('PS-pump')
    expect(fieldsOf(wrapper)).toEqual([
      ['Type', 'Process step'],
      ['ID', 'PS-pump'],
      ['Name', 'Feed Pumping'],
      ['Function', 'pumping'],
      ['Ports', 'suction, discharge'],
    ])
  })

  it('renders the semantic source and target of a selected ProcessStream', () => {
    const view = inspectorForSelection(selectProcessStream(PROJECTION_FIXTURE, 'S-004'))
    const wrapper = mount(InspectorPanel, { props: { view } })

    expect(wrapper.get('h2').text()).toBe('S-004')
    expect(fieldsOf(wrapper)).toEqual([
      ['Type', 'Process stream'],
      ['ID', 'S-004'],
      ['Name', 'Pump Discharge'],
      ['Source step', 'PS-pump'],
      ['Source port', 'discharge'],
      ['Target step', 'PS-mix'],
      ['Target port', 'in_recycle'],
    ])
  })

  it('shows a placeholder instead of an empty engineering value', () => {
    const view = inspectorForSelection(selectProcessStep(PROJECTION_FIXTURE, 'PS-mix'))
    const wrapper = mount(InspectorPanel, { props: { view } })

    expect(fieldsOf(wrapper)).toContainEqual(['Name', '—'])
  })

  it('never renders framework or presentation state as an engineering field', () => {
    const view = inspectorForSelection(selectProcessStep(PROJECTION_FIXTURE, 'PS-pump'))
    const wrapper = mount(InspectorPanel, { props: { view } })

    for (const forbidden of ['Selected', 'Position', 'Dimensions', 'Node type']) {
      expect(wrapper.findAll('dt').map((node) => node.text())).not.toContain(forbidden)
    }
  })
})
