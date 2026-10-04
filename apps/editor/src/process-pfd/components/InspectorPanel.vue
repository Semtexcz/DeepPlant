<script setup lang="ts">
import type { InspectorView } from '../view-models/inspector'

/**
 * Read-only Inspector.
 *
 * It renders engineering fields produced from the DeepPlant projection. It has no
 * editable inputs and it is independent of Vue Flow's node/edge shape: it only
 * ever receives a DeepPlant Inspector view model.
 *
 * Presentation is ordinary application UI, so it uses the canonical UnoCSS
 * utility layer rather than a bespoke stylesheet.
 */
const props = defineProps<{ view: InspectorView | null }>()
</script>

<template>
  <aside
    class="overflow-auto border-l border-[var(--dp-border)] bg-[var(--dp-surface)] p-3"
    aria-label="Inspector"
  >
    <h2 class="mb-3 mt-0 text-[15px]">
      {{ props.view === null ? 'Inspector' : props.view.title }}
    </h2>
    <p v-if="props.view === null" class="m-0 text-[var(--dp-muted)]">
      Select a process step or process stream.
    </p>
    <dl v-else class="m-0 grid grid-cols-[auto] gap-x-2 gap-y-0.5">
      <template v-for="field in props.view.fields" :key="field.label">
        <dt class="text-xs uppercase tracking-[0.04em] text-[var(--dp-muted)]">
          {{ field.label }}
        </dt>
        <dd class="mb-2 mt-0 [overflow-wrap:anywhere]">{{ field.value }}</dd>
      </template>
    </dl>
  </aside>
</template>
