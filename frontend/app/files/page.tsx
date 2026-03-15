'use client'

import { useAllWorkspaceScans } from '@/lib/hooks/useAllWorkspaceScans'
import { FileCode2, RefreshCw, FileText, Code, FileJson, Folder } from 'lucide-react'
import { fmtSize, extColor } from '@/lib/formatters'
import { relativeTime } from '@/lib/formatters'

function getFileIcon(path: string) {
  const ext = path.split('.').pop()?.toLowerCase()
  if (ext === 'md') return <FileText className="w-4 h-4" />
  if (ext === 'py') return <Code className="w-4 h-4" />
  if (ext === 'json') return <FileJson className="w-4 h-4" />
  return <FileCode2 className="w-4 h-4" />
}

export default function FilesPage() {
  const { files, mutate } = useAllWorkspaceScans()

  return (
    <div className="w-full px-6 py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FileCode2 className="w-6 h-6 text-accent-light" />
          <h1 className="text-xl font-bold text-gruvbox-fg">Workspace Files</h1>
          <span className="text-sm text-slate-500 font-mono">
            {files.length} {files.length === 1 ? 'file' : 'files'} across all agents
          </span>
        </div>
        <button
          onClick={() => mutate()}
          className="flex items-center gap-2 px-4 py-2 bg-accent hover:bg-accent-light
                     text-surface-hard font-semibold rounded-lg transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {files.length === 0 ? (
        <div className="glass-card rounded-2xl p-8 text-center">
          <Folder className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400">No files detected in any workspace</p>
          <p className="text-sm text-slate-500 mt-2">
            Files will appear here when agents scan their workspaces
          </p>
        </div>
      ) : (
        <div className="glass-card rounded-2xl overflow-hidden">
          <div className="grid grid-cols-12 gap-4 px-5 py-3 border-b border-slate-700/50 bg-slate-800/30 text-xs font-semibold uppercase tracking-wider text-slate-400">
            <div className="col-span-5">File Path</div>
            <div className="col-span-3">Agent</div>
            <div className="col-span-2">Modified</div>
            <div className="col-span-2 text-right">Size</div>
          </div>
          <div className="divide-y divide-slate-700/30">
            {files.map((file, i) => (
              <div
                key={i}
                className="grid grid-cols-12 gap-4 px-5 py-3 items-center
                           hover:bg-slate-800/30 transition-colors group"
              >
                <div className="col-span-5 flex items-center gap-3 min-w-0">
                  <span className={`flex-shrink-0 ${extColor(file.path)} text-surface-hard p-1.5 rounded`}>
                    {getFileIcon(file.path)}
                  </span>
                  <span className="font-mono text-sm text-slate-300 truncate group-hover:text-accent-light transition-colors">
                    {file.path}
                  </span>
                </div>
                <div className="col-span-3 text-xs font-mono text-slate-500 truncate">
                  {(file as { _dealer?: string })._dealer ?? '—'}
                </div>
                <div className="col-span-2 text-sm text-slate-500 font-mono">
                  {relativeTime(file.mtime)}
                </div>
                <div className="col-span-2 text-right text-sm text-slate-500 font-mono">
                  {fmtSize(file.size)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
