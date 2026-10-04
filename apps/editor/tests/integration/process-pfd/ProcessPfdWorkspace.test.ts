// @vitest-environment happy-dom
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, h, type PropType } from 'vue'

import ProcessPfdWorkspace from '../../../src/process-pfd/ProcessPfdWorkspace.vue'
import type { ProcessPfdProjectionDto } from '../../../src/process-pfd/dto'
import { PROJECTION_FIXTURE } from '../../fixtures/process-pfd'

/**
 * Feature integration test for the Process/PFD workspace.
 *
 * Only the two unavoidable boundaries are replaced:
 *
 * - the network, by stubbing `fetch` (the transport, the runtime contract
 *   narrowing, the feature state, selection resolution, the Inspector and the
 *   validation/error behaviour stay real),
 * - the canvas, by a minimal test double that emits the same DeepPlant-owned
 *   semantic selection contract as the real canvas component.
 *
 * It therefore runs without a server, without a browser engine, and without
 * Vue Flow. The real framework interaction is #82's browser E2E concern.
 */
const CanvasStub = defineComponent({
  name: 'ProcessPfdCanvas',
  props: {
    projection: { type: Object as PropType<ProcessPfdProjectionDto | null>, default: null },
  },
  emits: ['selectStep', 'selectStream', 'clearSelection'],
  setup(props, { emit, expose }) {
    // Honours the real canvas's exposed viewport action contract.
    expose({ fitView: () => {} })
    return () =>
      h(
        'div',
        {
          'data-test': 'canvas-stub',
          'data-projection-steps': String(props.projection?.steps.length ?? 0),
        },
        [
          h(
            'button',
            {
              type: 'button',
              'data-test': 'select-step',
              onClick: () => emit('selectStep', 'PS-pump'),
            },
            'select PS-pump',
          ),
          h(
            'button',
            {
              type: 'button',
              'data-test': 'select-stream',
              onClick: () => emit('selectStream', 'S-004'),
            },
            'select S-004',
          ),
        ],
      )
  },
})

/** Shape the boundary returns: `error` is only present when there is one. */
function envelope(
  projection: unknown,
  options: { error?: string; valid?: boolean; message?: string } = {},
): Record<string, unknown> {
  const valid = options.valid ?? true
  const body: Record<string, unknown> = {
    validation: { valid, message: options.message ?? (valid ? 'Valid' : 'Invalid') },
    projection,
  }
  if (options.error !== undefined) {
    body['error'] = options.error
  }
  return body
}

function stubBoundary(body: unknown, status = 200): void {
  vi.stubGlobal(
    'fetch',
    vi.fn(
      async () =>
        new Response(JSON.stringify(body), {
          status,
          headers: { 'Content-Type': 'application/json' },
        }),
    ),
  )
}

async function mountWorkspace(): Promise<VueWrapper> {
  const wrapper = mount(ProcessPfdWorkspace, {
    global: { stubs: { ProcessPfdCanvas: CanvasStub } },
  })
  await flushPromises()
  return wrapper
}

describe('ProcessPfdWorkspace', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('shows a loading state until the projection arrives', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => new Promise<Response>(() => {})),
    )

    const wrapper = await mountWorkspace()

    expect(wrapper.text()).toContain('Loading the process model…')
    expect(wrapper.get('footer').text()).toBe('Loading validation status…')
  })

  it('renders the projection envelope as usable Process/PFD state with Valid semantics', async () => {
    stubBoundary(envelope(PROJECTION_FIXTURE))

    const wrapper = await mountWorkspace()

    expect(wrapper.get('[data-test="canvas-stub"]').attributes('data-projection-steps')).toBe('2')
    expect(wrapper.get('footer').text()).toBe('Valid')
    expect(wrapper.text()).not.toContain('Loading the process model…')
    expect(wrapper.find('[role="alert"]').exists()).toBe(false)
  })

  it('drives the Inspector from a selected ProcessStep', async () => {
    stubBoundary(envelope(PROJECTION_FIXTURE))

    const wrapper = await mountWorkspace()
    await wrapper.get('[data-test="select-step"]').trigger('click')

    const inspector = wrapper.get('aside[aria-label="Inspector"]')
    expect(inspector.get('h2').text()).toBe('PS-pump')
    expect(inspector.text()).toContain('Feed Pumping')
    expect(inspector.text()).toContain('pumping')
  })

  it('drives the Inspector from a selected ProcessStream', async () => {
    stubBoundary(envelope(PROJECTION_FIXTURE))

    const wrapper = await mountWorkspace()
    await wrapper.get('[data-test="select-stream"]').trigger('click')

    const inspector = wrapper.get('aside[aria-label="Inspector"]')
    expect(inspector.get('h2').text()).toBe('S-004')
    expect(inspector.text()).toContain('PS-pump')
    expect(inspector.text()).toContain('in_recycle')
  })

  it('keeps a projection limitation separate from a valid semantic model', async () => {
    stubBoundary(envelope(null, { error: 'no process model to project' }), 422)

    const wrapper = await mountWorkspace()

    // The model is still semantically valid; only the view cannot be produced.
    expect(wrapper.get('footer').text()).toBe('Valid')
    expect(wrapper.get('[role="alert"]').text()).toBe('no process model to project')
  })

  it('reports an invalid semantic model as invalid, without a projection error', async () => {
    stubBoundary(envelope(null, { valid: false, message: 'duplicate process step id' }))

    const wrapper = await mountWorkspace()

    expect(wrapper.get('footer').text()).toBe('Invalid: duplicate process step id')
    expect(wrapper.find('[role="alert"]').exists()).toBe(false)
  })

  it('reports an unreachable boundary without claiming the model is invalid', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        throw new Error('connection refused')
      }),
    )

    const wrapper = await mountWorkspace()

    expect(wrapper.get('[role="alert"]').text()).toContain('cannot reach the local DeepPlant')
  })
})
