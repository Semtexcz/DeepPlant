import type { ValidationStatusDto, WorkspaceDto } from '../transport/dto'

/**
 * Workspace/validation status mapping.
 *
 * A pure mapping from the boundary's workspace state, semantic validation, and
 * any error to the status strip the user sees. Keeping it out of the feature-state
 * composable makes the precedence explicit and independently testable.
 *
 * The precedence encodes Issue #97's separation of concerns:
 *
 * - no project open is a neutral state, never an invalid model or a view failure;
 * - with a project open, the strip reports *semantic validation only*, so a
 *   Process/PFD view error is a separate canvas notice rather than an invalid
 *   model;
 * - an unreachable boundary is a genuine error and is never presented as a normal
 *   empty workspace.
 */
export type StatusTone = 'neutral' | 'valid' | 'invalid'

export interface StatusView {
  readonly text: string
  readonly tone: StatusTone
}

const LOADING_TEXT = 'Loading validation status…'
const EMPTY_TEXT = 'No project open'

export function workspaceStatus(
  workspace: WorkspaceDto,
  validation: ValidationStatusDto | null,
  error: string | null,
  loading: boolean,
): StatusView {
  if (loading) {
    return { text: LOADING_TEXT, tone: 'neutral' }
  }
  if (workspace.state !== 'loaded') {
    return error === null
      ? { text: EMPTY_TEXT, tone: 'neutral' }
      : { text: error, tone: 'invalid' }
  }
  if (validation !== null) {
    return validation.valid
      ? { text: 'Valid', tone: 'valid' }
      : { text: `Invalid: ${validation.message}`, tone: 'invalid' }
  }
  return { text: error ?? LOADING_TEXT, tone: 'invalid' }
}