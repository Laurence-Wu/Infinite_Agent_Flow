import { Zap } from 'lucide-react'
import type { Snapshot } from '@/lib/types'

const STATUS_DOT: Record<string, { color: string; label: string; ping: boolean }> = {
  running:           { color: 'bg-success',      label: 'Running',  ping: true  },
  error:             { color: 'bg-danger',        label: 'Error',    ping: false },
  workflow_finished: { color: 'bg-accent',        label: 'Finished', ping: false },
  completed:         { color: 'bg-accent',        label: 'Completed',ping: false },
  idle:              { color: 'bg-slate-500',     label: 'Idle',     ping: false },
}

export default function Header({ snapshot }: { snapshot: Snapshot }) {
  const dot = STATUS_DOT[snapshot.status] ?? STATUS_DOT.idle

  return (
    <header className="border-b border-slate-700/50 backdrop-blur-sm bg-surface/80 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">

        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent to-purple-500
                          flex items-center justify-center shadow-lg shadow-accent/20">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="text-base font-semibold tracking-tight leading-none">
              Infinite<span className="text-accent-light">Agent</span>Flow
            </h1>
            <p className="text-xs text-slate-500 leading-none mt-0.5">Autonomous Task Engine</p>
          </div>
        </div>

        {/* Right: workflow badge + status dot */}
        <div className="flex items-center gap-3">
          {snapshot.current_workflow && (
            <span className="px-2.5 py-1 text-xs font-mono rounded-full
                             bg-accent/10 text-accent-light border border-accent/20">
              {snapshot.current_workflow}/{snapshot.current_version}
            </span>
          )}
          <div className="flex items-center gap-1.5">
            <span className="relative flex h-2.5 w-2.5">
              {dot.ping && (
                <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${dot.color} opacity-75`} />
              )}
              <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${dot.color}`} />
            </span>
            <span className={`text-xs font-medium ${
              dot.color === 'bg-success' ? 'text-success' :
              dot.color === 'bg-danger'  ? 'text-danger'  :
              dot.color === 'bg-accent'  ? 'text-accent-light' : 'text-slate-400'
            }`}>{dot.label}</span>
          </div>
        </div>

      </div>
    </header>
  )
}
