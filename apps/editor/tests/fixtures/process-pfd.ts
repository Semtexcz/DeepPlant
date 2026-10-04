import type { ProcessPfdProjectionDto, ProcessStepDto, ProcessStreamDto } from '../../src/process-pfd/dto'

/**
 * Test-only fixture data for the editor frontend tests.
 *
 * It is not imported by the application, so it never enters the production
 * bundle. The shape mirrors the DeepPlant transport DTOs; the canonical
 * acceptance workload is still the Python projection, which the Python tests
 * exercise directly.
 */

export const PUMP_STEP: ProcessStepDto = {
  kind: 'process-step',
  id: 'PS-pump',
  name: 'Feed Pumping',
  function: 'pumping',
  symbol_role: 'pump',
  ports: ['suction', 'discharge'],
  x: 40,
  y: 40,
  in_anchors: [{ index: 0, x: 0, y: 50 }],
  out_anchors: [{ index: 0, x: 100, y: 50 }],
}

export const MIX_STEP: ProcessStepDto = {
  kind: 'process-step',
  id: 'PS-mix',
  name: null,
  function: 'mixing',
  symbol_role: 'mixing',
  ports: ['in_fresh', 'in_recycle', 'out_mixed'],
  x: 40,
  y: 220,
  in_anchors: [
    { index: 0, x: 0, y: 33 },
    { index: 1, x: 0, y: 67 },
  ],
  out_anchors: [{ index: 0, x: 100, y: 50 }],
}

export const PUMP_DISCHARGE_STREAM: ProcessStreamDto = {
  kind: 'process-stream',
  id: 'S-004',
  name: 'Pump Discharge',
  source: { step: 'PS-pump', port: 'discharge', anchor: 0 },
  target: { step: 'PS-mix', port: 'in_recycle', anchor: 1 },
  is_feedback: false,
}

export const RECYCLE_STREAM: ProcessStreamDto = {
  kind: 'process-stream',
  id: 'S-002',
  name: 'Recycle',
  source: { step: 'PS-pump', port: 'discharge', anchor: 0 },
  target: { step: 'PS-mix', port: 'in_fresh', anchor: 0 },
  is_feedback: true,
}

export const SYMBOL_SIZE = 100

export const PROJECTION_FIXTURE: ProcessPfdProjectionDto = {
  plant: { id: 'demo', name: 'Fixture Plant' },
  symbol_pack: 'basic',
  symbol_size: SYMBOL_SIZE,
  validation: { valid: true, message: 'Valid' },
  steps: [PUMP_STEP, MIX_STEP],
  streams: [PUMP_DISCHARGE_STREAM, RECYCLE_STREAM],
}
