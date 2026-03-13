'use client'

import { useEffect, useRef, useState } from 'react'

const MAX_LINES = 200

/**
 * Opens an SSE connection to /api/agent/stream and accumulates live pane
 * output lines in local state. Each line arrives within ~1 s of appearing
 * in the tmux pane.
 *
 * Falls back gracefully — if the SSE connection cannot be established
 * (e.g. no TmuxManager configured), `connected` stays false and `lines`
 * stays empty so the caller can fall back to polled pane_lines.
 */
export function useAgentStream() {
  const [lines, setLines]         = useState<string[]>([])
  const [connected, setConnected] = useState(false)
  const esRef                     = useRef<EventSource | null>(null)

  useEffect(() => {
    const es = new EventSource('/api/agent/stream')
    esRef.current = es

    es.onopen = () => setConnected(true)

    es.onerror = () => {
      setConnected(false)
      // EventSource auto-reconnects; no manual retry needed
    }

    es.onmessage = (e: MessageEvent) => {
      const line = e.data as string
      setLines(prev => {
        const next = [...prev, line]
        return next.length > MAX_LINES ? next.slice(-MAX_LINES) : next
      })
    }

    return () => {
      es.close()
      setConnected(false)
    }
  }, [])

  return { lines, connected }
}
