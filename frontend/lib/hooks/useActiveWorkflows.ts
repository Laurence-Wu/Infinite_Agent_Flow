import useSWR from 'swr'
import type { ActiveWorkflows } from '@/lib/types'

const fetcher = (url: string) => fetch(url).then(r => r.json())

/** Polls /api/status every 3 seconds and returns only the active workflows data. */
export function useActiveWorkflows() {
  const { data, error } = useSWR<{ active_workflows: ActiveWorkflows }>('/api/status', fetcher, {
    refreshInterval: 3000,
  })
  
  return {
    activeWorkflows: data?.active_workflows ?? {},
    isLoading: !data && !error,
    isError: error,
  }
}