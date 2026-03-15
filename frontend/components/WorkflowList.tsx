"use client"

import { useMemo, useState } from 'react'
import { GitBranch, Users } from 'lucide-react'
import ExpandableCard from '@/components/ExpandableCard'
import type { Workflow, DealerEntry } from '@/lib/types'
import { groupWorkflows, getStatusCounts } from '@/lib/workflowUtils'

interface WorkflowListProps {
  workflows: Workflow[]
  dealers?: DealerEntry[]
}

export default function WorkflowList({ workflows, dealers = [] }: WorkflowListProps) {
  const groups = useMemo(() => groupWorkflows(workflows, dealers), [workflows, dealers])

  const [expandedKeys, setExpandedKeys] = useState<Record<string, boolean>>({})

  const isExpanded = (key: string) => groups.length === 1 || !!expandedKeys[key]
  const toggleExpanded = (key: string, next: boolean) =>
    setExpandedKeys(prev => ({ ...prev, [key]: next }))

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
                  group.dealers.length === 0 ? (
                    <p className="text-xs text-slate-500 italic">No active dealers on this workflow.</p>
                  ) : (
                    <div className="space-y-2">
                      {group.dealers.map(dealer => (
                        <div
                          key={dealer.dealer_id}
                          className="rounded-lg border border-slate-700/50 bg-slate-900/30 px-3 py-2"
                        >
                          <div className="flex items-center justify-between gap-2">
                            <span className="text-xs font-mono text-slate-300 truncate">{dealer.dealer_id}</span>
                            <span className="text-[11px] text-slate-500 truncate">{dealer.current_card_id ?? 'N/A'}</span>
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
                    <span>{group.dealers.length} active dealer{group.dealers.length !== 1 ? 's' : ''}</span>
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
