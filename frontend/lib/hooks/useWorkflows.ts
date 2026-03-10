import useSWR from 'swr'
import type { Workflow } from '@/lib/types'

const fetcher = (url: string) => fetch(url).then(r => r.json())

/** Polls /api/workflows every 30 seconds and returns the available workflow list. */
export function useWorkflows() {
  const { data } = useSWR<Workflow[]>('/api/workflows', fetcher, {
    refreshInterval: 30_000,
  })
  return { workflows: data ?? [] }
}
