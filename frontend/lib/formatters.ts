/**
 * Pure display utility functions — single source of truth for all
 * formatting logic used across dashboard components.
 *
 * No React, no hooks, no side effects.
 */

/** Formats elapsed seconds into a human-readable uptime string. */
export function formatUptime(secs: number): string {
  const s = Math.floor(secs)
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const r = s % 60
  if (h > 0) return `${h}h ${String(m).padStart(2, '0')}m`
  if (m > 0) return `${m}m ${String(r).padStart(2, '0')}s`
  return `${r}s`
}

/** Returns a Tailwind text-color class appropriate for a log line string. */
export function lineClass(line: string): string {
  if (line.includes('[ERROR]'))   return 'text-red-400'
  if (line.includes('[WARNING]')) return 'text-yellow-400'
  if (line.includes('[INFO]'))    return 'text-green-400'
  return 'text-slate-500'
}

/** Converts an ISO 8601 UTC timestamp to a human-readable relative time label. */
export function relativeTime(isoUtc: string): string {
  const secs = Math.floor((Date.now() - new Date(isoUtc).getTime()) / 1000)
  if (secs < 5)  return 'just now'
  if (secs < 60) return `${secs}s ago`
  const m = Math.floor(secs / 60)
  if (m  < 60)  return `${m}m ago`
  return `${Math.floor(m / 60)}h ago`
}

/** Formats a byte count as "512 B" or "3.2 KB". */
export function fmtSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  return `${(bytes / 1024).toFixed(1)} KB`
}

/** Returns a Tailwind bg-* class for a file's extension dot badge. */
export function extColor(path: string): string {
  const ext = path.split('.').pop()?.toLowerCase() ?? ''
  const map: Record<string, string> = {
    md:   'bg-accent',
    py:   'bg-yellow-400',
    json: 'bg-green-400',
    txt:  'bg-slate-400',
    ts:   'bg-blue-400',
    tsx:  'bg-blue-400',
    js:   'bg-yellow-300',
  }
  return map[ext] ?? 'bg-slate-500'
}

/**
 * Parses GFM checklist items from a markdown string.
 * Returns null when no checklist items are present.
 */
export function parseChecklist(md: string): { done: number; total: number } | null {
  const done  = (md.match(/- \[x\]/gi) ?? []).length
  const open  = (md.match(/- \[ \]/g)  ?? []).length
  const total = done + open
  return total === 0 ? null : { done, total }
}
