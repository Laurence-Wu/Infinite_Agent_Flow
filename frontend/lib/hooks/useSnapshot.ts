import useSWR from 'swr'
import type { Snapshot } from '@/lib/types'

const fetcher = (url: string) => fetch(url).then(r => r.json())

/**
 * Polls per-dealer snapshot every 3 seconds.
 * Uses /api/dealer/<id> when agentId is provided (returns per-dealer log_lines, history, etc.)
 * Falls back to /api/status for the primary dealer.
 */
export function useSnapshot(agentId?: string) {
  const url = agentId ? `/api/dealer/${encodeURIComponent(agentId)}` : '/api/status'
  const { data, error } = useSWR<Snapshot>(url, fetcher, {
    refreshInterval: 3000,
  })
  return {
    snapshot:  data ?? null,
    isLoading: !data && !error,
    error,
  }
}
