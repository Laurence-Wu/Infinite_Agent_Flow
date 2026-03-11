/**
 * Log parsing and color utilities for the CardDealer dashboard.
 * Provides structured log parsing with Gruvbox-inspired color scheme.
 */

export type LogLevel = 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'FATAL';

export interface ParsedLogEntry {
  id: string;
  timestamp: string;
  level: LogLevel;
  source: string;
  message: string;
  raw: string;
  category: LogCategory;
}

export type LogCategory = 
  | 'orchestrator'
  | 'planner'
  | 'dealer'
  | 'picker'
  | 'state'
  | 'workflow'
  | 'system'
  | 'unknown';

/**
 * Gruvbox-inspired color scheme for log levels
 */
export const LOG_COLORS = {
  DEBUG: {
    bg: 'bg-slate-800/50',
    text: 'text-slate-500',
    border: 'border-slate-700',
    icon: 'text-slate-500',
    badge: 'bg-slate-700/50 text-slate-400',
  },
  INFO: {
    bg: 'bg-gruvbox-green/10',
    text: 'text-gruvbox-green-bright',
    border: 'border-gruvbox-green/30',
    icon: 'text-gruvbox-green',
    badge: 'bg-gruvbox-green/20 text-gruvbox-green-bright',
  },
  WARNING: {
    bg: 'bg-gruvbox-yellow/10',
    text: 'text-gruvbox-yellow-bright',
    border: 'border-gruvbox-yellow/30',
    icon: 'text-gruvbox-yellow',
    badge: 'bg-gruvbox-yellow/20 text-gruvbox-yellow-bright',
  },
  ERROR: {
    bg: 'bg-gruvbox-red/10',
    text: 'text-gruvbox-red-bright',
    border: 'border-gruvbox-red/30',
    icon: 'text-gruvbox-red',
    badge: 'bg-gruvbox-red/20 text-gruvbox-red-bright',
  },
  FATAL: {
    bg: 'bg-gruvbox-red/20',
    text: 'text-gruvbox-red-bright font-bold',
    border: 'border-gruvbox-red/50',
    icon: 'text-gruvbox-red-bright',
    badge: 'bg-gruvbox-red/40 text-gruvbox-red-bright',
  },
};

/**
 * Category colors for source identification
 */
export const CATEGORY_COLORS: Record<LogCategory, string> = {
  orchestrator: 'text-gruvbox-purple-bright',
  planner: 'text-gruvbox-cyan-bright',
  dealer: 'text-gruvbox-orange-bright',
  picker: 'text-gruvbox-aqua-bright',
  state: 'text-gruvbox-yellow-bright',
  workflow: 'text-accent-light',
  system: 'text-slate-400',
  unknown: 'text-slate-500',
};

/**
 * Parse a log line into structured components.
 * Expected format: "HH:MM:SS [LEVEL] source: message"
 * Example: "14:22:01 [INFO] planner: Workflow sample_workflow/v1 started"
 */
export function parseLogLine(line: string): ParsedLogEntry {
  const id = `log-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  
  // Regex to match: timestamp [LEVEL] source: message
  const regex = /^(\d{2}:\d{2}:\d{2})\s+\[(\w+)\]\s+([\w-]+):\s+(.*)$/;
  const match = line.match(regex);

  if (!match) {
    // Fallback for unstructured logs
    return {
      id,
      timestamp: new Date().toLocaleTimeString('en-US', { hour12: false }),
      level: 'INFO',
      source: 'unknown',
      message: line,
      raw: line,
      category: 'unknown',
    };
  }

  const [, timestamp, level, source, message] = match;
  const parsedLevel = (level.toUpperCase() as LogLevel) || 'INFO';
  const category = categorizeSource(source);

  return {
    id,
    timestamp,
    level: parsedLevel,
    source,
    message,
    raw: line,
    category,
  };
}

/**
 * Categorize log source for better organization
 */
function categorizeSource(source: string): LogCategory {
  const sourceLower = source.toLowerCase();
  
  if (sourceLower.includes('orchestrator')) return 'orchestrator';
  if (sourceLower.includes('planner')) return 'planner';
  if (sourceLower.includes('dealer')) return 'dealer';
  if (sourceLower.includes('picker')) return 'picker';
  if (sourceLower.includes('state')) return 'state';
  if (sourceLower.includes('workflow')) return 'workflow';
  if (sourceLower.includes('system') || sourceLower.includes('os')) return 'system';
  
  return 'unknown';
}

/**
 * Parse multiple log lines into structured entries
 */
export function parseLogLines(lines: string[]): ParsedLogEntry[] {
  return lines.map(parseLogLine);
}

/**
 * Filter log entries by level
 */
export function filterLogsByLevel(
  entries: ParsedLogEntry[],
  levels: LogLevel[]
): ParsedLogEntry[] {
  if (levels.length === 0) return entries;
  return entries.filter(entry => levels.includes(entry.level));
}

/**
 * Filter log entries by category
 */
export function filterLogsByCategory(
  entries: ParsedLogEntry[],
  categories: LogCategory[]
): ParsedLogEntry[] {
  if (categories.length === 0) return entries;
  return entries.filter(entry => categories.includes(entry.category));
}

/**
 * Get status indicator based on recent log activity
 */
export function getWorkflowStatusFromLogs(entries: ParsedLogEntry[]): {
  status: 'healthy' | 'warning' | 'error' | 'critical';
  message: string;
  recentErrors: number;
} {
  const recentEntries = entries.slice(-50); // Last 50 entries
  const errorCount = recentEntries.filter(
    e => e.level === 'ERROR' || e.level === 'FATAL'
  ).length;
  const warningCount = recentEntries.filter(
    e => e.level === 'WARNING'
  ).length;

  if (errorCount >= 3) {
    return {
      status: 'critical',
      message: 'Multiple errors detected',
      recentErrors: errorCount,
    };
  }
  
  if (errorCount >= 1) {
    return {
      status: 'error',
      message: 'Error in workflow',
      recentErrors: errorCount,
    };
  }
  
  if (warningCount >= 3) {
    return {
      status: 'warning',
      message: 'Multiple warnings',
      recentErrors: errorCount,
    };
  }

  return {
    status: 'healthy',
    message: 'Workflow running normally',
    recentErrors: errorCount,
  };
}

/**
 * Extract workflow events from logs (card transitions, completions, etc.)
 */
export function extractWorkflowEvents(entries: ParsedLogEntry[]): ParsedLogEntry[] {
  const eventKeywords = [
    'started',
    'completed',
    'advanced',
    'archived',
    'error',
    'timeout',
    'workflow',
    'card',
  ];

  return entries.filter(entry =>
    eventKeywords.some(keyword =>
      entry.message.toLowerCase().includes(keyword)
    )
  );
}

/**
 * Get color classes for a log entry based on level and category
 */
export function getLogEntryClasses(entry: ParsedLogEntry): {
  container: string;
  text: string;
  border: string;
  badge: string;
  icon: string;
} {
  const levelColors = LOG_COLORS[entry.level];
  const categoryColor = CATEGORY_COLORS[entry.category];

  return {
    container: `bg-slate-900/50 hover:bg-slate-800/50 ${levelColors.bg}`,
    text: levelColors.text,
    border: `border-l-2 ${levelColors.border}`,
    badge: levelColors.badge,
    icon: levelColors.icon,
  };
}
