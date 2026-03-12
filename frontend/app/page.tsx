'use client'

import { useState, useEffect } from 'react'
import { useAgents }        from '@/lib/hooks/useAgents'
import { useSnapshot }      from '@/lib/hooks/useSnapshot'
import { useTaskMarkdown }  from '@/lib/hooks/useTaskMarkdown'
import { useWorkflows }     from '@/lib/hooks/useWorkflows'
import { useWorkspaceScan } from '@/lib/hooks/useWorkspaceScan'
import Header        from '@/components/Header'
import AgentGrid     from '@/components/AgentGrid'
import TaskPreview   from '@/components/TaskPreview'
import WorkspaceScan from '@/components/WorkspaceScan'
import WorkflowList  from '@/components/WorkflowList'
import HistoryFeed   from '@/components/HistoryFeed'

export default function Dashboard() {
  const { agents }    = useAgents()
  const { markdown }  = useTaskMarkdown()
  const { workflows } = useWorkflows()
  const { files }     = useWorkspaceScan()

  const [activeAgentId, setActiveAgentId] = useState<string | null>(null)

  // Auto-select: prefer the first running agent, else first in list
  useEffect(() => {
    if (agents.length === 0) return
    const ids = agents.map(a => a.agent_id)
    if (!activeAgentId || !ids.includes(activeAgentId)) {
      const running = agents.find(a => a.status === 'running')
      setActiveAgentId(running?.agent_id ?? agents[0].agent_id)
    }
  }, [agents, activeAgentId])

  const activeAgent     = agents.find(a => a.agent_id === activeAgentId) ?? null
  const isLocalSelected = activeAgentId === 'default'

  // Fetch active agent snapshot for the bottom HistoryFeed
  // SWR deduplicates: if the expanded AgentCard fetches the same URL, zero extra requests
  const { snapshot: activeSnapshot } = useSnapshot(activeAgentId ?? undefined)

  return (
    <div className="min-h-screen">
      <Header agent={activeAgent} agentCount={agents.length} />

      <main className="max-w-7xl mx-auto px-6 py-6 space-y-6">

        {/* Primary: all agents as expandable cards */}
        <AgentGrid
          agents={agents}
          selectedId={activeAgentId}
          onSelect={setActiveAgentId}
        />

        {/* Secondary: local-workspace panels (only for the default local agent) */}
        {isLocalSelected && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <TaskPreview markdown={markdown} />
            </div>
            <WorkspaceScan files={files} />
          </div>
        )}

        {/* Bottom: workflow registry + completed history */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <WorkflowList workflows={workflows} agents={agents} />
          <div className="lg:col-span-2">
            <HistoryFeed history={activeSnapshot?.history ?? []} />
          </div>
        </div>
      </main>

      <footer className="border-t border-slate-700/30 mt-8">
        <div className="max-w-7xl mx-auto px-6 py-3 text-center text-xs text-slate-600">
          Infinite Agent Flow · Multi-Agent Dashboard · Flask API :5000
        </div>
      </footer>
    </div>
  )
}
