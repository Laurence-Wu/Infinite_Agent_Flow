'use client'

import { useCallback } from 'react'

/**
 * Provides action callbacks for interacting with the engine.
 * These actions trigger backend operations via API calls.
 */
export function useEngineActions() {
  /**
   * Manually trigger the engine to deal the next card.
   * Useful for stepping through workflows interactively.
   */
  const dealNext = useCallback(async () => {
    try {
      const response = await fetch('/api/deal-next', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
      if (!response.ok) {
        throw new Error('Failed to deal next card')
      }
      return await response.json()
    } catch (error) {
      console.error('Error dealing next card:', error)
      throw error
    }
  }, [])

  /** Pause a specific agent's workflow (defaults to agent_0). */
  const pauseWorkflow = useCallback(async (agentId = 'agent_0') => {
    try {
      const response = await fetch('/api/workflow/pause', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_id: agentId }),
      })
      if (!response.ok) throw new Error('Failed to pause workflow')
      return await response.json()
    } catch (error) {
      console.error('Error pausing workflow:', error)
      throw error
    }
  }, [])

  /** Resume a paused agent's workflow (defaults to agent_0). */
  const resumeWorkflow = useCallback(async (agentId = 'agent_0') => {
    try {
      const response = await fetch('/api/workflow/resume', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_id: agentId }),
      })
      if (!response.ok) throw new Error('Failed to resume workflow')
      return await response.json()
    } catch (error) {
      console.error('Error resuming workflow:', error)
      throw error
    }
  }, [])

  /** Stop a specific agent's workflow (defaults to agent_0). */
  const stopWorkflow = useCallback(async (agentId = 'agent_0') => {
    try {
      const response = await fetch('/api/workflow/stop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_id: agentId }),
      })
      if (!response.ok) throw new Error('Failed to stop workflow')
      return await response.json()
    } catch (error) {
      console.error('Error stopping workflow:', error)
      throw error
    }
  }, [])

  /** Deal next card for a specific agent (defaults to agent_0). */
  const dealNextFor = useCallback(async (agentId = 'agent_0') => {
    try {
      const response = await fetch('/api/deal-next', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_id: agentId }),
      })
      if (!response.ok) throw new Error('Failed to deal next card')
      return await response.json()
    } catch (error) {
      console.error('Error dealing next card:', error)
      throw error
    }
  }, [])

  /** Launch a new agent on a given workspace + workflow. */
  const startAgent = useCallback(async (workspace: string, workflow: string, version = 'v1') => {
    try {
      const response = await fetch('/api/agent/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workspace, workflow, version }),
      })
      if (!response.ok) throw new Error('Failed to start agent')
      return await response.json()
    } catch (error) {
      console.error('Error starting agent:', error)
      throw error
    }
  }, [])

  /** Refresh the workspace scan to detect new files. */
  const refreshWorkspace = useCallback(async () => {
    try {
      const response = await fetch('/api/workspace-scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
      if (!response.ok) throw new Error('Failed to refresh workspace')
      return await response.json()
    } catch (error) {
      console.error('Error refreshing workspace:', error)
      throw error
    }
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
