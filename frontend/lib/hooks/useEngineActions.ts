'use client'

import { useCallback } from 'react'

/**
 * Provides action callbacks for interacting with the engine.
 * Uses RESTful /api/agent/<id>/... routes with backward-compat aliases.
 */
export function useEngineActions() {

  /** Pause a specific agent's workflow. */
  const pauseWorkflow = useCallback(async (agentId = 'default') => {
    const response = await fetch(`/api/agent/${agentId}/pause`, { method: 'POST' })
    if (!response.ok) throw new Error('Failed to pause workflow')
    return response.json()
  }, [])

  /** Resume a paused agent's workflow. */
  const resumeWorkflow = useCallback(async (agentId = 'default') => {
    const response = await fetch(`/api/agent/${agentId}/resume`, { method: 'POST' })
    if (!response.ok) throw new Error('Failed to resume workflow')
    return response.json()
  }, [])

  /** Stop a specific agent's workflow permanently. */
  const stopWorkflow = useCallback(async (agentId = 'default') => {
    const response = await fetch(`/api/agent/${agentId}/stop`, { method: 'POST' })
    if (!response.ok) throw new Error('Failed to stop workflow')
    return response.json()
  }, [])

  /** Manually advance one card for a specific agent. */
  const dealNextFor = useCallback(async (agentId = 'default') => {
    const response = await fetch(`/api/agent/${agentId}/deal`, { method: 'POST' })
    if (!response.ok) throw new Error('Failed to deal next card')
    return response.json()
  }, [])

  /** Convenience alias for the primary agent. */
  const dealNext = useCallback(async () => dealNextFor('default'), [dealNextFor])

  /** Launch a new agent on a given workspace + workflow. */
  const startAgent = useCallback(async (workspace: string, workflow: string, version = 'v1') => {
    const response = await fetch('/api/agents', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ workspace, workflow, version }),
    })
    if (!response.ok) throw new Error('Failed to start agent')
    return response.json()
  }, [])

  /** Refresh the workspace scan to detect new files. */
  const refreshWorkspace = useCallback(async () => {
    const response = await fetch('/api/workspace-scan')
    if (!response.ok) throw new Error('Failed to refresh workspace')
    return response.json()
  }, [])

  return {
    dealNext,
    dealNextFor,
    pauseWorkflow,
    resumeWorkflow,
    stopWorkflow,
    startAgent,
    refreshWorkspace,
  }
}
