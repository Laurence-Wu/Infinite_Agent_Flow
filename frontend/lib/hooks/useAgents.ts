import useSWR from 'swr'
import type { Snapshot } from '@/lib/types'

const fetcher = (url: string) => fetch(url).then(r => r.json())

/** 
 * Returns a map of all agents reporting to the server.
 */
export function useAgents() {
  const { data, error } = useSWR<Record<string, Snapshot>>('/api/agents', fetcher, {
    refreshInterval: 5000,
  })
  
  return {
    agents: data ?? {},
    isLoading: !data && !error,
    error,
  }
}
