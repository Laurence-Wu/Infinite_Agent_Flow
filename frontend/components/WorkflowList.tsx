"use client"

import { useMemo, useState } from 'react'
import { GitBranch, Users } from 'lucide-react'
import ExpandableCard from '@/components/ExpandableCard'
import type { Workflow, AgentEntry } from '@/lib/types'
import { groupWorkflows, getStatusCounts } from '@/lib/workflowUtils'

interface WorkflowListProps {
  workflows: Workflow[]
  agents?: AgentEntry[]
}

export default function WorkflowList({ workflows, agents = [] }: WorkflowListProps) {
  const groups = useMemo(() => groupWorkflows(workflows, agents), [workflows, agents])

  const [expandedKeys, setExpandedKeys] = useState<Record<string, boolean>>({})

  const isExpanded = (key: string) => {
    if (groups.length === 1) return true
    return !!expandedKeys[key]
  }

  const toggleExpanded = (key: string, next: boolean) => {
    setExpandedKeys(prev => ({ ...prev, [key]: next }))
  }

  return (
    <div className="glass-card rounded-2xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <GitBranch className="w-4 h-4 text-slate-400" />
        <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          Available Workflows
        </h2>
      </div>

      {groups.length === 0 ? (
        <p className="text-sm text-slate-500 italic">No workflows found.</p>
      ) : (
        <div className="space-y-3">
          {groups.map(group => {
            const counts = getStatusCounts(group)

            return (
              <ExpandableCard
                key={group.key}
                title={group.name}
                className="bg-slate-900/20"
                isExpanded={isExpanded(group.key)}
                onToggle={next => toggleExpanded(group.key, next)}
                expandedContent={
                  group.agents.length === 0 ? (
                    <p className="text-xs text-slate-500 italic">No active agents on this workflow.</p>
                  ) : (
                    <div className="space-y-2">
                      {group.agents.map(agent => (
                        <div
                          key={agent.agent_id}
                          className="rounded-lg border border-slate-700/50 bg-slate-900/30 px-3 py-2"
                        >
                          <div className="flex items-center justify-between gap-2">
                            <span className="text-xs font-mono text-slate-300 truncate">{agent.agent_id}</span>
                            <span className="text-[11px] text-slate-500 truncate">{agent.current_card_id ?? 'N/A'}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )
                }
              >
                <div className="px-4 py-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-accent-light bg-accent/10 px-2 py-0.5 rounded-md border border-accent/15">
                      {group.version}
                    </span>
                    <div className="flex items-center gap-3 text-[11px]">
                      <span className="text-success">run {counts.running}</span>
                      <span className="text-warn">pause {counts.paused}</span>
                      <span className="text-danger">err {counts.error}</span>
                      <span className="text-slate-500">other {counts.other}</span>
                    </div>
                  </div>
                  <div className="mt-2 flex items-center gap-2 text-[11px] text-slate-500">
                    <Users className="w-3.5 h-3.5" />
                    <span>{group.agents.length} active agent(s)</span>
                  </div>
                </div>
              </ExpandableCard>
            )
          })}
        </div>
      )}
    </div>
  )
}
