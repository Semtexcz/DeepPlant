import { computed, ref, shallowRef, type ComputedRef, type Ref, type ShallowRef } from 'vue'

import { fetchProjection } from '../transport/api'
import type { ProcessPfdProjectionDto, ValidationStatusDto, WorkspaceDto } from '../transport/dto'
import {
  inspectorForSelection,
  selectProcessStep,
  selectProcessStream,
  type InspectorView,
  type SelectedEngineeringObject,
} from '../view-models/inspector'
import { workspaceStatus, type StatusView } from '../view-models/workspace-status'

/** The workspace state before the boundary has answered: no project open. */
const EMPTY_WORKSPACE: WorkspaceDto = { state: 'empty', document: null }

/**
 * Process/PFD feature state.
 *
 * This is the single owner of the read-only feature's mutable state:
 *
 * - workspace state (`workspace` and its derived `hasProject`),
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
 * engineering fact comes from the DeepPlant projection produced by Python. The
 * workspace state itself comes from the same boundary, so "no project is open" is
 * an authoritative fact rather than an absent projection (Issue #97).
 */
export interface ProcessPfdState {
  readonly workspace: ShallowRef<WorkspaceDto>
  readonly projection: ShallowRef<ProcessPfdProjectionDto | null>
  readonly validation: ShallowRef<ValidationStatusDto | null>
  readonly loading: Ref<boolean>
  readonly projectionError: Ref<string | null>
  readonly selection: ShallowRef<SelectedEngineeringObject | null>
  readonly hasProject: ComputedRef<boolean>
  readonly canFitView: ComputedRef<boolean>
  readonly inspector: ComputedRef<InspectorView | null>
  readonly status: ComputedRef<StatusView>
  load(): Promise<void>
  selectStep(stepId: string): void
  selectStream(streamId: string): void
  clearSelection(): void
}

export function useProcessPfd(): ProcessPfdState {
  const workspace = shallowRef<WorkspaceDto>(EMPTY_WORKSPACE)
  const projection = shallowRef<ProcessPfdProjectionDto | null>(null)
  const validation = shallowRef<ValidationStatusDto | null>(null)
  const projectionError = ref<string | null>(null)
  const loading = ref(true)
  const selection = shallowRef<SelectedEngineeringObject | null>(null)

  // Monotonic request token. Every `load()` takes the next token and a response
  // is applied only while it is still the newest request, so a slow reply for a
  // replaced project can never overwrite the current one (Issue #97).
  let latestRequest = 0

  const hasProject = computed(() => workspace.value.state === 'loaded')

  const canFitView = computed(() => projection.value !== null)

  const inspector = computed<InspectorView | null>(() => inspectorForSelection(selection.value))

  const status = computed<StatusView>(() =>
    workspaceStatus(workspace.value, validation.value, projectionError.value, loading.value),
  )

  async function load(): Promise<void> {
    const token = ++latestRequest
    const isStale = (): boolean => token !== latestRequest
    loading.value = true
    selection.value = null
    try {
      const envelope = await fetchProjection()
      if (isStale()) return
      workspace.value = envelope.workspace
      validation.value = envelope.validation
      projection.value = envelope.projection
      projectionError.value = envelope.error
    } catch (error) {
      if (isStale()) return
      projection.value = null
      validation.value = null
      projectionError.value = error instanceof Error ? error.message : String(error)
    } finally {
      if (!isStale()) loading.value = false
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
    workspace,
    projection,
    validation,
    loading,
    projectionError,
    selection,
    hasProject,
    canFitView,
    inspector,
    status,
    load,
    selectStep,
    selectStream,
    clearSelection,
  }
}
