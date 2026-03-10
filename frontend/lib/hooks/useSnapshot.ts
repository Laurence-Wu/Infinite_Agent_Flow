import useSWR from 'swr'
import type { Snapshot } from '@/lib/types'

const fetcher = (url: string) => fetch(url).then(r => r.json())

/** Polls /api/status every 3 seconds and returns the engine snapshot. */
export function useSnapshot() {
  const { data, error } = useSWR<Snapshot>('/api/status', fetcher, {
    refreshInterval: 3000,
  })
  return {
    snapshot:  data ?? null,
    isLoading: !data && !error,
  }
}
