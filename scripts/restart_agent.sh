#!/usr/bin/env bash
# Usage: ./scripts/restart_agent.sh [WORKSPACE] [SESSION_NAME] [AGENT_CMD] [STARTUP_WAIT]
#
# Stops the current session (if running) then starts a fresh one.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

WORKSPACE="${1:-./workspace}"
SESSION="${2:-gemini_agent}"
AGENT_CMD="${3:-gemini}"
STARTUP_WAIT="${4:-20}"

echo "Restarting session '$SESSION'..."
bash "$SCRIPT_DIR/stop_agent.sh" "$SESSION"
sleep 2
bash "$SCRIPT_DIR/start_agent.sh" "$WORKSPACE" "$SESSION" "$AGENT_CMD" "$STARTUP_WAIT"
