'use client'

import { useState, useEffect } from 'react'
import {
  ChevronDown, ChevronUp, User, Square, Pause, Play,
  RefreshCw, CheckSquare, Clock, AlertTriangle,
} from 'lucide-react'
import type { AgentEntry, HistoryEntry } from '@/lib/types'
import { STATUS_DOT, CONTROL_BTN, CONTROL_BTN_BASE } from '@/lib/statusConfig'
import { useSnapshot } from '@/lib/hooks/useSnapshot'
import { useEngineActions } from '@/lib/hooks/useEngineActions'
import { useUptime } from '@/lib/hooks/useUptime'
import CardProgressBar from '@/components/card/CardProgressBar'
import LogTerminal from '@/components/LogTerminal'

interface AgentCardProps {
  agent: AgentEntry
  isSelected: boolean
  onSelect: (id: string) => void
}

// ── Compact inline history strip ────────────────────────────────────────────
function HistoryStrip({ entries }: { entries: HistoryEntry[] }) {
  if (entries.length === 0) return null
  const recent = [...entries].reverse().slice(0, 3)
  return (
    <div className="space-y-1.5">
      {recent.map((item, i) => (
        <div key={i} className="flex items-start gap-2 px-3 py-2 rounded-lg bg-surface/60 border border-slate-700/30">
          <span className="font-mono text-xs text-accent-light font-semibold shrink-0">{item.card_id}</span>
          <span className="text-xs text-slate-400 line-clamp-1 flex-1">{item.summary}</span>
          <span className="text-xs text-slate-600 font-mono shrink-0">{item.completed_at.slice(11, 19)}</span>
        </div>
      ))}
    </div>
  )
}

// ── Mini stat tile (compact, no hover lift) ──────────────────────────────────
function MiniStat({ value, label, icon }: { value: string | number; label: string; icon: React.ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-1 px-4 py-3 rounded-xl bg-surface/60 border border-slate-700/30">
      <div className="opacity-40">{icon}</div>
      <div className="text-2xl font-black font-mono text-accent-light leading-none">{value}</div>
      <div className="text-[10px] uppercase tracking-widest text-slate-600">{label}</div>
    </div>
  )
}

