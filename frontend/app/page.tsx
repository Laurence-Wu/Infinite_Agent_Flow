'use client'

import { Suspense } from 'react'
import { useDealers } from '@/lib/hooks/useDealers'
import DealerPanel   from '@/components/DealerPanel'

function DashboardContent() {
  const { dealers } = useDealers()

  if (dealers.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3 p-12 text-center">
        <p className="text-slate-500 italic text-sm">No dealers running.</p>
        <p className="text-slate-600 text-xs">
          Start one with{' '}
          <code className="font-mono text-accent-light bg-accent/10 px-1.5 py-0.5 rounded">
            python orchestrator.py
          </code>
        </p>
      </div>
    )
  }

  return (
    <div className="p-4 space-y-4">
      <div className={`grid gap-4 ${dealers.length > 1 ? 'xl:grid-cols-2' : ''}`}>
        {dealers.map(dealer => (
          <DealerPanel key={dealer.dealer_id} dealer={dealer} />
        ))}
      </div>
    </div>
  )
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
