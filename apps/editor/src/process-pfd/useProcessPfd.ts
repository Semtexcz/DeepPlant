import { computed, ref, shallowRef, type ComputedRef, type Ref, type ShallowRef } from 'vue'

import { fetchProjection } from './api'
import type { ProcessPfdProjectionDto, ValidationStatusDto } from './dto'
import {
  inspectorForSelection,
  selectProcessStep,
  selectProcessStream,
  type InspectorView,
  type SelectedEngineeringObject,
} from './inspector-model'

/**
 * Process/PFD feature state.
 *
 * This is the single owner of the read-only feature's mutable state:
 *
 * - remote/projection state (`projection`, `validation`, `loading`,
 *   `projectionError`),
 * - selection state (`selection`),
 * - the loading lifecycle (`load`),
 * - explicit selection actions (`selectStep`, `selectStream`, `clearSelection`).
 *
 * Everything the UI reads beyond that is derived with `computed`; nothing here
 * is synchronized with a watcher, and the framework's transient state (Vue Flow
 * nodes, edges, viewport, fit view) deliberately does not live here - it stays
 * with the canvas boundary.
 *
 * The browser never parses YAML and never re-derives engineering meaning: every
 * engineering fact comes from the DeepPlant projection produced by Python.
 */
export interface ProcessPfdState {
  readonly projection: ShallowRef<ProcessPfdProjectionDto | null>
  readonly validation: ShallowRef<ValidationStatusDto | null>
  readonly loading: Ref<boolean>
  readonly projectionError: Ref<string | null>
  readonly selection: ShallowRef<SelectedEngineeringObject | null>
  readonly inspector: ComputedRef<InspectorView | null>
  readonly statusText: ComputedRef<string>
  readonly statusIsValid: ComputedRef<boolean>
  load(): Promise<void>
  selectStep(stepId: string): void
  selectStream(streamId: string): void
  clearSelection(): void
}

export function useProcessPfd(): ProcessPfdState {
  const projection = shallowRef<ProcessPfdProjectionDto | null>(null)
  const validation = shallowRef<ValidationStatusDto | null>(null)
  const projectionError = ref<string | null>(null)
  const loading = ref(true)
  const selection = shallowRef<SelectedEngineeringObject | null>(null)

  const inspector = computed<InspectorView | null>(() => inspectorForSelection(selection.value))

  const statusText = computed(() => {
    // The strip reports semantic validation only. A view/projection error (for
    // example a semantically valid model this Process/PFD view cannot render) is
    // shown as a separate notice in the canvas, never as an invalid model.
    if (validation.value !== null) {
      return validation.value.valid ? 'Valid' : `Invalid: ${validation.value.message}`
    }
    return projectionError.value ?? 'Loading validation status…'
  })

  const statusIsValid = computed(() => validation.value !== null && validation.value.valid)

  async function load(): Promise<void> {
    loading.value = true
    selection.value = null
    try {
      const envelope = await fetchProjection()
      validation.value = envelope.validation
      projection.value = envelope.projection
      projectionError.value = envelope.error
    } catch (error) {
      projection.value = null
      validation.value = null
      projectionError.value = error instanceof Error ? error.message : String(error)
    } finally {
      loading.value = false
    }
  }

  function selectStep(stepId: string): void {
    selection.value =
      projection.value === null ? null : selectProcessStep(projection.value, stepId)
  }

  function selectStream(streamId: string): void {
    selection.value =
      projection.value === null ? null : selectProcessStream(projection.value, streamId)
  }

  function clearSelection(): void {
    selection.value = null
  }

  return {
    projection,
    validation,
    loading,
    projectionError,
    selection,
    inspector,
    statusText,
    statusIsValid,
    load,
    selectStep,
    selectStream,
    clearSelection,
  }
}
