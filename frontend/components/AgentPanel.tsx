'use client'

import { Pause, Play, Square, RefreshCw, CheckSquare, Clock, ScanLine, AlertTriangle } from 'lucide-react'
import type { AgentEntry } from '@/lib/types'
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
import SessionPanel    from '@/components/SessionPanel'

// ── Compact stat tile ────────────────────────────────────────────────────────
function MiniStat({ value, label, icon }: { value: string | number; label: string; icon: React.ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-1 px-4 py-3 rounded-xl bg-surface/60 border border-slate-700/30">
      <div className="opacity-40">{icon}</div>
      <div className="text-2xl font-black font-mono text-accent-light leading-none">{value}</div>
      <div className="text-[10px] uppercase tracking-widest text-slate-600">{label}</div>
    </div>
  )
}

// ── Neutral button (restart / deal-next) ─────────────────────────────────────
const BTN_NEUTRAL = 'bg-slate-700/40 hover:bg-slate-700/70 text-slate-300 border-slate-600/40'

export default function AgentPanel({ agent }: { agent: AgentEntry }) {
  const { snapshot } = useSnapshot(agent.agent_id)
  const { pauseWorkflow, resumeWorkflow, stopWorkflow, dealNextFor, restartAgent } = useEngineActions()
  const uptime     = useUptime(snapshot?.engine_start_epoch ?? null)
  const { files }  = useWorkspaceScan(agent.agent_id)

  const isRunning  = agent.status === 'running'
  const isIdle     = agent.status === 'idle' || agent.status === 'workflow_finished'
  const dot        = STATUS_DOT[agent.status] ?? STATUS_DOT.idle
  const badgeCls   = STATUS_BADGE[agent.status] ?? STATUS_BADGE.idle

  return (
    <div className="space-y-5 p-6 max-w-5xl mx-auto">

      {/* ── Header card ── */}
      <div className="glass-card rounded-2xl px-6 py-4">

        {/* Top row: identity + controls */}
        <div className="flex flex-wrap items-center justify-between gap-4">

          {/* Identity */}
          <div className="flex items-center gap-3 min-w-0">
            {/* Live dot */}
            <div className="relative shrink-0">
              {dot.ping && (
                <span className="absolute inset-0 rounded-full bg-success animate-ping opacity-60" />
              )}
              <span className={`relative block w-3 h-3 rounded-full ${dot.color}`} />
            </div>

            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-mono text-xl font-bold text-accent-light truncate">
                  {agent.agent_id}
                </span>
                {agent.current_card_id && (
                  <span className="text-xs font-mono bg-slate-800/60 px-1.5 py-0.5 rounded-md border border-slate-700/40 text-slate-400 shrink-0">
                    {agent.current_card_id}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-xs font-mono text-slate-500">
                  {agent.workflow}/{agent.version}
                </span>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${badgeCls}`}>
                  {dot.label}
                </span>
                {agent.is_paused && (
                  <span className="text-xs text-warn">· paused</span>
                )}
              </div>
            </div>
          </div>

          {/* Controls */}
          <div className="flex items-center gap-1.5 flex-wrap">
            {/* Pause / Resume */}
            {agent.is_paused ? (
              <button
                onClick={() => resumeWorkflow(agent.agent_id)}
                className={`${CONTROL_BTN_BASE} ${CONTROL_BTN.resume}`}
              >
                <Play className="w-3 h-3" />
                <span>Resume</span>
              </button>
            ) : isRunning ? (
              <button
                onClick={() => pauseWorkflow(agent.agent_id)}
                className={`${CONTROL_BTN_BASE} ${CONTROL_BTN.pause}`}
              >
                <Pause className="w-3 h-3" />
                <span>Pause</span>
              </button>
            ) : null}

            {/* Stop */}
            {(isRunning || agent.is_paused) && (
              <button
                onClick={() => stopWorkflow(agent.agent_id)}
                className={`${CONTROL_BTN_BASE} ${CONTROL_BTN.stop}`}
              >
                <Square className="w-3 h-3" />
                <span>Stop</span>
              </button>
            )}

            {/* Deal Next — start when idle */}
            {(isIdle || agent.is_paused) && (
              <button
                onClick={() => dealNextFor(agent.agent_id)}
                className={`${CONTROL_BTN_BASE} ${BTN_NEUTRAL}`}
              >
                <Play className="w-3 h-3" />
                <span>Start</span>
              </button>
            )}

            {/* Restart — always available */}
            <button
              onClick={() => restartAgent(agent.agent_id)}
              className={`${CONTROL_BTN_BASE} ${BTN_NEUTRAL}`}
            >
              <RefreshCw className="w-3 h-3" />
              <span>Restart</span>
            </button>
          </div>
        </div>

        {/* Error banner */}
        {agent.error && (
          <div className="mt-3 flex items-start gap-2 px-3 py-2 rounded-lg bg-danger/8 border border-danger/25 text-xs text-danger font-mono">
            <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
            {agent.error}
          </div>
        )}
      </div>

      {/* ── Progress bar ── */}
      <CardProgressBar progressPct={agent.progress_pct ?? 0} />

      {/* ── Stats row ── */}
      <div className="grid grid-cols-3 gap-3">
        <MiniStat
          value={agent.cycles_completed}
          label="Cycles"
          icon={<RefreshCw className="w-4 h-4 text-accent-light" />}
        />
        <MiniStat
          value={agent.completed_total}
          label="Done"
          icon={<CheckSquare className="w-4 h-4 text-success" />}
        />
        <MiniStat
          value={uptime}
          label="Uptime"
          icon={<Clock className="w-4 h-4 text-info" />}
        />
      </div>

      {/* ── Current Task — all agents, not just 'default' ── */}
      <TaskPreview markdown={snapshot?.current_instruction ?? ''} />

      {/* ── Workspace files — per-agent, expandable ── */}
      <ExpandableCard
        title="Workspace Activity"
        icon={<ScanLine className="w-4 h-4 text-accent-light" />}
        defaultExpanded={false}
        expandedContent={<WorkspaceScan files={files} />}
      >
        <div className="px-5 py-2 text-xs text-slate-500 font-mono truncate">
          {agent.workspace || 'workspace path unavailable'}
        </div>
      </ExpandableCard>

      {/* ── Full live log ── */}
      <LogTerminal lines={snapshot?.log_lines ?? []} />

      {/* ── Completed tasks ── */}
      <HistoryFeed history={snapshot?.history ?? []} />

      {/* ── tmux session ── */}
      <SessionPanel />

    </div>
  )
}
