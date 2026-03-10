import useSWR from 'swr'

const fetcher = (url: string) =>
  fetch(url).then(r => (r.ok ? r.text() : Promise.resolve(null)))

/** Polls /api/current-task every 3 seconds and returns the raw markdown string. */
export function useTaskMarkdown() {
  const { data } = useSWR<string | null>('/api/current-task', fetcher, {
    refreshInterval: 3000,
  })
  return { markdown: data ?? '' }
}
