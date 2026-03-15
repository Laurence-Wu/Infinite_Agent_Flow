import useSWR from 'swr'
import type { HistoryEntry, Snapshot } from '@/lib/types'
import { useDealers } from '@/lib/hooks/useDealers'

async function fetchAllHistory(dealerIds: string[]): Promise<(HistoryEntry & { dealer_id: string })[]> {
  const results = await Promise.all(
    dealerIds.map(id =>
      fetch(`/api/status?agent_id=${encodeURIComponent(id)}`)
        .then(r => r.ok ? r.json() : null)
        .then((snap: Snapshot | null) =>
          (snap?.history ?? []).map(h => ({ ...h, dealer_id: id }))
        )
        .catch(() => [])
    )
  )
  const merged = results.flat()
  // Sort by completed_at descending (most recent first)
  merged.sort((a, b) => b.completed_at.localeCompare(a.completed_at))
  return merged
}

/** Aggregates completed task history across all running dealers. */
export function useAllHistory() {
  const { dealers } = useDealers()
  const ids = dealers.map(d => d.dealer_id)

  const { data, error } = useSWR<(HistoryEntry & { dealer_id: string })[]>(
    ids.length > 0 ? ['all-history', ...ids] : null,
    () => fetchAllHistory(ids),
    { refreshInterval: 5000 }
  )

  return {
    history: data ?? [],
    isLoading: !data && !error,
  }
}
