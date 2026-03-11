'use client'

import { Clock, Layers } from 'lucide-react'
import type { Snapshot } from '@/lib/types'

interface CardStatusBadgesProps {
  snapshot: Snapshot
}

export default function CardStatusBadges({ snapshot }: CardStatusBadgesProps) {
  return (
    <div className="flex items-center gap-2 flex-wrap">
      <span className={`px-3 py-1 text-xs font-semibold rounded-full border ${
        snapshot.status === 'running' 
          ? 'bg-success/10 text-success border-success/30' 
          : snapshot.status === 'error'
            ? 'bg-danger/10 text-danger border-danger/30'
            : 'bg-slate-700/50 text-slate-400 border-slate-600/30'
      }`}>
        {snapshot.status.toUpperCase()}
      </span>
      {snapshot.started_at && (
        <span className="flex items-center gap-1 px-3 py-1 text-xs rounded-full
                       bg-slate-800/50 text-slate-400 border border-slate-700/50">
          <Clock className="w-3 h-3" />
          Started: {new Date(snapshot.started_at).toLocaleTimeString()}
        </span>
      )}
      <span className="flex items-center gap-1 px-3 py-1 text-xs rounded-full
                     bg-slate-800/50 text-slate-400 border border-slate-700/50">
        <Layers className="w-3 h-3" />
        Cycle {snapshot.cycles_completed + 1}
      </span>
    </div>
  )
}
