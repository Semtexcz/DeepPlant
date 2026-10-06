// @vitest-environment happy-dom
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, h } from 'vue'

import App from '../../../src/App.vue'
import { EMPTY_WORKSPACE, LOADED_WORKSPACE, PROJECTION_FIXTURE } from '../../fixtures/process-pfd'

/**
 * Application-shell integration test (Issue #97).
 *
 * It proves the *same* application shell is present with and without a project,
 * and that a project-dependent toolbar action (`Fit view`) is disabled while no
 * project is open. Only the network is stubbed; the shell, the feature page, the
 * feature state, the Inspector and the status strip stay real. The Vue Flow
 * canvas is replaced by a minimal double so the shell can be mounted without a
 * browser engine.
 */
const CanvasStub = defineComponent({
  name: 'ProcessPfdCanvas',
  props: { projection: { type: Object, default: null } },
  emits: ['selectStep', 'selectStream', 'clearSelection'],
  setup(_props, { expose }) {
    expose({ fitView: () => {} })
    return () => h('div', { 'data-test': 'canvas-stub' })
  },
})

async function mountApp(body: unknown): Promise<VueWrapper> {
  vi.stubGlobal(
    'fetch',
    vi.fn(
      async () =>
        new Response(JSON.stringify(body), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
    ),
  )
  const wrapper = mount(App, { global: { stubs: { ProcessPfdCanvas: CanvasStub } } })
  await flushPromises()
  return wrapper
}

describe('App shell', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('keeps the shared shell and disables Fit view with no project open', async () => {
    const wrapper = await mountApp({ workspace: EMPTY_WORKSPACE, validation: null, projection: null })

    expect(wrapper.get('header').text()).toContain('DeepPlant')
    expect(wrapper.get('header').text()).toContain('Process / PFD')

    const button = wrapper.get('header button')
    expect(button.text()).toBe('Fit view')
    expect(button.attributes('disabled')).toBeDefined()

    expect(wrapper.find('[role="note"][aria-label="No project open"]').exists()).toBe(true)
    expect(wrapper.get('footer').text()).toBe('No project open')
  })

  it('enables Fit view once a project is loaded', async () => {
    const wrapper = await mountApp({
      workspace: LOADED_WORKSPACE,
      validation: { valid: true, message: 'Valid' },
      projection: PROJECTION_FIXTURE,
    })

    expect(wrapper.get('header button').attributes('disabled')).toBeUndefined()
    expect(wrapper.find('[role="note"][aria-label="No project open"]').exists()).toBe(false)
    expect(wrapper.get('footer').text()).toBe('Valid')
  })
})