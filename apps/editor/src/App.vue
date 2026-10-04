<script setup lang="ts">
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { computed, markRaw, nextTick, onMounted, ref, shallowRef } from 'vue'

import InspectorPanel from './process-pfd/InspectorPanel.vue'
import ProcessNode from './process-pfd/ProcessNode.vue'
import { fetchProjection } from './process-pfd/api'
import type { ProcessPfdProjectionDto, ValidationStatusDto } from './process-pfd/dto'
import {
  inspectorForSelection,
  selectProcessStep,
  selectProcessStream,
  type SelectedEngineeringObject,
} from './process-pfd/inspector-model'
import { DEEPLANT_STEP_NODE_TYPE, toProcessPfdView } from './process-pfd/vue-flow-adapter'

/**
 * Read-only Process/PFD workspace.
 *
 * Every engineering fact on screen comes from the DeepPlant projection produced
 * by the Python core; the browser never parses YAML and never re-derives
 * engineering meaning. Selection is transient UI state, and the view is
 * reconstructed from the projection on every load (nothing is persisted).
 */
const { fitView } = useVueFlow()

const nodeTypes = { [DEEPLANT_STEP_NODE_TYPE]: markRaw(ProcessNode) }

const projection = shallowRef<ProcessPfdProjectionDto | null>(null)
const validation = shallowRef<ValidationStatusDto | null>(null)
const loadError = ref<string | null>(null)
const loading = ref(true)
const selection = shallowRef<SelectedEngineeringObject | null>(null)

const view = computed(() =>
  projection.value === null
    ? { nodes: [], edges: [], symbolSize: 0 }
    : toProcessPfdView(projection.value),
)
const inspector = computed(() => inspectorForSelection(selection.value))

const statusText = computed(() => {
  // The strip reports semantic validation only. A view/projection error (for
  // example a valid model this Process/PFD view cannot render) is shown in the
  // canvas notice, never as an invalid model.
  if (validation.value !== null) {
    return validation.value.valid ? 'Valid' : `Invalid: ${validation.value.message}`
  }
  return loadError.value ?? 'Loading validation status…'
})

const statusIsValid = computed(() => validation.value !== null && validation.value.valid)

onMounted(load)

async function load(): Promise<void> {
  loading.value = true
  selection.value = null
  try {
    const envelope = await fetchProjection()
    validation.value = envelope.validation
    projection.value = envelope.projection
    loadError.value = envelope.error
  } catch (error) {
    projection.value = null
    validation.value = null
    loadError.value = error instanceof Error ? error.message : String(error)
  } finally {
    loading.value = false
    await nextTick()
    void fitView({ padding: 0.2 })
  }
}

function deepPlantIdentity(data: unknown): string | null {
  if (typeof data !== 'object' || data === null) {
    return null
  }
  const deeplantId: unknown = (data as { deeplantId?: unknown }).deeplantId
  return typeof deeplantId === 'string' ? deeplantId : null
}

function onNodeClick(payload: { node: { data: unknown } }): void {
  const id = deepPlantIdentity(payload.node.data)
  if (id === null || projection.value === null) {
    return
  }
  selection.value = selectProcessStep(projection.value, id)
}

function onEdgeClick(payload: { edge: { data: unknown } }): void {
  const id = deepPlantIdentity(payload.edge.data)
  if (id === null || projection.value === null) {
    return
  }
  selection.value = selectProcessStream(projection.value, id)
}

function clearSelection(): void {
  selection.value = null
}

function fitViewAction(): void {
  void fitView({ padding: 0.2 })
}
</script>

<template>
  <div class="dp-app">
    <header class="dp-header">
      <span class="dp-header__brand">DeepPlant</span>
      <span class="dp-header__sep" aria-hidden="true">|</span>
      <span class="dp-header__view">Process / PFD</span>
      <button type="button" class="dp-button" @click="fitViewAction">Fit view</button>
    </header>

    <main class="dp-main">
      <section class="dp-canvas" aria-label="Process PFD canvas">
        <VueFlow
          :nodes="view.nodes"
          :edges="view.edges"
          :node-types="nodeTypes"
          :nodes-draggable="false"
          :nodes-connectable="false"
          :edges-updatable="false"
          :elements-selectable="true"
          :delete-key-code="null"
          :min-zoom="0.1"
          :max-zoom="2.5"
          :fit-view-on-init="true"
          @node-click="onNodeClick"
          @edge-click="onEdgeClick"
          @pane-click="clearSelection"
        />
        <p v-if="loading" class="dp-canvas__notice">Loading the process model…</p>
        <p v-else-if="loadError" class="dp-canvas__notice dp-canvas__notice--error">
          {{ loadError }}
        </p>
      </section>

      <InspectorPanel :view="inspector" />
    </main>

    <footer class="dp-status" :class="{ 'dp-status--invalid': !statusIsValid }">
      <span class="dp-status__text">{{ statusText }}</span>
    </footer>
  </div>
</template>

