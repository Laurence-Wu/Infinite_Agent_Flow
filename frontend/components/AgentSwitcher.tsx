'use client'

import { Users, User, Circle } from 'lucide-react'
import type { Snapshot } from '@/lib/types'

interface AgentSwitcherProps {
  agents: Record<string, Snapshot>
  activeId: string
  onSelect: (id: string) => void
}

export default function AgentSwitcher({ agents, activeId, onSelect }: AgentSwitcherProps) {
  const agentIds = Object.keys(agents).sort()

  if (agentIds.length <= 1 && agentIds[0] === 'default') return null

  return (
    <div className="glass-card rounded-2xl overflow-hidden border border-slate-700/40">
      <div className="px-5 py-3 border-b border-slate-700/40 flex items-center gap-2 bg-slate-800/20">
        <Users className="w-4 h-4 text-accent-light" />
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
          Active Agents ({agentIds.length})
        </h3>
      </div>
      <div className="p-2 space-y-1">
        {agentIds.map((id) => {
          const s = agents[id]
          const isActive = id === activeId
          const isRunning = s.status === 'running'
          
          return (
            <button
              key={id}
              onClick={() => onSelect(id)}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-xl transition-all ${
                isActive 
                  ? 'bg-accent/10 border border-accent/30 text-accent-light' 
                  : 'hover:bg-slate-700/30 text-slate-400 border border-transparent'
              }`}
            >
              <div className="flex items-center gap-3">
                <div className={`relative flex items-center justify-center w-8 h-8 rounded-lg ${
                  isActive ? 'bg-accent/20' : 'bg-slate-800'
                }`}>
                  <User className={`w-4 h-4 ${isActive ? 'text-accent-light' : 'text-slate-500'}`} />
                  {isRunning && (
                    <span className="absolute -top-1 -right-1 flex h-2.5 w-2.5">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-success"></span>
                    </span>
                  )}
                </div>
                <div className="text-left">
                  <div className="text-sm font-mono font-bold truncate max-w-[120px]">
                    {id}
                  </div>
                  <div className="text-[10px] text-slate-500 uppercase">
                    {s.status}
                  </div>
                </div>
              </div>
              
              {s.progress_pct !== undefined && (
                <div className="text-xs font-mono text-slate-500">
                  {s.progress_pct}%
                </div>
              )}
            </button>
          )
        })}
      </div>
    </div>
  )
}