export default function AgentCard({ agent, isSelected, onSelect }: AgentCardProps) {
  const [expanded, setExpanded] = useState(false)

  // Auto-expand when this agent becomes selected for the first time
  useEffect(() => {
    if (isSelected) setExpanded(true)
  }, [isSelected])

  // Lazy fetch — only when expanded
  const { snapshot } = useSnapshot(expanded ? agent.agent_id : undefined)
  const { pauseWorkflow, resumeWorkflow, stopWorkflow } = useEngineActions()
  const uptime = useUptime(snapshot?.engine_start_epoch ?? null)

  const dot = STATUS_DOT[agent.status] ?? STATUS_DOT.idle
  const isRunning = agent.status === 'running'
  const cardClass = isRunning ? 'glass-card-active' : 'glass-card'

  const handleToggle = () => {
    setExpanded(v => !v)
    onSelect(agent.agent_id)
  }

  const handlePause  = (e: React.MouseEvent) => { e.stopPropagation(); pauseWorkflow(agent.agent_id) }
  const handleResume = (e: React.MouseEvent) => { e.stopPropagation(); resumeWorkflow(agent.agent_id) }
  const handleStop   = (e: React.MouseEvent) => { e.stopPropagation(); stopWorkflow(agent.agent_id) }

  return (
    <div className={`${cardClass} rounded-2xl overflow-hidden`}>

      {/* ── Collapsed header ── always visible ──────────────────────────── */}
      <div
        className="flex items-center justify-between px-5 py-4 cursor-pointer hover:bg-slate-800/20 transition-colors"
        onClick={handleToggle}
      >
        {/* Left: identity */}
        <div className="flex items-center gap-3 min-w-0">
          {/* Status icon */}
          <div className={`relative w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
            isRunning
              ? 'bg-gradient-to-br from-accent-light via-accent to-warn shadow-md shadow-accent/25'
              : 'bg-slate-800'
          }`}>
            <User className={`w-5 h-5 ${isRunning ? 'text-surface-hard' : 'text-slate-500'}`} />
            {isRunning && (
              <span className="absolute -top-1 -right-1 flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75" />
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-success" />
              </span>
            )}
          </div>

          {/* Agent name + workflow */}
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-mono text-base font-bold text-accent-light truncate">
                {agent.agent_id}
              </span>
              {agent.current_card_id && (
                <span className="text-xs font-mono text-slate-400 bg-slate-800/60 px-1.5 py-0.5 rounded-md border border-slate-700/40 truncate">
                  {agent.current_card_id}
                </span>
              )}
            </div>
            <div className="text-xs text-slate-500 font-mono mt-0.5">
              {agent.workflow}/{agent.version}
              {agent.is_paused && (
                <span className="ml-2 text-warn">· paused</span>
              )}
            </div>
          </div>
        </div>

        {/* Right: controls + progress% + chevron */}
        <div className="flex items-center gap-3 shrink-0 ml-3" onClick={e => e.stopPropagation()}>
          {/* Status badge */}
          <span className={`hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${
            agent.status === 'running'             ? 'bg-success/10 text-success border-success/25'
            : agent.status === 'error'             ? 'bg-danger/10 text-danger border-danger/25'
            : agent.status === 'workflow_finished' ? 'bg-accent/10 text-accent-light border-accent/25'
            :                                        'bg-slate-800/60 text-slate-500 border-slate-700/40'
          }`}>
            {dot.ping && <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" />}
            {dot.label}
          </span>

          {/* Error indicator */}
          {agent.error && (
            <AlertTriangle className="w-4 h-4 text-danger" title={agent.error} />
          )}

          {/* Control buttons */}
          <div className="flex items-center gap-1">
            {agent.is_paused ? (
              <button onClick={handleResume} className={`${CONTROL_BTN_BASE} ${CONTROL_BTN.resume}`}>
                <Play className="w-3 h-3" /> <span className="hidden sm:inline">Resume</span>
              </button>
            ) : isRunning ? (
              <button onClick={handlePause} className={`${CONTROL_BTN_BASE} ${CONTROL_BTN.pause}`}>
                <Pause className="w-3 h-3" /> <span className="hidden sm:inline">Pause</span>
              </button>
            ) : null}
            {(isRunning || agent.is_paused) && (
              <button onClick={handleStop} className={`${CONTROL_BTN_BASE} ${CONTROL_BTN.stop}`}>
                <Square className="w-3 h-3" /> <span className="hidden sm:inline">Stop</span>
              </button>
            )}
          </div>

          {/* Progress % */}
          <div className="text-right w-12">
            <div className="text-xl font-black font-mono text-accent-light glow-yellow leading-none">
              {agent.progress_pct ?? 0}%
            </div>
            <div className="text-[10px] text-slate-600 font-mono">
              {agent.card_index + 1}/{agent.total_cards}
            </div>
          </div>

          {/* Chevron */}
          <button
            onClick={handleToggle}
            className="text-slate-500 hover:text-accent-light transition-colors"
          >
            {expanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* ── Progress bar — always visible, thin ──────────────────────────── */}
      <CardProgressBar progressPct={agent.progress_pct ?? 0} />

      {/* ── Footer stats row — always visible ────────────────────────────── */}
      <div className="flex items-center gap-4 px-5 py-2 text-xs font-mono text-slate-600 border-t border-slate-700/20">
        <span>cycle <span className="text-slate-400">{agent.cycles_completed}</span></span>
        <span>done <span className="text-slate-400">{agent.completed_total}</span></span>
        {agent.started_at && (
          <span className="ml-auto text-slate-700">
            started {new Date(agent.started_at).toLocaleTimeString()}
          </span>
        )}
      </div>

      {/* ── Error banner ─────────────────────────────────────────────────── */}
      {agent.error && (
        <div className="mx-5 mb-3 px-4 py-2 rounded-xl bg-danger/8 border border-danger/25 text-xs text-danger font-mono">
          ✕ {agent.error}
        </div>
      )}

      {/* ── Expanded section — lazy, only when open ──────────────────────── */}
      {expanded && snapshot && (
        <div className="border-t border-slate-700/30 px-5 py-5 space-y-5">

          {/* Mini stats */}
          <div className="grid grid-cols-3 gap-3">
            <MiniStat value={snapshot.cycles_completed} label="Cycles"
              icon={<RefreshCw className="w-4 h-4 text-accent-light" />} />
            <MiniStat value={snapshot.completed_total} label="Done"
              icon={<CheckSquare className="w-4 h-4 text-success" />} />
            <MiniStat value={uptime} label="Uptime"
              icon={<Clock className="w-4 h-4 text-info" />} />
          </div>

          {/* Live log (last 10 lines) */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
              Live Log
            </h4>
            <LogTerminal lines={snapshot.log_lines.slice(-10)} />
          </div>

          {/* Current instruction (abbreviated) */}
          {snapshot.current_instruction && (
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
                Current Instruction
              </h4>
              <div className="prose prose-sm max-w-none max-h-40 overflow-y-auto custom-scrollbar
                              bg-surface/40 rounded-xl p-4 border border-slate-700/30 text-slate-400">
                {snapshot.current_instruction}
              </div>
            </div>
          )}

          {/* Recent completions */}
          {snapshot.history && snapshot.history.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
                Recent Completions
              </h4>
              <HistoryStrip entries={snapshot.history} />
            </div>
          )}
        </div>
      )}

      {/* Loading state while snapshot fetches */}
      {expanded && !snapshot && (
        <div className="border-t border-slate-700/30 px-5 py-8 text-center text-slate-600 text-sm italic">
          Loading agent details…
        </div>
      )}
    </div>
  )
}
