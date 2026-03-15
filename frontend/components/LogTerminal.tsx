'use client'

import { useEffect, useRef } from 'react'
import { Terminal } from 'lucide-react'
import { lineClass } from '@/lib/formatters'

export default function LogTerminal({ lines, compact = false }: { lines: string[]; compact?: boolean }) {
  const ref = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom whenever lines change
  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight
  }, [lines])

  return (
    <div className="glass-card rounded-2xl overflow-hidden flex flex-col">

      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-slate-700/40">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Live Log
          </span>
        </div>
        <span className="text-xs font-mono text-slate-600">{lines.length} lines</span>
      </div>

      {/* Terminal body */}
      <div ref={ref} className="log-terminal" style={compact ? { height: '140px' } : undefined}>
        {lines.length === 0 ? (
          <div className="text-slate-600 italic">No log output yet.</div>
        ) : (
          lines.map((line, i) => (
            <div key={i} className={`log-line ${lineClass(line)}`}>
              {line}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
