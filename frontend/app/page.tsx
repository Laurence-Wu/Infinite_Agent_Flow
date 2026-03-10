'use client'

import { useSnapshot }      from '@/lib/hooks/useSnapshot'
import { useTaskMarkdown }  from '@/lib/hooks/useTaskMarkdown'
import { useWorkflows }     from '@/lib/hooks/useWorkflows'
import { useWorkspaceScan } from '@/lib/hooks/useWorkspaceScan'
import Header        from '@/components/Header'
import StatsRow      from '@/components/StatsRow'
import ProgressPanel from '@/components/ProgressPanel'
import TaskPreview   from '@/components/TaskPreview'
import LogTerminal   from '@/components/LogTerminal'
import HistoryFeed   from '@/components/HistoryFeed'
import WorkflowList  from '@/components/WorkflowList'
import WorkspaceScan from '@/components/WorkspaceScan'

export default function Dashboard() {
  const { snapshot }  = useSnapshot()
  const { markdown }  = useTaskMarkdown()
  const { workflows } = useWorkflows()
  const { files }     = useWorkspaceScan()

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
            <TaskPreview markdown={markdown} />
          </div>
          <div>
            <LogTerminal lines={snapshot.log_lines ?? []} />
          </div>
        </div>

        {/* Workspace file activity */}
        <WorkspaceScan files={files} />

        {/* Workflows + history */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <WorkflowList workflows={workflows} />
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
