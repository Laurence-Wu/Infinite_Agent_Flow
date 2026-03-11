import useSWR from 'swr'
import type { AgentEntry } from '@/lib/types'

const fetcher = (url: string) => fetch(url).then(r => r.json())

/**
 * Returns the list of all agents reporting to the server.
 * Polls every 3 seconds to keep the dashboard fresh.
 */
export function useAgents() {
  const { data, error, mutate } = useSWR<AgentEntry[]>('/api/agents', fetcher, {
    refreshInterval: 3000,
  })

  return {
    agents: data ?? [],
    isLoading: !data && !error,
    error,
    mutate,
  }
}
