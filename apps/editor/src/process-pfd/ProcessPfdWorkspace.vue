<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'

import InspectorPanel from './InspectorPanel.vue'
import ProcessPfdCanvas from './ProcessPfdCanvas.vue'
import { useProcessPfd } from './useProcessPfd'

/**
 * Process/PFD feature workspace.
 *
 * Owns the feature state (`useProcessPfd`) and composes the feature UI: the
 * canvas, the read-only Inspector, the canvas notices, and the semantic status
 * strip. It is the one place that binds feature state to feature UI; the
 * application shell above it only composes and the canvas below it only renders
 * the graph.
 *
 * The canvas viewport action (*Fit view*) is exposed so the application toolbar
 * can offer it without importing the graph framework.
 */
const {
  projection,
  loading,
  projectionError,
  inspector,
  statusText,
  statusIsValid,
  load,
  selectStep,
  selectStream,
  clearSelection,
} = useProcessPfd()

const canvas = ref<InstanceType<typeof ProcessPfdCanvas> | null>(null)

onMounted(async () => {
  await load()
  // Nodes only exist once the projection is applied, so the initial fit view is
  // an imperative post-load framework interaction.
  await nextTick()
  canvas.value?.fitView()
})

function fitView(): void {
  canvas.value?.fitView()
}

defineExpose({ fitView })
</script>

<template>
  <div class="grid min-h-0 grid-rows-[minmax(0,1fr)_auto]">
    <main class="grid min-h-0 grid-cols-[minmax(0,1fr)_300px]">
      <section class="relative min-h-0 bg-[var(--dp-surface)]" aria-label="Process PFD canvas">
        <ProcessPfdCanvas
          ref="canvas"
          :projection="projection"
          @select-step="selectStep"
          @select-stream="selectStream"
          @clear-selection="clearSelection"
        />
        <p
          v-if="loading"
          class="absolute left-3 top-3 m-0 rounded border border-[var(--dp-border)] bg-[var(--dp-surface)] px-2.5 py-1.5 text-[var(--dp-muted)]"
        >
          Loading the process model…
        </p>
        <p
          v-else-if="projectionError"
          role="alert"
          class="absolute left-3 top-3 m-0 max-w-[60ch] rounded border border-[var(--dp-invalid-text)] bg-[var(--dp-invalid-bg)] px-2.5 py-1.5 text-[var(--dp-invalid-text)]"
        >
          {{ projectionError }}
        </p>
      </section>

      <InspectorPanel :view="inspector" />
    </main>

    <footer
      role="status"
      class="border-t border-[var(--dp-border)] px-3 py-1.5"
      :class="
        statusIsValid
          ? 'bg-[var(--dp-valid-bg)] text-[var(--dp-valid-text)]'
          : 'bg-[var(--dp-invalid-bg)] text-[var(--dp-invalid-text)]'
      "
    >
      {{ statusText }}
    </footer>
  </div>
</template>
