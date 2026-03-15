'use client'

import { useEffect, useRef, useState } from 'react'

const MAX_LINES = 200
// Connect directly to Flask — bypasses the Next.js proxy which does
// not support long-lived SSE streams and logs ECONNRESET on every disconnect.
const FLASK_ORIGIN = `http://127.0.0.1:${process.env.NEXT_PUBLIC_FLASK_PORT ?? '5000'}`

/**
 * Opens an SSE connection directly to the Flask backend (not through the
 * Next.js proxy) and accumulates live pane output lines in local state.
 * Each line arrives within ~1 s of appearing in the tmux pane.
 *
 * Falls back gracefully — if the SSE connection cannot be established
 * (e.g. no TmuxManager configured), `connected` stays false and `lines`
 * stays empty so the caller can fall back to polled pane_lines.
 *
 * Auto-reconnects with exponential backoff (1 s → 2 s → 4 s … cap 30 s)
 * so transient drops during agent startup are recovered automatically.
 *
 * @param dealerId - Optional dealer ID for per-dealer streams.
 *                   Falls back to the primary /api/agent/stream if omitted.
 */
export function useAgentStream(dealerId?: string) {
  const [lines, setLines]         = useState<string[]>([])
  const [connected, setConnected] = useState(false)
  const esRef                     = useRef<EventSource | null>(null)
  const retryDelay                = useRef(1000)
  const retryTimer                = useRef<ReturnType<typeof setTimeout> | null>(null)
  const unmounted                 = useRef(false)

  const sseUrl = dealerId
    ? `${FLASK_ORIGIN}/api/dealer/${encodeURIComponent(dealerId)}/stream`
    : `${FLASK_ORIGIN}/api/agent/stream`

  useEffect(() => {
    unmounted.current = false

    function connect() {
      if (unmounted.current) return

      const es = new EventSource(sseUrl)
      esRef.current = es

      es.onopen = () => {
        retryDelay.current = 1000   // reset backoff on successful connect
        setConnected(true)
      }

      es.onerror = () => {
        setConnected(false)
        es.close()
        esRef.current = null
        if (!unmounted.current) {
          // Reconnect with exponential backoff, cap at 30 s
          retryTimer.current = setTimeout(() => {
            retryDelay.current = Math.min(retryDelay.current * 2, 30_000)
            connect()
          }, retryDelay.current)
        }
      }

      es.onmessage = (e: MessageEvent) => {
        const line = e.data as string
        setLines(prev => {
          const next = [...prev, line]
          return next.length > MAX_LINES ? next.slice(-MAX_LINES) : next
        })
      }
    }

    connect()

    return () => {
      unmounted.current = true
      if (retryTimer.current) clearTimeout(retryTimer.current)
      esRef.current?.close()
      esRef.current = null
      setConnected(false)
    }
  }, [sseUrl])

  return { lines, connected }
}
