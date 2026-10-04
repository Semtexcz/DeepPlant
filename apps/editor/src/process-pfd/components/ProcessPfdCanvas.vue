<script setup lang="ts">
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { computed, markRaw } from 'vue'

import ProcessNode from './ProcessNode.vue'
import type { ProcessPfdProjectionDto } from '../transport/dto'
import {
  DEEPLANT_STEP_NODE_TYPE,
  deepPlantIdOf,
  toProcessPfdView,
  type ProcessPfdView,
} from '../adapters/vue-flow'

/**
 * Vue Flow canvas boundary for the Process/PFD feature.
 *
 * This component is the only place the graph framework appears. It registers the
 * DeepPlant node type, derives the framework view from the DeepPlant projection
 * through the adapter, owns the transient framework state (viewport, fit view),
 * and translates raw framework click payloads back into DeepPlant semantic
 * identities.
 *
 * It emits semantic selection *intent* only - a `ProcessStep`/`ProcessStream`
 * id - so no Vue Flow `Node`/`Edge` ever travels upwards. The inverse
 * translation (id -> projected object -> Inspector) belongs to the feature state.
 */
const props = defineProps<{ projection: ProcessPfdProjectionDto | null }>()

const emit = defineEmits<{
  selectStep: [stepId: string]
  selectStream: [streamId: string]
  clearSelection: []
}>()

/** Fit-view padding is a canvas viewport concern, not a feature concern. */
const FIT_VIEW_PADDING = 0.2

const EMPTY_VIEW: ProcessPfdView = { nodes: [], edges: [], symbolSize: 0 }

const nodeTypes = { [DEEPLANT_STEP_NODE_TYPE]: markRaw(ProcessNode) }
const { fitView: fitViewInViewport } = useVueFlow()

const view = computed<ProcessPfdView>(() =>
  props.projection === null ? EMPTY_VIEW : toProcessPfdView(props.projection),
)

/** Imperative viewport action, driven by the application toolbar. */
function fitView(): void {
  void fitViewInViewport({ padding: FIT_VIEW_PADDING })
}

function onNodeClick(payload: { node: { data: unknown } }): void {
  const stepId = deepPlantIdOf(payload.node.data)
  if (stepId !== null) {
    emit('selectStep', stepId)
  }
}

function onEdgeClick(payload: { edge: { data: unknown } }): void {
  const streamId = deepPlantIdOf(payload.edge.data)
  if (streamId !== null) {
    emit('selectStream', streamId)
  }
}

defineExpose({ fitView })
</script>

<template>
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
    @pane-click="emit('clearSelection')"
  />
</template>

<style scoped>
/*
 * Vue Flow integration boundary.
 *
 * These are third-party framework selectors, so they live with the canvas that
 * configures Vue Flow rather than with unrelated application components.
 * `:deep()` is required because the framework renders the wrapper elements,
 * which do not carry this component's scope id.
 *
 * The node wrapper is neutralised so the DeepPlant engineering symbol, not a
 * generic card, is what the engineer sees.
 */
:deep(.vue-flow__node-deeplantProcessStep) {
  padding: 0;
  background: transparent;
  border: none;
}
</style>
