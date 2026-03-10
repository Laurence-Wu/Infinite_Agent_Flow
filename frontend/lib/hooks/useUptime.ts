'use client'

import { useEffect, useState } from 'react'
import { formatUptime } from '@/lib/formatters'

/**
 * Tracks elapsed time since a Unix epoch timestamp, updating every second.
 * Returns a formatted uptime string (e.g. "1h 02m", "45s") or "—" if no epoch.
 */
export function useUptime(epoch: number | null): string {
  const [uptime, setUptime] = useState('—')

  useEffect(() => {
    if (!epoch) return
    const update = () => setUptime(formatUptime(Date.now() / 1000 - epoch))
    update()
    const id = setInterval(update, 1000)
    return () => clearInterval(id)
  }, [epoch])

  return uptime
}
