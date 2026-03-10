export interface HistoryEntry {
  card_id: string
  workflow: string
  version: string
  loop_id: string
  summary: string
  completed_at: string
}

export interface Snapshot {
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
}

export interface Workflow {
  name: string
  version: string
}
