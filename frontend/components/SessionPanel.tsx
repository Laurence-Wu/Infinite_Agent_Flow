'use client'

import { useRef, useEffect } from 'react'
import { Terminal, Play, Square, RefreshCw } from 'lucide-react'
import { useSession } from '@/lib/hooks/useSession'
import { useEngineActions } from '@/lib/hooks/useEngineActions'
import { CONTROL_BTN, CONTROL_BTN_BASE } from '@/lib/statusConfig'

export default function SessionPanel() {
  const { session, isLoading } = useSession()
  const { startSession, stopSession, restartSession } = useEngineActions()
  const paneRef = useRef<HTMLDivElement>(null)

  // Auto-scroll pane output to bottom
  useEffect(() => {
    if (paneRef.current) paneRef.current.scrollTop = paneRef.current.scrollHeight
  }, [session.pane_lines])

  const alive   = session.alive
  const starting = session.starting
  const name    = session.session_name || '—'
  const cmd     = session.agent_command || '—'

  return (
    <div className="glass-card rounded-2xl overflow-hidden">

      {/* ── Header ── */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-slate-700/40">
        <div className="flex items-center gap-3">
          <Terminal className="w-4 h-4 text-slate-400" />
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Agent Session
            </span>
            <span className="ml-2 text-xs font-mono text-slate-600">
              {name}
            </span>
          </div>
          {/* Status badge */}
          <span className={`flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-semibold border ${
            starting
              ? 'bg-warn/10 text-warn border-warn/25'
              : alive
                ? 'bg-success/10 text-success border-success/25'
                : 'bg-slate-800/60 text-slate-500 border-slate-700/40'
          }`}>
            <span className={`w-1.5 h-1.5 rounded-full ${
              starting ? 'bg-warn animate-pulse'
              : alive   ? 'bg-success animate-pulse'
              :           'bg-slate-600'
            }`} />
            {starting ? 'Starting…' : alive ? 'Alive' : 'Dead'}
          </span>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-1.5">
          <span className="text-xs font-mono text-slate-700 mr-1">{cmd}</span>
          {!alive && !starting && (
            <button
              onClick={startSession}
              disabled={isLoading}
              className={`${CONTROL_BTN_BASE} ${CONTROL_BTN.resume}`}
            >
              <Play className="w-3 h-3" />
              <span className="hidden sm:inline">Start</span>
            </button>
          )}
          {(alive || starting) && (
            <button
              onClick={stopSession}
              disabled={isLoading}
              className={`${CONTROL_BTN_BASE} ${CONTROL_BTN.stop}`}
            >
              <Square className="w-3 h-3" />
              <span className="hidden sm:inline">Stop</span>
            </button>
          )}
          <button
            onClick={restartSession}
            disabled={isLoading || starting}
            className={`${CONTROL_BTN_BASE} ${CONTROL_BTN.pause}`}
          >
            <RefreshCw className="w-3 h-3" />
            <span className="hidden sm:inline">Restart</span>
          </button>
        </div>
      </div>

      {/* ── Pane output ── */}
      <div
        ref={paneRef}
        className="log-terminal max-h-48"
        style={{ minHeight: '6rem' }}
      >
        {session.pane_lines.length === 0 ? (
          <div className="text-slate-600 italic text-xs">
            {alive ? 'No pane output captured.' : 'Session is not running.'}
          </div>
        ) : (
          session.pane_lines.slice(-20).map((line, i) => (
            <div key={i} className="log-line text-slate-400 font-mono text-xs">
              {line}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
