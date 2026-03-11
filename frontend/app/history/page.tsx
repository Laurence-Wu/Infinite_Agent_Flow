'use client'

import { useHistory } from '@/lib/hooks/useHistory'
import { CheckCircle, Clock } from 'lucide-react'
import ExpandableMarkdown from '@/components/ExpandableMarkdown'

export default function HistoryPage() {
  const { history, isLoading } = useHistory()
  const reversed = [...history].reverse()

  return (
    <div className="w-full px-6 py-6 space-y-6">
      <div className="flex items-center gap-3">
        <CheckCircle className="w-6 h-6 text-success" />
        <h1 className="text-xl font-bold text-gruvbox-fg">Task History</h1>
        <span className="text-sm text-slate-500 font-mono">
          {history.length} {history.length === 1 ? 'task' : 'tasks'} completed
        </span>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-slate-500">Loading history...</div>
      ) : reversed.length === 0 ? (
        <div className="glass-card rounded-2xl p-8 text-center">
          <Clock className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400">No completed tasks yet</p>
          <p className="text-sm text-slate-500 mt-2">
            Completed tasks will appear here as the workflow progresses
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {reversed.map((item, i) => (
            <div
              key={i}
              className="glass-card rounded-2xl overflow-hidden"
            >
              <div className="flex items-center justify-between px-5 py-3 border-b border-slate-700/50 bg-slate-800/30">
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-success" />
                  <span className="font-mono text-lg font-bold text-accent-light">
                    {item.card_id}
                  </span>
                  {item.loop_id && item.loop_id !== 'main' && (
                    <span className="text-xs px-2 py-0.5 rounded-full
                                     bg-purple-500/10 text-purple-300 border border-purple-500/20">
                      {item.loop_id}
                    </span>
                  )}
                </div>
                <div className="text-right">
                  <div className="text-sm font-mono text-slate-400">
                    {item.completed_at.slice(0, 10)}
                  </div>
                  <div className="text-xs font-mono text-slate-500">
                    {item.completed_at.slice(11, 19)}
                  </div>
                </div>
              </div>
              <div className="p-5">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Summary
                  </span>
                </div>
                <div className="prose prose-sm max-w-none">
                  <ExpandableMarkdown markdown={item.summary} />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
