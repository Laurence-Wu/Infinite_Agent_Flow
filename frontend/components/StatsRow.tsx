'use client'

import { useState, useEffect } from 'react'
import { RefreshCw, CheckSquare, Gauge, Clock } from 'lucide-react'
import type { Snapshot } from '@/lib/types'
import { useUptime } from '@/lib/hooks/useUptime'

interface StatCardProps {
  value: string | number
  label: string
  valueClass: string
  glowClass:  string
  icon: React.ReactNode
}

function StatCard({ value, label, valueClass, glowClass, icon }: StatCardProps) {
  return (
    <div className="stat-card">
      {/* Icon */}
      <div className="flex justify-center mb-2 opacity-40">
        {icon}
      </div>
      {/* Value — dominant */}
      <div className={`text-4xl font-black leading-none tracking-tight ${valueClass} ${glowClass}`}>
        {value}
      </div>
      {/* Label */}
      <div className="text-xs text-slate-600 uppercase tracking-widest mt-2 font-medium">
        {label}
      </div>
    </div>
  )
}

export default function StatsRow({ snapshot }: { snapshot: Snapshot }) {
  const uptime = useUptime(snapshot.engine_start_epoch)
  const [rate, setRate] = useState('—')

  useEffect(() => {
    if (!snapshot.engine_start_epoch) return
    const secs = Date.now() / 1000 - snapshot.engine_start_epoch
    if (secs > 60 && snapshot.completed_total > 0) {
      setRate((snapshot.completed_total / (secs / 3600)).toFixed(1))
    }
  }, [snapshot.engine_start_epoch, snapshot.completed_total])

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
      <StatCard
        value={snapshot.cycles_completed}
        label="Cycles"
        valueClass="text-accent-light"
        glowClass="glow-yellow"
        icon={<RefreshCw className="w-5 h-5 text-accent-light" />}
      />
      <StatCard
        value={snapshot.completed_total}
        label="Cards Done"
        valueClass="text-success"
        glowClass="glow-green"
        icon={<CheckSquare className="w-5 h-5 text-success" />}
      />
      <StatCard
        value={rate}
        label="Cards / hr"
        valueClass="text-warn"
        glowClass="glow-orange"
        icon={<Gauge className="w-5 h-5 text-warn" />}
      />
      <StatCard
        value={uptime}
        label="Uptime"
        valueClass="text-info"
        glowClass="glow-blue"
        icon={<Clock className="w-5 h-5 text-info" />}
      />
    </div>
  )
}
