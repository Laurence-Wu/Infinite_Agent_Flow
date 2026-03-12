'use client'

import useSWR from 'swr'
import type { SessionStatus } from '@/lib/types'

const fetcher = (url: string) => fetch(url).then(r => r.json())

const DEFAULT_SESSION: SessionStatus = {
  alive: false,
  starting: false,
  session_name: '',
  agent_command: '',
  workspace: '',
  pane_lines: [],
}

/** Polls /api/session every 5 seconds and returns tmux session status. */
export function useSession() {
  const { data, error, mutate } = useSWR<SessionStatus>('/api/session', fetcher, {
    refreshInterval: 5000,
  })

  return {
    session: data ?? DEFAULT_SESSION,
    isLoading: !data && !error,
    isError: !!error,
    refresh: mutate,
  }
}
