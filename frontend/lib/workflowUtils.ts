import type { DealerEntry, Workflow } from '@/lib/types'

export type WorkflowGroup = {
  key: string
  name: string
  version: string
  dealers: DealerEntry[]
}

export type WorkflowStatusCounts = {
  running: number
  paused: number
  error: number
  other: number
}

export type WorkflowBoardLane = 'running' | 'paused' | 'error' | 'other'

export const workflowKey = (name: string, version: string) => `${name}/${version}`

export function parseWorkflowKey(key: string): { name: string; version: string } {
  const [name, ...rest] = key.split('/')
  return {
    name,
    version: rest.join('/') || 'v1',
  }
}

export function groupWorkflows(workflows: Workflow[], dealers: DealerEntry[]): WorkflowGroup[] {
  const byKey = new Map<string, WorkflowGroup>()

  const ensure = (name: string, version: string) => {
    const key = workflowKey(name, version)
    if (!byKey.has(key)) {
      byKey.set(key, { key, name, version, dealers: [] })
    }
    return byKey.get(key)!
  }

  for (const workflow of workflows) {
    ensure(workflow.name, workflow.version)
  }

  for (const dealer of dealers) {
    ensure(dealer.workflow, dealer.version).dealers.push(dealer)
  }

  return Array.from(byKey.values()).sort((a, b) => {
    if (a.name === b.name) return a.version.localeCompare(b.version)
    return a.name.localeCompare(b.name)
  })
}

export function getStatusCounts(group: WorkflowGroup): WorkflowStatusCounts {
  let running = 0, paused = 0, error = 0, other = 0
  for (const d of group.dealers) {
    if (d.is_paused)          paused += 1
    else if (d.status === 'running') running += 1
    else if (d.status === 'error')   error += 1
    else                             other += 1
  }
  return { running, paused, error, other }
}

export function getBoardLane(group: WorkflowGroup): WorkflowBoardLane {
  const counts = getStatusCounts(group)
  if (counts.error > 0)   return 'error'
  if (counts.running > 0) return 'running'
  if (counts.paused > 0)  return 'paused'
  return 'other'
}
