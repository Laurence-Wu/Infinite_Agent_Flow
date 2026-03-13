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

/** Polls /api/agent every 5 seconds and returns AI agent (tmux) status. */
export function useAgentSession() {
  const { data, error, mutate } = useSWR<AgentStatus>('/api/agent', fetcher, {
    refreshInterval: 5000,
  })

  return {
    agentSession: data ?? DEFAULT_STATUS,
    isLoading: !data && !error,
    isError: !!error,
    refresh: mutate,
  }
}
