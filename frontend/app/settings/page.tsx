'use client'

import { useState } from 'react'
import {
  Settings as SettingsIcon, Database, Moon, Bell, Sliders, PlusCircle,
  CheckCircle, XCircle, RefreshCw, ChevronDown,
} from 'lucide-react'
import { useDealers }       from '@/lib/hooks/useDealers'
import { useWorkflows }     from '@/lib/hooks/useWorkflows'
import { useEngineActions } from '@/lib/hooks/useEngineActions'
import { useSettings }      from '@/lib/context/SettingsContext'
import { STATUS_DOT }       from '@/lib/statusConfig'

// ── Reusable toggle ────────────────────────────────────────────────────────────
function Toggle({ on, onChange }: { on: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      role="switch"
      aria-checked={on}
      onClick={() => onChange(!on)}
      className={`relative w-10 h-6 rounded-full transition-colors duration-200 focus:outline-none
        ${on ? 'bg-accent' : 'bg-slate-700'}`}
    >
      <span className={`absolute top-1 w-4 h-4 bg-white rounded-full shadow transition-transform duration-200
        ${on ? 'translate-x-5' : 'translate-x-1'}`} />
    </button>
  )
}

// ── Section card wrapper ───────────────────────────────────────────────────────
function Section({ title, icon, children }: {
  title: string
  icon: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <div className="glass-card rounded-2xl overflow-hidden">
      <div className="flex items-center gap-2 px-5 py-3 border-b border-slate-700/40 bg-slate-800/30">
        <span className="text-slate-400">{icon}</span>
        <span className="text-sm font-semibold uppercase tracking-wider text-slate-400">{title}</span>
      </div>
      <div className="p-5 space-y-4">{children}</div>
    </div>
  )
}

// ── Setting row ────────────────────────────────────────────────────────────────
function SettingRow({ label, desc, children }: {
  label: string; desc?: string; children: React.ReactNode
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <div>
        <div className="text-sm font-medium text-slate-300">{label}</div>
        {desc && <div className="text-xs text-slate-500 mt-0.5">{desc}</div>}
      </div>
      {children}
    </div>
  )
}

