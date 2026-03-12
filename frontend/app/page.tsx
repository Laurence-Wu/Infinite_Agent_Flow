'use client'

import { useEffect, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { useAgents } from '@/lib/hooks/useAgents'
import AgentPanel from '@/components/AgentPanel'

function DashboardContent() {
  const { agents }     = useAgents()
  const searchParams   = useSearchParams()
  const router         = useRouter()
  const agentIdFromUrl = searchParams.get('agent')

  // Auto-redirect to first running agent (or first in list) when no valid selection
  useEffect(() => {
    if (agents.length === 0) return
    const ids = agents.map(a => a.agent_id)
    if (!agentIdFromUrl || !ids.includes(agentIdFromUrl)) {
      const target = agents.find(a => a.status === 'running') ?? agents[0]
      router.replace(`/?agent=${target.agent_id}`)
    }
  }, [agents, agentIdFromUrl, router])

  const activeAgent = agents.find(a => a.agent_id === agentIdFromUrl) ?? null

  if (agents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3 p-12 text-center">
        <p className="text-slate-500 italic text-sm">No agents running.</p>
        <p className="text-slate-600 text-xs">
          Start one with{' '}
          <code className="font-mono text-accent-light bg-accent/10 px-1.5 py-0.5 rounded">
            python orchestrator.py
          </code>
        </p>
      </div>
    )
  }

  if (!activeAgent) {
    return (
      <div className="flex items-center justify-center h-full text-slate-600 text-sm italic">
        Selecting agent…
      </div>
    )
  }

  return <AgentPanel agent={activeAgent} />
}

export default function Dashboard() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center h-full text-slate-600 text-sm italic">
        Loading…
      </div>
    }>
      <DashboardContent />
    </Suspense>
  )
}
