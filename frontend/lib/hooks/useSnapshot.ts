import useSWR from 'swr'
import type { Snapshot } from '@/lib/types'

const fetcher = (url: string) => fetch(url).then(r => r.json())

/** 
 * Polls /api/status every 3 seconds and returns the engine snapshot. 
 * If agentId is provided, it fetches that specific agent's state.
 */
export function useSnapshot(agentId?: string) {
  const url = agentId ? `/api/status?agent_id=${encodeURIComponent(agentId)}` : '/api/status'
  const { data, error } = useSWR<Snapshot>(url, fetcher, {
    refreshInterval: 3000,
  })
  return {
    snapshot:  data ?? null,
    isLoading: !data && !error,
    error,
  }
}
