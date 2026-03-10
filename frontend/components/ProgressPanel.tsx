import type { Snapshot } from '@/lib/types'
import { STATUS_BADGE } from '@/lib/statusConfig'

export default function ProgressPanel({ snapshot }: { snapshot: Snapshot }) {
  const pct    = snapshot.progress_pct ?? 0
  const badge  = STATUS_BADGE[snapshot.status] ?? STATUS_BADGE.idle
  const isLoop = snapshot.current_loop_id && snapshot.current_loop_id !== 'main'
  const isActive = snapshot.status === 'running'

  return (
    <div className={isActive ? 'glass-card-active rounded-2xl p-6' : 'glass-card rounded-2xl p-6'}>

      {/* ── Primary identity row ─────────────────────────────────── */}
      <div className="flex items-start justify-between gap-4 mb-5">

        {/* Card ID — the most important piece of info on the screen */}
        <div className="flex flex-col gap-1.5 min-w-0">
          {snapshot.current_card_id ? (
            <>
              <span className={`font-mono text-4xl font-black leading-none tracking-tight
                               text-accent-light ${isActive ? 'card-id-glow' : ''}`}>
                {snapshot.current_card_id}
              </span>
              <div className="flex items-center gap-2 mt-1">
                <span className={`px-2 py-0.5 text-xs rounded-full font-medium border ${
                  isLoop
                    ? 'bg-gruvbox-purple/15 text-gruvbox-purple-bright border-gruvbox-purple/25'
                    : 'bg-accent/12 text-accent-light border-accent/25'
                }`}>
                  ⟳ {snapshot.current_loop_id || 'main'}
                </span>
                <span className="text-xs text-slate-600 font-mono">
                  {snapshot.current_workflow}/{snapshot.current_version}
                </span>
              </div>
            </>
          ) : (
            <span className="text-slate-600 text-lg italic font-light">No active card</span>
          )}
        </div>

        {/* Status badge — clearly visible, right-aligned */}
        <span className={`flex items-center gap-2 px-4 py-1.5 text-sm font-semibold
                         rounded-full border flex-shrink-0 ${badge}`}>
          {snapshot.status === 'running' && (
            <span className="w-2 h-2 rounded-full bg-success animate-pulse inline-block" />
          )}
          {snapshot.status === 'running'             ? 'Running'
           : snapshot.status === 'error'             ? 'Error'
           : snapshot.status === 'completed'         ? 'Completed'
           : snapshot.status === 'workflow_finished' ? 'Workflow Done'
           : 'Idle'}
        </span>
      </div>

      {/* ── Progress bar + percentage ────────────────────────────── */}
      <div className="flex items-center gap-4 mb-3">
        <div className="flex-1 h-3 bg-surface-lighter rounded-full overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-accent-dim via-accent to-accent-light
                       transition-all duration-700 ease-out progress-glow"
            style={{ width: `${pct}%` }}
          />
        </div>
        {/* Large % label — always visible */}
        <span className="font-mono text-2xl font-black text-accent-light w-16 text-right
                         leading-none flex-shrink-0 glow-yellow">
          {pct}%
        </span>
      </div>

      {/* ── Sub-labels ───────────────────────────────────────────── */}
      <div className="flex items-center justify-between text-xs text-slate-600 font-mono">
        <span>
          Card <span className="text-slate-400">{snapshot.card_index + 1}</span>
          {' / '}
          <span className="text-slate-400">{snapshot.total_cards}</span>
        </span>
        <span>
          Cycle <span className="text-slate-400">{snapshot.cycles_completed + 1}</span>
          {' · '}
          <span className="text-slate-400">{snapshot.completed_total}</span> done
        </span>
      </div>

      {/* ── Error banner ─────────────────────────────────────────── */}
      {snapshot.error && (
        <div className="mt-4 px-4 py-2.5 bg-danger/8 border border-danger/25
                        rounded-xl text-xs text-danger font-mono">
          ✕ {snapshot.error}
        </div>
      )}
    </div>
  )
}
