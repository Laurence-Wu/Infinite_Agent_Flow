'use client'

import { useState } from 'react'
import { ChevronDown, ChevronUp, FileText, Clock, Layers, GitBranch } from 'lucide-react'
import ExpandableMarkdown from '@/components/ExpandableMarkdown'
import type { Snapshot } from '@/lib/types'

interface CurrentCardPanelProps {
  snapshot: Snapshot
  markdown: string
}

export default function CurrentCardPanel({ snapshot, markdown }: CurrentCardPanelProps) {
  const [isExpanded, setIsExpanded] = useState(true)
  const [showFullInstruction, setShowFullInstruction] = useState(false)

  if (!snapshot.current_card_id) {
    return (
      <div className="glass-card rounded-2xl overflow-hidden">
        <div className="p-8 text-center">
          <FileText className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-slate-400 mb-1">No Active Card</h3>
          <p className="text-sm text-slate-500">
            {snapshot.status === 'workflow_finished' 
              ? 'Workflow completed successfully' 
              : 'Waiting for next card...'}
          </p>
        </div>
      </div>
    )
  }

  const progressPct = snapshot.progress_pct || 0
  const cardNumber = snapshot.card_index + 1
  const totalCards = snapshot.total_cards

  return (
    <div className="glass-card rounded-2xl overflow-hidden">
      {/* Header - always visible */}
      <div
        className="flex items-center justify-between px-5 py-4 border-b border-slate-700/40 cursor-pointer hover:bg-slate-800/30 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
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

        <div className="flex items-center gap-4">
          {/* Progress indicator */}
          <div className="text-right">
            <div className="text-2xl font-black text-accent-light glow-yellow">
              {progressPct}%
            </div>
            <div className="text-xs text-slate-500 font-mono">progress</div>
          </div>
          
          {/* Expand/collapse button */}
          <button
            onClick={(e) => {
              e.stopPropagation()
              setIsExpanded(!isExpanded)
            }}
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

      {/* Progress bar */}
      <div className="h-1 w-full bg-slate-800">
        <div
          className="h-full bg-gradient-to-r from-accent-dim via-accent to-accent-light progress-glow transition-all duration-700"
          style={{ width: `${progressPct}%` }}
        />
      </div>

      {/* Expanded content */}
      {isExpanded && (
        <div className="p-6 space-y-4">
          {/* Status badges */}
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

          {/* Instruction content */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
                Instruction
              </h4>
              {markdown && (
                <button
                  onClick={() => setShowFullInstruction(!showFullInstruction)}
                  className="text-xs text-accent-light hover:text-accent hover:underline"
                >
                  {showFullInstruction ? 'Show Less' : 'Show Full'}
                </button>
              )}
            </div>
            
            {markdown ? (
              <div className={`prose prose-sm max-w-none ${
                showFullInstruction ? '' : 'max-h-60 overflow-hidden relative'
              }`}>
                <ExpandableMarkdown 
                  markdown={markdown} 
                  defaultExpandedSections={['h1']}
                />
                {!showFullInstruction && (
                  <div className="absolute bottom-0 left-0 right-0 h-20 bg-gradient-to-t from-surface to-transparent pointer-events-none" />
                )}
              </div>
            ) : (
              <p className="text-slate-500 italic text-sm">Loading instruction...</p>
            )}
          </div>

          {/* Error display */}
          {snapshot.error && (
            <div className="p-4 rounded-xl bg-danger/10 border border-danger/30">
              <div className="flex items-center gap-2 text-danger mb-2">
                <span className="font-bold">⚠ Error</span>
              </div>
              <p className="text-sm text-slate-400 font-mono">{snapshot.error}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
