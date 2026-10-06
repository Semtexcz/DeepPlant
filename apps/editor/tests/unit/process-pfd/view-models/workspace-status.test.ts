import { describe, expect, it } from 'vitest'

import { workspaceStatus } from '../../../../src/process-pfd/view-models/workspace-status'
import { EMPTY_WORKSPACE, LOADED_WORKSPACE } from '../../../fixtures/process-pfd'

const VALID = { valid: true, message: 'Valid' }

describe('workspace status mapping', () => {
  it('reports loading before the boundary has answered', () => {
    expect(workspaceStatus(EMPTY_WORKSPACE, null, null, true)).toEqual({
      text: 'Loading validation status…',
      tone: 'neutral',
    })
  })

  it('reports a neutral no-project state for an empty workspace', () => {
    expect(workspaceStatus(EMPTY_WORKSPACE, null, null, false)).toEqual({
      text: 'No project open',
      tone: 'neutral',
    })
  })

  it('reports semantic validity for a loaded project', () => {
    expect(workspaceStatus(LOADED_WORKSPACE, VALID, null, false)).toEqual({
      text: 'Valid',
      tone: 'valid',
    })
  })

  it('reports an invalid semantic model for a loaded project', () => {
    expect(
      workspaceStatus(LOADED_WORKSPACE, { valid: false, message: 'duplicate step id' }, null, false),
    ).toEqual({ text: 'Invalid: duplicate step id', tone: 'invalid' })
  })

  it('keeps a loaded project valid when only its Process/PFD view cannot be produced', () => {
    // The projection error is a separate canvas notice; the model itself is valid.
    expect(workspaceStatus(LOADED_WORKSPACE, VALID, 'no process model to project', false)).toEqual({
      text: 'Valid',
      tone: 'valid',
    })
  })

  it('surfaces a genuine boundary error instead of claiming an empty workspace', () => {
    expect(workspaceStatus(EMPTY_WORKSPACE, null, 'cannot reach the boundary', false)).toEqual({
      text: 'cannot reach the boundary',
      tone: 'invalid',
    })
  })
})