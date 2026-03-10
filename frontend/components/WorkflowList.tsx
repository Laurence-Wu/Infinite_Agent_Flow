import { GitBranch } from 'lucide-react'
import type { Workflow } from '@/lib/types'

export default function WorkflowList({ workflows }: { workflows: Workflow[] }) {
  return (
    <div className="glass-card rounded-2xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <GitBranch className="w-4 h-4 text-slate-400" />
        <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          Available Workflows
        </h2>
      </div>

      {workflows.length === 0 ? (
        <p className="text-sm text-slate-500 italic">No workflows found.</p>
      ) : (
        <ul className="space-y-2">
          {workflows.map((wf, i) => (
            <li
              key={i}
              className="flex items-center justify-between px-4 py-2.5 rounded-xl
                         bg-slate-800/30 hover:bg-slate-800/50 transition-colors duration-200"
            >
              <span className="text-sm font-medium text-slate-300">{wf.name}</span>
              <span className="text-xs font-mono text-accent-light bg-accent/10
                               px-2 py-0.5 rounded-md border border-accent/15">
                {wf.version}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
