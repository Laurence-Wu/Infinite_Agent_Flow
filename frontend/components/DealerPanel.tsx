'use client'

import { useState } from 'react'
import { Pause, Play, Square, RefreshCw, CheckSquare, Clock, ScanLine, AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react'
import type { DealerEntry } from '@/lib/types'
import { STATUS_DOT, STATUS_BADGE, CONTROL_BTN, CONTROL_BTN_BASE } from '@/lib/statusConfig'
import { useSnapshot }      from '@/lib/hooks/useSnapshot'
import { useEngineActions } from '@/lib/hooks/useEngineActions'
import { useUptime }        from '@/lib/hooks/useUptime'
import { useWorkspaceScan } from '@/lib/hooks/useWorkspaceScan'
import CardProgressBar from '@/components/card/CardProgressBar'
import TaskPreview     from '@/components/TaskPreview'
import LogTerminal     from '@/components/LogTerminal'
import HistoryFeed     from '@/components/HistoryFeed'
import WorkspaceScan   from '@/components/WorkspaceScan'
import ExpandableCard  from '@/components/ExpandableCard'
import AgentPanel      from '@/components/AgentPanel'
import { useSettings } from '@/lib/context/SettingsContext'

// ── Compact stat tile ─────────────────────────────────────────────────────────
function MiniStat({ value, label, icon }: { value: string | number; label: string; icon: React.ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-1 px-4 py-3 rounded-xl bg-surface/60 border border-slate-700/30">
      <div className="opacity-40">{icon}</div>
      <div className="text-2xl font-black font-mono text-accent-light leading-none">{value}</div>
      <div className="text-[10px] uppercase tracking-widest text-slate-600">{label}</div>
    </div>
  )
}

const BTN_NEUTRAL = 'bg-slate-700/40 hover:bg-slate-700/70 text-slate-300 border-slate-600/40'

export default function DealerPanel({ dealer }: { dealer: DealerEntry }) {
  const { settings } = useSettings()
  const [expanded, setExpanded] = useState(() => settings.autoExpandCards)

  const { snapshot } = useSnapshot(dealer.dealer_id)
  const { pauseDealer, resumeDealer, stopDealer, dealNextFor, restartDealer } = useEngineActions()
  const uptime    = useUptime(snapshot?.engine_start_epoch ?? null)
  const { files } = useWorkspaceScan(dealer.dealer_id)

  const isRunning = dealer.status === 'running'
  const isIdle    = dealer.status === 'idle' || dealer.status === 'workflow_finished'
  const dot       = STATUS_DOT[dealer.status] ?? STATUS_DOT.idle
  const badgeCls  = STATUS_BADGE[dealer.status] ?? STATUS_BADGE.idle

  return (
    <div className="glass-card rounded-2xl overflow-hidden">

      {/* ── Clickable header ── */}
      <div
        onClick={() => setExpanded(v => !v)}
        className="cursor-pointer px-6 py-4"
      >
        {/* Top row: identity + dealer controls + chevron */}
        <div className="flex flex-wrap items-center justify-between gap-4">

          {/* Identity */}
          <div className="flex items-center gap-3 min-w-0">
            <div className="relative shrink-0">
              {dot.ping && (
                <span className="absolute inset-0 rounded-full bg-success animate-ping opacity-60" />
              )}
              <span className={`relative block w-3 h-3 rounded-full ${dot.color}`} />
            </div>

            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-mono text-xl font-bold text-accent-light truncate">
                  {dealer.dealer_id}
                </span>
                {dealer.current_card_id && (
                  <span className="text-xs font-mono bg-slate-800/60 px-1.5 py-0.5 rounded-md border border-slate-700/40 text-slate-400 shrink-0">
                    {dealer.current_card_id}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-xs font-mono text-slate-500">
                  {dealer.workflow}/{dealer.version}
                </span>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${badgeCls}`}>
                  {dot.label}
                </span>
                {dealer.is_paused && (
                  <span className="text-xs text-warn">· paused</span>
                )}
              </div>
            </div>
          </div>

          {/* Controls + chevron */}
          <div className="flex items-center gap-1.5 flex-wrap">
            {dealer.is_paused ? (
              <button
                onClick={(e) => { e.stopPropagation(); resumeDealer(dealer.dealer_id) }}
                className={`${CONTROL_BTN_BASE} ${CONTROL_BTN.resume}`}
              >
                <Play className="w-3 h-3" />
                <span>Resume</span>
              </button>
            ) : isRunning ? (
              <button
                onClick={(e) => { e.stopPropagation(); pauseDealer(dealer.dealer_id) }}
                className={`${CONTROL_BTN_BASE} ${CONTROL_BTN.pause}`}
              >
                <Pause className="w-3 h-3" />
                <span>Pause</span>
              </button>
            ) : null}

            {(isRunning || dealer.is_paused) && (
              <button
                onClick={(e) => { e.stopPropagation(); stopDealer(dealer.dealer_id) }}
                className={`${CONTROL_BTN_BASE} ${CONTROL_BTN.stop}`}
              >
                <Square className="w-3 h-3" />
                <span>Stop</span>
              </button>
            )}

            {(isIdle || dealer.is_paused) && (
              <button
                onClick={(e) => { e.stopPropagation(); dealNextFor(dealer.dealer_id) }}
                className={`${CONTROL_BTN_BASE} ${BTN_NEUTRAL}`}
              >
                <Play className="w-3 h-3" />
                <span>Start</span>
              </button>
            )}

            <button
              onClick={(e) => { e.stopPropagation(); restartDealer(dealer.dealer_id) }}
              className={`${CONTROL_BTN_BASE} ${BTN_NEUTRAL}`}
            >
              <RefreshCw className="w-3 h-3" />
              <span>Restart</span>
            </button>

            <span className="ml-1 text-slate-500">
              {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </span>
          </div>
        </div>

        {/* Error banner */}
        {dealer.error && (
          <div className="mt-3 flex items-start gap-2 px-3 py-2 rounded-lg bg-danger/8 border border-danger/25 text-xs text-danger font-mono">
            <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
            {dealer.error}
          </div>
        )}

        {/* Progress bar */}
        <div className="mt-3">
          <CardProgressBar progressPct={dealer.progress_pct ?? 0} />
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-3 gap-3 mt-3">
          <MiniStat
            value={dealer.cycles_completed}
            label="Cycles"
            icon={<RefreshCw className="w-4 h-4 text-accent-light" />}
          />
          <MiniStat
            value={dealer.completed_total}
            label="Done"
            icon={<CheckSquare className="w-4 h-4 text-success" />}
          />
          <MiniStat
            value={uptime}
            label="Uptime"
            icon={<Clock className="w-4 h-4 text-info" />}
          />
        </div>
      </div>

      {/* ── Expanded detail section ── */}
      {expanded && (
        <div className="border-t border-slate-700/30 space-y-4 p-4">

          {/* Current Task */}
          <TaskPreview markdown={snapshot?.current_instruction ?? ''} />

          {/* Compact live log */}
          <LogTerminal lines={snapshot?.log_lines ?? []} compact={settings.compactLogs} />

          {/* Workspace files — expandable */}
          <ExpandableCard
            title="Workspace Activity"
            icon={<ScanLine className="w-4 h-4 text-accent-light" />}
            defaultExpanded={false}
            expandedContent={<WorkspaceScan files={files} />}
          >
            <div className="px-5 py-2 text-xs text-slate-500 font-mono truncate">
              {dealer.workspace || 'workspace path unavailable'}
            </div>
          </ExpandableCard>

          {/* Completed tasks */}
          <HistoryFeed history={snapshot?.history ?? []} />

          {/* Agent tmux CLI — lazy: only mounts when expanded */}
          <AgentPanel />
        </div>
      )}
    </div>
  )
}
