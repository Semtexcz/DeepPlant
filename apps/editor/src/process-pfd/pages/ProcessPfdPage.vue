<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'

import InspectorPanel from '../components/InspectorPanel.vue'
import ProcessPfdCanvas from '../components/ProcessPfdCanvas.vue'
import { useProcessPfd } from '../composables/useProcessPfd'

/**
 * Process/PFD feature page.
 *
 * Page composition for the top-level Process/PFD screen: it owns the feature
 * state (`useProcessPfd`) and composes the feature UI: the canvas, the
 * read-only Inspector, the canvas notices, and the workspace/validation status
 * strip. It is the one place that binds feature state to feature UI; the
 * application shell above it only composes and the canvas below it only renders
 * the graph.
 *
 * The page exists in both workspace states (Issue #97). With no project open it
 * still renders the ordinary shell - canvas, Inspector, status strip - with an
 * explicit neutral empty-workspace notice, so the absence of a document is never
 * shown as invalid engineering data or a failed Process/PFD projection.
 *
 * The canvas viewport action (*Fit view*) is exposed so the application toolbar
 * can offer it without importing the graph framework; it is disabled with no
 * project open (`fitViewEnabled`) and a safe no-op when invoked.
 */
const {
  projection,
  loading,
  projectionError,
  hasProject,
  canFitView,
  inspector,
  status,
  load,
  selectStep,
  selectStream,
  clearSelection,
} = useProcessPfd()

const canvas = ref<InstanceType<typeof ProcessPfdCanvas> | null>(null)

const statusClass = computed(() => {
  switch (status.value.tone) {
    case 'valid':
      return 'bg-[var(--dp-valid-bg)] text-[var(--dp-valid-text)]'
    case 'invalid':
      return 'bg-[var(--dp-invalid-bg)] text-[var(--dp-invalid-text)]'
    default:
      return 'bg-[var(--dp-surface)] text-[var(--dp-muted)]'
  }
})

onMounted(async () => {
  await load()
  // Nodes only exist once the projection is applied, so the initial fit view is
  // an imperative post-load framework interaction. With no project open there is
  // nothing to fit.
  await nextTick()
  if (canFitView.value) {
    canvas.value?.fitView()
  }
})

function fitView(): void {
  if (canFitView.value) {
    canvas.value?.fitView()
  }
}

defineExpose({ fitView, fitViewEnabled: canFitView })
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
        <p
          v-else-if="!hasProject"
          role="note"
          aria-label="No project open"
          class="absolute left-1/2 top-1/2 m-0 -translate-x-1/2 -translate-y-1/2 text-center text-[var(--dp-muted)]"
        >
          No project open. Use File → Open… to open a plant model.
        </p>
      </section>

      <InspectorPanel :view="inspector" :has-project="hasProject" />
    </main>

    <footer
      role="status"
      class="border-t border-[var(--dp-border)] px-3 py-1.5"
      :class="statusClass"
    >
      {{ status.text }}
    </footer>
  </div>
</template>
