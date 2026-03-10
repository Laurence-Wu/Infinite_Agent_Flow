'use client'

import { ScanLine } from 'lucide-react'
import type { WorkspaceScanEntry } from '@/lib/types'
import { extColor, relativeTime, fmtSize } from '@/lib/formatters'

interface Props {
  files: WorkspaceScanEntry[]
}

export default function WorkspaceScan({ files }: Props) {
  const now = Date.now()

  return (
    <div className="glass-card rounded-2xl overflow-hidden">

      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-slate-700/40">
        <div className="flex items-center gap-2">
          <ScanLine className="w-4 h-4 text-accent-light" />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Workspace Activity
          </span>
        </div>
        {/* Staggered scanner dots */}
        <div className="flex items-center gap-1">
          <span className="w-1 h-1 rounded-full bg-accent animate-scanner-dot1" />
          <span className="w-1 h-1 rounded-full bg-accent animate-scanner-dot2" />
          <span className="w-1 h-1 rounded-full bg-accent animate-scanner-dot3" />
        </div>
      </div>

      {/* File list */}
      <ul className="divide-y divide-slate-700/20 max-h-64 overflow-y-auto custom-scrollbar">
        {files.length === 0 ? (
          <li className="px-5 py-6 text-center text-xs text-slate-500 italic">
            No files detected in workspace.
          </li>
        ) : (
          files.map((f) => {
            const ageSecs = Math.floor((now - new Date(f.mtime).getTime()) / 1000)
            const isHot   = ageSecs < 5
            const isWarm  = ageSecs < 30

            return (
              <li
                key={f.path}
                className={`flex items-center gap-3 px-5 py-2.5 transition-colors duration-300 ${
                  isHot  ? 'bg-accent/[.08]' :
                  isWarm ? 'bg-accent/[.04]' : ''
                }`}
              >
                {/* Extension color dot */}
                <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${extColor(f.path)} ${
                  isHot ? 'animate-soft-pulse' : ''
                }`} />

                {/* File path */}
                <span className={`font-mono text-xs flex-1 truncate ${
                  isHot  ? 'text-accent-light' :
                  isWarm ? 'text-slate-300'    : 'text-slate-500'
                }`}>
                  {f.path}
                </span>

                {/* File size */}
                <span className="text-xs text-slate-600 flex-shrink-0 w-14 text-right">
                  {fmtSize(f.size)}
                </span>

                {/* Relative time */}
                <span className={`text-xs flex-shrink-0 w-16 text-right ${
                  isHot ? 'text-accent-light font-medium' : 'text-slate-600'
                }`}>
                  {relativeTime(f.mtime)}
                </span>
              </li>
            )
          })
        )}
      </ul>
    </div>
  )
}
