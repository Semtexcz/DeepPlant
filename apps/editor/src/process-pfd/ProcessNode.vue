<script setup lang="ts">
import { Handle, Position, type NodeProps } from '@vue-flow/core'
import { computed } from 'vue'

import { symbolUrl } from './api'
import type { ProcessAnchorDto } from './dto'
import { stepHandleId, type DeepPlantNodeData } from './vue-flow-adapter'

/**
 * Custom Vue Flow node for one projected DeepPlant `ProcessStep`.
 *
 * The engineering symbol is the canonical packaged DeepPlant SVG for the
 * step's resolved presentation symbol role, served by the local Python
 * boundary; no frontend symbol pack exists. Vue Flow handles sit on the
 * DeepPlant presentation anchors and are explicitly non-connectable: this slice
 * cannot create semantic `ProcessStream`s.
 */
const props = defineProps<NodeProps<DeepPlantNodeData>>()

const step = computed(() => props.data.step)
const imageUrl = computed(() => symbolUrl(step.value.symbol_role))

function anchorStyle(anchor: ProcessAnchorDto): Record<string, string> {
  return { left: `${anchor.x}px`, top: `${anchor.y}px` }
}

function anchorSide(anchor: ProcessAnchorDto): Position {
  return anchor.x <= props.data.symbolSize / 2 ? Position.Left : Position.Right
}

const boxStyle = computed<Record<string, string>>(() => ({
  width: `${props.data.symbolSize}px`,
  height: `${props.data.symbolSize}px`,
}))
</script>

<template>
  <div class="dp-step" :class="{ 'dp-step--selected': props.selected }" :style="boxStyle">
    <img class="dp-step__symbol" :src="imageUrl" :alt="step.symbol_role" draggable="false" />
    <Handle
      v-for="anchor in step.in_anchors"
      :key="`in-${anchor.index}`"
      :id="stepHandleId('in', anchor.index)"
      type="target"
      :position="anchorSide(anchor)"
      :connectable="false"
      :style="anchorStyle(anchor)"
    />
    <Handle
      v-for="anchor in step.out_anchors"
      :key="`out-${anchor.index}`"
      :id="stepHandleId('out', anchor.index)"
      type="source"
      :position="anchorSide(anchor)"
      :connectable="false"
      :style="anchorStyle(anchor)"
    />
    <div class="dp-step__label">
      <span class="dp-step__id">{{ step.id }}</span>
      <span v-if="step.name" class="dp-step__name">{{ step.name }}</span>
    </div>
  </div>
</template>
