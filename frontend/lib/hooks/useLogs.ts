import useSWR from 'swr'

const fetcher = (url: string) => fetch(url).then(r => r.json())

/** Polls /api/logs every 2 seconds and returns recent log lines. */
export function useLogs() {
  const { data, error } = useSWR<{ logs: string[] }>('/api/logs', fetcher, {
    refreshInterval: 2000,
  })

  return {
    logs: data?.logs ?? [],
    isLoading: !data && !error,
    isError: error,
  }
}
