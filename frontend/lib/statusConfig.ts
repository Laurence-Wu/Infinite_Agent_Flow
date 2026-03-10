/**
 * Status display configuration — single source of truth for all
 * status-derived colors, labels, and badge styles.
 *
 * All colors use the Gruvbox-mapped Tailwind tokens:
 *   success = #b8bb26 (green bright)
 *   danger  = #fb4934 (red bright)
 *   accent  = #d79921 / accent-light = #fabd2f (yellow)
 */

export interface StatusDotConfig {
  /** Tailwind bg-* class for the indicator dot. */
  color: string
  /** Human-readable label. */
  label: string
  /** Whether the dot should animate with a ping effect. */
  ping:  boolean
}

/** Header status dot, keyed by Snapshot.status. */
export const STATUS_DOT: Record<string, StatusDotConfig> = {
  running:           { color: 'bg-success',   label: 'Running',   ping: true  },
  error:             { color: 'bg-danger',    label: 'Error',     ping: false },
  workflow_finished: { color: 'bg-accent',    label: 'Finished',  ping: false },
  completed:         { color: 'bg-accent',    label: 'Completed', ping: false },
  idle:              { color: 'bg-slate-700', label: 'Idle',      ping: false },
}

/** ProgressPanel badge classes, keyed by Snapshot.status. */
export const STATUS_BADGE: Record<string, string> = {
  running:           'bg-success/10 text-success border-success/30',
  error:             'bg-danger/10  text-danger  border-danger/30',
  completed:         'bg-accent/10  text-accent-light border-accent/30',
  workflow_finished: 'bg-accent/10  text-accent-light border-accent/30',
  idle:              'bg-slate-800/60 text-slate-500 border-slate-700/40',
}
