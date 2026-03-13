'use client'

import type { AgentEntry } from '@/lib/types'
import AgentCard from '@/components/AgentCard'

interface AgentGridProps {
  agents: AgentEntry[]
  selectedId: string | null
  onSelect: (id: string) => void
}

export default function AgentGrid({ agents, selectedId, onSelect }: AgentGridProps) {
  if (agents.length === 0) {
    return (
      <div className="glass-card rounded-2xl p-12 text-center">
        <p className="text-slate-500 italic text-sm">
          No agents running. Start one with{' '}
          <code className="font-mono text-accent-light bg-accent/10 px-1.5 py-0.5 rounded">
            python orchestrator.py
          </code>
        </p>
      </div>
    )
  }

  const gridClass =
    agents.length === 1 ? 'grid grid-cols-1 gap-4' :
    agents.length <= 3  ? 'grid grid-cols-1 lg:grid-cols-2 gap-4' :
                          'grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4'

  return (
    <div className={gridClass}>
      {agents.map(agent => (
        <AgentCard
          key={agent.agent_id}
          agent={agent}
          isSelected={agent.agent_id === selectedId}
          onSelect={onSelect}
        />
      ))}
    </div>
  )
}
