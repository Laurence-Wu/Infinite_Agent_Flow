'use client'

import { useEffect, useState } from 'react'
import type { Snapshot } from '@/lib/types'

function formatUptime(secs: number): string {
  const s = Math.floor(secs)
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const rem = s % 60
  if (h > 0) return `${h}h ${String(m).padStart(2, '0')}m`
  if (m > 0) return `${m}m ${String(rem).padStart(2, '0')}s`
  return `${rem}s`
}

interface StatCardProps {
  value: string | number
  label: string
  color: string
}
function StatCard({ value, label, color }: StatCardProps) {
  return (
    <div className="stat-card">
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      <div className="text-xs text-slate-400 uppercase tracking-wide mt-1">{label}</div>
    </div>
  )
}

export default function StatsRow({ snapshot }: { snapshot: Snapshot }) {
  const [uptime, setUptime] = useState('—')
  const [rate, setRate]     = useState('—')

  useEffect(() => {
    const epoch = snapshot.engine_start_epoch
    if (!epoch) return

    function update() {
      const secs = Date.now() / 1000 - epoch!
      setUptime(formatUptime(secs))
      if (secs > 60 && snapshot.completed_total > 0) {
        setRate((snapshot.completed_total / (secs / 3600)).toFixed(1))
      }
    }
    update()
    const id = setInterval(update, 1000)
    return () => clearInterval(id)
  }, [snapshot.engine_start_epoch, snapshot.completed_total])

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
      <StatCard value={snapshot.cycles_completed}  label="Cycles"      color="text-accent-light" />
      <StatCard value={snapshot.completed_total}   label="Cards Done"  color="text-success" />
      <StatCard value={rate}                        label="Cards / hr"  color="text-warn" />
      <StatCard value={uptime}                      label="Uptime"      color="text-slate-200" />
    </div>
  )
}
