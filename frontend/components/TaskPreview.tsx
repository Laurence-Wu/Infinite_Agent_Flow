'use client'

import { FileText } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import { parseChecklist } from '@/lib/formatters'

interface Props {
  markdown: string
}

export default function TaskPreview({ markdown }: Props) {
  const cl = parseChecklist(markdown)

  return (
    <div className="glass-card rounded-2xl overflow-hidden h-full">

      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-slate-700/40">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-accent-light" />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Current Task
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500 font-mono">live</span>
          <div className="w-1.5 h-1.5 rounded-full bg-accent animate-soft-pulse" />
        </div>
      </div>

      {/* Checklist progress strip — only shown when task has checklist items */}
      {cl && (
        <div className="px-5 py-2.5 border-b border-slate-700/30 flex items-center gap-3">
          <div className="flex-1 h-1.5 bg-surface-lighter rounded-full overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-accent-dim to-accent-light
                         transition-all duration-700 ease-out"
              style={{ width: `${Math.round((cl.done / cl.total) * 100)}%` }}
            />
          </div>
          <span className="text-xs font-mono text-slate-400 flex-shrink-0">
            <span className="text-accent-light font-semibold">{cl.done}</span>
            <span className="text-slate-600"> / {cl.total} steps</span>
          </span>
        </div>
      )}

      {/* Rendered markdown */}
      <div className="prose p-6 max-h-[560px] overflow-y-auto custom-scrollbar">
        {markdown ? (
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeHighlight]}
          >
            {markdown}
          </ReactMarkdown>
        ) : (
          <p className="text-slate-500 italic text-sm">No active task.</p>
        )}
      </div>
    </div>
  )
}
