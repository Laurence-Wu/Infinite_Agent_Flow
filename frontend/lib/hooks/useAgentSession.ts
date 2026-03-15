'use client'

import useSWR from 'swr'
import type { AgentStatus } from '@/lib/types'

const fetcher = (url: string) => fetch(url).then(r => r.json())

const DEFAULT_STATUS: AgentStatus = {
  alive: false,
  starting: false,
  session_name: '',
  agent_command: '',
  workspace: '',
  pane_lines: [],
}

/**
 * Polls per-dealer tmux session status every 5 seconds.
 * Uses /api/dealer/<dealerId>/session when dealerId is provided,
 * falls back to /api/agent for the primary agent.
 */
export function useAgentSession(dealerId?: string) {
  const url = dealerId ? `/api/dealer/${encodeURIComponent(dealerId)}/session` : '/api/agent'
  const { data, error, mutate } = useSWR<AgentStatus>(url, fetcher, {
    refreshInterval: 5000,
  })

  return {
    agentSession: data ?? DEFAULT_STATUS,
    isLoading: !data && !error,
    isError: !!error,
    refresh: mutate,
  }
}
