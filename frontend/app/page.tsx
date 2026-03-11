'use client'

import { useState, useEffect } from 'react'
import { useSnapshot }      from '@/lib/hooks/useSnapshot'
import { useAgents }        from '@/lib/hooks/useAgents'
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
import AgentSwitcher from '@/components/AgentSwitcher'

export default function Dashboard() {
  const [activeAgentId, setActiveAgentId] = useState<string>('default')
  const { agents } = useAgents()
  
  // Update activeAgentId if current one disappears, or if default is missing but others exist
  useEffect(() => {
    const ids = agents.map(a => a.agent_id)
    if (ids.length > 0 && !ids.includes(activeAgentId)) {
      setActiveAgentId(ids[0])
    }
  }, [agents, activeAgentId])

  const { snapshot }  = useSnapshot(activeAgentId)
  const { markdown }  = useTaskMarkdown()
  const { workflows } = useWorkflows()
  const { files }     = useWorkspaceScan()

  if (!snapshot) {
    return (
      <div className="flex items-center justify-center min-h-screen text-slate-500">
        Connecting to engine\u2026
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      <Header snapshot={snapshot} />

      <main className="max-w-7xl mx-auto px-6 py-6 space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-3 space-y-6">
            {/* Stats row */}
            <StatsRow snapshot={snapshot} />

            {/* Progress bar + card info */}
            <ProgressPanel snapshot={snapshot} />
          </div>
          
          <div className="lg:col-span-1">
            <AgentSwitcher 
              agents={agents} 
              activeId={activeAgentId} 
              onSelect={setActiveAgentId} 
            />
          </div>
        </div>

        {/* Task preview + log terminal */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <TaskPreview markdown={markdown} />
            {activeAgentId !== 'default' && (
              <div className="mt-2 text-xs text-slate-500 italic px-2">
                Note: Task preview and Workspace activity are only available for the local agent.
              </div>
            )}
          </div>
          <div>
            <LogTerminal lines={snapshot.log_lines ?? []} />
          </div>
        </div>

        {/* Workspace file activity - only for local */}
        {activeAgentId === 'default' && <WorkspaceScan files={files} />}

        {/* Workflows + history */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <WorkflowList workflows={workflows} agents={agents} />
          <div className="lg:col-span-2">
            <HistoryFeed history={snapshot.history ?? []} />
          </div>
        </div>
      </main>

      <footer className="border-t border-slate-700/30 mt-8">
        <div className="max-w-7xl mx-auto px-6 py-3 text-center text-xs text-slate-600">
          Infinite Agent Flow &middot; Multi-Agent Dashboard &middot; Flask API on :5000
        </div>
      </footer>
    </div>
  )
}
