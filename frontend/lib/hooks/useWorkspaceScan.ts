import useSWR from 'swr'
import type { WorkspaceScan } from '@/lib/types'

const fetcher = (url: string) => fetch(url).then(r => r.json())

/** Polls /api/workspace-scan every 3 seconds and returns recently modified files. */
export function useWorkspaceScan() {
  const { data } = useSWR<WorkspaceScan>('/api/workspace-scan', fetcher, {
    refreshInterval: 3000,
  })
  return { files: data?.files ?? [] }
}
