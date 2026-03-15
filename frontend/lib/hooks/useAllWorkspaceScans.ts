import useSWR from 'swr'
import type { WorkspaceScanEntry } from '@/lib/types'
import { useDealers } from '@/lib/hooks/useDealers'

async function fetchAllScans(dealerIds: string[]): Promise<WorkspaceScanEntry[]> {
  const results = await Promise.all(
    dealerIds.map(id =>
      fetch(`/api/agent/${encodeURIComponent(id)}/workspace-scan`)
        .then(r => r.ok ? r.json() : { files: [] })
        .then((d: { files?: WorkspaceScanEntry[] }) => (d.files ?? []).map(f => ({ ...f, _dealer: id })))
        .catch(() => [])
    )
  )
  // Merge and dedupe by path+dealer; sort newest first
  const merged = results.flat() as (WorkspaceScanEntry & { _dealer: string })[]
  merged.sort((a, b) => new Date(b.mtime).getTime() - new Date(a.mtime).getTime())
  return merged
}

/** Aggregates workspace scan files across all running dealers. */
export function useAllWorkspaceScans() {
  const { dealers } = useDealers()
  const ids = dealers.map(d => d.dealer_id)

  const { data, mutate } = useSWR<(WorkspaceScanEntry & { _dealer?: string })[]>(
    ids.length > 0 ? ['all-workspace-scans', ...ids] : null,
    () => fetchAllScans(ids),
    { refreshInterval: 3000 }
  )

  return { files: data ?? [], mutate }
}
