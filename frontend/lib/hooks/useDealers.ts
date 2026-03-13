import useSWR from 'swr'
import type { DealerEntry } from '@/lib/types'

const fetcher = (url: string) => fetch(url).then(r => r.json())

/**
 * Returns the list of all Card Dealers reporting to the server.
 * Polls every 3 seconds to keep the dashboard fresh.
 */
export function useDealers() {
  const { data, error, mutate } = useSWR<DealerEntry[]>('/api/dealers', fetcher, {
    refreshInterval: 3000,
  })

  return {
    dealers: data ?? [],
    isLoading: !data && !error,
    error,
    mutate,
  }
}
