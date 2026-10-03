<script setup lang="ts">
import type { InspectorView } from './inspector-model'

/**
 * Read-only Inspector.
 *
 * It renders engineering fields produced from the DeepPlant projection. It has
 * no editable inputs, and it is independent of Vue Flow's node/edge shape.
 */
const props = defineProps<{ view: InspectorView | null }>()
</script>

<template>
  <aside class="dp-inspector" aria-label="Inspector">
    <h2 class="dp-inspector__title">
      {{ props.view === null ? 'Inspector' : props.view.title }}
    </h2>
    <p v-if="props.view === null" class="dp-inspector__empty">
      Select a process step or process stream.
    </p>
    <dl v-else class="dp-inspector__fields">
      <template v-for="field in props.view.fields" :key="field.label">
        <dt class="dp-inspector__label">{{ field.label }}</dt>
        <dd class="dp-inspector__value">{{ field.value }}</dd>
      </template>
    </dl>
  </aside>
</template>
