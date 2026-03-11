'use client'

import { useState, useMemo } from 'react'
import { useLogs } from '@/lib/hooks/useLogs'
import { 
  Terminal, Trash2, Download, Filter, AlertCircle, AlertTriangle, 
  Info, Bug, ChevronDown, ChevronUp, Activity, XCircle 
} from 'lucide-react'
import { 
  parseLogLines, 
  LOG_COLORS, 
  getLogEntryClasses,
  getWorkflowStatusFromLogs,
  extractWorkflowEvents,
  type LogLevel,
  type LogCategory,
  type ParsedLogEntry,
} from '@/lib/logParser'

export default function LogsPage() {
  const { logs, isLoading } = useLogs()
  const [filterLevel, setFilterLevel] = useState<LogLevel | 'all'>('all')
  const [filterCategory, setFilterCategory] = useState<LogCategory | 'all'>('all')
  const [expandedLogs, setExpandedLogs] = useState<Set<string>>(new Set())
  const [showWorkflowEvents, setShowWorkflowEvents] = useState(false)

  // Parse all logs into structured entries
  const parsedLogs = useMemo(() => parseLogLines(logs), [logs])

  // Get workflow status from logs
  const workflowStatus = useMemo(() => getWorkflowStatusFromLogs(parsedLogs), [parsedLogs])

  // Extract workflow events for quick overview
  const workflowEvents = useMemo(() => extractWorkflowEvents(parsedLogs), [parsedLogs])

  // Filter logs
  const filteredLogs = useMemo(() => {
    let filtered = parsedLogs

    if (filterLevel !== 'all') {
      filtered = filtered.filter(log => log.level === filterLevel)
    }

    if (filterCategory !== 'all') {
      filtered = filtered.filter(log => log.category === filterCategory)
    }

    if (showWorkflowEvents) {
      filtered = workflowEvents
    }

    return filtered.reverse() // Show newest first
  }, [parsedLogs, filterLevel, filterCategory, showWorkflowEvents, workflowEvents])

  const toggleExpand = (id: string) => {
    setExpandedLogs((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const downloadLogs = () => {
    const blob = new Blob([logs.join('\n')], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `logs-${new Date().toISOString().slice(0, 19)}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  const clearFilters = () => {
    setFilterLevel('all')
    setFilterCategory('all')
    setShowWorkflowEvents(false)
  }

  const LevelIcon = ({ level }: { level: LogLevel }) => {
    switch (level) {
      case 'DEBUG': return <Bug className="w-3.5 h-3.5" />
      case 'INFO': return <Info className="w-3.5 h-3.5" />
      case 'WARNING': return <AlertTriangle className="w-3.5 h-3.5" />
      case 'ERROR': return <AlertCircle className="w-3.5 h-3.5" />
      case 'FATAL': return <XCircle className="w-3.5 h-3.5" />
    }
  }

  return (
    <div className="w-full px-6 py-6 space-y-4">
      {/* Header with status */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Terminal className="w-6 h-6 text-slate-400" />
          <h1 className="text-xl font-bold text-gruvbox-fg">Live Logs</h1>
          <span className="text-sm text-slate-500 font-mono">
            {logs.length} {logs.length === 1 ? 'line' : 'lines'}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {/* Workflow status indicator */}
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border ${
            workflowStatus.status === 'healthy' ? 'bg-success/10 border-success/30' :
            workflowStatus.status === 'warning' ? 'bg-warn/10 border-warn/30' :
            workflowStatus.status === 'error' ? 'bg-danger/10 border-danger/30' :
            'bg-danger/20 border-danger/50'
          }`}>
            <Activity className={`w-4 h-4 ${
              workflowStatus.status === 'healthy' ? 'text-success' :
              workflowStatus.status === 'warning' ? 'text-warn' :
              'text-danger'
            }`} />
            <span className={`text-xs font-semibold ${
              workflowStatus.status === 'healthy' ? 'text-success' :
              workflowStatus.status === 'warning' ? 'text-warn' :
              'text-danger'
            }`}>
              {workflowStatus.message}
            </span>
          </div>
          <button
            onClick={downloadLogs}
            className="flex items-center gap-2 px-4 py-1.5 bg-slate-800 hover:bg-slate-700
                       text-slate-300 rounded-lg transition-colors text-sm font-medium"
          >
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="glass-card rounded-xl p-4">
        <div className="flex items-center gap-3 flex-wrap">
          <Filter className="w-4 h-4 text-slate-500" />
          
          {/* Level filter */}
          <select
            value={filterLevel}
            onChange={(e) => setFilterLevel(e.target.value as LogLevel | 'all')}
            className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg
                       text-sm text-slate-300 focus:outline-none focus:border-accent"
          >
            <option value="all">All Levels</option>
            <option value="DEBUG">Debug</option>
            <option value="INFO">Info</option>
            <option value="WARNING">Warning</option>
            <option value="ERROR">Error</option>
            <option value="FATAL">Fatal</option>
          </select>

          {/* Category filter */}
          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value as LogCategory | 'all')}
            className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg
                       text-sm text-slate-300 focus:outline-none focus:border-accent"
          >
            <option value="all">All Sources</option>
            <option value="orchestrator">Orchestrator</option>
            <option value="planner">Planner</option>
            <option value="dealer">Dealer</option>
            <option value="picker">Picker</option>
            <option value="workflow">Workflow</option>
            <option value="system">System</option>
            <option value="unknown">Other</option>
          </select>

          {/* Workflow events toggle */}
          <button
            onClick={() => setShowWorkflowEvents(!showWorkflowEvents)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              showWorkflowEvents
                ? 'bg-accent/20 text-accent-light border border-accent/30'
                : 'bg-slate-800 text-slate-400 border border-slate-700'
            }`}
          >
            Events Only
          </button>

          {/* Clear filters */}
          {(filterLevel !== 'all' || filterCategory !== 'all' || showWorkflowEvents) && (
            <button
              onClick={clearFilters}
              className="px-3 py-1.5 text-sm text-slate-500 hover:text-slate-300 transition-colors"
            >
              Clear
            </button>
          )}

          {/* Count badge */}
          <span className="ml-auto text-xs font-mono text-slate-500">
            Showing {filteredLogs.length} of {parsedLogs.length}
          </span>
        </div>
      </div>

      {/* Loading state */}
      {isLoading ? (
        <div className="text-center py-12 text-slate-500">Loading logs...</div>
      ) : filteredLogs.length === 0 ? (
        <div className="glass-card rounded-2xl p-8 text-center">
          <Terminal className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400">
            {logs.length === 0 ? 'No log output yet' : 'No logs match the current filter'}
          </p>
        </div>
      ) : (
        /* Log entries */
        <div className="glass-card rounded-2xl overflow-hidden">
          <div className="max-h-[600px] overflow-y-auto custom-scrollbar">
            {filteredLogs.map((entry, i) => {
              const classes = getLogEntryClasses(entry)
              const isExpanded = expandedLogs.has(entry.id)

              return (
                <div
                  key={entry.id}
                  className={`border-b border-slate-800/50 ${classes.container} transition-colors`}
                >
                  {/* Main log row */}
                  <div 
                    className="flex items-start gap-3 p-3 cursor-pointer hover:bg-slate-800/30"
                    onClick={() => toggleExpand(entry.id)}
                  >
                    {/* Expand/collapse indicator */}
                    <div className="mt-0.5">
                      {isExpanded ? (
                        <ChevronUp className="w-4 h-4 text-slate-500" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-slate-500" />
                      )}
                    </div>

                    {/* Level icon */}
                    <div className={`flex-shrink-0 ${classes.icon}`}>
                      <LevelIcon level={entry.level} />
                    </div>

                    {/* Timestamp */}
                    <span className="font-mono text-xs text-slate-500 flex-shrink-0 pt-0.5">
                      {entry.timestamp}
                    </span>

                    {/* Level badge */}
                    <span className={`text-xs px-2 py-0.5 rounded font-mono flex-shrink-0 ${classes.badge}`}>
                      {entry.level}
                    </span>

                    {/* Source/Category */}
                    <span className={`text-xs font-mono flex-shrink-0 pt-0.5 ${
                      entry.category !== 'unknown' 
                        ? 'text-gruvbox-purple-bright' 
                        : 'text-slate-500'
                    }`}>
                      [{entry.source}]
                    </span>

                    {/* Message preview */}
                    <span className={`text-sm flex-1 ${classes.text} line-clamp-1`}>
                      {entry.message}
                    </span>
                  </div>

                  {/* Expanded content */}
                  {isExpanded && (
                    <div className="px-3 pb-3 pl-12">
                      <div className={`p-3 rounded-lg bg-slate-900/80 border ${classes.border}`}>
                        <div className="flex items-center gap-2 mb-2 text-xs font-mono text-slate-500">
                          <span>Full Message:</span>
                        </div>
                        <p className={`text-sm font-mono ${classes.text} whitespace-pre-wrap break-words`}>
                          {entry.message}
                        </p>
                      </div>
                      
                      {/* Additional context for errors */}
                      {(entry.level === 'ERROR' || entry.level === 'FATAL') && (
                        <div className="mt-2 p-3 rounded-lg bg-danger/10 border border-danger/30">
                          <div className="flex items-center gap-2 text-xs text-danger mb-1">
                            <AlertCircle className="w-3.5 h-3.5" />
                            <span className="font-semibold">Error Details</span>
                          </div>
                          <p className="text-xs text-slate-400 font-mono">
                            Source: {entry.source} • Category: {entry.category}
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
