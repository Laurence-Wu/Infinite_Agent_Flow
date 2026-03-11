'use client'

import { useSnapshot } from '@/lib/hooks/useSnapshot'
import { Settings as SettingsIcon, Sliders, Database, Bell, Shield, Moon } from 'lucide-react'
import ExpandableCard from '@/components/ExpandableCard'

export default function SettingsPage() {
  const { snapshot } = useSnapshot()

  return (
    <div className="w-full px-6 py-6 space-y-6">
      <div className="flex items-center gap-3">
        <SettingsIcon className="w-6 h-6 text-slate-400" />
        <h1 className="text-xl font-bold text-gruvbox-fg">Settings</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Engine Status */}
        <ExpandableCard
          title="Engine Status"
          icon={<Database className="w-4 h-4" />}
          defaultExpanded={true}
        >
          <div className="p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-400">Status</span>
              <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${
                snapshot?.status === 'running' ? 'bg-success/20 text-success' :
                snapshot?.status === 'error' ? 'bg-danger/20 text-danger' :
                'bg-slate-600/20 text-slate-400'
              }`}>
                {snapshot?.status || 'unknown'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-400">Current Workflow</span>
              <span className="font-mono text-sm text-accent-light">
                {snapshot?.current_workflow || 'N/A'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-400">Version</span>
              <span className="font-mono text-sm text-slate-300">
                {snapshot?.current_version || 'N/A'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-400">Cards Completed</span>
              <span className="font-mono text-sm text-success">
                {snapshot?.completed_total || 0}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-400">Cycles</span>
              <span className="font-mono text-sm text-slate-300">
                {snapshot?.cycles_completed || 0}
              </span>
            </div>
          </div>
        </ExpandableCard>

        {/* Display Settings */}
        <ExpandableCard
          title="Display"
          icon={<Moon className="w-4 h-4" />}
        >
          <div className="p-4 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-sm font-medium text-slate-300">Dark Mode</span>
                <p className="text-xs text-slate-500">Use dark theme</p>
              </div>
              <div className="w-10 h-6 bg-accent rounded-full relative cursor-pointer">
                <div className="absolute right-1 top-1 w-4 h-4 bg-surface-hard rounded-full" />
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <span className="text-sm font-medium text-slate-300">Animations</span>
                <p className="text-xs text-slate-500">Enable UI animations</p>
              </div>
              <div className="w-10 h-6 bg-accent rounded-full relative cursor-pointer">
                <div className="absolute right-1 top-1 w-4 h-4 bg-surface-hard rounded-full" />
              </div>
            </div>
          </div>
        </ExpandableCard>

        {/* Notification Settings */}
        <ExpandableCard
          title="Notifications"
          icon={<Bell className="w-4 h-4" />}
        >
          <div className="p-4 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-sm font-medium text-slate-300">Task Complete</span>
                <p className="text-xs text-slate-500">Notify when a task finishes</p>
              </div>
              <div className="w-10 h-6 bg-accent rounded-full relative cursor-pointer">
                <div className="absolute right-1 top-1 w-4 h-4 bg-surface-hard rounded-full" />
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <span className="text-sm font-medium text-slate-300">Errors</span>
                <p className="text-xs text-slate-500">Notify on errors</p>
              </div>
              <div className="w-10 h-6 bg-accent rounded-full relative cursor-pointer">
                <div className="absolute right-1 top-1 w-4 h-4 bg-surface-hard rounded-full" />
              </div>
            </div>
          </div>
        </ExpandableCard>

        {/* Advanced Settings */}
        <ExpandableCard
          title="Advanced"
          icon={<Sliders className="w-4 h-4" />}
        >
          <div className="p-4 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-sm font-medium text-slate-300">Auto-refresh</span>
                <p className="text-xs text-slate-500">Refresh data automatically</p>
              </div>
              <div className="w-10 h-6 bg-accent rounded-full relative cursor-pointer">
                <div className="absolute right-1 top-1 w-4 h-4 bg-surface-hard rounded-full" />
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <span className="text-sm font-medium text-slate-300">Debug Mode</span>
                <p className="text-xs text-slate-500">Show debug information</p>
              </div>
              <div className="w-10 h-6 bg-slate-700 rounded-full relative cursor-pointer">
                <div className="absolute left-1 top-1 w-4 h-4 bg-slate-400 rounded-full" />
              </div>
            </div>
          </div>
        </ExpandableCard>
      </div>
    </div>
  )
}
