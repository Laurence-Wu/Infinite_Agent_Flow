import type { Snapshot } from '@/lib/types'

const STATUS_BADGE: Record<string, string> = {
  running:           'bg-success/10 text-success border-success/25',
  error:             'bg-danger/10 text-danger border-danger/25',
  completed:         'bg-accent/10 text-accent-light border-accent/25',
  workflow_finished: 'bg-accent/10 text-accent-light border-accent/25',
  idle:              'bg-slate-700/50 text-slate-400 border-slate-600/25',
}

export default function ProgressPanel({ snapshot }: { snapshot: Snapshot }) {
  const pct    = snapshot.progress_pct ?? 0
  const badge  = STATUS_BADGE[snapshot.status] ?? STATUS_BADGE.idle
  const isLoop = snapshot.current_loop_id && snapshot.current_loop_id !== 'main'

  return (
    <div className="glass-card rounded-2xl p-5">

      {/* Top row */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          {snapshot.current_card_id ? (
            <>
              <span className="font-mono text-lg font-semibold text-white">
                {snapshot.current_card_id}
              </span>
              <span className={`px-2 py-0.5 text-xs rounded-full font-medium border ${
                isLoop
                  ? 'bg-purple-500/15 text-purple-300 border-purple-500/25'
                  : 'bg-accent/15 text-accent-light border-accent/25'
              }`}>
                loop: {snapshot.current_loop_id || 'main'}
              </span>
            </>
          ) : (
            <span className="text-slate-500 text-sm italic">No active card</span>
          )}
        </div>

        {/* Status badge */}
        <span className={`flex items-center gap-1.5 px-3 py-1 text-xs font-medium rounded-full border ${badge}`}>
          {snapshot.status === 'running' && (
            <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse inline-block" />
          )}
          {snapshot.status === 'running'           ? 'Running'
           : snapshot.status === 'error'           ? 'Error'
           : snapshot.status === 'completed'       ? 'Completed'
           : snapshot.status === 'workflow_finished' ? 'Workflow Done'
           : 'Idle'}
        </span>
      </div>

      {/* Progress bar */}
      <div className="w-full h-2 bg-surface-lighter rounded-full overflow-hidden mb-2">
        <div
          className="h-full rounded-full bg-gradient-to-r from-accent-dim via-accent to-accent-light
                     transition-all duration-700 ease-out progress-glow"
          style={{ width: `${pct}%` }}
        />
      </div>

      {/* Labels */}
      <div className="flex items-center justify-between text-xs text-slate-500">
        <span>Card {snapshot.card_index + 1} / {snapshot.total_cards}</span>
        <span className="font-mono text-accent-light">{pct}%</span>
        <span>Cycle {snapshot.cycles_completed + 1} &middot; {snapshot.completed_total} total done</span>
      </div>

      {/* Error */}
      {snapshot.error && (
        <div className="mt-3 px-4 py-2 bg-danger/5 border border-danger/20 rounded-xl text-xs text-danger">
          {snapshot.error}
        </div>
      )}
    </div>
  )
}
