/**
 * DeepPlant-owned Process/PFD projection DTOs.
 *
 * These types mirror the transport shape produced by the Python projection
 * (`deepplant.editor.projection.projection_to_dict`). They are a *view /
 * application projection*, not an authoritative engineering model: the Python
 * semantic model stays the single source of engineering truth.
 *
 * There is deliberately no TypeScript `PlantModel` / `ProcessModel` here. The
 * browser does not re-implement the domain model, it reads a read-only
 * projection of it. Framework concepts (Vue Flow nodes, edges, handles,
 * dimensions, selection) are also absent: those belong to the adapter.
 */

export type ProcessStepKind = 'process-step'
export type ProcessStreamKind = 'process-stream'

/** One presentation anchor slot in symbol-local pack coordinates (0..symbol_size). */
export interface ProcessAnchorDto {
  readonly index: number
  readonly x: number
  readonly y: number
}

/** Read-only projection of one semantic `ProcessStep`. */
export interface ProcessStepDto {
  readonly kind: ProcessStepKind
  readonly id: string
  readonly name: string | null
  readonly function: string
  readonly symbol_role: string
  readonly ports: readonly string[]
  readonly x: number
  readonly y: number
  readonly in_anchors: readonly ProcessAnchorDto[]
  readonly out_anchors: readonly ProcessAnchorDto[]
}

/** Read-only projection of one `ProcessStream` endpoint. */
export interface ProcessStreamEndpointDto {
  readonly step: string
  readonly port: string
  readonly anchor: number
}

/** Read-only projection of one semantic `ProcessStream`. */
export interface ProcessStreamDto {
  readonly kind: ProcessStreamKind
  readonly id: string
  readonly name: string | null
  readonly source: ProcessStreamEndpointDto
  readonly target: ProcessStreamEndpointDto
  readonly is_feedback: boolean
}

/** Current validation state, owned by the Python DeepPlant boundary. */
export interface ValidationStatusDto {
  readonly valid: boolean
  readonly message: string
}

export interface PlantRefDto {
  readonly id: string
  readonly name: string | null
}

/** Read-only Process/PFD projection of one plant model. */
export interface ProcessPfdProjectionDto {
  readonly plant: PlantRefDto
  readonly symbol_pack: string
  readonly symbol_size: number
  readonly validation: ValidationStatusDto
  readonly steps: readonly ProcessStepDto[]
  readonly streams: readonly ProcessStreamDto[]
}

/** Which editor-workspace state the local boundary reports (Issue #97). */
export type WorkspaceState = 'empty' | 'loaded'

/** Identity of the document an editor session has open, when one is open. */
export interface WorkspaceDocumentDto {
  readonly name: string
  readonly plant_id: string
  readonly plant_name: string | null
}

/**
 * Editor workspace state, independent of any engineering model.
 *
 * `state` is `'empty'` when no project is open and `'loaded'` when one is. An
 * empty workspace carries no model at all, so the frontend never mistakes the
 * absence of a document for a semantic validation or Process/PFD projection
 * failure, and a loaded-but-unprojectable model is still reported as loaded
 * (`document` is present while `projection` is `null`).
 */
export interface WorkspaceDto {
  readonly state: WorkspaceState
  readonly document: WorkspaceDocumentDto | null
}

/** Transport envelope returned by `/api/projection`. */
export interface ProjectionEnvelope {
  readonly workspace: WorkspaceDto
  readonly validation: ValidationStatusDto | null
  readonly projection: ProcessPfdProjectionDto | null
  readonly error: string | null
}
