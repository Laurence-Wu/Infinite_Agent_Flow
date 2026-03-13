'use client'

import { useCallback } from 'react'

/**
 * Provides action callbacks for interacting with the engine.
 *
 * Dealer methods  — control the Card Dealer workflow runner:
 *   pauseDealer / resumeDealer / stopDealer / dealNextFor / restartDealer
 *
 * Agent methods  — control the AI agent tmux process:
 *   startAgent / stopAgent / restartAgent
 */
export function useEngineActions() {

  // ── Card Dealer controls ──────────────────────────────────────────────

  const pauseDealer = useCallback(async (dealerId = 'default') => {
    const response = await fetch(`/api/dealer/${dealerId}/pause`, { method: 'POST' })
    if (!response.ok && response.status !== 503) throw new Error('Failed to pause dealer')
    return response.json().catch(() => ({ ok: false }))
  }, [])

  const resumeDealer = useCallback(async (dealerId = 'default') => {
    const response = await fetch(`/api/dealer/${dealerId}/resume`, { method: 'POST' })
    if (!response.ok && response.status !== 503) throw new Error('Failed to resume dealer')
    return response.json().catch(() => ({ ok: false }))
  }, [])

  const stopDealer = useCallback(async (dealerId = 'default') => {
    const response = await fetch(`/api/dealer/${dealerId}/stop`, { method: 'POST' })
    if (!response.ok && response.status !== 503) throw new Error('Failed to stop dealer')
    return response.json().catch(() => ({ ok: false }))
  }, [])

  const dealNextFor = useCallback(async (dealerId = 'default') => {
    const response = await fetch(`/api/dealer/${dealerId}/deal`, { method: 'POST' })
    if (!response.ok) throw new Error('Failed to deal next card')
    return response.json()
  }, [])

  const dealNext = useCallback(async () => dealNextFor('default'), [dealNextFor])

  const restartDealer = useCallback(async (dealerId = 'default') => {
    const response = await fetch(`/api/dealer/${dealerId}/restart`, { method: 'POST' })
    if (!response.ok) throw new Error('Failed to restart dealer')
    return response.json()
  }, [])

  /** Launch a new dealer on a given workspace + workflow. */
  const startDealer = useCallback(async (workspace: string, workflow: string, version = 'v1') => {
    const response = await fetch('/api/dealers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ workspace, workflow, version }),
    })
    if (!response.ok) throw new Error('Failed to start dealer')
    return response.json()
  }, [])

  const refreshWorkspace = useCallback(async () => {
    const response = await fetch('/api/workspace-scan')
    if (!response.ok) throw new Error('Failed to refresh workspace')
    return response.json()
  }, [])

  // ── AI Agent (tmux) controls ──────────────────────────────────────────

  const startAgent = useCallback(async () => {
    const response = await fetch('/api/agent/start', { method: 'POST' })
    if (!response.ok) throw new Error('Failed to start agent')
    return response.json()
  }, [])

  const stopAgent = useCallback(async () => {
    const response = await fetch('/api/agent/stop', { method: 'POST' })
    if (!response.ok) throw new Error('Failed to stop agent')
    return response.json()
  }, [])

  const pauseAgent = useCallback(async () => {
    const response = await fetch('/api/agent/pause', { method: 'POST' })
    if (!response.ok) throw new Error('Failed to pause agent')
    return response.json()
  }, [])

  const restartAgent = useCallback(async () => {
    const response = await fetch('/api/agent/restart', { method: 'POST' })
    if (!response.ok) throw new Error('Failed to restart agent')
    return response.json()
  }, [])

  // ── Backward-compat aliases ───────────────────────────────────────────

  const pauseWorkflow  = pauseDealer
  const resumeWorkflow = resumeDealer
  const stopWorkflow   = stopDealer
  const startSession   = startAgent
  const stopSession    = stopAgent
  const restartSession = restartAgent

  return {
    // Dealer
    pauseDealer,
    resumeDealer,
    stopDealer,
    dealNext,
    dealNextFor,
    restartDealer,
    startDealer,
    refreshWorkspace,
    // Agent (tmux)
    startAgent,
    stopAgent,
    pauseAgent,
    restartAgent,
    // Aliases
    pauseWorkflow,
    resumeWorkflow,
    stopWorkflow,
    startSession,
    stopSession,
    restartSession,
  }
}
