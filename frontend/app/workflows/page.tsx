'use client'

import { useState } from 'react'
import useSWR from 'swr'
import { useWorkflows } from '@/lib/hooks/useWorkflows'
import { useEngineActions } from '@/lib/hooks/useEngineActions'
import { Activity, Play, Pause, Square, RefreshCw, Plus, Terminal } from 'lucide-react'
import ExpandableCard from '@/components/ExpandableCard'
import type { AgentEntry } from '@/lib/types'

const fetcher = (url: string) => fetch(url).then(r => r.json())

export default function WorkflowsPage() {
  const { data, mutate } = useSWR<{ agents: AgentEntry[] }>('/api/agents', fetcher, {
    refreshInterval: 3000,
  })
  const { workflows } = useWorkflows()
  const { pauseWorkflow, resumeWorkflow, stopWorkflow, dealNextFor, startAgent } = useEngineActions()

  const [workspace, setWorkspace] = useState('')
  const [selectedWorkflow, setSelectedWorkflow] = useState('')
  const [version, setVersion] = useState('v1')
  const [launching, setLaunching] = useState(false)
  const [launchError, setLaunchError] = useState('')

  const agents = data?.agents ?? []

  const handleLaunch = async () => {
    if (!workspace.trim() || !selectedWorkflow) {
      setLaunchError('Workspace path and workflow are required.')
      return
    }
    setLaunching(true)
    setLaunchError('')
    try {
      await startAgent(workspace.trim(), selectedWorkflow, version || 'v1')
      setWorkspace('')
      setSelectedWorkflow('')
      setVersion('v1')
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
            value={selectedWorkflow}
            onChange={e => setSelectedWorkflow(e.target.value)}
            className="px-3 py-2 rounded-lg bg-surface-light border border-slate-700/60
                       text-sm text-slate-200 focus:outline-none focus:border-accent/50"
          >
            <option value="">— workflow —</option>
            {workflows.map(wf => (
              <option key={`${wf.name}/${wf.version}`} value={wf.name}>{wf.name}</option>
            ))}
          </select>
          <input
            type="text"
            placeholder="v1"
            value={version}
            onChange={e => setVersion(e.target.value)}
            className="w-20 px-3 py-2 rounded-lg bg-surface-light border border-slate-700/60
                       text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-accent/50"
          />
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

      {/* Agent cards */}
      {agents.length === 0 ? (
        <div className="glass-card rounded-2xl p-8 text-center">
          <p className="text-slate-400">No agents running.</p>
          <p className="text-sm text-slate-500 mt-1">Use the form above to launch one.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {agents.map(agent => (
            <ExpandableCard
              key={agent.agent_id}
              title={agent.agent_id}
              defaultExpanded={true}
              className="glass-card"
            >
              <div className="p-4 space-y-3">
                {/* Metadata rows */}
                {[
                  ['Workflow', `${agent.workflow}/${agent.version}`],
                  ['Workspace', agent.workspace],
                  ['Current Card', agent.current_card_id ?? 'N/A'],
                  ['Completed', `${agent.completed_total ?? 0} cards (${agent.cycles_completed ?? 0} cycles)`],
                  ['Last Updated', agent.last_updated
                    ? new Date(agent.last_updated).toLocaleTimeString() : 'N/A'],
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

                {/* Control buttons */}
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
            </ExpandableCard>
          ))}
        </div>
      )}
    </div>
  )
}
