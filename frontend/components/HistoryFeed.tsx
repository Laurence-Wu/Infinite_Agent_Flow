import { CheckCircle } from 'lucide-react'
import type { HistoryEntry } from '@/lib/types'

export default function HistoryFeed({ history }: { history: HistoryEntry[] }) {
  const reversed = [...history].reverse()

  return (
    <div className="glass-card rounded-2xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-success" />
          <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Completed Tasks
          </h2>
        </div>
        {history.length > 0 && (
          <span className="text-xs font-mono text-slate-600">{history.length}</span>
        )}
      </div>

      {reversed.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-sm text-slate-500 italic">No tasks completed yet.</p>
        </div>
      ) : (
        <ul className="space-y-2 max-h-72 overflow-y-auto custom-scrollbar pr-1">
          {reversed.map((item, i) => (
            <li
              key={i}
              className="bg-surface rounded-xl p-3 border border-slate-700/30
                         hover:border-accent/20 transition-colors duration-200"
            >
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-sm text-accent-light font-medium">
                    {item.card_id}
                  </span>
                  {item.loop_id && item.loop_id !== 'main' && (
                    <span className="text-xs px-1.5 py-0.5 rounded
                                     bg-purple-500/10 text-purple-300 border border-purple-500/20">
                      {item.loop_id}
                    </span>
                  )}
                </div>
                <span className="text-xs text-slate-500 font-mono">
                  {item.completed_at.slice(11, 19)}
                </span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed line-clamp-2">
                {item.summary}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
