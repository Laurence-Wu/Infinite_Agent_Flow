import useSWR from 'swr'
import type { HistoryEntry } from '@/lib/types'

const fetcher = (url: string) => fetch(url).then(r => r.json())

/** Polls /api/history every 5 seconds and returns completed task history. */
export function useHistory() {
  const { data, error } = useSWR<HistoryEntry[]>('/api/history', fetcher, {
    refreshInterval: 5000,
  })

  return {
    history: data ?? [],
    isLoading: !data && !error,
    isError: error,
  }
}