// ── System Overview ────────────────────────────────────────────────────────────
function SystemOverview() {
  const { dealers } = useDealers()
  const running  = dealers.filter(d => d.status === 'running').length
  const paused   = dealers.filter(d => d.is_paused).length
  const errored  = dealers.filter(d => d.status === 'error').length
  const totalDone = dealers.reduce((s, d) => s + d.completed_total, 0)
  const totalCycles = dealers.reduce((s, d) => s + d.cycles_completed, 0)

  return (
    <Section title="System Overview" icon={<Database className="w-4 h-4" />}>
      <div className="grid grid-cols-2 gap-3">
        {[
          { label: 'Total Agents',   value: dealers.length,  color: 'text-slate-300' },
          { label: 'Running',        value: running,         color: 'text-success'   },
          { label: 'Paused',         value: paused,          color: 'text-warn'      },
          { label: 'Errors',         value: errored,         color: 'text-danger'    },
          { label: 'Tasks Completed',value: totalDone,       color: 'text-accent-light' },
          { label: 'Total Cycles',   value: totalCycles,     color: 'text-info'      },
        ].map(({ label, value, color }) => (
          <div key={label} className="flex items-center justify-between px-3 py-2 rounded-lg bg-surface/60 border border-slate-700/30">
            <span className="text-xs text-slate-500">{label}</span>
            <span className={`font-mono text-sm font-bold ${color}`}>{value}</span>
          </div>
        ))}
      </div>

      {dealers.length > 0 && (
        <div className="mt-2 space-y-2">
          {dealers.map(dealer => {
            const dot = STATUS_DOT[dealer.status] ?? STATUS_DOT.idle
            return (
              <div key={dealer.dealer_id} className="flex items-center justify-between text-xs font-mono">
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${dot.color}`} />
                  <span className="text-slate-400">{dealer.dealer_id}</span>
                </div>
                <div className="flex items-center gap-3 text-slate-500">
                  <span>{dealer.workflow}/{dealer.version}</span>
                  <span className="text-accent-light">{dealer.progress_pct}%</span>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </Section>
  )
}

// ── Start New Dealer ───────────────────────────────────────────────────────────
function StartDealerForm() {
  const { workflows } = useWorkflows()
  const { startDealer } = useEngineActions()
  const [workspace, setWorkspace] = useState('')
  const [workflow,  setWorkflow]  = useState('')
  const [version,   setVersion]   = useState('v1')
  const [status, setStatus] = useState<'idle' | 'loading' | 'ok' | 'error'>('idle')
  const [errMsg, setErrMsg] = useState('')

  async function handleStart() {
    if (!workspace.trim() || !workflow.trim()) return
    setStatus('loading')
    setErrMsg('')
    try {
      await startDealer(workspace.trim(), workflow.trim(), version.trim() || 'v1')
      setStatus('ok')
      setWorkspace('')
      setTimeout(() => setStatus('idle'), 3000)
    } catch (e) {
      setStatus('error')
      setErrMsg(e instanceof Error ? e.message : 'Failed to start dealer')
    }
  }

  return (
    <Section title="Start New Dealer" icon={<PlusCircle className="w-4 h-4" />}>
      <div className="space-y-3">
        <div>
          <label className="text-xs text-slate-400 mb-1 block">Workspace Path</label>
          <input
            type="text"
            value={workspace}
            onChange={e => setWorkspace(e.target.value)}
            placeholder="./workspace_3"
            className="w-full px-3 py-2 rounded-lg bg-slate-800/60 border border-slate-700/50
                       text-sm font-mono text-slate-300 placeholder-slate-600
                       focus:outline-none focus:border-accent/60"
          />
        </div>

        <div className="flex gap-2">
          <div className="flex-1">
            <label className="text-xs text-slate-400 mb-1 block">Workflow</label>
            {workflows.length > 0 ? (
              <div className="relative">
                <select
                  value={workflow}
                  onChange={e => {
                    const [wf, ver] = e.target.value.split('|')
                    setWorkflow(wf)
                    setVersion(ver)
                  }}
                  className="w-full px-3 py-2 rounded-lg bg-slate-800/60 border border-slate-700/50
                             text-sm font-mono text-slate-300 appearance-none
                             focus:outline-none focus:border-accent/60"
                >
                  <option value="">Select workflow…</option>
                  {workflows.map(wf => (
                    <option key={`${wf.name}/${wf.version}`} value={`${wf.name}|${wf.version}`}>
                      {wf.name}/{wf.version}
                    </option>
                  ))}
                </select>
                <ChevronDown className="absolute right-2 top-2.5 w-4 h-4 text-slate-500 pointer-events-none" />
              </div>
            ) : (
              <input
                type="text"
                value={workflow}
                onChange={e => setWorkflow(e.target.value)}
                placeholder="sample_workflow"
                className="w-full px-3 py-2 rounded-lg bg-slate-800/60 border border-slate-700/50
                           text-sm font-mono text-slate-300 placeholder-slate-600
                           focus:outline-none focus:border-accent/60"
              />
            )}
          </div>
          <div className="w-24">
            <label className="text-xs text-slate-400 mb-1 block">Version</label>
            <input
              type="text"
              value={version}
              onChange={e => setVersion(e.target.value)}
              placeholder="v1"
              className="w-full px-3 py-2 rounded-lg bg-slate-800/60 border border-slate-700/50
                         text-sm font-mono text-slate-300 placeholder-slate-600
                         focus:outline-none focus:border-accent/60"
            />
          </div>
        </div>

        <button
          onClick={handleStart}
          disabled={status === 'loading' || !workspace.trim() || !workflow.trim()}
          className="w-full flex items-center justify-center gap-2 px-4 py-2
                     bg-accent hover:bg-accent-light disabled:opacity-40
                     text-surface-hard font-semibold rounded-lg transition-colors text-sm"
        >
          {status === 'loading'
            ? <><RefreshCw className="w-4 h-4 animate-spin" /> Starting…</>
            : status === 'ok'
              ? <><CheckCircle className="w-4 h-4" /> Started!</>
              : <><PlusCircle className="w-4 h-4" /> Start Dealer</>
          }
        </button>

        {status === 'error' && (
          <div className="flex items-center gap-2 text-xs text-danger">
            <XCircle className="w-3.5 h-3.5 shrink-0" />
            {errMsg}
          </div>
        )}
      </div>
    </Section>
  )
}

// ── Main page ──────────────────────────────────────────────────────────────────
export default function SettingsPage() {
  const { settings, set } = useSettings()

  async function toggleNotifications(enable: boolean) {
    if (enable) {
      if (typeof Notification === 'undefined') return
      const permission = await Notification.requestPermission()
      set('notificationsEnabled', permission === 'granted')
    } else {
      set('notificationsEnabled', false)
    }
  }

  return (
    <div className="w-full px-6 py-6 space-y-6">
      <div className="flex items-center gap-3">
        <SettingsIcon className="w-6 h-6 text-slate-400" />
        <h1 className="text-xl font-bold text-gruvbox-fg">Settings</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        <SystemOverview />

        <StartDealerForm />

        {/* UI Settings */}
        <Section title="Display" icon={<Moon className="w-4 h-4" />}>
          <SettingRow
            label="Auto-expand Cards"
            desc="Dealer cards start expanded when loaded"
          >
            <Toggle
              on={settings.autoExpandCards}
              onChange={v => set('autoExpandCards', v)}
            />
          </SettingRow>
          <SettingRow
            label="Compact Log View"
            desc="Show logs at reduced height (~140px) inside expanded cards"
          >
            <Toggle
              on={settings.compactLogs}
              onChange={v => set('compactLogs', v)}
            />
          </SettingRow>
        </Section>

        {/* Notifications */}
        <Section title="Notifications" icon={<Bell className="w-4 h-4" />}>
          <SettingRow
            label="Browser Notifications"
            desc={
              typeof Notification !== 'undefined' && Notification.permission === 'denied'
                ? 'Blocked by browser — allow in site settings'
                : 'Notify when a task completes'
            }
          >
            <Toggle
              on={settings.notificationsEnabled}
              onChange={toggleNotifications}
            />
          </SettingRow>
          {settings.notificationsEnabled && (
            <p className="text-xs text-success flex items-center gap-1">
              <CheckCircle className="w-3.5 h-3.5" />
              Notifications enabled — you'll be alerted when tasks finish
            </p>
          )}
        </Section>

        {/* Advanced info */}
        <Section title="Advanced" icon={<Sliders className="w-4 h-4" />}>
          <SettingRow label="Poll Interval" desc="How often the dashboard refreshes data">
            <span className="font-mono text-xs text-slate-400">3s / 5s</span>
          </SettingRow>
          <SettingRow label="API Base" desc="Backend API the dashboard talks to">
            <span className="font-mono text-xs text-slate-400 truncate max-w-[140px]">
              {typeof window !== 'undefined' ? window.location.origin : '—'}
            </span>
          </SettingRow>
          <SettingRow label="Settings Storage" desc="Where UI preferences are saved">
            <span className="font-mono text-xs text-slate-400">localStorage</span>
          </SettingRow>
        </Section>

      </div>
    </div>
  )
}
