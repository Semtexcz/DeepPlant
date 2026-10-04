// @vitest-environment happy-dom
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import { defineComponent, h, type PropType } from 'vue'

import { Position, type NodeProps } from '@vue-flow/core'

import ProcessNode from '../../../src/process-pfd/ProcessNode.vue'
import { SYMBOL_SIZE, PROJECTION_FIXTURE, PUMP_STEP } from '../../fixtures/process-pfd'
import {
  DEEPLANT_STEP_NODE_TYPE,
  frameworkNodeId,
  stepHandleId,
  type DeepPlantNodeData,
} from '../../../src/process-pfd/vue-flow-adapter'

/**
 * Minimal, test-local Vue Flow provider.
 *
 * `ProcessNode` is a custom Vue Flow node, so it is mounted with the framework's
 * node props. Only `Handle` is replaced, because it needs the whole Vue Flow
 * runtime graph context, which is exactly what this component test does not own
 * (#82 covers the real browser interaction). `Position` is used unreplaced.
 */
const HandleStub = defineComponent({
  name: 'HandleStub',
  props: {
    id: { type: String, default: null },
    type: { type: String, default: null },
    position: { type: String, default: null },
    connectable: { type: Boolean, default: null },
    style: { type: Object as PropType<Record<string, string> | null>, default: null },
  },
  setup(props) {
    return () =>
      h('span', {
        class: 'handle-stub',
        'data-handle-id': props.id,
        'data-handle-type': props.type,
        'data-handle-position': props.position,
        'data-handle-connectable': String(props.connectable),
        'data-anchor': `${props.style?.left ?? ''},${props.style?.top ?? ''}`,
      })
  },
})

/** Framework node event hooks are never exercised by this component. */
const IGNORED_NODE_EVENTS: NodeProps<DeepPlantNodeData>['events'] = {
  doubleClick: () => ({ off: () => {} }),
  click: () => ({ off: () => {} }),
  mouseEnter: () => ({ off: () => {} }),
  mouseMove: () => ({ off: () => {} }),
  mouseLeave: () => ({ off: () => {} }),
  contextMenu: () => ({ off: () => {} }),
  dragStart: () => ({ off: () => {} }),
  drag: () => ({ off: () => {} }),
  dragStop: () => ({ off: () => {} }),
}

function nodeProps(stepId: string, selected = false): NodeProps<DeepPlantNodeData> {
  const step = PROJECTION_FIXTURE.steps.find((candidate) => candidate.id === stepId)
  if (step === undefined) {
    throw new Error(`unknown fixture step: ${stepId}`)
  }
  const data: DeepPlantNodeData = {
    kind: 'process-step',
    deeplantId: step.id,
    symbolSize: SYMBOL_SIZE,
    step,
  }
  return {
    id: frameworkNodeId(step.id),
    type: DEEPLANT_STEP_NODE_TYPE,
    selected,
    connectable: false,
    position: { x: step.x, y: step.y },
    dimensions: { width: SYMBOL_SIZE, height: SYMBOL_SIZE },
    dragging: false,
    resizing: false,
    zIndex: 0,
    data,
    events: IGNORED_NODE_EVENTS,
  }
}

function mountNode(stepId: string, selected = false) {
  return mount(ProcessNode, {
    props: nodeProps(stepId, selected),
    global: { stubs: { Handle: HandleStub } },
  })
}

describe('ProcessNode', () => {
  it('renders the canonical DeepPlant symbol for the projected symbol role', () => {
    const wrapper = mountNode('PS-pump')

    expect(wrapper.get('img').attributes('src')).toBe('/api/symbols/pump.svg')
    expect(wrapper.get('img').attributes('alt')).toBe(PUMP_STEP.symbol_role)
  })

  it('shows the semantic identity and name of the projected step', () => {
    const wrapper = mountNode('PS-pump')

    expect(wrapper.get('.dp-step__id').text()).toBe('PS-pump')
    expect(wrapper.get('.dp-step__name').text()).toBe('Feed Pumping')
  })

  it('omits the name element when the projected step has no name', () => {
    const wrapper = mountNode('PS-mix')

    expect(wrapper.get('.dp-step__id').text()).toBe('PS-mix')
    expect(wrapper.find('.dp-step__name').exists()).toBe(false)
  })

  it('represents the framework selected state without becoming engineering truth', () => {
    expect(mountNode('PS-pump', true).get('.dp-step').classes()).toContain('dp-step--selected')
    expect(mountNode('PS-pump', false).get('.dp-step').classes()).not.toContain(
      'dp-step--selected',
    )
  })

  it('produces one non-connectable handle per projected presentation anchor', () => {
    const handles = mountNode('PS-mix').findAll('.handle-stub')

    expect(handles.map((handle) => handle.attributes('data-handle-id'))).toEqual([
      stepHandleId('in', 0),
      stepHandleId('in', 1),
      stepHandleId('out', 0),
    ])
    expect(handles.map((handle) => handle.attributes('data-handle-type'))).toEqual([
      'target',
      'target',
      'source',
    ])
    expect(handles.map((handle) => handle.attributes('data-handle-connectable'))).toEqual([
      'false',
      'false',
      'false',
    ])
  })

  it('places handles on the projected anchor slots', () => {
    const handles = mountNode('PS-pump').findAll('.handle-stub')
    const inHandle = handles[0]

    expect(inHandle?.attributes('data-anchor')).toBe('0px,50px')
    // x <= symbol centre is a left-side anchor; x beyond it is a right-side anchor.
    expect(inHandle?.attributes('data-handle-position')).toBe(Position.Left)
    expect(handles[1]?.attributes('data-handle-position')).toBe(Position.Right)
  })

  it('displays the DeepPlant semantic id, never the framework node id', () => {
    const wrapper = mountNode('PS-pump')

    expect(wrapper.text()).toContain(PUMP_STEP.id)
    expect(wrapper.text()).not.toContain(frameworkNodeId(PUMP_STEP.id))
  })
})
