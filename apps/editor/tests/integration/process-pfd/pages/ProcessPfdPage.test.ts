// @vitest-environment happy-dom
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, h, ref, type PropType } from 'vue'

import ProcessPfdPage from '../../../../src/process-pfd/pages/ProcessPfdPage.vue'
import type { ProcessPfdProjectionDto } from '../../../../src/process-pfd/transport/dto'
import {
  EMPTY_WORKSPACE,
  LOADED_WORKSPACE,
  PROJECTION_FIXTURE,
} from '../../../fixtures/process-pfd'

/**
 * Feature integration test for the Process/PFD page.
 *
 * Only the two unavoidable boundaries are replaced:
 *
 * - the network, by stubbing `fetch` (the transport, the runtime contract
 *   narrowing, the feature state, selection resolution, the Inspector and the
 *   validation/error behaviour stay real),
 * - the canvas, by a minimal test double that emits the same DeepPlant-owned
 *   semantic selection contract as the real canvas component and counts its
 *   exposed viewport action.
 *
 * It therefore runs without a server, without a browser engine, and without
 * Vue Flow. The real framework interaction is owned by the browser E2E suite
 * (`apps/editor/e2e/`).
 */
const CanvasStub = defineComponent({
  name: 'ProcessPfdCanvas',
  props: {
    projection: { type: Object as PropType<ProcessPfdProjectionDto | null>, default: null },
  },
  emits: ['selectStep', 'selectStream', 'clearSelection'],
  setup(props, { emit, expose }) {
    const fitViewCalls = ref(0)
    // Honours the real canvas's exposed viewport action contract.
    expose({
      fitView: () => {
        fitViewCalls.value += 1
      },
    })
    return () =>
      h(
        'div',
        {
          'data-test': 'canvas-stub',
          'data-projection-steps': String(props.projection?.steps.length ?? 0),
          'data-fit-view-calls': String(fitViewCalls.value),
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

/** The boundary envelope for a loaded project. `error` is only present with one. */
function loadedEnvelope(
  projection: unknown,
  options: { error?: string; valid?: boolean; message?: string } = {},
): Record<string, unknown> {
  const valid = options.valid ?? true
  const body: Record<string, unknown> = {
    workspace: LOADED_WORKSPACE,
    validation: { valid, message: options.message ?? (valid ? 'Valid' : 'Invalid') },
    projection,
  }
  if (options.error !== undefined) {
    body['error'] = options.error
  }
  return body
}

/** The boundary envelope for a workspace with no project open. */
function emptyEnvelope(): Record<string, unknown> {
  return { workspace: EMPTY_WORKSPACE, validation: null, projection: null }
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

async function mountPage(): Promise<VueWrapper> {
  const wrapper = mount(ProcessPfdPage, {
    global: { stubs: { ProcessPfdCanvas: CanvasStub } },
  })
  await flushPromises()
  return wrapper
}

describe('ProcessPfdPage', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('shows a loading state until the workspace answer arrives', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => new Promise<Response>(() => {})),
    )

    const wrapper = await mountPage()

    expect(wrapper.text()).toContain('Loading the process model…')
    expect(wrapper.get('footer').text()).toBe('Loading validation status…')
  })

  it('renders the ordinary shell with no project open', async () => {
    stubBoundary(emptyEnvelope())

    const wrapper = await mountPage()

    // The shared application shell is present: the canvas, the Inspector and the
    // status strip are all there, just with no document.
    expect(wrapper.find('[aria-label="Process PFD canvas"]').exists()).toBe(true)
    expect(wrapper.find('aside[aria-label="Inspector"]').exists()).toBe(true)
    expect(wrapper.get('[data-test="canvas-stub"]').attributes('data-projection-steps')).toBe('0')

    const notice = wrapper.get('[role="note"][aria-label="No project open"]')
    expect(notice.text()).toContain('No project open. Use File → Open… to open a plant model.')
    expect(wrapper.get('footer').text()).toBe('No project open')

    // No engineering model was fabricated and it is not an error state.
    expect(wrapper.find('[role="alert"]').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('Invalid')
  })

  it('does not fit the canvas with no project open', async () => {
    stubBoundary(emptyEnvelope())

    const wrapper = await mountPage()

    // The project-dependent canvas action is a safe no-op with no document.
    expect(wrapper.get('[data-test="canvas-stub"]').attributes('data-fit-view-calls')).toBe('0')
  })

  it('renders the projection envelope as usable Process/PFD state with Valid semantics', async () => {
    stubBoundary(loadedEnvelope(PROJECTION_FIXTURE))

    const wrapper = await mountPage()

    expect(wrapper.get('[data-test="canvas-stub"]').attributes('data-projection-steps')).toBe('2')
    expect(wrapper.get('footer').text()).toBe('Valid')
    expect(wrapper.text()).not.toContain('Loading the process model…')
    expect(wrapper.find('[role="alert"]').exists()).toBe(false)
    expect(wrapper.find('[role="note"][aria-label="No project open"]').exists()).toBe(false)
    // With a project open the canvas viewport action runs once on load.
    expect(wrapper.get('[data-test="canvas-stub"]').attributes('data-fit-view-calls')).toBe('1')
  })
})

describe('ProcessPfdPage selection and status', () => {
  it('drives the Inspector from a selected ProcessStep', async () => {
    stubBoundary(loadedEnvelope(PROJECTION_FIXTURE))

    const wrapper = await mountPage()
    await wrapper.get('[data-test="select-step"]').trigger('click')

    const inspector = wrapper.get('aside[aria-label="Inspector"]')
    expect(inspector.get('h2').text()).toBe('PS-pump')
    expect(inspector.text()).toContain('Feed Pumping')
    expect(inspector.text()).toContain('pumping')
  })

  it('drives the Inspector from a selected ProcessStream', async () => {
    stubBoundary(loadedEnvelope(PROJECTION_FIXTURE))

    const wrapper = await mountPage()
    await wrapper.get('[data-test="select-stream"]').trigger('click')

    const inspector = wrapper.get('aside[aria-label="Inspector"]')
    expect(inspector.get('h2').text()).toBe('S-004')
    expect(inspector.text()).toContain('PS-pump')
    expect(inspector.text()).toContain('in_recycle')
  })

  it('prompts for a selection in the Inspector once a project is open', async () => {
    stubBoundary(loadedEnvelope(PROJECTION_FIXTURE))

    const wrapper = await mountPage()

    const inspector = wrapper.get('aside[aria-label="Inspector"]')
    expect(inspector.text()).toContain('Select a process step or process stream.')
    expect(inspector.text()).not.toContain('No project open.')
  })

  it('keeps a projection limitation separate from a valid semantic model', async () => {
    stubBoundary(loadedEnvelope(null, { error: 'no process model to project' }), 422)

    const wrapper = await mountPage()

    // The model is still semantically valid; only the view cannot be produced.
    expect(wrapper.get('footer').text()).toBe('Valid')
    expect(wrapper.get('[role="alert"]').text()).toBe('no process model to project')
    // A project is still open, so this is not the empty-workspace state.
    expect(wrapper.find('[role="note"][aria-label="No project open"]').exists()).toBe(false)
  })

  it('reports an invalid semantic model as invalid, without a projection error', async () => {
    stubBoundary(loadedEnvelope(null, { valid: false, message: 'duplicate process step id' }))

    const wrapper = await mountPage()

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

    const wrapper = await mountPage()

    expect(wrapper.get('[role="alert"]').text()).toContain('cannot reach the local DeepPlant')
    // A boundary error is not the neutral empty-workspace state.
    expect(wrapper.find('[role="note"][aria-label="No project open"]').exists()).toBe(false)
  })
})
