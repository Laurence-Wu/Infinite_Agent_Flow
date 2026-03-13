'use client'

import { useEffect, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { useDealers }  from '@/lib/hooks/useDealers'
import DealerPanel from '@/components/DealerPanel'

function DashboardContent() {
  const { dealers }      = useDealers()
  const searchParams     = useSearchParams()
  const router           = useRouter()
  const dealerIdFromUrl  = searchParams.get('dealer')

  // Auto-redirect to first running dealer (or first in list) when no valid selection
  useEffect(() => {
    if (dealers.length === 0) return
    const ids = dealers.map(d => d.dealer_id)
    if (!dealerIdFromUrl || !ids.includes(dealerIdFromUrl)) {
      const target = dealers.find(d => d.status === 'running') ?? dealers[0]
      router.replace(`/?dealer=${target.dealer_id}`)
    }
  }, [dealers, dealerIdFromUrl, router])

  const activeDealer = dealers.find(d => d.dealer_id === dealerIdFromUrl) ?? null

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

  if (!activeDealer) {
    return (
      <div className="flex items-center justify-center h-full text-slate-600 text-sm italic">
        Selecting dealer…
      </div>
    )
  }

  return <DealerPanel dealer={activeDealer} />
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
