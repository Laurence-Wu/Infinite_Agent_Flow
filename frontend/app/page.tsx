'use client'

import useSWR from 'swr'
import type { Snapshot, Workflow } from '@/lib/types'
import Header from '@/components/Header'
import StatsRow from '@/components/StatsRow'
import ProgressPanel from '@/components/ProgressPanel'
import TaskPreview from '@/components/TaskPreview'
import LogTerminal from '@/components/LogTerminal'
import HistoryFeed from '@/components/HistoryFeed'
import WorkflowList from '@/components/WorkflowList'

const jsonFetcher = (url: string) => fetch(url).then(r => r.json())
const textFetcher = (url: string) =>
  fetch(url).then(r => (r.ok ? r.text() : Promise.resolve(null)))

export default function Dashboard() {
  const { data: snapshot } = useSWR<Snapshot>('/api/status', jsonFetcher, {
    refreshInterval: 3000,
  })
  const { data: taskMd } = useSWR<string | null>('/api/current-task', textFetcher, {
    refreshInterval: 3000,
  })
  const { data: workflows } = useSWR<Workflow[]>('/api/workflows', jsonFetcher, {
    refreshInterval: 30_000,
  })

  if (!snapshot) {
    return (
      <div className="flex items-center justify-center min-h-screen text-slate-500">
        Connecting to engine…
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      <Header snapshot={snapshot} />

      <main className="max-w-7xl mx-auto px-6 py-6 space-y-6">
        {/* Stats row */}
        <StatsRow snapshot={snapshot} />

        {/* Progress bar + card info */}
        <ProgressPanel snapshot={snapshot} />

        {/* Task preview + log terminal */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <TaskPreview markdown={taskMd ?? ''} />
          </div>
          <div>
            <LogTerminal lines={snapshot.log_lines ?? []} />
          </div>
        </div>

        {/* Workflows + history */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <WorkflowList workflows={workflows ?? []} />
          <div className="lg:col-span-2">
            <HistoryFeed history={snapshot.history ?? []} />
          </div>
        </div>
      </main>

      <footer className="border-t border-slate-700/30 mt-8">
        <div className="max-w-7xl mx-auto px-6 py-3 text-center text-xs text-slate-600">
          Infinite Agent Flow &middot; Next.js UI &middot; Flask API on :5000
        </div>
      </footer>
    </div>
  )
}
