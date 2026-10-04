<script setup lang="ts">
import { ref } from 'vue'

import ProcessPfdPage from './process-pfd/pages/ProcessPfdPage.vue'

/**
 * Application composition root.
 *
 * The editor currently exposes exactly one engineering view, so this shell owns
 * only application-level concerns: the application chrome (identity and the
 * active view) and the toolbar. The Process/PFD feature - projection state,
 * canvas, Inspector, semantic status - is owned by its page.
 *
 * Nothing here knows about the transport contract, the graph framework, or the
 * Inspector model. The toolbar's *Fit view* action is a canvas view action, so
 * it is delegated to the feature page rather than reached into.
 */
const page = ref<InstanceType<typeof ProcessPfdPage> | null>(null)

function fitView(): void {
  page.value?.fitView()
}
</script>

<template>
  <div class="grid h-full grid-rows-[auto_minmax(0,1fr)] bg-[var(--dp-bg)] text-[var(--dp-text)]">
    <header
      class="flex items-center gap-2.5 border-b border-[var(--dp-border)] bg-[var(--dp-surface)] px-3 py-2"
    >
      <span class="font-semibold">DeepPlant</span>
      <span class="text-[var(--dp-muted)]" aria-hidden="true">|</span>
      <span class="text-[var(--dp-muted)]">Process / PFD</span>
      <button
        type="button"
        class="ml-auto cursor-pointer rounded border border-[var(--dp-border)] bg-[var(--dp-surface)] px-3 py-1 text-[var(--dp-text)] [font:inherit] hover:border-[var(--dp-accent)] hover:text-[var(--dp-accent)]"
        @click="fitView"
      >
        Fit view
      </button>
    </header>

    <ProcessPfdPage ref="page" />
  </div>
</template>

