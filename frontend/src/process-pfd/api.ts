import type {
  PlantRefDto,
  ProcessAnchorDto,
  ProcessPfdProjectionDto,
  ProcessStepDto,
  ProcessStreamDto,
  ProcessStreamEndpointDto,
  ProjectionEnvelope,
  ValidationStatusDto,
} from './dto'

/**
 * Browser access to the local DeepPlant application boundary.
 *
 * The browser never parses YAML and never rebuilds the semantic model: it reads
 * the DeepPlant-owned projection JSON and the canonical packaged symbol assets
 * through the local Python boundary. Incoming data is narrowed to the DTO
 * contract so a contract mismatch fails clearly instead of silently producing a
 * half-valid view.
 */

export const PROJECTION_ROUTE = '/api/projection'

/** Raised when the boundary's payload does not match the expected contract. */
export class ProjectionContractError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'ProjectionContractError'
  }
}

function asRecord(value: unknown, what: string): Record<string, unknown> {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    throw new ProjectionContractError(`${what} must be a JSON object`)
  }
  return value as Record<string, unknown>
}

function asString(record: Record<string, unknown>, key: string, what: string): string {
  const value = record[key]
  if (typeof value !== 'string') {
    throw new ProjectionContractError(`${what}.${key} must be a string`)
  }
  return value
}

function asNumber(record: Record<string, unknown>, key: string, what: string): number {
  const value = record[key]
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    throw new ProjectionContractError(`${what}.${key} must be a finite number`)
  }
  return value
}

function asBoolean(record: Record<string, unknown>, key: string, what: string): boolean {
  const value = record[key]
  if (typeof value !== 'boolean') {
    throw new ProjectionContractError(`${what}.${key} must be a boolean`)
  }
  return value
}

function asNullableString(
  record: Record<string, unknown>,
  key: string,
  what: string,
): string | null {
  const value = record[key]
  if (value === null || value === undefined) {
    return null
  }
  if (typeof value !== 'string') {
    throw new ProjectionContractError(`${what}.${key} must be a string or null`)
  }
  return value
}

function asArray(value: unknown, what: string): readonly unknown[] {
  if (!Array.isArray(value)) {
    throw new ProjectionContractError(`${what} must be an array`)
  }
  return value
}

function asStringArray(record: Record<string, unknown>, key: string, what: string): string[] {
  return asArray(record[key], `${what}.${key}`).map((item, index) => {
    if (typeof item !== 'string') {
      throw new ProjectionContractError(`${what}.${key}[${index}] must be a string`)
    }
    return item
  })
}

function parseValidationStatus(value: unknown): ValidationStatusDto {
  const record = asRecord(value, 'validation')
  return {
    valid: asBoolean(record, 'valid', 'validation'),
    message: asString(record, 'message', 'validation'),
  }
}

function parsePlantRef(value: unknown): PlantRefDto {
  const record = asRecord(value, 'projection.plant')
  return {
    id: asString(record, 'id', 'projection.plant'),
    name: asNullableString(record, 'name', 'projection.plant'),
  }
}

function parseAnchor(value: unknown, what: string): ProcessAnchorDto {
  const record = asRecord(value, what)
  return {
    index: asNumber(record, 'index', what),
    x: asNumber(record, 'x', what),
    y: asNumber(record, 'y', what),
  }
}

function parseStep(value: unknown, what: string): ProcessStepDto {
  const record = asRecord(value, what)
  const kind = asString(record, 'kind', what)
  if (kind !== 'process-step') {
    throw new ProjectionContractError(`${what}.kind must be 'process-step'`)
  }
  return {
    kind,
    id: asString(record, 'id', what),
    name: asNullableString(record, 'name', what),
    function: asString(record, 'function', what),
    symbol_role: asString(record, 'symbol_role', what),
    ports: asStringArray(record, 'ports', what),
    x: asNumber(record, 'x', what),
    y: asNumber(record, 'y', what),
    in_anchors: asArray(record['in_anchors'], `${what}.in_anchors`).map((anchor, index) =>
      parseAnchor(anchor, `${what}.in_anchors[${index}]`),
    ),
    out_anchors: asArray(record['out_anchors'], `${what}.out_anchors`).map((anchor, index) =>
      parseAnchor(anchor, `${what}.out_anchors[${index}]`),
    ),
  }
}

function parseEndpoint(value: unknown, what: string): ProcessStreamEndpointDto {
  const record = asRecord(value, what)
  return {
    step: asString(record, 'step', what),
    port: asString(record, 'port', what),
    anchor: asNumber(record, 'anchor', what),
  }
}

function parseStream(value: unknown, what: string): ProcessStreamDto {
  const record = asRecord(value, what)
  const kind = asString(record, 'kind', what)
  if (kind !== 'process-stream') {
    throw new ProjectionContractError(`${what}.kind must be 'process-stream'`)
  }
  return {
    kind,
    id: asString(record, 'id', what),
    name: asNullableString(record, 'name', what),
    source: parseEndpoint(record['source'], `${what}.source`),
    target: parseEndpoint(record['target'], `${what}.target`),
    is_feedback: asBoolean(record, 'is_feedback', what),
  }
}

function parseProjection(value: unknown): ProcessPfdProjectionDto {
  const record = asRecord(value, 'projection')
  const validation = parseValidationStatus(record['validation'])
  return {
    plant: parsePlantRef(record['plant']),
    symbol_pack: asString(record, 'symbol_pack', 'projection'),
    symbol_size: asNumber(record, 'symbol_size', 'projection'),
    validation,
    steps: asArray(record['steps'], 'projection.steps').map((step, index) =>
      parseStep(step, `projection.steps[${index}]`),
    ),
    streams: asArray(record['streams'], 'projection.streams').map((stream, index) =>
      parseStream(stream, `projection.streams[${index}]`),
    ),
  }
}

/** Narrow an unknown `/api/projection` payload to the DTO contract. */
export function parseProjectionEnvelope(raw: unknown): ProjectionEnvelope {
  const record = asRecord(raw, 'projection response')
  const validation = parseValidationStatus(record['validation'])
  const errorValue = record['error']
  const projectionValue = record['projection']
  return {
    validation,
    error: errorValue === undefined ? null : asString(record, 'error', 'projection response'),
    projection:
      projectionValue === null || projectionValue === undefined
        ? null
        : parseProjection(projectionValue),
  }
}

/** Load the Process/PFD projection from the local DeepPlant boundary. */
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

