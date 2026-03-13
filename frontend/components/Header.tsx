import { Flame } from 'lucide-react'
import type { AgentEntry } from '@/lib/types'
import { STATUS_DOT } from '@/lib/statusConfig'

interface HeaderProps {
  agent: AgentEntry | null
  agentCount?: number
}

export default function Header({ agent, agentCount }: HeaderProps) {
  const status = agent?.status ?? 'idle'
  const dot = STATUS_DOT[status] ?? STATUS_DOT.idle

  // Map dot color to text color token
  const dotTextClass =
    dot.color === 'bg-success' ? 'text-success' :
    dot.color === 'bg-danger'  ? 'text-danger'  :
    dot.color === 'bg-accent'  ? 'text-accent-light' : 'text-slate-600'

  return (
    <header className="border-b border-accent/10 backdrop-blur-sm bg-surface-hard/85 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">

        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl
                          bg-gradient-to-br from-accent-light via-accent to-warn
                          flex items-center justify-center
                          shadow-lg shadow-accent/30 animate-warm-glow">
            <Flame className="w-4 h-4 text-surface-hard" />
          </div>
          <div>
            <h1 className="text-base font-bold tracking-tight leading-none text-gruvbox-fg">
              Infinite<span className="text-accent-light">Agent</span>Flow
            </h1>
            <p className="text-xs text-slate-700 leading-none mt-0.5 font-mono">
              autonomous task engine
            </p>
          </div>
        </div>

        {/* Right: active workflow badge + agent count + status */}
        <div className="flex items-center gap-3">
          {/* Workflow badge — from selected agent */}
          {agent?.workflow && (
            <span className="hidden sm:inline-flex px-3 py-1 text-xs font-mono rounded-full
                             bg-accent/10 text-accent-light border border-accent/20 tracking-wide">
              {agent.workflow}
              <span className="text-slate-700 mx-1">/</span>
              {agent.version}
            </span>
          )}

          {/* Agent count pill */}
          {agentCount !== undefined && agentCount > 0 && (
            <span className="px-2.5 py-1 text-xs font-mono rounded-full
                             bg-slate-800/60 text-slate-400 border border-slate-700/40">
              {agentCount} agent{agentCount !== 1 ? 's' : ''}
            </span>
          )}

          {/* Status indicator */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full
                          border border-slate-800/60 bg-surface/50">
            <span className="relative flex h-2.5 w-2.5">
              {dot.ping && (
                <span className={`animate-ping absolute inline-flex h-full w-full rounded-full
                                 ${dot.color} opacity-75`} />
              )}
              <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${dot.color}`} />
            </span>
            <span className={`text-xs font-semibold ${dotTextClass}`}>
              {agent ? dot.label : 'Connecting'}
            </span>
          </div>
        </div>

      </div>
    </header>
  )
}
