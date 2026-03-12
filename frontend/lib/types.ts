export interface HistoryEntry {
  card_id: string
  workflow: string
  version: string
  loop_id: string
  summary: string
  completed_at: string
}

export interface Snapshot {
  agent_id: string
  current_card_id: string | null
  current_workflow: string | null
  current_version: string | null
  current_instruction: string | null
  current_loop_id: string
  card_index: number
  total_cards: number
  progress_pct: number
  completed_total: number
  cycles_completed: number
  status: 'idle' | 'running' | 'completed' | 'error' | 'workflow_finished'
  started_at: string | null
  last_updated: string | null
  history: HistoryEntry[]
  error: string | null
  log_lines: string[]
  engine_start_epoch: number | null
  uptime_seconds: number
  is_paused?: boolean
  workspace?: string
}

/** Lightweight summary returned by GET /api/agents (registry list). */
export interface AgentEntry {
  agent_id: string
  workspace: string
  workflow: string
  version: string
  status: 'idle' | 'running' | 'completed' | 'error' | 'workflow_finished'
  current_card_id: string | null
  started_at: string
  last_updated: string | null
  is_paused: boolean
  cycles_completed: number
  completed_total: number
  progress_pct: number
  card_index: number
  total_cards: number
  error: string | null
}

export interface Workflow {
  name: string
  version: string
}

export type ActiveWorkflows = Record<string, string>

export interface WorkspaceScanEntry {
  path:  string   // relative POSIX path e.g. "current_task.md"
  mtime: string   // ISO 8601 UTC e.g. "2026-03-10T14:22:01.123456+00:00"
  size:  number   // bytes
}

export interface WorkspaceScan {
  files: WorkspaceScanEntry[]
}

export interface SessionStatus {
  alive: boolean
  starting: boolean
  session_name: string
  agent_command: string
  workspace: string
  pane_lines: string[]
}
