'use client'

import { FileText, GitBranch, ChevronUp, ChevronDown, Square, Pause, Play } from 'lucide-react'
import type { Snapshot } from '@/lib/types'

interface CardHeaderProps {
  snapshot: Snapshot
  isExpanded: boolean
  onToggleExpand: () => void
  onStop?: () => void
  onPause?: () => void
  onResume?: () => void
}

export default function CardHeader({
  snapshot,
  isExpanded,
  onToggleExpand,
  onStop,
  onPause,
  onResume,
}: CardHeaderProps) {
  const progressPct = snapshot.progress_pct || 0
  const cardNumber = snapshot.card_index + 1
  const totalCards = snapshot.total_cards
  const isPaused = snapshot.is_paused ?? false

  return (
    <div
      className="flex items-center justify-between px-5 py-4 border-b border-slate-700/40 cursor-pointer hover:bg-slate-800/30 transition-colors"
      onClick={onToggleExpand}
    >
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
          snapshot.status === 'running'
            ? 'bg-gradient-to-br from-accent-light via-accent to-warn shadow-lg shadow-accent/30'
            : 'bg-slate-700'
        }`}>
          <FileText className="w-5 h-5 text-surface-hard" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-lg font-bold text-accent-light">
              {snapshot.current_card_id}
            </span>
            {snapshot.current_loop_id && snapshot.current_loop_id !== 'main' && (
              <span className="text-xs px-2 py-0.5 rounded-full
                             bg-gruvbox-purple/20 text-gruvbox-purple-bright border border-gruvbox-purple/30">
                ⟳ {snapshot.current_loop_id}
              </span>
            )}
          </div>
          <div className="flex items-center gap-3 text-xs text-slate-500 font-mono">
            <span className="flex items-center gap-1">
              <GitBranch className="w-3 h-3" />
              {snapshot.current_workflow}/{snapshot.current_version}
            </span>
            <span>Card {cardNumber} of {totalCards}</span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3" onClick={(e) => e.stopPropagation()}>
        {/* Control buttons */}
        {(onStop || onPause || onResume) && (
          <div className="flex items-center gap-1">
            {isPaused ? (
              onResume && (
                <button
                  onClick={onResume}
                  title="Resume workflow"
                  className="flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-semibold
                             bg-success/10 hover:bg-success/20 text-success border border-success/20
                             transition-all"
                >
                  <Play className="w-3 h-3" /> Resume
                </button>
              )
            ) : (
              onPause && snapshot.status === 'running' && (
                <button
                  onClick={onPause}
                  title="Pause workflow"
                  className="flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-semibold
                             bg-warn/10 hover:bg-warn/20 text-warn border border-warn/20
                             transition-all"
                >
                  <Pause className="w-3 h-3" /> Pause
                </button>
              )
            )}
            {onStop && (
              <button
                onClick={onStop}
                title="Stop workflow"
                className="flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-semibold
                           bg-danger/10 hover:bg-danger/20 text-danger border border-danger/20
                           transition-all"
              >
                <Square className="w-3 h-3" /> Stop
              </button>
            )}
          </div>
        )}

        {/* Progress indicator */}
        <div className="text-right">
          <div className="text-2xl font-black text-accent-light glow-yellow">
            {progressPct}%
          </div>
          <div className="text-xs text-slate-500 font-mono">progress</div>
        </div>

        {/* Expand/collapse button */}
        <button
          onClick={onToggleExpand}
          className="text-slate-500 hover:text-accent-light transition-colors"
        >
          {isExpanded ? (
            <ChevronUp className="w-5 h-5" />
          ) : (
            <ChevronDown className="w-5 h-5" />
          )}
        </button>
      </div>
    </div>
  )
}
