'use client'

import { FileText } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'

interface Props {
  markdown: string
}

export default function TaskPreview({ markdown }: Props) {
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
