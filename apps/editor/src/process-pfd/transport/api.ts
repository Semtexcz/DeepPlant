import type { ProjectionEnvelope } from './dto'
import { parseProjectionEnvelope, ProjectionContractError } from './projection-contract'

/**
 * Browser transport access to the local DeepPlant application boundary.
 *
 * This module owns *only* how the browser talks to the boundary: the projection
 * route, the request, and the canonical symbol asset URL. It never parses YAML
 * and never rebuilds the semantic model. The payload shape contract it trusts
 * lives in `projection-contract.ts`.
 */

export const PROJECTION_ROUTE = '/api/projection'

/**
 * Load the Process/PFD projection from the local DeepPlant boundary.
 *
 * Transport and payload problems fail through `ProjectionContractError` so a
 * broken boundary is reported clearly rather than rendering a half-valid view.
 */
export async function fetchProjection(): Promise<ProjectionEnvelope> {
  let response: Response
  try {
    response = await fetch(PROJECTION_ROUTE, { headers: { Accept: 'application/json' } })
  } catch (error) {
    throw new ProjectionContractError(
      `cannot reach the local DeepPlant editor boundary: ${
        error instanceof Error ? error.message : String(error)
      }`,
    )
  }
  let payload: unknown
  try {
    payload = await response.json()
  } catch {
    throw new ProjectionContractError(
      `the local DeepPlant editor boundary returned non-JSON (HTTP ${response.status})`,
    )
  }
  return parseProjectionEnvelope(payload)
}

/** URL of one canonical packaged symbol asset, served by the local boundary. */
export function symbolUrl(symbolRole: string): string {
  return `/api/symbols/${encodeURIComponent(symbolRole)}.svg`
}
