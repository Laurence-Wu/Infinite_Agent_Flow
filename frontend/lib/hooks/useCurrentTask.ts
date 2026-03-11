import useSWR from 'swr'

const fetcher = (url: string) => fetch(url).then(r => (r.ok ? r.text() : Promise.resolve(null)))

/** Polls /api/current-task every 3 seconds and returns raw markdown content. */
export function useCurrentTask() {
  const { data, error, mutate } = useSWR<string | null>('/api/current-task', fetcher, {
    refreshInterval: 3000,
  })

  return {
    currentTask: data ?? null,
    isLoading: !data && !error,
    isError: error,
    refresh: mutate,
  }
}
