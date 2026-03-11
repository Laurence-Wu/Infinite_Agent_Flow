'use client'

import { useEffect, useMemo, useState } from 'react'
import useSWR from 'swr'
import { useWorkflows } from '@/lib/hooks/useWorkflows'
import { useEngineActions } from '@/lib/hooks/useEngineActions'
import {
  Activity,
  Play,
  Pause,
  Square,
  RefreshCw,
  Plus,
  Terminal,
  LayoutList,
  Grid3x3,
  Columns3,
} from 'lucide-react'
import ExpandableCard from '@/components/ExpandableCard'
import type { AgentEntry } from '@/lib/types'
import {
  groupWorkflows,
  parseWorkflowKey,
  workflowKey,
  getBoardLane,
  type WorkflowBoardLane,
} from '@/lib/workflowUtils'

const fetcher = (url: string) => fetch(url).then(r => r.json())
type LayoutMode = 'list' | 'grid' | 'board'
const LAYOUT_STORAGE_KEY = 'carddealer.workflows.layout'

export default function WorkflowsPage() {
  const { data, mutate } = useSWR<{ agents: AgentEntry[] }>('/api/agents', fetcher, {
    refreshInterval: 3000,
  })
  const { workflows } = useWorkflows()
  const { pauseWorkflow, resumeWorkflow, stopWorkflow, dealNextFor, startAgent } = useEngineActions()

  const [workspace, setWorkspace] = useState('')
  const [selectedWorkflowKey, setSelectedWorkflowKey] = useState('')
  const [layoutMode, setLayoutMode] = useState<LayoutMode>('list')
  const [launching, setLaunching] = useState(false)
  const [launchError, setLaunchError] = useState('')

  const agents = data?.agents ?? []
  const groupedAgents = useMemo(() => groupWorkflows(workflows, agents), [workflows, agents])

  useEffect(() => {
    const saved = window.localStorage.getItem(LAYOUT_STORAGE_KEY) as LayoutMode | null
    if (saved === 'list' || saved === 'grid' || saved === 'board') {
      setLayoutMode(saved)
    }
  }, [])

  useEffect(() => {
    window.localStorage.setItem(LAYOUT_STORAGE_KEY, layoutMode)
  }, [layoutMode])

  useEffect(() => {
    if (selectedWorkflowKey) return
    if (workflows.length === 0) return
    const first = workflows[0]
    setSelectedWorkflowKey(workflowKey(first.name, first.version))
  }, [selectedWorkflowKey, workflows])

  const [expandedWorkflows, setExpandedWorkflows] = useState<Record<string, boolean>>({})

  const workflowExpanded = (key: string) => {
    if (groupedAgents.length === 1) return true
    return !!expandedWorkflows[key]
  }

  const setWorkflowExpanded = (key: string, next: boolean) => {
    setExpandedWorkflows(prev => ({ ...prev, [key]: next }))
  }

  const handleLaunch = async () => {
    if (!workspace.trim() || !selectedWorkflowKey) {
      setLaunchError('Workspace path and workflow are required.')
      return
    }
    const { name, version } = parseWorkflowKey(selectedWorkflowKey)
    setLaunching(true)
    setLaunchError('')
    try {
      await startAgent(workspace.trim(), name, version || 'v1')
      setWorkspace('')
      mutate()
    } catch {
      setLaunchError('Failed to launch agent. Check the workspace path and workflow name.')
    } finally {
      setLaunching(false)
    }
  }

  const statusBadge = (agent: AgentEntry) => {
    const label = agent.is_paused ? 'paused' : agent.status
    const cls =
      label === 'running' ? 'bg-success/20 text-success' :
      label === 'paused' ? 'bg-warn/20 text-warn' :
      label === 'error' ? 'bg-danger/20 text-danger' :
      'bg-slate-600/20 text-slate-400'
    return <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${cls}`}>{label}</span>
  }

  const laneTitle = (lane: WorkflowBoardLane) => {
    if (lane === 'running') return 'Running'
    if (lane === 'paused') return 'Paused'
    if (lane === 'error') return 'Error'
    return 'Other'
  }

  const laneTone = (lane: WorkflowBoardLane) => {
    if (lane === 'running') return 'text-success border-success/30 bg-success/5'
    if (lane === 'paused') return 'text-warn border-warn/30 bg-warn/5'
    if (lane === 'error') return 'text-danger border-danger/30 bg-danger/5'
    return 'text-slate-400 border-slate-700/40 bg-slate-900/30'
  }

  const AgentCard = ({ agent }: { agent: AgentEntry }) => (
    <div key={agent.agent_id} className="rounded-xl border border-slate-700/50 bg-slate-900/20">
      <div className="px-4 py-3 border-b border-slate-700/40">
        <div className="text-sm font-semibold text-slate-300 truncate">{agent.agent_id}</div>
      </div>

      <div className="p-4 space-y-3">
        {[
          ['Workflow', `${agent.workflow}/${agent.version}`],
          ['Workspace', agent.workspace],
          ['Current Card', agent.current_card_id ?? 'N/A'],
          ['Completed', `${agent.completed_total ?? 0} cards (${agent.cycles_completed ?? 0} cycles)`],
          ['Last Updated', agent.last_updated ? new Date(agent.last_updated).toLocaleTimeString() : 'N/A'],
        ].map(([label, value]) => (
          <div key={label} className="flex items-center justify-between">
            <span className="text-sm text-slate-400">{label}</span>
            <span className="font-mono text-xs text-slate-300 max-w-48 truncate text-right">
              {value}
            </span>
          </div>
        ))}

        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-400">Status</span>
          {statusBadge(agent)}
        </div>

        <div className="flex gap-2 pt-3 border-t border-slate-700/50">
          <button
            onClick={() => dealNextFor(agent.agent_id).then(() => mutate())}
            className="flex-1 flex items-center justify-center gap-1 px-3 py-1.5
                       bg-accent/20 hover:bg-accent/30 text-accent-light rounded transition-colors text-sm"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Deal Next
          </button>

          {agent.is_paused ? (
            <button
              onClick={() => resumeWorkflow(agent.agent_id).then(() => mutate())}
              className="flex-1 flex items-center justify-center gap-1 px-3 py-1.5
                         bg-success/20 hover:bg-success/30 text-success rounded transition-colors text-sm"
            >
              <Play className="w-3.5 h-3.5" />
              Resume
            </button>
          ) : (
            <button
              onClick={() => pauseWorkflow(agent.agent_id).then(() => mutate())}
              className="flex-1 flex items-center justify-center gap-1 px-3 py-1.5
                         bg-warn/20 hover:bg-warn/30 text-warn rounded transition-colors text-sm"
            >
              <Pause className="w-3.5 h-3.5" />
              Pause
            </button>
          )}

          <button
            onClick={() => stopWorkflow(agent.agent_id).then(() => mutate())}
            className="flex-1 flex items-center justify-center gap-1 px-3 py-1.5
                       bg-danger/20 hover:bg-danger/30 text-danger rounded transition-colors text-sm"
          >
            <Square className="w-3.5 h-3.5" />
            Stop
          </button>
        </div>
      </div>
    </div>
  )

  const layoutButtons: { mode: LayoutMode; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
    { mode: 'list', label: 'List', icon: LayoutList },
    { mode: 'grid', label: 'Grid', icon: Grid3x3 },
    { mode: 'board', label: 'Board', icon: Columns3 },
  ]

  return (
    <div className="w-full px-6 py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Activity className="w-6 h-6 text-accent-light" />
        <h1 className="text-xl font-bold text-gruvbox-fg">Agent Workflows</h1>
        <span className="ml-auto text-xs text-slate-500 font-mono">{agents.length} agent(s)</span>
      </div>

      {/* Launch Agent form */}
      <div className="glass-card rounded-2xl p-5 space-y-3">
        <div className="flex items-center gap-2 mb-1">
          <Plus className="w-4 h-4 text-accent-light" />
          <h2 className="text-sm font-semibold text-slate-300">Launch New Agent</h2>
        </div>
        <div className="flex flex-wrap gap-3">
          <input
            type="text"
            placeholder="Workspace path  (e.g. C:/projects/myapp)"
            value={workspace}
            onChange={e => setWorkspace(e.target.value)}
            className="flex-1 min-w-48 px-3 py-2 rounded-lg bg-surface-light border border-slate-700/60
                       text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-accent/50"
          />
          <select
            value={selectedWorkflowKey}
            onChange={e => setSelectedWorkflowKey(e.target.value)}
            className="px-3 py-2 rounded-lg bg-surface-light border border-slate-700/60
                       text-sm text-slate-200 focus:outline-none focus:border-accent/50"
          >
            <option value="">— workflow —</option>
            {workflows.map(wf => (
              <option key={workflowKey(wf.name, wf.version)} value={workflowKey(wf.name, wf.version)}>
                {wf.name} / {wf.version}
              </option>
            ))}
          </select>
          <button
            onClick={handleLaunch}
            disabled={launching}
            className="flex items-center gap-2 px-4 py-2 bg-accent hover:bg-accent-light disabled:opacity-50
                       text-surface-hard font-semibold rounded-lg transition-colors text-sm"
          >
            <Terminal className="w-4 h-4" />
            {launching ? 'Launching…' : 'Launch'}
          </button>
        </div>
        {launchError && <p className="text-xs text-danger mt-1">{launchError}</p>}
      </div>

      {/* Layout controls */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs uppercase tracking-wider text-slate-500">Layout</span>
        {layoutButtons.map(({ mode, label, icon: Icon }) => {
          const active = layoutMode === mode
          return (
            <button
              key={mode}
              onClick={() => setLayoutMode(mode)}
              className={`inline-flex items-center gap-2 rounded-lg border px-3 py-1.5 text-sm transition-colors ${
                active
                  ? 'border-accent/40 bg-accent/15 text-accent-light'
                  : 'border-slate-700/60 bg-slate-900/20 text-slate-400 hover:bg-slate-800/40'
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          )
        })}
      </div>

      {/* Agent cards grouped by workflow */}
      {groupedAgents.length === 0 ? (
        <div className="glass-card rounded-2xl p-8 text-center">
          <p className="text-slate-400">No agents running.</p>
          <p className="text-sm text-slate-500 mt-1">Use the form above to launch one.</p>
        </div>
      ) : layoutMode === 'grid' ? (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {groupedAgents.map(group => (
            <div key={group.key} className="glass-card rounded-2xl p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-slate-300">{group.name}</h3>
                <span className="text-xs font-mono text-accent-light bg-accent/10 px-2 py-0.5 rounded-md border border-accent/15">
                  {group.version}
                </span>
              </div>
              {group.agents.length === 0 ? (
                <p className="text-xs text-slate-500 italic">No active agents for this workflow yet.</p>
              ) : (
                <div className="space-y-3">
                  {group.agents.map(agent => <AgentCard key={agent.agent_id} agent={agent} />)}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : layoutMode === 'board' ? (
        <div className="grid grid-cols-1 xl:grid-cols-4 gap-4">
          {(['running', 'paused', 'error', 'other'] as WorkflowBoardLane[]).map(lane => {
            const laneGroups = groupedAgents.filter(group => getBoardLane(group) === lane)
            return (
              <div key={lane} className={`rounded-2xl border p-4 ${laneTone(lane)}`}>
                <div className="mb-3 flex items-center justify-between">
                  <h3 className="text-sm font-semibold">{laneTitle(lane)}</h3>
                  <span className="text-xs">{laneGroups.length}</span>
                </div>
                <div className="space-y-3">
                  {laneGroups.length === 0 ? (
                    <div className="text-xs italic text-slate-500">No workflows in this lane.</div>
                  ) : (
                    laneGroups.map(group => (
                      <div key={group.key} className="rounded-lg border border-slate-700/40 bg-slate-950/30 p-3">
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-xs font-semibold text-slate-300 truncate">{group.name}</span>
                          <span className="text-[11px] text-slate-500">{group.version}</span>
                        </div>
                        <div className="mt-2 text-[11px] text-slate-500">{group.agents.length} active agent(s)</div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <div className="space-y-6">
          {groupedAgents.map(group => (
            <ExpandableCard
              key={group.key}
              title={`${group.name} / ${group.version}`}
              isExpanded={workflowExpanded(group.key)}
              onToggle={next => setWorkflowExpanded(group.key, next)}
              className="glass-card"
              expandedContent={
                group.agents.length === 0 ? (
                  <div className="text-sm text-slate-500 italic">No active agents for this workflow yet.</div>
                ) : (
                  <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                    {group.agents.map(agent => <AgentCard key={agent.agent_id} agent={agent} />)}
                  </div>
                )
              }
            >
              <div className="px-4 py-3 text-xs text-slate-500">
                {group.agents.length} active agent(s)
              </div>
            </ExpandableCard>
          ))}
        </div>
      )}
    </div>
  )
}
