'use client'

import { useState } from 'react'
import { FileText } from 'lucide-react'
import type { Snapshot } from '@/lib/types'
import CardHeader from './card/CardHeader'
import CardProgressBar from './card/CardProgressBar'
import CardStatusBadges from './card/CardStatusBadges'
import CardInstruction from './card/CardInstruction'
import { useEngineActions } from '@/lib/hooks/useEngineActions'

interface CurrentCardPanelProps {
  snapshot: Snapshot
  markdown: string
  onMutate?: () => void
}

export default function CurrentCardPanel({ snapshot, markdown, onMutate }: CurrentCardPanelProps) {
  const [isExpanded, setIsExpanded] = useState(true)
  const { pauseWorkflow, resumeWorkflow, stopWorkflow } = useEngineActions()

  const agentId = snapshot.agent_id

  const handlePause = async () => {
    await pauseWorkflow(agentId)
    onMutate?.()
  }

  const handleResume = async () => {
    await resumeWorkflow(agentId)
    onMutate?.()
  }

  const handleStop = async () => {
    await stopWorkflow(agentId)
    onMutate?.()
  }

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

  return (
    <div className="glass-card rounded-2xl overflow-hidden">
      <CardHeader
        snapshot={snapshot}
        isExpanded={isExpanded}
        onToggleExpand={() => setIsExpanded(!isExpanded)}
        onPause={handlePause}
        onResume={handleResume}
        onStop={handleStop}
      />

      <CardProgressBar progressPct={snapshot.progress_pct || 0} />

      {isExpanded && (
        <div className="p-6 space-y-4">
          <CardStatusBadges snapshot={snapshot} />

          <CardInstruction markdown={markdown} />

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
