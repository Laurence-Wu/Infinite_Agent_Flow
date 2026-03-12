import useSWR from 'swr'
import type { WorkspaceScan } from '@/lib/types'

const fetcher = (url: string) => fetch(url).then(r => r.json())

/**
 * Polls workspace-scan every 3 seconds.
 * When agentId is provided, calls /api/agent/<id>/workspace-scan (per-agent).
 * Otherwise calls /api/workspace-scan (primary workspace).
 */
export function useWorkspaceScan(agentId?: string) {
  const url = agentId
    ? `/api/agent/${agentId}/workspace-scan`
    : '/api/workspace-scan'
  const { data } = useSWR<WorkspaceScan>(url, fetcher, {
    refreshInterval: 3000,
  })
  return { files: data?.files ?? [] }
}
